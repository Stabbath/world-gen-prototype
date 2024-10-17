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
    
    # Create an arrow representation (a line with a triangle at the end)
    length = size
    end_pos = (tile.col + length * math.cos(angle), tile.row + length * math.sin(angle))
    
    # Draw a line for wind direction
    line_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.line(line_surface, color, (tile.col, tile.row), end_pos, 2)
    
    # Draw the arrow head
    arrow_size = size * 0.3
    arrow_angle1 = angle + math.pi / 6  # Angle for one side of the arrowhead
    arrow_angle2 = angle - math.pi / 6  # Angle for the other side
    point1 = (end_pos[0] + arrow_size * math.cos(arrow_angle1), end_pos[1] + arrow_size * math.sin(arrow_angle1))
    point2 = (end_pos[0] + arrow_size * math.cos(arrow_angle2), end_pos[1] + arrow_size * math.sin(arrow_angle2))
    pygame.draw.polygon(line_surface, color, [end_pos, point1, point2])
    
    return line_surface

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
