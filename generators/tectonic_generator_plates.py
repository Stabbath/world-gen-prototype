# file: tectonic_generator.py
import random
from collections import deque, defaultdict
from neighbor_functions import get_neighbors_wraparound
from generators.tectonic_fault_smoothing import smooth_faults
from generators.tectonic_altitude_generators import generator_consumer_model

def leftpop(l):
    return l.popleft()

def randpop(l):
    rand_index = random.randint(0, len(l) - 1)
    value = l[rand_index]
    del l[rand_index]
    return value

# TODO - move these variables into the external configurations
growth_scales = None  # [1.0] * 8 + [0.5] * 4

# TODO - add a config option once plate merging is implemented, as part of plate merging - boolean: start by merging all plates touching each pole and then exclude those plates from any more merges

# TODO - add a config option to tectonic method: turn non-wraparound edges into faults with -1 GenFactor. To force oceans at the poles.
# TODO - add a config option to tectonic method: plate properties: continental or oceanic. A continental plate gets an initial boost to its altitude to every tile. An oceanic one gets a symmetric decrease.
# ^ note i already have a similar concept written down somewhere else

# TODO - also consider a variant option for the consumer-generator model's smoothing: alternate avg() functions, like doing signed quadratic instead (x^2 but keep sign), or square root actually might be better, to spread height differences faster.

def generate_world_plates(grid, config, func_neighbors=get_neighbors_wraparound):
    individual_spread = config['plates']['individual_spread']
    plate_count = config['plates']['gen_plate_count']
    popfunc = randpop if config['plates']['random_pop'] else leftpop
    
    grid = plate_method(grid, plate_count, individual_spread, func_neighbors, popfunc)
    
    # === Step 1: Generation of Plates and Faults === 
    # TODO - if we need optimization later, detection should be made a part of the plate_method. 
    plates, faults = detect_plates_and_faults(grid, config)
    grid.set_plates_from_lists(plates)
    grid.set_faults_from_lists(faults)

    # TODO - this feels dirty just throwing it on here like this, maybe clean it up later
    for fault in grid.faults:
        fault.refresh_neighbor_groups() # we need faults to know their neighboring faults if we want to smoothen their gen factors
    
    # === Steps 2 and 3: Assignment of Plate/Fault Properties, and Elevation Map Generation ===
    # They're intimately connected, even if we can combine them differently; but the properties we assing in Step 2 define the generators we can use in Step 3.
    # So, for now, just keep them merged.
    
    # GENERATOR/CONSUMER MODEL - for now. We can possibly have different models later
    grid = generator_consumer_model(grid, config, func_neighbors)
    
    return grid
    
def detect_plates_and_faults(grid, config):
    cols = grid.width
    rows = grid.height
    
    # Step 1: Find all unique plate indices
    plate_to_cells = defaultdict(set)
    for row_idx in range(rows):
        for col_idx in range(cols):
            tile = grid.get_tile(col_idx, row_idx)
            plate = tile.get_plate_index()
            plate_to_cells[plate].add(tile)

    # Step 2: Create plates assuming each color has only one connected cluster
    plates = []
    for plate_index, cells in plate_to_cells.items():
        plates.append(cells)  # Each plate is a set of hextiles

    # Step 3: Identify and set fault lines (boundaries between plates)
    fault_tiles = set()  # To store tiles that are faults
    for plate in plates:
        # We use a list to create a static copy since we'll be modifying the plate set during iteration
        for tile in list(plate):
            neighbors = tile.get_neighbors()
            
            # Check if any neighbor belongs to a different plate
            is_border_tile = False
            for neighbor in neighbors:
                neighbor_plate = neighbor.get_plate_index()
                
                # If neighbor is a different plate and not already a fault
                if neighbor_plate != tile.get_plate_index() and neighbor_plate is not None:
                    is_border_tile = True
                    break
            
            if is_border_tile:
                plate.remove(tile)  # Remove the tile from its current plate
                fault_tiles.add(tile)  # Add the tile to the fault_tiles set
                tile.set_plate_index(None)  # Set the tile's plate index to None to mark it as a fault
    
    # Step 4: Smoothing
    # Reduce the faults to the bare minimum to separate plates.
    if config['plates']['fault_smoothing']:
        smooth_faults(fault_tiles, plate_to_cells)
        plates = list(plate_to_cells.values()) # Update plates to reflect changes

    # Step 5: Create specific fault lines from the fault tiles.
    # Each sequence of fault tiles between 2 junctions is a fault line. After smoothing, a junction is simply a fault tile with more than 2 fault tile neighbors.
    faults = []  # List to store fault lines

    # Identify fault junction tiles (tiles with more than 2 neighboring fault tiles)
    fault_junction_tiles = set()
    for tile in fault_tiles:
        fault_neighbors = [
            neighbor for neighbor in tile.get_neighbors()
            if neighbor.get_plate_index() is None
        ]
        if len(fault_neighbors) > 2:
            fault_junction_tiles.add(tile)

    assigned_tiles = set()
    faults = []

    # Process fault junction tiles
    for tile in fault_junction_tiles:
        if tile in assigned_tiles:
            continue

        # Start a new fault line
        fault_line = set()
        queue = deque()
        queue.append((tile, None))  # No parent yet
        assigned_tiles.add(tile)
        fault_line.add(tile)

        while queue:
            current_tile, parent_had_two_or_less = queue.popleft()

            current_fault_neighbors = [
                neighbor for neighbor in current_tile.get_neighbors()
                if neighbor.get_plate_index() is None
            ]
            num_current_fault_neighbors = len(current_fault_neighbors)

            # Exception: If this is the first tile in the fault, force it to add one of its neighbors
            if len(fault_line) == 1 and num_current_fault_neighbors > 2:
                # Add one of its neighbors to ensure it doesn't become isolated
                for neighbor in current_fault_neighbors:
                    if neighbor not in assigned_tiles:
                        queue.append((neighbor, True))  # Set parent_had_two_or_less to True
                        assigned_tiles.add(neighbor)
                        fault_line.add(neighbor)
                        break
                continue  # Skip the usual termination check

            # Check if current tile has >2 fault neighbors and none of its neighbors have >2 fault neighbors
            any_neighbor_has_more_than_two = any(
                len([
                    n for n in neighbor.get_neighbors()
                    if n.get_plate_index() is None
                ]) > 2
                for neighbor in current_fault_neighbors
            )

            # If current tile meets the condition, stop adding neighbors but keep the tile
            if num_current_fault_neighbors > 2 and not any_neighbor_has_more_than_two:
                continue  # Do not add neighbors to the queue

            for neighbor in current_fault_neighbors:
                if neighbor in assigned_tiles:
                    continue

                neighbor_fault_neighbors = [
                    n for n in neighbor.get_neighbors()
                    if n.get_plate_index() is None
                ]
                num_neighbor_fault_neighbors = len(neighbor_fault_neighbors)

                # Decide whether to add neighbor based on the criteria
                if (num_neighbor_fault_neighbors <= 2 or
                    (parent_had_two_or_less is not None and parent_had_two_or_less)):
                    queue.append((neighbor, num_neighbor_fault_neighbors <= 2))
                    assigned_tiles.add(neighbor)
                    fault_line.add(neighbor)

        # Add the completed fault line
        faults.append(list(fault_line))

    # Process remaining unassigned fault tiles
    for tile in fault_tiles:
        if tile in assigned_tiles:
            continue

        fault_line = set()
        queue = deque()
        queue.append((tile, None))
        assigned_tiles.add(tile)
        fault_line.add(tile)

        while queue:
            current_tile, parent_had_two_or_less = queue.popleft()

            current_fault_neighbors = [
                neighbor for neighbor in current_tile.get_neighbors()
                if neighbor.get_plate_index() is None
            ]
            num_current_fault_neighbors = len(current_fault_neighbors)

            any_neighbor_has_more_than_two = any(
                len([
                    n for n in neighbor.get_neighbors()
                    if n.get_plate_index() is None
                ]) > 2
                for neighbor in current_fault_neighbors
            )

            if num_current_fault_neighbors > 2 and not any_neighbor_has_more_than_two:
                continue  # Do not add neighbors to the queue

            for neighbor in current_fault_neighbors:
                if neighbor in assigned_tiles:
                    continue

                neighbor_fault_neighbors = [
                    n for n in neighbor.get_neighbors()
                    if n.get_plate_index() is None
                ]
                num_neighbor_fault_neighbors = len(neighbor_fault_neighbors)

                if (num_neighbor_fault_neighbors <= 2 or
                    (parent_had_two_or_less is not None and parent_had_two_or_less)):
                    queue.append((neighbor, num_neighbor_fault_neighbors <= 2))
                    assigned_tiles.add(neighbor)
                    fault_line.add(neighbor)

        faults.append(list(fault_line))

    # Step 5.1: Set fault indices on the tiles themselves
    for i, fault in enumerate(faults):
        for tile in fault:
            tile.set_fault_index(i)

    # Step 6: TODO - This needs to be fixed in some future refactor, but for now it is what it is
    # Plates is a list of sets -> convert to list of lists
    out_plates = []
    for plate in plates:
        out_plates.append(list(plate))

    return out_plates, faults

def spread_generic(grid, plate_queues, neighborsfunc, popfunc, individual_spread=True, growth_scales=None):
    # Spread colors using BFS for each plate with horizontal wraparound
    plates_active = len(plate_queues)  # Number of plates still spreading

    while plates_active > 0:
        for plate_index in range(len(plate_queues)):
            if not plate_queues[plate_index]:
                continue  # Plate has no more cells to spread to
                
            # Statistical growth scale - % chance to grow or not grow each iteration
            if growth_scales is not None:
                if random.random() > growth_scales[plate_index]:
                    continue

            # individual spread: one at a time per plate
            if individual_spread:
                tile = popfunc(plate_queues[plate_index])
                col, row = tile.get_coords()
                
                # If not colored yet, assign the plate's color to the cell
                if tile.get_plate_index() is None:
                    tile.set_plate_index(plate_index)

                    # Get its neighbors, add them to the queue
                    for neighbor in tile.get_neighbors():
                        plate_queues[plate_index].append(neighbor)
            else:
                # non-individual spread: "clear" the queue for each plate one at a time, i.e. BFS (although not BFS if we use any pop other than leftpop)
                for _ in range(len(plate_queues[plate_index])):
                    tile = popfunc(plate_queues[plate_index])
                    col, row = tile.get_coords()
                    
                    # If not assigned yet, assign
                    if tile.get_plate_index() is None:
                        tile.set_plate_index(plate_index)

                        # Get its neighbors, add them to the queue
                        for neighbor in tile.get_neighbors():
                            plate_queues[plate_index].append(neighbor)

            # Check if the plate's queue is empty after spreading
            if not plate_queues[plate_index]:
                plates_active -= 1

    return grid

def plate_method(grid, plate_count, individual_spread, func_neighbors, popfunc):
    # Initialize neighbors queues for each plate
    plate_queues = [ deque() for _ in range(plate_count) ]

    cols = grid.width
    rows = grid.height

    # Add seed position for each plate to its queue
    for i in range(plate_count):
        while True:
            rand_col = random.randint(0, cols - 1)
            rand_row = random.randint(0, rows - 1)
            tile = grid.get_tile(rand_col, rand_row)
            if tile.get_plate_index() is None:
                plate_queues[i].append(tile)
                break  # Ensure unique initial seeds
    return spread_generic(grid, plate_queues, func_neighbors, popfunc, individual_spread, growth_scales)
        # TODO - an idea for another mode - generate extra plates, then merge some of them at random until we're down to the desired number
        # TODO - another idea: as something of a replacement for scale: breakout plates. Create small plates expanding outward from some fault line into other plates. To simulate things like Juan de Fuca.
        
