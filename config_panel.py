import pygame

# Define base UIElement class
class UIElement:
    def __init__(self):
        pass

    def draw(self, screen, position, width, height):
        pass

    def handle_event(self, event, position):
        pass

# Label UIElement
class Label(UIElement):
    def __init__(self, text, font, color=(255, 255, 255)):
        super().__init__()
        self.text = text
        self.font = font
        self.color = color
        self.rendered_text = self.font.render(self.text, True, self.color)

    def draw(self, screen, position, width, height):
        draw_position = (position[0], position[1])
        screen.blit(self.rendered_text, draw_position)

    def handle_event(self, event, position):
        return False

# Button UIElement
class Button(UIElement):
    def __init__(self, text, font, callback):
        super().__init__()
        self.text = text
        self.font = font
        self.callback = callback
        self.color = (70, 70, 70)
        self.text_color = (255, 255, 255)
        self.hovered = False
        self.rect = pygame.Rect(0, 0, 0, 0)  # Will be set in draw

    def draw(self, screen, position, width, height):
        self.rect = pygame.Rect(position[0], position[1], width, height)
        
        # Change color on hover
        current_color = (100, 100, 100) if self.hovered else self.color
        pygame.draw.rect(screen, current_color, self.rect)
        rendered_text = self.font.render(self.text, True, self.text_color)
        text_rect = rendered_text.get_rect(center=(position[0] + width // 2, position[1] + height // 2))
        screen.blit(rendered_text, text_rect)

    def handle_event(self, event, position):
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            self.hovered = self.rect.collidepoint(mouse_pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False

# InputField UIElement
class InputField(UIElement):
    def __init__(self, config, field_info, font):
        super().__init__()
        self.config = config
        self.field_info = field_info
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
        self.rect = pygame.Rect(0, 0, 0, 0)  # Will be set in draw

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

    def draw(self, screen, position, width, height):
        self.rect = pygame.Rect(position[0], position[1], width, height)
        
        # Draw input box
        pygame.draw.rect(screen, self.color, pygame.Rect(position[0], position[1], width, height))
        text_surface = self.font.render(self.text, True, self.text_color)
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))
        
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

    def handle_event(self, event, position):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Adjust mouse position based on scroll offset
            adjusted_pos = (event.pos[0], event.pos[1])
            if self.rect.collidepoint(adjusted_pos):
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
    def __init__(self, config, field_info, font):
        super().__init__()
        self.config = config
        self.field_info = field_info
        self.font = font
        self.checked = self.get_config_value()
        self.box_color = (70, 70, 70)
        self.check_color = (255, 255, 255)
        self.label = self.field_info['name']
        self.text_surface = self.font.render(self.label, True, (255, 255, 255))
        self.rect = pygame.Rect(0, 0, 0, 0)  # Will be set in draw

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

    def draw(self, screen, position, width, height):
        spacing = 10
        self.rect = pygame.Rect(position[0], position[1], width, height)
        pygame.draw.rect(screen, self.box_color, self.rect)
        if self.checked:
            pygame.draw.rect(screen, self.check_color, self.rect.inflate(-4, -4))
        screen.blit(self.text_surface, (self.rect.right + spacing, self.rect.y))

    def handle_event(self, event, position):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Adjust mouse position based on scroll offset
            adjusted_pos = (event.pos[0], event.pos[1])
            if self.rect.collidepoint(adjusted_pos):
                self.checked = not self.checked
                self.set_config_value(self.checked)
                return True
        return False

# Dropdown UIElement
class Dropdown(UIElement):
    def __init__(self, config, field_info, font):
        super().__init__()
        self.config = config
        self.field_info = field_info
        self.font = font
        self.active = False
        self.color_inactive = (70, 70, 70)
        self.color_active = (100, 100, 100)
        self.color = self.color_inactive
        self.text_color = (255, 255, 255)
        self.options = field_info['options']
        self.selected_option = self.get_config_value()
        self.expanded = False
        self.option_rects = []

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

    def draw(self, screen, position, width, height):
        # Define fixed width and height
        dropdown_width = 200
        dropdown_height = 30
        self.rect = pygame.Rect(position[0], position[1], width, height)
        
        # Draw the main dropdown box
        pygame.draw.rect(screen, self.color, pygame.Rect(position[0], position[1], width, height))
        text_surface = self.font.render(str(self.selected_option), True, self.text_color)
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))
        
        # Draw dropdown arrow
        pygame.draw.polygon(screen, self.text_color, [
            (self.rect.right - 15, self.rect.y + 10),
            (self.rect.right - 5, self.rect.y + 10),
            (self.rect.right - 10, self.rect.y + 15)
        ])  # Draw a small arrow indicating dropdown

        if self.expanded:
            # Draw each option
            self.option_rects = []
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * dropdown_height, dropdown_width, dropdown_height)
                pygame.draw.rect(screen, self.color_inactive, option_rect)
                option_text = self.font.render(option, True, self.text_color)
                screen.blit(option_text, (option_rect.x + 5, option_rect.y + 5))
                self.option_rects.append((option_rect, option))

    def handle_event(self, event, position):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Adjust mouse position based on scroll offset
            adjusted_pos = (event.pos[0], event.pos[1])
            if self.rect.collidepoint(adjusted_pos):
                self.expanded = not self.expanded
                return True
            elif self.expanded:
                for option_rect, option in self.option_rects:
                    if option_rect.collidepoint(adjusted_pos):
                        self.selected_option = option
                        self.set_config_value(option)
                        self.expanded = False
                        return True
                # Clicked outside options
                self.expanded = False
        return False

# ConfigPanel with scrolling
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
        
        # Scroll management
        self.scroll_offset = 0
        self.max_scroll = 0

    def build_ui_elements(self):
        self.ui_elements = []

        # Regenerate Button
        regenerate_button = Button(
            text="Regenerate",
            font=self.font,
            callback=self.regenerate_world
        )
        self.ui_elements.append(regenerate_button)

        # Scroll up indicator
        self.scroll_up_label = Label(
            text="Scroll up for more...",
            font=self.font,
            color=(255, 255, 255)
        )

        # Scroll down indicator
        self.scroll_down_label = Label(
            text="Scroll down for more...",
            font=self.font,
            color=(255, 255, 255)
        )

        # Build UI elements based on ui_fields
        self.add_ui_fields(self.ui_fields, parent_keys=[])

    def add_ui_fields(self, fields, parent_keys):
        for key, field in fields.items():
            if isinstance(field, dict) and 'type' in field:
                # Prepare field info
                field_info = field.copy()
                field_info['config_path'] = parent_keys + [field_info['id']]
                
                # Label
                label = Label(
                    text=field_info['name'],
                    font=self.font
                )
                self.ui_elements.append(label)
                
                # Create appropriate input element
                if field_info['type'] == 'select':
                    input_element = Dropdown(
                        config=self.config,
                        field_info=field_info,
                        font=self.font
                    )
                elif field_info['type'] in [int, float]:
                    input_element = InputField(
                        config=self.config,
                        field_info=field_info,
                        font=self.font
                    )
                elif field_info['type'] == bool:
                    input_element = Checkbox(
                        config=self.config,
                        field_info=field_info,
                        font=self.font
                    )
                else:
                    continue  # Unsupported type

                self.ui_elements.append(input_element)
            elif isinstance(field, dict):
                # Nested fields, recursively add
                self.add_ui_fields(field, parent_keys + [key])

    def regenerate_world(self):
        self.action_callback('regen')

    def process_event(self, event):
        # Handle MOUSEWHEEL events for scrolling
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_offset -= event.y * 20  # Adjust scroll speed
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
            return
    
        # Ignore MOUSEBUTTONDOWN events for scroll wheel (buttons 4 and 5)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            # Optionally, you can handle scrolling here if you prefer
            # For example:
            # if event.button == 4:
            #     self.scroll_offset -= 20
            # elif event.button == 5:
            #     self.scroll_offset += 20
            # self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
            return  # Do not propagate these events to UI elements
    
        # Adjust event positions based on scroll_offset for relevant events
        if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
            adjusted_pos = list(event.pos)
            adjusted_pos[1] += self.scroll_offset
            # Create an adjusted event with the modified position
            event_attrs = {'pos': tuple(adjusted_pos)}
            if hasattr(event, 'button'):
                event_attrs['button'] = event.button
            if hasattr(event, 'rel'):
                event_attrs['rel'] = event.rel
            if hasattr(event, 'buttons'):
                event_attrs['buttons'] = event.buttons
            adjusted_event = pygame.event.Event(event.type, event_attrs)
        else:
            adjusted_event = event  # Other events remain unchanged
    
        # Propagate the adjusted event to UI elements
        for element in self.ui_elements:
            if element.handle_event(adjusted_event, (0, 0)):
                # Rebuild UI if necessary
                if isinstance(element, Dropdown):
                    if element.field_info['id'] in ['base_method', 'altitude_gen_method']:
                        self.build_ui_elements()
                        self.calculate_scroll()
                return

    def calculate_scroll(self):
        # Calculate total content height
        total_height = 20  # Initial padding
        element_spacing = 10
        for element in self.ui_elements:
            if isinstance(element, Label):
                total_height += element.rendered_text.get_height() + element_spacing
            elif isinstance(element, Button):
                total_height += 40  # Button height + spacing
            elif isinstance(element, InputField):
                total_height += 40  # Input field height + spacing
            elif isinstance(element, Checkbox):
                total_height += 30  # Checkbox height + spacing
            elif isinstance(element, Dropdown):
                # If expanded, add space for options
                total_height += 40  # Dropdown height + spacing
                if element.expanded:
                    total_height += len(element.options) * 30  # Assuming each option adds 30px
        self.max_scroll = max(0, total_height - self.panel_rect.height + 20)  # Additional padding
        self.scroll_offset = min(self.scroll_offset, self.max_scroll)

    def draw(self, screen):
        # Draw panel background
        pygame.draw.rect(screen, self.background_color, self.panel_rect)

        # Create a clipping area for the panel
        clip_rect = self.panel_rect.copy()
        screen.set_clip(clip_rect)

        # Starting position for UI elements
        x = 20
        y = 20
        element_spacing = 20
        element_height = 30

        # Draw Regenerate button
        self.ui_elements[0].draw(screen, (x, y - self.scroll_offset), self.panel_rect.width, element_height)
        y += 40

        # Draw scroll up indicator if needed
        if self.scroll_offset > 0:
            self.scroll_up_label.draw(screen, (x, y - self.scroll_offset), self.panel_rect.width, element_height)
            y += element_height + element_spacing

        # Draw all other UI elements
        for element in self.ui_elements[1:]:
            element.draw(screen, (x, y - self.scroll_offset), self.panel_rect.width, element_height)
            # Update y based on element type
            if isinstance(element, Label):
                y += element.rendered_text.get_height() + element_spacing
            elif isinstance(element, Button):
                y += 40  # Button height + spacing
            elif isinstance(element, InputField):
                y += 40  # Input field height + spacing
            elif isinstance(element, Checkbox):
                y += 30  # Checkbox height + spacing
            elif isinstance(element, Dropdown):
                y += 40  # Dropdown height + spacing
                if element.expanded:
                    y += len(element.options) * 30  # Assuming each option adds 30px

        # Draw scroll down indicator if needed
        if y - self.scroll_offset > self.panel_rect.height:
            self.scroll_down_label.draw(screen, (x, self.panel_rect.height - element_height), self.panel_rect.width, element_height)

        # Reset clipping
        screen.set_clip(None)

    def update(self):
        self.calculate_scroll()