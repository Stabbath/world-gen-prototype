import math
import pygame
import sys
import traceback
from camera import Camera
from hex_view import HexView
from map_generator import generate_map
from neighbor_functions import get_neighbors_wraparound

# ------------------------------
# Constants and Configurations
# ------------------------------

# Screen settings
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
BACKGROUND_COLOR = (0, 0, 0)  # White background
FPS = 60 # CAP the frame rate at 60 FPS

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
MIN_ZOOM = 0.5    # Minimum zoom level
MAX_ZOOM = 3.0    # Maximum zoom level

# Number of tiles to select for fault generation
INITIAL_N_SELECTED_TILES = 12  # Number of starting points along the boundaries

# Generation method
GEN_METHOD = 1  # Set to 0 for fault-based generation, 1 for plate-based generation

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
        hex_grid = generate_map(
            GEN_METHOD,
            cols=INITIAL_GRID_COLS,
            rows=INITIAL_GRID_ROWS,
            n_selected=INITIAL_N_SELECTED_TILES,
            func_neighbors=get_neighbors_wraparound
        )

        hex_view = HexView(hex_grid, size=HEX_SIZE, offset_x=100, offset_y=100)

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
                    elif event.button == 5:  # Mouse wheel down to zoom out
                        mouse_pos = event.pos
                        camera.adjust_zoom(1 / ZOOM_STEP, mouse_pos)
                    elif event.button == 1:  # Left mouse button to start panning
                        is_panning = True
                        pan_start_pos = pygame.math.Vector2(event.pos)
                        pan_start_offset = camera.offset.copy()

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
                        # Regenerate the map
                        hex_grid = generate_map(
                            GEN_METHOD,
                            cols=INITIAL_GRID_COLS,
                            rows=INITIAL_GRID_ROWS,
                            n_selected=INITIAL_N_SELECTED_TILES
                        )
                        hex_view = HexView(hex_grid, size=HEX_SIZE, offset_x=100, offset_y=100)

            # Clear the screen
            screen.fill(BACKGROUND_COLOR)

            # Draw the hex grid with labels
            if hex_view:
                hex_view.draw(screen, camera)

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
