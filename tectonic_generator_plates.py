# file: tectonic_generator.py
import random
from collections import deque, defaultdict
from neighbor_functions import get_neighbors_wraparound

def leftpop(l):
    return l.popleft()

def randpop(l):
    rand_index = random.randint(0, len(l) - 1)
    value = l[rand_index]
    del l[rand_index]
    return value

PLATE_COLORS = [
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

# TODO - move these variables into the external configurations
popfunc = randpop
individual_spread = False
growth_scales = None  # [1.0] * 8 + [0.5] * 4

def generate_world_plates(grid, plate_count=12, func_neighbors=get_neighbors_wraparound):
    grid = plate_method(grid, plate_count, func_neighbors)  # TODO - gui's alternative would be here instead of plate_method
    grid.plate_colors = PLATE_COLORS;
    
    # NOTE - if we need optimization later, detection should be made a part of the plate_method (or fault_method)
    # plates, faults = detect_plates_and_faults(grid)
    # grid.set_plates(plates)
    # grid.set_faults(faults)
    
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

    # Step 3: Identify fault lines (boundaries between plates)
    faults = []
    fault_pairs = set()
    for row_idx in range(rows):
        for col_idx in range(cols):
            tile = grid.get_tile(col_idx, row_idx)
            current_plate = tile.get_plate_index()

            for neighbor in tile.get_neighbors():
                neighbor_plate = neighbor.get_plate_index()
                if neighbor_plate != current_plate:
                    # Create a sorted tuple to avoid duplicate pairs
                    pair = tuple(sorted([ tile, neighbor ]))
                    fault_pairs.add(pair)
    # Convert fault_pairs to list of sets
    faults = [ set(pair) for pair in fault_pairs ]

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
