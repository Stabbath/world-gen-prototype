import math
import pygame
import sys
import traceback
from camera import Camera
from hex_view import HexView
from hex_view_colors import color_plates, color_altitude, color_hydro, color_faults
from map_generator import generate_map
from neighbor_functions import get_neighbors_wraparound
from config import default_config, ConfigPanel
from view_tabs import TabPanel

# ------------------------------
# Constants and Configurations
# ------------------------------

# Screen settings
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
BACKGROUND_COLOR = (0, 0, 0)  # Black background
FPS = 60  # Cap the frame rate at 60 FPS

# Panel settings
PANEL_WIDTH = 200  # Width of the left-side panel
TAB_BUTTON_WIDTH = 100
TAB_BUTTON_HEIGHT = 30
TAB_BUTTON_PADDING = 10
TABS_HEIGHT = TAB_BUTTON_HEIGHT + TAB_BUTTON_PADDING 

# Hexagon settings
HEX_SIZE = 20  # Adjusted size
HEX_HEIGHT = math.sqrt(3) * HEX_SIZE
HEX_WIDTH = 2 * HEX_SIZE
VERTICAL_SPACING = HEX_HEIGHT
HORIZONTAL_SPACING = HEX_WIDTH * 0.75  # Flat-topped hexagons overlap horizontally by 25%

# Zoom settings
ZOOM_STEP = 1.1  # Zoom in/out factor per mouse wheel event
MIN_ZOOM = 0.1   # Reduced minimum zoom level to allow more zooming out
MAX_ZOOM = 3.0   # Maximum zoom level


VIEW_LABELS = ["Plates", "Faults", "Elevation", "Hydro"]

def full_gen(config):
    hex_grid = gen_world(config)
    hex_views = gen_views(config, hex_grid)
    return hex_grid, hex_views

def gen_views(config, hex_grid):
    # HexViews for different tabs
    hex_views = {
        "Plates": HexView(hex_grid, size=HEX_SIZE, func_color=color_plates, config=config, offset_x=100, offset_y=100),
        "Faults": HexView(hex_grid, size=HEX_SIZE, func_color=color_faults, config=config, offset_x=100, offset_y=100),
        "Elevation": HexView(hex_grid, size=HEX_SIZE, func_color=color_altitude, config=config, offset_x=100, offset_y=100),
        "Hydro": HexView(hex_grid, size=HEX_SIZE, func_color=color_hydro, config=config, offset_x=100, offset_y=100)
    }
    return hex_views

def gen_world(config):
    hex_grid = generate_map(
        gen_method=config["gen_method"],
        cols=config["width"],
        rows=config["height"],
        n_selected=config["startpoint_count"],
        func_neighbors=get_neighbors_wraparound
    )
    return hex_grid


# ------------------------------
# Pygame Initialization and Main Loop
# ------------------------------

def main():
    try:
        # Initialize Pygame
        pygame.init()
        pygame.font.init()  # Initialize font module

        # Set up the display
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Hexagonal Grid World with Zoom and Pan")

        # Create a clock to manage the frame rate
        clock = pygame.time.Clock()

        # Initialize Camera
        camera = Camera(zoom=1.0, offset=(0, 0), min_zoom=MIN_ZOOM, max_zoom=MAX_ZOOM)

        # Variables for panning
        is_panning = False
        pan_start_pos = pygame.math.Vector2(0, 0)
        pan_start_offset = pygame.math.Vector2(0, 0)

        config = default_config()

        # Initial map generation
        hex_grid, hex_views = full_gen(config)
        
        current_tab = VIEW_LABELS[0] # defaul view

        font = pygame.font.SysFont('Arial', 18)

        config_panel = ConfigPanel(PANEL_WIDTH, SCREEN_HEIGHT, config)
        tab_panel = TabPanel(VIEW_LABELS, PANEL_WIDTH, TAB_BUTTON_WIDTH, TAB_BUTTON_HEIGHT, TAB_BUTTON_PADDING)

        # Main view rectangle adjusted to not overlap with tab buttons
        main_view_rect = pygame.Rect(PANEL_WIDTH, TABS_HEIGHT, SCREEN_WIDTH - PANEL_WIDTH, SCREEN_HEIGHT - TABS_HEIGHT)

        # Main loop flag
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # First, check if the click is on any tab button
                    tab_clicked = tab_panel.process_event(event)

                    if tab_clicked is not None:
                        current_tab = tab_clicked
                    else:
                        # Check if mouse is over the main view pane
                        if main_view_rect.collidepoint(event.pos):
                            if event.button == 4:  # Mouse wheel up to zoom in
                                mouse_pos = event.pos
                                camera.adjust_zoom(ZOOM_STEP, mouse_pos)
                            elif event.button == 5:  # Mouse wheel down to zoom out
                                mouse_pos = event.pos
                                camera.adjust_zoom(1 / ZOOM_STEP, mouse_pos)
                            elif event.button == 1:  # Left mouse button to start panning
                                is_panning = True
                                pan_start_pos = pygame.math.Vector2(event.pos)
                                pan_start_offset = camera.offset.copy()
                        else:
                            # Let the left panel check for its events
                            action = config_panel.process_event(event)
                            if action == 'regen':
                                hex_grid, hex_views = full_gen(config)
                            elif action == 'config_changed':
                                pass # we're updating config in-place, so we ignore this

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left mouse button to stop panning
                        is_panning = False

                elif event.type == pygame.MOUSEMOTION:
                    if is_panning:
                        current_pos = pygame.math.Vector2(event.pos)
                        delta = current_pos - pan_start_pos
                        camera.offset = pan_start_offset + delta

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # Regenerate the map with current settings
                        hex_grid, hex_views = full_gen(config)

            # Clear the screen
            screen.fill(BACKGROUND_COLOR)

            # Draw left panel
            config_panel.draw(screen, font)

            # Draw main view pane background
            pygame.draw.rect(screen, (50, 50, 50), main_view_rect)

            # Draw the hex grid within the main view pane
            if current_tab and hex_views.get(current_tab):
                # Create a surface for the main view
                main_view_surface = pygame.Surface((main_view_rect.width, main_view_rect.height))
                main_view_surface.fill(BACKGROUND_COLOR)  # Background color

                # Adjust camera offset to consider the main view pane position
                adjusted_camera = Camera(
                    zoom=camera.zoom,
                    offset=(camera.offset[0] - PANEL_WIDTH, camera.offset[1] - TABS_HEIGHT),
                    min_zoom=MIN_ZOOM,
                    max_zoom=MAX_ZOOM
                )

                hex_views[current_tab].draw(main_view_surface, adjusted_camera)

                # Blit the main view surface onto the screen at the correct position
                screen.blit(main_view_surface, (PANEL_WIDTH, TABS_HEIGHT))

            # Draw tabs on top of the main view
            tab_panel.draw(screen, font, current_tab)

            # Update the display
            pygame.display.flip()

            # Cap the frame rate at 60 FPS
            clock.tick(FPS)

    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()
    finally:
        # Quit Pygame
        pygame.quit()
        sys.exit()

# ------------------------------
# Entry Point
# ------------------------------

if __name__ == "__main__":
    main()
