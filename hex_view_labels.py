import pygame

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
