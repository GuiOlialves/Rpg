import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

import main
import save_manager
from story.prologue import opening_sequence
from ui.game_renderer import GameRenderer
from ui.narrative_overlay import draw_narrative


class PrologueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_only_approved_beats_and_fade_timing(self):
        sequence = opening_sequence()
        self.assertEqual(sequence.current.text, "Corre.")
        self.assertEqual(sequence.current.background, "black")
        self.assertEqual([beat.text for beat in sequence.beats], [
            "Corre.", "Não olha para trás.", "Você prometeu.", "*****", "...",
            None, "Onde...", "...", "Quem sou eu?", "Meu nome...", "*****",
            None, "Esse nome...", "Não.", "Nem isso.",
        ])

        for beat in sequence.beats[:5]:
            self.assertTrue(sequence.active)
            sequence.update(beat.duration_ms)
        self.assertEqual(sequence.current.background, "world")
        self.assertEqual(sequence.current.text, None)
        self.assertEqual(sequence.fade.alpha, 255)
        sequence.update(600)
        self.assertGreater(sequence.fade.alpha, 0)
        sequence.update(650)
        self.assertEqual(sequence.fade.alpha, 0)
        self.assertEqual(sequence.current.text, "Onde...")

        for beat in sequence.beats[6:]:
            finished = sequence.update(beat.duration_ms)
        self.assertTrue(finished)
        self.assertFalse(sequence.active)
        self.assertFalse(sequence.update(1000))

    def test_cutscene_starts_black_and_blocks_gameplay_input(self):
        batches = [
            [pygame.event.Event(pygame.KEYDOWN, key=key) for key in
             (pygame.K_v, pygame.K_i, pygame.K_e, pygame.K_SPACE, pygame.K_q)],
            [pygame.event.Event(pygame.QUIT)],
        ]
        captured = []
        draw = GameRenderer.draw

        def capture_draw(renderer, canvas, **kwargs):
            if kwargs["narrative"] and kwargs["narrative"].current.background == "black":
                captured.append(canvas.get_at((0, 0))[:3])
            return draw(renderer, canvas, **kwargs)

        with tempfile.TemporaryDirectory() as directory, \
             patch.object(save_manager, "SAVE_PATH", Path(directory) / "savegame.json"), \
             patch.object(pygame.event, "get", side_effect=batches), \
             patch("core.game.InputHandler.route") as route, \
             patch.object(main.Player, "update") as update_player, \
             patch("ui.game_renderer.GameRenderer.draw", autospec=True, side_effect=capture_draw):
            self.assertEqual(main.main(), 0)

        route.assert_not_called()
        update_player.assert_not_called()
        self.assertTrue(captured)
        self.assertEqual(captured[0], (0, 0, 0))

    def test_home_is_a_real_region_with_a_safe_static_spawn(self):
        pygame.init()
        pygame.display.set_mode((1, 1))
        region = main.build_region("home")
        self.assertEqual(region["exits"], {})
        self.assertEqual(region["enemy_spawns"], [])
        position = main.safe_respawn_position("home", region, [])
        player = main.Player(main.load("assets/player/f_player_sheet.png"),
                             main.load("assets/player/f_player_attack_sheet.png"))
        player.x, player.y = position
        self.assertEqual(position, (512.0, 288.0))
        self.assertFalse(player.hitbox.collidelist(region["obstacles"]) >= 0)


if __name__ == "__main__":
    unittest.main()
