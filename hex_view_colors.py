WHITE  = (255,255,255)
BLACK  = (0,0,0)
RED    = (255,0,0)
YELLOW = (255,255,0)

# Colors (default values)
DEFAULT_HEX_COLOR = (173, 216, 230) # Light blue (ocean)
DEFAULT_OUTLINE_COLOR = BLACK
LABEL_COLOR = BLACK
LINE_HEX_COLOR = BLACK
LINE_OUTLINE_COLOR = BLACK
LINE_LABEL_COLOR = WHITE

color_dict = {
    'default_hex':  DEFAULT_HEX_COLOR,
    'default_outline':  DEFAULT_OUTLINE_COLOR,
    'default_label':  LABEL_COLOR,
    'line_hex':  LINE_HEX_COLOR,
    'line_outline':  LINE_OUTLINE_COLOR,
    'line_label':  LINE_LABEL_COLOR
}

def color_plates(viewTile, config):
    if viewTile.tile.plate_index is not None:
        color = color_generator(viewTile.tile.plate_index)
        return (color, BLACK, BLACK)
    if viewTile.tile.fault_index is not None:
        return (BLACK, BLACK, WHITE)
    return WHITE, WHITE, RED

def color_faults(viewTile, config):
    if viewTile.tile.is_selected or viewTile.tile.is_line:
        fill_color = color_dict['line_hex']
        outline_color = color_dict['line_outline']
        label_color = color_dict['line_label']
    elif viewTile.tile.continent_label is not None:
        fill_color = viewTile.gridview.grid.continent_colors[viewTile.tile.continent_label]
        outline_color = color_dict['default_outline']
        label_color = color_dict['default_label']
    else:
        fill_color = color_dict['default_hex']
        outline_color = color_dict['default_outline']
        label_color = color_dict['default_label']
    return fill_color, outline_color, label_color
    
def color_altitude(viewTile, config):
    value = 255 * int(viewTile.tile.altitude) // config['max_altitude']
    return (value, value, value), (value, value, value), RED

def color_hydro(viewTile, config):
    if viewTile.tile.altitude <= config['sea_level']:
        return (32, 128, 255), (32, 128, 255), BLACK
    return color_altitude(viewTile, config)
    
def color_generator(index):
    if index is None: # fault
        return (0,0,0)
    
    # Total combinations: 6x6 = 36. Change this if the multipliers array is changed
    if index >= 36:
        return (255, 255, 255) # return White if out of bounds
        
    matrices = [
        [(1,0,0),(0,0,0)],
        [(0,1,0),(0,0,0)],
        [(0,0,1),(0,0,0)],
        [(1,0,0),(0,1,0)],
        [(1,0,0),(0,0,1)],
        [(0,1,0),(0,0,1)]
    ]
    
    multipliers = [
        (255, 255),
        (128, 128),
        (255, 165),
        (165, 255),
        (192, 96),
        (96, 192)
    ]

    # Calculate sub-indices directly from the provided index
    matrix_index = index % len(matrices)
    index = index // len(matrices)

    multipliers_index = index

    matrix = matrices[matrix_index]
    multipliers = multipliers[multipliers_index]
    
    # Compute the color using the selected matrices and multipliers
    color = [
        matrix[0][i] * multipliers[0] + matrix[1][i] * multipliers[1]
        for i in range(3)
    ]
    
    return color