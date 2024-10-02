import math
import pygame
import sys
import traceback
import random
from camera import Camera
from hex_board_generator import HexGrid

# ------------------------------
# Constants and Configurations
# ------------------------------

# Screen settings
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
BACKGROUND_COLOR = (255, 255, 255)  # White background

# Hexagon settings
HEX_SIZE = 30  # Initial radius of the hexagon
HEX_HEIGHT = math.sqrt(3) * HEX_SIZE
HEX_WIDTH = 2 * HEX_SIZE
VERTICAL_SPACING = HEX_HEIGHT
HORIZONTAL_SPACING = HEX_WIDTH * 0.75  # Flat-topped hexagons overlap horizontally by 25%

# Initial Grid settings
INITIAL_GRID_COLS = 25  # Increased grid size for better visual effect
INITIAL_GRID_ROWS = 25  # Increased grid size for better visual effect

# Colors (default values)
DEFAULT_HEX_COLOR = (173, 216, 230)               # Light blue (ocean)
DEFAULT_OUTLINE_COLOR = (0, 0, 0)                 # Black
LABEL_COLOR = (255, 255, 255)        # White

SELECTED_HEX_COLOR = (0, 0, 0)             # Black
SELECTED_LABEL_COLOR = (255, 255, 255)    # White
SELECTED_OUTLINE_COLOR = (255, 255, 255)  # White

LINE_HEX_COLOR = (0, 0, 0)                 # Black (fault lines)
LINE_LABEL_COLOR = (255, 255, 255)        # White
LINE_OUTLINE_COLOR = (255, 255, 255)      # White

color_dict = {
    'default_hex':  DEFAULT_HEX_COLOR,
    'default_outline':  DEFAULT_OUTLINE_COLOR,
    'default_label':  LABEL_COLOR,
    'line_hex':  LINE_HEX_COLOR,
    'line_outline':  LINE_OUTLINE_COLOR,
    'line_label':  LINE_LABEL_COLOR
}

# Font settings
FONT_NAME = None  # Default font
BASE_FONT_SIZE = 14  # Base font size for hex labels

font_dict = {
    'base_size':  14,
    'base_name':  FONT_NAME
}

# Zoom settings
ZOOM_STEP = 1.1  # Zoom in/out factor per mouse wheel event
MIN_ZOOM = 0.5    # Minimum zoom level
MAX_ZOOM = 3.0    # Maximum zoom level

# Number of tiles to select
INITIAL_N_SELECTED_TILES = 12  # Number of starting points along the boundaries




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
        pygame.display.set_caption("Hexagonal Grid with Multi-Segment Fault Lines and Continents")

        # Create a clock to manage the frame rate
        clock = pygame.time.Clock()

        # Initialize font
        #try:
            #font = pygame.font.SysFont(FONT_NAME, 24)
        #except Exception as e:
            #print("Error initializing font:", e)
            #font = pygame.font.Font(None, 24)

        # Initialize Camera
        camera = Camera(zoom=1.0, offset=(0, 0), min_zoom=MIN_ZOOM, max_zoom=MAX_ZOOM)

        # Variables for panning
        is_panning = False
        pan_start_pos = pygame.math.Vector2(0, 0)
        pan_start_offset = pygame.math.Vector2(0, 0)

        # Create the hex grid by regenerating the map
        hex_grid = None
        selected_tiles = []

        def regenerate_map():
            nonlocal hex_grid, selected_tiles
            try:
                # Get values from constants
                n_selected = INITIAL_N_SELECTED_TILES
                cols = INITIAL_GRID_COLS
                rows = INITIAL_GRID_ROWS
                hex_color = DEFAULT_HEX_COLOR
                outline_color = DEFAULT_OUTLINE_COLOR

                # Create new hex grid
                hex_grid = HexGrid(cols, rows, HEX_SIZE, offset_x=100, offset_y=100, hex_color=hex_color, outline_color=outline_color)

                # Select boundary tiles
                selected_tiles = hex_grid.select_distributed_boundary_tiles(n_selected)
                print(f"Selected {n_selected} boundary tiles for line generation.")

                # Generate lines
                hex_grid.generate_lines_in_directions(selected_tiles)
                print("Generated lines from boundary tiles.")

                # Convert isolated tiles to fault lines
                #hex_grid.convert_isolated_tiles_to_fault_lines()

                # Label continents
                hex_grid.label_continents()

            except Exception as e:
                print("Error regenerating map:", e)

        # Initial map generation
        regenerate_map()

        # Main loop flag
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Handle zooming with mouse wheel
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:  # Mouse wheel up to zoom in
                        mouse_pos = event.pos
                        camera.adjust_zoom(ZOOM_STEP, mouse_pos)
                        print(f"Zoomed in to {camera.zoom:.2f}x")
                    elif event.button == 5:  # Mouse wheel down to zoom out
                        mouse_pos = event.pos
                        camera.adjust_zoom(1 / ZOOM_STEP, mouse_pos,)
                        print(f"Zoomed out to {camera.zoom:.2f}x")
                    elif event.button == 1:  # Left mouse button to start panning
                        is_panning = True
                        pan_start_pos = pygame.math.Vector2(event.pos)
                        pan_start_offset = camera.offset.copy()
                        print("Started panning")

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left mouse button to stop panning
                        is_panning = False
                        print("Stopped panning")

                elif event.type == pygame.MOUSEMOTION:
                    if is_panning:
                        current_pos = pygame.math.Vector2(event.pos)
                        delta = current_pos - pan_start_pos
                        camera.offset = pan_start_offset + delta

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # Regenerate the map
                        regenerate_map()
                        print("Map regenerated")

            # Clear the screen
            screen.fill(BACKGROUND_COLOR)

            # Draw the hex grid with labels
            if hex_grid:
                hex_grid.draw(screen, camera, color_dict, font_dict)

            # Update the display
            pygame.display.flip()

            # Cap the frame rate at 60 FPS
            clock.tick(60)

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
