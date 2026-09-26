import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

import main
import save_manager
from entities.npc import nearest
from story.alden_scene import AldenScene, interact_with_alden, post_slimes_available
from story.arrival_scene import restore_resident
from story.sequence import Beat
from story.story_manager import StoryManager
from systems.combat import CombatSystem
from systems.dialogue import DialogueBox, DialogueSystem
from systems.quest import ACTIVE, COMPLETED, REWARDED, QuestManager
from ui.game_renderer import GameRenderer
from world.world_manager import WorldManager


class Prologue2ATests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((1, 1))
        self.player = main.Player(main.load("assets/player/f_player_sheet.png"),
                                  main.load("assets/player/f_player_attack_sheet.png"))
        self.story = StoryManager({"woke_up": True, "saw_silhouette": True,
                                   "slime_quest_started": True})
        self.quests = QuestManager()
        self.quests.accept("forest_trouble")
        self.inventory = []
        self.dialogue = DialogueBox()
        self.village = main.build_region("village")
        self.alden = next(npc for npc in self.village["npcs"] if npc.uid == "alden")
        self.player.x, self.player.y = self.alden.x, self.alden.y + 42

    def tearDown(self):
        pygame.quit()

    def kills(self, count=5):
        for _ in range(count):
            self.quests.enemy_defeated("slime")

    def interact(self):
        return interact_with_alden(self.alden, self.player, self.dialogue,
                                    self.quests, self.story)

    def finish_normally(self, scene):
        spoken, timed = [], []
        while scene.active:
            if scene.sequence is not None:
                timed.append(scene.sequence.current.text)
                scene.update(scene.sequence.current.duration_ms, self.dialogue,
                             self.story, self.quests, self.inventory)
            else:
                spoken.append((self.dialogue.npc.speaker_for(self.dialogue.index),
                               self.dialogue.npc.dialogue_for("default")[self.dialogue.index]))
                scene.advance(self.dialogue)
                scene.update(0, self.dialogue, self.story, self.quests, self.inventory)
        return spoken, timed

    def save_and_load(self, region_id):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "savegame.json"
            save_manager.save_game(self.player, self.inventory, self.quests, region_id,
                                   set(), [], path, story=self.story)
            return save_manager.load_game(
                path, lambda: main.Player(self.player.idle, self.player.attack_sheet),
                main.build_region, main.spawn_enemies,
                lambda: self.fail("O prólogo não pode criar o Guardião"))

    def test_four_slimes_do_not_unlock_alden(self):
        self.kills(4)
        self.assertFalse(post_slimes_available(self.quests, self.story))
        self.assertIsNone(self.interact())
        while self.dialogue.active:
            DialogueSystem().advance(self.dialogue, self.quests, self.inventory)
        self.assertEqual(self.quests.get("forest_trouble").state, ACTIVE)
        self.assertEqual(self.story.objective_text, "")
        self.assertFalse(self.story.get("alden_post_slimes_talk"))
        self.assertEqual(self.inventory, [])

    def test_five_slimes_require_interaction_with_existing_accessible_civilian(self):
        self.kills()
        self.assertTrue(post_slimes_available(self.quests, self.story))
        self.assertFalse(self.dialogue.active)
        self.assertEqual(self.story.home_phase, "home_initial")
        self.assertEqual(self.story.objective_text, "")
        self.assertIn("5/5", self.quests.active_text())
        self.assertIn("Alden", self.quests.active_text())
        self.assertIs(nearest(self.village["npcs"], self.player, self.quests), self.alden)
        self.assertFalse(any(self.player.hitbox.colliderect(box)
                             for box in self.village["obstacles"]))
        self.assertEqual(self.alden.frame_size, 32)
        self.player.invulnerability_timer = 30
        scene = self.interact()
        self.assertEqual(self.player.invulnerability_timer, 0)
        self.assertIs(scene.alden, self.alden)
        self.assertEqual(sum(npc.uid == "alden" for npc in self.village["npcs"]), 1)
        self.assertEqual(self.dialogue.npc.dialogue_for("default")[0], "Então era verdade.")
        self.assertEqual(self.quests.get("forest_trouble").state, COMPLETED)

    def test_complete_dialogue_pauses_name_and_final_objective(self):
        self.kills()
        spoken, timed = self.finish_normally(self.interact())
        self.assertEqual([text for _, text in spoken], [
            "Então era verdade.", "O quê?", "Que você sabe usar essa espada.",
            "Meu corpo sabe.", "E você não?", "Não lembro de nada.", "Nada?",
            "Acordei naquela casa.", "Não sei meu nome.", "Não sei de onde vim.",
            "Não sei por que sei lutar.", "Há alguma coisa que lembra?", "Um nome.",
            "De quem?", "Não sei.", "Qual?", "...", "Não consigo dizer.",
            "Talvez não devesse forçar.", "Preciso descobrir quem sou.",
            "Quando trouxemos você, encontramos algumas coisas lá dentro.",
            "Você disse que ela estava vazia.", "Estava.",
            "É justamente isso que me incomoda.",
        ])
        self.assertEqual({speaker for speaker, _ in spoken}, {"Alden", "Protagonista"})
        self.assertEqual(timed, [None, None, None, "*****", None, None, None])
        self.assertTrue(self.story.get("alden_post_slimes_talk"))
        self.assertTrue(self.story.get("house_investigation_unlocked"))
        self.assertEqual(self.story.objective_text, "Investigue a casa.")
        self.assertEqual(self.story.home_phase, "home_investigation")
        self.assertEqual(self.quests.get("forest_trouble").state, REWARDED)
        self.assertEqual([(item["id"], item["amount"]) for item in self.inventory], [("herb", 3)])
        self.assertFalse(self.dialogue.active)

    def test_repeated_interaction_is_contextual_without_another_reward(self):
        self.kills()
        self.finish_normally(self.interact())
        for _ in range(2):
            self.assertIsNone(self.interact())
            self.assertEqual(len(self.dialogue.npc.dialogue_for("default")), 1)
            self.assertIn("naquela casa", self.dialogue.npc.dialogue_for("default")[0])
            DialogueSystem().advance(self.dialogue, self.quests, self.inventory)
        self.assertEqual(self.inventory[0]["amount"], 3)

    def test_skip_at_every_step_matches_normal_completion(self):
        self.kills()
        original_story = self.story.to_dict()
        scene = self.interact()
        self.finish_normally(scene)
        expected_story = self.story.to_dict()
        for index, step in enumerate(AldenScene.STEPS):
            with self.subTest(step=index):
                story = StoryManager(original_story)
                quests = QuestManager()
                quests.accept("forest_trouble")
                for _ in range(5):
                    quests.enemy_defeated("slime")
                dialogue, inventory = DialogueBox(), []
                scene = interact_with_alden(self.alden, self.player, dialogue, quests, story)
                while scene.index < index:
                    if scene.sequence is None:
                        while dialogue.active:
                            scene.advance(dialogue)
                    scene.update(3000, dialogue, story, quests, inventory)
                if isinstance(step, Beat):
                    scene.advance(dialogue)
                    self.assertEqual(scene.index, index)
                self.assertTrue(scene.finish(dialogue, story, quests, inventory))
                self.assertFalse(scene.finish(dialogue, story, quests, inventory))
                self.assertEqual(story.to_dict(), expected_story)
                self.assertEqual(quests.get("forest_trouble").state, REWARDED)
                self.assertEqual(inventory[0]["amount"], 3)
                self.assertFalse(dialogue.active)
                self.assertFalse(quests.forest_event_started)

    def test_save_before_talk_keeps_conversation_available(self):
        self.kills()
        loaded = self.save_and_load("village")
        self.assertTrue(post_slimes_available(loaded.quests, loaded.story))
        self.assertEqual(loaded.quests.get("forest_trouble").state, COMPLETED)
        self.assertEqual(loaded.story.home_phase, "home_initial")
        self.assertEqual(loaded.story.objective_text, "")
        dialogue = DialogueBox()
        alden = next(npc for npc in loaded.region["npcs"] if npc.uid == "alden")
        self.assertIsNotNone(interact_with_alden(alden, loaded.player, dialogue,
                                                loaded.quests, loaded.story))
        self.assertEqual(dialogue.npc.dialogue_for("default")[0], "Então era verdade.")

    def test_save_after_talk_in_village_and_house_preserves_state(self):
        self.kills()
        self.finish_normally(self.interact())
        for region_id in ("village", "home"):
            with self.subTest(region=region_id):
                self.player.x, self.player.y = (1780, 602) if region_id == "village" else (512, 288)
                loaded = self.save_and_load(region_id)
                self.assertFalse(post_slimes_available(loaded.quests, loaded.story))
                self.assertEqual(loaded.story.objective_text, "Investigue a casa.")
                self.assertEqual(loaded.quests.get("forest_trouble").state, REWARDED)
                self.assertEqual(loaded.inventory[0]["amount"], 3)
                if region_id == "home":
                    self.assertEqual(loaded.region["story_phase"], "home_investigation")
                    self.assertEqual({obj.uid for obj in loaded.region["interactables"]},
                                     {"mirror", "sword", "house_door", "two_chairs",
                                      "second_mug", "height_marks", "damaged_letter",
                                      "broken_pendant"})
                    self.assertEqual(loaded.enemies, [])
                dialogue = DialogueBox()
                self.assertIsNone(interact_with_alden(self.alden, loaded.player, dialogue,
                                                      loaded.quests, loaded.story))
                self.assertIn("naquela casa", dialogue.npc.dialogue_for("default")[0])

    def test_legacy_rewarded_save_does_not_duplicate_herbs(self):
        self.kills()
        self.quests.claim("forest_trouble", self.inventory)
        loaded = self.save_and_load("village")
        self.assertTrue(post_slimes_available(loaded.quests, loaded.story))
        self.finish_normally(self.interact())
        self.assertEqual(self.inventory[0]["amount"], 3)

    def test_inconsistent_story_flags_are_rejected(self):
        self.kills()
        data = save_manager.snapshot(self.player, [], self.quests, "village", set(), [], self.story)
        for flags in ({"alden_post_slimes_talk": True},
                      {"house_investigation_unlocked": True},
                      {"alden_post_slimes_talk": True, "house_investigation_unlocked": True},
                      {"alden_post_slimes_talk": "yes"}):
            with self.subTest(flags=flags):
                invalid = copy.deepcopy(data)
                invalid["story"].update(flags)
                with self.assertRaises(save_manager.SaveError):
                    save_manager.validate(invalid)

    def test_resident_recognizes_completion_and_points_to_alden_without_claiming(self):
        self.kills()
        resident = restore_resident(self.village, main.load("assets/npc/civilian_customer.png"))
        text = " ".join(resident.dialogue_for("default", self.quests))
        self.assertIn("conseguiu", text)
        self.assertIn("Alden", text)
        self.assertNotIn("Pode nos ajudar?", text)
        resident.begin_interaction(self.dialogue, self.player, self.quests)
        while self.dialogue.active:
            DialogueSystem().advance(self.dialogue, self.quests, self.inventory)
        self.assertEqual(self.quests.get("forest_trouble").state, COMPLETED)
        self.assertEqual(self.inventory, [])
        self.assertFalse(self.story.get("alden_post_slimes_talk"))
        self.finish_normally(self.interact())
        self.assertIn("Slimes", resident.dialogue_for("default", self.quests)[0])

    def test_reward_keeps_forest_initial_and_all_future_content_disabled(self):
        self.kills()
        self.finish_normally(self.interact())
        world = WorldManager.for_game(main.load)
        forest = world.transition(
            "village", "forest", self.quests, set(), save_manager.prepare_region,
            lambda: self.fail("Guardião não permitido"), source_region=self.village)
        self.player.x, self.player.y = 1300, 430
        with patch.object(self.player, "update"):
            frame = CombatSystem(main.load).update(
                self.player, "forest", forest.region, forest.enemies, [],
                self.inventory, self.quests, 0)
        self.assertEqual(forest.region["story_phase"], "forest_initial")
        self.assertEqual([enemy.kind for enemy in frame.enemies], ["slime"] * 5)
        self.assertFalse(self.quests.forest_event_started)
        self.assertFalse(self.quests.forest_boss_defeated)
        self.assertFalse(self.quests.boss_loot_given)
        self.assertTrue(forest.region["north_locked"])
        self.assertFalse(forest.region.get("arena_locked"))
        self.assertFalse(world.can_transition("forest", "desert", self.quests))
        self.assertEqual(set(self.story.to_dict()), {
            "woke_up", "saw_silhouette", "slime_quest_started",
            "alden_post_slimes_talk", "house_investigation_unlocked",
        })

    def test_integrated_new_game_return_dialogue_house_save_and_load(self):
        for skip_alden in (False, True):
            with self.subTest(skip_alden=skip_alden), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "savegame.json"
                state = {"stage": "opening", "frame": None, "polls": 0,
                         "resident_seen": False, "context_seen": False,
                         "lines": [], "masked_name": False, "entry_fade": False,
                         "blocked_inputs_sent": False}

                def key(value):
                    return [pygame.event.Event(pygame.KEYDOWN, key=value)]

                def events():
                    state["polls"] += 1
                    self.assertLess(state["polls"], 180, state["stage"])
                    stage, frame = state["stage"], state["frame"]
                    if stage == "opening":
                        state["stage"] = "leave_home"
                        return key(pygame.K_F4)
                    if stage == "done":
                        return [pygame.event.Event(pygame.QUIT)]
                    if frame["arrival_scene"] is not None:
                        state["stage"] = "quest"
                        return key(pygame.K_F4)
                    if stage == "combat":
                        for enemy in frame["enemies"]:
                            if enemy.state != "DEAD":
                                enemy.receive_hit(enemy.hp, 120, 575, 0)
                    if (stage == "alden" and frame["alden_scene"] is not None
                            and not state["blocked_inputs_sent"]):
                        state["blocked_inputs_sent"] = True
                        state["save_before_blocked_inputs"] = path.read_bytes()
                        return [pygame.event.Event(pygame.KEYDOWN, key=value) for value in
                                (pygame.K_ESCAPE, pygame.K_F5, pygame.K_F9, pygame.K_v,
                                 pygame.K_i, pygame.K_SPACE, pygame.K_q)]
                    if stage in {"leave_home", "resident", "alden", "repeat", "house"}:
                        target_pos = {"leave_home": (512, 470), "resident": (582, 640),
                                      "alden": (1780, 602), "repeat": (1780, 602),
                                      "house": (540, 490)}[stage]
                        player = frame["player"]
                        if (player.x, player.y) == target_pos:
                            if skip_alden and frame["alden_scene"] is not None:
                                return key(pygame.K_F4)
                            return key(pygame.K_e)
                    if stage == "save":
                        state["stage"] = "saved"
                        return key(pygame.K_F5)
                    if stage == "load":
                        state["stage"] = "loaded"
                        return key(pygame.K_F9)
                    return []

                update_player = main.Player.update

                def move(player, keys, obstacles):
                    self.assertFalse(state["frame"] is not None
                                     and state["frame"]["alden_scene"] is not None
                                     and state["frame"]["alden_scene"].active,
                                     "Movimento não pode avançar durante a conversa")
                    update_player(player, keys, obstacles)
                    positions = {"leave_home": (512, 470), "forest": (1990, 575),
                                 "combat": (120, 575), "return": (40, 575),
                                 "resident": (582, 640), "alden": (1780, 602),
                                 "repeat": (1780, 602)}
                    if state["frame"] is not None and state["frame"]["region"]["name"] == "Vila do Vale":
                        positions["house"] = (540, 490)
                    if state["stage"] in positions:
                        player.x, player.y = positions[state["stage"]]

                draw = GameRenderer.draw

                def observe(renderer, canvas, **frame):
                    state["frame"] = frame
                    stage = state["stage"]
                    quests, story = frame["quest_manager"], frame["story"]
                    quest = quests.get("forest_trouble")
                    region, dialogue = frame["region"], frame["dialogue"]
                    scene = frame["alden_scene"]
                    self.assertFalse(quests.forest_event_started)
                    self.assertTrue(all(enemy.kind == "slime" for enemy in frame["enemies"]))
                    if stage == "quest" and frame["arrival_scene"] is None:
                        self.assertEqual(quest.state, ACTIVE)
                        state["stage"] = "forest"
                    elif stage == "forest" and region["name"] == "Floresta Mística":
                        self.assertEqual(len(frame["enemies"]), 5)
                        self.assertEqual(region["story_phase"], "forest_initial")
                        state["stage"] = "combat"
                    elif stage == "combat" and quest.state == COMPLETED:
                        self.assertEqual(quest.progress, 5)
                        self.assertIsNone(scene)
                        self.assertFalse(story.get("alden_post_slimes_talk"))
                        self.assertEqual(story.objective_text, "")
                        state["stage"] = "return"
                    elif stage == "return" and region["name"] == "Vila do Vale":
                        self.assertIsNone(scene)
                        self.assertFalse(dialogue.active)
                        state["stage"] = "resident"
                    elif stage == "resident":
                        self.assertEqual(quest.state, COMPLETED)
                        if dialogue.active:
                            state["resident_seen"] = True
                            self.assertEqual(dialogue.npc.uid, "prologue_villager")
                            self.assertNotIn("Pode nos ajudar?", dialogue.npc.dialogue_for("default", quests))
                        elif state["resident_seen"]:
                            state["herbs_before"] = next(i["amount"] for i in frame["inventory"] if i["id"] == "herb")
                            state["stage"] = "alden"
                    elif stage == "alden":
                        if scene is not None:
                            self.assertIsNone(frame["ui_mode"])
                            self.assertFalse(story.get("house_investigation_unlocked"))
                            self.assertEqual(quest.state, COMPLETED)
                            if state["blocked_inputs_sent"]:
                                self.assertEqual(path.read_bytes(), state["save_before_blocked_inputs"])
                            if scene.sequence is not None:
                                state["masked_name"] |= scene.sequence.current.text == "*****"
                            elif dialogue.active:
                                state["lines"].append(dialogue.npc.dialogue_for("default")[dialogue.index])
                        if story.get("alden_post_slimes_talk"):
                            self.assertEqual(quest.state, REWARDED)
                            self.assertEqual(story.objective_text, "Investigue a casa.")
                            herbs = next(i["amount"] for i in frame["inventory"] if i["id"] == "herb")
                            self.assertEqual(herbs, state["herbs_before"] + 3)
                            self.assertIsNone(scene)
                            state["stage"] = "repeat"
                    elif stage == "repeat":
                        if dialogue.active:
                            state["context_seen"] = True
                            self.assertIn("naquela casa", dialogue.npc.dialogue_for("default")[0])
                            self.assertIsNone(scene)
                        elif state["context_seen"]:
                            state["stage"] = "house"
                    elif stage == "house":
                        fade = frame["transition_fade"]
                        state["entry_fade"] |= fade.alpha > 0
                        if region["name"] == "Casa" and not fade.active:
                            self.assertTrue(state["entry_fade"])
                            self.assertEqual(region["story_phase"], "home_investigation")
                            self.assertIsNone(frame["narrative"])
                            self.assertIsNone(frame["arrival_scene"])
                            self.assertIsNone(scene)
                            self.assertFalse(dialogue.active)
                            state["stage"] = "save"
                    elif stage == "saved":
                        saved = save_manager.read_save(path)
                        self.assertEqual(saved["region"], "home")
                        self.assertTrue(saved["story"]["house_investigation_unlocked"])
                        state["stage"] = "load"
                    elif stage == "loaded":
                        self.assertEqual(region["name"], "Casa")
                        self.assertEqual(region["story_phase"], "home_investigation")
                        self.assertEqual(story.objective_text, "Investigue a casa.")
                        self.assertFalse(post_slimes_available(quests, story))
                        self.assertEqual({obj.uid for obj in region["interactables"]},
                                         {"mirror", "sword", "house_door", "two_chairs",
                                          "second_mug", "height_marks", "damaged_letter",
                                          "broken_pendant"})
                        self.assertIsNone(scene)
                        self.assertIsNone(frame["narrative"])
                        state["stage"] = "done"
                    return draw(renderer, canvas, **frame)

                class FastClock:
                    def tick(self, fps):
                        return 260

                with patch.object(save_manager, "SAVE_PATH", path), \
                     patch("core.game.pygame.time.Clock", FastClock), \
                     patch.object(pygame.event, "get", side_effect=events), \
                     patch.object(main.Player, "update", move), \
                     patch.object(GameRenderer, "draw", autospec=True, side_effect=observe):
                    self.assertEqual(main.main(), 0)
                self.assertEqual(state["stage"], "done")
                self.assertTrue(state["resident_seen"])
                self.assertTrue(state["context_seen"])
                if not skip_alden:
                    self.assertTrue(state["masked_name"])
                    self.assertIn("Então era verdade.", state["lines"])
                    self.assertIn("É justamente isso que me incomoda.", state["lines"])


if __name__ == "__main__":
    unittest.main()
