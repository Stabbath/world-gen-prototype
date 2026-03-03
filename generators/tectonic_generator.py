from fault_method import generate_world_faults
from plate_method import generate_world_plates

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
        'methods': [ # TODO - this will basically replace "gen_method" and all code using it
            TECTONIC_METHOD_CFG
        ]
    }

# Basically, the structure of a method is as follows:
# name
# id (unique)
# props (each prop should have a name, id, type, and default value. These will be inputs we add dynamically to the config panel)
# submethods (a list of sub-method selectors. Each stores a name (label for the Select field), id, and list of methods which are the options for that field. This should be nestable, so a method in a submethod can have submethods of its own)

PLATES_METHOD_CFG = {
    'name': 'Plates',
    'id': 'plates',
    'func': generate_world_plates,
    'props': [
        {
            'name': 'Fault Reduce',
            'id': 'fault_smoothing',
            'type': bool,
            'default': True
        }
    ]
}

FAULTS_METHOD_CFG = {
    'name': 'Faults',
    'id': 'faults',
    'func': generate_world_faults,
    'props': []
}

TECTONIC_METHOD_CFG = {
    'name': 'Tectonic',
    'id': 'tectonic',
    'props': [

    ],
    'submethods': [
        {
            'name': 'Submethod',
            'id': 'tectonic_sub',
            'methods': [
                PLATES_METHOD_CFG,
                FAULTS_METHOD_CFG
            ]
        }
    ]
}



        