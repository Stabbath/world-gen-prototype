import math
import pygame

def color_generator(index):
    # Total combinations: 6x7 = 42. Change this if the multipliers array is changed
    if index >= 30:
        return (255, 255, 255) # return White if out of bounds
        
    matrices = [
        [(1,0,0),(0,0,0)],
        [(0,1,0),(0,0,0)],
        [(0,0,1),(0,0,0)],
        [(1,0,0),(0,1,0)],
        [(1,0,0),(0,0,1)],
        [(0,1,0),(0,0,1)]
    ]
    
    multipliers = [
        (255, 255),
        (128, 128),
        (255, 165),
        (165, 255),
        (192, 96),
        (96, 192),
        (128, 128)
    ]

    # Calculate sub-indices directly from the provided index
    matrix_index = index % len(matrices)
    index = index // len(matrices)

    multipliers_index = index

    matrix = matrices[matrix_index]
    multipliers = multipliers[multipliers_index]
    
    # Compute the color using the selected matrices and multipliers
    color = [
        matrix[0][i] * multipliers[0] + matrix[1][i] * multipliers[1]
        for i in range(3)
    ]
    
    return color

class HexViewTile:
    is_selected = False
    
    def __init__(self, tile, center, size, gridview):
        self.tile = tile
        self.center = pygame.math.Vector2(center)
        self.size = size
        self.gridview = gridview

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
        if self.is_selected or self.tile.is_line:
            fill_color = color_dict['line_hex']
            outline_color = color_dict['line_outline']
            label_color = color_dict['line_label']
        elif self.tile.continent_label is not None:
            fill_color = self.gridview.grid.continent_colors[self.tile.continent_label] # TODO - should just one color array/fetch function. Check with Gui what his goal with this specific colour scheme was.
            outline_color = color_dict['default_outline']
            label_color = color_dict['default_label']
        elif self.tile.plate_index is not None:
            fill_color = color_generator(self.tile.plate_index)
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
    
        # # Prepare label
        # label = f"({self.tile.col},{self.tile.row})"
        # if self.tile.continent_label is not None:
        #     label += f" {self.tile.continent_label}"
        # elif self.tile.plate_index is not None:
        #     label += f" P{self.tile.plate_index}"
    
        # # Font size for labels scales with zoom
        # adjusted_font_size = max(int(font_dict['base_size'] * camera.zoom), 8)
        # try:
        #     adjusted_font = pygame.font.SysFont(font_dict['base_name'], adjusted_font_size)
        # except:
        #     adjusted_font = pygame.font.Font(None, adjusted_font_size)
        # text_surface = adjusted_font.render(label, True, label_color)
        # text_rect = text_surface.get_rect(center=camera.world_to_screen(self.center))
        # screen.blit(text_surface, text_rect)
        

class HexView:
    def __init__(self, hexgrid, size, offset_x=100, offset_y=100):
        self.grid = hexgrid
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.size = size
        HEX_HEIGHT = math.sqrt(3) * self.size
        HEX_WIDTH = 2 * self.size
        VERTICAL_SPACING = HEX_HEIGHT
        HORIZONTAL_SPACING = HEX_WIDTH * 0.75  # Flat-topped hexagons overlap horizontally by 25%

        self.tiles = [
            HexViewTile(
                tile,
                (
                    self.offset_x + tile.col * HORIZONTAL_SPACING,
                    (self.offset_y + tile.row * VERTICAL_SPACING) 
                    - (VERTICAL_SPACING / 2 if tile.col % 2 == 0 else 0)
                ),
                size,
                self
            )
            for tile in hexgrid.tiles
        ]
        
    def draw(self, screen, camera, color_dict, font_dict):
        for tile in self.tiles:
            tile.draw(screen, camera, color_dict, font_dict)
        
