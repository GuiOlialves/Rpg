import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from collections import deque
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

import main
import save_manager
from story.story_manager import StoryManager
from systems.combat import CombatSystem
from systems.dialogue import DialogueBox, DialogueSystem
from systems.quest import ACTIVE, COMPLETED, REWARDED, QuestManager
from story.arrival_scene import restore_resident
from ui.game_renderer import GameRenderer
from world.world_manager import WorldManager


class PrologueStabilizationTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def tearDown(self):
        pygame.quit()

    def test_f4_completes_both_scenes_and_load_restores_villager(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "savegame.json"
            polls = [0]
            scene_seen = [False]
            scene_skipped = [False]
            finished = [False]
            home_control = [False]
            resident_states = []
            movement_calls = [0]

            def events():
                polls[0] += 1
                if polls[0] == 1:
                    return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F4)]
                if polls[0] in (2, 3):
                    return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)]
                if scene_seen[0] and not scene_skipped[0]:
                    scene_skipped[0] = True
                    return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F4)]
                if finished[0]:
                    return [pygame.event.Event(pygame.QUIT)]
                self.assertLess(polls[0], 35, "A chegada travou após o skip")
                return []

            def move_to_door(player, keys, obstacles):
                movement_calls[0] += 1
                if movement_calls[0] == 1:
                    player.x, player.y = 512, 470

            original_draw = GameRenderer.draw

            def observe(renderer, canvas, **kwargs):
                if kwargs["region"]["name"] == "Casa" and kwargs["narrative"] is None:
                    home_control[0] = True
                if kwargs["arrival_scene"] is not None:
                    scene_seen[0] = True
                if (kwargs["region"]["name"] == "Vila do Vale"
                        and kwargs["arrival_scene"] is None
                        and kwargs["quest_manager"].get("forest_trouble").state == ACTIVE):
                    resident = next(npc for npc in kwargs["region"]["npcs"]
                                    if npc.uid == "prologue_villager")
                    resident_states.append((resident.enabled, kwargs["dialogue"].active,
                                            kwargs["player"].invulnerability_timer))
                    finished[0] = True
                return original_draw(renderer, canvas, **kwargs)

            class FastClock:
                def tick(self, fps):
                    return 130

            with patch.object(save_manager, "SAVE_PATH", path), \
                 patch("core.game.pygame.time.Clock", FastClock), \
                 patch.object(pygame.event, "get", side_effect=events), \
                 patch.object(main.Player, "update", move_to_door), \
                 patch("ui.game_renderer.GameRenderer.draw", autospec=True, side_effect=observe):
                self.assertEqual(main.main(), 0)

            saved = save_manager.read_save(path)
            self.assertTrue(home_control[0])
            self.assertTrue(scene_seen[0])
            self.assertTrue(scene_skipped[0])
            self.assertGreaterEqual(movement_calls[0], 2)
            self.assertEqual(saved["region"], "village")
            self.assertEqual(saved["story"], {
                "woke_up": True,
                "saw_silhouette": True,
                "slime_quest_started": True,
            })
            self.assertEqual(saved["quests"]["forest_trouble"]["state"], ACTIVE)
            self.assertEqual(saved["quests"]["forest_trouble"]["progress"], 0)
            self.assertTrue(all(enabled and not dialogue and timer == 0
                                for enabled, dialogue, timer in resident_states))

            travel_frames = [0]
            travel_regions = []
            restored_resident = []

            def load_and_travel_events():
                travel_frames[0] += 1
                if travel_frames[0] == 1:
                    return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F9)]
                if travel_frames[0] == 4:
                    return [pygame.event.Event(pygame.QUIT)]
                return []

            travel_moves = [0]

            def travel(player, keys, obstacles):
                travel_moves[0] += 1
                if travel_moves[0] == 1:
                    player.x, player.y = 1990, 575
                elif travel_moves[0] == 2:
                    player.x, player.y = 40, 575

            def observe_travel(renderer, canvas, **kwargs):
                travel_regions.append(kwargs["region"]["name"])
                if kwargs["region"]["name"] == "Vila do Vale":
                    residents = [npc for npc in kwargs["region"]["npcs"]
                                 if npc.uid == "prologue_villager"]
                    restored_resident.append(len(residents) == 1 and residents[0].enabled)
                self.assertIsNone(kwargs["arrival_scene"])
                return original_draw(renderer, canvas, **kwargs)

            with patch.object(save_manager, "SAVE_PATH", path), \
                 patch("story.sequence.NarrativeSequence.update", return_value=True), \
                 patch.object(pygame.event, "get", side_effect=load_and_travel_events), \
                 patch.object(main.Player, "update", travel), \
                 patch("ui.game_renderer.GameRenderer.draw", autospec=True, side_effect=observe_travel):
                self.assertEqual(main.main(), 0)

            self.assertIn("Floresta Mística", travel_regions)
            self.assertEqual(travel_regions[-1], "Vila do Vale")
            self.assertTrue(all(restored_resident))
            returned_save = save_manager.read_save(path)
            self.assertEqual(returned_save["quests"]["forest_trouble"]["state"], ACTIVE)
            self.assertEqual(returned_save["quests"]["forest_trouble"]["progress"], 0)

    def test_first_forest_visit_has_five_reachable_slimes_and_no_future_encounter(self):
        forest = main.build_region("forest")
        enemies = main.spawn_enemies(forest)
        self.assertEqual(forest["story_phase"], "forest_initial")
        self.assertEqual([enemy.kind for enemy in enemies], ["slime"] * 5)
        self.assertEqual([kind for kind, _ in forest["future_enemy_spawns"]["forest_post_army"]],
                         ["warrior", "warrior"])

        step = 16
        width, height = forest["terrain"].get_size()

        def free(cell):
            x, y = cell
            if not 18 <= x <= width - 18 or not 38 <= y <= height - 12:
                return False
            box = pygame.Rect(x - 13, y - 9, 26, 18)
            return not any(box.colliderect(obstacle) for obstacle in forest["obstacles"])

        start = (128, 576)
        self.assertTrue(free(start))
        reachable = {start}
        queue = deque([start])
        while queue:
            x, y = queue.popleft()
            for cell in ((x + step, y), (x - step, y),
                         (x, y + step), (x, y - step)):
                if cell not in reachable and free(cell):
                    reachable.add(cell)
                    queue.append(cell)
        for enemy in enemies:
            self.assertFalse(any(enemy.hitbox.colliderect(obstacle)
                                 for obstacle in forest["obstacles"]))
            self.assertTrue(any(abs(x - enemy.x) <= 48 and abs(y - enemy.y) <= 48
                                for x, y in reachable), enemy.spawn_x)

        player = main.Player(main.load("assets/player/f_player_sheet.png"),
                             main.load("assets/player/f_player_attack_sheet.png"))
        player.x, player.y = forest["spawn"]["village"]
        quests = QuestManager()
        quests.accept("forest_trouble")
        inventory = []
        drops = []
        combat = CombatSystem(main.load)
        for enemy in enemies:
            enemy.state = "DEAD"
            enemy.dead_timer = 36
            result = combat.update(player, "forest", forest, enemies, drops,
                                   inventory, quests, 0)
            enemies, drops = result.enemies, result.drops
        self.assertEqual(quests.get("forest_trouble").state, COMPLETED)
        self.assertEqual(quests.get("forest_trouble").progress, 5)
        self.assertFalse(quests.forest_event_started)
        self.assertFalse(any(enemy.kind == "forest_guardian" for enemy in enemies))

        world = WorldManager.for_game(main.load)
        returned = world.transition(
            "forest", "village", quests, set(), save_manager.prepare_region,
            None, source_region=forest)
        self.assertEqual(returned.region_id, "village")
        self.assertEqual(quests.get("forest_trouble").state, COMPLETED)
        self.assertEqual(quests.get("forest_trouble").progress, 5)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "savegame.json"
            player.x, player.y = returned.spawn
            story = StoryManager({"woke_up": True, "saw_silhouette": True,
                                  "slime_quest_started": True})
            save_manager.save_game(player, inventory, quests, "village", set(), [],
                                   path, story=story)
            loaded = save_manager.load_game(
                path,
                lambda: main.Player(player.idle, player.attack_sheet),
                main.build_region, main.spawn_enemies,
                lambda: main.Enemy("forest_guardian", (1300, 430), main.load, seed=77))
            self.assertEqual(loaded.quests.get("forest_trouble").state, COMPLETED)
            self.assertEqual(loaded.quests.get("forest_trouble").progress, 5)
            self.assertTrue(loaded.story.get("slime_quest_started"))

        # Even an old rewarded save cannot trigger the guardian by walking
        # into the former arena. Only a future story event can set its flag.
        quests.claim("forest_trouble", inventory)
        self.assertEqual(quests.get("forest_trouble").state, REWARDED)
        player.x, player.y = 1300, 430
        result = combat.update(player, "forest", forest, enemies, drops,
                               inventory, quests, 0)
        self.assertFalse(quests.forest_event_started)
        self.assertFalse(any(enemy.kind == "forest_guardian" for enemy in result.enemies))

    def test_resident_dialogue_tracks_quest_without_restarting_or_claiming_it(self):
        village = main.build_region("village")
        resident = restore_resident(village, main.load("assets/npc/civilian_customer.png"))
        self.assertIs(resident, restore_resident(village, resident.sprite))
        self.assertEqual(sum(npc.uid == "prologue_villager" for npc in village["npcs"]), 1)
        quests = QuestManager()
        quests.accept("forest_trouble")
        quests.enemy_defeated("slime")
        inventory = []
        dialogue = DialogueBox()
        system = DialogueSystem()
        for state, expected_line in ((ACTIVE, "Você ainda está aqui?"),
                                     (COMPLETED, "Você voltou.")):
            self.assertEqual(quests.get("forest_trouble").state, state)
            self.assertIn(expected_line, resident.dialogue_for("default", quests)[0])
            dialogue.open(resident, quests)
            while dialogue.active:
                system.advance(dialogue, quests, inventory)
            if state == ACTIVE:
                for _ in range(4):
                    quests.enemy_defeated("slime")
        self.assertEqual(quests.get("forest_trouble").progress, 5)
        self.assertEqual(quests.get("forest_trouble").state, COMPLETED)
        self.assertEqual(inventory, [])


if __name__ == "__main__":
    unittest.main()
