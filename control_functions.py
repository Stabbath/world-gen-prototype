import pygame
def handle_zoom(event, zoom_factor):
    """Adjust the hex size based on zoom input"""
    if event.type == pygame.MOUSEWHEEL:
        if event.y > 0:  # Zoom in
            zoom_factor *= 1.1
        elif event.y < 0:  # Scroll down, zoom out
            zoom_factor /= 1.1  # Prevent hex size from being too small
    return zoom_factor


