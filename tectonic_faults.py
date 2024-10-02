import math
import pygame
import sys
import traceback
import random

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

# Grid settings
GRID_COLS = 10  # Number of columns
GRID_ROWS = 10  # Number of rows

# Colors
HEX_COLOR = (173, 216, 230)      # Light blue
OUTLINE_COLOR = (0, 0, 0)        # Black
LABEL_COLOR = (0, 0, 0)          # Black

SELECTED_HEX_COLOR = (0, 0, 0)    # Black
SELECTED_LABEL_COLOR = (255, 255, 255)  # White
SELECTED_OUTLINE_COLOR = (255, 255, 255)  # White

LINE_HEX_COLOR = (0, 0, 0)        # Black
LINE_LABEL_COLOR = (255, 255, 255)  # White
LINE_OUTLINE_COLOR = (255, 255, 255)  # White

# Font settings
FONT_NAME = None  # Default font
BASE_FONT_SIZE = 14  # Base font size for zoom_factor = 1.0

# Zoom settings
ZOOM_STEP = 1.1  # Zoom in/out factor per mouse wheel event
MIN_ZOOM = 0.5    # Minimum zoom level
MAX_ZOOM = 3.0    # Maximum zoom level

# Number of tiles to select
N_SELECTED_TILES = 2  # Adjust as needed

# ------------------------------
# Class Definitions
# ------------------------------

class HexTile:
    def __init__(self, col, row, center, size):
        """
        Initialize a HexTile.

        :param col: Column number (starting at 1)
        :param row: Row number (starting at 1)
        :param center: Tuple (x, y) for the center position
        :param size: Radius of the hexagon
        """
        self.col = col
        self.row = row
        self.center = center
        self.size = size
        self.is_selected = False
        self.is_line = False

    def get_corners(self):
        """
        Calculate the six corner points of the hexagon.

        :return: List of (x, y) tuples for each corner
        """
        corners = []
        for i in range(6):
            angle_deg = 60 * i + 30  # Offset to make flat-topped
            angle_rad = math.radians(angle_deg)
            x = self.center[0] + self.size * math.cos(angle_rad)
            y = self.center[1] + self.size * math.sin(angle_rad)
            corners.append((x, y))
        return corners

    def draw(self, screen, font, zoom_factor):
        """
        Draw the hexagon and its label on the screen.

        :param screen: Pygame surface to draw on
        :param font: Pygame font object for rendering text
        :param zoom_factor: Current zoom factor to adjust font size
        """
        # Determine colors based on tile status
        if self.is_selected:
            fill_color = SELECTED_HEX_COLOR
            outline_color = SELECTED_OUTLINE_COLOR
            label_color = SELECTED_LABEL_COLOR
        elif self.is_line:
            fill_color = LINE_HEX_COLOR
            outline_color = LINE_OUTLINE_COLOR
            label_color = LINE_LABEL_COLOR
        else:
            fill_color = HEX_COLOR
            outline_color = OUTLINE_COLOR
            label_color = LABEL_COLOR

        # Draw filled hexagon
        pygame.draw.polygon(screen, fill_color, self.get_corners())
        # Draw hexagon outline
        pygame.draw.polygon(screen, outline_color, self.get_corners(), 2)

        # Prepare label
        label = f"({self.col},{self.row})"
        # Adjust font size based on zoom
        adjusted_font_size = max(int(BASE_FONT_SIZE * zoom_factor), 8)
        try:
            adjusted_font = pygame.font.SysFont(FONT_NAME, adjusted_font_size)
        except Exception as e:
            print(f"Error initializing font for label '{label}':", e)
            adjusted_font = pygame.font.Font(None, adjusted_font_size)
        text_surface = adjusted_font.render(label, True, label_color)
        text_rect = text_surface.get_rect(center=self.center)
        screen.blit(text_surface, text_rect)


class HexGrid:
    def __init__(self, cols, rows, size, offset_x=100, offset_y=100):
        """
        Initialize the HexGrid.

        :param cols: Number of columns
        :param rows: Number of rows
        :param size: Radius of each hexagon
        :param offset_x: Horizontal offset from the screen's origin
        :param offset_y: Vertical offset from the screen's origin
        """
        self.cols = cols
        self.rows = rows
        self.size = size
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.tiles = self.generate_grid()

    def generate_grid(self):
        """
        Generate the grid of HexTile instances.

        :return: List of HexTile objects
        """
        tiles = []
        for row in range(1, self.rows + 1):
            for col in range(1, self.cols + 1):
                # Calculate the position of the hex center
                x = self.offset_x + (col - 1) * HORIZONTAL_SPACING
                y = self.offset_y + (row - 1) * VERTICAL_SPACING
                if col % 2 == 0:
                    y -= VERTICAL_SPACING / 2  # Shift even columns upwards
                center = (x, y)
                tile = HexTile(col, row, center, self.size)
                tiles.append(tile)
        return tiles

    def select_random_tiles(self, n):
        """
        Select n random unique tiles from the grid.

        :param n: Number of tiles to select
        :return: List of selected HexTile objects
        """
        if n > len(self.tiles):
            raise ValueError("Number of tiles to select exceeds total tiles in the grid.")
        selected_tiles = random.sample(self.tiles, n)
        for tile in selected_tiles:
            tile.is_selected = True
        return selected_tiles

    def generate_north_lines(self, selected_tiles):
        """
        From each selected tile, generate a line moving northwards until the boundary.

        :param selected_tiles: List of HexTile objects that are selected
        """
        for tile in selected_tiles:
            current_col = tile.col
            current_row = tile.row
            while current_row < self.rows:
                current_row += 1  # Move northwards
                # Find the tile at (current_col, current_row)
                target_tile = self.get_tile(current_col, current_row)
                if target_tile:
                    target_tile.is_line = True
                else:
                    break  # Reached boundary

    def get_tile(self, col, row):
        """
        Retrieve the tile at a specific (col, row).

        :param col: Column number
        :param row: Row number
        :return: HexTile object or None if not found
        """
        for tile in self.tiles:
            if tile.col == col and tile.row == row:
                return tile
        return None

    def draw(self, screen, zoom_factor):
        """
        Draw all hex tiles on the screen.

        :param screen: Pygame surface to draw on
        :param zoom_factor: Current zoom factor to adjust font sizes
        """
        for tile in self.tiles:
            tile.draw(screen, None, zoom_factor)


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
        pygame.display.set_caption("Flat-Top Hexagonal Grid with Labels")

        # Create a clock to manage the frame rate
        clock = pygame.time.Clock()

        # Initialize font
        try:
            font = pygame.font.SysFont(FONT_NAME, BASE_FONT_SIZE)
        except Exception as e:
            print("Error initializing font:", e)
            font = pygame.font.Font(None, BASE_FONT_SIZE)

        # Create the hex grid
        hex_grid = HexGrid(GRID_COLS, GRID_ROWS, HEX_SIZE, offset_x=100, offset_y=100)

        # Select N random tiles
        selected_tiles = hex_grid.select_random_tiles(N_SELECTED_TILES)
        print(f"Selected {N_SELECTED_TILES} tiles for line generation.")

        # Generate northwards lines from selected tiles
        hex_grid.generate_north_lines(selected_tiles)
        print("Generated northwards lines from selected tiles.")

        # Zoom and pan variables
        zoom_factor = 1.0
        camera_offset = [0, 0]
        zoom_center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)  # Center of the screen

        # Variables for panning
        is_panning = False
        pan_start_pos = (0, 0)
        pan_start_offset = [0, 0]

        # Main loop flag
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Handle zooming with mouse wheel
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:  # Mouse wheel up to zoom in
                        # Calculate new zoom factor
                        new_zoom = zoom_factor * ZOOM_STEP
                        if new_zoom <= MAX_ZOOM:
                            # Adjust camera offset to keep zoom centered
                            mouse_x, mouse_y = event.pos
                            rel_x = mouse_x - zoom_center[0]
                            rel_y = mouse_y - zoom_center[1]
                            camera_offset[0] = (camera_offset[0] - rel_x) * ZOOM_STEP + rel_x
                            camera_offset[1] = (camera_offset[1] - rel_y) * ZOOM_STEP + rel_y
                            zoom_factor = new_zoom
                            print(f"Zoomed in to {zoom_factor:.2f}x")
                    elif event.button == 5:  # Mouse wheel down to zoom out
                        # Calculate new zoom factor
                        new_zoom = zoom_factor / ZOOM_STEP
                        if new_zoom >= MIN_ZOOM:
                            # Adjust camera offset to keep zoom centered
                            mouse_x, mouse_y = event.pos
                            rel_x = mouse_x - zoom_center[0]
                            rel_y = mouse_y - zoom_center[1]
                            camera_offset[0] = (camera_offset[0] - rel_x) / ZOOM_STEP + rel_x
                            camera_offset[1] = (camera_offset[1] - rel_y) / ZOOM_STEP + rel_y
                            zoom_factor = new_zoom
                            print(f"Zoomed out to {zoom_factor:.2f}x")
                    elif event.button == 1:  # Left mouse button to start panning
                        is_panning = True
                        pan_start_pos = event.pos
                        pan_start_offset = camera_offset.copy()
                        print("Started panning")

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left mouse button to stop panning
                        is_panning = False
                        print("Stopped panning")

                elif event.type == pygame.MOUSEMOTION:
                    if is_panning:
                        dx = event.pos[0] - pan_start_pos[0]
                        dy = event.pos[1] - pan_start_pos[1]
                        camera_offset[0] = pan_start_offset[0] + dx
                        camera_offset[1] = pan_start_offset[1] + dy
                        # Optional: Print camera offset for debugging
                        # print(f"Panning to offset: {camera_offset}")

            # Clear the screen
            screen.fill(BACKGROUND_COLOR)

            # Draw the hex grid with labels
            hex_grid.draw(screen, zoom_factor)

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
