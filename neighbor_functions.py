# Define Neighbor Offsets for Even-Q Vertical Layout
EVEN_Q_NEIGHBORS = [ 
    (+1,  0), (+1, -1), ( 0, -1),
    (-1, -1), (-1,  0), ( 0, +1)
]

ODD_Q_NEIGHBORS = [
    (+1, +1), (+1,  0), ( 0, -1),
    (-1,  0), (-1, +1), ( 0, +1)
]

def get_neighbors(col, row, cols, rows):
    """
    Returns a list of neighboring cells' coordinates for a given cell in an even-q vertical offset grid,
    ensuring that neighbors are within grid boundaries.

    Parameters:
        col (int): The column index of the current cell.
        row (int): The row index of the current cell.
        cols (int): Total number of columns in the grid.
        rows (int): Total number of rows in the grid.

    Returns:
        List[Tuple[int, int]]: A list of (col, row) tuples representing neighboring cells within bounds.
    """
    neighbors = []

    # Determine if the column is even or odd
    if col % 2 == 0:
        deltas = EVEN_Q_NEIGHBORS
    else:
        deltas = ODD_Q_NEIGHBORS

    # Calculate neighbor positions with boundary checks
    for dc, dr in deltas:
        neighbor_col = col + dc
        neighbor_row = row + dr

        # Check if neighbor is within grid boundaries
        if 0 <= neighbor_col < cols and 0 <= neighbor_row < rows:
            neighbors.append((neighbor_col, neighbor_row))

    return neighbors

def get_neighbors_wraparound(col, row, cols, rows):
    """
    Returns a list of neighboring cells' coordinates for a given cell in an even-q vertical offset grid,
    with horizontal wraparound.

    Parameters:
        col (int): The column index of the current cell.
        row (int): The row index of the current cell.
        cols (int): Total number of columns in the grid.
        rows (int): Total number of rows in the grid.

    Returns:
        List[Tuple[int, int]]: A list of (col, row) tuples representing neighboring cells with horizontal wraparound.
    """
    neighbors = []

    # Determine if the column is even or odd
    if col % 2 == 0:
        deltas = EVEN_Q_NEIGHBORS
    else:
        deltas = ODD_Q_NEIGHBORS

    # Calculate neighbor positions with wraparound for rows
    for dc, dr in deltas:
        neighbor_col = col + dc
        neighbor_row = (row + dr) % rows  # Wrap around rows vertically

        # Check if the neighbor column is within bounds (no wraparound horizontally)
        if 0 <= neighbor_col < cols:
            neighbors.append((neighbor_col, neighbor_row))

    return neighbors