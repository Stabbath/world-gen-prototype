
import math
import pygame
# Function to calculate hex corners
def hex_corner(center, size, i):
    """Calculate the corner of a hexagon (using radians)"""
    angle_deg = 60 * i  # Adjust for flat-top hex
    angle_rad = math.radians(angle_deg)
    return [center[0] + size * math.cos(angle_rad), center[1] + size * math.sin(angle_rad)]

# Function to generate a hexagon polygon
def hex_polygon(center, size):
    """Return the vertices of a hexagon centered at a point"""
    return [hex_corner(center, size, i) for i in range(6)]

# Function to generate the hexagonal grid map
def hex_grid_map(MAP_WIDTH, MAP_HEIGHT, size, outline, fillcolor, screen):
    """Generate a flat-topped hexagonal grid"""
    hex_height = math.sqrt(3) * size  # Height of hex from top to bottom
    hex_width = 2 * size  # Width of hex from one corner to another
    vertical_spacing = hex_height  # Vertical spacing between rows of hexes
    horizontal_spacing = hex_width  # Horizontal spacing between hexes
    
    for row in range(MAP_HEIGHT):
        for col in range(MAP_WIDTH):
            # Offset each second column for flat-topped alignment
            x_offset = col * horizontal_spacing * 0.75
            y_offset = row * vertical_spacing
            if col % 2 == 1:
                y_offset += vertical_spacing / 2  # Stagger odd columns vertically

            # Center of the current hex
            center = (x_offset + 100, y_offset + 100)  # Adjust offsets for screen placement

            # Draw hexagon
            pygame.draw.polygon(screen, fillcolor, hex_polygon(center, size), 0)  # Fill hex
            pygame.draw.polygon(screen, outline, hex_polygon(center, size), 2)  # Outline hex