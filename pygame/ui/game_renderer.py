"""Composes world, HUD, dialogue, menus and defeat overlay for one frame."""
import pygame

from core.config import VIEW
from ui.character_menu import draw_character_menu, fit_text
from ui.coordinates import logical_mouse_position
from ui.hud import draw_hud
from ui.inventory_menu import draw_inventory
from ui.narrative_overlay import draw_narrative
from ui.world_renderer import draw_world, draw_region_banner


class GameRenderer:
    def draw(self, canvas, *, region, player, enemies, drops, camera, debug,
             damage_numbers, hitstop_frames, font, title_font, dialogue,
             quest_manager, ui_mode, inventory, inventory_ui, game_over_screen,
             narrative=None, transition_fade=None, arrival_scene=None,
             alden_scene=None, house_memory_scene=None, blue_march_scene=None,
             forest_ambush_scene=None, insignia_memory_scene=None,
             red_officer_scene=None,
             story=None):
        def render_world(show_controls=True, scene_actors=()):
            if region.get("ambient_kind") == "home":
                # An integer close shot suits an interior. World positions and
                # collisions stay unchanged; HUD/text remain at native UI size.
                if not hasattr(self, "home_canvas"):
                    self.home_canvas = pygame.Surface((VIEW[0] // 2, VIEW[1] // 2))
                    self.home_font = pygame.font.Font(None, 12)
                size = self.home_canvas.get_size()
                bounds = region["terrain"].get_size()
                close_camera = (max(0, min(bounds[0] - size[0], round(player.x - size[0] / 2))),
                                max(0, min(bounds[1] - size[1], round(player.y - size[1] / 2 - 32))))
                draw_world(self.home_canvas, region, self.home_font, close_camera,
                           player, enemies, drops, debug, show_controls,
                           interaction_context=quest_manager, scene_actors=scene_actors,
                           show_banner=False)
                pygame.transform.scale(self.home_canvas, VIEW, canvas)
                if show_controls:
                    draw_region_banner(canvas, region, font)
            else:
                draw_world(canvas, region, font, camera, player, enemies, drops, debug,
                           show_controls=show_controls, interaction_context=quest_manager,
                           scene_actors=scene_actors)

        if narrative is not None and narrative.active:
            draw_narrative(
                canvas, narrative,
                world_renderer=lambda: render_world(show_controls=False))
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
        cinematic = (bool(arrival_scene is not None and arrival_scene.active)
                     or alden_active or house_memory_active or blue_march_active
                     or forest_ambush_active or insignia_memory_active
                     or red_officer_active)
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
        render_world(show_controls=not cinematic and not dialogue.active,
                     scene_actors=scene_actors)
        if insignia_memory_active:
            insignia_memory_scene.draw_overlay(canvas)
        if arrival_scene is not None and arrival_scene.active:
            arrival_scene.draw(canvas, camera, font)
        if hitstop_frames == 0:
            damage_numbers[:] = [number for number in damage_numbers if number.update()]
        for number in damage_numbers:
            number.draw(canvas, camera, font, title_font)

        if cinematic:
            pygame.draw.rect(canvas, (12, 15, 19), (0, 0, VIEW[0], 20))
            pygame.draw.rect(canvas, (12, 15, 19), (0, VIEW[1] - 20, VIEW[0], 20))
        elif not dialogue.active:
            draw_hud(canvas, player, font)
        dialogue.draw(canvas, font, title_font)
        quest_text = (story.objective_text if story is not None else "") or quest_manager.active_text()
        if quest_text and not cinematic and not dialogue.active:
            objective = font.render(quest_text, True, (244, 224, 166))
            canvas.blit(objective, (VIEW[0] - objective.get_width() - 16, 52))
        if quest_manager.notice_timer and not cinematic and not dialogue.active:
            notice = font.render(fit_text(quest_manager.notice, font, VIEW[0] - 350),
                                 True, (255, 235, 170))
            canvas.blit(notice, (16, 52))

        boss = next((enemy for enemy in enemies
                     if enemy.kind == "forest_guardian" and enemy.state != "DEAD"), None)
        if boss:
            bar = pygame.Rect(280, 78, 464, 22)
            pygame.draw.rect(canvas, (25, 25, 28), bar, border_radius=5)
            pygame.draw.rect(
                canvas, (166, 50, 62),
                (bar.x, bar.y, round(bar.width * boss.hp / boss.max_hp), bar.height),
                border_radius=5)
            pygame.draw.rect(canvas, (235, 207, 142), bar, 2, border_radius=5)
            canvas.blit(font.render(f"{boss.name}  {boss.hp}/{boss.max_hp}", True, "white"),
                        (bar.x + 10, bar.y + 3))

        mouse = logical_mouse_position(pygame.mouse.get_pos())
        if ui_mode == "character":
            draw_character_menu(canvas, player, font, title_font, mouse)
        elif ui_mode == "inventory":
            draw_inventory(canvas, inventory, font, title_font, player, inventory_ui, mouse)
        if game_over_screen is not None:
            game_over_screen.draw(canvas, font, title_font, mouse)
        if transition_fade is not None:
            transition_fade.draw(canvas)
