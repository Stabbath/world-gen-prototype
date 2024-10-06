import math
import pygame
import sys
import traceback
from camera import Camera
from hex_view import HexView
from hex_view_colors import color_plates, color_altitude, color_hydro, color_faults
from map_generator import generate_map
from neighbor_functions import get_neighbors_wraparound

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

# Hexagon settings
HEX_SIZE = 20  # Adjusted size
HEX_HEIGHT = math.sqrt(3) * HEX_SIZE
HEX_WIDTH = 2 * HEX_SIZE
VERTICAL_SPACING = HEX_HEIGHT
HORIZONTAL_SPACING = HEX_WIDTH * 0.75  # Flat-topped hexagons overlap horizontally by 25%

# Initial Grid settings
INITIAL_GRID_COLS = 50  # Increased grid size for better visual effect
INITIAL_GRID_ROWS = 50  # Increased grid size for better visual effect

# Zoom settings
ZOOM_STEP = 1.1  # Zoom in/out factor per mouse wheel event
MIN_ZOOM = 0.1   # Reduced minimum zoom level to allow more zooming out
MAX_ZOOM = 3.0   # Maximum zoom level

# Number of tiles to select for fault generation
INITIAL_N_SELECTED_TILES = 12  # Number of starting points along the boundaries

# Generation method
GEN_METHOD = 0  # Set to 0 for fault-based generation, 1 for plate-based generation

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

        # Initial map generation
        gen_method = GEN_METHOD
        n_selected_tiles = INITIAL_N_SELECTED_TILES
        hex_grid = generate_map(
            gen_method,
            cols=INITIAL_GRID_COLS,
            rows=INITIAL_GRID_ROWS,
            n_selected=n_selected_tiles,
            func_neighbors=get_neighbors_wraparound
        )
        
        configs = {
            "max_altitude": 20000, # TODO - note this should be read from the inputs, which will also determine the value during world gen
            "sea_level": 10000 # TODO - it would be cool if we could dynamically change sea level, but not a priority
        }

        # HexViews for different tabs
        hex_views = {
            "Plates": HexView(hex_grid, size=HEX_SIZE, func_color=color_plates, configs=configs, offset_x=100, offset_y=100),
            "Faults": HexView(hex_grid, size=HEX_SIZE, func_color=color_faults, configs=configs, offset_x=100, offset_y=100),
            "Elevation": HexView(hex_grid, size=HEX_SIZE, func_color=color_altitude, configs=configs, offset_x=100, offset_y=100),
            "Hydro": HexView(hex_grid, size=HEX_SIZE, func_color=color_hydro, configs=configs, offset_x=100, offset_y=100)
        }
        current_tab = "Plates"

        # Fonts
        font = pygame.font.SysFont('Arial', 18)

        # Left panel rectangle
        panel_rect = pygame.Rect(0, 0, PANEL_WIDTH, SCREEN_HEIGHT)

        # Define the height reserved for tab buttons
        TABS_HEIGHT = 40  # Adjust as needed for tab button size and padding

        # Main view rectangle adjusted to not overlap with tab buttons
        main_view_rect = pygame.Rect(PANEL_WIDTH, TABS_HEIGHT, SCREEN_WIDTH - PANEL_WIDTH, SCREEN_HEIGHT - TABS_HEIGHT)

        # Tab buttons
        tabs = ["Plates", "Faults", "Elevation", "Hydro"]
        tab_buttons = []
        tab_button_height = 30
        tab_button_width = 100
        tab_padding = 10  # Padding from the top of the screen

        for idx, tab in enumerate(tabs):
            # Position tabs with padding from the top and horizontally aligned
            button_rect = pygame.Rect(
                PANEL_WIDTH + idx * (tab_button_width + tab_padding), 
                (TABS_HEIGHT - tab_button_height) // 2,  # Center vertically within the TABS_HEIGHT
                tab_button_width, 
                tab_button_height
            )
            tab_buttons.append((tab, button_rect))

        # Buttons and controls in the left panel
        regenerate_button_rect = pygame.Rect(20, 60, PANEL_WIDTH - 40, 30)
        gen_method_label_rect = pygame.Rect(20, 110, PANEL_WIDTH - 40, 20)
        gen_method_button_rect = pygame.Rect(20, 140, PANEL_WIDTH - 40, 30)
        n_selected_label_rect = pygame.Rect(20, 190, PANEL_WIDTH - 40, 20)
        n_selected_increase_rect = pygame.Rect(20, 220, (PANEL_WIDTH - 60) // 2, 30)
        n_selected_decrease_rect = pygame.Rect(40 + (PANEL_WIDTH - 60) // 2, 220, (PANEL_WIDTH - 60) // 2, 30)

        # Main loop flag
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # First, check if the click is on any tab button
                    clicked_on_tab = False
                    for tab, button_rect in tab_buttons:
                        if button_rect.collidepoint(event.pos):
                            current_tab = tab
                            clicked_on_tab = True
                            break  # Stop checking other tabs

                    if not clicked_on_tab:
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
                            # Check if mouse is over the left panel controls
                            if regenerate_button_rect.collidepoint(event.pos):
                                # Regenerate the map with current settings
                                hex_grid = generate_map(
                                    gen_method,
                                    cols=INITIAL_GRID_COLS,
                                    rows=INITIAL_GRID_ROWS,
                                    n_selected=n_selected_tiles,
                                    func_neighbors=get_neighbors_wraparound
                                )
                                # Update hex views
                                hex_views = {
                                    "Plates": HexView(hex_grid, size=HEX_SIZE, func_color=color_plates, configs=configs, offset_x=100, offset_y=100),
                                    "Faults": HexView(hex_grid, size=HEX_SIZE, func_color=color_faults, configs=configs, offset_x=100, offset_y=100),
                                    "Elevation": HexView(hex_grid, size=HEX_SIZE, func_color=color_altitude, configs=configs, offset_x=100, offset_y=100),
                                    "Hydro": HexView(hex_grid, size=HEX_SIZE, func_color=color_hydro, configs=configs, offset_x=100, offset_y=100)
                                }
                            elif gen_method_button_rect.collidepoint(event.pos):
                                # Toggle generation method
                                gen_method = 1 - gen_method
                            elif n_selected_increase_rect.collidepoint(event.pos):
                                # Increase n_selected_tiles
                                n_selected_tiles += 1
                            elif n_selected_decrease_rect.collidepoint(event.pos):
                                # Decrease n_selected_tiles
                                if n_selected_tiles > 1:
                                    n_selected_tiles -= 1

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
                        hex_grid = generate_map(
                            gen_method,
                            cols=INITIAL_GRID_COLS,
                            rows=INITIAL_GRID_ROWS,
                            n_selected=n_selected_tiles,
                            func_neighbors=get_neighbors_wraparound
                        )
                        # Update hex views
                        hex_views = {
                            "Plates": HexView(hex_grid, size=HEX_SIZE, func_color=color_plates, configs=configs, offset_x=100, offset_y=100),
                            "Faults": HexView(hex_grid, size=HEX_SIZE, func_color=color_faults, configs=configs, offset_x=100, offset_y=100),
                            "Elevation": HexView(hex_grid, size=HEX_SIZE, func_color=color_altitude, configs=configs, offset_x=100, offset_y=100),
                            "Hydro": HexView(hex_grid, size=HEX_SIZE, func_color=color_hydro, configs=configs, offset_x=100, offset_y=100)
                        }

            # Clear the screen
            screen.fill(BACKGROUND_COLOR)

            # Draw left panel
            pygame.draw.rect(screen, (30, 30, 30), panel_rect)

            # Draw regenerate button
            pygame.draw.rect(screen, (70, 70, 70), regenerate_button_rect)
            regen_text = font.render("Regenerate", True, (255, 255, 255))
            regen_text_rect = regen_text.get_rect(center=regenerate_button_rect.center)
            screen.blit(regen_text, regen_text_rect)

            # Draw generation method label and button
            gen_method_label = font.render("Generation Method:", True, (255, 255, 255))
            screen.blit(gen_method_label, gen_method_label_rect.topleft)
            gen_method_text = "Plate Tectonics" if gen_method == 1 else "Fault Lines"
            pygame.draw.rect(screen, (70, 70, 70), gen_method_button_rect)
            method_text = font.render(gen_method_text, True, (255, 255, 255))
            method_text_rect = method_text.get_rect(center=gen_method_button_rect.center)
            screen.blit(method_text, method_text_rect)

            # Draw n_selected_tiles label and buttons
            n_selected_label = font.render("Number of Plates:", True, (255, 255, 255))
            screen.blit(n_selected_label, n_selected_label_rect.topleft)
            # Increase button
            pygame.draw.rect(screen, (70, 70, 70), n_selected_increase_rect)
            inc_text = font.render("+", True, (255, 255, 255))
            inc_text_rect = inc_text.get_rect(center=n_selected_increase_rect.center)
            screen.blit(inc_text, inc_text_rect)
            # Decrease button
            pygame.draw.rect(screen, (70, 70, 70), n_selected_decrease_rect)
            dec_text = font.render("-", True, (255, 255, 255))
            dec_text_rect = dec_text.get_rect(center=n_selected_decrease_rect.center)
            screen.blit(dec_text, dec_text_rect)
            # Display current n_selected_tiles value
            n_selected_value_text = font.render(str(n_selected_tiles), True, (255, 255, 255))
            n_selected_value_rect = n_selected_value_text.get_rect(center=(PANEL_WIDTH // 2, 235))
            screen.blit(n_selected_value_text, n_selected_value_rect)

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
            for tab, button_rect in tab_buttons:
                color = (100, 100, 100) if tab == current_tab else (50, 50, 50)
                pygame.draw.rect(screen, color, button_rect)
                text_surface = font.render(tab, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=button_rect.center)
                screen.blit(text_surface, text_rect)

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
