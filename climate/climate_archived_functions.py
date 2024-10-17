
def all_wind_simple(grid, config, state, prev_state):
    wind_friction_altitude = config['climate']['wind_friction_altitude']
    wind_friction_biomass = config['climate']['wind_friction_biomass']
    distance_between_tiles = config['climate']['distance_between_tiles']
    pressure_gradient_to_wind_factor = 100

    for tile in grid.tiles:
        sea_level_air_pressure = state[tile.id]['sea_level_air_pressure']
        
        pressure_gradient = [0, 0]
        vectors = []
        for neighbor in tile.get_neighbors():
            neighbor_pressure = state[neighbor.id]['sea_level_air_pressure']
                        
            vector_direction = normalize_vector(neighbor.col - tile.col, neighbor.row - tile.row)
            vector_intensity = (neighbor_pressure - sea_level_air_pressure) / distance_between_tiles
            vectors.append((vector_direction[0] * vector_intensity, vector_direction[1] * vector_intensity))
        for vector in vectors:
            pressure_gradient[0] += vector[0]
            pressure_gradient[1] += vector[1]
        
        wind = [pressure_gradient[0] * pressure_gradient_to_wind_factor, pressure_gradient[1] * pressure_gradient_to_wind_factor]
        
        # then we divide this wind into 2, proportionally, for the 2 tiles towards which it's pointing
        result = vector_to_flat_hex_neighbors_and_ratio(tile, wind)
        neighbor1, ratio1, neighbor2, ratio2 = (result + (None, 0)) if len(result) == 2 else result

        # sometimes even our only neighbor migh be None: if we get a wind straight up into the pole, for example
        if not neighbor1:
            continue
        
        magnitude = vector_magnitude(wind[0], wind[1])

        # break it up into sub-winds
        wind1 = ratio1 * magnitude
        if neighbor2: # it's possible to point straight to the center and therefore have only one downwind neighbor here
            wind2 = ratio2 * magnitude
        
        # winds are slowed down by friction
        friction = 0.0
        # - however, this is a minor effect at a large scale. But still something I want to include
        # most of this will be due to mountainous terrain - so we look at differences in altitude between this tile and its neighbors
        friction += (altitude_from_sea_level(config, neighbor1.altitude) - altitude_from_sea_level(config, tile.altitude)) * wind_friction_altitude # we're assuming every 100m difference is 0.05 friction
        # but forests also have an effect, so let's look at biomass on this tile
        friction += (state[tile.id]['biomass'] + state[neighbor1.id]['biomass'])/2 * wind_friction_biomass # assume every 10 kg of biomass per surface area in either tile adds 0.005 friction
        # and we apply the friction
        friction = min(1.0, friction)
        wind1 *= (1.0 - friction)
        if neighbor2:
            friction = 0.0
            friction += (altitude_from_sea_level(config, neighbor2.altitude) - altitude_from_sea_level(config, tile.altitude)) * wind_friction_altitude
            friction += (state[tile.id]['biomass'] + state[neighbor2.id]['biomass'])/2 * wind_friction_biomass # assume every 10 kg of biomass per surface area in either tile adds 0.01 friction
            friction = min(1.0, friction)
            wind2 *= (1.0 - friction)

        # store sub-winds
        if wind1 > 0:
            state[tile.id]['wind1'] = wind1
            state[tile.id]['wind1_neighbor'] = neighbor1
        if neighbor2 and wind2 > 0:
            state[tile.id]['wind2'] = wind2
            state[tile.id]['wind2_neighbor'] = neighbor2


def distribution_wind_simple(grid, config, state, prev_state):
    # first compute the wind map
    all_wind_simple(grid, config, state, prev_state)

    # queue = every tile on the map, sorted by air pressure (lowest first)
    queue = sorted(grid.tiles, key=lambda tile: state[tile.id]['sea_level_air_pressure'])

    while queue:
        tile = queue.pop(0)

        if 'wind1_neighbor' not in state[tile.id] or not state[tile.id]['wind1_neighbor']: # if there's no wind, skip
            continue
    
        # get calculated winds 
        neighbors = [(state[tile.id]['wind1_neighbor'], state[tile.id]['wind1'])]
        combined_wind = neighbors[0][1]
        
        if 'wind2_neighbor' in state[tile.id]:
            neighbors.append((state[tile.id]['wind2_neighbor'], state[tile.id]['wind2']))
            combined_wind += neighbors[1][1]
        
        # calculate how much of each variable to distribute
        vapor_wind_ratio = min(1.0, combined_wind / config['climate']['winds_max_vapor_transfer_speed'])
        vapor_out = state[tile.id]['vapor_content'] * vapor_wind_ratio * config['climate']['winds_max_vapor_transfer_ratio']
        cloud_wind_ratio = min(1.0, combined_wind / config['climate']['winds_max_cloud_transfer_speed'])
        cloud_out = state[tile.id]['cloud_content'] * cloud_wind_ratio * config['climate']['winds_max_cloud_transfer_ratio']

        # distribute vapor content and clouds
        for neighbor, ratio in neighbors:
            vapor_transfer = vapor_out * ratio / combined_wind
            state[neighbor.id]['vapor_content'] += vapor_transfer
            cloud_transfer = cloud_out * ratio / combined_wind
            state[neighbor.id]['cloud_content'] += cloud_transfer

        state[tile.id]['vapor_content'] -= vapor_out
        state[tile.id]['cloud_content'] -= cloud_out