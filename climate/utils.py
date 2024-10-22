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

def xy_to_qrs(x, y):
    q = x - (y / 2)
    r = y
    s = -q - r
    return q, r, s

def qrs_to_xy(q, r, s):
    x = q + (r / 2)
    y = r
    return x, y

def get_tile_qrs(grid, q, r, s):
    x, y = qrs_to_xy(q, r, s)
    return grid.get_tile(x, y)

def aux_coriolis_velocity_qrs(config, normalized_latitude, wind_vector):
    planet_angular_velocity = config['climate']['planet_angular_velocity']
    distance_between_tiles = config['climate']['distance_between_tiles']

    if wind_vector[0] < 1e-15 and wind_vector[1] < 1e-15 and wind_vector[2] < 1e-15:
        return [0, 0, 0]

    # apply coriolis effect to the outgoing wind stream (the neighbor's incoming)
    coriolis_parameter = 2 * planet_angular_velocity * math.sin(normalized_latitude * math.pi / 2)
    xy_buffer = qrs_to_xy(wind_vector[0], wind_vector[1], wind_vector[2])
    direction_vector = normalize_vector(xy_buffer[0], xy_buffer[1])
    # coriolis direction is perpendicular to the wind direction
    coriolis_speed = [direction_vector[1], -direction_vector[0]]
    # wind speed cancels out in the equation when applying coriolis force over a distance (to get velocity), so we just need the coriolis parameter and distance
    coriolis_speed_magnitude = coriolis_parameter * distance_between_tiles
    coriolis_speed = [coriolis_speed[0] * coriolis_speed_magnitude, coriolis_speed[1] * coriolis_speed_magnitude]
    coriolis_vector = xy_to_qrs(coriolis_speed[0], coriolis_speed[1])
    return coriolis_vector

# Adjusted direction vector calculation for flat-topped hex grid
# specifically, one where 1,0 is placed lower than 0,0
# wraparound: 1 for horizontal, 2 for vertical, 3 for both
def get_hex_direction_vector(source_tile, sink_tile, wraparound=1):
    sinkX = sink_tile.col
    sinkY = sink_tile.row
    sourceX = source_tile.col
    sourceY = source_tile.row

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

    # adjust for the fact that every 2nd column is down half a tile compared to the first
    if source_tile.col % 2 == 1:
        sourceY += 0.5
    if sink_tile.col % 2 == 1:
        sinkY += 0.5

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
    if vector[0] == 0 and vector[1] == 0:
        return None, 0.0, None, 0.0

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
