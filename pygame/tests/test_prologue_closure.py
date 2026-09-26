import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

import main
import save_manager
from entities.npc import NPC
from systems.quest import ACTIVE, QuestManager
from story.story_manager import StoryManager
from ui.game_renderer import GameRenderer


class PrologueClosureTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def tearDown(self):
        pygame.quit()

    def test_starting_house_entry_and_wall_hitboxes_have_clear_doorway(self):
        village = main.build_region("village")
        entry = next(item for item in village["interactables"]
                     if item.uid == "starting_house_entry")
        self.assertTrue(entry.transition_on_interact)
        self.assertEqual(entry.transition_to, "home")

        player = main.Player(main.load("assets/player/f_player_sheet.png"),
                             main.load("assets/player/f_player_attack_sheet.png"))
        player.x, player.y = entry.x, entry.y - 21
        self.assertTrue(entry.interaction_rect.colliderect(player.hitbox))
        self.assertFalse(any(player.hitbox.colliderect(box)
                             for box in village["obstacles"]))

        player.x, player.y = 500, 450
        self.assertTrue(any(player.hitbox.colliderect(box)
                            for box in village["obstacles"]))

        home = main.build_region("home")
        self.assertEqual(home["spawn"]["village"], (512, 288))
        player.x, player.y = home["spawn"]["village"]
        self.assertFalse(any(player.hitbox.colliderect(box)
                             for box in home["obstacles"]))

    def test_civilian_idle_and_run_frames_keep_their_full_alpha_footprint(self):
        village = main.build_region("village")
        civilians = village["npcs"]
        self.assertEqual({npc.uid for npc in civilians}, {"alden", "mira", "tomas"})
        for npc in civilians:
            self.assertEqual(npc.sprite.get_height(), npc.frame_height)
            self.assertEqual(npc.sprite.get_width() % npc.frame_size, 0)
            for running in (False, True):
                npc.running = running
                for frame_index in range(npc.sprite.get_width() // npc.frame_size):
                    npc.anim_tick = frame_index * 5
                    canvas = pygame.Surface((180, 140), pygame.SRCALPHA)
                    npc.x, npc.y = 90, 92
                    npc.draw(canvas, (0, 0))
                    bounds = canvas.get_bounding_rect()
                    self.assertGreater(bounds.height, 0, npc.uid)
                    self.assertEqual(bounds.bottom, 92,
                                     f"{npc.uid}: feet not grounded on frame {frame_index}")

    def test_reentry_fades_in_and_back_out_without_replaying_completed_prologue(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "savegame.json"
            player = main.Player(main.load("assets/player/f_player_sheet.png"),
                                 main.load("assets/player/f_player_attack_sheet.png"))
            player.x, player.y = 540, 490
            quests = QuestManager()
            quests.accept("forest_trouble")
            quests.enemy_defeated("slime")
            quests.enemy_defeated("slime")
            story = StoryManager({"woke_up": True, "saw_silhouette": True,
                                  "slime_quest_started": True})
            save_manager.save_game(player, [], quests, "village", set(), [],
                                   path, story=story)

            def exercise(direction):
                state = {"poll": 0, "ready": False, "seen": [], "fade_seen": False}

                def events():
                    state["poll"] += 1
                    if state["poll"] == 1:
                        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F4)]
                    if state["poll"] == 2:
                        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F9)]
                    if direction == "enter" and state["poll"] == 3:
                        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)]
                    if direction == "leave" and state["poll"] in (3, 4):
                        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)]
                    if state["ready"]:
                        state["ready"] = False
                        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F5),
                                pygame.event.Event(pygame.QUIT)]
                    self.assertLess(state["poll"], 30,
                                    f"transição {direction} não terminou")
                    return []

                def move_to_inner_door(character, keys, obstacles):
                    if direction == "leave":
                        character.x, character.y = 512, 470

                original_draw = GameRenderer.draw

                def observe(renderer, canvas, **kwargs):
                    name = kwargs["region"]["name"]
                    state["seen"].append(name)
                    fade = kwargs["transition_fade"]
                    if fade.alpha > 0:
                        state["fade_seen"] = True
                    if direction == "enter":
                        arrived = name == "Casa" and not fade.active and fade.alpha == 0
                    else:
                        arrived = (name == "Vila do Vale" and not fade.active
                                   and fade.alpha == 0)
                        self.assertIsNone(kwargs["arrival_scene"])
                    if arrived and state["fade_seen"]:
                        state["ready"] = True
                    self.assertIsNone(kwargs["narrative"])
                    return original_draw(renderer, canvas, **kwargs)

                class FastClock:
                    def tick(self, fps):
                        return 130

                with patch.object(save_manager, "SAVE_PATH", path), \
                     patch("core.game.pygame.time.Clock", FastClock), \
                     patch("story.sequence.NarrativeSequence.update", return_value=True), \
                     patch.object(pygame.event, "get", side_effect=events), \
                     patch.object(main.Player, "update", move_to_inner_door), \
                     patch("ui.game_renderer.GameRenderer.draw", autospec=True,
                           side_effect=observe):
                    self.assertEqual(main.main(), 0)
                self.assertTrue(state["fade_seen"])
                self.assertIn("Casa" if direction == "enter" else "Vila do Vale",
                              state["seen"])
                saved = save_manager.read_save(path)
                self.assertEqual(saved["region"], "home" if direction == "enter" else "village")
                self.assertEqual(saved["story"], {
                    "woke_up": True,
                    "saw_silhouette": True,
                    "slime_quest_started": True,
                })
                self.assertEqual(saved["quests"]["forest_trouble"]["state"], ACTIVE)
                self.assertEqual(saved["quests"]["forest_trouble"]["progress"], 2)

            exercise("enter")
            exercise("leave")


if __name__ == "__main__":
    unittest.main()
