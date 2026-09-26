import unittest
from types import SimpleNamespace

import pygame

from core.input_handler import InputHandler
from story.story_manager import StoryManager
from world.world_manager import WorldManager


class ArchitectureTests(unittest.TestCase):
    def test_story_flags_round_trip_as_plain_data(self):
        story = StoryManager()
        story.set("house_searched")
        story.set("saw_silhouette", False)

        serialized = story.to_dict()
        restored = StoryManager.from_dict(serialized)

        self.assertEqual(restored.to_dict(), {
            "house_searched": True,
            "saw_silhouette": False,
        })
        self.assertEqual(restored.get("not_started"), False)
        with self.assertRaises(ValueError):
            story.set("invalid", "yes")

    def test_world_manager_dispatches_existing_builders(self):
        village = {"name": "village"}
        manager = WorldManager({
            "village": lambda opened: village,
            "desert": lambda opened: {"opened": opened},
        })

        self.assertEqual(manager.region_ids, ("village", "desert"))
        self.assertIs(manager.build_region("village"), village)
        self.assertEqual(manager.build_region("desert", {"chest"}),
                         {"opened": {"chest"}})
        with self.assertRaises(ValueError):
            manager.build_region("unknown")

    def test_input_handler_preserves_existing_action_keys(self):
        handler = InputHandler()
        dialogue = SimpleNamespace(active=False)
        keys = {
            pygame.K_F5: "save",
            pygame.K_F9: "load",
            pygame.K_ESCAPE: "escape",
            pygame.K_e: "interact",
            pygame.K_v: "toggle_character",
            pygame.K_i: "toggle_inventory",
            pygame.K_F3: "toggle_debug",
            pygame.K_SPACE: "attack",
            pygame.K_q: "dash",
        }
        for key, expected in keys.items():
            with self.subTest(key=key):
                command = handler.route(
                    pygame.event.Event(pygame.KEYDOWN, key=key),
                    ui_mode=None, dialogue=dialogue, player=None,
                    inventory=[], inventory_ui={"tab": "TODOS"},
                    game_over_screen=None, view=(1024, 576))
                self.assertEqual(command.name, expected)

        stat = handler.route(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_3),
            ui_mode="character", dialogue=dialogue, player=None,
            inventory=[], inventory_ui={"tab": "TODOS"},
            game_over_screen=None, view=(1024, 576))
        self.assertEqual((stat.name, stat.value), ("spend_stat", "magia"))


if __name__ == "__main__":
    unittest.main()
