# file: tectonic_generator.py
import random
from collections import deque, defaultdict
from neighbor_functions import get_neighbors_wraparound

# Define constant for white color
WHITE = (255, 255, 255)

def leftpop(l):
    return l.popleft()

def randpop(l):
    rand_index = random.randint(0, len(l) - 1)
    value = l[rand_index]
    del l[rand_index]
    return value
    
neighbors_func = get_neighbors_wraparound  # or get_neighbors
popfunc = randpop
individual_spread = False
growth_scales = None  # [1.0] * 8 + [0.5] * 4

def generate_world(grid, cols, rows):
    grid = plate_method(grid, cols, rows)  # TODO - gui's alternative would be here instead of plate_method
    
    # NOTE - if we need optimization later, smoothen and detection should be made a part of the plate_method (or fault_method)
    grid, plates, faults = detect_plates_and_faults(grid, cols, rows)

    # TODO - fault line and plate properties
    # TODO - simulation of movements, creation of mountains, etc
    # TODO - creation of a secondary hexmap which stores an altitude map instead of plates. Tones of grey I guess, black is deepest, white is highest.
    
    return grid  # TODO - return altitude map instead of plate map. Or possibly both.

def detect_plates_and_faults(grid_colored, cols, rows):
    """
    Detects connected plates and fault lines, ensuring that each color represents a single connected plate.
    Recolors any disconnected clusters to white.

    Parameters:
        grid_colored (List[Tuple[int, int, Tuple[int, int, int]]]): Grid with color assignments as (row, col, color).
        cols (int): Number of columns in the grid.
        rows (int): Number of rows in the grid.

    Returns:
        Tuple[List[Tuple[int, int, Tuple[int, int, int]]], List[Set[Tuple[int, int]]], List[Set[Tuple[Tuple[int, int], Tuple[int, int]]]]]:
            - Updated grid with corrected color assignments.
            - List of plates, each represented as a set of (row, col) tuples.
            - List of faults, each represented as a set of boundary cell pairs.
    """
    # Step 1: Convert grid_colored to a 2D grid for easier access
    grid = [[None for _ in range(cols)] for _ in range(rows)]
    for cell in grid_colored:
        row, col, color = cell  # Changed order to (row, col, color)
        grid[row][col] = color

    # Step 2: Find all unique colors
    color_to_cells = defaultdict(set)
    for row in range(rows):
        for col in range(cols):
            color = grid[row][col]
            color_to_cells[color].add((row, col))  # Store as (row, col)

    # Step 3: For each color, find connected components
    plates = []  # List of sets, each set contains (row, col) tuples
    color_plate_mapping = defaultdict(list)  # color -> list of plate indices

    for color, cells in color_to_cells.items():
        if color == WHITE:
            continue  # Skip white cells if they already exist

        visited = set()
        clusters = []
        for cell in cells:
            if cell not in visited:
                # Perform BFS to find all connected cells of this color
                cluster = set()
                queue = deque()
                queue.append(cell)
                visited.add(cell)
                while queue:
                    current = queue.popleft()
                    cluster.add(current)
                    neighbors = neighbors_func(current[1], current[0], cols, rows)  # (col, row)
                    for neighbor in neighbors:
                        neighbor_row, neighbor_col = neighbor[1], neighbor[0]  # Convert to (row, col)
                        if grid[neighbor_row][neighbor_col] == color and (neighbor_row, neighbor_col) not in visited:
                            visited.add((neighbor_row, neighbor_col))
                            queue.append((neighbor_row, neighbor_col))
                clusters.append(cluster)
        
        # Identify the largest cluster to retain the original color
        if not clusters:
            continue
        clusters.sort(key=lambda x: len(x), reverse=True)
        primary_cluster = clusters[0]
        plates.append(primary_cluster)
        primary_plate_index = len(plates) - 1
        color_plate_mapping[color].append(primary_plate_index)

        # Recolor smaller clusters to white
        for cluster in clusters[1:]:
            for cell in cluster:
                row, col = cell
                grid[row][col] = WHITE  # Recolor to white
            # Optionally, you can keep track of these recolored clusters if needed
            # plates.append(cluster)  # Not adding white regions as separate plates

    # Step 4: Reconstruct grid_colored
    updated_grid_colored = []
    for row in range(rows):
        for col in range(cols):
            updated_grid_colored.append((row, col, grid[row][col]))  # (row, col, color)

    # Step 5: Identify fault lines (boundaries between plates)
    faults = []
    fault_pairs = set()
    for row in range(rows):
        for col in range(cols):
            current_color = grid[row][col]
            neighbors = neighbors_func(col, row, cols, rows)  # (col, row)
            for neighbor in neighbors:
                neighbor_col, neighbor_row = neighbor
                neighbor_color = grid[neighbor_row][neighbor_col]
                if neighbor_color != current_color:
                    # Create a sorted tuple to avoid duplicate pairs
                    pair = tuple(sorted([ (row, col), (neighbor_row, neighbor_col) ]))
                    fault_pairs.add(pair)
    # Convert fault_pairs to list of sets
    faults = [ set(pair) for pair in fault_pairs ]

    return updated_grid_colored, plates, faults

def spread_generic(cols, rows, colors, grid_colored, plate_queues, neighborsfunc, popfunc, individual_spread=True, growth_scales=None):
    """
    Spreads colors across the grid using BFS.

    Parameters:
        cols (int): Number of columns in the grid.
        rows (int): Number of rows in the grid.
        colors (List[Tuple[int, int, int]]): List of RGB color tuples representing different plates.
        grid_colored (List[Tuple[int, int, Tuple[int, int, int]]]): Grid with initial color assignments as (row, col, color).
        plate_queues (List[deque]): Queues for each plate to manage BFS.
        neighborsfunc (function): Function which takes a cell's (col, row) and returns an array containing its neighbors.
        popfunc (function): Function which takes a list and removes and returns one of its elements.
        individual_spread (boolean): If True, process 1 tile of plate expansion per color each iteration.
        growth_scales (List[double]): For each plate, the probability to skip expansion each iteration.

    Returns:
        List[Tuple[int, int, Tuple[int, int, int]]]: Updated grid with colors spread across it as (row, col, color).
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
                row, col = current_cell  # (row, col)
                current_idx = row * cols + col
                
                # If not colored yet, assign the plate's color to the cell
                if grid_colored[current_idx][2] is None:
                    grid_colored[current_idx] = (row, col, color)

                    # Get its neighbors, add them to the queue
                    neighbors = neighborsfunc(col, row, cols, rows)  # (col, row)
                    for neighbor in neighbors:
                        neighbor_col, neighbor_row = neighbor
                        plate_queues[i].append((neighbor_row, neighbor_col))  # (row, col)
            else:
                for _ in range(len(plate_queues[i])):
                    current_cell = popfunc(plate_queues[i])
                    row, col = current_cell  # (row, col)
                    current_idx = row * cols + col
                    
                    # If not colored yet, assign the plate's color to the cell
                    if grid_colored[current_idx][2] is None:
                        grid_colored[current_idx] = (row, col, color)

                        # Get its neighbors, add them to the queue
                        neighbors = neighborsfunc(col, row, cols, rows)  # (col, row)
                        for neighbor in neighbors:
                            neighbor_col, neighbor_row = neighbor
                            plate_queues[i].append((neighbor_row, neighbor_col))  # (row, col)
                

            # Check if the plate's queue is empty after spreading
            if not plate_queues[i]:
                plates_active -= 1

    return grid_colored

def plate_method(grid, cols, rows):
    """
    Assigns colors to the grid cells simulating tectonic plate spreading.

    Parameters:
        grid (List[Tuple[int, int]]): List of grid cells as (row, col) tuples.
        cols (int): Number of columns.
        rows (int): Number of rows.

    Returns:
        List[Tuple[int, int, tuple]]: List of (row, col, color) tuples.
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
    grid_colored = [ (row, col, None) for (row, col) in grid ]  # (row, col, color)

    # Initialize neighbors queues for each plate
    plate_queues = [ deque() for _ in range(len(colors)) ]

    # Add seed position for each plate to its queue
    for i, color in enumerate(colors):
        while True:
            rand_col = random.randint(0, cols - 1)
            rand_row = random.randint(0, rows - 1)
            rand_idx = rand_row * cols + rand_col
            if grid_colored[rand_idx][2] is None:
                plate_queues[i].append((rand_row, rand_col))  # (row, col)
                break  # Ensure unique initial seeds
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
