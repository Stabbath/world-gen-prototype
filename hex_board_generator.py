
import math
import pygame
import random
from collections import deque


# Define compass directions for flat-top hexagons as per user specification
COMPASS_DIRECTIONS = {
    'north': (0, 1),
    'south': (0, -1),
    'northeast': (1, 1),
    'northwest': (-1, 1),
    'southeast': (-1, 0),
    'southwest': (1, 0)
}

DIRECTION_NAMES = ['north', 'northeast', 'southeast', 'south', 'southwest', 'northwest']

class HexTile:
    def __init__(self, row, col, center, size):
        self.row = row
        self.col = col
        self.center = center  # (x, y) coordinates of the hex center
        self.size = size

    def hex_corners(self):
        """Calculate the six corners of the hexagon."""
        return [self.hex_corner(i) for i in range(6)]

    def hex_corner(self, i):
        """Calculate the corner of a hexagon (using radians)."""
        angle_deg = 60 * i  # Flat-top hexagon adjustment
        angle_rad = math.radians(angle_deg)
        return [
            self.center[0] + self.size * math.cos(angle_rad),
            self.center[1] + self.size * math.sin(angle_rad)
        ]

    def draw(self, screen, fillcolor, outlinecolor, zoom_factor, zoom_center, camera_offset, font, fault_info=None):
        """
        Draw the hexagon on the screen with zoom centered at zoom_center.
        fault_info: Tuple (fault_index, iteration_number) or None
        """
        # Adjust center with camera offset
        adjusted_center = (
            self.center[0] + camera_offset[0],
            self.center[1] + camera_offset[1]
        )

        # Calculate relative position to zoom center
        rel_x = adjusted_center[0] - zoom_center[0]
        rel_y = adjusted_center[1] - zoom_center[1]

        # Apply zoom factor
        zoomed_center = (
            zoom_center[0] + rel_x * zoom_factor,
            zoom_center[1] + rel_y * zoom_factor
        )

        # Calculate zoomed and offset corners
        corners = []
        for corner in self.hex_corners():
            # Adjust corner with camera offset
            adjusted_corner = (
                corner[0] + camera_offset[0],
                corner[1] + camera_offset[1]
            )
            # Calculate relative position to zoom center
            rel_corner_x = adjusted_corner[0] - zoom_center[0]
            rel_corner_y = adjusted_corner[1] - zoom_center[1]
            # Apply zoom factor
            zoomed_corner = (
                zoom_center[0] + rel_corner_x * zoom_factor,
                zoom_center[1] + rel_corner_y * zoom_factor
            )
            corners.append(zoomed_corner)

        # Draw filled hex
        pygame.draw.polygon(screen, fillcolor, corners, 0)
        # Draw hex outline
        pygame.draw.polygon(screen, outlinecolor, corners, 2)

        # Draw fault index and iteration number labels if present
        if fault_info is not None:
            fault_index, iteration_number = fault_info
            # Combine labels, e.g., "F1-I3"
            label_text = f"F{fault_index}-I{iteration_number}"
            # Render the label
            text_surface = font.render(label_text, True, (255, 255, 255))  # White text for contrast
            text_rect = text_surface.get_rect(center=zoomed_center)
            screen.blit(text_surface, text_rect)


class HexGrid:
    def __init__(self, width, height, size):
        self.width = width
        self.height = height
        self.size = size
        self.grid = self.generate_grid()

    def generate_grid(self):
        """Generate the hexagonal grid and return a list of HexTile objects."""
        hex_height = math.sqrt(3) * self.size  # Height of hex from top to bottom
        hex_width = 2 * self.size  # Width of hex from one corner to another
        vertical_spacing = hex_height
        horizontal_spacing = hex_width * 0.75  # Flat-topped alignment adjustment

        grid = []
        for row in range(1, self.height + 1):  # Rows start at 1
            for col in range(1, self.width + 1):  # Columns start at 1
                x_offset = (col - 1) * horizontal_spacing
                y_offset = (row - 1) * vertical_spacing
                if col % 2 == 0:  # Even-numbered columns are shifted upwards
                    y_offset -= vertical_spacing / 2
                # Create a new hex tile and store it in the grid
                grid.append(HexTile(row, col, (x_offset + 100, y_offset + 100), self.size))

        return grid

    def draw(self, screen, fault_tiles, zoom_factor, zoom_center, camera_offset, font):
        """Draw the hex grid on the screen, coloring based on whether a tile is part of a fault."""
        for hex_tile in self.grid:
            fault_info = fault_tiles.get((hex_tile.row, hex_tile.col))  # Tuple (fault_index, iteration_number) or None
            if fault_info is not None:
                fillcolor = (0, 0, 0)  # Fault tiles are black
                outlinecolor = (255, 255, 255)  # White outline for contrast
            else:
                fillcolor = (173, 216, 230)  # Regular tiles use a base color (light blue)
                outlinecolor = (0, 0, 0)  # Outline color for non-fault hexes (black)

            hex_tile.draw(
                screen,
                fillcolor,
                outlinecolor,
                zoom_factor,
                zoom_center,
                camera_offset,
                font,
                fault_info=fault_info
            )


class FaultFront:
    def __init__(self, row, col, direction_name, fault_index, previous_direction_name=None):
        self.row = row
        self.col = col
        self.direction_name = direction_name  # Compass direction name
        self.fault_index = fault_index  # Unique fault identifier
        self.previous_direction_name = previous_direction_name  # To prevent immediate reversal


class FaultGenerator:
    def __init__(self, map_width, map_height, num_faults, seed=42, noise_prob=0.2):
        self.map_width = map_width
        self.map_height = map_height
        self.num_faults = num_faults
        self.seed = seed
        self.noise_prob = noise_prob  # Probability to change direction slightly

    def get_hex_neighbors(self, row, col):
        """Return the neighboring hexes with their compass directions."""
        neighbors = []
        for direction_name in DIRECTION_NAMES:
            dr, dc = COMPASS_DIRECTIONS[direction_name]
            new_row = row + dr
            new_col = col + dc
            # Check boundaries (non-periodic)
            if 0 <= new_row < self.map_height and 0 <= new_col < self.map_width:
                neighbors.append(((new_row, new_col), direction_name))
        return neighbors

    def is_opposite_direction(self, direction1, direction2):
        """Check if two compass directions are opposite of each other."""
        opposite = {
            'north': 'south',
            'south': 'north',
            'northeast': 'southwest',
            'southwest': 'northeast',
            'southeast': 'northwest',
            'northwest': 'southeast'
        }
        return opposite.get(direction1) == direction2

    def get_opposite_direction(self, direction_name):
        """Get the opposite compass direction."""
        opposite = {
            'north': 'south',
            'south': 'north',
            'northeast': 'southwest',
            'southwest': 'northeast',
            'southeast': 'northwest',
            'northwest': 'southeast'
        }
        return opposite.get(direction_name, None)

    def get_adjacent_directions(self, direction_name):
        """Get left and right adjacent directions for smoother propagation."""
        index = DIRECTION_NAMES.index(direction_name)
        left = DIRECTION_NAMES[(index - 1) % len(DIRECTION_NAMES)]
        right = DIRECTION_NAMES[(index + 1) % len(DIRECTION_NAMES)]
        return [left, right]

    def generate_faults(self):
        """Generate fault lines based on the specified algorithm."""
        random.seed(self.seed)
        fault_tiles = dict()  # Dict to store all fault tiles with (fault_index, iteration_number)
        fault_fronts = deque()  # Queue to manage fault fronts
        step = 0  # Initialize iteration counter

        # Step 1 & 2: Choose N random starting points and assign initial directions
        for fault_index in range(1, self.num_faults + 1):
            row = random.randint(1, self.map_height)  # Rows start at 1
            col = random.randint(1, self.map_width)   # Columns start at 1

            # Ensure unique starting points
            while (row, col) in fault_tiles:
                row = random.randint(1, self.map_height)
                col = random.randint(1, self.map_width)

            fault_tiles[(row, col)] = (fault_index, step)  # Assign fault index and iteration number

            # Choose a random initial direction
            direction_name = random.choice(DIRECTION_NAMES)
            opposite_direction_name = self.get_opposite_direction(direction_name)

            # Initialize fault fronts in both forward and backward directions
            fault_fronts.append(FaultFront(row, col, direction_name, fault_index))
            fault_fronts.append(FaultFront(row, col, opposite_direction_name, fault_index))

        # Step 3-7: Extend faults simultaneously
        while fault_fronts:
            step += 1  # Increment iteration counter at each propagation step
            fronts_to_process = len(fault_fronts)
            current_step_fronts = []

            # Gather all fronts to process in this step
            for _ in range(fronts_to_process):
                front = fault_fronts.popleft()
                current_step_fronts.append(front)

            # Process each front
            for front in current_step_fronts:
                current_row, current_col = front.row, front.col
                direction_name = front.direction_name
                fault_index = front.fault_index
                previous_direction_name = front.previous_direction_name

                # Step 3 & 4: Propagate forward or backward
                neighbors = self.get_hex_neighbors(current_row, current_col)
                target = None
                for (nr, nc), dir_name in neighbors:
                    if dir_name == direction_name:
                        target = (nr, nc)
                        break

                if not target:
                    continue  # Cannot propagate in this direction (boundary)

                new_row, new_col = target

                # Step 5: Check if new tile is already a fault or at boundary
                if (new_row, new_col) in fault_tiles:
                    continue  # Stop propagation in this direction

                # Step 6: Check neighbors for intersection
                fault_neighbor_count = 0
                for (nr, nc), _ in self.get_hex_neighbors(new_row, new_col):
                    if (nr, nc) in fault_tiles:
                        fault_neighbor_count += 1
                    if fault_neighbor_count > 1:
                        break

                if fault_neighbor_count > 1:
                    continue  # Stop propagation due to intersection

                # Add the new tile to faults with the current step
                fault_tiles[(new_row, new_col)] = (fault_index, step)

                # Step 2: Choose next direction with slight randomness
                if random.random() < self.noise_prob:
                    # Choose to change direction to left or right
                    adjacent_dirs = self.get_adjacent_directions(direction_name)
                    # Optionally include continuing in the same direction
                    possible_directions = adjacent_dirs + [direction_name]
                    new_direction_name = random.choice(possible_directions)
                else:
                    # Continue in the same direction
                    new_direction_name = direction_name

                # Prevent immediate reversal
                if previous_direction_name and self.is_opposite_direction(new_direction_name, previous_direction_name):
                    new_direction_name = direction_name  # Revert to original direction

                # Step 6: Check if the new direction is valid (not reversing)
                if self.is_opposite_direction(new_direction_name, direction_name):
                    continue  # Invalid direction change, skip

                # Step 7: Append the new front with updated direction
                fault_fronts.append(FaultFront(new_row, new_col, new_direction_name, fault_index, direction_name))
                
        return fault_tiles