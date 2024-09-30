import pygame
def handle_zoom(event, size):
    """Adjust the hex size based on zoom input"""
    if event.type == pygame.MOUSEWHEEL:
        if event.y > 0:  # Zoom in
            size += 5
        elif event.y < 0:  # Scroll down, zoom out
            size = max(5, size - 5)  # Prevent hex size from being too small
    return size