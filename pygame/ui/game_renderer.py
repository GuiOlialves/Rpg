"""Composes world, HUD, dialogue, menus and defeat overlay for one frame."""
import math
import pygame

from core.config import VIEW
from ui.character_menu import draw_character_menu
from ui.coordinates import logical_mouse_position
from ui.hud import draw_bar, draw_hud, draw_notice, draw_objective_tracker
from ui.inventory_menu import draw_inventory
from ui.narrative_overlay import draw_narrative, draw_letterbox
from ui.world_renderer import draw_world, draw_region_banner


def draw_prologue_card(canvas):
    canvas.fill((5, 7, 10))
    lines = (("O VALE", 56, 0.30, (224, 207, 165)),
             ("Prólogo", 24, 0.45, (157, 166, 173)),
             ("O Nome que Falta", 34, 0.51, (218, 218, 212)),
             ("CONCLUÍDO", 24, 0.67, (224, 207, 165)))
    for text, size, height, color in lines:
        image = pygame.font.Font(None, size).render(text, True, color)
        canvas.blit(image, image.get_rect(center=(canvas.get_width() // 2,
                                                   round(canvas.get_height() * height))))
    prompt = pygame.font.Font(None, 20).render("[E / Enter] Continuar", True, (139, 147, 152))
    canvas.blit(prompt, prompt.get_rect(center=(canvas.get_width() // 2, canvas.get_height() - 48)))


class GameRenderer:
    def draw(self, canvas, *, region, player, enemies, drops, camera, debug,
             damage_numbers, hitstop_frames, font, title_font, dialogue,
             quest_manager, ui_mode, inventory, inventory_ui, game_over_screen,
             narrative=None, transition_fade=None, arrival_scene=None,
             alden_scene=None, house_memory_scene=None, blue_march_scene=None,
             forest_ambush_scene=None, insignia_memory_scene=None,
             red_officer_scene=None, prologue_3c_scene=None,
             chapter1_return_scene=None,
             old_road_scene=None,
             watchpost_scene=None, edrin_scene=None,
             story=None, prologue_end_card=False):
        if chapter1_return_scene is not None and chapter1_return_scene.active:
            if chapter1_return_scene.phase != "return":
                chapter1_return_scene.draw_title(canvas)
            else:
                draw_world(canvas, region, font, camera, player, [], [],
                           show_controls=False, show_banner=False, story_context=story)
                draw_letterbox(canvas)
                chapter1_return_scene.fade.draw(canvas)
            return
        if getattr(self,'impact_serial',0) != player.impact_serial:
            self.impact_serial = player.impact_serial
            self.shake_tick = 4
        if getattr(self,'shake_tick',0) and ui_mode is None and not dialogue.active:
            offset = ((0,0),(-1,0),(1,-1),(-1,1),(1,0))[self.shake_tick]
            camera = (camera[0]+offset[0]*player.impact_strength,
                      camera[1]+offset[1]*player.impact_strength)
            self.shake_tick -= 1
        # Framing is presentation-only: no actor, collision or gameplay camera is moved.
        shot_scene = next((scene for scene in (
            edrin_scene, watchpost_scene, old_road_scene, prologue_3c_scene, red_officer_scene, blue_march_scene,
            forest_ambush_scene, insignia_memory_scene, alden_scene)
            if scene is not None and scene.active), None)
        memory = (prologue_3c_scene is not None and prologue_3c_scene.active
                  and prologue_3c_scene.memory_visible)
        post_memory = bool(watchpost_scene is not None and watchpost_scene.memory_visible)
        memory = memory or post_memory

        def render_world(show_controls=True, scene_actors=(), include_player=True):
            world_player = player if include_player else None
            if region.get("ambient_kind") == "home":
                # An integer close shot suits an interior. World positions and
                # collisions stay unchanged; HUD/text remain at native UI size.
                if not hasattr(self, "home_canvas"):
                    self.home_canvas = pygame.Surface((VIEW[0] // 2, VIEW[1] // 2))
                    self.home_font = pygame.font.Font(None, 12)
                size = self.home_canvas.get_size()
                bounds = region["terrain"].get_size()
                close_camera = (max(0, min(bounds[0] - size[0], round(player.x - size[0] / 2))),
                                max(-48, min(bounds[1] - size[1], round(player.y - size[1] / 2 - 32))))
                # Headroom keeps wall clues below the normal HUD at the north wall.
                self.home_canvas.fill((30, 29, 33))
                draw_world(self.home_canvas, region, self.home_font, close_camera,
                           world_player, enemies, drops, debug, show_controls,
                           interaction_context=quest_manager, scene_actors=scene_actors,
                           show_banner=False, story_context=story)
                pygame.transform.scale(self.home_canvas, VIEW, canvas)
                if show_controls:
                    draw_region_banner(canvas, region, font)
            elif shot_scene is not None or (dialogue.active and arrival_scene is None):
                if not hasattr(self, "shot_canvas"):
                    self.shot_canvas = pygame.Surface((768, 432))
                focus_x, focus_y = player.x, player.y
                if shot_scene is alden_scene and alden_scene is not None:
                    focus_x = (player.x + alden_scene.alden.x) / 2
                    focus_y = (player.y + alden_scene.alden.y) / 2
                elif shot_scene is edrin_scene and edrin_scene is not None:
                    focus_x,focus_y = edrin_scene.focus
                elif shot_scene is old_road_scene and old_road_scene is not None:
                    focus_x,focus_y = old_road_scene.focus
                elif shot_scene is watchpost_scene and watchpost_scene is not None:
                    focus_x,focus_y = watchpost_scene.focus
                elif shot_scene is blue_march_scene and blue_march_scene is not None:
                    focus_x, focus_y = player.x - 85, player.y + 30
                elif shot_scene is forest_ambush_scene and forest_ambush_scene is not None:
                    actors = (player, *forest_ambush_scene.actors)
                    focus_x = sum(actor.x for actor in actors) / len(actors)
                    focus_y = sum(actor.y for actor in actors) / len(actors)
                elif shot_scene is red_officer_scene and red_officer_scene is not None:
                    focus_x = (player.x + red_officer_scene.commander.x - 56) / 2
                elif shot_scene is prologue_3c_scene and prologue_3c_scene is not None:
                    if memory:
                        focus_x, focus_y = prologue_3c_scene.memory_center
                    elif prologue_3c_scene.phase == "epilogue_looks":
                        pan = math.sin(math.pi * min(1, prologue_3c_scene.elapsed_ms / 3600))
                        focus_x -= 240 * pan
                        focus_y -= 45 * pan
                    elif prologue_3c_scene.phase in {"after_memory", "after_pause", "flee"}:
                        focus_x += 70
                elif dialogue.active and hasattr(dialogue.npc, "x"):
                    focus_x = (player.x + dialogue.npc.x) / 2
                    focus_y = (player.y + dialogue.npc.y) / 2
                bounds = region["terrain"].get_size()
                target = (max(0, min(bounds[0] - 768, focus_x - 384)),
                          max(0, min(bounds[1] - 432, focus_y - 190)))
                shot_key = (id(shot_scene or dialogue.npc), memory)
                if getattr(self, "shot_key", None) != shot_key:
                    self.shot_camera = target
                self.shot_key = shot_key
                self.shot_camera = tuple(a + (b - a) * .12 for a, b in zip(self.shot_camera, target))
                shot_camera = tuple(round(value) for value in self.shot_camera)
                backdrop = region
                if memory:
                    # Keep the existing landscape, omitting present-day bodies and props.
                    backdrop = dict(region, objects=[],
                                    terrain=region.get("memory_terrain",region["terrain"]) if post_memory else region["terrain"],
                                    scenery=region.get("memory_scenery",region["scenery"]) if post_memory else [],
                                    npcs=[], interactables=[])
                    world_player = None
                draw_world(self.shot_canvas, backdrop, font, shot_camera,
                           world_player, [] if memory else enemies, [] if memory else drops,
                           debug, False, interaction_context=quest_manager,
                           scene_actors=scene_actors, show_banner=False,
                           story_context=None if memory else story)
                pygame.transform.scale(self.shot_canvas, VIEW, canvas)
            else:
                self.shot_key = None
                draw_world(canvas, region, font, camera, world_player, enemies, drops, debug,
                           show_controls=show_controls, interaction_context=quest_manager,
                           scene_actors=scene_actors, story_context=story)

        if prologue_end_card:
            draw_prologue_card(canvas)
            return
        if narrative is not None and narrative.active:
            draw_narrative(
                canvas, narrative,
                world_renderer=lambda: render_world(show_controls=False))
            return
        if edrin_scene is not None and edrin_scene.active:
            render_encounter = lambda: render_world(show_controls=False,scene_actors=edrin_scene.world_actors)
            if edrin_scene.sequence is not None:
                draw_narrative(canvas,edrin_scene.sequence,world_renderer=render_encounter)
            else:
                render_encounter()
                draw_letterbox(canvas)
                dialogue.draw(canvas,font,title_font)
            return
        if old_road_scene is not None and old_road_scene.active:
            def render_road_moment():
                render_world(show_controls=False,scene_actors=old_road_scene.world_actors)
                old_road_scene.draw_overlay(canvas)
            draw_narrative(canvas,old_road_scene.sequence,world_renderer=render_road_moment)
            return
        if watchpost_scene is not None and watchpost_scene.active:
            def render_post_moment():
                render_world(show_controls=False,scene_actors=watchpost_scene.world_actors,
                             include_player=not watchpost_scene.memory_visible)
                watchpost_scene.draw_overlay(canvas)
            draw_narrative(canvas,watchpost_scene.sequence,world_renderer=render_post_moment)
            return
        alden_active = alden_scene is not None and alden_scene.active
        if alden_active and alden_scene.sequence is not None:
            draw_narrative(canvas, alden_scene.sequence,
                           world_renderer=lambda: render_world(show_controls=False))
            return
        house_memory_active = house_memory_scene is not None and house_memory_scene.active
        blue_march_active = blue_march_scene is not None and blue_march_scene.active
        forest_ambush_active = forest_ambush_scene is not None and forest_ambush_scene.active
        insignia_memory_active = insignia_memory_scene is not None and insignia_memory_scene.active
        red_officer_active = red_officer_scene is not None and red_officer_scene.active
        if house_memory_active and house_memory_scene.sequence is not None:
            def render_memory_world():
                render_world(show_controls=False,
                             scene_actors=house_memory_scene.world_actors)
                house_memory_scene.draw_overlay(canvas)

            draw_narrative(canvas, house_memory_scene.sequence,
                           world_renderer=render_memory_world)
            return
        if insignia_memory_active and insignia_memory_scene.sequence is not None:
            def render_insignia_memory_world():
                render_world(show_controls=False,
                             scene_actors=insignia_memory_scene.world_actors)
                insignia_memory_scene.draw_overlay(canvas)

            draw_narrative(canvas, insignia_memory_scene.sequence,
                           world_renderer=render_insignia_memory_world)
            return
        if red_officer_active and red_officer_scene.sequence is not None:
            draw_narrative(
                canvas, red_officer_scene.sequence,
                world_renderer=lambda: render_world(
                    show_controls=False,
                    scene_actors=red_officer_scene.world_actors))
            return
        prologue_3c_active = prologue_3c_scene is not None and prologue_3c_scene.active
        if prologue_3c_active and prologue_3c_scene.sequence is not None:
            draw_narrative(
                canvas, prologue_3c_scene.sequence,
                world_renderer=lambda: (
                    render_world(show_controls=False,
                                 scene_actors=prologue_3c_scene.world_actors,
                                 include_player=not prologue_3c_scene.memory_visible),
                    prologue_3c_scene.draw_overlay(canvas)))
            return
        cinematic = (bool(arrival_scene is not None and arrival_scene.active)
                     or alden_active or house_memory_active or blue_march_active
                     or forest_ambush_active or insignia_memory_active
                     or red_officer_active or prologue_3c_active)
        scene_actors = (arrival_scene.world_actors
                        if arrival_scene is not None and arrival_scene.active else ())
        if house_memory_active:
            scene_actors += house_memory_scene.world_actors
        if blue_march_active:
            scene_actors += blue_march_scene.world_actors
        if forest_ambush_active:
            scene_actors += forest_ambush_scene.world_actors
        if insignia_memory_active:
            scene_actors += insignia_memory_scene.world_actors
        if red_officer_active:
            scene_actors += red_officer_scene.world_actors
        if prologue_3c_active:
            scene_actors += prologue_3c_scene.world_actors
        render_world(show_controls=not cinematic and not dialogue.active,
                     scene_actors=scene_actors,
                     include_player=not (prologue_3c_active
                                         and prologue_3c_scene.memory_visible))
        if prologue_3c_active:
            prologue_3c_scene.draw_overlay(canvas)
        if insignia_memory_active:
            insignia_memory_scene.draw_overlay(canvas)
        if house_memory_active:
            house_memory_scene.draw_overlay(canvas)
        if arrival_scene is not None and arrival_scene.active:
            arrival_scene.draw(canvas, camera, font)
        if hitstop_frames == 0:
            damage_numbers[:] = [number for number in damage_numbers if number.update()]
        for number in (() if cinematic else damage_numbers):
            number.draw(canvas, camera, font, title_font)

        if cinematic:
            draw_letterbox(canvas)
        elif not dialogue.active and not cinematic and ui_mode is None:
            draw_hud(canvas, player, font)
        dialogue.draw(canvas, font, title_font)
        quest_text = (story.objective_text if story is not None else "") or quest_manager.active_text()
        if quest_text and not cinematic and not dialogue.active and ui_mode is None:
            draw_objective_tracker(canvas, quest_text, font,
                                   title=story.objective_title if story is not None else "OBJETIVO ATUAL")
        if (quest_manager.notice_timer and not cinematic and not dialogue.active
                and ui_mode is None):
            draw_notice(canvas, quest_manager.notice, font)

        boss = next((enemy for enemy in enemies
                     if enemy.kind in {"forest_guardian", "red_officer"}
                     and enemy.state not in {"DEAD", "DEFEATED"}
                     and (enemy.kind != "red_officer" or region.get("boss_battle_active"))), None)
        if (boss and player.hp > 0 and game_over_screen is None
                and region.get("ambient_kind") == "forest" and not cinematic
                and (boss.kind == "red_officer" or (not dialogue.active and ui_mode is None))):
            draw_bar(canvas, pygame.Rect(280, 136, 464, 30), boss.hp,
                     boss.max_hp, (166, 50, 62), boss.name, font)

        mouse = logical_mouse_position(pygame.mouse.get_pos())
        if ui_mode == "character":
            draw_character_menu(canvas, player, font, title_font, mouse)
        elif ui_mode == "inventory":
            draw_inventory(canvas, inventory, font, title_font, player, inventory_ui, mouse)
        if game_over_screen is not None:
            game_over_screen.draw(canvas, font, title_font, mouse)
        if transition_fade is not None:
            transition_fade.draw(canvas)
