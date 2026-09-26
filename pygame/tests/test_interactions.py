import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

import main
import save_manager
from story.arrival_scene import ArrivalScene
from ui.game_renderer import GameRenderer
from entities.npc import nearest


class InteractionTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def tearDown(self):
        pygame.quit()

    def test_house_dialogues_exit_fade_and_village_spawn(self):
        scripted_events = {
            2: [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)],
            3: [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE),
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q),
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)],
            4: [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)],
            5: [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)],
            6: [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)],
            7: [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)],
            8: [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)],
            9: [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)],
            10: [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)],
        }
        polls = [0]
        advance_scene_dialogue = [False]
        scene_complete = [False]
        save_sent = [False]
        scene_lock_test_pending = [False]
        scene_lock_test_sent = [False]

        def get_events():
            polls[0] += 1
            if polls[0] in scripted_events:
                return scripted_events[polls[0]]
            if scene_lock_test_pending[0] and not scene_lock_test_sent[0]:
                scene_lock_test_pending[0] = False
                scene_lock_test_sent[0] = True
                return [pygame.event.Event(pygame.KEYDOWN, key=key) for key in
                        (pygame.K_v, pygame.K_i, pygame.K_SPACE, pygame.K_q)]
            if advance_scene_dialogue[0]:
                advance_scene_dialogue[0] = False
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)]
            if scene_complete[0]:
                if not save_sent[0]:
                    save_sent[0] = True
                    return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F5)]
                return [pygame.event.Event(pygame.QUIT)]
            return []

        movement_frames = [0]

        def move_between_examinables(player, keys, obstacles):
            movement_frames[0] += 1
            positions = {1: (300, 260), 2: (690, 313), 3: (512, 470)}
            if movement_frames[0] in positions:
                player.x, player.y = positions[movement_frames[0]]

        spoken_lines = []
        spoken_speakers = []
        movement_at_dialogue = []
        rendered_regions = []
        fade_alphas = []
        scene_phases = []
        scene_player_timers = []
        player_pixels_changed = []
        rendering_arrival = [False]
        original_draw = GameRenderer.draw
        original_player_draw = main.Player.draw

        def inspect_player_draw(player, canvas, camera):
            if not rendering_arrival[0]:
                return original_player_draw(player, canvas, camera)
            sprite_rect = pygame.Rect(round(player.x - 48 - camera[0]),
                                      round(player.y - 72 - camera[1]), 96, 96)
            sprite_rect = sprite_rect.clip(canvas.get_rect())
            before = pygame.image.tobytes(canvas.subsurface(sprite_rect), "RGB")
            original_player_draw(player, canvas, camera)
            after = pygame.image.tobytes(canvas.subsurface(sprite_rect), "RGB")
            player_pixels_changed.append(before != after)

        def inspect_frame(renderer, canvas, **kwargs):
            rendered_regions.append(kwargs["region"]["name"])
            fade_alphas.append(kwargs["transition_fade"].alpha)
            arrival_scene = kwargs.get("arrival_scene")
            if arrival_scene is not None and arrival_scene.active:
                scene_phases.append(arrival_scene.phase)
                scene_player_timers.append(kwargs["player"].invulnerability_timer)
                if arrival_scene.phase == "silhouette" and not scene_lock_test_sent[0]:
                    scene_lock_test_pending[0] = True
            dialogue = kwargs["dialogue"]
            if dialogue.active:
                spoken_lines.append(dialogue.npc.dialogue_for("default", dialogue.manager)[dialogue.index])
                movement_at_dialogue.append(movement_frames[0])
                if polls[0] >= 20:
                    spoken_speakers.append(dialogue.npc.speaker_for(dialogue.index))
                    advance_scene_dialogue[0] = True
            if (kwargs["quest_manager"].get("forest_trouble").state == "ACTIVE"
                    and kwargs["quest_manager"].notice.startswith("Missão recebida:")):
                scene_complete[0] = True
            rendering_arrival[0] = arrival_scene is not None and arrival_scene.active
            try:
                return original_draw(renderer, canvas, **kwargs)
            finally:
                rendering_arrival[0] = False

        class FastTestClock:
            def __init__(self):
                self.frames = 0

            def tick(self, fps):
                self.frames += 1
                return 30000 if self.frames == 1 else 130

        with tempfile.TemporaryDirectory() as directory, \
             patch.object(save_manager, "SAVE_PATH", Path(directory) / "savegame.json"), \
             patch("core.game.pygame.time.Clock", FastTestClock), \
             patch.object(pygame.event, "get", side_effect=get_events), \
             patch.object(main.Player, "update", move_between_examinables), \
             patch.object(main.Player, "attack") as attack, \
             patch.object(main.Player, "start_dash") as dash, \
             patch.object(main.Player, "draw", inspect_player_draw), \
             patch("ui.game_renderer.GameRenderer.draw", autospec=True, side_effect=inspect_frame):
            with self.assertRaises(SystemExit) as exit_result:
                runpy.run_path("main.py", run_name="__main__")
            self.assertEqual(exit_result.exception.code, 0)
            saved = save_manager.read_save(Path(directory) / "savegame.json")

        self.assertEqual(spoken_lines[:6], [
            "Esse sou eu?", "Não sinto que estou olhando para um estranho.",
            "Mas também não lembro desse rosto.",
            "Sei como segurar isso.", "Só não sei quem me ensinou.",
            "Talvez alguém aqui saiba alguma coisa.",
        ])
        self.assertEqual(spoken_lines[6:], [line for _, line in ArrivalScene.LINES])
        self.assertEqual(spoken_speakers, [speaker for speaker, _ in ArrivalScene.LINES])
        self.assertEqual(movement_at_dialogue[:6], [1, 1, 1, 2, 2, 3])
        for phase in ("walk", "silhouette", "ei", "flash_near", "near",
                      "flash_gone", "ellipsis", "shout", "run", "dialogue"):
            self.assertIn(phase, scene_phases)
        self.assertTrue(scene_lock_test_sent[0])
        self.assertTrue(player_pixels_changed)
        self.assertTrue(all(player_pixels_changed))
        self.assertEqual(set(scene_player_timers), {0})
        attack.assert_not_called()
        dash.assert_not_called()
        self.assertIn("Vila do Vale", rendered_regions)
        self.assertIn(255, fade_alphas)
        self.assertEqual(saved["region"], "village")
        spawn_x, spawn_y = saved["player"]["position"]
        self.assertEqual(spawn_x, 540)
        self.assertGreater(spawn_y, 490)
        self.assertTrue(saved["story"]["woke_up"])
        self.assertTrue(saved["story"]["saw_silhouette"])
        self.assertTrue(saved["story"]["slime_quest_started"])
        self.assertEqual(saved["quests"]["forest_trouble"]["state"], "ACTIVE")
        self.assertEqual(saved["quests"]["forest_trouble"]["progress"], 0)

        pygame.init()
        pygame.display.set_mode((1, 1))
        village = main.build_region("village")
        hitbox = pygame.Rect(round(spawn_x - 13), round(spawn_y - 9), 26, 18)
        self.assertFalse(any(hitbox.colliderect(obstacle) for obstacle in village["obstacles"]))
        self.assertFalse(any(hitbox.colliderect(exit_rect) for exit_rect in village["exits"].values()))

    def test_player_can_walk_house_and_reach_each_interaction_without_crossing_solid_objects(self):
        home = main.build_region("home")
        player = main.Player(main.load("assets/player/f_player_sheet.png"),
                             main.load("assets/player/f_player_attack_sheet.png"))
        player.x, player.y = 512, 288

        class Keys:
            active = None

            def __getitem__(self, key):
                return key == self.active

        keys = Keys()

        def walk(key, frames):
            keys.active = key
            for _ in range(frames):
                player.update(keys, home["obstacles"])

        walk(pygame.K_s, 20)
        self.assertGreater(player.y, 288)
        walk(pygame.K_w, 60)
        self.assertGreaterEqual(player.y, 231)
        self.assertFalse(player.hitbox.colliderect(pygame.Rect(464, 188, 96, 34)))

        walk(pygame.K_s, 20)
        walk(pygame.K_a, 25)
        walk(pygame.K_w, 12)
        walk(pygame.K_a, 44)
        mirror, sword, door = home["interactables"]
        self.assertIs(nearest([mirror], player), mirror)

        player.x, player.y = 300, 260
        walk(pygame.K_w, 100)
        self.assertLessEqual(player.y, 51)
        player.x, player.y = 320, 269
        walk(pygame.K_d, 130)
        self.assertIs(nearest([sword], player), sword)
        walk(pygame.K_a, 12)
        walk(pygame.K_s, 100)
        walk(pygame.K_a, 60)
        self.assertIs(nearest([door], player), door)


if __name__ == "__main__":
    unittest.main()
