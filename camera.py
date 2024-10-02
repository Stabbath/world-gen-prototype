import pygame
# ------------------------------
# Camera Class Definition
# ------------------------------

class Camera:
    def __init__(self, zoom=1.0, offset=(0, 0), min_zoom=0.5, max_zoom=3.0):
        """
        Initialize the Camera.

        :param zoom: Initial zoom factor
        :param offset: Initial offset (x, y)
        """
        self.zoom = zoom
        self.offset = pygame.math.Vector2(offset)
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom

    def world_to_screen(self, pos):
        """
        Convert world coordinates to screen coordinates based on zoom and offset.

        :param pos: Tuple (x, y) in world coordinates
        :return: Tuple (x, y) in screen coordinates
        """
        return (
            (pos[0] * self.zoom) + self.offset.x,
            (pos[1] * self.zoom) + self.offset.y
        )

    def adjust_zoom(self, zoom_change, mouse_pos):
        """
        Adjust the zoom factor and offset to zoom centered around the mouse position.

        :param zoom_change: Factor to adjust the zoom (e.g., 1.1 for zooming in)
        :param mouse_pos: Tuple (x, y) of the mouse position in screen coordinates
        """
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
