import pygame
import sys
from pytmx import load_pygame

def main():
    pygame.init()
    screen_width = 1200
    screen_height = 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Tiled Map Collision Example")

    clock = pygame.time.Clock()

    # 1) Load the Tiled map
    tmx_data = load_pygame(r"python\games\PlumberLite\Assets\PokeClone.tmx")  # Replace with your .tmx filename

    tile_width = tmx_data.tilewidth
    tile_height = tmx_data.tileheight
    map_width = tmx_data.width    # number of tiles horizontally
    map_height = tmx_data.height  # number of tiles vertically

    # 2) Build a list of "collidable" tile rects
    collidable_rects = []
    for layer in tmx_data.visible_layers:
        if not hasattr(layer, 'data'):
            continue  # skip Non-tile layers (ObjectLayers, ImageLayers, etc.)
        for x, y, gid in layer:
            if gid == 0:
                continue  # no tile here
            tile_props = tmx_data.get_tile_properties_by_gid(gid)
            if tile_props and tile_props.get("collision") is True:
                # Create a rect in pixel coordinates
                rect = pygame.Rect(
                    x * tile_width,
                    y * tile_height,
                    tile_width,
                    tile_height
                )
                collidable_rects.append(rect)

    # Simple camera
    camera_x = 0
    camera_y = 0

    # Player setup
    player_size = 32
    player_pos = [64, 31872]
    player_rect = pygame.Rect(player_pos[0], player_pos[1], player_size, player_size)
    player_speed = 5
    player_color = (255, 0, 0)

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        
        # We'll use separate variables for x/y movement
        dx = 0
        dy = 0
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -player_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = player_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -player_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = player_speed

        # 3) Move the player in the X direction, check collisions
        player_rect.x += dx
        # Check collision with each collidable rect
        for rect in collidable_rects:
            if player_rect.colliderect(rect):
                # Collided, so move back
                if dx > 0:  # moving right
                    player_rect.right = rect.left
                elif dx < 0:  # moving left
                    player_rect.left = rect.right

        # 4) Move the player in the Y direction, check collisions
        player_rect.y += dy
        for rect in collidable_rects:
            if player_rect.colliderect(rect):
                # Collided, so move back
                if dy > 0:  # moving down
                    player_rect.bottom = rect.top
                elif dy < 0:  # moving up
                    player_rect.top = rect.bottom

        # 5) Center the camera on the player
        camera_x = player_rect.centerx - screen_width // 2
        camera_y = player_rect.centery - screen_height // 2

        # Clamp the camera so it doesn't scroll past the edges
        max_camera_x = map_width * tile_width - screen_width
        max_camera_y = map_height * tile_height - screen_height
        camera_x = max(0, min(camera_x, max_camera_x))
        camera_y = max(0, min(camera_y, max_camera_y))

        # Clear the screen
        screen.fill((0, 0, 0))

        # 6) Draw the Tiled map
        for layer in tmx_data.visible_layers:
            if not hasattr(layer, 'data'):
                continue
            for x, y, gid in layer:
                if gid != 0:
                    tile_image = tmx_data.get_tile_image_by_gid(gid)
                    if tile_image:
                        tile_px = x * tile_width
                        tile_py = y * tile_height
                        screen.blit(
                            tile_image,
                            (tile_px - camera_x, tile_py - camera_y)
                        )

        # 7) Draw the player
        screen_x = player_rect.x - camera_x
        screen_y = player_rect.y - camera_y
        pygame.draw.rect(screen, player_color, (screen_x, screen_y, player_size, player_size))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()