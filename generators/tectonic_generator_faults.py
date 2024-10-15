import random

# Constants used in the generation methods. This can be improved
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

class LineState:
    def __init__(self, tile, direction, initial_direction, branch_depth):
        self.tile = tile
        self.direction = direction
        self.initial_direction = initial_direction
        self.branch_depth = branch_depth

def generate_world_faults(hex_grid, config, func_neighbors):
    # NOTE: func_neighbors is not used.
    n_sides = config['faults']['n_selected_tiles']
    n_topbot = n_sides  # For simplicity let's use the same number of starting tiles

    # Step1: Select boundary tiles
    selected_tiles = select_distributed_boundary_tiles(hex_grid, n_sides, n_topbot)
    print(f"Selected {n_sides} boundary tiles for line generation from the left boundary and {n_topbot} tiles from the top and bot boundary.")

    # Generate lines
    generate_lines_in_directions(hex_grid, config, selected_tiles)
    print("Generated lines from boundary tiles.")

    # Label continents
    label_continents(hex_grid)
    print("Continents labeled.")
    
    return hex_grid

def select_distributed_boundary_tiles(hex_grid, n_sides, n_topbot):
    
    # Get boundary tiles for each side
    top_tiles = [tile for tile in hex_grid.tiles if tile.row == 0]
    bottom_tiles = [tile for tile in hex_grid.tiles if tile.row == hex_grid.height - 1]
    left_tiles = [tile for tile in hex_grid.tiles if tile.col == 0]
    right_tiles = [tile for tile in hex_grid.tiles if tile.col == hex_grid.width - 1]

    sides = ['left','top', 'bottom']
    side_tiles = {
        'top': top_tiles,
        'bottom': bottom_tiles,
        'left': left_tiles
    }

    # Distribute the starting points per side.
    side_counts = {
        'top': n_topbot,
        'bottom': n_topbot,
        'left': n_sides
        }

    selected_tiles = []
    for side in sides:
        tiles = side_tiles[side]
        count = side_counts[side]
        if count > len(tiles):  #This should never happen, but check
            count = len(tiles)
        selected = random.sample(tiles, count)  # For each side we select random tiles to start the line generation
        selected_tiles.extend(selected)
        for tile in selected:
            tile.is_selected = True
            tile.is_line = True  # Mark starting tiles as part of the fault line
        if side == 'left':
            rows_in_selected_tiles = set(tile.row for tile in selected)
            
            wraparound_selected = [tile for tile in right_tiles if tile.row in rows_in_selected_tiles]

            for tile in wraparound_selected:
                tile.is_selected = True
                tile.is_line = True  # Mark starting tiles as part of the fault line
            selected_tiles.extend(wraparound_selected)  # Extends the generator tiles with the wraparound tiles on the right
    return selected_tiles

def get_weighted_initial_directions(hex_grid, tile):
    direction_weights = {}

    # Check for corners first
    if tile.row == 0 and tile.col == 0:
        # Top-left corner
        direction_weights['SE'] = 1
    elif tile.row == 0 and tile.col == hex_grid.width - 1:
        # Top-right corner
        direction_weights['SW'] = 1
    elif tile.row == hex_grid.height - 1 and tile.col == 0:
        # Bottom-left corner
        direction_weights['NE'] = 1
    elif tile.row == hex_grid.height - 1 and tile.col == hex_grid.width - 1:
        # Bottom-right corner
        direction_weights['NW'] = 1
    else:
        # Edge conditions (non-corner)
        if tile.row == 0:
            # Top edge
            direction_weights['S'] = 0.7
            direction_weights['SE'] = 0.15
            direction_weights['SW'] = 0.15
        if tile.row == hex_grid.height - 1:
            # Bottom edge
            direction_weights['N'] = 0.7
            direction_weights['NE'] = 0.15
            direction_weights['NW'] = 0.15
        if tile.col == 0:
            # Left edge
            direction_weights['NE'] = 0.5
            direction_weights['SE'] = 0.5
        if tile.col == hex_grid.width - 1:
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

""" def generate_lines_in_directions(hex_grid, config, selected_tiles):
    MAX_BRANCH_DEPTH = config['faults']['max_branch_depth']
    random.shuffle(selected_tiles)
    for tile in selected_tiles:
        # Get weighted possible initial directions based on tile position
        weighted_directions = get_weighted_initial_directions(hex_grid, tile)
        if weighted_directions:
            # Randomly choose one initial direction based on weights
            directions, weights = zip(*weighted_directions)
            initial_direction = random.choices(directions, weights=weights)[0]
            print(f"Generating line from Tile ({tile.col}, {tile.row}) towards {initial_direction}")
            generate_line(hex_grid, config, tile, initial_direction, initial_direction, MAX_BRANCH_DEPTH)
        else:
            print(f"No possible initial directions for Tile ({tile.col}, {tile.row})") """


def generate_lines_in_directions(hex_grid, config, selected_tiles):
    MAX_BRANCH_DEPTH = config['faults']['max_branch_depth']
    
    # Phase 1: Initialize the main line states for all selected tiles
    branching_tiles = []  # To store potential branching tiles
    line_states = []
    
    # Initialize line states for each selected tile
    for tile in selected_tiles:
        weighted_directions = get_weighted_initial_directions(hex_grid, tile)
        if weighted_directions:
            directions, weights = zip(*weighted_directions)
            initial_direction = random.choices(directions, weights=weights)[0]
            print(f"Starting main line from Tile ({tile.col}, {tile.row}) towards {initial_direction}")
            line_states.append(LineState(tile, initial_direction, initial_direction, MAX_BRANCH_DEPTH))
        else:
            print(f"No possible initial directions for Tile ({tile.col}, {tile.row})")
    
    # Phase 1: Step through all lines in parallel, one tile at a time
    while line_states:
        next_line_states = []
        for state in line_states:
            if generate_line_step_main(hex_grid, config, state, branching_tiles):
                next_line_states.append(state)  # If line can continue, keep it in the next iteration
        line_states = next_line_states  # Update the active line states for the next iteration

    # Phase 2: Extend branches from the marked branching tiles
    extend_branches(hex_grid, config, branching_tiles)


def generate_line_step_main(hex_grid, config, state, branching_tiles):
    """
    Perform one step of line generation for the main line, marking potential branching tiles but not creating branches.
    :param hex_grid: The HexGrid object
    :param state: LineState object tracking the current tile and direction
    :param branching_tiles: List to store potential branching tiles
    :return: True if the line can continue, False if the line should stop
    """
    STOP_ON_INTERSECTION = config['faults']['stop_on_intersection']
    
    current_tile = state.tile
    current_direction = state.direction
    
    # Get the next tile
    next_tile = get_neighbor_in_direction(hex_grid, current_tile, current_direction)
    
    if next_tile:
        if next_tile.is_selected:
            pass  # Allow lines to pass through selected tiles
        
        if STOP_ON_INTERSECTION and next_tile.is_line:
            print(f"Line reached an intersection at Tile ({next_tile.col}, {next_tile.row})")
            return False  # Stop the line if it hits another line

        if not next_tile.is_line:
            next_tile.is_line = True
            print(f"Added Tile ({next_tile.col}, {next_tile.row}) to the main line")
            
            # Mark this tile as a potential branching tile, but don't branch yet
            branching_tiles.append((next_tile, state.direction, state.initial_direction, state.branch_depth))
            
            # Decide the next direction, favoring the initial direction
            allowed_directions = ADJACENT_DIRECTIONS[current_direction]
            weights = []
            for d in allowed_directions:
                angle_diff = angular_difference(DIRECTION_ANGLES[d], DIRECTION_ANGLES[state.initial_direction])
                weight = (180 - angle_diff) + 1
                weights.append(weight)
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]
            state.direction = random.choices(allowed_directions, weights=normalized_weights)[0]

            state.tile = next_tile  # Move to the next tile
            return True  # Continue the line
        else:
            print(f"Line stopped at Tile ({next_tile.col}, {next_tile.row}) to prevent cycles")
            return False  # Stop the line to prevent cycles
    else:
        print(f"Line reached boundary at Tile ({current_tile.col}, {current_tile.row})")
        return False  # Stop the line if it reaches the boundary

def extend_branches(hex_grid, config, branching_tiles):
    """
    Extend branches from the marked branching tiles after the main lines are drawn.
    :param hex_grid: The HexGrid object
    :param branching_tiles: List of tiles where branching should occur
    """
    for tile, current_direction, initial_direction, branch_depth in branching_tiles:
        if branch_depth > 0:
            branch_directions = [d for d in ADJACENT_DIRECTIONS[current_direction]]
            if branch_directions:
                branch_direction = random.choice(branch_directions)
                print(f"Extending branch from Tile ({tile.col}, {tile.row}) towards {branch_direction}")
                state = LineState(tile, branch_direction, initial_direction, branch_depth - 1)
                while generate_line_step_branch(hex_grid, config, state):
                    pass  # Continue generating the branch until it stops

def generate_line_step_branch(hex_grid, config, state):
    """
    Perform one step of line generation for a branch, ensuring it doesn't intersect with the main line.
    :param hex_grid: The HexGrid object
    :param state: LineState object tracking the current tile and direction
    :return: True if the branch can continue, False if the branch should stop
    """
    STOP_ON_INTERSECTION = config['faults']['stop_on_intersection']
    
    current_tile = state.tile
    current_direction = state.direction
    
    # Get the next tile
    next_tile = get_neighbor_in_direction(hex_grid, current_tile, current_direction)
    
    if next_tile:
        if next_tile.is_selected:
            pass  # Allow lines to pass through selected tiles
        
        if STOP_ON_INTERSECTION and next_tile.is_line:
            print(f"Branch stopped at Tile ({next_tile.col}, {next_tile.row}) due to intersection")
            return False  # Stop the branch if it hits another line

        if not next_tile.is_line:
            next_tile.is_line = True
            print(f"Added Tile ({next_tile.col}, {next_tile.row}) to the branch")
            
            # Decide the next direction, favoring the initial direction
            allowed_directions = ADJACENT_DIRECTIONS[current_direction]
            weights = []
            for d in allowed_directions:
                angle_diff = angular_difference(DIRECTION_ANGLES[d], DIRECTION_ANGLES[state.initial_direction])
                weight = (180 - angle_diff) + 1
                weights.append(weight)
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]
            state.direction = random.choices(allowed_directions, weights=normalized_weights)[0]

            state.tile = next_tile  # Move to the next tile
            return True  # Continue the branch
        else:
            print(f"Branch stopped at Tile ({next_tile.col}, {next_tile.row}) to prevent cycles")
            return False  # Stop the branch to prevent cycles
    else:
        print(f"Branch reached boundary at Tile ({current_tile.col}, {current_tile.row})")
        return False  # Stop the branch if it reaches the boundary

def generate_line(hex_grid, config, start_tile, direction, initial_direction, branch_depth):
    """
    Generate a line from the start_tile, moving randomly without sharp turns,
    preferring to continue towards the initial direction. Allows for branching.

    :param hex_grid: The HexGrid object
    :param start_tile: HexTile object to start the line from
    :param direction: Current direction string ('N', 'NE', 'SE', 'S', 'SW', 'NW')
    :param initial_direction: The initial preferred direction
    :param branch_depth: Remaining branching depth
    """
    BRANCHING_CHANCE = config['faults']['branching_chance']
    STOP_ON_INTERSECTION = config['faults']['stop_on_intersection']

    current_tile = start_tile
    current_direction = direction
    visited_tiles = set()
    while True:
        next_tile = get_neighbor_in_direction(hex_grid, current_tile, current_direction)
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
                        generate_line(hex_grid, config, next_tile, branch_direction, initial_direction, branch_depth - 1)  # Generate a new line with branch depth - 1 

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

def get_neighbor_in_direction(hex_grid, tile, direction):
    """
    Get the neighboring tile in the specified direction, with horizontal wraparound.

    :param hex_grid: The HexGrid object
    :param tile: Current HexTile object
    :param direction: Direction string ('N', 'NE', 'SE', 'S', 'SW', 'NW')
    :return: Neighbor HexTile object or None if out of vertical bounds
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
    
    # Handle horizontal wraparound
    if neighbor_col < 0:
        neighbor_col = hex_grid.width -1 
    elif neighbor_col > hex_grid.width -1 :
        neighbor_col = 0
    
    
    neighbor = hex_grid.get_tile(neighbor_col, neighbor_row)
    return neighbor


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
            for neighbor in tile.get_neighbors():
                if neighbor and not neighbor.is_line and neighbor.continent_label is None:
                    stack.append(neighbor)

def generate_continent_colors():
    """
    Generate a list of colors for continents.
    """
    colors = [
    (34, 139, 34),    # Forest Green
    (85, 107, 47),    # Dark Olive Green
    (107, 142, 35),   # Olive Drab
    (124, 252, 0),    # Lawn Green
    (127, 255, 0),    # Chartreuse
    (173, 255, 47),   # Green Yellow
    (50, 205, 50),    # Lime Green
    (60, 179, 113),   # Medium Sea Green
    (0, 128, 0),      # Green
    (0, 100, 0),      # Dark Green
    (255, 69, 0),     # Red Orange
    (220, 20, 60),    # Crimson
    (255, 140, 0),    # Dark Orange
    (255, 165, 0),    # Orange
    (255, 255, 0),    # Yellow
    (255, 215, 0),    # Gold
    (255, 192, 203),  # Pink
    (255, 105, 180),  # Hot Pink
    (138, 43, 226),   # Blue Violet
    (75, 0, 130),     # Indigo
    (0, 191, 255),    # Deep Sky Blue
    (30, 144, 255),   # Dodger Blue
    (70, 130, 180),   # Steel Blue
    (0, 0, 255),      # Blue
    (0, 0, 139),      # Dark Blue
    (100, 149, 237),  # Cornflower Blue
    (135, 206, 235),  # Sky Blue
    (72, 61, 139),    # Dark Slate Blue
    (240, 230, 140),  # Khaki
    (210, 180, 140),  # Tan
    (139, 69, 19),    # Saddle Brown
    (160, 82, 45),    # Sienna
    (128, 0, 0),      # Maroon
    (255, 248, 220),  # Cornsilk
    (192, 192, 192),  # Silver
    (169, 169, 169),  # Dark Grey
    (47, 79, 79),     # Dark Slate Grey
    (105, 105, 105),  # Dim Grey
    (0, 255, 255),    # Cyan / Aqua
    (224, 255, 255),  # Light Cyan
    (255, 250, 250),  # Snow White
    (245, 245, 220),  # Beige
]
    random.shuffle(colors)
    return colors
