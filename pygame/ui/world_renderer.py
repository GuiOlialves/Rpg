"""Rendering of region layers, actors, exits and debug overlays."""
import pygame
import ambient
import environment
from core.config import VIEW
from entities.npc import nearest
from ui.hud import draw_key_prompt, draw_panel

def draw_world(canvas, region, font, camera, player=None, enemies=None, drops=None,
               debug=False, show_controls=True, interaction_context=None, scene_actors=(),
               show_banner=True):
    canvas.blit(region["terrain"], (-camera[0], -camera[1]))
    ambient.draw_water(canvas,region,camera,pygame.time.get_ticks())
    houses, objects, nature = region["houses"], region["objects"], region["nature"]
    entities = [(y + im.get_height() - 10, im, (x, y)) for im, (x, y) in nature + objects + houses]
    for obj in region.get('scenery',[]):
        entities.append((obj.depth,'scenery',obj))
    # Sombras no chão, antes dos corpos e das copas; nunca sobre a interface.
    for actor in ([player] if player else []) + list(enemies or []) + region.get('npcs',[]) + list(scene_actors):
        if getattr(actor, 'has_embedded_shadow', False):
            continue
        radius=getattr(actor,'config',{}).get('hitbox_radius',17)
        environment.shadow(canvas,(actor.x-camera[0],actor.y-camera[1]),round(radius*1.6),10,38)
    if player is not None:
        entities.append((player.y, "player", player))
    for enemy in enemies or []:
        entities.append((enemy.y, "enemy", enemy))
    for drop in drops or []:
        entities.append((drop.y, "drop", drop))
    for obj in region.get("interactables", []):
        entities.append((getattr(obj, "visual_depth", obj.y), "interactable", obj))
    for actor in scene_actors:
        entities.append((actor.y, "npc", actor))
    for npc in region.get("npcs", []):
        entities.append((npc.y, "npc", npc))
    for _, image, pos in sorted(entities, key=lambda entry: entry[0]):
        if image == 'scenery':
            pos.draw(canvas,camera,player)
        elif image == "player" or image == "enemy" or image == "drop" or image == "npc" or image == "interactable":
            pos.draw(canvas, camera)
        else:
            canvas.blit(image, (pos[0] - camera[0], pos[1] - camera[1]))
    ambient.draw(canvas,region,camera,pygame.time.get_ticks())
    if region.get("lighting") is not None:
        canvas.blit(region["lighting"], (-camera[0], -camera[1]))
    if debug:
        if player is not None:
            pygame.draw.rect(canvas, (75, 231, 247), player.hitbox.move(-camera[0], -camera[1]), 2)
            if player.attack_box.width:
                pygame.draw.rect(canvas, (255, 250, 112), player.attack_box.move(-camera[0], -camera[1]), 2)
        for enemy in enemies or []:
            pygame.draw.rect(canvas, (235, 75, 75), enemy.hitbox.move(-camera[0], -camera[1]), 1)
            pygame.draw.rect(canvas, (245, 220, 90), enemy.hurtbox.move(-camera[0], -camera[1]), 1)
            if enemy.attack_box().width:
                pygame.draw.rect(canvas, (255, 84, 83), enemy.attack_box().move(-camera[0], -camera[1]), 2)
            if enemy.attack_action == "aoe" and enemy.attack_phase == "windup":
                pygame.draw.circle(canvas, (255, 84, 83), (round(enemy.x - camera[0]), round(enemy.y - camera[1])), 65, 1)
            if enemy.attack_action == "charge" and enemy.attack_phase == "windup":
                dx, dy = enemy.attack_direction
                pygame.draw.line(canvas, (255, 84, 83), (round(enemy.x - camera[0]), round(enemy.y - camera[1])),
                                 (round(enemy.x + dx * 168 - camera[0]), round(enemy.y + dy * 168 - camera[1])), 2)
            pygame.draw.circle(canvas, (240, 145, 70), (round(enemy.spawn_x - camera[0]), round(enemy.spawn_y - camera[1])), 4, 1)
            debug_text = font.render(enemy.state, True, (255, 230, 120))
            canvas.blit(debug_text, (round(enemy.x - camera[0] - 25), round(enemy.y - camera[1] - 48)))
    for exit_name, exit_rect in (region["exits"].items() if show_controls else ()):
        viewport = pygame.Rect(camera[0], camera[1], VIEW[0], VIEW[1])
        if viewport.colliderect(exit_rect):
            label = "FLORESTA" if exit_name == "forest" else "VILA" if exit_name == "village" else "DESERTO" if exit_name == "desert" else "RUÍNAS"
            draw_key_prompt(canvas, f"Saída: {label}", font,
                            exit_rect.centerx - camera[0],
                            exit_rect.top - camera[1] - 34)
    if region.get("arena_locked"):
        lock = region["exits"].get("desert")
        if lock:
            pygame.draw.rect(canvas, (125, 84, 49), lock.move(-camera[0], -camera[1]), 2)
            draw_key_prompt(canvas, "Passagem bloqueada", font,
                            lock.centerx - camera[0],
                            lock.bottom - camera[1] + 8)
    if show_controls and show_banner:
        draw_region_banner(canvas, region, font)
    targets = (region.get("npcs", []) + [obj for obj in region.get("interactables", [])
                                          if not obj.opened and getattr(
                                              obj, "available", lambda _context: True)(interaction_context)]
               if show_controls else [])
    target = nearest(targets, player, interaction_context) if player is not None else None
    if target is not None:
        prompt_top = round(target.y - camera[1] - 78)
        prompt_top = max(18, min(canvas.get_height() - font.get_height() - 18,
                                 prompt_top))
        draw_key_prompt(canvas, getattr(target, "prompt", "[E] Interagir"), font,
                        target.x - camera[0], prompt_top)
    if show_controls and region.get("north_locked") and not region.get("arena_locked") and "desert" in region["exits"]:
        lock = region["exits"]["desert"]
        pygame.draw.rect(canvas, (125, 84, 49), lock.move(-camera[0], -camera[1]), 2)
        draw_key_prompt(canvas, "Passagem bloqueada", font,
                        lock.centerx - camera[0],
                        lock.bottom - camera[1] + 8)


def draw_region_banner(canvas, region, font):
    panel_rect = pygame.Rect(16, 12, 842, 36)
    draw_panel(canvas, panel_rect, fill=(24, 33, 39), radius=6, shadow=True)
    name_font = pygame.font.Font(None, 22)
    controls_font = pygame.font.Font(None, 17)
    name = name_font.render(region["name"].upper(), True, (239, 205, 139))
    canvas.blit(name, (panel_rect.x + 12,
                       panel_rect.centery - name.get_height() // 2))
    divider_x = panel_rect.x + 18 + name.get_width()
    pygame.draw.line(canvas, (77, 91, 93), (divider_x, panel_rect.y + 8),
                     (divider_x, panel_rect.bottom - 8), 1)
    controls = controls_font.render(
        "WASD mover   ·   Espaço atacar   ·   Q dash   ·   E interagir   ·   V personagem   ·   I inventário",
        True, (182, 193, 190))
    canvas.blit(controls, (divider_x + 12,
                           panel_rect.centery - controls.get_height() // 2))
