# ============ #
# === WIND === #
# ============ #
# === WIND - v0 === #
# First attempt, kind of jumped headfirst into it, overly complex and got lost in the details
# Hard to debug and finetune a model that starts too complex
# wind v0 accounted for coriolis effect right off the bat, and used a single vector on each tile for wind, suffering from the same issues as simple v1 later but while also being harder to study
def all_wind(grid, config, state, prev_state):
    specific_gas_constant_for_air = config['climate']['specific_gas_constant_for_air']
    planet_angular_velocity = config['climate']['planet_angular_velocity']
    wind_friction_altitude = config['climate']['wind_friction_altitude']
    wind_friction_biomass = config['climate']['wind_friction_biomass']
    distance_between_tiles = config['climate']['distance_between_tiles']

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
        
        # TODO - temp fix, because we're getting values too close to 0 when calculating manually
        air_density = 1.225 #    sea_level_air_pressure / (specific_gas_constant_for_air * state[tile.id]['temperature'])

        # finally, we calculate the geostrophic wind, to account for the coriolis effect
        # geostrophic wind is an approximation of the wind speed, which considers the coriolis effect and pressure gradient force to be in equilibrium
        # this is great because it accounts for the coriolis effect while also simplifying away the PGF and yielding a nice direct wind speed
        latitude = normalized_latitude(tile) * math.pi / 2
        epsilon = 1e-6  # Small regularization factor to prevent division by zero at equator
        coriolis_parameter = 2 * planet_angular_velocity * math.sin(latitude + epsilon)
        k = 1 / (coriolis_parameter * air_density)
        # this is in m/s
        geostrophic_wind = (pressure_gradient[0] * k, pressure_gradient[1] * k) 
        
        state[tile.id]['wind'] = geostrophic_wind
        # print('wind', geostrophic_wind)

        # then we divide this wind into 2, proportionally, for the 2 tiles towards which it's pointing
        neighbor1, ratio1, neighbor2, ratio2 = vector_to_flat_hex_neighbors_and_ratio(tile, geostrophic_wind)

        # sometimes even our only neighbor migh be None: if we get a wind straight up into the pole, for example
        if not neighbor1:
            continue
        
        magnitude = vector_magnitude(geostrophic_wind[0], geostrophic_wind[1])

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

def distribution_wind(grid, config, state, prev_state):
    # first compute the wind map
    all_wind(grid, config, state, prev_state)

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

        # pressure_out_percent = combined_wind / config['climate']['winds_max_pressure_transfer_speed'] * config['climate']['winds_max_pressure_transfer_ratio']
        # temperature_out_percent = combined_wind / config['climate']['winds_max_temperature_transfer_speed'] * config['climate']['winds_max_temperature_transfer_ratio']
        # self_adjust_pressure = 0
        # self_adjust_temperature = 0

        # distribute temperature, air pressure, vapor content and clouds
        for neighbor, ratio in neighbors:
            vapor_transfer = vapor_out * ratio / combined_wind
            state[neighbor.id]['vapor_content'] += vapor_transfer
            cloud_transfer = cloud_out * ratio / combined_wind
            state[neighbor.id]['cloud_content'] += cloud_transfer
            
            # # Temperature
            # # We transfer a percentage of the temperature *difference*
            # temperature_difference = state[tile.id]['temperature'] - state[neighbor.id]['temperature']
            # temperature_transfer = temperature_difference * temperature_out_percent * ratio
            # state[neighbor.id]['temperature'] += temperature_transfer
            # self_adjust_temperature += temperature_transfer

            # # Air pressure
            # # We transfer a percentage of the pressure *difference*
            # pressure_difference = state[tile.id]['sea_level_air_pressure'] - state[neighbor.id]['sea_level_air_pressure']
            # pressure_transfer = pressure_difference * pressure_out_percent * ratio
            # state[neighbor.id]['sea_level_air_pressure'] += pressure_transfer
            # self_adjust_pressure += pressure_transfer

        state[tile.id]['vapor_content'] -= vapor_out
        state[tile.id]['cloud_content'] -= cloud_out
        # state[tile.id]['temperature'] -= self_adjust_temperature
        # state[tile.id]['sea_level_air_pressure'] -= self_adjust_pressure

# === WIND - SIMPLE v1 === #
# simple v1 looks at pressure gradients to determine a single wind vector, then determines which 2 tiles it points to and how much of it goes to each
# key issues: 
#   - vapor is spread along straight lines because of winds
#   - winds can abruptly go to 0 as soon as air pressure stabilizes, blocking any vapor from being transfered onwards. This leads to continents being entirely permanently dry.
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


# === WIND - SIMPLE v2 === #
# simple_v2 considers wind continuation from tile to tile, and generates local winds based on pressure gradients 
# it considers winds from each tile to all of its downwind neighbours
def distribution_wind_simple_v2(grid, config, state, prev_state):
    # all_wind and distribution joined into one function
    # we no longer compute a combined pressure gradient, instead we transfer vapor and clouds to every neighbour downwind
    # this is because vapor on the map was being spread along straight lines because of winds, and so creating a very unsmooth map for humidity
    wind_friction_altitude = config['climate']['wind_friction_altitude']
    wind_friction_biomass = config['climate']['wind_friction_biomass']
    distance_between_tiles = config['climate']['distance_between_tiles']
    pressure_gradient_to_wind_factor = 100

    # cumulative wind
    incoming_winds = {}
    local_pressure_winds = {}
    for tile in grid.tiles:
        incoming_winds[tile.id] = [0, 0]

    # queue = every tile on the map, sorted by air pressure (highest first)
    queue = sorted(grid.tiles, key=lambda tile: state[tile.id]['sea_level_air_pressure'], reverse=True)
    while queue:
        tile = queue.pop(0)
        sea_level_air_pressure = state[tile.id]['sea_level_air_pressure']
        
        incoming_wind = incoming_winds[tile.id]
        neighbor1, ratio1, neighbor2, ratio2 = vector_to_flat_hex_neighbors_and_ratio(tile, incoming_wind)
        incoming_wind_magnitude = vector_magnitude(incoming_wind[0], incoming_wind[1])

        neighbors_winds = []
        for neighbor in tile.get_neighbors():
            neighbor_pressure = state[neighbor.id]['sea_level_air_pressure']
            
            # if the neighbor has higher air pressure, it's not downwind
            if neighbor_pressure > sea_level_air_pressure:
                continue

            pressure_gradient_1d = (sea_level_air_pressure - neighbor_pressure) / distance_between_tiles

            wind = pressure_gradient_1d * pressure_gradient_to_wind_factor

            # add incoming winds if appropriate,  based on the direction of incoming wind
            if neighbor == neighbor1:
                wind += incoming_wind_magnitude * ratio1
            elif neighbor == neighbor2:
                wind += incoming_wind_magnitude * ratio2

            # winds are slowed down by friction
            friction = 0.0
            # - however, this is a minor effect at a large scale. But still something I want to include
            # most of this will be due to mountainous terrain - so we look at differences in altitude between this tile and its neighbors
            friction += (altitude_from_sea_level(config, neighbor.altitude) - altitude_from_sea_level(config, tile.altitude)) * wind_friction_altitude # we're assuming every 100m difference is 0.05 friction
            # but forests also have an effect, so let's look at biomass on this tile
            friction += (state[tile.id]['biomass'] + state[neighbor.id]['biomass'])/2 * wind_friction_biomass # assume every 10 kg of biomass per surface area in either tile adds 0.005 friction
            # and we apply the friction
            friction = min(1.0, friction)

            wind *= (1.0 - friction)

            direction_vector = normalize_vector(neighbor.col - tile.col, neighbor.row - tile.row)
            incoming_winds[neighbor.id][0] += direction_vector[0] * wind
            incoming_winds[neighbor.id][1] += direction_vector[1] * wind

            neighbors_winds.append((neighbor, wind))

        wind_vector = [0, 0]
        combined_wind = 0
        for neighbor, wind in neighbors_winds:
            combined_wind += wind

            # the wind vector calculation is just for display on the map
            direction_vector = normalize_vector(neighbor.col - tile.col, neighbor.row - tile.row)
            wind_vector[0] += direction_vector[0] * wind
            wind_vector[1] += direction_vector[1] * wind
        state[tile.id]['wind'] = wind_vector

        if combined_wind == 0:
            continue

        # calculate how much of each variable to transfer out
        vapor_wind_ratio = min(1.0, combined_wind / config['climate']['winds_max_vapor_transfer_speed'])
        vapor_out = state[tile.id]['vapor_content'] * vapor_wind_ratio * config['climate']['winds_max_vapor_transfer_ratio']
        cloud_wind_ratio = min(1.0, combined_wind / config['climate']['winds_max_cloud_transfer_speed'])
        cloud_out = state[tile.id]['cloud_content'] * cloud_wind_ratio * config['climate']['winds_max_cloud_transfer_ratio']

        print('vapor_wind_ratio', vapor_wind_ratio, 'cloud_wind_ratio', cloud_wind_ratio)

        for neighbor, wind in neighbors_winds:
            # calculate how much to transfer to this one neighbor
            vapor_transfer = vapor_out * wind / combined_wind
            cloud_transfer = cloud_out * wind / combined_wind
            state[neighbor.id]['vapor_content'] += vapor_transfer
            state[neighbor.id]['cloud_content'] += cloud_transfer

        state[tile.id]['vapor_content'] -= vapor_out
        state[tile.id]['cloud_content'] -= cloud_out
