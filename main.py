import math
import pygame
import sys
import traceback
from camera import Camera
from hex_view import HexView
from hex_view_colors import color_plates, color_altitude, color_hydro, color_faults, color_biomass, color_temperature, color_sea_pressure, color_humidity, color_clouds
from map_generator import generate_map
from neighbor_functions import get_neighbors_wraparound
from config import default_config, ui_fields as UI_FIELDS
#from config_panel import ConfigPanel
from config_filer import update_config_from_file, config_to_file
from view_tabs import TabPanel
from climate.climate import generate_climate

from hex_view_labels import wind_overlay_element, water_flow_overlay_element

# ------------------------------
# Constants and Configurations
# ------------------------------

# Screen settings
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
BACKGROUND_COLOR = (0, 0, 0)  # Black background
FPS = 60  # Cap the frame rate at 60 FPS

# Panel settings
PANEL_WIDTH = 0  # Width of the left-side panel
TAB_BUTTON_WIDTH = 100
TAB_BUTTON_HEIGHT = 30
TAB_BUTTON_PADDING = 10
TABS_HEIGHT = TAB_BUTTON_HEIGHT + TAB_BUTTON_PADDING 

# Hexagon settings
HEX_SIZE = 20  # Adjusted size
HEX_HEIGHT = math.sqrt(3) * HEX_SIZE
HEX_WIDTH = 2 * HEX_SIZE
VERTICAL_SPACING = HEX_HEIGHT
HORIZONTAL_SPACING = HEX_WIDTH * 0.75  # Flat-topped hexagons overlap horizontally by 25%

# Zoom settings
ZOOM_STEP = 1.1  # Zoom in/out factor per mouse wheel event
MIN_ZOOM = 0.1   # Reduced minimum zoom level to allow more zooming out
MAX_ZOOM = 3.0   # Maximum zoom level


VIEW_LABELS = ["Plates", "Faults", "Elevation", "Hydro", 
               "Temperature", "Pressure", "Humidity",
               "Clouds", "Biomass"]

OVERLAY_LABELS = ["None", "Wind", "Water Flow"]

# Define overlay functions and their parameters
OVERLAY_FUNCTIONS = {
    "Wind": wind_overlay_element,
    "Water Flow": water_flow_overlay_element
}

OVERLAY_REF = {
    "Wind": 100.0,
    "Water Flow": 10.0
}

OVERLAY_DRAW_SIZE = {
    "Wind": 400,
    "Water Flow": 100
}


def full_gen(config):
    print('Generating everything...')
    # NOTE - this is kind of a bandaid to simplify logic.
    # The UI was a pain in the ass, so now we read and re-read the config from a json file whenever we want to generate a map
    update_config_from_file(config)
    hex_grid = gen_world(config)
    hex_grid.climate_data = gen_climate(config, hex_grid)
    print('Done')
    hex_views = gen_views(config, hex_grid)
    return hex_grid, hex_views

def gen_climate(config, hex_grid):
    return generate_climate(hex_grid, config)

def regen_climate(config, hex_grid):
    print('Regenerating climate...')
    update_config_from_file(config)
    hex_grid.climate_data = generate_climate(hex_grid, config)
    print('Done')
    hex_views = gen_views(config, hex_grid)
    return hex_views

hex_view_color_map = {
    "Plates": color_plates,
    "Faults": color_faults,
    "Elevation": color_altitude,
    "Hydro": color_hydro,
    "Temperature": color_temperature,
    "Biomass": color_biomass,
    "Pressure": color_sea_pressure,
    "Humidity": color_humidity,
    "Clouds": color_clouds
}

def gen_views(config, hex_grid):
    
    # HexViews for different tabs
    hex_views = {}
    for key in hex_view_color_map.keys():
        func = hex_view_color_map[key]
        hex_views[key] = HexView(hex_grid, size=HEX_SIZE, func_color=func, config=config)
    return hex_views

def gen_world(config):
    hex_grid = generate_map(
        config,
        func_neighbors=get_neighbors_wraparound
    )
    return hex_grid

def print_tile_info(tile, config):
    climate = tile.grid.climate_data
    print('Tile', tile.col, ',', tile.row)
    print('Elevation', tile.altitude - config['sea_level'])
    print('Vapor', int(climate[tile.id]['vapor_content'] / 1000000), 'M /', int(climate[tile.id]['vapor_capacity'] / 1000000), 'M')
    print('Humidity', (climate[tile.id]['vapor_content'] / climate[tile.id]['vapor_capacity'] * 100), '%')
    print('Wind', climate[tile.id]['wind'], 'm/s')
    print('Water Flow', climate[tile.id]['water_flow'])
    print('Air Pressure', climate[tile.id]['sea_level_air_pressure'])

# ------------------------------
# Pygame Initialization and Main Loop
# ------------------------------

def main():
    try:
        # Initialize Pygame
        pygame.init()
        pygame.font.init()  # Initialize font module

        # Set up the display
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Hexagonal Grid World with Zoom and Pan")

        # Create a clock to manage the frame rate
        clock = pygame.time.Clock()

        # Initialize Camera
        camera = Camera(zoom=1.0, 
                        offset=(- PANEL_WIDTH, - TABS_HEIGHT * 2),
                        min_zoom=MIN_ZOOM, 
                        max_zoom=MAX_ZOOM)
        
        # Variables for panning
        is_panning = False
        pan_start_pos = pygame.math.Vector2(0, 0)
        pan_start_offset = pygame.math.Vector2(0, 0)

        config = default_config() # TODO - temp, but plates config has nothing that would tamper with faults method, right now anyway
        
        # NOTE - this is for our bandaid config input solution
        # it just makes sure that the file's starting settings are always the same as we've set them in our default_config in code
        config_to_file(config)

        # Initial map generation
        hex_grid, hex_views = full_gen(config)
        
        current_tab = VIEW_LABELS[0] # defaul view
        current_overlay = OVERLAY_LABELS[0]

        font = pygame.font.SysFont('Arial', 18)

        def config_panel_callback(action):
            nonlocal hex_grid, hex_views
            if action == 'regen':
                hex_grid, hex_views = full_gen(config)
            elif action == 'config_changed':
                pass # we don't need to do anything, config is changed in place

#        config_panel = ConfigPanel(PANEL_WIDTH, SCREEN_HEIGHT, config, UI_FIELDS, font, config_panel_callback)
        tab_panel = TabPanel(VIEW_LABELS, PANEL_WIDTH, TAB_BUTTON_WIDTH, TAB_BUTTON_HEIGHT, TAB_BUTTON_PADDING)
        overlay_panel = TabPanel(OVERLAY_LABELS, PANEL_WIDTH, TAB_BUTTON_WIDTH, TAB_BUTTON_HEIGHT, TAB_BUTTON_PADDING, TABS_HEIGHT)
        
        # Main view rectangle adjusted to not overlap with tab buttons
        main_view_rect = pygame.Rect(PANEL_WIDTH, TABS_HEIGHT, SCREEN_WIDTH - PANEL_WIDTH, SCREEN_HEIGHT - TABS_HEIGHT)

        # Main loop flag
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
        
                # # Process the event with the config panel first
                # if config_panel.process_event(event):
                #     # If the config panel handled the event, skip further processing
                #     continue
        
                # TODO - should clean this up a bit. We should have the view pane in its own class, and then here we would just call "process_event" for each component.
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # First, check if the click is on any tab button
                    tab_clicked = tab_panel.process_event(event)
                    overlay_clicked = overlay_panel.process_event(event)
        
                    if tab_clicked is not None:
                        current_tab = tab_clicked
                    elif overlay_clicked is not None:
                        current_overlay = overlay_clicked
                    else:
                        # Check if mouse is over the main view pane
                        if main_view_rect.collidepoint(event.pos):
                            mouse_pos = pygame.math.Vector2(event.pos)
                            # Convert screen coordinates to world coordinates
                            # Adjust for the main view pane's position
                            adjusted_screen_pos = mouse_pos - pygame.math.Vector2(main_view_rect.topleft)
                            world_pos = camera.screen_to_world(adjusted_screen_pos)

                            # Iterate through all tiles in the current view to find which one contains the point
                            clicked_tile = None
                            for tile in hex_views[current_tab].tiles:
                                if tile.contains_point(world_pos):
                                    clicked_tile = tile
                                    break

                            if clicked_tile:
                                print_tile_info(clicked_tile.tile, config)
                                
                            if event.button == 4:  # Mouse wheel up to zoom in
                                mouse_pos = event.pos
                                camera.adjust_zoom(ZOOM_STEP, mouse_pos)
                            elif event.button == 5:  # Mouse wheel down to zoom out
                                mouse_pos = event.pos
                                camera.adjust_zoom(1 / ZOOM_STEP, mouse_pos)
                            elif event.button == 1:  # Left mouse button to start panning
                                is_panning = True
                                pan_start_pos = pygame.math.Vector2(event.pos)
                                pan_start_offset = camera.offset.copy()
        
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left mouse button to stop panning
                        is_panning = False
        
                elif event.type == pygame.MOUSEMOTION:
                    if is_panning:
                        current_pos = pygame.math.Vector2(event.pos)
                        delta = current_pos - pan_start_pos
                        camera.offset = pan_start_offset + delta
        
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # Regenerate the map with current settings
                        hex_grid, hex_views = full_gen(config)
                    elif event.key == pygame.K_c:
                        # Regenerate climate with current settings
                        hex_views = regen_climate(config, hex_grid)

            # Clear the screen
            screen.fill(BACKGROUND_COLOR)
        
            # # Draw left panel
            # config_panel.draw(screen)
        
            # Draw main view pane background
            pygame.draw.rect(screen, (50, 50, 50), main_view_rect)
        
            # Draw the hex grid within the main view pane
            if current_tab and hex_views.get(current_tab):
                # Create a surface for the main view
                main_view_surface = pygame.Surface((main_view_rect.width, main_view_rect.height), pygame.SRCALPHA)
                main_view_surface.fill(BACKGROUND_COLOR)  # Background color
    
                # Draw the hex grid itself
                hex_views[current_tab].draw(main_view_surface, camera)
    
                # Draw overlays if an overlay is selected
                if current_overlay != "None" and current_overlay in OVERLAY_FUNCTIONS:
                    overlay_func = OVERLAY_FUNCTIONS[current_overlay]
                    ref_value = OVERLAY_REF[current_overlay]
                    draw_size = OVERLAY_DRAW_SIZE[current_overlay]
    
                    for tile in hex_views[current_tab].tiles:
                        overlay_color = hex_view_color_map[current_tab](tile, config)[2]  # Get overlay color from the map
                        # Get the overlay element for the tile
                        overlay_element = overlay_func(tile.tile, hex_grid.climate_data, ref_value, draw_size, overlay_color, camera)
                        if overlay_element:
                            # Blit the overlay element onto the main view surface
                            main_view_surface.blit(
                                overlay_element,
                                camera.world_to_screen(tile.center)
                            )
    
                # Blit the main view surface onto the screen at the correct position
                screen.blit(main_view_surface, (PANEL_WIDTH, TABS_HEIGHT))
            
            # Draw tabs on top of the main view
            tab_panel.draw(screen, font, current_tab)
            overlay_panel.draw(screen, font, current_overlay)
        
            # Update the display
            pygame.display.flip()
        
            # Cap the frame rate at 60 FPS
            clock.tick(FPS)

    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()
    finally:
        # Quit Pygame
        pygame.quit()
        sys.exit()

# ------------------------------
# Entry Point
# ------------------------------

if __name__ == "__main__":
    main()
