import random
from utils import gaussian_in_range

def generator_consumer_model(grid, config, func_neighbors):
    # Straightforward - when we're expanding our plates and run into a filled neighbor, we turn the tile into a fault.

    # === Step 2: Assignment of Fault and/or Plate Properties ===
    # This is deeply connected to step 3. Our altitude generation depends on the properties we include. 
    # And for the same properties, there may be different altitude generation methods.
    # For now, just assuming my initial method. Later, we'll need to possibly restructure/extract things to make it more flexible, with different combinations of Property Assignment and Altitude Map Generation

    MAX_ALTITUDE=config['max_altitude']
    MAX_ITER = config['generator_consumer']['max_iter']
    MAXGENFACTOR = config['generator_consumer']['max_genfactor']
    NOISE_FACTOR = config['generator_consumer']['noise_factor']
    SMOOTHEN_GENFACTORS = config['generator_consumer']['smoothen_genfactors']
    plate_continental_factor = config['generator_consumer']['plate_continental_factor']

    # Step 2.1 - Plate Properties
    plate_is_continental = {}
    for plate in grid.plates:
        plate_is_continental[plate.id] = False # init

    unassigned_plates = list(grid.plates)
    continentals_assigned = 0
    
    if config['generator_consumer']['polar_plates_are_oceanic']: 
        # make it so polar plates cannot be assigned
        for plate in grid.plates:
            if plate.borders_pole():
                unassigned_plates.remove(plate)
    
    while continentals_assigned < config['generator_consumer']['continental_plates_count'] and len(unassigned_plates) > 0:
        plate = random.choice(unassigned_plates)
        plate_is_continental[plate.id] = True
        continentals_assigned += 1
        unassigned_plates.remove(plate)
    
    # # 50/50 init
    # for plate in grid.plates:
    #     plate_is_continental[plate.id] = bool(random.getrandbits(1)) # 50/50 for now


    # Step 2.2 - Fault Properties
    # First, we assign to each fault a float between 1 and -1, completely at random. This is its Generation Factor. If negative, it means it consumes mass. If positive, it generates it.
    # We use a dictionary, external to the Fault class.
    generation_factors = {}
    for fault in grid.faults:
        generation_factors[fault.id] = gaussian_in_range(min=-1, max=1)

    # Then we smooth these factors: we check for each fault its neighboring faults, and the Generation Factor we have for it,
    # and we recalculate them all as a weighted average of their own factor and their neighbors', with their own factor being worth twice as much for the average.
    if SMOOTHEN_GENFACTORS:
        smoothed_generation_factors = {}
        for fault in grid.faults:
            own_factor = generation_factors[fault.id]
            neighbor_indices = fault.get_fault_neighbor_indices()
            neighbor_factors = [generation_factors[neighbor_index] for neighbor_index in neighbor_indices]
            total_weight = 2 + len(neighbor_factors)
            weighted_sum = 2 * own_factor + sum(neighbor_factors)
            smoothed_factor = weighted_sum / total_weight
            smoothed_generation_factors[fault.id] = smoothed_factor
        generation_factors = smoothed_generation_factors
    
    # Then, we renormalize everything so that the lowest is -1 and the highest is +1.
    factor_values = generation_factors.values()
    min_factor = min(factor_values)
    max_factor = max(factor_values)
    for fault_id, factor in generation_factors.items():
        normalized_factor = -1 + 2 * (factor - min_factor) / (max_factor - min_factor)
        generation_factors[fault_id] = normalized_factor

    
    # === Step 3: Altitude Map Generation ===
    # Each iteration has the following steps: 
    #   1. Each fault adds landmass to itself equal to its generation_factor times the MaxGenFactor
    #   2. We add a small amount of noise to the entire hex grid.
    #   3. We smoothen the entire hexgrid based on neighbors
    for _ in range(MAX_ITER):
        # Step 1: Each fault adds landmass to itself equal to its generation_factor times the MaxGenFactor
        for fault in grid.faults:
            gen_factor = generation_factors[fault.id]
            mass_change = gen_factor * MAXGENFACTOR
            for tile in fault.get_tiles():
                alt = tile.get_altitude()
                tile.set_altitude(alt + mass_change)

        # Then, if we are using continental vs oceanic plate features, we assign one of those 2 properties to each plate
        # For every tile in a continental plate, we add the appropriate altitude.
        # We use a dictionary, external to the Plate class.
        if plate_continental_factor:
            for plate in grid.plates:
                if plate_is_continental[plate.id]:
                    for tile in plate.tiles:
                        alt = tile.get_altitude()
                        tile.set_altitude(alt + plate_continental_factor)
        
        # Step 2: Add a small amount of noise to the entire hex grid
        for tile in grid.get_tiles():
            alt = tile.get_altitude()
            noise = random.uniform(-1, 1) * NOISE_FACTOR
            tile.set_altitude(alt + noise)
        
        # Step 3: Smooth the entire hexgrid based on neighbors
        # Collect current altitudes before smoothing
        tile_altitudes = {tile: tile.get_altitude() for tile in grid.get_tiles()}
        for tile in grid.get_tiles():
            neighbors = tile.get_neighbors()
            neighbor_alts = [tile_altitudes[neighbor] for neighbor in neighbors]
            avg_neighbor_alt = sum(neighbor_alts) / len(neighbor_alts)
            # New altitude is the average of own altitude and neighbors'
            new_altitude = (tile_altitudes[tile] + avg_neighbor_alt) / 2
            tile.set_altitude(new_altitude)
    
    # Finally, we normalize the altitude of every tile according to MAXALTITUDE, so that the lowest altitude is 0, and the highest altitude is 20000.
    altitudes = [tile.get_altitude() for tile in grid.get_tiles()]
    min_altitude = min(altitudes)
    max_altitude = max(altitudes)
    
    for tile in grid.get_tiles():
        alt = tile.get_altitude()
        normalized_altitude = (alt - min_altitude) / (max_altitude - min_altitude) * MAX_ALTITUDE
        tile.set_altitude(normalized_altitude)
    return grid
