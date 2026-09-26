"""Safe respawn placement and player recovery after defeat."""
import pygame
from core.config import RESPAWN_IFRAMES

def safe_respawn_position(region_id, region, enemies):
    source = {"forest": "village", "desert": "forest"}.get(region_id)
    default = (512, 288) if region_id == "home" else (1024, 576)
    preferred = region.get("spawn", {}).get(source, default) if source else default
    candidates = [preferred]
    for distance in (24, 48, 72, 96, 128):
        candidates.extend((preferred[0] + dx, preferred[1] + dy)
                          for dx, dy in ((distance, 0), (-distance, 0), (0, distance), (0, -distance)))
    width, height = region["terrain"].get_size()
    for x, y in candidates:
        box = pygame.Rect(round(x - 13), round(y - 9), 26, 18)
        if not (18 <= x <= width - 18 and 38 <= y <= height - 12):
            continue
        if any(box.colliderect(obstacle) for obstacle in region["obstacles"]):
            continue
        if any(box.colliderect(enemy.hitbox.inflate(18, 18)) for enemy in enemies if enemy.state != "DEAD"):
            continue
        return float(x), float(y)
    return float(preferred[0]), float(preferred[1])

def restore_player_after_death(player, region_id, region, enemies):
    player.x, player.y = safe_respawn_position(region_id, region, enemies)
    player.hp, player.sp = player.max_hp, player.max_sp
    player.attack_timer = player.attack_cooldown_timer = 0
    player.dash_timer = player.dash_cooldown = player.dash_iframes = 0
    player.invulnerability_timer = RESPAWN_IFRAMES
    player.knockback_x = player.knockback_y = 0.0
    player.knockback_frames = 0
    player.dash_feedback_timer = 0
    player.dash_feedback_kind = ""
    player.attack_serial += 1
    return player.x, player.y
