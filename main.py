import pygame
import sys
import math
import random
from collections import deque

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

# Define Neighbor Offsets for Even-Q Vertical Layout
EVEN_Q_NEIGHBORS = [ 
    (+1,  0), (+1, -1), ( 0, -1),
    (-1, -1), (-1,  0), ( 0, +1)
]

ODD_Q_NEIGHBORS = [
    (+1, +1), (+1,  0), ( 0, -1),
    (-1,  0), (-1, +1), ( 0, +1)
]

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

def get_neighbors(col, row, cols, rows):
    """
    Returns a list of neighboring cells' coordinates for a given cell in an even-q vertical offset grid,
    ensuring that neighbors are within grid boundaries.

    Parameters:
        col (int): The column index of the current cell.
        row (int): The row index of the current cell.
        cols (int): Total number of columns in the grid.
        rows (int): Total number of rows in the grid.

    Returns:
        List[Tuple[int, int]]: A list of (col, row) tuples representing neighboring cells within bounds.
    """
    neighbors = []

    # Determine if the column is even or odd
    if col % 2 == 0:
        deltas = EVEN_Q_NEIGHBORS
    else:
        deltas = ODD_Q_NEIGHBORS

    # Calculate neighbor positions with boundary checks
    for dc, dr in deltas:
        neighbor_col = col + dc
        neighbor_row = row + dr

        # Check if neighbor is within grid boundaries
        if 0 <= neighbor_col < cols and 0 <= neighbor_row < rows:
            neighbors.append((neighbor_col, neighbor_row))

    return neighbors

def generate_offset_grid(cols, rows):
    """
    Generates a list of grid cells as (col, row) tuples.

    Parameters:
        cols (int): Number of columns.
        rows (int): Number of rows.

    Returns:
        List[Tuple[int, int]]: List of (col, row) tuples.
    """
    grid = []
    for row in range(rows):
        for col in range(cols):
            grid.append((col, row))
    return grid

def get_neighbors_wraparound(col, row, cols, rows):
    """
    Returns a list of neighboring cells' coordinates for a given cell in an even-q vertical offset grid,
    with horizontal wraparound.

    Parameters:
        col (int): The column index of the current cell.
        row (int): The row index of the current cell.
        cols (int): Total number of columns in the grid.
        rows (int): Total number of rows in the grid.

    Returns:
        List[Tuple[int, int]]: A list of (col, row) tuples representing neighboring cells with horizontal wraparound.
    """
    neighbors = []

    # Determine if the column is even or odd
    if col % 2 == 0:
        deltas = EVEN_Q_NEIGHBORS
    else:
        deltas = ODD_Q_NEIGHBORS

    # Calculate neighbor positions with wraparound for columns
    for dc, dr in deltas:
        # Wrap the column index
        neighbor_col = (col + dc) % cols
        neighbor_row = row + dr

        # Check if the neighbor row is within bounds
        if 0 <= neighbor_row < rows:
            neighbors.append((neighbor_col, neighbor_row))

    return neighbors

def spread_generic(cols, rows, colors, grid_colored, plate_queues, neighborsfunc, popfunc, individual_spread=True, growth_scales=None):
    """
    Spreads colors across the grid using BFS, allowing horizontal wraparound.

    Parameters:
        cols (int): Number of columns in the grid.
        rows (int): Number of rows in the grid.
        colors (List[Tuple[int, int, int]]): List of RGB color tuples representing different plates.
        grid_colored (List[Tuple[int, int, Tuple[int, int, int]]]): Grid with initial color assignments.
        plate_queues (List[deque]): Queues for each plate to manage BFS.

    Returns:
        List[Tuple[int, int, Tuple[int, int, int]]]: Updated grid with colors spread across it.
    """
    # Spread colors using BFS for each plate with horizontal wraparound
    plates_active = len(colors)  # Number of plates still spreading

    while plates_active > 0:
        for i, color in enumerate(colors):
            if not plate_queues[i]:
                continue  # Plate has no more cells to spread to
                
            # Statistical growth scale - % chance to grow or not grow each iteration
            if growth_scales is not None:
                if random.random() > growth_scales[i]:
                    continue

            if individual_spread:
                current_cell = popfunc(plate_queues[i])
                current_col, current_row = current_cell
                current_idx = current_row * cols + current_col
                
                # If not colored yet, assign the plate's color to the cell
                if grid_colored[current_idx][2] is None:
                    grid_colored[current_idx] = (current_col, current_row, color)

                    # Get its neighbors, add them to the queue
                    neighbors = neighborsfunc(current_col, current_row, cols, rows)
                    for neighbor_col, neighbor_row in neighbors:
                        plate_queues[i].append((neighbor_col, neighbor_row))
            else:
                for _ in range(len(plate_queues[i])):
                    current_cell = popfunc(plate_queues[i])
                    current_col, current_row = current_cell
                    current_idx = current_row * cols + current_col
                    
                    # If not colored yet, assign the plate's color to the cell
                    if grid_colored[current_idx][2] is None:
                        grid_colored[current_idx] = (current_col, current_row, color)
    
                        # Get its neighbors, add them to the queue
                        neighbors = neighborsfunc(current_col, current_row, cols, rows)
                        for neighbor_col, neighbor_row in neighbors:
                            plate_queues[i].append((neighbor_col, neighbor_row))
                

            # Check if the plate's queue is empty after spreading
            if not plate_queues[i]:
                plates_active -= 1

    return grid_colored

def assign_colors(grid, cols, rows):
    """
    Assigns colors to the grid cells simulating tectonic plate spreading.

    Parameters:
        grid (List[Tuple[int, int]]): List of grid cells as (col, row) tuples.
        cols (int): Number of columns.
        rows (int): Number of rows.

    Returns:
        List[Tuple[int, int, tuple]]: List of (col, row, color) tuples.
    """
    # Define colors representing tectonic plates
    colors = [
        (255, 0, 0),       # Red
        (0, 255, 0),       # Green
        (0, 0, 255),       # Blue
        (255, 255, 0),     # Yellow
        (255, 0, 255),     # Magenta
        (0, 255, 255),     # Cyan
        (255, 165, 0),     # Orange
        (128, 0, 128),     # Purple
        (0, 128, 0),       # Dark Green
        (128, 128, 0),     # Olive
        (0, 0, 128),       # Navy
        (255, 192, 203),   # Pink
    ]

    # Initialize grid with no colors
    grid_colored = [ (col, row, None) for (col, row) in grid ]

    # Initialize neighbors queues for each plate
    plate_queues = [ deque() for _ in range(len(colors)) ]

    # Add seed position for each plate to its queue
    for i, color in enumerate(colors):
        while True:
            rand_col = random.randint(0, cols - 1)
            rand_row = random.randint(0, rows - 1)
            rand_idx = rand_row * cols + rand_col
            if grid_colored[rand_idx][2] is None:
                plate_queues[i].append((rand_col, rand_row))
                break  # Ensure unique initial seeds

    def leftpop(l):
        return l.popleft()

    def randpop(l):
        rand_index = random.randint(0, len(l) - 1)
        value = l[rand_index]
        del l[rand_index]
        return value
        
    neighbors_func = get_neighbors_wraparound # or get_neighbors
    popfunc = leftpop
    individual_spread = False
    growth_scales = None # [1.0] * 8 + [0.5] * 4
    
    return spread_generic(cols, rows, colors, grid_colored, plate_queues, neighbors_func, popfunc, individual_spread, growth_scales)
        # TODO - an idea for another mode - generate extra plates, then merge some of them at random until we're down to the desired number
        # TODO - another idea: as something of a replacement for scale: breakout plates. Create small plates expanding outward from some fault line into other plates. To simulate things like Juan de Fuca.
        
        
    # TODO - detect all fault lines, assign a fault type to each one
    # TODO - simulate the movements of our plates for a while and deform them appropriately on a 2D plane still
    # TODO - then level it up to a 3D plane, so we can add subduction etc and make tectonic mountains and pits
    # TODO - then add hot spots, volcanoes, and any other such extras. Maybe meteor craters too.
    #   And that will conclude our Topology. It could however be developed further by for example defining oceanic vs continental plates, or rock composition (and density), or plate age.
    #   - Step 2 would then be seas, oceans, rivers, lakes. Probably in conjunction with climate. For now, assume sea level is universally the same, ignore tides and tide differences between seas and stuff.
    #   - Step 3 would be climate, if not already done. But I think that goes hand in hand with 2.
    #   - Step 4 would then be erosion, finetuning topology based on the effect of climate.
    #   And that would conclude our Geology. I think. Afterwards, we can tackle civilizational simulation.
        
def get_color(color):
    """
    Returns the RGB color tuple.

    Parameters:
        color (tuple): RGB color.

    Returns:
        tuple: RGB color.
    """
    return color if color else (255, 255, 255)  # Default to white if no color

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

def main():
    # Hexagon size
    size = 20  # Adjust size as needed

    # Grid dimensions
    cols = 200  # Number of columns
    rows = 200  # Number of rows

    # Generate and assign colors to the grid
    grid = generate_offset_grid(cols, rows)
    grid = assign_colors(grid, cols, rows)

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
        for cell in grid:
            col, row, color = cell
            pixel = offset_to_pixel(col, row, size, camera_offset, scale)
            if is_visible(pixel, size * scale, SCREEN_WIDTH, SCREEN_HEIGHT):
                hex_color = get_color(color)
                draw_hexagon(screen, hex_color, pixel, size * scale, width=0)

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
