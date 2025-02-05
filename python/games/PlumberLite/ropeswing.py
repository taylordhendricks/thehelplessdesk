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
                # Return collision point
                return (x, y)
    # No hit
    return None

def apply_rope_constraint(player_rect, anchor_pos, rope_length):
    """
    Force the player's center to remain within 'rope_length' distance of 'anchor_pos'.
    This simplistic approach directly clamps position (no swinging physics).
    """
    px, py = player_rect.center
    ax, ay = anchor_pos
    dx = px - ax
    dy = py - ay
    dist = math.hypot(dx, dy)
    if dist > rope_length:
        ratio = rope_length / dist
        clamped_x = ax + dx * ratio
        clamped_y = ay + dy * ratio
        # Update player center
        player_rect.center = (clamped_x, clamped_y)
    return player_rect

def main():
    pygame.init()
    screen_width = 1200
    screen_height = 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Grapple + Ladder + Retract/Extend Rope")

    clock = pygame.time.Clock()

    # 1) Load your Tiled map
    tmx_data = load_pygame(r"python\games\PlumberLite\Assets\TestSet.tmx")

    tile_width = tmx_data.tilewidth
    tile_height = tmx_data.tileheight
    map_width = tmx_data.width   # number of tiles horizontally
    map_height = tmx_data.height # number of tiles vertically

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
                # collision object
                if props.get("collision") is True:
                    r = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                    collidable_rects.append(r)
                # ladder object
                if props.get("climbable") is True:
                    r = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                    climbable_rects.append(r)

    # 3) Basic camera setup
    camera_x = 0
    camera_y = 0

    # 4) Player setup
    player_size = 32
    start_x, start_y = 64, 3072
    player_rect = pygame.Rect(start_x, start_y, player_size, player_size)
    player_color = (255, 0, 0)

    # Movement speeds
    player_walk_speed = 5
    player_sprint_speed = 9

    # Gravity-related variables
    gravity = 0.8
    jump_power = 15
    player_vel_y = 0
    on_ground = False

    # Ladder-related variables
    on_ladder = False
    climb_speed = 4

    # -------------------
    # Grappling Hook Vars
    # -------------------
    rope_active = False
    rope_anchor = None
    rope_length = 0

    # We'll define the MAX_ROPE_DIST to 6 tiles = 192 px
    MAX_ROPE_DIST = 32 * 6

    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Check mouse input for grappling
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Left click -> shoot grappling hook
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    # Convert mouse to world coords
                    world_mx = mx + camera_x
                    world_my = my + camera_y

                    # We'll clamp the mouse point to MAX_ROPE_DIST from player center
                    player_center = (player_rect.centerx, player_rect.centery)
                    clamped_target = clamp_point(player_center, (world_mx, world_my), MAX_ROPE_DIST)

                    # Now do a raycast from the player to clamped_target
                    hit_point = raycast_to_collidable(
                        player_center, 
                        clamped_target, 
                        collidable_rects
                    )
                    if hit_point:
                        # Attach the rope
                        rope_active = True
                        rope_anchor = hit_point
                        # Distance from player to anchor
                        dx = player_center[0] - hit_point[0]
                        dy = player_center[1] - hit_point[1]
                        dist = math.hypot(dx, dy)
                        rope_length = dist  # we already clamped, so dist <= 192
                # Right click -> detach rope
                if event.button == 3:
                    rope_active = False
                    rope_anchor = None

        # --- KEY INPUT ---
        keys = pygame.key.get_pressed()

        # Determine current horizontal speed (walking vs. sprinting)
        current_speed = player_walk_speed
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            current_speed = player_sprint_speed

        # Horizontal movement
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -current_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = current_speed

        # Check if on ladder
        on_ladder = False
        for ladder_rect in climbable_rects:
            if player_rect.colliderect(ladder_rect):
                on_ladder = True
                break

        # Jumping logic (jump if on ground OR on a ladder)
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and (on_ground or on_ladder):
            # If on a ladder, jump = let go + jump
            if on_ladder:
                on_ladder = False
            player_vel_y = -jump_power
            on_ground = False

        # --- VERTICAL MOVEMENT ---
        if on_ladder:
            player_vel_y = 0  # zero out gravity
            dy = 0

            if (keys[pygame.K_DOWN] or keys[pygame.K_s]):
                if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
                    # let go of ladder, apply downward velocity
                    on_ladder = False
                    player_vel_y += 15
                    dy = player_vel_y
                else:
                    dy = climb_speed
            elif (keys[pygame.K_UP] or keys[pygame.K_w]):
                if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
                    # let go of ladder, apply upward velocity
                    on_ladder = False
                    player_vel_y -= 15
                    dy = player_vel_y
                else:
                    dy = -climb_speed
        else:
            # Normal gravity-based movement
            player_vel_y += gravity
            dy = player_vel_y

        # --- MOVE THE PLAYER (HORIZONTAL FIRST) ---
        player_rect.x += dx
        # Collision checks horizontally
        for rect in collidable_rects:
            if player_rect.colliderect(rect):
                if dx > 0:  # moving right
                    player_rect.right = rect.left
                elif dx < 0:  # moving left
                    player_rect.left = rect.right

        # Horizontal boundary clamp
        if player_rect.left < 0:
            player_rect.left = 0
        right_boundary = map_width * tile_width
        if player_rect.right > right_boundary:
            player_rect.right = right_boundary

        # --- MOVE THE PLAYER (VERTICAL) ---
        on_ground = False
        player_rect.y += dy
        for rect in collidable_rects:
            if player_rect.colliderect(rect):
                if dy > 0:  # falling down
                    player_rect.bottom = rect.top
                    player_vel_y = 0
                    on_ground = True
                elif dy < 0:  # jumping up
                    player_rect.top = rect.bottom
                    player_vel_y = 0

        # Bottom boundary check (if player falls off map)
        bottom_boundary = map_height * tile_height
        if player_rect.top > bottom_boundary:
            # Reset the player
            player_rect.x = start_x
            player_rect.y = start_y
            player_vel_y = 0
            on_ground = False
            # Also reset rope
            rope_active = False
            rope_anchor = None

        # --------------------------------
        # RETRACT/EXTEND ROPE
        # --------------------------------
        if rope_active and rope_anchor:
            # Press Up/W to retract, Down/S to extend
            retract_speed = 3
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                rope_length -= retract_speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                rope_length += retract_speed

            # Clamp rope_length between 0 and MAX_ROPE_DIST
            rope_length = max(0, min(rope_length, MAX_ROPE_DIST))

        # --------------------------------
        # APPLY ROPE CONSTRAINT IF ACTIVE
        # --------------------------------
        if rope_active and rope_anchor:
            player_rect = apply_rope_constraint(player_rect, rope_anchor, rope_length)

        # --- CAMERA ---
        camera_x = player_rect.centerx - screen_width // 2
        camera_y = player_rect.centery - screen_height // 2
        max_camera_x = map_width * tile_width - screen_width
        max_camera_y = map_height * tile_height - screen_height
        camera_x = max(0, min(camera_x, max_camera_x))
        camera_y = max(0, min(camera_y, max_camera_y))

        # --- DRAW ---
        screen.fill((0, 0, 0))

        # Draw Tiled layers
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

        # 1) Draw the rope line if active
        if rope_active and rope_anchor:
            anchor_x_screen = rope_anchor[0] - camera_x
            anchor_y_screen = rope_anchor[1] - camera_y
            player_center_x_screen = player_rect.centerx - camera_x
            player_center_y_screen = player_rect.centery - camera_y
            pygame.draw.line(
                screen,
                (255, 255, 255),  # rope color
                (player_center_x_screen, player_center_y_screen),
                (anchor_x_screen, anchor_y_screen),
                2
            )

        # 2) Draw an indicator line from player to (clamped) mouse position
        mx, my = pygame.mouse.get_pos()
        player_center = (player_rect.centerx, player_rect.centery)
        world_mx = mx + camera_x
        world_my = my + camera_y
        # clamp to 6 tiles distance
        clamped_mouse_world = clamp_point(player_center, (world_mx, world_my), MAX_ROPE_DIST)
        cmx_screen = clamped_mouse_world[0] - camera_x
        cmy_screen = clamped_mouse_world[1] - camera_y
        pygame.draw.line(
            screen,
            (0, 255, 0),  # green line for direction
            (player_rect.centerx - camera_x, player_rect.centery - camera_y),
            (cmx_screen, cmy_screen),
            1
        )

        # 3) Draw the player
        screen_x = player_rect.x - camera_x
        screen_y = player_rect.y - camera_y
        pygame.draw.rect(screen, player_color, (screen_x, screen_y, player_size, player_size))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
