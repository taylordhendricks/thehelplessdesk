import pygame
import sys

def main():
    # Initialize Pygame
    pygame.init()

    # Set up the game window
    screen_width = 800
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Simple Side Scroller")

    # Define clock for controlling the frame rate
    clock = pygame.time.Clock()

    # Define rectangle properties
    rect_color = (255, 0, 0)    # Red
    rect_width = 50
    rect_height = 50
    rect_x = 50
    rect_y = screen_height - rect_height - 50  # Slightly above the bottom
    rect_speed = 5

    # Main game loop
    running = True
    while running:
        # Limit the frame rate to 60 FPS
        clock.tick(60)

        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Get key presses
        keys = pygame.key.get_pressed()

        # Move left
        if keys[pygame.K_LEFT]:
            rect_x -= rect_speed

        # Move right
        if keys[pygame.K_RIGHT]:
            rect_x += rect_speed

        # (Optional) Prevent the rectangle from going off-screen
        if rect_x < 0:
            rect_x = 0
        elif rect_x + rect_width > screen_width:
            rect_x = screen_width - rect_width

        # Clear the screen (fill with white)
        screen.fill((255, 255, 255))

        # Draw the rectangle
        pygame.draw.rect(screen, rect_color, (rect_x, rect_y, rect_width, rect_height))

        # Update the display
        pygame.display.flip()

    # Quit Pygame
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()