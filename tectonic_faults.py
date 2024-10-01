# Import libraries
import pygame
from hex_board_generator import HexGrid, HexTile, FaultGenerator
from control_functions import handle_zoom
# Initialize pygame
pygame.init()

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
COLOR_A = (255, 0, 0)  
COLOR_B = (0, 255, 0) 
COLOR_C = (0, 255, 0)   

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
    
    clock = pygame.time.Clock()

    MAP_HEIGHT = 50
    MAP_WIDTH = 50
    FAULT_LINES = 2
    size = 30  # Size of the hexagon
    outline = BLACK
    fillcolor = COLOR_B
    
    # Camera and zoom settings
    camera_offset = [0, 0]
    zoom_factor = 1.0

    # Generate the base hex grid (without drawing)
    hex_grid = HexGrid(MAP_WIDTH, MAP_HEIGHT, size)
    fault_generator = FaultGenerator(MAP_WIDTH, MAP_HEIGHT, num_faults=FAULT_LINES, seed=42, noise_prob=0.2)
    fault_tiles = fault_generator.generate_faults()
    
     # Variables for panning
    is_panning = False
    pan_start_pos = (0, 0)
    pan_start_offset = [0, 0]
    zoom_center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)  # Center of the screen

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Handle zooming with mouse wheel
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Mouse wheel up to zoom in
                    zoom_factor *= 1.1
                elif event.button == 5:  # Mouse wheel down to zoom out
                    zoom_factor /= 1.1
                elif event.button == 1:  # Left mouse button to start panning
                    is_panning = True
                    pan_start_pos = event.pos
                    pan_start_offset = camera_offset.copy()

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button to stop panning
                    is_panning = False

            elif event.type == pygame.MOUSEMOTION:
                if is_panning:
                    dx = event.pos[0] - pan_start_pos[0]
                    dy = event.pos[1] - pan_start_pos[1]
                    camera_offset = [
                        pan_start_offset[0] + dx / zoom_factor,
                        pan_start_offset[1] + dy / zoom_factor
                    ]


        # Fill the background
        screen.fill(WHITE)
        # Compute font size based on zoom_factor to maintain readability
        base_font_size = 14  # Base size for zoom_factor = 1.0
        font_size = max(int(base_font_size * zoom_factor), 8)  # Minimum font size
        font = pygame.font.SysFont(None, font_size)
        # Draw the hex grid
        hex_grid.draw(screen, fault_tiles, zoom_factor, zoom_center, camera_offset, font)

        draw_zoom_label(zoom_factor) # Draw the zoom label
        # Update the screen
        pygame.display.flip()

        # Cap the frame rate
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()
