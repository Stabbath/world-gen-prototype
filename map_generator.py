import random
from collections import deque, defaultdict
from neighbor_functions import get_neighbors, get_neighbors_wraparound

# Constants used in the generation methods
DIRECTIONS = ['N', 'NE', 'SE', 'S', 'SW', 'NW']
OPPOSITE_DIRECTIONS = {
    'N': 'S',
    'NE': 'SW',
    'SE': 'NW',
    'S': 'N',
    'SW': 'NE',
    'NW': 'SE'
}
DIRECTION_ANGLES = {
    'N': 0,
    'NE': 60,
    'SE': 120,
    'S': 180,
    'SW': 240,
    'NW': 300
}
ADJACENT_DIRECTIONS = {
    'N': ['NW', 'N', 'NE'],
    'NE': ['N', 'NE', 'SE'],
    'SE': ['NE', 'SE', 'S'],
    'S': ['SE', 'S', 'SW'],
    'SW': ['S', 'SW', 'NW'],
    'NW': ['SW', 'NW', 'N']
}
BRANCHING_CHANCE = 0.1
MAX_BRANCH_DEPTH = 2
STOP_ON_INTERSECTION = True  # As in original code

def generate_world_faults(hex_grid, n_selected=12):
    # Select boundary tiles
    selected_tiles = select_distributed_boundary_tiles(hex_grid, n_selected)
    print(f"Selected {n_selected} boundary tiles for line generation.")

    # Generate lines
    generate_lines_in_directions(hex_grid, selected_tiles)
    print("Generated lines from boundary tiles.")

    # Label continents
    label_continents(hex_grid)
    print("Continents labeled.")

def select_distributed_boundary_tiles(hex_grid, n):
    # Get boundary tiles for each side
    top_tiles = [tile for tile in hex_grid.tiles if tile.row == 0]
    bottom_tiles = [tile for tile in hex_grid.tiles if tile.row == hex_grid.rows - 1]
    left_tiles = [tile for tile in hex_grid.tiles if tile.col == 0]
    right_tiles = [tile for tile in hex_grid.tiles if tile.col == hex_grid.cols - 1]

    sides = ['top', 'right', 'bottom', 'left']
    side_tiles = {
        'top': top_tiles,
        'right': right_tiles,
        'bottom': bottom_tiles,
        'left': left_tiles
    }

    # Distribute starting points among sides
    num_sides = len(sides)
    points_per_side = n // num_sides
    extra_points = n % num_sides

    # Randomly assign extra points to sides
    side_counts = {side: points_per_side for side in sides}
    extra_sides = random.sample(sides, extra_points)
    for side in extra_sides:
        side_counts[side] += 1

    selected_tiles = []
    for side in sides:
        tiles = side_tiles[side]
        count = side_counts[side]
        if count > len(tiles):
            count = len(tiles)
        selected = random.sample(tiles, count)
        selected_tiles.extend(selected)
        for tile in selected:
            tile.is_selected = True
            tile.is_line = True  # Mark starting tiles as part of the fault line

    return selected_tiles

def get_weighted_initial_directions(hex_grid, tile):
    direction_weights = {}

    # Check for corners first
    if tile.row == 0 and tile.col == 0:
        # Top-left corner
        direction_weights['SE'] = 1
    elif tile.row == 0 and tile.col == hex_grid.cols - 1:
        # Top-right corner
        direction_weights['SW'] = 1
    elif tile.row == hex_grid.rows - 1 and tile.col == 0:
        # Bottom-left corner
        direction_weights['NE'] = 1
    elif tile.row == hex_grid.rows - 1 and tile.col == hex_grid.cols - 1:
        # Bottom-right corner
        direction_weights['NW'] = 1
    else:
        # Edge conditions (non-corner)
        if tile.row == 0:
            # Top edge
            direction_weights['S'] = 0.7
            direction_weights['SE'] = 0.15
            direction_weights['SW'] = 0.15
        if tile.row == hex_grid.rows - 1:
            # Bottom edge
            direction_weights['N'] = 0.7
            direction_weights['NE'] = 0.15
            direction_weights['NW'] = 0.15
        if tile.col == 0:
            # Left edge
            direction_weights['NE'] = 0.5
            direction_weights['SE'] = 0.5
        if tile.col == hex_grid.cols - 1:
            # Right edge
            direction_weights['NW'] = 0.5
            direction_weights['SW'] = 0.5

    # Remove invalid directions
    valid_directions = set(DIRECTIONS)
    direction_weights = {d: w for d, w in direction_weights.items() if d in valid_directions}

    # Normalize weights if necessary
    total_weight = sum(direction_weights.values())
    if total_weight > 0:
        direction_weights = {d: w / total_weight for d, w in direction_weights.items()}

    # Convert to list of tuples
    weighted_directions = list(direction_weights.items())
    return weighted_directions

def generate_lines_in_directions(hex_grid, selected_tiles):
    for tile in selected_tiles:
        # Get weighted possible initial directions based on tile position
        weighted_directions = get_weighted_initial_directions(hex_grid, tile)
        if weighted_directions:
            # Randomly choose one initial direction based on weights
            directions, weights = zip(*weighted_directions)
            initial_direction = random.choices(directions, weights=weights)[0]
            print(f"Generating line from Tile ({tile.col}, {tile.row}) towards {initial_direction}")
            generate_line(hex_grid, tile, initial_direction, initial_direction, MAX_BRANCH_DEPTH)
        else:
            print(f"No possible initial directions for Tile ({tile.col}, {tile.row})")

def generate_line(hex_grid, start_tile, direction, initial_direction, branch_depth):
    """
    Generate a line from the start_tile, moving randomly without sharp turns,
    preferring to continue towards the initial direction. Allows for branching.

    :param hex_grid: The HexGrid object
    :param start_tile: HexTile object to start the line from
    :param direction: Current direction string ('N', 'NE', 'SE', 'S', 'SW', 'NW')
    :param initial_direction: The initial preferred direction
    :param branch_depth: Remaining branching depth
    """
    current_tile = start_tile
    current_direction = direction
    visited_tiles = set()
    while True:
        next_tile = get_neighbor(hex_grid, current_tile, current_direction)
        if next_tile:
            if next_tile.is_selected:
                # Allow lines to pass through selected tiles
                pass

            if STOP_ON_INTERSECTION and next_tile.is_line:
                # If stopping on intersection and the next tile is already a line, stop
                print(f"Line stopped at Tile ({next_tile.col}, {next_tile.row}) due to intersection")
                break

            if next_tile not in visited_tiles:
                next_tile.is_line = True
                visited_tiles.add(next_tile)
                print(f"Added Tile ({next_tile.col}, {next_tile.row}) to the line")

                # Branching logic
                if branch_depth > 0 and random.random() < BRANCHING_CHANCE:
                    # Choose a different direction to branch
                    branch_directions = [d for d in ADJACENT_DIRECTIONS[current_direction] if d != current_direction]
                    if branch_directions:
                        branch_direction = random.choice(branch_directions)
                        print(f"Branching from Tile ({next_tile.col}, {next_tile.row}) towards {branch_direction}")
                        generate_line(hex_grid, next_tile, branch_direction, initial_direction, branch_depth - 1)

                # Decide the next direction, favoring the initial direction
                allowed_directions = ADJACENT_DIRECTIONS[current_direction]
                weights = []
                for d in allowed_directions:
                    angle_diff = angular_difference(DIRECTION_ANGLES[d], DIRECTION_ANGLES[initial_direction])
                    weight = (180 - angle_diff) + 1  # Add 1 to avoid zero weights
                    weights.append(weight)
                # Normalize weights
                total_weight = sum(weights)
                normalized_weights = [w / total_weight for w in weights]
                current_direction = random.choices(allowed_directions, weights=normalized_weights)[0]

                current_tile = next_tile
            else:
                # Already visited this tile, prevent cycles
                print(f"Line stopped at Tile ({next_tile.col}, {next_tile.row}) to prevent cycles")
                break
        else:
            # Reached boundary
            print(f"Line reached boundary at Tile ({current_tile.col}, {current_tile.row})")
            break

def angular_difference(angle1, angle2):
    """
    Calculate the smallest angular difference between two angles in degrees.

    :param angle1: First angle in degrees
    :param angle2: Second angle in degrees
    :return: Smallest angular difference in degrees (0 to 180)
    """
    diff = abs(angle1 - angle2) % 360
    if diff > 180:
        diff = 360 - diff
    return diff

def get_neighbor(hex_grid, tile, direction):
    """
    Get the neighboring tile in the specified direction.

    :param hex_grid: The HexGrid object
    :param tile: Current HexTile object
    :param direction: Direction string ('N', 'NE', 'SE', 'S', 'SW', 'NW')
    :return: Neighbor HexTile object or None if out of bounds
    """
    parity = 'even' if tile.col % 2 == 0 else 'odd'
    NEIGHBOR_DELTAS = {
        'even': {
            'N': (0, -1),
            'NE': (+1, -1),
            'SE': (+1, 0),
            'S': (0, +1),
            'SW': (-1, 0),
            'NW': (-1, -1)
        },
        'odd': {
            'N': (0, -1),
            'NE': (+1, 0),
            'SE': (+1, +1),
            'S': (0, +1),
            'SW': (-1, +1),
            'NW': (-1, 0)
        }
    }
    delta = NEIGHBOR_DELTAS[parity].get(direction)
    if not delta:
        return None
    neighbor_col = tile.col + delta[0]
    neighbor_row = tile.row + delta[1]
    neighbor = hex_grid.get_tile(neighbor_col, neighbor_row)
    return neighbor

def label_continents(hex_grid):
    """
    Label each continent (region) separated by fault lines with a unique label.
    """
    label_counter = 0
    continent_labels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    colors = generate_continent_colors()
    hex_grid.continent_colors = {}
    for tile in hex_grid.tiles:
        if not tile.is_line and tile.continent_label is None:
            # Start a new continent
            label = continent_labels[label_counter % len(continent_labels)]
            color = colors[label_counter % len(colors)]
            flood_fill(tile, label)
            hex_grid.continent_colors[label] = color
            label_counter += 1

    print(f"Labeled {label_counter} continents.")

def flood_fill(start_tile, label):
    """
    Perform flood fill to label connected tiles.

    :param start_tile: HexTile object to start flood fill from
    :param label: Continent label to assign
    """
    stack = [start_tile]
    while stack:
        tile = stack.pop()
        if tile.continent_label is None and not tile.is_line:
            tile.continent_label = label
            # Get neighbors without wraparound
            for neighbor in tile.get_neighbors(wraparound=False):
                if neighbor and not neighbor.is_line and neighbor.continent_label is None:
                    stack.append(neighbor)

def generate_continent_colors():
    """
    Generate a list of colors for continents.
    """
    colors = [
        (34, 139, 34),   # Forest Green
        (85, 107, 47),   # Dark Olive Green
        (107, 142, 35),  # Olive Drab
        (124, 252, 0),   # Lawn Green
        (127, 255, 0),   # Chartreuse
        (173, 255, 47),  # Green Yellow
        (50, 205, 50),   # Lime Green
        (60, 179, 113),  # Medium Sea Green
        (0, 128, 0),     # Green
        (0, 100, 0),     # Dark Green
    ]
    random.shuffle(colors)
    return colors

# Plate-based generation method
def generate_world_plates(hex_grid, plate_count=12):
    # Initialize plate queues
    plate_queues = [deque() for _ in range(plate_count)]
    cols = hex_grid.cols
    rows = hex_grid.rows
    # Add seed positions
    for i in range(plate_count):
        while True:
            rand_col = random.randint(0, cols - 1)
            rand_row = random.randint(0, rows - 1)
            tile = hex_grid.get_tile(rand_col, rand_row)
            if tile.get_plate_index() is None:
                plate_queues[i].append(tile)
                break  # Ensure unique initial seeds
    spread_generic(hex_grid, plate_queues)
    detect_faults(hex_grid)

def spread_generic(hex_grid, plate_queues):
    plates_active = len(plate_queues)
    while plates_active > 0:
        for plate_index in range(len(plate_queues)):
            if not plate_queues[plate_index]:
                continue  # Plate has no more cells to spread to

            tile = plate_queues[plate_index].popleft()
            if tile.get_plate_index() is None:
                tile.set_plate_index(plate_index)
                # Get its neighbors with wraparound
                for neighbor in tile.get_neighbors(wraparound=True):
                    plate_queues[plate_index].append(neighbor)

            if not plate_queues[plate_index]:
                plates_active -= 1

def detect_faults(hex_grid):
    faults = []
    fault_pairs = set()
    for tile in hex_grid.tiles:
        current_plate = tile.get_plate_index()
        for neighbor in tile.get_neighbors(wraparound=True):
            neighbor_plate = neighbor.get_plate_index()
            if neighbor_plate != current_plate:
                pair = tuple(sorted([tile, neighbor], key=lambda t: (t.col, t.row)))
                fault_pairs.add(pair)
    # Convert fault_pairs to list of sets
    faults = [set(pair) for pair in fault_pairs]
    # Mark tiles on faults
    for fault in faults:
        for tile in fault:
            tile.is_line = True  # Mark as fault line

    # Generate plate colors
    colors = generate_plate_colors()
    hex_grid.plate_colors = {i: colors[i % len(colors)] for i in range(len(colors))}

def generate_plate_colors():
    colors = [
        (255, 0, 0),       # Red
        (0, 255, 0),       # Green
        (0, 0, 255),       # Blue
        (255, 255, 0),     # Yellow
        (255, 0, 255),     # Magenta
        (0, 255, 255),     # Cyan
        (128, 0, 0),       # Maroon
        (0, 128, 0),       # Dark Green
        (0, 0, 128),       # Navy
        (128, 128, 0),     # Olive
        (128, 0, 128),     # Purple
        (0, 128, 128),     # Teal
        (255, 165, 0),     # Orange
        (255, 192, 203),   # Pink
    ]
    random.shuffle(colors)
    return colors
