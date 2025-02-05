import pygame
import sys
import math
from pytmx import load_pygame, TiledImageLayer

def clamp_point(origin, target, max_dist):
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
    x1, y1 = start_pos
    x2, y2 = end_pos
    for i in range(steps + 1):
        t = i / steps
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        point_rect = pygame.Rect(x, y, 1, 1)
        for crect in collidable_rects:
            if point_rect.colliderect(crect):
                return (x, y)
    return None

def apply_rope_physics(px, py, vx, vy, anchor_x, anchor_y, rope_length):
    """
    Physics-based rope constraint:
      1) If distance > rope_length, clamp position to that circle.
      2) Remove radial velocity -> preserves tangential velocity (pendulum effect).
    """
    dx = px - anchor_x
    dy = py - anchor_y
    dist = math.hypot(dx, dy)

    if dist > rope_length and dist != 0:
        ratio = rope_length / dist
        px = anchor_x + dx * ratio
        py = anchor_y + dy * ratio

        # remove radial velocity
        radial_dir_x = dx / dist
        radial_dir_y = dy / dist
        dot = vx * radial_dir_x + vy * radial_dir_y
        radial_vx = dot * radial_dir_x
        radial_vy = dot * radial_dir_y
        vx -= radial_vx
        vy -= radial_vy

    return px, py, vx, vy

def collide_and_adjust(player_rect, vel_x, vel_y, collidable_rects):
    """
    Collide horizontally, then vertically, returning updated
    (player_rect, vel_x, vel_y, on_ground).
    """
    on_ground = False

    # HORIZONTAL
    player_rect.x += int(vel_x)
    for crect in collidable_rects:
        if player_rect.colliderect(crect):
            if vel_x > 0:  # moving right
                player_rect.right = crect.left
                vel_x = 0
            elif vel_x < 0:  # moving left
                player_rect.left = crect.right
                vel_x = 0

    # VERTICAL
    player_rect.y += int(vel_y)
    for crect in collidable_rects:
        if player_rect.colliderect(crect):
            if vel_y > 0:  # falling
                player_rect.bottom = crect.top
                vel_y = 0
                on_ground = True
            elif vel_y < 0:  # jumping up
                player_rect.top = crect.bottom
                vel_y = 0

    return player_rect, vel_x, vel_y, on_ground

def main():
    pygame.init()
    screen_width = 1200
    screen_height = 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Pendulum Rope + High Ground Friction Example")

    clock = pygame.time.Clock()

    # Load map
    tmx_data = load_pygame(r"python\games\PlumberLite\Assets\TestSet.tmx")
    tile_width = tmx_data.tilewidth
    tile_height = tmx_data.tileheight
    map_width = tmx_data.width
    map_height = tmx_data.height

    collidable_rects = []
    climbable_rects = []
    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'data'):
            for x, y, gid in layer:
                if gid == 0:
                    continue
                tile_props = tmx_data.get_tile_properties_by_gid(gid)
                if tile_props:
                    if tile_props.get("collision") is True:
                        rect = pygame.Rect(
                            x * tile_width, y * tile_height,
                            tile_width, tile_height
                        )
                        collidable_rects.append(rect)
                    if tile_props.get("climbable") is True:
                        rect = pygame.Rect(
                            x * tile_width, y * tile_height,
                            tile_width, tile_height
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

    camera_x = 0
    camera_y = 0

    # Player setup
    player_size = 32
    start_x, start_y = 64, 3072
    player_rect = pygame.Rect(start_x, start_y, player_size, player_size)

    # We'll store velocity in floats
    vel_x = 0.0
    vel_y = 0.0

    # Movement parameters
    accel = 0.4      # how quickly we accelerate left/right
    max_speed = 9
    # Distinguish friction for ground vs. air
    ground_friction = 0.5    # lower value means a quicker stop on ground
    air_friction = 0.98      # lower friction in air => preserve momentum

    gravity = 0.8
    jump_power = 15
    on_ground = False
    on_ladder = False
    climb_speed = 4

    # Rope
    rope_active = False
    rope_anchor = None
    rope_length = 0
    MAX_ROPE_DIST = 32 * 6
    RETRACT_EXTEND_SPEED = 3

    # New: limit how fast the rope can pull the player
    MAX_PULL_SPEED = 12.0  # tweak as desired

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Left click -> rope
                    mx, my = pygame.mouse.get_pos()
                    world_mx = mx + camera_x
                    world_my = my + camera_y

                    px_center = player_rect.centerx
                    py_center = player_rect.centery

                    # Just a simple "above" check (optional)
                    if world_my > py_center:
                        # skip if below
                        continue

                    # clamp
                    clamped = clamp_point(
                        (px_center, py_center),
                        (world_mx, world_my),
                        MAX_ROPE_DIST
                    )
                    hit_pt = raycast_to_collidable((px_center, py_center), clamped, collidable_rects)
                    if hit_pt:
                        rope_active = True
                        rope_anchor = hit_pt
                        dx = px_center - hit_pt[0]
                        dy = py_center - hit_pt[1]
                        rope_length = math.hypot(dx, dy)
                elif event.button == 3:
                    # right click -> detach rope
                    rope_active = False
                    rope_anchor = None

        # Key input
        keys = pygame.key.get_pressed()

        # Horizontal movement by acceleration
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            vel_x -= accel
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            vel_x += accel

        # Limit speed
        if abs(vel_x) > max_speed:
            vel_x = max_speed if vel_x > 0 else -max_speed

        # Jump
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and (on_ground or on_ladder):
            on_ladder = False
            vel_y = -jump_power
            on_ground = False

        # Rope retraction
        if rope_active and rope_anchor:
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                rope_length = max(32, rope_length - RETRACT_EXTEND_SPEED)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                rope_length = min(MAX_ROPE_DIST, rope_length + RETRACT_EXTEND_SPEED)

        # Ladder or gravity
        if on_ladder:
            vel_y = 0
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                vel_y = climb_speed
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                vel_y = -climb_speed
        else:
            vel_y += gravity

        # Ground vs. Air friction
        if on_ground:
            # If the player is on the ground and not pressing horizontal keys,
            # quickly reduce vel_x => no sliding
            if not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]):
                vel_x *= ground_friction
                if abs(vel_x) < 0.5:
                    vel_x = 0
        else:
            vel_x *= air_friction

        # 1) Collision pass (for normal movement)
        player_rect, vel_x, vel_y, on_ground = collide_and_adjust(
            player_rect, vel_x, vel_y, collidable_rects
        )

        # 2) Rope physics
        if rope_active and rope_anchor:
            px_center = player_rect.centerx
            py_center = player_rect.centery
            px_center, py_center, vel_x, vel_y = apply_rope_physics(
                px_center, py_center,
                vel_x, vel_y,
                rope_anchor[0], rope_anchor[1],
                rope_length
            )

            # --- NEW: Clamp maximum rope pull speed ---
            speed_sq = vel_x*vel_x + vel_y*vel_y
            if speed_sq > MAX_PULL_SPEED*MAX_PULL_SPEED:
                factor = MAX_PULL_SPEED / math.sqrt(speed_sq)
                vel_x *= factor
                vel_y *= factor
            # ------------------------------------------

            # Reposition the player rect
            player_rect.centerx = int(px_center)
            player_rect.centery = int(py_center)

            # second collision pass
            player_rect, vel_x, vel_y, on_ground = collide_and_adjust(
                player_rect, vel_x, vel_y, collidable_rects
            )

        # Check ladder
        on_ladder = False
        for lad in climbable_rects:
            if player_rect.colliderect(lad):
                on_ladder = True
                break

        # Fell off
        bottom_boundary = map_height*tile_height
        if player_rect.top > bottom_boundary:
            player_rect.x = start_x
            player_rect.y = start_y
            vel_x = 0
            vel_y = 0
            on_ground = False
            rope_active = False
            rope_anchor = None

        # Camera
        camera_x = player_rect.centerx - screen_width//2
        camera_y = player_rect.centery - screen_height//2
        max_cx = (map_width*tile_width) - screen_width
        max_cy = (map_height*tile_height) - screen_height
        camera_x = max(0, min(camera_x, max_cx))
        camera_y = max(0, min(camera_y, max_cy))

        # Render
        screen.fill((0, 0, 0))

        for layer in tmx_data.visible_layers:
            if isinstance(layer, TiledImageLayer):
                if layer.image:
                    screen.blit(layer.image, (layer.x - camera_x, layer.y - camera_y))
            elif hasattr(layer, 'data'):
                for x, y, gid in layer:
                    if gid != 0:
                        tile_image = tmx_data.get_tile_image_by_gid(gid)
                        if tile_image:
                            tile_px = x*tile_width
                            tile_py = y*tile_height
                            screen.blit(tile_image, (tile_px - camera_x, tile_py - camera_y))

        # rope line
        if rope_active and rope_anchor:
            anchor_scr_x = rope_anchor[0] - camera_x
            anchor_scr_y = rope_anchor[1] - camera_y
            pctrx = player_rect.centerx - camera_x
            pctry = player_rect.centery - camera_y
            pygame.draw.line(screen, (255, 255, 255), (pctrx, pctry), (anchor_scr_x, anchor_scr_y), 2)

        # player
        px = player_rect.x - camera_x
        py = player_rect.y - camera_y
        pygame.draw.rect(screen, (255,0,0), (px, py, player_size, player_size))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
