import math


# === GENERAL TODO NOTES ===
# TODO - maybe have to redefine cloud density as cloud vapor content, and model it as vapor going from the air to the clouds
# TODO - think about Albedo
# TODO - temperature should be tracked as average, minimum, and maximum, probably.
# TODO - if the map takes too long to stabilize, we can consider adding neighbor smoothing during the generation of the climate (probably not during gameplay)
# TODO - add soil quality/minerals as a factor in plant growth (and beyond)
# TODO - add roughness of terrain as a factor in wind friction (and beyond)
# TODO - temperature and air pressure transfer in the wind are commented out because they currently don't matter much, since we calculate them fresh on each iteration

# === UTILS ===
def is_sea_tile(tile, config):
    return tile.altitude <= config["sea_level"]

def normalized_latitude(tile):
    # 1. calculate distance from equator
    max_latitude = tile.grid.height / 2
    latitude = max_latitude - tile.row
    if tile.col % 2 == 0: # because every 2nd column is down half a tile compared to the first, since they're tiles and flat-topped
        latitude -= 0.5
    latitude = latitude / max_latitude
    return latitude

def init_state(grid):
    state = {} # climate variable objects indexed by tile id
    for tile in grid.tiles:
        state[tile.id] = {}
    return state

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
            
            # Get the neighboring tiles
            coords1 = (q + AXIAL_DIRECTIONS[i][0], r + AXIAL_DIRECTIONS[i][1])
            coords2 = (q + AXIAL_DIRECTIONS[next_i][0], r + AXIAL_DIRECTIONS[next_i][1])
            first_neighbor = tile.grid.get_tile(coords1[0], coords1[1])
            second_neighbor = tile.grid.get_tile(coords2[0], coords2[1])
            
            return ((first_neighbor, ratio), (second_neighbor, 1 - ratio))
    
    # Handle edge case if the angle is exactly aligned with one direction
    coords = (q + AXIAL_DIRECTIONS[0][0], r + AXIAL_DIRECTIONS[0][1])
    neighbor = tile.grid.get_tile(coords[0], coords[1])
    return (neighbor, 1.0)


# === CONFIG CONSTANTS ===
config = {}
config['climate'] = {}
config['climate']['max_iterations'] = 100
config['climate']['smoothen_temperature_map'] = True
config['climate']['temperature_smoothing_self_weight'] = 3
config['climate']['temperature_lapse_rate'] = 0.0065    # C/m       : rate of decrease in temperature with height
config['climate']['geothermal_constant'] = 0            # C         : a flat temperature bonus to every tile from the planet's own heat
config['climate']['reference_temperature'] = 27         # C         : the baseline for temperature around the equator, not counting geothermal effects, basically
config['climate']['reference_radiation'] = 1361         # W/m^2     : the radiation which will give the equator the reference_temperature
config['climate']['cloud_reduction_factor'] = 0.8       #           : how much a cloud density of 1.0 reduces incoming solar radiation by
config['climate']['solar_constant'] = 1361              # W/m^2     : average solar energy received per unit area at the top of the atmosphere / at the equator
config['climate']['relative_humidity_precipitation_threshold'] = 0.85 # % : how much relative humidity we need for it to cause precipitation
config['climate']['precipitation_rate_multiplier'] = 1  #           : factor to multiply precipitation rate by
config['climate']['plant_cold_threshold'] = 0           # C         : temperature below which growth stops
config['climate']['plant_optimal_low'] = 15             # C         : lower bound for optimal growth
config['climate']['plant_optimal_high'] = 25            # C         : upper bound for optimal growth
config['climate']['plant_hot_threshold'] = 45           # C         : temperature above which growth stops
config['climate']['photosynthesis_radiation_ratio'] = 0.45 #        : how much of the solar radiation is converted to energy for the plant
config['climate']['solar_conversion_rate'] = 0.02       #           : how much of the solar energy is converted into growth for the plant
config['climate']['biomass_efficiency_exponent'] = 1.33 #           : exponent to define improved water efficiency from higher biomass in processing water intake
config['climate']['one_kilo_intake_reference'] = 0.00001157407 # kg/s : how much water a standard 1kg plant can take per second
config['climate']['biomass_growth_constant'] = 0.0001   # kg        : how much flat biomass is added to each tile each iteration
config['climate']['humidity_cloud_formation_threshold'] = 0.75 # % : relative humidity at which clouds start forming
config['climate']['humidity_absorption_rate'] = 0.001   # kg/s      : how much water a plant can absorb from the air per second
config['climate']['atmospheric_pressure'] = 101325      # Pa        : standard atmospheric pressure at sea level
config['climate']['g'] = 9.80665                        # m/s^2     : acceleration due to gravity
config['climate']['planet_molar_mass'] = 0.0289644      # kg/mol    : molar mass of Earth's air
config['climate']['water_molar_mass'] = 0.01801528      # kg/mol    : molar mass of water
config['climate']['universal_gas_constant'] = 8.31432   # J/(mol.K) : ideal gas constant
config['climate']['plant_transpiration'] = 0.01         # kg        : base value for water lost to transpiration per kg of biomass per iteration
config['climate']['evaporation_rate_factor'] = 1.0      #           : factor to multiply evaporation rate by
config['climate']['water_temperature_multiplier'] = 0.8 # C         : factor to multiply temperature by to obtain water temperature
config['climate']['water_temperature_constant'] = 3     # C         : constant to add to temperature to obtain water temperature
config['climate']['water_temperature_multiplier_ocean'] = 0.4 # C   : factor to multiply temperature by to obtain water temperature; for the ocean
config['climate']['water_temperature_constant_ocean'] = 6 # C       : constant to add to temperature to obtain water temperature; for the ocean
config['climate']['ocean_water_flow_equivalent'] = 1    # kg/m^2/s  : how much water flow a tile needs to have equivalent water flow to an ocean tile, for purposes of calculating evaporation
config['climate']['cloud_density_to_water_ratio'] = 0.1 #           : ratio to convert cloud density into rain
config['climate']['transpiration_reference_temperature'] = 25 # C   : temperature which has a neutral effect on evapotranspiration (below reduces it, above increases it)
config['climate']['wind_friction_altitude'] = 0.0005    #           : how much friction is added per meter of altitude difference
config['climate']['wind_friction_biomass'] = 0.0005     #           : how much friction is added per kg of biomass per surface
config['climate']['specific_gas_constant_for_air'] = 287.058 # J/(kg.K) : specific gas constant for dry air
config['climate']['planet_angular_velocity'] = 0.000072921 # rad / s : angular velocity of the planet
config['climate']['winds_max_vapor_transfer_speed'] = 10 # m/s      : wind speed required to transfer all of the appropriate variable out of a tile
config['climate']['winds_max_cloud_transfer_speed'] = 25 # m/s      : ""
config['climate']['winds_max_pressure_transfer_speed'] = 30 # m/s   : ""
config['climate']['winds_max_temperature_transfer_speed'] = 15 # m/s : ""
config['climate']['winds_max_vapor_transfer_ratio'] = 0.5 #         : how much of the variable is transferred by the wind at max wind
config['climate']['winds_max_cloud_transfer_ratio'] = 0.6 #         : ""
config['climate']['winds_max_pressure_transfer_ratio'] = 0.05 #     : ""
config['climate']['winds_max_temperature_transfer_ratio'] = 0.1 #   : ""


# === CLIMATE VARIABLES === 
units = {
    "solar_radiation": "W/m^2", # Average power per unit of surface area
    "water_flow": "kg/m^2/s", # Flow by weight per unit of surface area
    "temperature": "C", # In Celsius
    "vapor_capacity": "kg/m^2", # Maximum amount of water vapor in the air, per unit of surface area
    "vapor_content": "kg/m^2", # Amount of water vapor in the air, per unit of surface area
    "evaporation": "kg/m^2/s", # Water mass evaporated per second per unit of surface area
    "evapotranspiration": "kg/m^2/s", # Water mass evapotranspirated per second per unit of surface area
    "air_pressure": "Pa",
    "wind": "m/s",
    "cloud_density": "%", # 100% means every unit of surface area is covered by the thickest cloud possible
    "precipitation": "kg/m^2", # Average rainfall volume per unit of surface area
    "biomass": "kg/m^2", # Average biomass per unit of surface area
    "plant_humidity_absorption": "kg/m^2/s" # Water taken in by plants directly from the atmosphere
}


# === SMOOTHING ===
def smoothen_temperature(grid, config, state, prev_state):
    weight = config['climate']['temperature_smoothing_self_weight']

    # calculate smoothed temperature map
    temperature_map = {}
    for tile in grid.tiles:
        temperature_sum = weight * state[tile.id]['temperature']
        temperature_count = weight
        for neighbor in tile.get_neighbors():
            temperature_sum += state[neighbor.id]['temperature']
            temperature_count += 1
        temperature_map[tile.id] = temperature_sum / temperature_count
    
    # mutate state
    for tile in grid.tiles:
        state[tile.id]['temperature'] = temperature_map[tile.id]


# === BASIC CALCULATION FUNCTIONS ===
# normalized_latitude: between -1 and 1, with 0 being equator and -1 and 1 being the poles
def calculate_spherical_average_yearly_solar_radiation(config, normalized_latitude):
    # Ensure the normalized latitude is within the range of -1 to 1
    if not -1 <= normalized_latitude <= 1:
        raise ValueError("Normalized latitude must be between -1 and 1.")

    solar_constant = config['climate']['solar_constant']
    
    # Convert the normalized latitude to an angle in radians
    latitude_rad = normalized_latitude * (math.pi / 2)  # -1 maps to -90°, 0 to 0°, and 1 to 90°

    # Calculate the average solar radiation based on the latitude
    avg_solar_radiation = solar_constant * max(0, math.cos(latitude_rad))

    return avg_solar_radiation

def calculate_cyllindral_average_yearly_solar_radiation(config, normalized_latitude):
    solar_constant = config['climate']['solar_constant']
    # For an actual seriously cyllindrical planet, there is no difference in actual latitude (i.e. angle from the equator)
    # So the angle of incidence for solar radiation will be approximately the same for every point of the cyllinder
    return solar_constant

def calculate_precipitation(config, vapor_content, vapor_capacity, cloud_density):
    relative_humidity_threshold = config['climate']['relative_humidity_precipitation_threshold']
    precipitation_rate_multiplier = config['climate']['precipitation_rate_multiplier']
    relative_humidity = vapor_content / vapor_capacity
    excess_humidity = max(0, relative_humidity  - relative_humidity_threshold)
    return precipitation_rate_multiplier * cloud_density  * excess_humidity

def calculate_solar_radiation_init(config, normalized_latitude):
    return calculate_spherical_average_yearly_solar_radiation(normalized_latitude)

def calculate_solar_radiation(config, normalized_latitude, cloud_density):
    cloud_reduction_factor = config['climate']['cloud_reduction_factor']
    return calculate_solar_radiation_init(config, normalized_latitude) * (1.0 - cloud_density * cloud_reduction_factor)

def calculate_cloud_density_init(config, vapor_content, vapor_capacity):
    humidity_cloud_formation_threshold = config['climate']['humidity_cloud_formation_threshold']
    relative_humidity = vapor_content / vapor_capacity
    return max(0, (relative_humidity - humidity_cloud_formation_threshold)/(1 - humidity_cloud_formation_threshold))

def calculate_cloud_density(config, prev_cloud_density, vapor_content, vapor_capacity, humidity_cloud_formation_threshold=0.75):
    relative_humidity = (prev_cloud_density + vapor_content) / vapor_capacity
    cloud_density = max(0, (relative_humidity - humidity_cloud_formation_threshold)/(1 - humidity_cloud_formation_threshold))
    cloud_density = min(1, cloud_density + prev_cloud_density)
    return cloud_density

# Plant growth is maximum within a certain optimal range, and impossible beyond certain temperatures
def _temperature_growth_factor(config, temperature): 
    cold_threshold = config['climate']['plant_cold_threshold']
    hot_threshold = config['climate']['plant_hot_threshold'] 
    optimal_temp_low = config['climate']['plant_optimal_low']
    optimal_temp_high = config['climate']['plant_optimal_high']
    
    if temperature < cold_threshold: # too cold
        return 0.0
    elif temperature < optimal_temp_low: # decreases linearly from 1 to 0 based on proximity to our thresholds here
        return (temperature - cold_threshold)/(optimal_temp_low - cold_threshold)
    elif temperature < optimal_temp_high: # optimal range
        return 1.0
    elif temperature < hot_threshold: # decreases linearly from 1 to 0 based on proximity to our thresholds here
        return (hot_threshold - temperature)/(hot_threshold - optimal_temp_high)
    else: # too hot
        return 0.0

# one_kilo_intake_reference = water a standard 1kg plant can take per second. Default value is basically 1 kg per day scaled down to seconds
def calculate_biomass(config, prev_biomass, evapotranspiration, plant_humidity_absorption, water_flow, solar_radiation, temperature, is_sea_tile):
    solar_constant = config['climate']['solar_constant']
    solar_conversion_rate = config['climate']['solar_conversion_rate']
    photosynthesis_radiation_ratio = config['climate']['photosynthesis_radiation_ratio']
    biomass_efficiency_exponent = config['climate']['biomass_efficiency_exponent']
    one_kilo_intake_reference = config['climate']['one_kilo_intake_reference']
    biomass_growth_constant = config['climate']['biomass_growth_constant']
    
    # Sea tiles don't grow plants. For now.
    if is_sea_tile:
        return 0.0
    
    # How to make a plant: Water, Energy, Food
    # And some magic: add a small constant to allow spontaneous vegetation growth
    prev_biomass = prev_biomass + biomass_growth_constant

    # === WATER === #
    # from water_flow, we can determine how much water is available for use
    # assume it's the same, for now. Here we're considering ground water to be measured in kg/m^2/s, as in kilos of water available per unit of surface area in any given second
    ground_water = water_flow
    # some plants also take in water from air humidity
    humidity_intake = plant_humidity_absorption
    # the plant loses water through transpiration
    transpiration_loss = evapotranspiration 
    # resulting in a net intake (or outtake)
    available_water = ground_water + humidity_intake - transpiration_loss
    # however, there is a maximum amount it can actually use, depending on its biomass
    # this scales supra-linearly, due to improvements in water efficiency with greater biomass
    useable_water = one_kilo_intake_reference * prev_biomass ** biomass_efficiency_exponent
    water_factor = min(1.0, available_water/useable_water)
    
    # === ENERGY === #
    # plants are solar-powered, this is our source of energy for growth
    # for now, assume baseline is the normal value at equator without cloud cover
    energy_factor = solar_radiation / solar_constant
    # but not all of that radiation is useable for photosynthesis
    energy_factor *= photosynthesis_radiation_ratio
    # and they are inefficient converters of this into actual growth, after maintenance etc
    energy_factor *= solar_conversion_rate
    
    # === FOOD === #
    # plants rely on food, minerals and stuff from the soil
    # think about this later, for now ignore it
    mineral_factor = 1.0 

    # === GROWTH === #
    # growth is limited by all the factors above
    growth_factor = min(water_factor, energy_factor, mineral_factor)
    
    # growth also depends on temperature. A certain range of temperatures is probably ideal for growth, and growth probably slows down if it's too hot, and definitely if it's too cold.
    temperature_factor = _temperature_growth_factor(temperature)
    growth_factor *= temperature_factor
    
    biomass = prev_biomass * (1.0 + growth_factor)
    return biomass

# temperature in Celsius
def calculate_temperature(config, altitude, solar_radiation):
    temperature_lapse_rate = config['climate']['temperature_lapse_rate']
    geothermal_constant = config['climate']['geothermal_constant']
    reference_temperature = config['climate']['reference_temperature']
    reference_radiation = config['climate']['reference_radiation']

    # assume geothermal_constant just gives us our base temperature for the world at sea level
    temperature = geothermal_constant
    # we add an effect from radiation, for now just as a linear scale with no real physics, using the earth's equator as reference
    temperature += solar_radiation/reference_radiation * reference_temperature
    # temperature decreases with altitude
    temperature -= altitude * temperature_lapse_rate

    return temperature

def calculate_temperature_init(config, altitude, solar_radiation):
    return calculate_temperature(config, altitude, solar_radiation)

# in g/m^3
def calculate_vapor_capacity_init(config, temperature):
    return calculate_vapor_capacity(temperature)

def aux_calculate_saturation_vapor_pressure(config, temperature):
    # Auguste-Roche-Magnus equation (see Clausius-Clapeyron relation)
    # NOTE: Current model is best suited for standard temperature and pressure, so 0ºC to 50ºC and close to 0 atm.
    return 610.94 * math.exp((17.625*temperature)/(temperature + 243.04))

def calculate_vapor_capacity(config, temperature):
    water_molar_mass = config['climate']['water_molar_mass']
    universal_gas_constant = config['climate']['universal_gas_constant']

    saturation_vapor_pressure = aux_calculate_saturation_vapor_pressure(config, temperature)

    # Ideal gas law
    idea_gas_law_multiplier = water_molar_mass / universal_gas_constant
    saturation_vapor_capacity = idea_gas_law_multiplier * saturation_vapor_pressure / (temperature + 273.15)

    return saturation_vapor_capacity

def calculate_vapor_content_init(config, is_sea, vapor_capacity):
    return vapor_capacity if is_sea else 0.1 * vapor_capacity

def calculate_air_pressure_init(config, temperature, altitude, TEMPERATURE_AT_SEA_LEVEL = calculate_temperature_init(config, 0, 0) + 273.15):
    return calculate_air_pressure(config, temperature, altitude, TEMPERATURE_AT_SEA_LEVEL)

def calculate_air_pressure(config, temperature, altitude, TEMPERATURE_AT_SEA_LEVEL = calculate_temperature_init(config, 0, 0) + 273.15):
    g = config['climate']['g']
    planet_molar_mass = config['climate']['planet_molar_mass']
    universal_gas_constant = config['climate']['universal_gas_constant']
    atmospheric_pressure = config['climate']['atmospheric_pressure']
    temperature_lapse_rate = config['climate']['temperature_lapse_rate']
    # TODO - should probably reconsider how this is calculated, regarding temperature at sea level? Need to understand the formula better
    # TODO - these constants combine into the atmospheric pressure scale height constant, which is 0.00012 m^-1
    # - So maybe we could pass in a base version of this constant, and adjust it based on the variables other than temperature and universal gas constant 

    temperature_change_coefficient = (1 - temperature_lapse_rate * altitude / TEMPERATURE_AT_SEA_LEVEL)
    exp_constant = g * planet_molar_mass / universal_gas_constant / temperature_lapse_rate
    
    # Barometric formula
    pressure = atmospheric_pressure * (temperature_change_coefficient ** exp_constant)
    return pressure
    
# plants lose water to the air
def calculate_evapotranspiration(config, biomass, temperature, vapor_content, vapor_capacity):
    transpiration_rate = config['climate']['plant_transpiration']
    transpiration_reference_temperature = config['climate']['transpiration_reference_temperature']

    relative_humidity = min(1.0, vapor_content / vapor_capacity)
    temperature_factor = max(0.0, temperature / transpiration_reference_temperature) # assuming linear for now
    transpiration_loss_per_biomass = transpiration_rate * (1.0 - humidity_factor) * temperature_factor 
    transpiration_loss_per_biomass = math.min(transpiration_loss_per_biomass, 1.0) # can't lose more water than you have
    transpiration_loss = transpiration_loss_per_biomass * biomass
    return transpiration_loss

# some plants take water from the air
def calculate_plant_humidity_absorption(config, biomass, vapor_content, vapor_capacity):
    humidity_absorption_rate = config['climate']['humidity_absorption_rate']

    relative_humidity = min(1.0, vapor_content / vapor_capacity)
    # assuming linear relation with relative humidity for now
    humidity_intake = humidity_absorption_rate * relative_humidity * biomass
    return humidity_intake

def calculate_evaporation(config, water_flow, temperature, vapor_content, vapor_capacity, is_sea_tile, air_pressure):
    evaporation_rate_factor = config['climate']['evaporation_rate_factor']
    if is_sea_tile:
        water_temperature_multiplier = config['climate']['water_temperature_multiplier_ocean']
        water_temperature_constant = config['climate']['water_temperature_constant_ocean']
    else:
        water_temperature_multiplier = config['climate']['water_temperature_multiplier']
        water_temperature_constant = config['climate']['water_temperature']
    ocean_water_flow_equivalent = config['climate']['ocean_water_flow_equivalent']

    water_temperature = water_temperature_multiplier * temperature + water_temperature_constant
    air_temperature = temperature
    water_temperature_saturation_vapor_pressure = aux_calculate_saturation_vapor_pressure(config, water_temperature)
    vapor_pressure = vapor_content / vapor_capacity * aux_calculate_saturation_vapor_pressure(config, air_temperature)
    pressure_ratio = (water_temperature_saturation_vapor_pressure - vapor_pressure) / air_pressure

    evaporation = evaporation_rate_factor * pressure_ratio
    if not is_sea_tile:
        evaporation = evaporation * water_flow / ocean_water_flow_equivalent
    return evaporation

def calculate_vapor_content(config, prev_vapor_content, evaporation, evapotransporation, plant_humidity_absorption):
    return prev_vapor_content + evaporation + evapotransporation - plant_humidity_absorption


# === ITERATIVE FUNCTIONS ===
def all_solar_radiation(grid, config, state, prev_state):
    for tile in grid.tiles:
        latitude = normalized_latitude(tile)
        state[tile.id]['solar_radiation'] = calculate_solar_radiation(
            config,
            latitude, 
            prev_state[tile.id]['cloud_density']
        )

def all_biomass(grid, config, state, prev_state):
    for tile in grid.tiles:
        state[tile.id]['biomass'] = calculate_biomass(
            config,
            prev_state[tile.id]['biomass'],
            prev_state[tile.id]['evapotranspiration'],
            prev_state[tile.id]['plant_humidity_absorption'],
            prev_state[tile.id]['water_flow'],
            prev_state[tile.id]['solar_radiation'],
            prev_state[tile.id]['temperature'],
            is_sea_tile(tile, config)
        )

def all_temperature(grid, config, state, prev_state):
    for tile in grid.tiles:
        state[tile.id]['temperature'] = calculate_temperature(
            config,
            state[tile.id]['solar_radiation'],
            tile.altitude
        )

def all_air_pressure(grid, config, state, prev_state):
    for tile in grid.tiles:
        state[tile.id]['air_pressure'] = calculate_air_pressure(
            config,
            state[tile.id]['temperature'],
            tile.altitude
        )

def all_vapor_capacity(grid, config, state, prev_state):
    for tile in grid.tiles:
        state[tile.id]['vapor_capacity'] = calculate_vapor_capacity(
            config,
            state[tile.id]['temperature']
        )

def all_vapor_content(grid, config, state, prev_state):
    for tile in grid.tiles:
        state[tile.id]['vapor_content'] = calculate_vapor_content(
            config,
            prev_state[tile.id]['vapor_content'],
            state[tile.id]['evaporation'],
            state[tile.id]['evapotranspiration'],
            state[tile.id]['plant_humidity_absorption']
        )

def all_evapotranspiration(grid, config, state, prev_state):
    for tile in grid.tiles:
        state[tile.id]['evapotranspiration'] = calculate_evapotranspiration(
            config,
            prev_state[tile.id]['biomass'],
            prev_state[tile.id]['temperature'],
            prev_state[tile.id]['vapor_content'],
            prev_state[tile.id]['vapor_capacity']
        )

def all_evaporation(grid, config, state, prev_state):
    for tile in grid.tiles:
        state[tile.id]['vapor_capacity'] = calculate_evaporation(
            config,
            prev_state[tile.id]['water_flow'],
            prev_state[tile.id]['temperature'],
            prev_state[tile.id]['vapor_content'],
            prev_state[tile.id]['vapor_capacity'],
            is_sea_tile(tile, config),
            prev_state[tile.id]['air_pressure']
        )

def all_plant_humidity_absorption(grid, config, state, prev_state):
    for tile in grid.tiles:
        state[tile.id]['plant_humidity_absorption'] = calculate_plant_humidity_absorption(
            config,
            prev_state[tile.id]['biomass'],
            prev_state[tile.id]['vapor_content'],
            prev_state[tile.id]['vapor_capacity']
        )

def all_cloud_density(grid, config, state, prev_state):
    for tile in grid.tiles:
        state[tile.id]['cloud_density'] = calculate_cloud_density(
            config,
            state[tile.id]['vapor_content'],
            state[tile.id]['vapor_capacity']
        )


# === DISTRIBUTION FUNCTIONS ===
def all_wind(grid, config, state, prev_state):
    specific_gas_constant_for_air = config['climate']['specific_gas_constant_for_air']
    planet_angular_velocity = config['climate']['planet_angular_velocity']
    wind_friction_altitude = config['climate']['wind_friction_altitude']
    wind_friction_biomass = config['climate']['wind_friction_biomass']

    for tile in grid.tiles:
        air_pressure = state[tile.id]['air_pressure']
        
        pressure_gradient = [0, 0]
        vectors = []
        for neighbor in tile.get_neighbors():
            neighbor_pressure = state[neighbor.id]['air_pressure']
                        
            vector_direction = (neighbor.col - tile.col, neighbor.row - tile.row)
            vector_intensity = neighbor_pressure - air_pressure
            vectors.append((vector_direction[0] * vector_intensity, vector_direction[1] * vector_intensity))
        for vector in vectors:
            pressure_gradient[0] += vector[0]
            pressure_gradient[1] += vector[1]
        
        air_density = air_pressure / (specific_gas_constant_for_air * state[tile.id]['temperature'])

        # finally, we calculate the geostrophic wind, to account for the coriolis effect
        # geostrophic wind is an approximation of the wind speed, which considers the coriolis effect and pressure gradient force to be in equilibrium
        # this is great because it accounts for the coriolis effect while also simplifying away the PGF and yielding a nice direct wind speed
        latitude = normalized_latitude(tile) * math.pi / 2
        coriolis_parameter = 2 * planet_angular_velocity * math.sin(latitude)
        k = 1 / (coriolis_parameter * air_density)
        # this is in m/s
        geostrophic_wind = (pressure_gradient[0] * k, pressure_gradient[1] * k) 
        
        state[tile.id]['wind'] = geostrophic_wind

        # then we divide this wind into 2, proportionally, for the 2 tiles towards which it's pointing
        (neighbor1, ratio1), (neighbor2, ratio2) = vector_to_flat_hex_neighbors_and_ratio
        state[tile.id]['wind1'] = ratio1
        state[tile.id]['wind1_neighbor'] = neighbor1
        if (neighbor2): # it's possible to point straight to the center and therefore have only one downwind neighbor here
            state[tile.id]['wind2'] = ratio2
            state[tile.id]['wind2_neighbor'] = neighbor2
        
        # winds are slowed down by friction
        friction = 0.0
        # - however, this is a minor effect at a large scale. But still something I want to include
        # most of this will be due to mountainous terrain - so we look at differences in altitude between this tile and its neighbors
        friction += (neighbor1.altitude - tile.altitude) * wind_friction_altitude # we're assuming every 100m difference is 0.05 friction
        # but forests also have an effect, so let's look at biomass on this tile
        friction += (state[tile.id]['biomass'] + state[neighbor1.id]['biomass']) * wind_friction_biomass # assume every 10 kg of biomass per surface area in either tile adds 0.005 friction
        # and we apply the friction
        state[tile.id]['wind1'] *= (1.0 - friction)
        if 'wind2' in state[tile.id]:
            friction = 0.0
            friction += (neighbor2.altitude - tile.altitude) * wind_friction_altitude
            friction += (state[tile.id]['biomass'] + state[neighbor2.id]['biomass']) * wind_friction_biomass # assume every 10 kg of biomass per surface area in either tile adds 0.01 friction
            state[tile.id]['wind2'] *= (1.0 - friction)

def distribution_wind(grid, config, state, prev_state):
    # queue = every tile on the map, sorted by air pressure (lowest first)
    queue = sorted(grid.tiles, key=lambda tile: state[tile.id]['air_pressure'])

    while queue:
        tile = queue.pop(0)

        # get calculated winds 
        neighbors = [(state[tile.id]['wind1_neighbor'], state[tile.id]['wind1'])]
        if 'wind2_neighbor' in state[tile.id]:
            neighbors.append((state[tile.id]['wind2_neighbor'], state[tile.id]['wind2']))

        # get wind magnitude
        combined_wind = state[tile.id]['wind']
        combined_wind = math.sqrt(combined_wind[0] ** 2 + combined_wind[1] ** 2)

        # calculate how much of each variable to distribute
        vapor_out = state[tile.id]['vapor_content'] * combined_wind / config['climate']['winds_max_vapor_transfer_speed'] * config['climate']['winds_max_vapor_transfer_ratio']
        cloud_out = state[tile.id]['cloud_density'] * combined_wind / config['climate']['winds_max_cloud_transfer_speed'] * config['climate']['winds_max_cloud_transfer_ratio']

        # pressure_out_percent = combined_wind / config['climate']['winds_max_pressure_transfer_speed'] * config['climate']['winds_max_pressure_transfer_ratio']
        # temperature_out_percent = combined_wind / config['climate']['winds_max_temperature_transfer_speed'] * config['climate']['winds_max_temperature_transfer_ratio']
        # self_adjust_pressure = 0
        # self_adjust_temperature = 0

        # distribute temperature, air pressure, vapor content and clouds
        for neighbor, ratio in neighbors:
            vapor_transfer = vapor_out * ratio
            state[neighbor.id]['vapor_content'] += vapor_transfer
            cloud_transfer = cloud_out * ratio
            state[neighbor.id]['cloud_density'] += cloud_transfer

            # # Temperature
            # # We transfer a percentage of the temperature *difference*
            # temperature_difference = state[tile.id]['temperature'] - state[neighbor.id]['temperature']
            # temperature_transfer = temperature_difference * temperature_out_percent * ratio
            # state[neighbor.id]['temperature'] += temperature_transfer
            # self_adjust_temperature += temperature_transfer

            # # Air pressure
            # # We transfer a percentage of the pressure *difference*
            # pressure_difference = state[tile.id]['air_pressure'] - state[neighbor.id]['air_pressure']
            # pressure_transfer = pressure_difference * pressure_out_percent * ratio
            # state[neighbor.id]['air_pressure'] += pressure_transfer
            # self_adjust_pressure += pressure_transfer

        state[tile.id]['vapor_content'] -= vapor_out
        state[tile.id]['cloud_density'] -= cloud_out
        # state[tile.id]['temperature'] -= self_adjust_temperature
        # state[tile.id]['air_pressure'] -= self_adjust_pressure

def distribution_water_flow(grid, config, state, prev_state):
    # calculate every tile's precipitation and initial water flow
    for tile in grid.tiles:
        # get local precipitation
        state[tile.id]['precipitation'] = calculate_precipitation(
            config,
            state[tile.id]['vapor_content'],
            state[tile.id]['vapor_capacity'],
            state[tile.id]['cloud_density']
        )

        # adjust vapor content and set water flow based on how much it rained
        # these, along with precipitation, are all referenced in kg per area, so it's a straight conversion
        # NOTE: technically, water_flow is per area and per second, but we're ignore the per second part for now, we could take any time reference we wanted, since we never actually work with time
        state[tile.id]['vapor_content'] -= state[tile.id]['precipitation']
        if not is_sea_tile(tile, config): # sea tiles don't have water flow
            state[tile.id]['water_flow'] = state[tile.id]['precipitation']

        # cloud density is adjusted based on the change in vapor content
        state[tile.id]['cloud_density'] = calculate_cloud_density(
            config,
            state[tile.id]['cloud_density'],
            state[tile.id]['vapor_content'],
            state[tile.id]['vapor_capacity']
        )

    # queue = every tile on the map which is above sea level, sorted by altitude (highest first)
    queue = sorted([tile for tile in grid.tiles if not is_sea_tile(tile)], key=lambda tile: tile.altitude, reverse=True)
    while queue:
        tile = queue.pop(0)

        # find altitude gradients to each neighbor
        gradients = []
        for neighbor in tile.get_neighbors():
            if neighbor.altitude < tile.altitude: # water only flows to lower tiles
                gradients.append((neighbor, neighbor.altitude - tile.altitude))

        # divide local water_flow between neighbors, weighted by the gradient (bigger change in altitude = more water flowing towards it)
        for neighbor, gradient in gradients:
            state[neighbor.id]['water_flow'] += state[tile.id]['water_flow'] * gradient


# === MAIN FUNCTIONS ===
# iterative method:
# input: config, prev_state, latitude, is_sea_tile, altitude
# 1. source calculations (based on prev state)
#   1.1 solar radiation - from previous state's cloud density (its not too important to have the most accurate factor here)
#   1.2 biomass
#   1.3 evaporation                # based on the previous water cycle
#   1.4 evapotranspiration         #
#   1.5 plant_humidity_absorption  #

# 2. our mega strongly-connected component
#   2.2 calculate temperature
#       2.2.1 calculate air pressure
#   2.3 calculate evaporation from previous state (water flows should be relatively stable so this wont matter much)
#   2.4 calculate vapor capacity
#   2.5 calculate vapor content
#   2.6 calculate cloud density

# 3. distribution flows
#   3.1 wind
#       3.2.1 calculate wind map from air pressure
#       3.2.2 distribute temperature, air pressure, vapor content and clouds
#   3.2 water
#       3.2.1 calculate precipitation - important that it's AFTER wind
#           add water flow to a tile and subtract vapor content based on how much it rained
#                adjust cloud density after the change to vapor content
#       3.2.2 create map of water flow. Additive process only, flow is not destroyed, only added to children.
#           sea tiles always have maximum flow
def iterate_climate(grid, config, prev_state):
    # each of the functions mutates state directly
    state = init_state(grid)
    
    # variables we base on prev state
    all_solar_radiation(grid, config, state, prev_state)
    all_biomass(grid, config, state, prev_state)
    all_evaporation(grid, config, state, prev_state)
    all_evapotranspiration(grid, config, state, prev_state)
    all_plant_humidity_absorption(grid, config, state, prev_state)
    
    # fresh variables - based on variables from this same state
    all_temperature(grid, config, state, prev_state)
    if config['climate']['smoothen_temperature_map']:
        smoothen_temperature(grid, config, state, prev_state)
    all_air_pressure(grid, config, state, prev_state)
    all_vapor_capacity(grid, config, state, prev_state)
    all_vapor_content(grid, config, state, prev_state) # this one also depends on prev_state, but only on itself
    all_cloud_density(grid, config, state, prev_state)
        
    # calculate wind
    all_wind(grid, config, state, prev_state)
    # distribute stuff via wind
    distribution_wind(grid, config, state, prev_state)
    
    # calculate precipitation, adjust cloud density, distribute water flow throughout the world
    distribution_water_flow(grid, config, state, prev_state)

def starting_state(grid, config):
    state = init_state(grid)
    
    #           (is required means it's needed for the first iteration)
    # VARIABLE                  - IS REQUIRED - IS INITIALIZED
    # solar radiation           - Yes         - Yes
    # temperature               - Yes         - Yes
    # vapor_capacity            - Yes         - Yes
    # evaporation               - No          - As 0
    # evapotranspiration        - Yes         - As 0
    # plant_humidity_absorption - Yes         - As 0
    # vapor_content             - No          - Yes
    # air_pressure              - No          - Yes
    # cloud_density             - No          - Yes
    # biomass                   - No          - No
    # wind                      - No          - No
    # precipitation             - No          - No
    # water_flow                - No          - No
    for tile in grid.tiles:
        state[tile.id]['solar_radiation'] = calculate_solar_radiation_init(
            config,
            normalized_latitude(tile)
        )

        state[tile.id]['temperature'] = calculate_temperature_init(
            config,
            state[tile.id]['solar_radiation'],
            tile.altitude
        )

        state[tile.id]['vapor_capacity'] = calculate_vapor_capacity_init(
            config,
            state[tile.id]['temperature']
        )
        
        state[tile.id]['vapor_content'] = calculate_vapor_content_init(
            config,
            is_sea_tile(tile, config)
        )
        
        state[tile.id]['air_pressure'] = calculate_air_pressure_init(
            config,
            state[tile.id]['temperature'],
            tile.altitude
        )
        
        state[tile.id]['cloud_density'] = calculate_cloud_density_init(
            config,
            state[tile.id]['vapor_content'],
            state[tile.id]['vapor_capacity']
        )

        state[tile.id]['evaporation'] = 0.0
        state[tile.id]['evapotranspiration'] = 0.0
        state[tile.id]['plant_humidity_absorption'] = 0.0

    return state

# the actual function supposed to be called from outside this module
def generate_climate(grid, config):
    CLIMATE_MAX_ITER = config['climate']['max_iterations']
    
    state = starting_state(grid, config)

    for i in range(CLIMATE_MAX_ITER):
        prev_state = state
        state = iterate_climate(grid, config, prev_state)

    return state
