import math

# === UTILS ===
def vector_magnitude(x, y):
    return math.sqrt(x * x + y * y)

def normalize_vector(x, y):
    magnitude = vector_magnitude(x, y)
    return (x/magnitude, y/magnitude)

def altitude_from_sea_level(config, altitude):
    return max(0, altitude - config["sea_level"]) # we're not simulating the ocean currently, so we never need to know the depth of a tile, so min = 0

def is_sea_tile(tile, config):
    return tile.altitude <= config["sea_level"]

def normalized_latitude(tile):
    # 1. calculate distance from equator
    max_latitude = tile.grid.height / 2
    latitude = max_latitude - tile.row
    if tile.col % 2 == 1: # because every 2nd column is down half a tile compared to the first, since they're tiles and flat-topped
        latitude -= 0.5
    latitude = latitude / max_latitude
    return latitude

def new_state(grid):
    state = {} # climate variable objects indexed by tile id
    for tile in grid.tiles:
        state[tile.id] = {}
    return state

# Adjusted direction vector calculation for flat-topped hex grid
# specifically, one where 1,0 is placed lower than 0,0
# wraparound: 1 for horizontal, 2 for vertical, 3 for both
def get_hex_direction_vector(source_tile, sink_tile, wraparound=1):
    sinkX = sink_tile.col
    sinkY = sink_tile.row
    sourceX = source_tile.col
    sourceY = source_tile.row

    # adjust for the fact that every 2nd column is down half a tile compared to the first, since they're tiles and flat-topped
    if source_tile.col % 2 == 1:
        sourceY += 0.5
    if sink_tile.col % 2 == 1:
        sinkY += 0.5

    if wraparound & 1:
        width = source_tile.grid.width
        if abs(sinkX - sourceX) > width / 2:
            if sinkX > sourceX:
                sinkX -= width
            else:
                sinkX += width
    if wraparound & 2:
        height = source_tile.grid.height
        if abs(sinkY - sourceY) > height / 2:
            if sinkY > sourceY:
                sinkY -= height
            else:
                sinkY += height

    return normalize_vector(sinkX - sourceX, sinkY - sourceY)

# Directions in a flat-topped hex grid (axial coordinates)
AXIAL_DIRECTIONS = [
    (1, 0),   # Right
    (1, -1),  # Top-right
    (0, -1),  # Top-left
    (-1, 0),  # Left
    (-1, 1),  # Bottom-left
    (0, 1)    # Bottom-right
]

# from a tile and a (wind or water flow) vector, returns the neighbors it points to and the ratio
#   the "ratio" is 1.0 if the vector points exactly from the center of the tile to the center of a neighbor,
#   0.5 if it points straight to the middle point between 2 neighbors
#   etc
def vector_to_flat_hex_neighbors_and_ratio(tile, vector):
    q = tile.col
    r = tile.row
    
    angle = math.atan2(vector[1], vector[0])
    if angle < 0: # Normalize the angle between 0 and 2π
        angle += 2 * math.pi    
    
    hex_angles = [
        0,                   # Right (1, 0)
        math.pi / 3,         # Top-right (1, -1)
        2 * math.pi / 3,     # Top-left (0, -1)
        math.pi,             # Left (-1, 0)
        4 * math.pi / 3,     # Bottom-left (-1, 1)
        5 * math.pi / 3      # Bottom-right (0, 1)
    ]
    
    # Find which two directions the vector lies between
    for i in range(len(hex_angles)):
        next_i = (i + 1) % len(hex_angles)
        if hex_angles[i] <= angle < hex_angles[next_i]:
            # Calculate the ratio of the angle between the two directions
            total_angle_diff = hex_angles[next_i] - hex_angles[i]
            angle_diff = angle - hex_angles[i]
            ratio = 1 - (angle_diff / total_angle_diff)
            
            # Get the neighboring tiles, adjust for dimensions, in case wraparound is enabled and the wind is pointing us there
            q1 = (q + AXIAL_DIRECTIONS[i][0]) % tile.grid.width
            r1 = (r + AXIAL_DIRECTIONS[i][1]) % tile.grid.height
            q2 = (q + AXIAL_DIRECTIONS[next_i][0]) % tile.grid.width
            r2 = (r + AXIAL_DIRECTIONS[next_i][1]) % tile.grid.height
            coords1 = (q1, r1)
            coords2 = (q2, r2)
            first_neighbor = tile.grid.get_tile(coords1[0], coords1[1])
            second_neighbor = tile.grid.get_tile(coords2[0], coords2[1])
            
            return first_neighbor, ratio, second_neighbor, 1 - ratio
    
    # Handle edge case if the angle is exactly aligned with one direction
    coords = (q + AXIAL_DIRECTIONS[0][0], r + AXIAL_DIRECTIONS[0][1])
    neighbor = tile.grid.get_tile(coords[0], coords[1])
    return neighbor, 1.0, None, 0.0
