import pygame
import time
import random

pygame.init()

# Colors
white = (255, 255, 255)
yellow = (255, 255, 102)
black = (0, 0, 0)
red = (213, 50, 80)
green = (0, 255, 0)
blue = (50, 153, 213)

# Screen dimensions
width = 600
height = 400
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Snake Game')

clock = pygame.time.Clock()
snake_block = 10
snake_speed = 15

# Load the sprite images
head_image = pygame.image.load(r"python\games\Snake\Snakey\snake_head.png").convert_alpha()
body_image = pygame.image.load(r"python\games\Snake\Snakey\snake_body.png").convert_alpha()
tail_image = pygame.image.load(r"python\games\Snake\Snakey\snake_tail.png").convert_alpha()

# Scale the images to match the snake block size
head_image = pygame.transform.scale(head_image, (snake_block, snake_block))
body_image = pygame.transform.scale(body_image, (snake_block, snake_block))
tail_image = pygame.transform.scale(tail_image, (snake_block, snake_block))

font_style = pygame.font.SysFont("bahnschrift", 25)
score_font = pygame.font.SysFont("comicsansms", 35)

def main_menu():
    menu_running = True
    selected_index = 0  # Track which menu item is selected
    options = ["New Game", "HiScores", "Settings", "Exit"]
    option_positions = []

    while menu_running:
        screen.fill(blue)

        # Title or Game Image
        title_font = pygame.font.SysFont("comicsansms", 50)
        title = title_font.render("Snake Game", True, yellow)
        screen.blit(title, [width / 2 - title.get_width() / 2, 50])

        # Menu Options
        options_font = pygame.font.SysFont("bahnschrift", 35)
        option_positions = []  # Reset positions for hit detection

        for idx, option in enumerate(options):
            # Check if the current option is hovered/selected
            is_selected = idx == selected_index
            color = white if not is_selected else yellow
            scale = 1.0 if not is_selected else 1.2

            # Render option with scaling
            option_surface = options_font.render(option, True, color)
            option_rect = option_surface.get_rect(center=(width // 2, 150 + idx * 50))
            scaled_surface = pygame.transform.scale(option_surface, (int(option_rect.width * scale), int(option_rect.height * scale)))

            # Store positions for hit detection
            option_positions.append(option_rect)

            # Draw the option
            screen.blit(scaled_surface, scaled_surface.get_rect(center=option_rect.center))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEMOTION:
                # Highlight the option the mouse hovers over
                mouse_pos = pygame.mouse.get_pos()
                for idx, rect in enumerate(option_positions):
                    if rect.collidepoint(mouse_pos):
                        selected_index = idx

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
                if selected_index == 0:  # New Game
                    return "new_game"
                elif selected_index == 1:  # HiScores
                    return "hi_scores"
                elif selected_index == 2:  # Settings
                    return "settings"
                elif selected_index == 3:  # Exit
                    pygame.quit()
                    quit()

            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_UP, pygame.K_w]:  # Move selection up
                    selected_index = (selected_index - 1) % len(options)
                elif event.key in [pygame.K_DOWN, pygame.K_s]:  # Move selection down
                    selected_index = (selected_index + 1) % len(options)
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:  # Select the option
                    if selected_index == 0:  # New Game
                        return "new_game"
                    elif selected_index == 1:  # HiScores
                        return "hi_scores"
                    elif selected_index == 2:  # Settings
                        return "settings"
                    elif selected_index == 3:  # Exit
                        pygame.quit()
                        quit()

def our_snake(snake_list, x1_change, y1_change):
    for i, segment in enumerate(snake_list[::-1]):
        if i == 0:  # Head (last in original list)
            if len(snake_list) == 1:  # Single-segment snake
                if x1_change > 0:  # Moving right
                    rotated_head = pygame.transform.rotate(head_image, 180)
                elif x1_change < 0:  # Moving left
                    rotated_head = pygame.transform.rotate(head_image, 0)
                elif y1_change > 0:  # Moving down
                    rotated_head = pygame.transform.rotate(head_image, 90)
                elif y1_change < 0:  # Moving up
                    rotated_head = pygame.transform.rotate(head_image, 270)
                else:  # Default orientation if no movement yet
                    rotated_head = head_image
            else:  # Multi-segment snake
                dx, dy = segment[0] - snake_list[-2][0], segment[1] - snake_list[-2][1]
                if dx > 0:  # Moving right
                    rotated_head = pygame.transform.rotate(head_image, 180)
                elif dx < 0:  # Moving left
                    rotated_head = pygame.transform.rotate(head_image, 0)
                elif dy > 0:  # Moving down
                    rotated_head = pygame.transform.rotate(head_image, 90)
                elif dy < 0:  # Moving up
                    rotated_head = pygame.transform.rotate(head_image, 270)
            screen.blit(rotated_head, (segment[0], segment[1]))
        elif i == len(snake_list) - 1:  # Tail (first in original list)
            # Determine the direction of the tail
            dx, dy = snake_list[1][0] - segment[0], snake_list[1][1] - segment[1]
            if dx > 0:  # Tail pointing right
                rotated_tail = pygame.transform.rotate(tail_image, 0)
            elif dx < 0:  # Tail pointing left
                rotated_tail = pygame.transform.rotate(tail_image, 180)
            elif dy > 0:  # Tail pointing down
                rotated_tail = pygame.transform.rotate(tail_image, 90)
            elif dy < 0:  # Tail pointing up
                rotated_tail = pygame.transform.rotate(tail_image, 270)
            screen.blit(rotated_tail, (segment[0], segment[1]))
        else:  # Body
            # Determine the orientation of the body segment
            prev_seg = snake_list[::-1][i - 1]
            next_seg = snake_list[::-1][i + 1]
            dx_prev, dy_prev = segment[0] - prev_seg[0], segment[1] - prev_seg[1]
            dx_next, dy_next = next_seg[0] - segment[0], next_seg[1] - segment[1]

            if (dx_prev == 0 and dx_next == 0) or (dy_prev == 0 and dy_next == 0):
                # Straight body (horizontal or vertical)
                if dx_prev != 0 or dx_next != 0:  # Horizontal
                    rotated_body = pygame.transform.rotate(body_image, 0)
                else:  # Vertical
                    rotated_body = pygame.transform.rotate(body_image, 90)
            else:
                # Curved body
                if (dx_prev > 0 and dy_next > 0) or (dx_next > 0 and dy_prev > 0):  # Bottom-left curve
                    rotated_body = pygame.transform.rotate(body_image, 90)
                elif (dx_prev < 0 and dy_next > 0) or (dx_next < 0 and dy_prev > 0):  # Bottom-right curve
                    rotated_body = pygame.transform.rotate(body_image, 180)
                elif (dx_prev > 0 and dy_next < 0) or (dx_next > 0 and dy_prev < 0):  # Top-left curve
                    rotated_body = pygame.transform.rotate(body_image, 0)
                elif (dx_prev < 0 and dy_next < 0) or (dx_next < 0 and dy_prev < 0):  # Top-right curve
                    rotated_body = pygame.transform.rotate(body_image, 270)

            screen.blit(rotated_body, (segment[0], segment[1]))

def message(msg, color):
    mesg = font_style.render(msg, True, color)
    screen.blit(mesg, [width / 6, height / 3])

def display_score(score):
    value = score_font.render(f"Score: {score}", True, yellow)
    screen.blit(value, [10, 10])

def game_over_screen(final_score):
    menu_running = True
    selected_index = 0
    options = ["Play Again", "Quit to Main Menu"]

    while menu_running:
        screen.fill(blue)

        # Title for Game Over Screen
        title_font = pygame.font.SysFont("comicsansms", 50)
        title = title_font.render("Game Over", True, yellow)
        screen.blit(title, [width / 2 - title.get_width() / 2, 50])

        # Display Final Score
        score_font_large = pygame.font.SysFont("comicsansms", 35)
        score_text = score_font_large.render(f"Score: {final_score}", True, white)
        screen.blit(score_text, [width / 2 - score_text.get_width() / 2, 120])

        # Menu Options
        options_font = pygame.font.SysFont("bahnschrift", 30)
        option_positions = []

        for idx, option in enumerate(options):
            color = white if idx != selected_index else yellow
            option_surface = options_font.render(option, True, color)
            option_rect = option_surface.get_rect(center=(width // 2, 200 + idx * 50))
            option_positions.append(option_rect)

            screen.blit(option_surface, option_rect.topleft)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_UP, pygame.K_w]:  # Move selection up
                    selected_index = (selected_index - 1) % len(options)
                elif event.key in [pygame.K_DOWN, pygame.K_s]:  # Move selection down
                    selected_index = (selected_index + 1) % len(options)
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    if selected_index == 0:  # Play Again
                        return "play_again"
                    elif selected_index == 1:  # Quit to Main Menu
                        return "quit_to_menu"
            if event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                for idx, rect in enumerate(option_positions):
                    if rect.collidepoint(mouse_pos):
                        selected_index = idx
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
                for idx, rect in enumerate(option_positions):
                    if rect.collidepoint(pygame.mouse.get_pos()):
                        if idx == 0:  # Play Again
                            return "play_again"
                        elif idx == 1:  # Quit to Main Menu
                            return "quit_to_menu"

def gameLoop(debug=False):
    running = True  # Main control for the game loop

    while running:  # Main loop for restarting the game
        # Reset all game state variables
        game_over = False
        game_close = False
        game_start = False  # Wait for user input to start

        # Snake's initial position
        x1 = width // 2
        y1 = height // 2

        # Initialize snake with a single segment
        snake_List = [[x1, y1]]
        Length_of_snake = 1

        # Place food randomly
        foodx = random.randint(0, (width - snake_block) // snake_block) * snake_block
        foody = random.randint(0, (height - snake_block) // snake_block) * snake_block

        # Debug initial values
        if debug:
            print("Game reset:")
            print(f"Initial x1: {x1}, y1: {y1}")
            print(f"Initial Snake List: {snake_List}")
            print(f"Initial Food Position: {foodx}, {foody}")

        # Reset direction variables
        x1_change = 0
        y1_change = 0

        while not game_over:
            # Handle "game close" state
            while game_close:
                result = game_over_screen(Length_of_snake - 1)
                if result == "play_again":
                    return gameLoop(debug)
                elif result == "quit_to_menu":
                    return

                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_q:  # Quit the game
                            return
                        if event.key == pygame.K_c:  # Restart the game
                            return gameLoop(debug)  # Restart the game loop

            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # Handle window close
                    running = False
                    game_over = True
                if event.type == pygame.KEYDOWN:
                    game_start = True  # Set the flag once a key is pressed
                    if (event.key == pygame.K_LEFT or event.key == pygame.K_a) and x1_change == 0:
                        x1_change = -snake_block
                        y1_change = 0
                    elif (event.key == pygame.K_RIGHT or event.key == pygame.K_d) and x1_change == 0:
                        x1_change = snake_block
                        y1_change = 0
                    elif (event.key == pygame.K_UP or event.key == pygame.K_w) and y1_change == 0:
                        y1_change = -snake_block
                        x1_change = 0
                    elif (event.key == pygame.K_DOWN or event.key == pygame.K_s) and y1_change == 0:
                        y1_change = snake_block
                        x1_change = 0

            if not game_start:
                # Draw the initial state of the game while waiting for input
                screen.fill(blue)
                pygame.draw.rect(screen, green, [foodx, foody, snake_block, snake_block])
                our_snake(snake_List, x1_change, y1_change)
                display_score(Length_of_snake - 1)
                pygame.display.update()
                continue

            # Update snake's head position
            x1 += x1_change
            y1 += y1_change

            # Create the new head
            snake_Head = [x1, y1]

            # Check for boundary collision
            if x1 >= width or x1 < 0 or y1 >= height or y1 < 0:
                game_close = True
                continue

            # Check for self-collision only when the snake has more than one segment
            if len(snake_List) > 1 and snake_Head in snake_List[:-1]:
                game_close = True
                continue

            # Append new head to the snake
            snake_List.append(snake_Head)

            # Remove the oldest segment if necessary
            if len(snake_List) > Length_of_snake:
                del snake_List[0]

            # Check if the snake eats the food
            if x1 == foodx and y1 == foody:
                foodx = random.randint(0, (width - snake_block) // snake_block) * snake_block
                foody = random.randint(0, (height - snake_block) // snake_block) * snake_block
                Length_of_snake += 1  # Increment the snake length (score)

            # Render the game elements
            screen.fill(blue)
            pygame.draw.rect(screen, green, [foodx, foody, snake_block, snake_block])
            our_snake(snake_List, x1_change, y1_change)
            display_score(Length_of_snake - 1)  # Display the score
            pygame.display.update()

            clock.tick(snake_speed)

    # Cleanup after exiting
    pygame.quit()
    quit()

if __name__ == "__main__":
    while True:
        choice = main_menu()
        if choice == "new_game":
            gameLoop(debug=True)
        elif choice == "hi_scores":
            print("HiScores - To be implemented")
        elif choice == "settings":
            print("Settings - To be implemented")
