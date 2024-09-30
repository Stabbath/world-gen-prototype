import random
from collections import deque
from neighbor_functions import get_neighbors_wraparound

def generate_world(grid, cols, rows):
    grid = plate_method(grid, cols, rows) # TODO - gui's alternative would be here instead of plate_method
    
    # NOTE - if we need optimization later, smoothen and detection should be made a part of the plate_method (or fault_method)
    grid = smoothen_faults(grid, cols, rows)
    plates, faults = detect_plates_and_faults(grid, cols, rows)

    # TODO - fault line and plate properties
    # TODO - simulation of movements, creation of mountains, etc
    # TODO - creation of a secondary hexmap which stores an altitude map instead of plates. Tones of grey I guess, black is deepest, white is highest.
    
    return grid # TODO - return altitude map instead of plate map. Or possibly both.

def smoothen_faults(grid, cols, rows):
    # TODO - smoothing of disconnected plate parts. 
    return grid

def detect_plates_and_faults(grid, cols, rows):
    # TODO - detection of plates and faults
    plates = []
    faults = []
    return plates, faults

def spread_generic(cols, rows, colors, grid_colored, plate_queues, neighborsfunc, popfunc, individual_spread=True, growth_scales=None):
    """
    Spreads colors across the grid using BFS.

    Parameters:
        cols (int): Number of columns in the grid.
        rows (int): Number of rows in the grid.
        colors (List[Tuple[int, int, int]]): List of RGB color tuples representing different plates.
        grid_colored (List[Tuple[int, int, Tuple[int, int, int]]]): Grid with initial color assignments.
        plate_queues (List[deque]): Queues for each plate to manage BFS.
        neighborsfunc (function): function which takes a cell and returns an array containing its neighbors.
        popfunc (function): function which takes a list and removes and returns one of its elements
        individual_spread (boolean): if True, we process 1 tile of plate expansion per color at each iteration, rather than a neighborhood
        growth_scales (List[double]): for each plate, the probability that we skip its expansion in each iteration, causing it to expand more slowly than the others.

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

def plate_method(grid, cols, rows):
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
    popfunc = randpop
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
