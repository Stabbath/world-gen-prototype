import pygame

# Define base UIElement class
class UIElement:
    def __init__(self):
        pass

    def draw(self, screen):
        pass

    def handle_event(self, event):
        pass

# Label UIElement
class Label(UIElement):
    def __init__(self, text, position, font, color=(255, 255, 255)):
        super().__init__()
        self.text = text
        self.position = position
        self.font = font
        self.color = color
        self.rendered_text = self.font.render(self.text, True, self.color)

    def draw(self, screen):
        screen.blit(self.rendered_text, self.position)

# Button UIElement
class Button(UIElement):
    def __init__(self, text, rect, font, callback):
        super().__init__()
        self.text = text
        self.rect = pygame.Rect(rect)
        self.font = font
        self.callback = callback
        self.color = (70, 70, 70)
        self.text_color = (255, 255, 255)
        self.hovered = False

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        rendered_text = self.font.render(self.text, True, self.text_color)
        text_rect = rendered_text.get_rect(center=self.rect.center)
        screen.blit(rendered_text, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False

# InputField UIElement
class InputField(UIElement):
    def __init__(self, config, field_info, position, size, font):
        super().__init__()
        self.config = config
        self.field_info = field_info
        self.rect = pygame.Rect(position, size)
        self.font = font
        self.active = False
        self.text = str(self.get_config_value())
        self.color_inactive = (70, 70, 70)
        self.color_active = (100, 100, 100)
        self.color = self.color_inactive
        self.text_color = (255, 255, 255)
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_interval = 500  # milliseconds

    def get_config_value(self):
        keys = self.field_info['config_path']
        value = self.config
        for key in keys:
            value = value[key]
        return value

    def set_config_value(self, value):
        keys = self.field_info['config_path']
        config_section = self.config
        for key in keys[:-1]:
            config_section = config_section[key]
        config_section[keys[-1]] = value

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        text_surface = self.font.render(self.text, True, self.text_color)
        screen.blit(text_surface, (self.rect.x+5, self.rect.y+5))
        # Handle cursor blinking
        if self.active:
            current_time = pygame.time.get_ticks()
            if current_time - self.cursor_timer > self.cursor_interval:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = current_time
            if self.cursor_visible:
                cursor_x = self.rect.x + 5 + text_surface.get_width()
                cursor_y = self.rect.y + 5
                pygame.draw.rect(screen, self.text_color, (cursor_x, cursor_y, 2, text_surface.get_height()))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
                self.color = self.color_active if self.active else self.color_inactive
            else:
                self.active = False
                self.color = self.color_inactive
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    # Apply the filter function if it exists
                    try:
                        new_value = self.field_info['type'](self.text)
                        if 'filter' in self.field_info:
                            new_value = self.field_info['filter'](new_value, self.get_config_value())
                        self.set_config_value(new_value)
                    except ValueError:
                        pass  # Ignore invalid input
                    self.active = False
                    self.color = self.color_inactive
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                return True
        return False

# Checkbox UIElement
class Checkbox(UIElement):
    def __init__(self, config, field_info, position, size, font):
        super().__init__()
        self.config = config
        self.field_info = field_info
        self.rect = pygame.Rect(position, size)
        self.font = font
        self.checked = self.get_config_value()
        self.box_color = (70, 70, 70)
        self.check_color = (255, 255, 255)
        self.label = self.field_info['name']
        self.text_surface = self.font.render(self.label, True, (255, 255, 255))

    def get_config_value(self):
        keys = self.field_info['config_path']
        value = self.config
        for key in keys:
            value = value[key]
        return value

    def set_config_value(self, value):
        keys = self.field_info['config_path']
        config_section = self.config
        for key in keys[:-1]:
            config_section = config_section[key]
        config_section[keys[-1]] = value

    def draw(self, screen):
        pygame.draw.rect(screen, self.box_color, self.rect)
        if self.checked:
            pygame.draw.rect(screen, self.check_color, self.rect.inflate(-10, -10))
        screen.blit(self.text_surface, (self.rect.right + 10, self.rect.y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.checked = not self.checked
                self.set_config_value(self.checked)
                return True
        return False

# Dropdown UIElement
class Dropdown(UIElement):
    def __init__(self, config, field_info, position, size, font):
        super().__init__()
        self.config = config
        self.field_info = field_info
        self.rect = pygame.Rect(position, size)
        self.font = font
        self.active = False
        self.color_inactive = (70, 70, 70)
        self.color_active = (100, 100, 100)
        self.color = self.color_inactive
        self.text_color = (255, 255, 255)
        self.options = field_info['options']
        self.selected_option = self.get_config_value()
        self.expanded = False
        self.option_rects = []  # Initialize here

    def get_config_value(self):
        keys = self.field_info['config_path']
        value = self.config
        for key in keys:
            value = value[key]
        return value

    def set_config_value(self, value):
        keys = self.field_info['config_path']
        config_section = self.config
        for key in keys[:-1]:
            config_section = config_section[key]
        config_section[keys[-1]] = value

    def draw(self, screen):
        # Draw the main dropdown box
        pygame.draw.rect(screen, self.color, self.rect)
        text_surface = self.font.render(str(self.selected_option), True, self.text_color)
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.polygon(screen, self.text_color, [
            (self.rect.right - 15, self.rect.y + 10),
            (self.rect.right - 5, self.rect.y + 10),
            (self.rect.right - 10, self.rect.y + 15)
        ])  # Draw a small arrow indicating dropdown

        if self.expanded:
            # Draw each option
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                pygame.draw.rect(screen, self.color_inactive, option_rect)
                option_text = self.font.render(option, True, self.text_color)
                screen.blit(option_text, (option_rect.x + 5, option_rect.y + 5))
                self.option_rects.append((option_rect, option))
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.expanded = not self.expanded
                return True
            elif self.expanded:
                for option_rect, option in self.option_rects:
                    if option_rect.collidepoint(event.pos):
                        self.selected_option = option
                        self.set_config_value(option)
                        self.expanded = False
                        self.option_rects.clear()  # Clear after selection
                        return True
                self.expanded = False
                self.option_rects.clear()  # Clear if clicked outside
        return False


class ConfigPanel:
    def __init__(self, panel_width, screen_height, config, ui_fields, font, action_callback, background_color=(30, 30, 30)):
        self.panel_rect = pygame.Rect(0, 0, panel_width, screen_height)
        self.background_color = background_color
        self.panel_width = panel_width
        self.config = config
        self.ui_fields = ui_fields
        self.font = font
        self.action_callback = action_callback
        self.ui_elements = []
        self.build_ui_elements()

    def build_ui_elements(self):
        self.ui_elements = []

        # Starting position for UI elements
        x = 20
        y = 60
        element_spacing = 40
        input_width = self.panel_width - 40
        input_height = 30

        # Regenerate Button
        regenerate_button = Button(
            text="Regenerate",
            rect=(x, y, input_width, input_height),
            font=self.font,
            callback=self.regenerate_world
        )
        self.ui_elements.append(regenerate_button)
        y += element_spacing + input_height

        # Build UI elements based on ui_fields
        self.add_ui_fields(self.ui_fields, position=(x, y), parent_keys=[])

    def add_ui_fields(self, fields, position, parent_keys):
        x, y = position
        element_spacing = 10  # Reduced spacing between label and input
        input_spacing = 40    # Spacing between input elements
        input_width = self.panel_width - 40
        input_height = 30
    
        for key, field in fields.items():
            if isinstance(field, dict) and 'type' in field:
                # Prepare field info
                field_info = field.copy()
                field_info['config_path'] = parent_keys + [field_info['id']]
                
                # Label
                label = Label(
                    text=field_info['name'],
                    position=(x, y),
                    font=self.font
                )
                self.ui_elements.append(label)
                
                # Get label height to adjust y position
                label_height = label.rendered_text.get_height()
                y += label_height + element_spacing
    
                # Create appropriate input element
                if field_info['type'] == 'select':
                    input_element = Dropdown(
                        config=self.config,
                        field_info=field_info,
                        position=(x, y),
                        size=(input_width, input_height),
                        font=self.font
                    )
                elif field_info['type'] in [int, float]:
                    input_element = InputField(
                        config=self.config,
                        field_info=field_info,
                        position=(x, y),
                        size=(input_width, input_height),
                        font=self.font
                    )
                elif field_info['type'] == bool:
                    input_element = Checkbox(
                        config=self.config,
                        field_info=field_info,
                        position=(x, y),
                        size=(input_height, input_height),
                        font=self.font
                    )
                else:
                    continue  # Unsupported type
    
                self.ui_elements.append(input_element)
                y += input_spacing
            elif isinstance(field, dict):
                # Nested fields, check if they should be displayed
                # For base_method and other conditional fields
                display = True
                if parent_keys:
                    # Check if parent field value matches
                    config_value = self.config
                    for key in parent_keys:
                        config_value = config_value[key]
                    if parent_keys[-1] == 'base_method' and config_value != key:
                        display = False
                    elif parent_keys[-1] == 'altitude_gen_method' and config_value != key:
                        display = False

                if display:
                    # Add a separator label
                    separator_label = Label(
                        text=field.get('name', key).upper(),
                        position=(x, y),
                        font=self.font
                    )
                    self.ui_elements.append(separator_label)
                    y += element_spacing // 2
                    # Recursively add nested fields
                    self.add_ui_fields(field, (x, y), parent_keys + [key])
                    y += element_spacing
        # Update the panel height if necessary
        self.panel_rect.height = max(self.panel_rect.height, y + 20)

    def regenerate_world(self):
        self.action_callback('regen')

    def process_event(self, event):
        for element in self.ui_elements:
            if element.handle_event(event):
                # If 'base_method' or other method fields change, rebuild UI
                if isinstance(element, Dropdown):
                    if element.field_info['id'] == 'base_method' or element.field_info['id'] == 'altitude_gen_method':
                        self.build_ui_elements()
                return True

    def draw(self, screen):
        pygame.draw.rect(screen, self.background_color, self.panel_rect)
        
        # First draw all UI elements except expanded dropdowns
        for element in self.ui_elements:
            if isinstance(element, Dropdown) and element.expanded:
                continue  # Skip expanded dropdowns for now
            element.draw(screen)
        
        # Then draw expanded dropdowns on top
        for element in self.ui_elements:
            if isinstance(element, Dropdown) and element.expanded:
                element.draw(screen)
