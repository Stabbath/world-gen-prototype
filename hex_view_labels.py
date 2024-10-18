# hex_view_labels.py
import pygame
import math

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800

# Font settings
FONT_NAME = None  # Default font
BASE_FONT_SIZE = 14  # Base font size for hex labels

font_dict = {
    'base_size':  14,
    'base_name':  FONT_NAME
}

def _get_surface(string, color, camera):
    # Font size for labels scales with zoom
    adjusted_font_size = max(int(font_dict['base_size'] * camera.zoom), 8)
    try:
        adjusted_font = pygame.font.SysFont(font_dict['base_name'], adjusted_font_size)
    except:
        adjusted_font = pygame.font.Font(None, adjusted_font_size)
    text_surface = adjusted_font.render(string, True, color)
    return text_surface
    
def text_label_from_tile(tile, color, camera):
    if tile.fault_index != None:
        return None
        return _get_surface(str(tile.fault_index), color, camera)
    return None

def wind_overlay_element(tile, climate_data, ref_magnitude, draw_size, color, camera):
    wind = climate_data[tile.id]['wind']
    magnitude = math.sqrt(wind[0] * wind[0] + wind[1] * wind[1])
    scale = min(1, magnitude / ref_magnitude)
    size = scale * draw_size
    
    # Calculate angle for wind direction
    angle = math.atan2(wind[1], wind[0])
    
    # Create a triangle centered at the tile's position
    triangle_surface = pygame.Surface((draw_size, draw_size), pygame.SRCALPHA)
    
    # Triangle dimensions (scaled based on wind magnitude)
    triangle_height = size
    triangle_base = size * 0.5
    
    # Calculate the center of the tile (camera can adjust the position if needed)
    center_x = tile.col  # Adjust this with camera logic if needed
    center_y = tile.row  # Adjust this with camera logic if needed
    
    # Calculate the points of the triangle
    # The first point is at the tip of the triangle (pointing in the wind's direction)
    tip_x = center_x + triangle_height * math.cos(angle)
    tip_y = center_y + triangle_height * math.sin(angle)
    
    # The other two points form the base of the triangle, at an angle from the tip
    base_angle1 = angle + math.pi / 2
    base_angle2 = angle - math.pi / 2
    
    base_point1_x = center_x + (triangle_base / 2) * math.cos(base_angle1)
    base_point1_y = center_y + (triangle_base / 2) * math.sin(base_angle1)
    
    base_point2_x = center_x + (triangle_base / 2) * math.cos(base_angle2)
    base_point2_y = center_y + (triangle_base / 2) * math.sin(base_angle2)
    
    # Draw the triangle
    pygame.draw.polygon(triangle_surface, color, [
        (tip_x, tip_y), 
        (base_point1_x, base_point1_y), 
        (base_point2_x, base_point2_y)
    ])
    
    return triangle_surface

def water_flow_overlay_element(tile, climate_data, ref_flow, draw_size, color, camera):
    flow = climate_data[tile.id]['water_flow']
    scale = min(1, flow / ref_flow)
    size = scale * draw_size
    
    # Create a water drop or circle representation
    drop_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    
    # Calculate position and radius of the water drop
    drop_radius = max(2, int(size / 2))  # Ensures the minimum size isn't too small
    drop_position = camera.world_to_screen((tile.col, tile.row))
    
    # Draw the water drop as a filled circle
    pygame.draw.circle(drop_surface, color, drop_position, drop_radius)
    
    return drop_surface
