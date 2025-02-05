import pygame
import sys
import math
from pytmx import load_pygame, TiledImageLayer

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------

def clamp_point(origin, target, max_dist):
    """
    Clamps 'target' so that it's no more than 'max_dist' away from 'origin'.
    Returns the clamped (x, y) point.
    """
    ox, oy = origin
    tx, ty = target
    dx = tx - ox
    dy = ty - oy
    cur_dist = math.hypot(dx, dy)
    if cur_dist > max_dist:
        ratio = max_dist / cur_dist
        tx = ox + dx * ratio
        ty = oy + dy * ratio
    return (tx, ty)


def raycast_to_collidable(start_pos, end_pos, collidable_rects, steps=100):
    """
    Naive line-cast from start_pos -> end_pos.
    Returns the first collision point or None if no hit.
    Subdivides the line into 'steps' and checks collisions at each step.
    """
    x1, y1 = start_pos
    x2, y2 = end_pos
    for i in range(steps + 1):
        t = i / steps
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        # A tiny rect to represent the point
        point_rect = pygame.Rect(x, y, 1, 1)
        for crect in collidable_rects:
            if point_rect.colliderect(crect):
                return (x, y)
    # No hit
    return None


def apply_rope_physics(px, py, vx, vy, anchor_x, anchor_y, rope_length):
    """
    Physics-based rope constraint:
      1) If distance from anchor > rope_length, clamp position to that circle.
      2) Remove radial velocity so only tangential velocity remains (swing).
    Returns updated (px, py, vx, vy).
    """
    dx = px - anchor_x
    dy = py - anchor_y
    dist = math.hypot(dx, dy)

    if dist > rope_length and dist != 0:
        # 1) Clamp the position
        ratio = rope_length / dist
        px = anchor_x + dx * ratio
        py = anchor_y + dy * ratio

        # 2) Remove radial velocity
        radial_dir_x = dx / dist
        radial_dir_y = dy / dist
        dot = vx * radial_dir_x + vy * radial_dir_y
        radial_vx = dot * radial_dir_x
        radial_vy = dot * radial_dir_y
        vx -= radial_vx
        vy -= radial_vy

    return px, py, vx, vy


def main():
    pygame.init()
    screen_width = 1200
    screen_height = 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Grapple + Ladder + Swinging Physics + Retract/Extend")

    clock = pygame.time.Clock()

    # 1) Load your Tiled map
    tmx_data = load_pygame(r"python\games\PlumberLite\Assets\TestSet.tmx")

    tile_width = tmx_data.tilewidth
    tile_height = tmx_data.tileheight
    map_width = tmx_data.width    # number of tiles horizontally
    map_height = tmx_data.height  # number of tiles vertically

    # 2) Build lists for "collidable" rects (solid ground) and "climbable" rects (ladders)
    collidable_rects = []
    climbable_rects = []

    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'data'):  # Tile layer
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
        elif hasattr(layer, 'objects'):  # Object layer
            for obj in layer.objects:
                props = obj.properties
                if props.get("collision") is True:
                    r = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                    collidable_rects.append(r)
                if props.get("climbable") is True:
                    r = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                    climbable_rects.append(r)

    # 3) Basic camera setup
    camera_x = 0
    camera_y = 0

    # 4) Player setup
    player_size = 32
    start_x, start_y = 64, 3072

    # Instead of storing just dx/dy, we'll track float positions + velocity:
    player_x = float(start_x)
    player_y = float(start_y)
    player_vel_x = 0.0
    player_vel_y = 0.0

    # We'll keep a rect around for collisions, but it updates from (player_x, player_y).
    player_rect = pygame.Rect(player_x, player_y, player_size, player_size)
    player_color = (255, 0, 0)

    # Movement speeds
    player_walk_speed = 5
    player_sprint_speed = 9

    # Gravity-related variables
    gravity = 0.8
    jump_power = 15
    on_ground = False

    # Ladder-related
    on_ladder = False
    climb_speed = 4

    # Rope
    rope_active = False
    rope_anchor = None
    rope_length = 0
    MAX_ROPE_DIST = 32 * 6

    running = True
    while running:
        clock.tick(60)

        # 1) EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Left click -> shoot grappling hook
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    world_mx = mx + camera_x
                    world_my = my + camera_y
                    player_center = (player_x + player_size/2, player_y + player_size/2)

                    # clamp target to MAX_ROPE_DIST
                    clamped_target = clamp_point(player_center, (world_mx, world_my), MAX_ROPE_DIST)
                    hit_point = raycast_to_collidable(player_center, clamped_target, collidable_rects)
                    if hit_point:
                        rope_active = True
                        rope_anchor = hit_point
                        dx = player_center[0] - hit_point[0]
                        dy = player_center[1] - hit_point[1]
                        rope_length = math.hypot(dx, dy)

                # Right click -> detach rope
                if event.button == 3:
                    rope_active = False
                    rope_anchor = None

        # 2) INPUT
        keys = pygame.key.get_pressed()

        # Decide horizontal speed (walk vs. sprint)
        current_speed = player_walk_speed
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            current_speed = player_sprint_speed

        # We'll set horizontal velocity each frame from input
        desired_vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            desired_vel_x = -current_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            desired_vel_x = current_speed

        player_vel_x = desired_vel_x

        # Jump if on ground or on ladder
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and (on_ground or on_ladder):
            on_ladder = False  # let go of ladder
            player_vel_y = -jump_power
            on_ground = False

        # Retract/Extend rope if active
        if rope_active and rope_anchor:
            retract_speed = 3
            # Up/W = retract
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                rope_length -= retract_speed
            # Down/S = extend
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                rope_length += retract_speed
            # clamp
            rope_length = max(0, min(rope_length, MAX_ROPE_DIST))

        # Ladder or gravity
        if on_ladder:
            player_vel_y = 0
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                player_vel_y = climb_speed
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                player_vel_y = -climb_speed
        else:
            # Normal gravity
            player_vel_y += gravity

        # 3) UPDATE POSITION by velocity
        # We'll do horizontal & vertical collision in two passes
        old_x, old_y = player_x, player_y

        # Move horizontally
        player_x += player_vel_x
        player_rect.x = int(player_x)
        # Horizontal collision
        for crect in collidable_rects:
            if player_rect.colliderect(crect):
                if player_vel_x > 0:  # moving right
                    player_rect.right = crect.left
                    player_x = player_rect.x
                    player_vel_x = 0
                elif player_vel_x < 0:  # moving left
                    player_rect.left = crect.right
                    player_x = player_rect.x
                    player_vel_x = 0

        # Move vertically
        player_y += player_vel_y
        player_rect.y = int(player_y)
        # Vertical collision
        on_ground = False
        for crect in collidable_rects:
            if player_rect.colliderect(crect):
                if player_vel_y > 0:  # falling
                    player_rect.bottom = crect.top
                    player_y = player_rect.y
                    player_vel_y = 0
                    on_ground = True
                elif player_vel_y < 0:  # jumping
                    player_rect.top = crect.bottom
                    player_y = player_rect.y
                    player_vel_y = 0

        # Update final player_x, player_y from rect
        player_x = float(player_rect.x)
        player_y = float(player_rect.y)

        # Check ladder
        on_ladder = False
        for lad in climbable_rects:
            if player_rect.colliderect(lad):
                on_ladder = True
                break

        # If fell off map
        bottom_boundary = map_height * tile_height
        if player_rect.top > bottom_boundary:
            player_rect.x = start_x
            player_rect.y = start_y
            player_x = float(start_x)
            player_y = float(start_y)
            player_vel_x = 0
            player_vel_y = 0
            on_ground = False
            rope_active = False
            rope_anchor = None

        # ---------------------------------------
        # 4) APPLY ROPE PHYSICS IF ACTIVE
        # ---------------------------------------
        if rope_active and rope_anchor:
            anchor_x, anchor_y = rope_anchor
            # Convert player top-left -> center
            px_center = player_x + player_size / 2
            py_center = player_y + player_size / 2

            # apply swinging
            px_center, py_center, player_vel_x, player_vel_y = apply_rope_physics(
                px_center, py_center,
                player_vel_x, player_vel_y,
                anchor_x, anchor_y,
                rope_length
            )

            # reposition rect so top-left lines up with new center
            player_x = px_center - player_size / 2
            player_y = py_center - player_size / 2
            player_rect.x = int(player_x)
            player_rect.y = int(player_y)

        # Horizontal clamp
        if player_rect.left < 0:
            player_rect.left = 0
            player_x = float(player_rect.left)
        right_boundary = map_width * tile_width
        if player_rect.right > right_boundary:
            player_rect.right = right_boundary
            player_x = float(player_rect.left)

        # 5) CAMERA
        camera_x = player_rect.centerx - screen_width // 2
        camera_y = player_rect.centery - screen_height // 2
        max_cam_x = (map_width*tile_width) - screen_width
        max_cam_y = (map_height*tile_height) - screen_height
        camera_x = max(0, min(camera_x, max_cam_x))
        camera_y = max(0, min(camera_y, max_cam_y))

        # 6) RENDER
        screen.fill((0,0,0))

        # Tiled layers
        for layer in tmx_data.visible_layers:
            if isinstance(layer, TiledImageLayer):
                if layer.image:
                    screen.blit(layer.image, (layer.x - camera_x, layer.y - camera_y))
            elif hasattr(layer, 'data'):
                for x, y, gid in layer:
                    if gid != 0:
                        tile_image = tmx_data.get_tile_image_by_gid(gid)
                        if tile_image:
                            tile_px = x * tile_width
                            tile_py = y * tile_height
                            screen.blit(tile_image, (tile_px - camera_x, tile_py - camera_y))

        # Rope line if active
        if rope_active and rope_anchor:
            anchor_scr_x = rope_anchor[0] - camera_x
            anchor_scr_y = rope_anchor[1] - camera_y
            player_ctr_x = (player_x + player_size/2) - camera_x
            player_ctr_y = (player_y + player_size/2) - camera_y
            pygame.draw.line(
                screen,
                (255,255,255),
                (player_ctr_x, player_ctr_y),
                (anchor_scr_x, anchor_scr_y),
                2
            )

        # Aiming line (green)
        mx, my = pygame.mouse.get_pos()
        world_mx = mx + camera_x
        world_my = my + camera_y
        center_player = (player_x + player_size/2, player_y + player_size/2)
        clamped = clamp_point(center_player, (world_mx, world_my), MAX_ROPE_DIST)
        cmx = clamped[0] - camera_x
        cmy = clamped[1] - camera_y
        pygame.draw.line(
            screen, (0,255,0),
            (player_rect.centerx - camera_x, player_rect.centery - camera_y),
            (cmx, cmy),
            1
        )

        # Player
        screen_x = player_rect.x - camera_x
        screen_y = player_rect.y - camera_y
        pygame.draw.rect(screen, (255,0,0), (screen_x, screen_y, player_size, player_size))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
