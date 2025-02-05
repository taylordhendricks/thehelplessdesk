import pygame
import sys
from pytmx import load_pygame, TiledImageLayer

def main():
    pygame.init()
    screen_width = 1200
    screen_height = 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Static Sky + Moving Clouds Tile Layer")

    clock = pygame.time.Clock()

    # 1) Load the universal backdrop image in Python
    background_img = pygame.image.load(r"python\games\PlumberLite\Assets\sky.png").convert()

    # 2) Load Tiled map for collisions, cloud layer, etc.
    tmx_data = load_pygame(r"python\games\PlumberLite\Assets\TestSet.tmx")
    tile_width = tmx_data.tilewidth
    tile_height = tmx_data.tileheight
    map_width = tmx_data.width    # in tiles
    map_height = tmx_data.height

    # We'll store collisions in these:
    collidable_rects = []
    climbable_rects = []

    # We'll keep a reference to the "Clouds" tile layer, if you named it that in Tiled
    clouds_layer = None

    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'data'):  # tile layer
            # Check layer.name to see if it’s "Clouds"
            if layer.name == "Clouds":
                clouds_layer = layer
            else:
                # normal tile layers (collision, etc.)
                for x, y, gid in layer:
                    if gid == 0:
                        continue
                    tile_props = tmx_data.get_tile_properties_by_gid(gid)
                    if tile_props:
                        if tile_props.get("collision") is True:
                            rect = pygame.Rect(
                                x * tile_width,
                                y * tile_height,
                                tile_width,
                                tile_height
                            )
                            collidable_rects.append(rect)
                        if tile_props.get("climbable") is True:
                            rect = pygame.Rect(
                                x * tile_width,
                                y * tile_height,
                                tile_width,
                                tile_height
                            )
                            climbable_rects.append(rect)

        elif hasattr(layer, 'objects'):
            for obj in layer.objects:
                props = obj.properties
                if props.get("collision") is True:
                    r = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                    collidable_rects.append(r)
                if props.get("climbable") is True:
                    r = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                    climbable_rects.append(r)

    # Basic camera
    camera_x = 0
    camera_y = 0

    # Player setup
    player_size = 32
    start_x, start_y = 64, 3072
    player_rect = pygame.Rect(start_x, start_y, player_size, player_size)
    player_color = (255, 0, 0)

    # Movement speeds
    player_walk_speed = 5
    player_sprint_speed = 9

    # Gravity, jump
    gravity = 0.8
    jump_power = 15
    player_vel_y = 0
    on_ground = False

    # Ladder
    on_ladder = False
    climb_speed = 4

    # -------------------------------
    # CLOUDS LAYER SCROLL CONFIG
    # -------------------------------
    # We'll shift clouds_offset_x in tile coords
    clouds_offset_x = 0
    clouds_scroll_timer = 0
    clouds_scroll_interval = 300  # ms, shift 1 tile every 0.3 seconds

    running = True
    while running:
        dt = clock.tick(60)  # in ms
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # -- KEY INPUT --
        keys = pygame.key.get_pressed()

        current_speed = player_walk_speed
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            current_speed = player_sprint_speed

        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -current_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = current_speed

        # Check ladder
        on_ladder = False
        for ladder_rect in climbable_rects:
            if player_rect.colliderect(ladder_rect):
                on_ladder = True
                break

        # Jump
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and (on_ground or on_ladder):
            if on_ladder:
                on_ladder = False
            player_vel_y = -jump_power
            on_ground = False

        # Vertical movement
        if on_ladder:
            player_vel_y = 0
            dy = 0
            if (keys[pygame.K_DOWN] or keys[pygame.K_s]):
                if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
                    on_ladder = False
                    player_vel_y = 15
                    dy = player_vel_y
                else:
                    dy = climb_speed
            elif (keys[pygame.K_UP] or keys[pygame.K_w]):
                if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
                    on_ladder = False
                    player_vel_y = -15
                    dy = player_vel_y
                else:
                    dy = -climb_speed
        else:
            player_vel_y += gravity
            dy = player_vel_y

        # Move horizontally
        player_rect.x += dx
        for rect in collidable_rects:
            if player_rect.colliderect(rect):
                if dx > 0:  # right
                    player_rect.right = rect.left
                elif dx < 0: # left
                    player_rect.left = rect.right

        if player_rect.left < 0:
            player_rect.left = 0
        right_boundary = map_width * tile_width
        if player_rect.right > right_boundary:
            player_rect.right = right_boundary

        # Move vertically
        on_ground = False
        player_rect.y += dy
        for rect in collidable_rects:
            if player_rect.colliderect(rect):
                if dy > 0: # falling
                    player_rect.bottom = rect.top
                    player_vel_y = 0
                    on_ground = True
                elif dy < 0: # jumping
                    player_rect.top = rect.bottom
                    player_vel_y = 0

        # Bottom boundary
        bottom_boundary = map_height * tile_height
        if player_rect.top > bottom_boundary:
            player_rect.x = start_x
            player_rect.y = start_y
            player_vel_y = 0
            on_ground = False

        # Camera
        camera_x = player_rect.centerx - screen_width // 2
        camera_y = player_rect.centery - screen_height // 2
        max_camera_x = map_width * tile_width - screen_width
        max_camera_y = map_height * tile_height - screen_height
        camera_x = max(0, min(camera_x, max_camera_x))
        camera_y = max(0, min(camera_y, max_camera_y))

        # -------------------------
        # Update clouds layer offset
        # -------------------------
        clouds_scroll_timer += dt
        if clouds_scroll_timer >= clouds_scroll_interval:
            clouds_scroll_timer = 0
            clouds_offset_x += 0.125  # shift the clouds 1 tile to the left each time
            clouds_offset_x %= map_width  # wrap around

        # Draw
        screen.fill((0,0,0))

        # 1) Draw the universal backdrop image at (0,0), ignoring camera
        screen.blit(background_img, (0, 0))
        
        # 3) Draw the Clouds layer with offset
        if clouds_layer is not None:
            for x, y, gid in clouds_layer:
                if gid == 0:
                    continue
                tile_img = tmx_data.get_tile_image_by_gid(gid)
                if tile_img:
                    # Subtract clouds_offset_x in tile coords => shift horizontally
                    tile_px = (x - clouds_offset_x) * tile_width
                    tile_py = y * tile_height
                    # Optional wrap-around
                    tile_px_mod = tile_px % (map_width * tile_width)
                    final_x = tile_px_mod - camera_x
                    final_y = tile_py - camera_y
                    screen.blit(tile_img, (final_x, final_y))

        # 2) Draw other Tiled layers (NOT the Clouds yet)
        for layer in tmx_data.visible_layers:
            # skip the clouds layer if we find it
            if layer == clouds_layer:
                continue

            if isinstance(layer, TiledImageLayer):
                if layer.image:
                    screen.blit(layer.image, (0 - camera_x, 0 - camera_y))
            elif hasattr(layer, 'data'):
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


        # 4) Draw the player
        px = player_rect.x - camera_x
        py = player_rect.y - camera_y
        pygame.draw.rect(screen, player_color, (px, py, player_size, player_size))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()