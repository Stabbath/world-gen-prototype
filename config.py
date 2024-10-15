from generators.tectonic_generator_faults import generate_world_faults
from generators.tectonic_generator_plates import generate_world_plates

# TODO - this will become the way we interface with the generation later.
# "config" will list the customizable options for generation, e.g. number of plates or lines, the data type and acceptable range
# this will inform the UI for world gen, and will be how the generation functions process these settings


# === BASE IDEA ===
# We store default values for configurable settings here.
# We also set the structure of the input fields to match those settings.
# We consider that each "method", which might be a part of a larger method (e.g. PLATES method can have different ways of calculating elevation map), is just a generic "method", we don't distinguish them.
# Config properties for the top level, in both logic and UI layout, are stored at the root level of config, under their id. The core object is a generic dictionary.
# Config properties for methods, in both logic and UI layout, are stored inside a child dictionary, under a property of the root which is named after the id of the method.
# So, we just need to be careful not to have duplicate id's, knowing especially that a global property cannot have the same name as any method, no matter the method's level.

def default_config():
    config = {
        "max_altitude": 20000,
        "sea_level": 10000,
        "width": 120,
        "height": 80
    }
    config['gen_method'] = 'faults'
    
    config['plates'] = {}
    config['plates']['gen_plate_count'] = 60
    config['plates']['altitude_gen_method'] = 'generator_consumer'
    config['plates']['individual_spread'] = True
    config['plates']['random_pop'] = False
    config['plates']['fault_smoothing'] = True
    config['plates']['merge_plates_count'] = 48
    
    config['faults'] = {}
    config['faults']['n_selected_tiles'] = 3
    config['faults']['branching_chance'] = 0.01
    config['faults']['max_branch_depth'] = 1
    config['faults']['stop_on_intersection'] = True
    config['faults']['method'] = 1 # Choose the method for the fault generation. 
    # Method 1: generates lines 1 by 1 and the branches are generated during the procedure
    # Method 2: generates lines 1 by 1 and the branches are generated after the main faults
    # Method 3: generated lines in parallel and the branches are generated during the procedure
    # Method 4: generates lines in parallel and the branches are generated after the main faults.
    
    config['generator_consumer'] = {}
    config['generator_consumer']['max_iter'] = 100
    config['generator_consumer']['max_genfactor'] = 1
    config['generator_consumer']['plate_continental_factor'] = 0.05
    config['generator_consumer']['noise_factor'] = 0.1
    config['generator_consumer']['smoothen_genfactors'] = False
    config['generator_consumer']['polar_plates_are_oceanic'] = False
    config['generator_consumer']['continental_plates_count'] = 2
    config['generator_consumer']['continents_count'] = 0
    return config

# === BASE IDEA (cont.) - UI ===
# Each field is stored as an object, which has a name, id, type, and optionally also filter.
#   type can be any standard data type, or 'select'
#       the options to be made available for any given select are stored in a common "select_options" dict, indexed by the id of the input
#   filter is a function which binds any value sent to it to an accepted range

# NOTE - default values for UI fields should be fetched from the default config above. Id's MUST match

# === FILTER FUNCTIONS FOR INPUTS ===
def filter_positive_integer(new_val, old_val):
    # TODO - add type checks, return old_val if new_val is not an int (and can't be converted to one)
    if new_val < 1:
        return 1
    return int(new_val)

def filter_positive_float(new_val, old_val):
    # TODO - add type checks, return old_val if new_val is not a float (and can't be converted to one)
    if new_val <= 0.0:
        return 0.0
    return new_val

# === CORE FIELDS === 
ui_fields = {}
ui_fields['gen_method'] = {
    'name': 'Method',
    'id': 'gen_method',
    'type': 'select',
    'options': [
        'plates', 'faults'
    ]
}

ui_fields['height'] = {
    'name': 'Height',
    'id': 'height',
    'type': int,
    'filter': filter_positive_integer
}
ui_fields['width'] = {
    'name': 'Width',
    'id': 'width',
    'type': int,
    'filter': filter_positive_integer
}
ui_fields['max_altitude'] = {
    'name': 'Max Elevation',
    'id': 'max_altitude',
    'type': int,
    'filter': filter_positive_integer
}
ui_fields['sea_level'] = {
    'name': 'Sea Level',
    'id': 'sea_level',
    'type': int,
    'filter': filter_positive_integer
}

# === PLATES FIELDS === 
ui_fields['plates'] = {}
ui_fields['plates']['altitude_gen_method'] = {
    'name': 'Elevation Map Generator',
    'id': 'altitude_gen_method',
    'type': 'select',
    'options': [
        'generator_consumer'
    ]
}
ui_fields['plates']['individual_spread'] = {
    'name': 'Individual Spread?',
    'id': 'individual_spread',
    'type': bool
}
ui_fields['plates']['random_pop'] = {
    'name': 'Random Queue Pop?',
    'id': 'random_pop',
    'type': bool
}
ui_fields['plates']['fault_smoothing'] = {
    'name': 'Reduce and Smoothen Faults?',
    'id': 'fault_smoothing',
    'type': bool
}

# === GENERATOR/CONSUMER FIELDS ===
ui_fields['generator_consumer'] = {}
ui_fields['generator_consumer']['max_iter'] = {
    'name': 'Iterations',
    'id': 'max_iter',
    'type': int,
    'filter': filter_positive_integer
}
ui_fields['generator_consumer']['max_genfactor'] = {
    'name': 'Gen Factor Multiplier',
    'id': 'max_genfactor',
    'type': float,
    'filter': filter_positive_float
}
ui_fields['generator_consumer']['noise_factor'] = {
    'name': 'Noise Factor',
    'id': 'noise_factor',
    'type': float,
    'filter': filter_positive_float
}
ui_fields['generator_consumer']['smoothen_genfactors'] = {
    'name': 'Smoothen Gen Factors?',
    'id': 'smoothen_genfactors',
    'type': bool
}

# === FAULTS FIELDS === 
ui_fields['faults'] = {}
# ...

        