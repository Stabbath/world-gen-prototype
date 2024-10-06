import pygame

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

        # Width controls
        self.width_label_rect = pygame.Rect(20, 270, panel_width - 40, 20)
        self.width_increase_rect = pygame.Rect(20, 300, (panel_width - 60) // 2, 30)
        self.width_decrease_rect = pygame.Rect(40 + (panel_width - 60) // 2, 300, (panel_width - 60) // 2, 30)

        # Height controls
        self.height_label_rect = pygame.Rect(20, 350, panel_width - 40, 20)
        self.height_increase_rect = pygame.Rect(20, 380, (panel_width - 60) // 2, 30)
        self.height_decrease_rect = pygame.Rect(40 + (panel_width - 60) // 2, 380, (panel_width - 60) // 2, 30)

        # Sea Level controls
        self.sea_level_label_rect = pygame.Rect(20, 430, panel_width - 40, 20)
        self.sea_level_increase_rect = pygame.Rect(20, 460, (panel_width - 60) // 2, 30)
        self.sea_level_decrease_rect = pygame.Rect(40 + (panel_width - 60) // 2, 460, (panel_width - 60) // 2, 30)

        # Max Altitude controls
        self.max_altitude_label_rect = pygame.Rect(20, 510, panel_width - 40, 20)
        self.max_altitude_increase_rect = pygame.Rect(20, 540, (panel_width - 60) // 2, 30)
        self.max_altitude_decrease_rect = pygame.Rect(40 + (panel_width - 60) // 2, 540, (panel_width - 60) // 2, 30)

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
        elif self.width_increase_rect.collidepoint(event.pos):
            self.config['width'] += 1
            return 'config_changed'
        elif self.width_decrease_rect.collidepoint(event.pos):
            if self.config['width'] > 1:
                self.config['width'] -= 1
                return 'config_changed'
        elif self.height_increase_rect.collidepoint(event.pos):
            self.config['height'] += 1
            return 'config_changed'
        elif self.height_decrease_rect.collidepoint(event.pos):
            if self.config['height'] > 1:
                self.config['height'] -= 1
                return 'config_changed'
        elif self.sea_level_increase_rect.collidepoint(event.pos):
            self.config['sea_level'] += 1000
            # Ensure sea level does not exceed max altitude
            if self.config['sea_level'] > self.config['max_altitude']:
                self.config['sea_level'] = self.config['max_altitude']
            return 'config_changed'
        elif self.sea_level_decrease_rect.collidepoint(event.pos):
            if self.config['sea_level'] >= 1000:
                self.config['sea_level'] -= 1000
                return 'config_changed'
        elif self.max_altitude_increase_rect.collidepoint(event.pos):
            self.config['max_altitude'] += 1000
            return 'config_changed'
        elif self.max_altitude_decrease_rect.collidepoint(event.pos):
            if self.config['max_altitude'] > 1000:
                self.config['max_altitude'] -= 1000
                # Ensure sea level does not exceed max altitude
                if self.config['sea_level'] > self.config['max_altitude']:
                    self.config['sea_level'] = self.config['max_altitude']
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

        # Draw number of plates label and buttons
        n_selected_label = font.render("Number of Plates:", True, (255, 255, 255))
        screen.blit(n_selected_label, self.n_selected_label_rect.topleft)
        # Increase button
        pygame.draw.rect(screen, (70, 70, 70), self.n_selected_increase_rect)
        inc_text = font.render("+", True, (255, 255, 255))
        inc_text_rect = inc_text.get_rect(center=self.n_selected_increase_rect.center)
        screen.blit(inc_text, inc_text_rect)
        # Decrease button
        pygame.draw.rect(screen, (70, 70, 70), self.n_selected_decrease_rect)
        dec_text = font.render("-", True, (255, 255, 255))
        dec_text_rect = dec_text.get_rect(center=self.n_selected_decrease_rect.center)
        screen.blit(dec_text, dec_text_rect)
        # Display current number of plates value
        n_selected_value_text = font.render(str(self.config['startpoint_count']), True, (255, 255, 255))
        n_selected_value_rect = n_selected_value_text.get_rect(center=(self.panel_width // 2, 235))
        screen.blit(n_selected_value_text, n_selected_value_rect)

        # Draw width label and buttons
        width_label = font.render("Width:", True, (255, 255, 255))
        screen.blit(width_label, self.width_label_rect.topleft)
        # Increase button
        pygame.draw.rect(screen, (70, 70, 70), self.width_increase_rect)
        inc_text = font.render("+", True, (255, 255, 255))
        inc_text_rect = inc_text.get_rect(center=self.width_increase_rect.center)
        screen.blit(inc_text, inc_text_rect)
        # Decrease button
        pygame.draw.rect(screen, (70, 70, 70), self.width_decrease_rect)
        dec_text = font.render("-", True, (255, 255, 255))
        dec_text_rect = dec_text.get_rect(center=self.width_decrease_rect.center)
        screen.blit(dec_text, dec_text_rect)
        # Display current width value
        width_value_text = font.render(str(self.config['width']), True, (255, 255, 255))
        width_value_rect = width_value_text.get_rect(center=(self.panel_width // 2, 315))
        screen.blit(width_value_text, width_value_rect)

        # Draw height label and buttons
        height_label = font.render("Height:", True, (255, 255, 255))
        screen.blit(height_label, self.height_label_rect.topleft)
        # Increase button
        pygame.draw.rect(screen, (70, 70, 70), self.height_increase_rect)
        inc_text = font.render("+", True, (255, 255, 255))
        inc_text_rect = inc_text.get_rect(center=self.height_increase_rect.center)
        screen.blit(inc_text, inc_text_rect)
        # Decrease button
        pygame.draw.rect(screen, (70, 70, 70), self.height_decrease_rect)
        dec_text = font.render("-", True, (255, 255, 255))
        dec_text_rect = dec_text.get_rect(center=self.height_decrease_rect.center)
        screen.blit(dec_text, dec_text_rect)
        # Display current height value
        height_value_text = font.render(str(self.config['height']), True, (255, 255, 255))
        height_value_rect = height_value_text.get_rect(center=(self.panel_width // 2, 395))
        screen.blit(height_value_text, height_value_rect)

        # Draw sea level label and buttons
        sea_level_label = font.render("Sea Level:", True, (255, 255, 255))
        screen.blit(sea_level_label, self.sea_level_label_rect.topleft)
        # Increase button
        pygame.draw.rect(screen, (70, 70, 70), self.sea_level_increase_rect)
        inc_text = font.render("+", True, (255, 255, 255))
        inc_text_rect = inc_text.get_rect(center=self.sea_level_increase_rect.center)
        screen.blit(inc_text, inc_text_rect)
        # Decrease button
        pygame.draw.rect(screen, (70, 70, 70), self.sea_level_decrease_rect)
        dec_text = font.render("-", True, (255, 255, 255))
        dec_text_rect = dec_text.get_rect(center=self.sea_level_decrease_rect.center)
        screen.blit(dec_text, dec_text_rect)
        # Display current sea level value
        sea_level_value_text = font.render(str(self.config['sea_level']), True, (255, 255, 255))
        sea_level_value_rect = sea_level_value_text.get_rect(center=(self.panel_width // 2, 475))
        screen.blit(sea_level_value_text, sea_level_value_rect)

        # Draw max altitude label and buttons
        max_altitude_label = font.render("Max Altitude:", True, (255, 255, 255))
        screen.blit(max_altitude_label, self.max_altitude_label_rect.topleft)
        # Increase button
        pygame.draw.rect(screen, (70, 70, 70), self.max_altitude_increase_rect)
        inc_text = font.render("+", True, (255, 255, 255))
        inc_text_rect = inc_text.get_rect(center=self.max_altitude_increase_rect.center)
        screen.blit(inc_text, inc_text_rect)
        # Decrease button
        pygame.draw.rect(screen, (70, 70, 70), self.max_altitude_decrease_rect)
        dec_text = font.render("-", True, (255, 255, 255))
        dec_text_rect = dec_text.get_rect(center=self.max_altitude_decrease_rect.center)
        screen.blit(dec_text, dec_text_rect)
        # Display current max altitude value
        max_altitude_value_text = font.render(str(self.config['max_altitude']), True, (255, 255, 255))
        max_altitude_value_rect = max_altitude_value_text.get_rect(center=(self.panel_width // 2, 555))
        screen.blit(max_altitude_value_text, max_altitude_value_rect)
