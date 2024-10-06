import pygame

class TabPanel:
    def __init__(self, labels, panel_width, tab_button_width, tab_button_height, tab_padding, selected_color=(100,100,100), base_color=(50,50,50), background_color=(255, 255, 255)):
        self.background_color = background_color
        self.base_color = base_color
        self.selected_color = selected_color
        self.tab_buttons = []

        for idx, label in enumerate(labels):
            # Position tabs with padding from the top and horizontally aligned
            button_rect = pygame.Rect(
                panel_width + idx * (tab_button_width + tab_padding), 
                (tab_padding) // 2,
                tab_button_width, 
                tab_button_height
            )
            self.tab_buttons.append((label, button_rect))

    def process_event(self, event):
        # check if we clicked a tab button, return its label if we did
        for label, button_rect in self.tab_buttons:
            if button_rect.collidepoint(event.pos):
                return label
        return None


    def draw(self, screen, font, selected_label):
        for label, button_rect in self.tab_buttons:
            color = self.selected_color if label == selected_label else self.base_color
            pygame.draw.rect(screen, color, button_rect)
            text_surface = font.render(label, True, self.background_color)
            text_rect = text_surface.get_rect(center=button_rect.center)
            screen.blit(text_surface, text_rect)