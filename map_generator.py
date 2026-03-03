from neighbor_functions import get_neighbors_wraparound
from hex_grid import HexGrid
from generators.tectonic_generator_faults import generate_world_faults
from generators.tectonic_generator_plates import generate_world_plates

# Function to regenerate the map
def generate_map(config, func_neighbors=get_neighbors_wraparound):
    """
    Generates a hex grid map based on the specified configuration and generation method.

    Parameters:
    ----------
    config : dict
        A configuration dictionary containing map parameters such as:
        - 'width': int, the number of hex columns.
        - 'height': int, the number of hex rows.
        - 'gen_method': str, the method to generate the world ('faults' or 'plates').
    
    func_neighbors : function, optional
        A function to define how neighbors of a hex tile are calculated.
        The default function is `get_neighbors_wraparound`, which handles wraparound behavior
        at the edges of the grid (making the map behave as a continuous surface, like a torus).

    Returns:
    -------
    hex_grid : HexGrid
        The generated hex grid map, populated with data based on the chosen generation method.

    Generation Methods:
    -------------------
    - 'faults': The map is generated using a fault-based algorithm that simulates tectonic faults
                first and after defines the tectonic plates.
                Calls the function `generate_world_faults`.

    - 'plates': The map is generated using a plate-based algorithm that generates tectonic plates first
                and after defines the faults from the intersection. 
                Calls the function `generate_world_plates`.

    Notes:
    -----
    - This function relies on external helper functions like `generate_world_faults`, 
      `generate_world_plates`, and `HexGrid`.
    - The function prints a message indicating the method used to generate the world.
    """
    # Extract map dimensions and generation method from the configuration
    cols = config['width']  # Number of columns (hex grid width)
    rows = config['height']  # Number of rows (hex grid height)
    gen_method = config['gen_method']  # World generation method ('faults' or 'plates')

    # Create an empty hex grid with the specified dimensions
    hex_grid = HexGrid(width=cols, height=rows, func_neighbors=func_neighbors)

    # Generate the world based on the specified method
    if gen_method == 'faults':
        # Use fault-based world generation
        hex_grid = generate_world_faults(hex_grid, config, func_neighbors=func_neighbors)
        print("Generated world using fault-based method.")
    else:
        # Use plate-based world generation
        hex_grid = generate_world_plates(hex_grid, config, func_neighbors=func_neighbors)
        print("Generated world using plate-based method.")

    return hex_grid  # Return the generated hex grid

