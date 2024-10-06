import math
import pygame
from hex_view_labels import text_label_from_tile

class HexViewTile:
    def __init__(self, tile, center, gridview):
        self.tile = tile
        self.center = pygame.math.Vector2(center)
        self.gridview = gridview

    def get_corners(self):
        # TODO can optimize this by buffering the result in a class variable and only initializing it when first called
        corners = []
        for i in range(6):
            angle_deg = 60 * i  # Flat-topped hexagons
            angle_rad = math.radians(angle_deg)
            x = self.center.x + self.gridview.size * math.cos(angle_rad)
            y = self.center.y + self.gridview.size * math.sin(angle_rad)
            corners.append((x, y))
        return corners
    
    def draw(self, screen, camera):
        # Determine colors based on tile status
        fill_color, outline_color, label_color = self.gridview.func_color(self, self.gridview.config)

        # Get transformed corners
        world_corners = self.get_corners()
        screen_corners = [camera.world_to_screen(corner) for corner in world_corners]
    
        # Draw filled hexagon
        pygame.draw.polygon(screen, fill_color, screen_corners)
        # Draw hexagon outline
        pygame.draw.polygon(screen, outline_color, screen_corners, 2)
    
        # Prepare label
        text_surface = text_label_from_tile(self.tile, label_color, camera)
        if text_surface is not None:
            text_rect = text_surface.get_rect(center=camera.world_to_screen(self.center))
            screen.blit(text_surface, text_rect)
        

class HexView:
    def __init__(self, hexgrid, size, func_color, config, offset_x=100, offset_y=100):
        self.grid = hexgrid
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.size = size
        self.func_color = func_color
        self.config = config
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
                self
            )
            for tile in hexgrid.tiles
        ]
        
    def draw(self, screen, camera):
        for tile in self.tiles:
            tile.draw(screen, camera)
        
