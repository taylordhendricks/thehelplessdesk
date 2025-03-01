import pygame
import sys
from pytmx import load_pygame

def main():
    pygame.init()
    screen_width = 1200
    screen_height = 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Tiled Map RPG")

    clock = pygame.time.Clock()

    # Load the Tiled map
    tmx_data = load_pygame(r"python\games\PlumberLite\Assets\FallGame.tmx")

    tile_width = tmx_data.tilewidth
    tile_height = tmx_data.tileheight
    map_width = tmx_data.width
    map_height = tmx_data.height

    # 1) Start at 12:00 noon => plenty of full daylight before 17:00
    game_time = 12 * 60  
    minutes_per_tick = 0.1

    # Fonts
    font = pygame.font.Font(None, 36)

    # Player
    player_size = 32
    player_pos = [16608, 16608]
    player_rect = pygame.Rect(player_pos[0], player_pos[1], player_size, player_size)
    player_speed = 5

    # Load Light Sources
    light_sources = []
    for obj in tmx_data.objects:
        if "light_source" in obj.properties:
            light_radius = int(obj.properties["light_source"])
            light_sources.append((obj.x, obj.y, light_radius))

    print("Loaded Light Sources:", light_sources)

    # Collision
    collision_map = {}
    for layer in tmx_data.visible_layers:
        if not hasattr(layer, 'data'):
            continue
        for x, y, gid in layer:
            if gid == 0:
                continue
            tile_props = tmx_data.get_tile_properties_by_gid(gid)
            if tile_props and tile_props.get("collision") is True:
                collision_map[(x, y)] = pygame.Rect(
                    x * tile_width, y * tile_height, tile_width, tile_height
                )

    running = True
    while running:
        clock.tick(120)
        # Advance time
        game_time += minutes_per_tick
        if game_time >= 24 * 60:
            game_time = 0  # wrap at midnight

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Movement
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -player_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = player_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -player_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = player_speed

        # Collisions X
        new_rect = player_rect.move(dx, 0)
        if not any(new_rect.colliderect(r) for r in collision_map.values()):
            player_rect.x += dx
        # Collisions Y
        new_rect = player_rect.move(0, dy)
        if not any(new_rect.colliderect(r) for r in collision_map.values()):
            player_rect.y += dy

        # Camera
        camera_x = player_rect.centerx - screen_width // 2
        camera_y = player_rect.centery - screen_height // 2
        camera_x = max(0, min(camera_x, map_width * tile_width - screen_width))
        camera_y = max(0, min(camera_y, map_height * tile_height - screen_height))

        # Clear
        screen.fill((0,0,0))

        # Visible tile range
        start_x = max(0, camera_x // tile_width)
        end_x   = min(map_width, (camera_x + screen_width)//tile_width + 1)
        start_y = max(0, camera_y // tile_height)
        end_y   = min(map_height, (camera_y + screen_height)//tile_height + 1)

        # Layers before player
        for layer in tmx_data.visible_layers:
            if not hasattr(layer, 'data'):
                continue
            if layer.name == "Player_Layer":
                break
            for x in range(start_x, end_x):
                for y in range(start_y, end_y):
                    gid = layer.data[y][x]
                    if gid != 0:
                        tile_image = tmx_data.get_tile_image_by_gid(gid)
                        if tile_image:
                            screen.blit(tile_image, (x*tile_width - camera_x, y*tile_height - camera_y))

        # Player
        screen_x = player_rect.x - camera_x
        screen_y = player_rect.y - camera_y
        pygame.draw.rect(screen, (255,0,0), (screen_x, screen_y, player_size, player_size))

        # Layers after player
        draw_player = False
        for layer in tmx_data.visible_layers:
            if layer.name == "Player_Layer":
                draw_player = True
                continue
            if not hasattr(layer, 'data'):
                continue
            if not draw_player:
                continue
            for x in range(start_x, end_x):
                for y in range(start_y, end_y):
                    gid = layer.data[y][x]
                    if gid != 0:
                        tile_image = tmx_data.get_tile_image_by_gid(gid)
                        if tile_image:
                            screen.blit(tile_image, (x*tile_width - camera_x, y*tile_height - camera_y))

        # Light Map
        light_map = create_light_map(screen_width, screen_height, light_sources, camera_x, camera_y, game_time)
        light_map = blur_surface(light_map, amount=2)
        screen.blit(light_map, (0, 0))

        # Clock
        draw_clock(screen, font, game_time)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

def extendedDayNightFactor(game_time):
    """
    0 => full day, 1 => full night
    - Day: 8->17 => factor=0
    - Dusk: 17->20 => 0..1
    - Night: 20->5 => 1
    - Dawn: 5->8 => 1..0
    """
    hour = (game_time / 60.0) % 24.0

    # Dusk: 17->20 => 0..1
    if 17.0 <= hour < 20.0:
        prog = (hour - 17.0)/3.0  # 0..1 over 3 hours
        return prog
    # Night: 20->5 => factor=1
    elif hour >= 20.0 or hour < 5.0:
        return 1.0
    # Dawn: 5->8 => 1..0
    elif 5.0 <= hour < 8.0:
        dawn_prog = (hour - 5.0)/3.0  # 0..1
        return 1.0 - dawn_prog
    # Day: 8->17 => factor=0
    else:
        return 0.0

def create_light_map(width, height, light_sources, cx, cy, game_time):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)

    df = extendedDayNightFactor(game_time)
    max_alpha = 200
    dark_alpha = int(max_alpha * df)
    surf.fill((0,0,0,dark_alpha))

    for (lx,ly,radius) in light_sources:
        sx = lx - cx
        sy = ly - cy
        draw_light_on_map(surf, sx, sy, radius)

    # Debug in console to see what's happening
    hour_f = (game_time/60.0)%24.0
    print(f"H={hour_f:.2f} Factor={df:.2f} alpha={dark_alpha}")

    return surf

def draw_light_on_map(surface, x, y, radius):
    """Center fully removes darkness => never extinguish."""
    light_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)

    # from center=0 out to radius
    for r in range(0, radius, 2):
        alpha = int(255 * (1.0 - (r/float(radius))))
        pygame.draw.circle(light_surf, (0,0,0,alpha), (radius, radius), r)

    surface.blit(light_surf, (x - radius, y - radius), special_flags=pygame.BLEND_RGBA_SUB)

def blur_surface(surface, amount=2):
    for _ in range(amount):
        surface.blit(surface, (1,0), special_flags=pygame.BLEND_RGBA_ADD)
        surface.blit(surface, (-1,0), special_flags=pygame.BLEND_RGBA_ADD)
        surface.blit(surface, (0,1), special_flags=pygame.BLEND_RGBA_ADD)
        surface.blit(surface, (0,-1), special_flags=pygame.BLEND_RGBA_ADD)
    return surface

def draw_clock(screen, font, game_time):
    hour_float = (game_time/60.0) % 24.0
    hour_i = int(hour_float)
    minute_i = int((hour_float-hour_i)*60)
    label = f"{hour_i:02}:{minute_i:02}"
    text = font.render(label, True, (255,255,255))
    screen.blit(text, (10,10))

if __name__ == "__main__":
    main()
