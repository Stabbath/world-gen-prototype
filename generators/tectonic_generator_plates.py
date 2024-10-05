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

# TODO I think we don't need this
# def calculate_plates_and_faults(grid):
#     # TODO - very suboptimal, we should just keep accurate track of all of this dynamically through the get_plate / fault_index functions in HexTile
#     # Step 1: Find all unique plate indices
#     plate_to_tiles = defaultdict(set)
#     for row_idx in range(grid.height):
#         for col_idx in range(grid.width):
#             tile = grid.get_tile(col_idx, row_idx)
#             plate = tile.get_plate_index()
#             plate_to_tiles[plate].add(tile)

#     # Step 2: Fault tiles are stored under plate_index "None"; 
#     faults
        
#     # Step 3: Create plates assuming each color has only one connected cluster
#     plates = []
#     for plate_index, tiles in plate_to_tiles.items():
#         plates.append(Plate(tiles))  # Each plate is a set of hextiles

#     return plates, faults

def generate_world_plates(grid, plate_count=12, func_neighbors=get_neighbors_wraparound):
    grid = plate_method(grid, plate_count, func_neighbors)  # TODO - gui's alternative would be here instead of plate_method
    
    # TODO - if we need optimization later, detection should be made a part of the plate_method. 
    # Straightforward - when we're expanding our plates and run into a filled neighbor, we turn the tile into a fault.
    plates, faults = detect_plates_and_faults(grid)
    
    # TODO - fault line and plate properties
    # TODO - simulation of movements, creation of mountains, etc
    # TODO - creation of a secondary hexmap which stores an altitude map instead of plates. Tones of grey I guess, black is deepest, white is highest.
    
    return grid  # TODO - return altitude map instead of plate map. Or possibly both.
    
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
                if neighbor_plate != tile.get_plate_index() and neighbor_plate != -1:
                    is_border_tile = True
                    break
            
            if is_border_tile:
                plate.remove(tile)  # Remove the tile from its current plate
                fault_tiles.add(tile)  # Add the tile to the fault_tiles set
                tile.set_plate_index(-1)  # Set the tile's plate index to -1 to mark it as a fault
    
    # Step 4: Smoothing
    # Reduce the faults to the bare minimum to separate plates.
    smooth_faults(fault_tiles, plate_to_cells)
    plates = list(plate_to_cells.values()) # Update plates to reflect changes

    # Step 5: Create specific fault lines from the fault tiles.
    # Each sequence of fault tiles between 2 junctions is a fault line. After smoothing, a junction is simply a fault tile with more than 2 fault tile neighbors.
    faults = []  # List to store fault lines
    
    # Build adjacency list of fault tiles
    fault_adjacency = defaultdict(list)
    for tile in fault_tiles:
        neighbors = tile.get_neighbors()
        for neighbor in neighbors:
            if neighbor in fault_tiles:
                fault_adjacency[tile].append(neighbor)
    
    # Identify junctions and endpoints
    junctions = set()
    endpoints = set()
    for tile, neighbors in fault_adjacency.items():
        degree = len(neighbors)
        if degree > 2:
            junctions.add(tile)
        elif degree == 1:
            endpoints.add(tile)
    # Tiles with degree == 2 are neither junctions nor endpoints
    
    # Initialize set to keep track of visited edges
    visited_edges = set()
    
    # Traverse fault lines starting from junctions and endpoints
    for tile in junctions.union(endpoints):
        neighbors = fault_adjacency[tile]
        for neighbor in neighbors:
            edge = frozenset({tile, neighbor})
            if edge not in visited_edges:
                fault_line = [tile]
                visited_edges.add(edge)
                previous_tile = tile
                current_tile = neighbor
                while True:
                    fault_line.append(current_tile)
                    visited_edges.add(frozenset({previous_tile, current_tile}))
                    next_neighbors = fault_adjacency[current_tile]
                    # Exclude previous tile
                    next_neighbors = [n for n in next_neighbors if n != previous_tile]
                    # Get unvisited neighbors
                    unvisited_neighbors = [n for n in next_neighbors if frozenset({current_tile, n}) not in visited_edges]
                    if (current_tile in junctions.union(endpoints)) and current_tile != tile:
                        # Reached another junction or endpoint
                        break
                    if unvisited_neighbors:
                        # Continue to next tile
                        next_tile = unvisited_neighbors[0]
                        visited_edges.add(frozenset({current_tile, next_tile}))
                        previous_tile = current_tile
                        current_tile = next_tile
                    else:
                        # No unvisited neighbors, end of fault line
                        break
                faults.append(fault_line)
    
    # Process any remaining unvisited edges (e.g., loops without junctions)
    all_edges = set()
    for tile, neighbors in fault_adjacency.items():
        for neighbor in neighbors:
            edge = frozenset({tile, neighbor})
            all_edges.add(edge)
    remaining_edges = all_edges - visited_edges
    while remaining_edges:
        edge = remaining_edges.pop()
        tile, neighbor = list(edge)
        fault_line = [tile]
        visited_edges.add(edge)
        previous_tile = tile
        current_tile = neighbor
        while True:
            fault_line.append(current_tile)
            visited_edges.add(frozenset({previous_tile, current_tile}))
            # Get neighbors excluding previous tile
            next_neighbors = fault_adjacency[current_tile]
            next_neighbors = [n for n in next_neighbors if n != previous_tile]
            # Get unvisited neighbors
            unvisited_neighbors = [n for n in next_neighbors if frozenset({current_tile, n}) not in visited_edges]
            if unvisited_neighbors:
                next_tile = unvisited_neighbors[0]
                visited_edges.add(frozenset({current_tile, next_tile}))
                previous_tile = current_tile
                current_tile = next_tile
            else:
                # No unvisited neighbors, end of fault line
                break
        faults.append(fault_line)
        remaining_edges = all_edges - visited_edges  # Update remaining_edges

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
