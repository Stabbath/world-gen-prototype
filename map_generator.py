from neighbor_functions import get_neighbors_wraparound
from hex_grid import HexGrid
from generators.tectonic_generator_faults import generate_world_faults
from generators.tectonic_generator_plates import generate_world_plates

# Number of tiles to select for fault generation
INITIAL_N_SELECTED_TILES = 12  # Number of starting points along the boundaries

# Function to regenerate the map
def generate_map(gen_method=0, cols=50, rows=50, n_selected=12, func_neighbors=get_neighbors_wraparound):
    hex_grid = HexGrid(width=cols, height=rows, func_neighbors=func_neighbors)
    if gen_method == 0:
        hex_grid = generate_world_faults(hex_grid, n_selected=INITIAL_N_SELECTED_TILES, func_neighbors=func_neighbors)
        print("Generated world using fault-based method.")
    else:
        hex_grid = generate_world_plates(hex_grid, plate_count=12, func_neighbors=func_neighbors)
        print("Generated world using plate-based method.")
    return hex_grid

