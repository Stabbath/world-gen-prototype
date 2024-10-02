import math
import pygame
import random

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

    def get_corners(self):
        """
        Calculate the six corner points of the hexagon.

        :return: List of (x, y) tuples for each corner
        """
        corners = []
        for i in range(6):
            angle_deg = 60 * i   # Offset to make flat-topped
            angle_rad = math.radians(angle_deg)
            x = self.center[0] + self.size * math.cos(angle_rad)
            y = self.center[1] + self.size * math.sin(angle_rad)
            corners.append((x, y))
        return corners

    def draw(self, screen, font, zoom_factor, is_selected=False):
        """
        Draw the hexagon and its label on the screen.

        :param screen: Pygame surface to draw on
        :param font: Pygame font object for rendering text
        :param zoom_factor: Current zoom factor to adjust font size
        :param is_selected: Boolean indicating if the tile is selected
        """
        # Colors
        LABEL_COLOR = (0, 0, 0)          # Black
        HEX_COLOR = (173, 216, 230)      # Light blue
        OUTLINE_COLOR = (0, 0, 0)        # Black

        SELECTED_HEX_COLOR = (0, 0, 0)    # Black
        SELECTED_OUTLINE_COLOR = (255, 255, 255)  # White
        SELECTED_LABEL_COLOR = (255, 255, 255)    # White
        BASE_FONT_SIZE = 14  # Base font size for zoom_factor = 1.0
        FONT_NAME = None  # Default font
        
        if is_selected:
            fill_color = SELECTED_HEX_COLOR
            outline_color = SELECTED_OUTLINE_COLOR
            label_color = SELECTED_LABEL_COLOR
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

        
        text_surface = font.render(label, True, LABEL_COLOR)
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
    
    def select_random_tiles(self, n):
        """
        Select n unique random tiles from the grid.

        :param n: Number of tiles to select
        :return: Set of (col, row) tuples representing selected tiles
        """
        if n > len(self.tiles):
            raise ValueError("Number of tiles to select exceeds total tiles in the grid.")
        selected_tiles = set(random.sample([(tile.col, tile.row) for tile in self.tiles], n))
        print(f"Selected tiles: {selected_tiles}")
        print('Hello')
        return selected_tiles
    
    def generate_grid(self):
        """
        Generate the grid of HexTile instances.

        :return: List of HexTile objects
        """
        HEX_HEIGHT = math.sqrt(3) * self.size
        HEX_WIDTH = 2 * self.size
        VERTICAL_SPACING = HEX_HEIGHT
        HORIZONTAL_SPACING = HEX_WIDTH * 0.75  # Flat-topped hexagons overlap horizontally by 25%
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

    def draw(self, screen, font, selected_tiles):
        """
        Draw all hex tiles on the screen.

        :param screen: Pygame surface to draw on
        :param font: Pygame font object for rendering text
        """
        for tile in self.tiles:
            is_selected = (tile.col, tile.row) in selected_tiles
            tile.draw(screen,None, font, is_selected=is_selected)
