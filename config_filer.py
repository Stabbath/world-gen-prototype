# This is a simpler alternative to the annoying-to-prototype-in-pygame UI shit.
# Just read the config from a json file whenever we regenerate.
# That way we can edit it live while running the app.

import json

PATH='config.json'

def config_to_file(config):
    with open(PATH, 'w') as f:
        json.dump(config, f, indent=4)  # Write the config as JSON to the file

def config_from_file():
    with open(PATH, 'r') as f:
        config = json.load(f)
    return config

# this function is required so we can change the config by reference
def update_config_from_file(config):
    from_file = config_from_file()
    
    # Update the existing config with all of the properties from from_file.
    config.update(from_file)