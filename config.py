import pygame

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
        "max_altitude": MAX_ALTITUDE, # TODO - note this should be read from the inputs, which will also determine the value during world gen
        "sea_level": SEA_LEVEL, # TODO - it would be cool if we could dynamically change sea level, but not a priority
        "width": INITIAL_GRID_COLS,
        "height": INITIAL_GRID_ROWS,
        "startpoint_count": INITIAL_N_SELECTED_TILES
    }

class ConfigPanel:
    def __init__(self, panel_width, screen_height, config, background_color=(30, 30, 30)):
        self.panel_rect = pygame.Rect(0, 0, panel_width, screen_height)
        self.background_color = background_color
        self.panel_width = panel_width
        self.config = config

        # Buttons and controls in the left panel
        self.regenerate_button_rect = pygame.Rect(20, 60, panel_width - 40, 30)
        self.gen_method_label_rect = pygame.Rect(20, 110, panel_width - 40, 20)
        self.gen_method_button_rect = pygame.Rect(20, 140, panel_width - 40, 30)
        self.n_selected_label_rect = pygame.Rect(20, 190, panel_width - 40, 20)
        self.n_selected_increase_rect = pygame.Rect(20, 220, (panel_width - 60) // 2, 30)
        self.n_selected_decrease_rect = pygame.Rect(40 + (panel_width - 60) // 2, 220, (panel_width - 60) // 2, 30)

    def process_event(self, event):
        # Check if mouse is over the left panel controls
        if self.regenerate_button_rect.collidepoint(event.pos):
            return 'regen'
        elif self.gen_method_button_rect.collidepoint(event.pos):
            self.config['gen_method'] = 1 - self.config['gen_method']
            return 'config_changed'
        elif self.n_selected_increase_rect.collidepoint(event.pos):
            self.config['startpoint_count'] += 1
            return 'config_changed'
        elif self.n_selected_decrease_rect.collidepoint(event.pos):
            if self.config['startpoint_count'] > 1:
                self.config['startpoint_count'] -= 1
                return 'config_changed'

    def draw(self, screen, font):
        pygame.draw.rect(screen, self.background_color, self.panel_rect)

        # Draw regenerate button
        pygame.draw.rect(screen, (70, 70, 70), self.regenerate_button_rect)
        regen_text = font.render("Regenerate", True, (255, 255, 255))
        regen_text_rect = regen_text.get_rect(center=self.regenerate_button_rect.center)
        screen.blit(regen_text, regen_text_rect)

        # Draw generation method label and button
        gen_method_label = font.render("Generation Method:", True, (255, 255, 255))
        screen.blit(gen_method_label, self.gen_method_label_rect.topleft)
        gen_method_text = "Plate Tectonics" if self.config['gen_method'] == 1 else "Fault Lines"
        pygame.draw.rect(screen, (70, 70, 70), self.gen_method_button_rect)
        method_text = font.render(gen_method_text, True, (255, 255, 255))
        method_text_rect = method_text.get_rect(center=self.gen_method_button_rect.center)
        screen.blit(method_text, method_text_rect)

        # Draw n_selected_tiles label and buttons
        n_selected_label = font.render("Number of Plates:", True, (255, 255, 255))
        screen.blit(n_selected_label, self.n_selected_label_rect.topleft)
        # Increase button
        pygame.draw.rect(screen, (70, 70, 70),self. n_selected_increase_rect)
        inc_text = font.render("+", True, (255, 255, 255))
        inc_text_rect = inc_text.get_rect(center=self.n_selected_increase_rect.center)
        screen.blit(inc_text, inc_text_rect)
        # Decrease button
        pygame.draw.rect(screen, (70, 70, 70), self.n_selected_decrease_rect)
        dec_text = font.render("-", True, (255, 255, 255))
        dec_text_rect = dec_text.get_rect(center=self.n_selected_decrease_rect.center)
        screen.blit(dec_text, dec_text_rect)
        # Display current n_selected_tiles value
        n_selected_value_text = font.render(str(self.config['startpoint_count']), True, (255, 255, 255))
        n_selected_value_rect = n_selected_value_text.get_rect(center=(self.panel_width // 2, 235))
        screen.blit(n_selected_value_text, n_selected_value_rect)