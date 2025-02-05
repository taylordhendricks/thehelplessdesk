import pygame
import time
import random
import configparser
import os

pygame.init()

# Useful Colors
white = (255, 255, 255)
yellow = (255, 255, 102)
black = (0, 0, 0)
red = (213, 50, 80)
green = (0, 255, 0)
blue = (50, 153, 213)

HIGHSCORES_FILE = (r"python\games\Snake\highscores.txt")

# Load configuration or create a default one
CONFIG_FILE = (r"python\games\Snake\config.ini")
def load_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        config['SETTINGS'] = {
            'width': '600',
            'height': '400',
            'snake_block': '10',
            'snake_speed': '15'
        }
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
    else:
        config.read(CONFIG_FILE)
    return config

def save_config(config):
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

config = load_config()
width = int(config['SETTINGS']['width'])
height = int(config['SETTINGS']['height'])
snake_block = int(config['SETTINGS']['snake_block'])
snake_speed = int(config['SETTINGS']['snake_speed'])

# Screen dimensions
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Danger Noodle')
fullscreen = False

# Load and set the custom game icon
icon = pygame.image.load(r"python\games\Snake\Assets\snake_icon.ico").convert_alpha()
pygame.display.set_icon(icon)

# Load and scale the main menu background image
main_menu_bg = pygame.image.load(r"python\games\Snake\Assets\main_menu.png").convert()
game_loop_bg = pygame.image.load(r"python\games\Snake\Assets\game_background.png").convert()

clock = pygame.time.Clock()

font_style = pygame.font.SysFont("bahnschrift", 25)
score_font = pygame.font.SysFont("comicsansms", 35)

#Load and scale Sprites
def scale_sprites():
    global head_image, body_image, tail_image, food_image, food2_image, food3_image, food4_image, multiplier_image, divider_image, poison_image, antidote_image
    head_image = pygame.transform.scale(pygame.image.load(r"python\games\Snake\Assets\snake_head.png").convert_alpha(), (snake_block, snake_block))
    body_image = pygame.transform.scale(pygame.image.load(r"python\games\Snake\Assets\snake_body.png").convert_alpha(), (snake_block, snake_block))
    tail_image = pygame.transform.scale(pygame.image.load(r"python\games\Snake\Assets\snake_tail.png").convert_alpha(), (snake_block, snake_block))
    food_image = pygame.transform.scale(pygame.image.load(r"python\games\Snake\Assets\food.png").convert_alpha(), (snake_block, snake_block))
    food2_image = pygame.transform.scale(pygame.image.load(r"python\games\Snake\Assets\food2.png").convert_alpha(), (snake_block, snake_block))
    food3_image = pygame.transform.scale(pygame.image.load(r"python\games\Snake\Assets\food3.png").convert_alpha(), (snake_block, snake_block))
    food4_image = pygame.transform.scale(pygame.image.load(r"python\games\Snake\Assets\food4.png").convert_alpha(), (snake_block, snake_block))
    multiplier_image = pygame.transform.scale(pygame.image.load(r"python\games\Snake\Assets\egg.png").convert_alpha(), (snake_block, snake_block))
    divider_image = pygame.transform.scale(pygame.image.load(r"python\games\Snake\Assets\divider.png").convert_alpha(), (snake_block, snake_block))
    poison_image = pygame.transform.scale(pygame.image.load(r"python\games\Snake\Assets\poison.png").convert_alpha(), (snake_block, snake_block))
    antidote_image = pygame.transform.scale(pygame.image.load(r"python\games\Snake\Assets\antidote.png").convert_alpha(), (snake_block, snake_block))

def render_text_with_background(text, font, text_color, bg_color, position, center=False):
    """
    Render text with a semi-transparent background.
    :param text: The text to render.
    :param font: The pygame font object.
    :param text_color: The color of the text.
    :param bg_color: The background color (with alpha).
    :param position: Tuple (x, y) for the top-left corner or center of the text.
    :param center: Whether to center the text at the given position.
    :return: Rendered surface and its rectangle.
    """
    # Render the text surface
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect()

    if center:
        text_rect.center = position
    else:
        text_rect.topleft = position

    # Create a semi-transparent background surface
    bg_surface = pygame.Surface((text_rect.width + 10, text_rect.height + 10), pygame.SRCALPHA)
    bg_surface.fill(bg_color)  # Semi-transparent background

    # Draw background and then text
    screen.blit(bg_surface, (text_rect.x - 5, text_rect.y - 5))
    screen.blit(text_surface, text_rect.topleft)

    return text_surface, text_rect

def main_menu():
    menu_running = True
    selected_index = 0  # Track which menu item is selected
    options = ["New Game", "HiScores", "Settings", "Exit"]
    option_positions = []  # Stores rectangles for hit detection

    while menu_running:
        # Scale the background image to fit the current resolution
        scaled_bg = pygame.transform.scale(main_menu_bg, (width, height))
        screen.blit(scaled_bg, (0, 0))  # Draw the background image

        # Title or Game Image
        title_font = pygame.font.SysFont("comicsansms", 50)
        render_text_with_background(
            "Snake Game",
            title_font,
            yellow,
            (0, 0, 0, 150),  # Semi-transparent black (alpha=150)
            (width / 2, 50),  # Centered horizontally
            center=True
        )

        # Menu Options
        options_font = pygame.font.SysFont("bahnschrift", 35)
        option_positions.clear()  # Reset positions for hit detection

        for idx, option in enumerate(options):
            # Check if the current option is hovered/selected
            is_selected = idx == selected_index
            color = white if not is_selected else yellow

            # Render option with background
            _, option_rect = render_text_with_background(
                option,
                options_font,
                color,
                (0, 0, 0, 150),  # Semi-transparent black background
                (width / 2, 150 + idx * 50),
                center=True
            )

            # Store the rect for hit detection
            option_positions.append(option_rect)

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
                rotated_tail = pygame.transform.rotate(tail_image, 270)
            elif dy < 0:  # Tail pointing up
                rotated_tail = pygame.transform.rotate(tail_image, 90)
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

def load_highscores():
    """Load high scores from a file."""
    if not os.path.exists(HIGHSCORES_FILE):
        return []
    with open(HIGHSCORES_FILE, "r") as file:
        scores = [line.strip() for line in file.readlines()]
    return [(name, int(score)) for name, score in (entry.split(":") for entry in scores)]

def save_highscores(scores):
    """Save high scores to a file."""
    with open(HIGHSCORES_FILE, "w") as file:
        for name, score in scores:
            file.write(f"{name}:{score}\n")

def add_highscore(name, score):
    """Add a new high score and keep only the top 10."""
    scores = load_highscores()
    scores.append((name, score))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)[:10]  # Keep top 10
    save_highscores(scores)

def reset_highscores():
    """Reset the high scores."""
    with open(HIGHSCORES_FILE, "w") as file:
        file.write("")

def display_highscores():
    """Display the high scores screen."""
    scores = load_highscores()
    menu_running = True
    scroll_offset = 0
    r_key_held = False
    r_key_start_time = None  # Tracks the start time for holding the R key

    while menu_running:
        scaled_bg = pygame.transform.scale(main_menu_bg, (width, height))
        screen.blit(scaled_bg, (0, 0))  # Draw the background image

        title_font = pygame.font.SysFont("comicsansms", 50)
        render_text_with_background(
            "High Scores",
            title_font,
            yellow,
            (0, 0, 0, 150),
            (width / 2 - 150, 50)
        )

        scores_font = pygame.font.SysFont("bahnschrift", 30)
        y_offset = 150 - scroll_offset
        for idx, (name, score) in enumerate(scores):
            # Name on the left at 25% width
            render_text_with_background(
                f"{idx + 1}. {name}",
                scores_font,
                white,
                (0, 0, 0, 150),
                (width * 0.25, y_offset + idx * 30)
            )
            # Score on the right at 75% width
            render_text_with_background(
                str(score),
                scores_font,
                white,
                (0, 0, 0, 150),
                (width * 0.75 - scores_font.size(str(score))[0], y_offset + idx * 30)
            )

        back_font = pygame.font.SysFont("bahnschrift", 30)
        render_text_with_background(
            "Press ESC to return to Main Menu",
            back_font,
            white,
            (0, 0, 0, 150),
            (width / 2, height - 50),
            center=True 
        )

        render_text_with_background(
            "Hold R for 5 seconds to Reset High Scores",
            back_font,
            white,
            (0, 0, 0, 150),
            (width / 2, height - 100),
            center=True 
        )

        if r_key_held:
            remaining_time = max(0, 5 - (pygame.time.get_ticks() - r_key_start_time) // 1000)
            hold_text = f"Resetting in {remaining_time} seconds..."
            render_text_with_background(
                hold_text,
                back_font,
                red,
                (0, 0, 0, 150),
                (width / 2, height - 150),
                center=True 
            )
            if remaining_time <= 0:  # Reset the high scores after 5 seconds
                reset_highscores()
                scores = []  # Clear the in-memory scores
                r_key_held = False  # Reset the state

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # Return to Main Menu
                    return
                if event.key == pygame.K_r and not r_key_held:  # Start reset timer
                    r_key_held = True
                    r_key_start_time = pygame.time.get_ticks()  # Record the time when R is pressed
                if event.key == pygame.K_UP:  # Scroll up
                    scroll_offset = max(0, scroll_offset - 30)
                if event.key == pygame.K_DOWN:  # Scroll down
                    if len(scores) * 30 + 150 > height:
                        scroll_offset = min(scroll_offset + 30, len(scores) * 30 + 150 - height)
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_r:  # Cancel the reset timer on key release
                    r_key_held = False
                    r_key_start_time = None

def game_over_screen(score):
    """Display the game over screen."""
    menu_running = True
    scaled_bg = pygame.transform.scale(main_menu_bg, (width, height))
    screen.blit(scaled_bg, (0, 0))  # Draw the background image

    # Check if the score is a new high score
    scores = load_highscores()
    is_new_highscore = len(scores) < 5 or score > scores[-1][1]

    # Input box for name entry
    input_box = pygame.Rect(width / 2 - 100, 250, 200, 50)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    name = ""
    cursor_visible = True
    cursor_timer = 0

    # Menu Options
    options = ["Play Again", "Quit to Main Menu"]
    selected_index = 0
    options_font = pygame.font.SysFont("bahnschrift", 30)
    option_positions = []

    while menu_running:
        scaled_bg = pygame.transform.scale(main_menu_bg, (width, height))
        screen.blit(scaled_bg, (0, 0))  # Draw the background image

        # Draw Title
        title_font = pygame.font.SysFont("comicsansms", 50)
        render_text_with_background(
            "Game Over",
            title_font,
            yellow,
            (0, 0, 0, 150),
            (width / 2, 50),
            center=True
        )

        # Display Final Score
        score_font = pygame.font.SysFont("comicsansms", 35)
        render_text_with_background(
            f"Score: {score}",
            score_font,
            white,
            (0, 0, 0, 150),
            (width / 2, 150),
            center=True
        )

        # Display Message for High Score or Not
        message_font = pygame.font.SysFont("bahnschrift", 30)
        if is_new_highscore:
            render_text_with_background(
                "Congratulations, new HiScore!!",
                message_font,
                white,
                (0, 0, 0, 150),
                (width / 2, 200),
                center=True
            )
        else:
            render_text_with_background(
                "No new HiScore, better luck next time!",
                message_font,
                white,
                (0, 0, 0, 150),
                (width / 2, 200),
                center=True
            )

        # Draw Input Box if New HiScore
        if is_new_highscore:
            input_box_bg = pygame.Surface((input_box.w + 10, input_box.h + 10), pygame.SRCALPHA)
            input_box_bg.fill((0, 0, 0, 150))  # Semi-transparent black
            screen.blit(input_box_bg, (input_box.x - 5, input_box.y - 5))

            txt_surface = options_font.render(name, True, white)
            width_box = max(200, txt_surface.get_width() + 10)
            input_box.w = width_box
            screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
            pygame.draw.rect(screen, color, input_box, 2)

            # Handle blinking cursor
            cursor_timer += clock.get_time()
            if cursor_timer >= 500:
                cursor_visible = not cursor_visible
                cursor_timer = 0
            if active and cursor_visible:
                pygame.draw.line(screen, white, (input_box.x + 5 + txt_surface.get_width(), input_box.y + 5),
                                 (input_box.x + 5 + txt_surface.get_width(), input_box.y + 45), 2)

        # Draw Menu Options
        option_positions.clear()
        for idx, option in enumerate(options):
            color = yellow if idx == selected_index else white
            _, option_rect = render_text_with_background(
                option,
                options_font,
                color,
                (0, 0, 0, 150),
                (width / 2, 350 + idx * 50),
                center=True
            )
            option_positions.append(option_rect)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                for idx, rect in enumerate(option_positions):
                    if rect.collidepoint(mouse_pos):
                        selected_index = idx
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if option_positions[0].collidepoint(event.pos):  # Play Again
                        if is_new_highscore:
                            add_highscore(name, score)
                        return "play_again"
                    if option_positions[1].collidepoint(event.pos):  # Quit to Main Menu
                        if is_new_highscore:
                            add_highscore(name, score)
                        return "quit_to_menu"
                if input_box.collidepoint(event.pos):  # Click on input box
                    active = not active
                    color = color_active if active else color_inactive
                else:
                    active = False
                    color = color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        if is_new_highscore:
                            add_highscore(name, score)
                        return "quit_to_menu"
                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    else:
                        name += event.unicode
                else:
                    if event.key == pygame.K_UP:
                        selected_index = (selected_index - 1) % len(options)
                    elif event.key == pygame.K_DOWN:
                        selected_index = (selected_index + 1) % len(options)
                    elif event.key == pygame.K_RETURN:
                        if selected_index == 0:  # Play Again
                            if is_new_highscore:
                                add_highscore(name, score)
                            return "play_again"
                        elif selected_index == 1:  # Quit to Main Menu
                            if is_new_highscore:
                                add_highscore(name, score)
                            return "quit_to_menu"

def toggle_fullscreen():
    global screen, fullscreen
    fullscreen = not fullscreen
    if fullscreen:
        display_info = pygame.display.Info()  # Get native resolution
        width, height = display_info.current_w, display_info.current_h
        screen = pygame.display.set_mode((width, height), pygame.NOFRAME | pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((width, height))

def settings_menu():
    global width, height, snake_block, snake_speed, screen, fullscreen
    menu_running = True
    selected_index = 0  # Tracks the currently highlighted option
    resolutions = ["1280 x 720", "1920 x 1080"]
    resolution_values = [(1280, 720), (1920, 1080)]
    current_resolution_index = resolution_values.index((width, height)) if (width, height) in resolution_values else 0
    current_speed = snake_speed

    while menu_running:
        scaled_bg = pygame.transform.scale(main_menu_bg, (width, height))
        screen.blit(scaled_bg, (0, 0))  # Draw the background image

        # Title for Settings Menu
        title_font = pygame.font.SysFont("comicsansms", 50)
        render_text_with_background(
            "Settings",
            title_font,
            yellow,
            (0, 0, 0, 150),
            (width / 2, 50),
            center=True
        )

        # Menu Options
        options = [
            f"Game Resolution: {resolutions[current_resolution_index]}",
            f"Game Speed: {current_speed}",
            f"Fullscreen: {'ON' if fullscreen else 'OFF'}",
            "Back to Main Menu"
        ]
        options_font = pygame.font.SysFont("bahnschrift", 30)
        option_positions = []

        for idx, option in enumerate(options):
            color = white if idx != selected_index else yellow
            _, option_rect = render_text_with_background(
                option,
                options_font,
                color,
                (0, 0, 0, 150),
                (width / 2, 150 + idx * 50),
                center=True
            )
            option_positions.append(option_rect)

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
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:  # Increase resolution or toggle settings
                    if selected_index == 0:  # Change Resolution
                        current_resolution_index = (current_resolution_index + 1) % len(resolutions)
                        new_width, new_height = resolution_values[current_resolution_index]
                        width, height = new_width, new_height
                        screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN if fullscreen else 0)
                        snake_block = max(10, width // 64)  # Adjust snake block size proportionally
                        scale_sprites()
                        config['SETTINGS']['width'] = str(width)
                        config['SETTINGS']['height'] = str(height)
                        config['SETTINGS']['snake_block'] = str(snake_block)
                        save_config(config)
                    elif selected_index == 1:  # Adjust Speed
                        current_speed = min(50, current_speed + 1)
                        snake_speed = current_speed
                        config['SETTINGS']['snake_speed'] = str(snake_speed)
                        save_config(config)
                    elif selected_index == 2:  # Toggle Fullscreen
                        fullscreen = not fullscreen
                        display_info = pygame.display.Info()  # Get native resolution
                        width, height = display_info.current_w, display_info.current_h
                        screen = pygame.display.set_mode((width, height), pygame.NOFRAME | pygame.FULLSCREEN if fullscreen else 0)
                        config['SETTINGS']['fullscreen'] = str(fullscreen)
                        save_config(config)
                elif event.key in [pygame.K_LEFT, pygame.K_a]:  # Decrease resolution or settings
                    if selected_index == 0:  # Change Resolution
                        current_resolution_index = (current_resolution_index - 1) % len(resolutions)
                        new_width, new_height = resolution_values[current_resolution_index]
                        width, height = new_width, new_height
                        screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN if fullscreen else 0)
                        snake_block = max(10, width // 64)  # Adjust snake block size proportionally
                        scale_sprites()
                        config['SETTINGS']['width'] = str(width)
                        config['SETTINGS']['height'] = str(height)
                        config['SETTINGS']['snake_block'] = str(snake_block)
                        save_config(config)
                    elif selected_index == 1:  # Adjust Speed
                        current_speed = max(1, current_speed - 1)
                        snake_speed = current_speed
                        config['SETTINGS']['snake_speed'] = str(snake_speed)
                        save_config(config)
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:  # Select option
                    if selected_index == 3:  # Back to Main Menu
                        return

            if event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                for idx, rect in enumerate(option_positions):
                    if rect.collidepoint(mouse_pos):
                        selected_index = idx

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if option_positions[selected_index].collidepoint(event.pos):
                        if selected_index == 0:  # Change Resolution
                            current_resolution_index = (current_resolution_index + 1) % len(resolutions)
                            new_width, new_height = resolution_values[current_resolution_index]
                            width, height = new_width, new_height
                            screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN if fullscreen else 0)
                            snake_block = max(10, width // 64)  # Adjust snake block size proportionally
                            scale_sprites()
                            config['SETTINGS']['width'] = str(width)
                            config['SETTINGS']['height'] = str(height)
                            config['SETTINGS']['snake_block'] = str(snake_block)
                            save_config(config)
                        elif selected_index == 1:  # Adjust Speed
                            current_speed = min(50, current_speed + 1)
                            snake_speed = current_speed
                            config['SETTINGS']['snake_speed'] = str(snake_speed)
                            save_config(config)
                        elif selected_index == 2:  # Toggle Fullscreen
                            fullscreen = not fullscreen
                            display_info = pygame.display.Info()  # Get native resolution
                            width, height = display_info.current_w, display_info.current_h
                            screen = pygame.display.set_mode((width, height), pygame.NOFRAME | pygame.FULLSCREEN if fullscreen else 0)
                            config['SETTINGS']['fullscreen'] = str(fullscreen)
                            save_config(config)
                        elif selected_index == 3:  # Back to Main Menu
                            return
                elif event.button == 3:  # Right click
                    if option_positions[selected_index].collidepoint(event.pos):
                        if selected_index == 0:  # Change Resolution
                            current_resolution_index = (current_resolution_index - 1) % len(resolutions)
                            new_width, new_height = resolution_values[current_resolution_index]
                            width, height = new_width, new_height
                            screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN if fullscreen else 0)
                            snake_block = max(10, width // 64)  # Adjust snake block size proportionally
                            scale_sprites()
                            config['SETTINGS']['width'] = str(width)
                            config['SETTINGS']['height'] = str(height)
                            config['SETTINGS']['snake_block'] = str(snake_block)
                            save_config(config)
                        elif selected_index == 1:  # Adjust Speed
                            current_speed = max(1, current_speed - 1)
                            snake_speed = current_speed
                            config['SETTINGS']['snake_speed'] = str(snake_speed)
                            save_config(config)

def gameLoop(debug=False):
    global snake_block, snake_speed
    scale_sprites()  # Ensure sprites are scaled correctly
    running = True

    while running:
        # Reset all game state variables
        game_over = False
        game_close = False
        game_start = False
        poisoned = False
        poison_timer = 0

        # Snake's initial position
        x1 = width // 2
        y1 = height // 2

        # Initialize snake with a single segment
        snake_List = [[x1, y1]]
        Length_of_snake = 1
        score = 0  # Separate variable to track the score

        # Place food randomly
        foodx = random.randint(0, (width - snake_block) // snake_block) * snake_block
        foody = random.randint(0, (height - snake_block) // snake_block) * snake_block

        # Determine the food type
        food_type = "add_1"

        # Debug initial values
        if debug:
            print("Game reset:")
            print(f"Initial x1: {x1}, y1: {y1}")
            print(f"Initial Snake List: {snake_List}")
            print(f"Initial Food Position: {foodx}, {foody}")
            print(f"Initial Food Type: {food_type}")

        # Reset direction variables
        x1_change = 0
        y1_change = 0

        while not game_over:
            # Handle "game close" state
            while game_close:
                result = game_over_screen(score)
                if result == "play_again":
                    return gameLoop(debug)
                elif result == "quit_to_menu":
                    return

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
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
                scaled_bg = pygame.transform.scale(game_loop_bg, (width, height))
                screen.blit(scaled_bg, (0, 0))  # Draw the background image
                screen.blit(get_food_image(food_type), (foodx, foody))
                our_snake(snake_List, x1_change, y1_change)
                display_score(score)
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
                if food_type.startswith("add_"):
                    Length_of_snake += int(food_type[-1])  # Add corresponding length
                    score += int(food_type[-1])  # Increase score
                elif food_type == "multiplier":
                    Length_of_snake *= 2
                    score *= 2  # Double the score
                elif food_type == "divider":
                    Length_of_snake = max(1, Length_of_snake // 2)  # Reduce length but not below 1
                    snake_List = snake_List[-Length_of_snake:]  # Visually truncate the snake
                elif food_type == "poison":
                    poisoned = True
                elif food_type == "antidote":
                    poisoned = False

                # Respawn food
                foodx = random.randint(0, (width - snake_block) // snake_block) * snake_block
                foody = random.randint(0, (height - snake_block) // snake_block) * snake_block
                food_type = get_random_food(poisoned)

            # Handle poisoning effect
            if poisoned:
                poison_timer += clock.get_time()
                if poison_timer >= 1000:  # Reduce length every second
                    poison_timer = 0
                    if Length_of_snake > 1:
                        Length_of_snake -= 1
                        score += 5
                        del snake_List[0]  # Visually shorten the snake
                    if Length_of_snake == 1:
                        game_close = True

            # Render the game elements
            scaled_bg = pygame.transform.scale(game_loop_bg, (width, height))
            screen.blit(scaled_bg, (0, 0))  # Draw the background image
            screen.blit(get_food_image(food_type), (foodx, foody))
            our_snake(snake_List, x1_change, y1_change)
            display_score(score)  # Display the score
            pygame.display.update()

            clock.tick(snake_speed)

    # Cleanup after exiting
    pygame.quit()
    quit()

# Helper functions for food
def get_random_food(poisoned):
    if poisoned:
        return random.choices(
            ["antidote", "add_4"], weights=[2, 1], k=1)[0]
    return random.choices(
        ["add_1", "add_2", "add_3", "add_4", "multiplier", "divider", "poison"],
        weights=[6, 3, 2, 1, 1, 1, 1],
        k=1
    )[0]


def get_food_image(food_type):
    # Map food types to images
    food_images = {
        "add_1": food_image,
        "add_2": food2_image,
        "add_3": food3_image,
        "add_4": food4_image,
        "multiplier": multiplier_image,
        "divider": divider_image,
        "poison": poison_image,
        "antidote": antidote_image
    }
    return food_images.get(food_type, food_image)

if __name__ == "__main__":
    while True:
        choice = main_menu()
        if choice == "new_game":
            gameLoop(debug=True)
        elif choice == "hi_scores":
            display_highscores()
        elif choice == "settings":
            settings_menu()
