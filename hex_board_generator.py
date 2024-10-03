import math
import pygame
from neighbor_functions import get_neighbors, get_neighbors_wraparound

class HexTile:
    def __init__(self, col, row, center, size, grid):
        self.col = col
        self.row = row
        self.center = pygame.math.Vector2(center)
        self.size = size
        self.grid = grid
        self.is_selected = False
        self.is_line = False
        self.continent_label = None
        self.plate_index = None

    def get_coords(self):
        return self.col, self.row

    def set_plate_index(self, plate_index):
        self.plate_index = plate_index

    def get_plate_index(self):
        return self.plate_index

    def get_neighbors(self, wraparound=False):
        neighbors = []
        if wraparound:
            neighbor_coords = get_neighbors_wraparound(self.col, self.row, self.grid.cols, self.grid.rows)
        else:
            neighbor_coords = get_neighbors(self.col, self.row, self.grid.cols, self.grid.rows)
        for x, y in neighbor_coords:
            neighbor = self.grid.get_tile(x, y)
            if neighbor:
                neighbors.append(neighbor)
        return neighbors

    def get_corners(self):
        corners = []
        for i in range(6):
            angle_deg = 60 * i  # Flat-topped hexagons
            angle_rad = math.radians(angle_deg)
            x = self.center.x + self.size * math.cos(angle_rad)
            y = self.center.y + self.size * math.sin(angle_rad)
            corners.append((x, y))
        return corners

    def draw(self, screen, camera, color_dict, font_dict):
        # Determine colors based on tile status
        if self.is_selected or self.is_line:
            fill_color = color_dict['line_hex']
            outline_color = color_dict['line_outline']
            label_color = color_dict['line_label']
        elif self.continent_label is not None:
            fill_color = self.grid.continent_colors[self.continent_label]
            outline_color = color_dict['default_outline']
            label_color = color_dict['default_label']
        elif self.plate_index is not None:
            fill_color = self.grid.plate_colors[self.plate_index]
            outline_color = color_dict['default_outline']
            label_color = color_dict['default_label']
        else:
            fill_color = color_dict['default_hex']
            outline_color = color_dict['default_outline']
            label_color = color_dict['default_label']

        # Get transformed corners
        world_corners = self.get_corners()
        screen_corners = [camera.world_to_screen(corner) for corner in world_corners]

        # Draw filled hexagon
        pygame.draw.polygon(screen, fill_color, screen_corners)
        # Draw hexagon outline
        pygame.draw.polygon(screen, outline_color, screen_corners, 2)

        # Prepare label
        label = f"({self.col},{self.row})"
        if self.continent_label is not None:
            label += f" {self.continent_label}"
        elif self.plate_index is not None:
            label += f" P{self.plate_index}"

        # Font size for labels scales with zoom
        adjusted_font_size = max(int(font_dict['base_size'] * camera.zoom), 8)
        try:
            adjusted_font = pygame.font.SysFont(font_dict['base_name'], adjusted_font_size)
        except Exception as e:
            adjusted_font = pygame.font.Font(None, adjusted_font_size)
        text_surface = adjusted_font.render(label, True, label_color)
        text_rect = text_surface.get_rect(center=camera.world_to_screen(self.center))
        screen.blit(text_surface, text_rect)

class HexGrid:
    def __init__(self, cols, rows, size, offset_x=100, offset_y=100):
        self.cols = cols
        self.rows = rows
        self.size = size
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.tiles = []
        self.continent_colors = {}
        self.plate_colors = {}
        self.generate_grid()

    def generate_grid(self):
        HEX_HEIGHT = math.sqrt(3) * self.size
        HEX_WIDTH = 2 * self.size
        VERTICAL_SPACING = HEX_HEIGHT
        HORIZONTAL_SPACING = HEX_WIDTH * 0.75  # Flat-topped hexagons overlap horizontally by 25%

        for row in range(self.rows):
            for col in range(self.cols):
                # Calculate the position of the hex center in world coordinates
                x = self.offset_x + col * HORIZONTAL_SPACING
                y = self.offset_y + row * VERTICAL_SPACING
                if col % 2 == 0:
                    y -= VERTICAL_SPACING / 2  # Shift even columns upwards
                center = (x, y)
                tile = HexTile(col, row, center, self.size, self)
                self.tiles.append(tile)

    def get_tile(self, col, row):
        if 0 <= col < self.cols and 0 <= row < self.rows:
            return self.tiles[row * self.cols + col]
        else:
            return None

    def draw(self, screen, camera, color_dict, font_dict):
        for tile in self.tiles:
            tile.draw(screen, camera, color_dict, font_dict)
