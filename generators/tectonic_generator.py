from fault_method import generate_world_faults
from plate_method import generate_world_plates

# TODO - this will become the way we interface with the generation later.
# "config" will list the customizable options for generation, e.g. number of plates or lines, the data type and acceptable range
# this will inform the UI for world gen, and will be how the generation functions process these settings
class TectonicGenerator:
    def get_configs(self):
        return [
            {
                'genId': 'faults',
                'name': 'Tectonic Gen - Fault Method',
                'genFunc': generate_world_faults,
                'config': {}
            },
            {
                'genId': 'plates',
                'name': 'Tectonic Gen - Plate Method',
                'genFunc': generate_world_plates,
                'config': {}
            }
        ]
        