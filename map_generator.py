from neighbor_functions import get_neighbors_wraparound
from hex_board_generator import HexGrid
from fault_method import generate_world_faults
from plate_method import generate_world_plates

# Number of tiles to select for fault generation
INITIAL_N_SELECTED_TILES = 12  # Number of starting points along the boundaries

# Function to regenerate the map
def generate_map(gen_method=0, cols=50, rows=50, size=20, offset_x=100, offset_y=100, n_selected=12):
    hex_grid = HexGrid(cols=cols, rows=rows, size=size, offset_x=offset_x, offset_y=offset_y)
    if gen_method == 0:
        generate_world_faults(hex_grid, n_selected=INITIAL_N_SELECTED_TILES, func_neighbors=get_neighbors_wraparound)
        print("Generated world using fault-based method.")
    else:
        generate_world_plates(hex_grid, plate_count=12, func_neighbors=get_neighbors_wraparound)
        print("Generated world using plate-based method.")
    return hex_grid

