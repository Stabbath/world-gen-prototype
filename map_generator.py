from neighbor_functions import get_neighbors_wraparound
from hex_grid import HexGrid
from generators.tectonic_generator_faults import generate_world_faults
from generators.tectonic_generator_plates import generate_world_plates

# Function to regenerate the map
def generate_map(config, func_neighbors=get_neighbors_wraparound):
    cols = config['width']
    rows = config['height']
    gen_method = config['gen_method']
    hex_grid = HexGrid(width=cols, height=rows, func_neighbors=func_neighbors)
    if gen_method == 'faults':
        hex_grid = generate_world_faults(hex_grid, n_selected=config['startpoint_count'])
        print("Generated world using fault-based method.")
    else:
        hex_grid = generate_world_plates(hex_grid, config, func_neighbors=func_neighbors)
        print("Generated world using plate-based method.")
    return hex_grid

