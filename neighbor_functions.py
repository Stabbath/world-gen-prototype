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
        List[Tuple[int, int]]: A list of (col, row) tuples with the coordinates of neighboring cells within bounds.
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

def get_neighbors_wraparound(col, row, cols, rows, axis=1):
    """
    Returns a list of neighboring cells' coordinates for a given cell in an even-q vertical offset grid,
    with wraparound.

    Parameters:
        col (int): The column index of the current cell.
        row (int): The row index of the current cell.
        cols (int): Total number of columns in the grid.
        rows (int): Total number of rows in the grid.
        axis (int): Flags for axes to wrap around. 1 = horizontal, 2 = vertical

    Returns:
        List[Tuple[int, int]]: A list of (col, row) tuples with the coordinates of neighboring cells with wraparound.
    """
    neighbors = []

    if col % 2 == 0:
        deltas = EVEN_Q_NEIGHBORS
    else:
        deltas = ODD_Q_NEIGHBORS

    for dc, dr in deltas:
        neighbor_col = col + dc
        if axis & 1:
            neighbor_col = neighbor_col % cols # Wrap around columns

        neighbor_row = row + dr
        if axis & 2:
            neighbor_row = neighbor_row % rows # Wrap around rows

        if 0 <= neighbor_col < cols and 0 <= neighbor_row < rows: # If we're not wrapping around both axes, this needs to be checked
            neighbors.append((neighbor_col, neighbor_row))

    return neighbors
