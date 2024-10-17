import pygame

class Camera:
    def __init__(self, zoom=1.0, offset=(0, 0), min_zoom=0.5, max_zoom=3.0):
        self.zoom = zoom
        self.offset = pygame.math.Vector2(offset)
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom

    def world_to_screen(self, pos):
        return (
            (pos[0] * self.zoom) + self.offset.x,
            (pos[1] * self.zoom) + self.offset.y
        )
    
    def screen_to_world(self, pos):
        return (
            (pos[0] - self.offset.x)/self.zoom,
            (pos[1] - self.offset.y)/self.zoom
        )

    def adjust_zoom(self, zoom_change, mouse_pos):
        # Calculate the world coordinates before zoom
        world_x_before = (mouse_pos[0] - self.offset.x) / self.zoom
        world_y_before = (mouse_pos[1] - self.offset.y) / self.zoom

        # Adjust zoom
        new_zoom = self.zoom * zoom_change
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))  # Clamp zoom

        # Update zoom
        self.zoom = new_zoom

        # Calculate the world coordinates after zoom
        world_x_after = (mouse_pos[0] - self.offset.x) / self.zoom
        world_y_after = (mouse_pos[1] - self.offset.y) / self.zoom

        # Adjust offset to keep the point under the mouse stationary
        self.offset.x += (world_x_after - world_x_before) * self.zoom
        self.offset.y += (world_y_after - world_y_before) * self.zoom
