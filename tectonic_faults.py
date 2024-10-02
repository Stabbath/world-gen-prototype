import math
import pygame
import sys
import traceback
import random

# ------------------------------
# Constants and Configurations
# ------------------------------

# Screen settings
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
BACKGROUND_COLOR = (255, 255, 255)  # White background

# Hexagon settings
HEX_SIZE = 30  # Initial radius of the hexagon
HEX_HEIGHT = math.sqrt(3) * HEX_SIZE
HEX_WIDTH = 2 * HEX_SIZE
VERTICAL_SPACING = HEX_HEIGHT
HORIZONTAL_SPACING = HEX_WIDTH * 0.75  # Flat-topped hexagons overlap horizontally by 25%

# Initial Grid settings
INITIAL_GRID_COLS = 25  # Increased grid size for better visual effect
INITIAL_GRID_ROWS = 25  # Increased grid size for better visual effect

# Colors (default values)
DEFAULT_HEX_COLOR = (173, 216, 230)               # Light blue (ocean)
DEFAULT_OUTLINE_COLOR = (0, 0, 0)                 # Black
LABEL_COLOR = (255, 255, 255)        # White

SELECTED_HEX_COLOR = (0, 0, 0)             # Black
SELECTED_LABEL_COLOR = (255, 255, 255)    # White
SELECTED_OUTLINE_COLOR = (255, 255, 255)  # White

LINE_HEX_COLOR = (0, 0, 0)                 # Black (fault lines)
LINE_LABEL_COLOR = (255, 255, 255)        # White
LINE_OUTLINE_COLOR = (255, 255, 255)      # White

# Font settings
FONT_NAME = None  # Default font
BASE_FONT_SIZE = 14  # Base font size for hex labels

# Zoom settings
ZOOM_STEP = 1.1  # Zoom in/out factor per mouse wheel event
MIN_ZOOM = 0.5    # Minimum zoom level
MAX_ZOOM = 3.0    # Maximum zoom level

# Number of tiles to select
INITIAL_N_SELECTED_TILES = 12  # Number of starting points along the boundaries

# Line Generation Option
STOP_ON_INTERSECTION = True

# Directions
DIRECTIONS = ['N', 'NE', 'SE', 'S', 'SW', 'NW']

# Opposite Directions Mapping
OPPOSITE_DIRECTIONS = {
    'N': 'S',
    'NE': 'SW',
    'SE': 'NW',
    'S': 'N',
    'SW': 'NE',
    'NW': 'SE'
}

# Direction Angles (for flat-topped hexagons)
DIRECTION_ANGLES = {
    'N': 0,
    'NE': 60,
    'SE': 120,
    'S': 180,
    'SW': 240,
    'NW': 300
}

# Neighbor deltas based on column parity
NEIGHBOR_DELTAS = {
    'even': {
        'N': (0, -1),
        'NE': (1, -1),
        'SE': (1, 0),
        'S': (0, 1),
        'SW': (-1, 0),
        'NW': (-1, -1)
    },
    'odd': {
        'N': (0, -1),
        'NE': (1, 0),
        'SE': (1, 1),
        'S': (0, 1),
        'SW': (-1, 1),
        'NW': (-1, 0)
    }
}

# Adjacent directions mapping to avoid sharp turns
ADJACENT_DIRECTIONS = {
    'N': ['NW', 'N', 'NE'],
    'NE': ['N', 'NE', 'SE'],
    'SE': ['NE', 'SE', 'S'],
    'S': ['SE', 'S', 'SW'],
    'SW': ['S', 'SW', 'NW'],
    'NW': ['SW', 'NW', 'N']
}

# Branching parameters
BRANCHING_CHANCE = 0.1  # Probability of branching at each tile
MAX_BRANCH_DEPTH = 2    # Maximum depth of branching

# ------------------------------
# Camera Class Definition
# ------------------------------

class Camera:
    def __init__(self, zoom=1.0, offset=(0, 0)):
        """
        Initialize the Camera.

        :param zoom: Initial zoom factor
        :param offset: Initial offset (x, y)
        """
        self.zoom = zoom
        self.offset = pygame.math.Vector2(offset)

    def world_to_screen(self, pos):
        """
        Convert world coordinates to screen coordinates based on zoom and offset.

        :param pos: Tuple (x, y) in world coordinates
        :return: Tuple (x, y) in screen coordinates
        """
        return (
            (pos[0] * self.zoom) + self.offset.x,
            (pos[1] * self.zoom) + self.offset.y
        )

    def adjust_zoom(self, zoom_change, mouse_pos):
        """
        Adjust the zoom factor and offset to zoom centered around the mouse position.

        :param zoom_change: Factor to adjust the zoom (e.g., 1.1 for zooming in)
        :param mouse_pos: Tuple (x, y) of the mouse position in screen coordinates
        """
        # Calculate the world coordinates before zoom
        world_x_before = (mouse_pos[0] - self.offset.x) / self.zoom
        world_y_before = (mouse_pos[1] - self.offset.y) / self.zoom

        # Adjust zoom
        new_zoom = self.zoom * zoom_change
        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, new_zoom))  # Clamp zoom

        # Update zoom
        self.zoom = new_zoom

        # Calculate the world coordinates after zoom
        world_x_after = (mouse_pos[0] - self.offset.x) / self.zoom
        world_y_after = (mouse_pos[1] - self.offset.y) / self.zoom

        # Adjust offset to keep the point under the mouse stationary
        self.offset.x += (world_x_after - world_x_before) * self.zoom
        self.offset.y += (world_y_after - world_y_before) * self.zoom

# ------------------------------
# HexTile Class Definition
# ------------------------------

class HexTile:
    def __init__(self, col, row, center, size):
        """
        Initialize a HexTile.

        :param col: Column number (starting at 1)
        :param row: Row number (starting at 1)
        :param center: Tuple (x, y) for the center position in world coordinates
        :param size: Radius of the hexagon
        """
        self.col = col
        self.row = row
        self.center = pygame.math.Vector2(center)
        self.size = size
        self.is_selected = False
        self.is_line = False
        self.grid = None  # Will be set later

    def get_corners(self):
        """
        Calculate the six corner points of the hexagon in world coordinates.

        :return: List of (x, y) tuples for each corner
        """
        corners = []
        for i in range(6):
            angle_deg = 60 * i  # Flat-topped hexagons
            angle_rad = math.radians(angle_deg)
            x = self.center.x + self.size * math.cos(angle_rad)
            y = self.center.y + self.size * math.sin(angle_rad)
            corners.append((x, y))
        return corners

    def draw(self, screen, camera):
        """
        Draw the hexagon and its label on the screen.

        :param screen: Pygame surface to draw on
        :param camera: Camera object for coordinate transformations
        """
        # Determine colors based on tile status
        if self.is_selected:
            fill_color = SELECTED_HEX_COLOR
            outline_color = SELECTED_OUTLINE_COLOR
            label_color = SELECTED_LABEL_COLOR
        elif self.is_line:
            fill_color = LINE_HEX_COLOR
            outline_color = LINE_OUTLINE_COLOR
            label_color = LINE_LABEL_COLOR
        elif hasattr(self, 'continent_label'):
            fill_color = self.grid.continent_colors[self.continent_label]
            outline_color = DEFAULT_OUTLINE_COLOR
            label_color = LABEL_COLOR
        else:
            fill_color = DEFAULT_HEX_COLOR
            outline_color = DEFAULT_OUTLINE_COLOR
            label_color = LABEL_COLOR

        # Get transformed corners
        world_corners = self.get_corners()
        screen_corners = [camera.world_to_screen(corner) for corner in world_corners]

        # Draw filled hexagon
        pygame.draw.polygon(screen, fill_color, screen_corners)
        # Draw hexagon outline
        pygame.draw.polygon(screen, outline_color, screen_corners, 2)

        # Prepare label
        label = f"({self.col},{self.row})"
        if hasattr(self, 'continent_label'):
            label += f" {self.continent_label}"

        # Font size for labels scales with zoom
        adjusted_font_size = max(int(BASE_FONT_SIZE * camera.zoom), 8)
        try:
            adjusted_font = pygame.font.SysFont(FONT_NAME, adjusted_font_size)
        except Exception as e:
            print(f"Error initializing font for label '{label}':", e)
            adjusted_font = pygame.font.Font(None, adjusted_font_size)
        text_surface = adjusted_font.render(label, True, label_color)
        text_rect = text_surface.get_rect(center=camera.world_to_screen(self.center))
        screen.blit(text_surface, text_rect)

# ------------------------------
# HexGrid Class Definition
# ------------------------------

class HexGrid:
    def __init__(self, cols, rows, size, offset_x=100, offset_y=100, hex_color=DEFAULT_HEX_COLOR, outline_color=DEFAULT_OUTLINE_COLOR):
        """
        Initialize the HexGrid.

        :param cols: Number of columns
        :param rows: Number of rows
        :param size: Radius of each hexagon
        :param offset_x: Horizontal offset from the screen's origin
        :param offset_y: Vertical offset from the screen's origin
        :param hex_color: Color of the hexagons
        :param outline_color: Color of the hexagon outlines
        """
        self.cols = cols
        self.rows = rows
        self.size = size
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.hex_color = hex_color
        self.outline_color = outline_color
        self.continent_colors = {}
        self.tiles = self.generate_grid()

    def generate_grid(self):
        """
        Generate the grid of HexTile instances.

        :return: List of HexTile objects
        """
        tiles = []
        for row in range(1, self.rows + 1):
            for col in range(1, self.cols + 1):
                # Calculate the position of the hex center in world coordinates
                x = self.offset_x + (col - 1) * HORIZONTAL_SPACING
                y = self.offset_y + (row - 1) * VERTICAL_SPACING
                if col % 2 == 0:
                    y -= VERTICAL_SPACING / 2  # Shift even columns upwards
                center = (x, y)
                tile = HexTile(col, row, center, self.size)
                tile.grid = self  # Set reference to grid
                tiles.append(tile)
        return tiles

    def select_distributed_boundary_tiles(self, n):
        """
        Select n tiles from the boundaries, ensuring a distribution among all sides.

        :param n: Total number of tiles to select
        :return: List of selected HexTile objects
        """
        # Get boundary tiles for each side
        top_tiles = [tile for tile in self.tiles if tile.row == 1]
        bottom_tiles = [tile for tile in self.tiles if tile.row == self.rows]
        left_tiles = [tile for tile in self.tiles if tile.col == 1]
        right_tiles = [tile for tile in self.tiles if tile.col == self.cols]

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

    def get_weighted_initial_directions(self, tile):
        """
        Get possible initial directions for a tile with weights,
        favoring directions opposite to the boundary side.

        :param tile: HexTile object
        :return: List of tuples (direction, weight)
        """
        direction_weights = {}

        # Check for corners first
        if tile.row == 1 and tile.col == 1:
            # Top-left corner
            direction_weights['SE'] = 1
        elif tile.row == 1 and tile.col == self.cols:
            # Top-right corner
            direction_weights['SW'] = 1
        elif tile.row == self.rows and tile.col == 1:
            # Bottom-left corner
            direction_weights['NE'] = 1
        elif tile.row == self.rows and tile.col == self.cols:
            # Bottom-right corner
            direction_weights['NW'] = 1
        else:
            # Edge conditions (non-corner)
            if tile.row == 1:
                # Top edge
                direction_weights['S'] = 0.7
                direction_weights['SE'] = 0.15
                direction_weights['SW'] = 0.15
            if tile.row == self.rows:
                # Bottom edge
                direction_weights['N'] = 0.7
                direction_weights['NE'] = 0.15
                direction_weights['NW'] = 0.15
            if tile.col == 1:
                # Left edge
                direction_weights['NE'] = 0.5
                direction_weights['SE'] = 0.5
            if tile.col == self.cols:
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

    def generate_lines_in_directions(self, selected_tiles):
        """
        From each selected tile, generate lines moving in one direction until the boundary or intersection.

        :param selected_tiles: List of HexTile objects that are selected
        """
        for tile in selected_tiles:
            # Get weighted possible initial directions based on tile position
            weighted_directions = self.get_weighted_initial_directions(tile)
            if weighted_directions:
                # Randomly choose one initial direction based on weights
                directions, weights = zip(*weighted_directions)
                initial_direction = random.choices(directions, weights=weights)[0]
                print(f"Generating line from Tile ({tile.col}, {tile.row}) towards {initial_direction}")
                self.generate_line(tile, initial_direction, initial_direction, MAX_BRANCH_DEPTH)
            else:
                print(f"No possible initial directions for Tile ({tile.col}, {tile.row})")

    def generate_line(self, start_tile, direction, initial_direction, branch_depth):
        """
        Generate a line from the start_tile, moving randomly without sharp turns,
        preferring to continue towards the initial direction. Allows for branching.

        :param start_tile: HexTile object to start the line from
        :param direction: Current direction string ('N', 'NE', 'SE', 'S', 'SW', 'NW')
        :param initial_direction: The initial preferred direction
        :param branch_depth: Remaining branching depth
        """
        current_tile = start_tile
        current_direction = direction
        visited_tiles = set()
        while True:
            next_tile = self.get_neighbor(current_tile, current_direction)
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
                            self.generate_line(next_tile, branch_direction, initial_direction, branch_depth - 1)

                    # Decide the next direction, favoring the initial direction
                    allowed_directions = ADJACENT_DIRECTIONS[current_direction]
                    weights = []
                    for d in allowed_directions:
                        angle_diff = self.angular_difference(DIRECTION_ANGLES[d], DIRECTION_ANGLES[initial_direction])
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

    def angular_difference(self, angle1, angle2):
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

    def get_neighbor(self, tile, direction):
        """
        Get the neighboring tile in the specified direction.

        :param tile: Current HexTile object
        :param direction: Direction string ('N', 'NE', 'SE', 'S', 'SW', 'NW')
        :return: Neighbor HexTile object or None if out of bounds
        """
        parity = 'even' if tile.col % 2 == 0 else 'odd'
        delta = NEIGHBOR_DELTAS[parity].get(direction)
        if not delta:
            return None
        neighbor_col = tile.col + delta[0]
        neighbor_row = tile.row + delta[1]
        # Check if the neighbor is within grid bounds
        if 1 <= neighbor_col <= self.cols and 1 <= neighbor_row <= self.rows:
            return self.get_tile(neighbor_col, neighbor_row)
        else:
            return None

    def get_tile(self, col, row):
        """
        Retrieve the tile at a specific (col, row).

        :param col: Column number
        :param row: Row number
        :return: HexTile object or None if not found
        """
        return next((tile for tile in self.tiles if tile.col == col and tile.row == row), None)

    def label_continents(self):
        """
        Label each continent (region) separated by fault lines with a unique label.
        """
        label_counter = 0
        continent_labels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        colors = self.generate_continent_colors()
        self.continent_colors = {}
        for tile in self.tiles:
            if not tile.is_line and not hasattr(tile, 'continent_label'):
                # Start a new continent
                label = continent_labels[label_counter % len(continent_labels)]
                color = colors[label_counter % len(colors)]
                self.flood_fill(tile, label)
                self.continent_colors[label] = color
                label_counter +=1

        print(f"Labeled {label_counter} continents.")

    def flood_fill(self, start_tile, label):
        """
        Perform flood fill to label connected tiles.

        :param start_tile: HexTile object to start flood fill from
        :param label: Continent label to assign
        """
        stack = [start_tile]
        while stack:
            tile = stack.pop()
            if not hasattr(tile, 'continent_label') and not tile.is_line:
                tile.continent_label = label
                # Get neighbors
                for direction in DIRECTIONS:
                    neighbor = self.get_neighbor(tile, direction)
                    if neighbor and not neighbor.is_line and not hasattr(neighbor, 'continent_label'):
                        stack.append(neighbor)

    def generate_continent_colors(self):
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

    def convert_isolated_tiles_to_fault_lines(self):
        """
        Convert tiles completely surrounded by fault lines into fault lines themselves.
        """
        to_convert = []
        for tile in self.tiles:
            if not tile.is_line:
                all_neighbors_fault_line = True
                for direction in DIRECTIONS:
                    neighbor = self.get_neighbor(tile, direction)
                    if neighbor and not neighbor.is_line:
                        all_neighbors_fault_line = False
                        break
                if all_neighbors_fault_line:
                    to_convert.append(tile)
        # Convert the tiles after checking all to avoid modifying the list during iteration
        for tile in to_convert:
            tile.is_line = True
            print(f"Converted isolated Tile ({tile.col}, {tile.row}) to fault line")

    def draw(self, screen, camera):
        """
        Draw all hex tiles on the screen.

        :param screen: Pygame surface to draw on
        :param camera: Camera object for coordinate transformations
        """
        for tile in self.tiles:
            tile.draw(screen, camera)

# ------------------------------
# Pygame Initialization and Main Loop
# ------------------------------

def main():
    try:
        # Initialize Pygame
        pygame.init()
        pygame.font.init()  # Initialize font module

        # Set up the display
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Hexagonal Grid with Multi-Segment Fault Lines and Continents")

        # Create a clock to manage the frame rate
        clock = pygame.time.Clock()

        # Initialize font
        try:
            font = pygame.font.SysFont(FONT_NAME, 24)
        except Exception as e:
            print("Error initializing font:", e)
            font = pygame.font.Font(None, 24)

        # Initialize Camera
        camera = Camera(zoom=1.0, offset=(0, 0))

        # Variables for panning
        is_panning = False
        pan_start_pos = pygame.math.Vector2(0, 0)
        pan_start_offset = pygame.math.Vector2(0, 0)

        # Create the hex grid by regenerating the map
        hex_grid = None
        selected_tiles = []

        def regenerate_map():
            nonlocal hex_grid, selected_tiles
            try:
                # Get values from constants
                n_selected = INITIAL_N_SELECTED_TILES
                cols = INITIAL_GRID_COLS
                rows = INITIAL_GRID_ROWS
                hex_color = DEFAULT_HEX_COLOR
                outline_color = DEFAULT_OUTLINE_COLOR

                # Create new hex grid
                hex_grid = HexGrid(cols, rows, HEX_SIZE, offset_x=100, offset_y=100, hex_color=hex_color, outline_color=outline_color)

                # Select boundary tiles
                selected_tiles = hex_grid.select_distributed_boundary_tiles(n_selected)
                print(f"Selected {n_selected} boundary tiles for line generation.")

                # Generate lines
                hex_grid.generate_lines_in_directions(selected_tiles)
                print("Generated lines from boundary tiles.")

                # Convert isolated tiles to fault lines
                #hex_grid.convert_isolated_tiles_to_fault_lines()

                # Label continents
                hex_grid.label_continents()

            except Exception as e:
                print("Error regenerating map:", e)

        # Initial map generation
        regenerate_map()

        # Main loop flag
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Handle zooming with mouse wheel
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:  # Mouse wheel up to zoom in
                        mouse_pos = event.pos
                        camera.adjust_zoom(ZOOM_STEP, mouse_pos)
                        print(f"Zoomed in to {camera.zoom:.2f}x")
                    elif event.button == 5:  # Mouse wheel down to zoom out
                        mouse_pos = event.pos
                        camera.adjust_zoom(1 / ZOOM_STEP, mouse_pos)
                        print(f"Zoomed out to {camera.zoom:.2f}x")
                    elif event.button == 1:  # Left mouse button to start panning
                        is_panning = True
                        pan_start_pos = pygame.math.Vector2(event.pos)
                        pan_start_offset = camera.offset.copy()
                        print("Started panning")

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left mouse button to stop panning
                        is_panning = False
                        print("Stopped panning")

                elif event.type == pygame.MOUSEMOTION:
                    if is_panning:
                        current_pos = pygame.math.Vector2(event.pos)
                        delta = current_pos - pan_start_pos
                        camera.offset = pan_start_offset + delta

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # Regenerate the map
                        regenerate_map()
                        print("Map regenerated")

            # Clear the screen
            screen.fill(BACKGROUND_COLOR)

            # Draw the hex grid with labels
            if hex_grid:
                hex_grid.draw(screen, camera)

            # Update the display
            pygame.display.flip()

            # Cap the frame rate at 60 FPS
            clock.tick(60)

    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()
    finally:
        # Quit Pygame
        pygame.quit()
        sys.exit()

# ------------------------------
# Entry Point
# ------------------------------

if __name__ == "__main__":
    main()
