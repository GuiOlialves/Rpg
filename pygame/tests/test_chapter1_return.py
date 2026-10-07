"""Focused Chapter 1A transitions, dialogue, controls and save regressions."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame
import main
import save_manager
from core.debug_checkpoints import create_checkpoint
from core.camera import camera_for
from story.arrival_scene import restore_resident
from story.chapter1_return import (
    Chapter1ReturnScene, Chapter1AldenScene, interact_with_returned_alden,
)
from story.prologue import opening_sequence
from story.prologue_3c import Prologue3CScene, EPILOGUE
from systems.dialogue import DialogueBox
from ui.game_renderer import GameRenderer
from world.world_manager import WorldManager


class Chapter1ReturnTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((1, 1))
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "chapter1.json"
        self.p = create_checkpoint("prologue_2e", load=main.load,
            build_region=main.build_region, spawn_enemies=main.spawn_enemies,
            restore_resident=restore_resident, opening_sequence=opening_sequence)
        for flag in ("red_officer_met", "red_officer_boss_ready", "red_officer_defeated",
                     "red_officer_memory_seen", "red_officer_escaped", "prologue_completed"):
            self.p.story.set(flag)
        self.p.story.apply_to_region(self.p.region)
        self.p.enemies = []
        self.returns = 0

    def tearDown(self):
        self.tmp.cleanup()
        # Game.run shuts SDL down; debug fonts belong to that SDL lifetime.
        from ui import world_renderer, debug_overlay
        world_renderer._DEBUG_LABEL_FONT = None
        debug_overlay._DEBUG_FONT = None
        pygame.quit()

    def return_home(self):
        self.returns += 1
        self.p.region_id = "village"
        self.p.region = main.build_region("village")
        restore_resident(self.p.region, main.load("assets/npc/civilian_customer.png"))
        self.p.player.x, self.p.player.y = self.p.region["spawn"]["forest"]
        return self.p.region

    def return_scene(self):
        return Chapter1ReturnScene(self.p.player, self.p.story, self.p.quests, self.return_home)

    def returned(self):
        self.return_scene().finish()
        return next(npc for npc in self.p.region["npcs"] if npc.uid == "alden")

    def save(self):
        save_manager.save_game(self.p.player, self.p.inventory, self.p.quests,
            self.p.region_id, set(), [], self.path, story=self.p.story)

    def reload(self):
        return save_manager.load_game(self.path,
            lambda: main.Player(self.p.player.idle, self.p.player.attack_sheet),
            main.build_region, main.spawn_enemies,
            lambda: main.Enemy("forest_guardian", (1300, 430), main.load))

    def drive_alden(self, scene, dialogue):
        spoken = []
        for _ in range(200):
            if not scene.active:
                return spoken
            if dialogue.active:
                spoken.append((dialogue.npc.speaker_for(dialogue.index),
                               dialogue.npc.dialogue_for("default")[dialogue.index]))
                scene.advance(dialogue)
            scene.update(200, dialogue, self.p.story, self.p.quests, self.p.inventory)
        self.fail("Alden scene did not release control")

    def test_last_question_and_existing_fade_are_preserved(self):
        self.p.story.set("prologue_completed", False)
        dialogue = DialogueBox()
        scene = Prologue3CScene(self.p.player, self.p.story, self.p.region, dialogue, main.load)
        scene.index = 2
        scene._dialogue((EPILOGUE[2],), "epilogue")
        self.assertEqual(dialogue.npc.dialogue_for("default"), ("Quem era eu?",))
        scene.advance()
        self.assertEqual(scene.phase, "ending")
        self.assertFalse(scene.update(1500))
        self.assertGreater(scene.sequence.fade.alpha, 230)
        self.assertTrue(scene.update(100))
        self.assertTrue(self.p.story.get("prologue_completed"))
        chapter = self.return_scene()
        self.assertEqual(chapter.title_alpha, 0)
        self.assertEqual(self.p.region_id, "forest")

    def test_title_pause_fades_then_returns_without_hud_or_extra_input(self):
        scene = self.return_scene()
        self.assertFalse(scene.update(650))
        scene.update(425)
        self.assertAlmostEqual(scene.title_alpha, 128, delta=1)
        scene.update(425)
        self.assertEqual(scene.title_alpha, 255)
        canvas = pygame.Surface((1024, 576))
        self.render(canvas, scene)
        self.assertEqual(canvas.get_at((16, 470))[:3], (5, 7, 10))
        self.assertNotEqual(canvas.get_at((512, 258))[:3], (0, 0, 0))
        scene.update(1650)
        scene.update(350)
        self.assertAlmostEqual(scene.title_alpha, 128, delta=1)
        scene.update(350)
        scene.update(250)
        self.assertEqual(scene.phase, "return")
        self.assertEqual(self.returns, 1)
        self.assertTrue(scene.autosave_requested)
        self.assertEqual(scene.fade.alpha, 255)
        self.assertFalse(scene.update(700))
        self.assertTrue(scene.update(700))
        self.assertFalse(scene.active)
        self.assertFalse(scene.finish())
        self.assertEqual(self.returns, 1)

    def render(self, canvas, scene=None):
        GameRenderer().draw(canvas, region=self.p.region, player=self.p.player,
            enemies=[], drops=[], camera=camera_for(self.p.player, self.p.region["terrain"].get_size()),
            debug=False, damage_numbers=[], hitstop_frames=0,
            font=pygame.font.Font(None, 22), title_font=pygame.font.Font(None, 30),
            dialogue=DialogueBox(), quest_manager=self.p.quests, ui_mode=None,
            inventory=self.p.inventory, inventory_ui={}, game_over_screen=None,
            story=self.p.story, chapter1_return_scene=scene)

    def test_return_spawn_objective_and_current_art_remain_safe(self):
        hp, sp = self.p.player.hp, self.p.player.sp
        visual = self.p.player.visual
        self.p.player.dash_cooldown = 20
        self.returned()
        self.assertEqual(self.p.player.dash_cooldown, 0)
        self.assertEqual((self.p.player.x, self.p.player.y), (1850, 575))
        self.assertFalse(any(self.p.player.hitbox.colliderect(box) for box in self.p.region["obstacles"]))
        self.assertFalse(any(self.p.player.hitbox.colliderect(box) for box in self.p.region["exits"].values()))
        self.assertEqual((self.p.player.hp, self.p.player.sp), (hp, sp))
        self.assertIs(self.p.player.visual, visual)
        self.assertEqual(visual.frame_size, (32, 36))
        self.assertEqual(self.p.story.objective_title, "Ecos da Guerra")
        self.assertEqual(self.p.story.objective_text, "Fale com Alden.")

    def test_village_reactions_keep_obstacles_and_apply_idempotently(self):
        self.returned()
        before = list(self.p.region["obstacles"])
        count = len(self.p.region["npcs"])
        for _ in range(3):
            self.p.story.apply_to_region(self.p.region)
        self.assertEqual(self.p.region["obstacles"], before)
        self.assertEqual(len(self.p.region["npcs"]), count)
        for uid in ("mira", "tomas", "prologue_villager"):
            npc = next(n for n in self.p.region["npcs"] if n.uid == uid)
            self.assertIn(npc.hitbox, before)
            self.assertTrue(npc.dialogue_for("default", self.p.quests))
        self.assertNotIn("old_road_future", self.p.region["exits"])

    def test_admission_has_a_real_pause_and_dialogue_delivers_only_the_lead(self):
        alden = self.returned()
        dialogue = DialogueBox()
        scene = interact_with_returned_alden(alden, self.p.player, dialogue,
                                             self.p.story, self.p.region)
        while scene.index < 9:
            if dialogue.active:
                scene.advance(dialogue)
            scene.update(200, dialogue, self.p.story, self.p.quests, self.p.inventory)
        self.assertFalse(dialogue.active)
        scene.advance(dialogue)
        self.assertFalse(scene.update(1000, dialogue, self.p.story, self.p.quests, self.p.inventory))
        self.assertEqual(scene.index, 9)
        self.assertFalse(self.p.story.get("chapter1_alden_talk"))
        remaining = self.drive_alden(scene, dialogue)
        text = " ".join(line for _, line in remaining)
        self.assertIn("Não entraram no Vale.", text)
        self.assertIn("A saída a oeste.", text)
        self.assertIn("Preciso descobrir o que fiz", text)
        self.assertTrue(self.p.story.get("chapter1_alden_talk"))
        self.assertEqual(self.p.story.objective_text, "Investigue a antiga estrada.")
        self.assertFalse(dialogue.active)

    def test_normal_and_skip_finish_have_the_same_state_without_extra_reward(self):
        alden = self.returned()
        inventory = deepcopy(self.p.inventory)
        dialogue = DialogueBox()
        normal = Chapter1AldenScene(alden, self.p.player, dialogue, self.p.region)
        self.drive_alden(normal, dialogue)
        flags = self.p.story.to_dict()
        self.p.story.set("chapter1_alden_talk", False)
        self.p.story.set("old_road_unlocked", False)
        skip = Chapter1AldenScene(alden, self.p.player, dialogue, self.p.region)
        self.assertTrue(skip.finish(dialogue, self.p.story, self.p.quests, self.p.inventory))
        self.assertFalse(skip.finish(dialogue, self.p.story, self.p.quests, self.p.inventory))
        self.assertEqual(self.p.story.to_dict(), flags)
        self.assertEqual(self.p.inventory, inventory)

    def test_save_before_and_after_alden_does_not_repeat_completed_events(self):
        alden = self.returned()
        for talked in (False, True):
            if talked:
                dialogue = DialogueBox()
                scene = Chapter1AldenScene(alden, self.p.player, dialogue, self.p.region)
                self.drive_alden(scene, dialogue)
            self.save()
            loaded = self.reload()
            called = []
            resume = Chapter1ReturnScene(loaded.player, loaded.story, loaded.quests,
                                         lambda: called.append(True))
            self.assertFalse(resume.active)
            self.assertFalse(resume.update(10000))
            self.assertFalse(called)
            self.assertEqual(loaded.story.get("chapter1_alden_talk"), talked)
            self.assertEqual(loaded.story.objective_text, self.p.story.objective_text)
            self.assertEqual(loaded.region["story_phase"], "village_chapter1")
            self.assertEqual("old_road" in loaded.region["exits"], talked)
            if talked:
                d = DialogueBox()
                a = next(n for n in loaded.region["npcs"] if n.uid == "alden")
                self.assertIsNone(interact_with_returned_alden(a, loaded.player, d, loaded.story, loaded.region))
                self.assertIn("A estrada antiga", d.npc.dialogue_for("default")[0])

    def test_title_already_committed_resumes_return_only_and_bad_flags_are_rejected(self):
        self.p.story.set("chapter1_started")
        self.save()
        loaded = self.reload()
        scene = Chapter1ReturnScene(self.p.player, loaded.story, self.p.quests, self.return_home)
        self.assertEqual(scene.phase, "resume")
        scene.update(1)
        self.assertEqual(scene.phase, "return")
        self.assertEqual(self.returns, 1)
        data = save_manager.read_save(self.path)
        for changes in ({"prologue_completed": False}, {"chapter1_alden_talk": True},
                        {"old_road_unlocked": True}):
            invalid = deepcopy(data)
            invalid["story"].update(changes)
            with self.assertRaises(save_manager.SaveError):
                save_manager.validate(invalid)

    def test_old_road_connection_opens_after_alden(self):
        alden = self.returned()
        dialogue = DialogueBox()
        Chapter1AldenScene(alden, self.p.player, dialogue, self.p.region).finish(
            dialogue, self.p.story, self.p.quests, self.p.inventory)
        marker = next(obj for obj in self.p.region["interactables"] if obj.uid == "old_road_marker")
        self.assertTrue(marker.available())
        world = WorldManager.for_game(main.load)
        self.assertIn("old_road", world.region_ids)
        transition = world.transition("village", "old_road", self.p.quests, set(),
            save_manager.prepare_region, None, source_region=self.p.region)
        self.assertEqual(transition.region_id, "old_road")
        self.assertEqual(transition.region["name"], "Antiga Estrada")
        self.assertEqual(transition.spawn,(1910,850))

    def test_real_game_loop_connects_epilogue_title_return_dialogue_controls_and_reload(self):
        self.p.story.set("prologue_completed", False)
        self.save()
        state = {"poll": 0, "spoken": set(),
                 "title": set(), "return": False, "stage": "return", "movement": False,
                 "attack": False, "dash": False, "talk": False, "reload": False}
        keys = defaultdict(bool)
        current = {}
        original_draw = GameRenderer.draw

        def events():
            state["poll"] += 1
            self.assertLess(state["poll"], 240)
            if state["poll"] == 1:
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F4)]
            if state["poll"] == 2:
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F9),
                        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F3)]
            if not current:
                return []
            scene = current.get("chapter1_return_scene")
            if scene is not None and scene.active:
                return [pygame.event.Event(pygame.KEYDOWN, key=k) for k in
                        (pygame.K_e, pygame.K_SPACE, pygame.K_q, pygame.K_i, pygame.K_v)]
            if current["dialogue"].active:
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)]
            player = current["player"]
            if not current["story"].get("chapter1_returned"):
                return []
            stage = state["stage"]
            if stage == "return":
                keys[pygame.K_a] = True
                state["x"] = player.x
                state["stage"] = "move"
            elif stage == "move":
                state["movement"] = player.x < state["x"]
                keys[pygame.K_a] = False
                state["stage"] = "attack"
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)]
            elif stage == "attack":
                state["attack"] |= player.attack_timer > 0
                if player.attack_timer == 0:
                    state["stage"] = "dash"
                    return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q)]
            elif stage == "dash":
                state["dash"] |= player.dash_timer > 0
                if player.dash_timer == 0:
                    player.x, player.y = 1830, 560
                    state["stage"] = "talk"
                    return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)]
            elif stage == "talk" and current["story"].get("chapter1_alden_talk"):
                state["talk"] = True
                state["stage"] = "reload"
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F9)]
            elif stage == "reload":
                self.assertIsNone(current.get("chapter1_return_scene"))
                self.assertIsNone(current.get("alden_scene"))
                self.assertTrue(current["story"].get("chapter1_alden_talk"))
                state["reload"] = True
                return [pygame.event.Event(pygame.QUIT)]
            return []

        def observe(renderer, canvas, **kwargs):
            current.update(kwargs)
            scene = kwargs.get("chapter1_return_scene")
            if scene is not None and scene.active:
                if scene.phase == "title":
                    state["title"].add(scene.sequence.index)
                else:
                    state["return"] = True
                    self.assertEqual(kwargs["region"]["name"], "Vila do Vale")
                    self.assertEqual((kwargs["player"].x, kwargs["player"].y), (1850, 575))
                self.assertIsNone(kwargs["ui_mode"])
                self.assertEqual(kwargs["player"].attack_timer, 0)
                self.assertEqual(kwargs["player"].dash_timer, 0)
            if kwargs["dialogue"].active:
                d = kwargs["dialogue"]
                state["spoken"].add(d.npc.dialogue_for("default")[d.index])
            return original_draw(renderer, canvas, **kwargs)

        class FastClock:
            def tick(self, fps):
                return 200

        with patch.object(save_manager, "SAVE_PATH", self.path), \
             patch("core.game.pygame.time.Clock", FastClock), \
             patch.object(pygame.event, "get", side_effect=events), \
             patch.object(pygame.key, "get_pressed", return_value=keys), \
             patch("ui.game_renderer.GameRenderer.draw", autospec=True, side_effect=observe):
            self.assertEqual(main.main(), 0)
        self.assertIn("Quem era eu?", state["spoken"])
        self.assertIn("Eu fazia parte deles.", state["spoken"])
        self.assertTrue({0, 1, 2, 3, 4}.issubset(state["title"]))
        for key in ("return", "movement", "attack", "dash", "talk", "reload"):
            self.assertTrue(state[key], key)
        saved = save_manager.read_save(self.path)
        self.assertTrue(saved["story"]["chapter1_alden_talk"])
        self.assertEqual(saved["region"], "village")


if __name__ == "__main__":
    unittest.main()
