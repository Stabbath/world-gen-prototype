import random
from collections import deque, defaultdict
from typing import List, Tuple, Dict, Set

from neighbor_functions import get_neighbors_wraparound

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

def generate_world(grid, cols, rows):
    grid = plate_method(grid, cols, rows) # TODO - gui's alternative would be here instead of plate_method
    
    # NOTE - if we need optimization later, smoothen and detection should be made a part of the plate_method (or fault_method)
    grid, plates, faults = detect_plates_and_faults(grid, cols, rows)

    # TODO - fault line and plate properties
    # TODO - simulation of movements, creation of mountains, etc
    # TODO - creation of a secondary hexmap which stores an altitude map instead of plates. Tones of grey I guess, black is deepest, white is highest.
    
    return grid # TODO - return altitude map instead of plate map. Or possibly both.


def detect_plates_and_faults(grid: List[Tuple[int, int, Tuple[int, int, int]]],
                             cols: int,
                             rows: int) -> Tuple[List[Dict], List[Dict]]:
    """
    Detects tectonic plates and fault lines in a hexagonal grid.

    Parameters:
        grid (List[Tuple[int, int, Tuple[int, int, int]]]):
            The grid represented as a list where each element is a tuple:
            (column, row, color), where color is an RGB tuple.
        cols (int):
            Number of columns in the grid.
        rows (int):
            Number of rows in the grid.

    Returns:
        Tuple[List[Dict], List[Dict]]:
            - plates: A list of dictionaries, each representing a plate with its properties.
            - faults: A list of dictionaries, each representing a fault line with its properties.
    """
    
    def group_plates(grid: List[Tuple[int, int, Tuple[int, int, int]]],
                    cols: int,
                    rows: int,
                    get_neighbors) -> Tuple[List[Dict], Dict[Tuple[int, int], int]]:
        """
        Groups contiguous cells of the same color into plates using BFS.

        Parameters:
            grid (List[Tuple[int, int, Tuple[int, int, int]]]):
                The grid represented as a list of tuples.
            cols (int): Number of columns.
            rows (int): Number of rows.
            get_neighbors (Callable): Function to get neighbors of a cell.

        Returns:
            Tuple[List[Dict], Dict[Tuple[int, int], int]]:
                - plates: List of plate dictionaries.
                - cell_to_plate: Mapping from cell coordinates to plate indices.
        """
        plates = []
        cell_to_plate = {}
        visited = set()

        for idx, cell in enumerate(grid):
            col, row, color = cell
            if (col, row) in visited:
                continue
            # Initialize BFS
            plate_cells = set()
            queue = deque()
            queue.append((col, row))
            visited.add((col, row))
            while queue:
                current_col, current_row = queue.popleft()
                plate_cells.add((current_col, current_row))
                for neighbor in get_neighbors(current_col, current_row, cols, rows):
                    n_col, n_row = neighbor
                    n_idx = n_row * cols + n_col
                    n_cell = grid[n_idx]
                    n_color = n_cell[2]
                    if n_color == color and (n_col, n_row) not in visited:
                        visited.add((n_col, n_row))
                        queue.append((n_col, n_row))
            # Add the discovered plate
            plate = {
                'cells': plate_cells,
                'color': color,
                'boundary_cells': set(),
                'faults': set()
            }
            plates.append(plate)
            # Map cells to plate index
            plate_index = len(plates) - 1
            for cell_coord in plate_cells:
                cell_to_plate[cell_coord] = plate_index
        return plates, cell_to_plate

    def remove_smallest_plates(grid: List[Tuple[int, int, Tuple[int, int, int]]],
                               plates: List[Dict],
                               cell_to_plate: Dict[Tuple[int, int], int],
                               cols: int,
                               rows: int,
                               get_neighbors) -> List[Tuple[int, int, Tuple[int, int, int]]]:
        """
        Removes all but the largest plate for each color and reassigns colors of removed plates.

        Parameters:
            grid (List[Tuple[int, int, Tuple[int, int, int]]]):
                The grid represented as a list of tuples.
            plates (List[Dict]): List of plate dictionaries.
            cell_to_plate (Dict[Tuple[int, int], int]): Mapping from cell to plate index.
            cols (int): Number of columns.
            rows (int): Number of rows.
            get_neighbors (Callable): Function to get neighbors of a cell.

        Returns:
            List[Tuple[int, int, Tuple[int, int, int]]]: Updated grid after plate removal.
        """
        # Group plates by color
        color_to_plates = defaultdict(list)
        for i, plate in enumerate(plates):
            color_to_plates[plate['color']].append(i)
        
        # Identify plates to remove (all but the largest plate per color)
        plates_to_remove = []
        for color, plate_indices in color_to_plates.items():
            if len(plate_indices) <= 1:
                continue  # Only one plate for this color
            # Sort plate indices by size in descending order
            sorted_plate_indices = sorted(plate_indices, key=lambda x: len(plates[x]['cells']), reverse=True)
            # Keep the largest plate, remove the rest
            plates_to_remove.extend(sorted_plate_indices[1:])
        
        # Remove identified plates by reassigning their cell colors
        for plate_idx in plates_to_remove:
            plate = plates[plate_idx]
            plate_color = plate['color']
            for cell in plate['cells']:
                col, row = cell
                neighbors = get_neighbors(col, row, cols, rows)
                neighbor_colors = []
                for n_col, n_row in neighbors:
                    n_idx = n_row * cols + n_col
                    n_color = grid[n_idx][2]
                    if n_color is not None and n_color != plate_color:
                        neighbor_colors.append(n_color)
                if neighbor_colors:
                    # Assign a random neighboring color different from the current plate's color
                    new_color = random.choice(neighbor_colors)
                else:
                    # If no neighbor has a different color, retain the same color to avoid isolated cells
                    new_color = plate_color
                # Update the grid with the new color
                grid_idx = row * cols + col
                grid[grid_idx] = (col, row, new_color)
                # Remove the cell from cell_to_plate mapping
                del cell_to_plate[cell]
        
        return grid

    def regroup_plates(grid: List[Tuple[int, int, Tuple[int, int, int]]],
                      cols: int,
                      rows: int,
                      get_neighbors) -> Tuple[List[Dict], Dict[Tuple[int, int], int]]:
        """
        Regroups plates after color reassignment.

        Parameters:
            grid (List[Tuple[int, int, Tuple[int, int, int]]]):
                The grid after plate removal.
            cols (int): Number of columns.
            rows (int): Number of rows.
            get_neighbors (Callable): Function to get neighbors of a cell.

        Returns:
            Tuple[List[Dict], Dict[Tuple[int, int], int]]:
                - plates: Updated list of plate dictionaries.
                - cell_to_plate: Updated mapping from cell coordinates to plate indices.
        """
        return group_plates(grid, cols, rows, get_neighbors)

    def identify_faults(plates: List[Dict],
                       cell_to_plate: Dict[Tuple[int, int], int],
                       get_neighbors,
                       cols: int,
                       rows: int) -> List[Dict]:
        """
        Identifies fault lines (borders) between different plates.

        Parameters:
            plates (List[Dict]): List of plate dictionaries.
            cell_to_plate (Dict[Tuple[int, int], int]): Mapping from cell to plate index.
            get_neighbors (Callable): Function to get neighbors of a cell.
            cols (int): Number of columns.
            rows (int): Number of rows.

        Returns:
            List[Dict]: List of fault dictionaries.
        """
        # Dictionary to map plate pairs to their fault cells
        plate_pair_to_fault_cells = defaultdict(set)
        
        for plate_idx, plate in enumerate(plates):
            for cell in plate['cells']:
                col, row = cell
                neighbors = get_neighbors(col, row, cols, rows)
                for n_col, n_row in neighbors:
                    neighbor_coord = (n_col, n_row)
                    neighbor_plate_idx = cell_to_plate.get(neighbor_coord)
                    if neighbor_plate_idx is None:
                        continue  # Skip if neighbor is not part of any plate
                    if neighbor_plate_idx != plate_idx:
                        # Create a sorted tuple of plate indices to ensure uniqueness
                        plate_pair = tuple(sorted([plate_idx, neighbor_plate_idx]))
                        # Store the cell pair as a tuple (sorted to avoid duplicates)
                        fault_pair = tuple(sorted([cell, neighbor_coord]))
                        plate_pair_to_fault_cells[plate_pair].add(fault_pair)
        
        faults = []
        # Set to keep track of already processed plate pairs
        processed_plate_pairs = set()
        
        for plate_pair, fault_pairs in plate_pair_to_fault_cells.items():
            if plate_pair in processed_plate_pairs:
                continue  # Already processed this plate pair
            # Create a fault entry
            fault = {
                'cells': set(),
                'plates': plate_pair
            }
            for pair in fault_pairs:
                fault['cells'].add(pair[0])
                fault['cells'].add(pair[1])
            faults.append(fault)
            # Assign fault index
            fault_index = len(faults) - 1
            plate_a, plate_b = plate_pair
            # Assign fault to both plates
            plates[plate_a]['faults'].add(fault_index)
            plates[plate_b]['faults'].add(fault_index)
            # Assign boundary cells to both plates
            for pair in fault_pairs:
                plates[plate_a]['boundary_cells'].add(pair[0])
                plates[plate_a]['boundary_cells'].add(pair[1])
                plates[plate_b]['boundary_cells'].add(pair[0])
                plates[plate_b]['boundary_cells'].add(pair[1])
            # Mark this plate pair as processed
            processed_plate_pairs.add(plate_pair)
        
        return faults

    # Step 1: Initial grouping of plates
    initial_plates, initial_cell_to_plate = group_plates(grid, cols, rows, neighbors_func)
    
    # Step 2: Remove smaller plates and reassign colors
    updated_grid = remove_smallest_plates(grid, initial_plates, initial_cell_to_plate, cols, rows, neighbors_func)
    
    # Step 3: Regroup plates after color reassignment
    final_plates, final_cell_to_plate = regroup_plates(updated_grid, cols, rows, neighbors_func)
    
    # Step 4: Identify fault lines between plates
    fault_lines = identify_faults(final_plates, final_cell_to_plate, neighbors_func, cols, rows)
    
    return updated_grid, final_plates, fault_lines


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
