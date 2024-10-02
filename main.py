import pygame
import sys
import math

from hexgrid import HexGrid
from tectonic_generator import generate_world

# Initialize Pygame
pygame.init()

# Define screen dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hexagonal Grid World with Zoom and Pan")

# Clock for controlling frame rate
clock = pygame.time.Clock()
FPS = 60


def hex_corner(center, size, i):
    """
    Calculate the corner position of a hexagon.

    Parameters:
        center (tuple): (x, y) position of the hexagon center.
        size (float): Size (radius) of the hexagon.
        i (int): Corner index (0 to 5).

    Returns:
        tuple: (x, y) position of the corner.
    """
    angle_deg = 60 * i + 30  # Adjusted for pointy-topped hexagons
    angle_rad = math.radians(angle_deg)
    return (
        center[0] + size * math.cos(angle_rad),
        center[1] + size * math.sin(angle_rad),
    )

def draw_hexagon(surface, color, position, size, width=0):
    """
    Draw a single hexagon on the surface.

    Parameters:
        surface (pygame.Surface): The surface to draw on.
        color (tuple): RGB color of the hexagon.
        position (tuple): (x, y) position of the hexagon center.
        size (float): Size (radius) of the hexagon.
        width (int): Border width. 0 for filled hexagon.
    """
    corners = [hex_corner(position, size, i) for i in range(6)]
    pygame.draw.polygon(surface, color, corners, width)

def offset_to_pixel(col, row, size, camera_offset, scale):
    """
    Converts even-q offset coordinates to pixel positions with camera transformations.

    Parameters:
        col (int): Column index.
        row (int): Row index.
        size (float): Size (radius) of the hexagon.
        camera_offset (list): [x_offset, y_offset] for panning.
        scale (float): Zoom scale.

    Returns:
        tuple: (x, y) pixel position.
    """
    x = size * math.sqrt(3) * (col + 0.5 * (row & 1))
    y = size * 1.5 * row
    # Apply camera transformations
    x = x * scale + camera_offset[0]
    y = y * scale + camera_offset[1]
    return (x, y)

def pixel_to_offset(x, y, size, camera_offset, scale, cols, rows):
    """
    Converts pixel positions back to even-q offset coordinates.

    Parameters:
        x (float): X position in pixels.
        y (float): Y position in pixels.
        size (float): Size (radius) of the hexagon.
        camera_offset (list): [x_offset, y_offset] for panning.
        scale (float): Zoom scale.
        cols (int): Total number of columns.
        rows (int): Total number of rows.

    Returns:
        tuple: (col, row) coordinates.
    """
    # Adjust for camera
    x = (x - camera_offset[0]) / scale
    y = (y - camera_offset[1]) / scale

    q = (x * math.sqrt(3)/3 - y / 3)
    r = y * 2/3

    # Round to nearest hex
    q_round = round(q)
    r_round = round(r)
    s_round = round(-q - r)

    q_diff = abs(q_round - q)
    r_diff = abs(r_round - r)
    s_diff = abs(s_round - (-q - r))

    if q_diff > r_diff and q_diff > s_diff:
        q_round = -r_round - s_round
    elif r_diff > s_diff:
        r_round = -q_round - s_round
    else:
        s_round = -q_round - r_round

    col = q_round
    row = r_round + (q_round - (q_round & 1)) // 2

    # Clamp to grid boundaries
    col = max(0, min(cols - 1, col))
    row = max(0, min(rows - 1, row))

    return (col, row)

def is_visible(pixel, size, screen_width, screen_height):
    """
    Checks if a hexagon is within the visible screen area with a buffer.

    Parameters:
        pixel (tuple): (x, y) pixel position of the hexagon center.
        size (float): Size (radius) of the hexagon.
        screen_width (int): Width of the screen.
        screen_height (int): Height of the screen.

    Returns:
        bool: True if visible, False otherwise.
    """
    x, y = pixel
    buffer = size * 2
    return (-buffer < x < screen_width + buffer) and (-buffer < y < screen_height + buffer)

def plate_to_color(plate_index):
    # Define colors representing tectonic plates
    colors = [
        (255, 0, 0),       # Red - 1
        (0, 255, 0),       # Green
        (0, 0, 255),       # Blue
        (255, 255, 0),     # Yellow
        (255, 0, 255),     # Magenta
        (0, 255, 255),     # Cyan
        (128, 0, 0),       # ?
        (0, 128, 0),       # Dark Green
        (0, 0, 128),       # Navy
        (128, 128, 0),     # Olive - 10
        (128, 0, 128),     # Purple
        (0, 128, 128),     # ?
        (255, 165, 0),     # Orange
        (255, 0, 165),     # ?
        (165, 255, 0),     # ?
        (0, 255, 165),     # ?
        (165, 0, 255),     # ?
        (0, 165, 255),     # ?
        (255, 192, 203),   # Pink- 19
    ]
    return colors[plate_index]


def main():
    # Hexagon size
    size = 20  # Adjust size as needed

    # Grid dimensions
    cols = 200  # Number of columns
    rows = 200  # Number of rows

    # Generate and assign colors to the grid
    grid = HexGrid(cols, rows)
    grid = generate_world(grid)

    # Camera parameters
    camera_offset = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]  # Start at center
    scale = 1.0  # Initial zoom level
    dragging = False
    last_mouse_pos = (0, 0)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    dragging = True
                    last_mouse_pos = event.pos
                elif event.button == 4:  # Mouse wheel up
                    # Zoom in
                    scale *= 1.1
                    # Adjust camera to zoom towards mouse position
                    mouse_x, mouse_y = event.pos
                    camera_offset[0] = mouse_x - (mouse_x - camera_offset[0]) * 1.1
                    camera_offset[1] = mouse_y - (mouse_y - camera_offset[1]) * 1.1
                elif event.button == 5:  # Mouse wheel down
                    # Zoom out
                    scale /= 1.1
                    # Adjust camera to zoom towards mouse position
                    mouse_x, mouse_y = event.pos
                    camera_offset[0] = mouse_x - (mouse_x - camera_offset[0]) / 1.1
                    camera_offset[1] = mouse_y - (mouse_y - camera_offset[1]) / 1.1

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    dx = event.pos[0] - last_mouse_pos[0]
                    dy = event.pos[1] - last_mouse_pos[1]
                    camera_offset[0] += dx
                    camera_offset[1] += dy
                    last_mouse_pos = event.pos

        # Fill screen with background color
        screen.fill((0, 0, 0))  # Black background

        # Draw hexagons
        for cell in grid.get_tiles():
            row, col = cell.get_coords() # bandaid fix for wrong neighbors
            color = plate_to_color(cell.get_plate_index())
            pixel = offset_to_pixel(col, row, size, camera_offset, scale)
            if is_visible(pixel, size * scale, SCREEN_WIDTH, SCREEN_HEIGHT):
                draw_hexagon(screen, color, pixel, size * scale, width=0)

        # Optionally, display current zoom level
        font = pygame.font.SysFont(None, 24)
        zoom_text = font.render(f'Zoom: {scale:.2f}x', True, (255, 255, 255))
        screen.blit(zoom_text, (10, 10))

        # Update the display
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
