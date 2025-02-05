import pygame
import sys
import math
from pytmx import load_pygame, TiledImageLayer

# --------------------------------
# 1) Helper to load frames from separate sheets
# --------------------------------
def load_animation_frames(sheet_path, frame_count, frame_w=64, frame_h=96):
    sheet = pygame.image.load(sheet_path).convert_alpha()
    left_frames = []
    for i in range(frame_count):
        surf = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
        surf.blit(sheet, (0,0), (i*frame_w, 0, frame_w, frame_h))
        left_frames.append(surf)
    right_frames = [pygame.transform.flip(f, True, False) for f in left_frames]
    return left_frames, right_frames

def main():
    pygame.init()
    screen_width = 1200
    screen_height = 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("My Game")

    clock = pygame.time.Clock()

    # 2) Load the universal backdrop image in Python
    background_img = pygame.image.load(r"python\games\PlumberLite\Assets\sky.png").convert()

    # 3) Load Tiled map
    tmx_data = load_pygame(r"python\games\PlumberLite\Assets\TestSet.tmx")
    tile_width = tmx_data.tilewidth
    tile_height = tmx_data.tileheight
    map_width = tmx_data.width    # in tiles
    map_height = tmx_data.height

    collidable_rects = []
    climbable_rects = []
    clouds_layer = None

    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'data'):
            if layer.name == "Clouds":
                clouds_layer = layer
            else:
                for x, y, gid in layer:
                    if gid == 0:
                        continue
                    tile_props = tmx_data.get_tile_properties_by_gid(gid)
                    if tile_props:
                        if tile_props.get("collision") is True:
                            rect = pygame.Rect(x*tile_width, y*tile_height, tile_width, tile_height)
                            collidable_rects.append(rect)
                        if tile_props.get("climbable") is True:
                            rect = pygame.Rect(x*tile_width, y*tile_height, tile_width, tile_height)
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

    camera_x = 0
    camera_y = 0

    # --------------------------------
    # 4) PLAYER SETUP
    # --------------------------------
    # Use 61x96 bounding box
    player_width, player_height = 60, 96
    start_x, start_y = 64, 3072
    player_rect = pygame.Rect(start_x, start_y, player_width, player_height)

    # A) Load separate sprite sheets
    walk_left,  walk_right  = load_animation_frames(r"python\games\PlumberLite\Assets\player_walk.png",  9, 62, 96)
    idle_left,  idle_right  = load_animation_frames(r"python\games\PlumberLite\Assets\player_idle.png",  9, 64, 96)
    jump_left,  jump_right  = load_animation_frames(r"python\games\PlumberLite\Assets\player_jump.png",  2, 64, 96)
    climb_left, climb_right = load_animation_frames(r"python\games\PlumberLite\Assets\player_climb.png", 6, 64, 96)

    # B) Animation state
    player_state = "idle"  # or "jump", "climb"
    player_facing_left = True
    player_frame_index = 0
    player_anim_timer = 0
    # We can define a speed for each animation:
    idle_anim_speed  = 100  # ms per frame
    jump_anim_speed  = 80   # optional if you want frame0->frame1 timing
    climb_anim_speed = 120

    # Movement
    player_walk_speed = 5
    player_sprint_speed = 9
    gravity = 0.8
    jump_power = 15
    player_vel_y = 0
    on_ground = False
    on_ladder = False
    climb_speed_val = 4

    # Clouds
    clouds_offset_x = 0
    clouds_scroll_timer = 0
    clouds_scroll_interval = 120

    running = True
    while running:
        # Retrieve the current FPS
        fps = clock.get_fps()

        # Update the window caption with the FPS value
        # {:.2f} formats the number with 2 decimals
        pygame.display.set_caption(f"My Game - FPS: {fps:.2f}")
        
        dt = clock.tick(60)  # ms
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        # 5) Horizontal input
        current_speed = player_walk_speed
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            current_speed = player_sprint_speed

        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -current_speed
            player_facing_left = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = current_speed
            player_facing_left = False

        # Ladder detection
        on_ladder = False
        for lad_rect in climbable_rects:
            if player_rect.colliderect(lad_rect):
                on_ladder = True
                break

        # Jump logic
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and (on_ground or on_ladder):
            if on_ladder:
                on_ladder = False
            player_vel_y = -jump_power
            on_ground = False

        # Vertical
        if on_ladder:
            player_vel_y = 0
            dy = 0
            if (keys[pygame.K_DOWN] or keys[pygame.K_s]):
                dy = climb_speed_val
            elif (keys[pygame.K_UP] or keys[pygame.K_w]):
                dy = -climb_speed_val
        else:
            player_vel_y += gravity
            dy = player_vel_y

        # 6) Move & collisions (horizontal)
        player_rect.x += dx
        for c_rect in collidable_rects:
            if player_rect.colliderect(c_rect):
                if dx > 0:
                    player_rect.right = c_rect.left
                elif dx < 0:
                    player_rect.left = c_rect.right

        # Boundaries horizontally
        if player_rect.left < 0:
            player_rect.left = 0
        right_bound = map_width * tile_width
        if player_rect.right > right_bound:
            player_rect.right = right_bound

        # Move & collisions (vertical)
        on_ground = False
        player_rect.y += dy
        for c_rect in collidable_rects:
            if player_rect.colliderect(c_rect):
                if dy > 0:
                    player_rect.bottom = c_rect.top
                    player_vel_y = 0
                    on_ground = True
                elif dy < 0:
                    player_rect.top = c_rect.bottom
                    player_vel_y = 0

        # Bottom boundary
        bottom_boundary = map_height * tile_height
        if player_rect.top > bottom_boundary:
            # reset
            player_rect.x = start_x
            player_rect.y = start_y
            player_vel_y = 0
            on_ground = False

        # Camera
        camera_x = player_rect.centerx - screen_width//2
        camera_y = player_rect.centery - screen_height//2
        max_cam_x = (map_width * tile_width) - screen_width
        max_cam_y = (map_height * tile_height) - screen_height
        camera_x = max(0, min(camera_x, max_cam_x))
        camera_y = max(0, min(camera_y, max_cam_y))

        # 7) Update clouds
        clouds_scroll_timer += dt
        if clouds_scroll_timer >= clouds_scroll_interval:
            clouds_scroll_timer = 0
            # Cloud movment step
            clouds_offset_x += .1
            clouds_offset_x %= map_width

        # --------------------------------
        # 8) Determine player_state
        # --------------------------------
        if on_ladder:
            player_state = "climb"
        elif not on_ground:
            player_state = "jump"
        else:
            # on ground
            if dx != 0:
                # If you had a separate 'walk' sheet, you'd do: player_state = "walk"
                # But we only have idle for ground. We'll just reuse idle anim
                player_state = "walk"
            else:
                player_state = "idle"

        # --------------------------------
        # 9) Animate depending on state
        # --------------------------------
        if player_state == "idle":
            # cycle through 9 frames
            player_anim_timer += dt
            if player_anim_timer >= idle_anim_speed:
                player_anim_timer = 0
                player_frame_index += 1
                # wrap 0..8
                if player_frame_index > 8:
                    player_frame_index = 0

        elif player_state == "jump":
            # We have 2 frames:
            # Frame 0 => ascending? Frame 1 => while in air
            # or simpler approach: as soon as jump starts, show frame 0 for a short time, then frame 1
            # We'll do ascending vs descending:
            if player_vel_y < 0:
                # ascending => frame 0
                player_frame_index = 0
            else:
                # descending or in air => frame 1
                player_frame_index = 1

        elif player_state == "climb":
            # 6 frames
            # If no vertical input => freeze on frame 0
            if dy == 0:
                player_frame_index = 0
                player_anim_timer = 0
            else:
                # cycle frames 1..5
                player_anim_timer += dt
                if player_anim_timer >= climb_anim_speed:
                    player_anim_timer = 0
                    player_frame_index += 1
                    if player_frame_index < 1 or player_frame_index > 5:
                        player_frame_index = 1

        elif player_state == "walk":
            # 9 frames
            # If no horizontal input => go to idle
            if dx == 0:
                player_state = "idle"
            else:
                # cycle frames 1..5
                player_anim_timer += dt
                if player_anim_timer >= climb_anim_speed:
                    player_anim_timer = 0
                    player_frame_index += 1
                    if player_frame_index < 1 or player_frame_index > 8:
                        player_frame_index = 1


        # 10) Choose which frames array
        if player_state == "idle":
            frames_left  = idle_left
            frames_right = idle_right
        elif player_state == "walk":
            frames_left  = walk_left
            frames_right = walk_right
        elif player_state == "jump":
            frames_left  = jump_left
            frames_right = jump_right
        elif player_state == "climb":
            frames_left  = climb_left
            frames_right = climb_right
        else:
            # fallback
            frames_left  = idle_left
            frames_right = idle_right

        # clamp frame_index in range
        # for example, if 'jump' => 0..1 range
        if player_state == "jump" and player_frame_index > 1:
            player_frame_index = 1
        if player_state == "climb" and player_frame_index > 5:
            player_frame_index = 5
        if player_state == "walk"  and player_frame_index > 8:
            player_frame_index = 8
        if player_state == "idle"  and player_frame_index > 8:
            player_frame_index = 8

        # pick left vs right
        if player_facing_left:
            current_frame = frames_left[player_frame_index]
        else:
            current_frame = frames_right[player_frame_index]

        # Draw
        screen.fill((0,0,0))
        screen.blit(background_img, (0,0))

        # clouds layer
        if clouds_layer:
            for x,y,gid in clouds_layer:
                if gid == 0:
                    continue
                tile_img = tmx_data.get_tile_image_by_gid(gid)
                if tile_img:
                    tile_px = (x - clouds_offset_x) * tile_width
                    tile_py = y * tile_height
                    tile_px_mod = tile_px % (map_width * tile_width)
                    final_x = tile_px_mod - camera_x
                    final_y = tile_py - camera_y
                    screen.blit(tile_img, (final_x, final_y))

        # draw other layers (skip clouds_layer) ...
        for layer in tmx_data.visible_layers:
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
                            tile_px = x*tile_width
                            tile_py = y*tile_height
                            screen.blit(tile_image, (tile_px - camera_x, tile_py - camera_y))

        # Draw the player sprite
        px = player_rect.x - camera_x
        py = player_rect.y - camera_y
        screen.blit(current_frame, (px, py))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
