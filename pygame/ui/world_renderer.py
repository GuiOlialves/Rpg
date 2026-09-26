"""Rendering of region layers, actors, exits and debug overlays."""
import pygame
import ambient
import environment
from core.config import VIEW
from entities.npc import nearest
from ui.hud import draw_key_prompt, draw_panel

_DEBUG_LABEL_FONT = None

def draw_world(canvas, region, font, camera, player=None, enemies=None, drops=None,
               debug=False, show_controls=True, interaction_context=None, scene_actors=(),
               show_banner=True, story_context=None):
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
        global _DEBUG_LABEL_FONT
        if _DEBUG_LABEL_FONT is None:
            _DEBUG_LABEL_FONT = pygame.font.Font(None, 15)
        viewport = pygame.Rect(camera[0], camera[1], canvas.get_width(), canvas.get_height())
        label_font = _DEBUG_LABEL_FONT

        def on_screen(rect):
            return rect is not None and viewport.colliderect(rect)

        def label(text, x, y, color):
            rendered = label_font.render(str(text), True, color)
            canvas.blit(rendered, (round(x - camera[0]), round(y - camera[1])))

        # Solid footprints include walls, facades, props and static obstacles.
        for obstacle in region.get("obstacles", ()):
            if on_screen(obstacle):
                pygame.draw.rect(canvas, (255, 145, 55),
                                 obstacle.move(-camera[0], -camera[1]), 1)
        if player is not None:
            pygame.draw.rect(canvas, (75, 231, 247), player.hitbox.move(-camera[0], -camera[1]), 2)
            if player.attack_box.width:
                pygame.draw.rect(canvas, (255, 250, 112), player.attack_box.move(-camera[0], -camera[1]), 2)
            label("PLAYER", player.x - 20, player.y - 29, (75, 231, 247))
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
            label(getattr(enemy, "kind", "enemy"), enemy.x - 20, enemy.y - 62,
                  (255, 180, 155))

        for npc in region.get("npcs", ()):
            hitbox = getattr(npc, "hitbox", None)
            interaction_rect = getattr(npc, "interaction_rect", None)
            if on_screen(hitbox):
                pygame.draw.rect(canvas, (105, 149, 255),
                                 hitbox.move(-camera[0], -camera[1]), 1)
            if on_screen(interaction_rect):
                pygame.draw.rect(canvas, (80, 206, 238),
                                 interaction_rect.move(-camera[0], -camera[1]), 1)
            label(f"NPC {getattr(npc, 'uid', '?')} {getattr(npc, 'enabled', True)}",
                  npc.x - 28, npc.y - 48, (145, 190, 255))
        for actor in scene_actors:
            hitbox = getattr(actor, "hitbox", None)
            interaction_rect = getattr(actor, "interaction_rect", None)
            if on_screen(hitbox):
                pygame.draw.rect(canvas, (105, 149, 255),
                                 hitbox.move(-camera[0], -camera[1]), 1)
            if on_screen(interaction_rect):
                pygame.draw.rect(canvas, (80, 206, 238),
                                 interaction_rect.move(-camera[0], -camera[1]), 1)
            if hasattr(actor, "uid"):
                label(f"SCENE {actor.uid}", actor.x - 28, actor.y - 48,
                      (145, 190, 255))

        candidates = list(region.get("interactables", ()))
        candidates.extend(region.get("investigation_interactables", ()))
        active_interactables = {getattr(obj, "uid", id(obj))
                                for obj in region.get("interactables", ())}
        seen = set()
        for obj in candidates:
            uid = getattr(obj, "uid", str(id(obj)))
            if uid in seen:
                continue
            seen.add(uid)
            interaction_rect = getattr(obj, "interaction_rect", None)
            if interaction_rect is None or not on_screen(interaction_rect):
                continue
            available = (uid in active_interactables
                         and getattr(obj, "enabled", True))
            try:
                available = available and getattr(
                    obj, "available", lambda _context: True)(interaction_context)
            except (TypeError, AttributeError):
                available = False
            opened = getattr(obj, "opened", False)
            color = ((75, 235, 130) if available and not opened
                     else (135, 145, 143))
            pygame.draw.rect(canvas, color,
                             interaction_rect.move(-camera[0], -camera[1]), 1)
            radius = getattr(obj, "interaction_radius", None)
            if radius is not None:
                center = (round(obj.x - camera[0]), round(obj.y - camera[1]))
                pygame.draw.circle(canvas, color, center, int(radius), 1)
            state = "open" if opened else "on" if available else "off"
            condition = getattr(obj, "condition", None)
            condition_label = " cond" if condition is not None else ""
            label(f"{uid} [{state}{condition_label}]", obj.x - 30,
                  obj.y - (radius or 18) - 15, color)

        # Exits are collision-like transition triggers; interaction circles above
        # remain a separate color and category.
        for exit_name, trigger in region.get("exits", {}).items():
            if on_screen(trigger):
                pygame.draw.rect(canvas, (247, 74, 153),
                                 trigger.move(-camera[0], -camera[1]), 2)
                label(f"EXIT {exit_name}", trigger.left, trigger.top - 16,
                      (255, 133, 192))

        if (story_context is not None and region.get("story_phase") == "forest_post_march"
                and story_context.get("blue_army_departed")):
            groups = region.get("red_encounter_groups", ())
            progress = story_context.get("forest_battle_progress", 0)
            active_group = ((progress - 1) // 2 if progress % 2 else progress // 2)
            for index, group in enumerate(groups):
                center_x = round(sum(position[0] for position in group) / len(group))
                center_y = round(sum(position[1] for position in group) / len(group))
                center = (center_x - camera[0], center_y - camera[1])
                active = (index == active_group and progress < 10
                          and not story_context.get("red_insignia_found"))
                color = (240, 114, 231) if active else (128, 105, 151)
                circle_rect = pygame.Rect(center_x - 158, center_y - 158, 316, 316)
                if on_screen(circle_rect):
                    pygame.draw.circle(canvas, color,
                                       (round(center[0]), round(center[1])), 158, 1)
                    label(f"red_group_{index + 1} {'active' if active else 'idle'}",
                          center_x - 56, center_y - 162, color)
            officer_trigger = region.get("red_officer_trigger")
            if (officer_trigger is not None and story_context.get("red_insignia_found")
                    and not story_context.get("red_officer_met")):
                x, y = officer_trigger
                circle_rect = pygame.Rect(x - 108, y - 108, 216, 216)
                if on_screen(circle_rect):
                    pygame.draw.circle(canvas, (255, 87, 190),
                                       (round(x - camera[0]), round(y - camera[1])), 108, 2)
                    label("red_officer_trigger", x - 65, y - 115, (255, 133, 205))
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
