# Import libraries
import pygame
from hex_board_generator import hex_grid_map
from game_functions import handle_zoom
# Initialize pygame
pygame.init()

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
COLOR_A = (255, 0, 0)  # Replace colora with this
COLOR_B = (0, 255, 0)  # Replace colrb with this

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Font for displaying zoom level
pygame.font.init()
font = pygame.font.SysFont('Arial', 24)

def draw_zoom_label(zoom_level):
    """Display the current zoom level on the screen"""
    text_surface = font.render(f"Zoom: {zoom_level}x", True, BLACK)
    screen.blit(text_surface, (10, 10))  # Position the zoom label at the top-left

def main():
    """Main game loop"""
    running = True
    clock = pygame.time.Clock()

    MAP_HEIGHT = 20
    MAP_WIDTH = 20
    size = 30  # Size of the hexagon
    outline = BLACK
    fillcolor = COLOR_B
    zoom_level = 1  # Track the zoom level

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Handle zooming
            new_size = handle_zoom(event, size)
            if new_size != size:
                size = new_size
                zoom_level = size / 30  # Assuming 30 is the default zoom (1x)
        # Fill the background
        screen.fill(WHITE)

        # Draw the hex grid
        hex_grid_map(MAP_WIDTH, MAP_HEIGHT, size, outline, fillcolor, screen)
        draw_zoom_label(zoom_level) # Draw the zoom label
        # Update the screen
        pygame.display.flip()

        # Cap the frame rate
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()
