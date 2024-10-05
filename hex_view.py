import math
import pygame

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
            fill_color = self.gridview.grid.continent_colors[self.tile.continent_label]
            outline_color = color_dict['default_outline']
            label_color = color_dict['default_label']
        elif self.tile.plate_index is not None:
            fill_color = self.gridview.grid.plate_colors[self.tile.plate_index]
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
        
