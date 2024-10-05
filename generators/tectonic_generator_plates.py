# file: tectonic_generator.py
import random
from collections import deque, defaultdict
from neighbor_functions import get_neighbors_wraparound
from generators.tectonic_fault_smoothing import smooth_faults

def leftpop(l):
    return l.popleft()

def randpop(l):
    rand_index = random.randint(0, len(l) - 1)
    value = l[rand_index]
    del l[rand_index]
    return value

# TODO - move these variables into the external configurations
popfunc = randpop
individual_spread = False
growth_scales = None  # [1.0] * 8 + [0.5] * 4

# TODO - add a config option once plate merging is implemented, as part of plate merging - boolean: start by merging all plates touching each pole and then exclude those plates from any more merges

# TODO - add a config option to tectonic method: turn non-wraparound edges into faults with -1 GenFactor. To force oceans at the poles.

# TODO - move this to utils
def gaussian_in_range(mean=0, std_dev=0.7, min=-1, max=1):
    counter = 0
    while counter < 10: # to prevent eternal loops
        value = random.gauss(mean, std_dev)
        if min <= value <= max:
            return value
        else:
            counter += 1
    raise Exception("Bad parameters for gaussian_in_range; could not succeed after 10 tries")

# Example usage
random_value = gaussian_in_range()

def generate_world_plates(grid, plate_count=12, func_neighbors=get_neighbors_wraparound):
    grid = plate_method(grid, plate_count, func_neighbors)  # TODO - gui's alternative would be here instead of plate_method
    
    # === Step 1: Generation of Plates and Faults === 
    # TODO - if we need optimization later, detection should be made a part of the plate_method. 
    # Straightforward - when we're expanding our plates and run into a filled neighbor, we turn the tile into a fault.
    plates, faults = detect_plates_and_faults(grid)
    grid.set_plates_from_lists(plates)
    grid.set_faults_from_lists(faults)

    # TODO - this feels dirty just throwing it on here like this, maybe clean it up later
    for fault in grid.faults:
        fault.refresh_neighbor_groups()
    
    # === Step 2: Assignment of Fault and/or Plate Properties ===
    # This is deeply connected to step 3. Our altitude generation depends on the properties we include. 
    # And for the same properties, there may be different altitude generation methods.
    # For now, just assuming my initial method. Later, we'll need to possibly restructure/extract things to make it more flexible, with different combinations of Property Assignment and Altitude Map Generation

    # GENERATOR/CONSUMER MODEL
    # These settings should come from the gen config later.
    MAX_ITER = 100
    MAXGENFACTOR = 1
    MAXALTITUDE = 20000
    NOISE_FACTOR = 0.02
    SMOOTHEN_GENFACTORS = False

    # First, we assign to each fault a float between 1 and -1, completely at random. This is its Generation Factor. If negative, it means it consumes mass. If positive, it generates it.
    # We use a dictionary, external to the Fault class.
    generation_factors = {}
    for fault in grid.faults:
        generation_factors[fault.id] = gaussian_in_range(min=-1, max=1)

    # Then we smooth these factors: we check for each fault its neighboring faults, and the Generation Factor we have for it,
    # and we recalculate them all as a weighted average of their own factor and their neighbors', with their own factor being worth twice as much for the average.
    if SMOOTHEN_GENFACTORS:
        smoothed_generation_factors = {}
        for fault in grid.faults:
            own_factor = generation_factors[fault.id]
            neighbor_indices = fault.get_fault_neighbor_indices()
            neighbor_factors = [generation_factors[neighbor_index] for neighbor_index in neighbor_indices]
            total_weight = 2 + len(neighbor_factors)
            weighted_sum = 2 * own_factor + sum(neighbor_factors)
            smoothed_factor = weighted_sum / total_weight
            smoothed_generation_factors[fault.id] = smoothed_factor
        generation_factors = smoothed_generation_factors
    
    # Then, we renormalize everything so that the lowest is -1 and the highest is +1.
    factor_values = generation_factors.values()
    min_factor = min(factor_values)
    max_factor = max(factor_values)

    for fault_id, factor in generation_factors.items():
        normalized_factor = -1 + 2 * (factor - min_factor) / (max_factor - min_factor)
        generation_factors[fault_id] = normalized_factor
    
    # === Step 3: Altitude Map Generation ===
    # Each iteration has the following steps: 
    #   1. Each fault adds landmass to itself equal to its generation_factor times the MaxGenFactor
    #   2. We add a small amount of noise to the entire hex grid.
    #   3. We smoothen the entire hexgrid based on neighbors
    for _ in range(MAX_ITER):
        # Step 1: Each fault adds landmass to itself equal to its generation_factor times the MaxGenFactor
        for fault in grid.faults:
            gen_factor = generation_factors[fault.id]
            mass_change = gen_factor * MAXGENFACTOR
            for tile in fault.get_tiles():
                alt = tile.get_altitude()
                tile.set_altitude(alt + mass_change)
        
        # Step 2: Add a small amount of noise to the entire hex grid
        for tile in grid.get_tiles():
            alt = tile.get_altitude()
            noise = random.uniform(-1, 1) * NOISE_FACTOR
            tile.set_altitude(alt + noise)
        
        # Step 3: Smooth the entire hexgrid based on neighbors
        # Collect current altitudes before smoothing
        tile_altitudes = {tile: tile.get_altitude() for tile in grid.get_tiles()}
        for tile in grid.get_tiles():
            neighbors = tile.get_neighbors()
            neighbor_alts = [tile_altitudes[neighbor] for neighbor in neighbors]
            avg_neighbor_alt = sum(neighbor_alts) / len(neighbor_alts)
            # New altitude is the average of own altitude and neighbors'
            new_altitude = (tile_altitudes[tile] + avg_neighbor_alt) / 2
            tile.set_altitude(new_altitude)
    
    # Finally, we normalize the altitude of every tile according to MAXALTITUDE, so that the lowest altitude is 0, and the highest altitude is 20000.
    altitudes = [tile.get_altitude() for tile in grid.get_tiles()]
    min_altitude = min(altitudes)
    max_altitude = max(altitudes)
    
    for tile in grid.get_tiles():
        alt = tile.get_altitude()
        normalized_altitude = (alt - min_altitude) / (max_altitude - min_altitude) * MAXALTITUDE
        tile.set_altitude(normalized_altitude)
    
    return grid
    
def detect_plates_and_faults(grid):
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

    # TODO - consider the edge case where a 4-way intersection can have a singular tile which will not be reached by the fault lines leading to it, and as such will be identified as a 1-tile fault.
    # TODO - more meaningful, that also happens whenever we have a star junction (as opposed to a triangle junction)

    # Step 5.1: Set fault indices on the tiles themselves
    for i, fault in enumerate(faults):
        for tile in fault:
            tile.set_fault_index(i)

    return plates, faults

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

def plate_method(grid, plate_count, func_neighbors):
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
        
        
    # TODO - detect all fault lines, assign a fault type to each one
    # TODO - simulate the movements of our plates for a while and deform them appropriately on a 2D plane still
    # TODO - then level it up to a 3D plane, so we can add subduction etc and make tectonic mountains and pits
    # TODO - then add hot spots, volcanoes, and any other such extras. Maybe meteor craters too.
    #   And that will conclude our Topology. It could however be developed further by for example defining oceanic vs continental plates, or rock composition (and density), or plate age.
    #   - Step 2 would then be seas, oceans, rivers, lakes. Probably in conjunction with climate. For now, assume sea level is universally the same, ignore tides and tide differences between seas and stuff.
    #   - Step 3 would be climate, if not already done. But I think that goes hand in hand with 2.
    #   - Step 4 would then be erosion, finetuning topology based on the effect of climate.
    #   And that would conclude our Geology. I think. Afterwards, we can tackle civilizational simulation.
