from generators.tectonic_generator_faults import generate_world_faults
from generators.tectonic_generator_plates import generate_world_plates
from abc import ABC, abstractmethod

# TODO - this will become the way we interface with the generation later.
# "config" will list the customizable options for generation, e.g. number of plates or lines, the data type and acceptable range
# this will inform the UI for world gen, and will be how the generation functions process these settings

# Initial Grid settings
INITIAL_GRID_COLS = 50  # Increased grid size for better visual effect
INITIAL_GRID_ROWS = 50  # Increased grid size for better visual effect

# Number of tiles to select for fault generation
INITIAL_N_SELECTED_TILES = 12  # Number of starting points along the boundaries

# Generation method
GEN_METHOD = 0  # Set to 0 for fault-based generation, 1 for plate-based generation

MAX_ALTITUDE = 20000
SEA_LEVEL = 10000

def default_config():
    return {
        "gen_method": GEN_METHOD,
        "max_altitude": MAX_ALTITUDE,
        "sea_level": SEA_LEVEL,
        "width": INITIAL_GRID_COLS,
        "height": INITIAL_GRID_ROWS,
        "startpoint_count": INITIAL_N_SELECTED_TILES,
    }

def default_config_plates():
    config = default_config()
    config['gen_method'] = 1
    config['generator_consumer'] = {}
    config['generator_consumer']['max_iter'] = 100
    config['generator_consumer']['max_genfactor'] = 1
    config['generator_consumer']['noise_factor'] = 0.02
    config['generator_consumer']['smoothen_genfactors'] = False
    return config

# # Basically, the structure of a method is as follows:
# # name
# # id (unique)
# # props (each prop should have a name, id, type, and default value. These will be inputs we add dynamically to the config panel)
# # submethods (a list of sub-method selectors. Each stores a name (label for the Select field), id, and list of methods which are the options for that field. This should be nestable, so a method in a submethod can have submethods of its own)



# class PlatesMethod(GenerationMethod):
#     def __init__(self):
#         self.func = generate_world_plates
#         self.props = {
#             'random_pop': True,
#             'fault_smoothing': True,
#             'individual_spread': False
#         }

#     def get_name(self): return 'Tectonic'
    
#     def get_id(self): return 'tectonic'

#     def get_props_ui(self):
#         return [
#             {
#                 'id': 'random_pop',
#                 'name': 'Random Pop',
#                 'type': bool
#             },
#             {
#                 'id': 'fault_smoothing',
#                 'name': 'Fault Reduce',
#                 'type': bool
#             },
#             {
#                 'id': 'individual_spread',
#                 'name': 'Individual Spread',
#                 'type': bool
#             }
#         ] + super.get_props_ui()

#     def get_props(self):
#         return self.props

#     def set_prop(self, prop, value):
#         self.props[prop] = value

#     def generate(self, props):
        
        
            
# class PlatesMethod(GenerationMethod)
    

# FAULTS_METHOD_CFG = {
#     'name': 'Faults',
#     'id': 'faults',
#     'func': generate_world_faults,
#     'props': []
# }

# TECTONIC_METHOD_CFG = {
#     'name': 'Tectonic',
#     'id': 'tectonic',
#     'props': [

#     ],
#     'submethods': [
#         {
#             'id': 'tectonic_sub',
#             'name': 'Submethod',
#             'methods': [
#                 PLATES_METHOD_CFG,
#                 FAULTS_METHOD_CFG
#             ]
#         }
#     ]
# }



        