"""Exercita Save/Load com os objetos e mapas reais do jogo."""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame

import main
from enemy import Drop, Enemy
from equipment import item
from items import consumable
from quest import ACTIVE, COMPLETED, REWARDED, QuestManager
import save_manager


class SaveLoadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.idle = main.load("assets/player/f_player_sheet.png")
        cls.attack = main.load("assets/player/f_player_attack_sheet.png")

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        if not pygame.display.get_init():
            pygame.init()
            pygame.display.set_mode((1, 1))
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "savegame.json"

    def player(self):
        return main.Player(self.idle, self.attack)

    def load(self):
        return save_manager.load_game(
            self.path, self.player, main.build_region, main.spawn_enemies,
            lambda: Enemy("forest_guardian", (1300, 430), main.load, seed=77))

    def save(self, player, inventory, quests, region="village", chests=None, drops=None):
        save_manager.save_game(player, inventory, quests, region, chests or set(), drops or [], self.path)

    def starter(self):
        return [consumable("potion", 3), consumable("ether", 2), consumable("herb", 5),
                item("iron_blade"), item("reinforced_leather")]

    def test_full_adventure_round_trip_and_repeated_load(self):
        player, inventory, quests = self.player(), self.starter(), QuestManager()
        player.gain_xp(275)
        self.assertEqual(player.level, 3)
        player.spend_stat("vitalidade")
        player.spend_stat("força")
        player.hp -= 20
        main.apply_inventory_action(inventory[0], inventory, player, {"selected": inventory[0]})
        inventory.append(item("grove_charm"))
        player.equip(inventory[3])
        player.equip(inventory[-1])
        player.hp -= 27
        player.sp -= 19
        quests.accept("forest_trouble")
        for _ in range(5):
            quests.enemy_defeated("slime")
        self.assertEqual(quests.get("forest_trouble").state, COMPLETED)
        self.assertTrue(quests.claim("forest_trouble", inventory))
        quests.forest_event_started = True
        quests.forest_boss_defeated = True
        quests.boss_loot_given = True
        player.x, player.y = 1025, 105
        drop = Drop(consumable("ether", 2), 1100, 140, 4500)
        self.save(player, inventory, quests, "desert", {"desert_chest_ruins"}, [drop])

        expected = (player.level, player.current_xp, player.xp_to_next_level,
                    player.stat_points, dict(player.stats), player.hp, player.sp,
                    dict(player.final_stats), player.attack_damage, player.speed)
        for _ in range(2):
            loaded = self.load()  # novo Player, QuestManager e mapa; como após reiniciar
            restored = loaded.player
            self.assertEqual((restored.level, restored.current_xp, restored.xp_to_next_level,
                              restored.stat_points, restored.stats, restored.hp, restored.sp,
                              restored.final_stats, restored.attack_damage, restored.speed), expected)
            self.assertEqual(loaded.region_id, "desert")
            self.assertEqual((restored.x, restored.y), (1025, 105))
            self.assertEqual({entry["id"]: entry.get("amount", 1) for entry in loaded.inventory}["potion"], 2)
            self.assertEqual(restored.equipment["Arma"]["id"], "iron_blade")
            self.assertEqual(restored.equipment["Acessório"]["id"], "grove_charm")
            self.assertIs(restored.equipment["Arma"], next(entry for entry in loaded.inventory if entry["id"] == "iron_blade"))
            self.assertEqual(loaded.quests.get("forest_trouble").state, REWARDED)
            self.assertFalse(loaded.quests.claim("forest_trouble", loaded.inventory))
            self.assertTrue(loaded.quests.forest_boss_defeated)
            self.assertIn("desert_chest_ruins", loaded.opened_chests)
            self.assertTrue(next(chest for chest in loaded.region["interactables"] if chest.uid == "desert_chest_ruins").opened)
            self.assertEqual((loaded.drops[0].item["id"], loaded.drops[0].lifetime), ("ether", 4500))

    def test_missing_corrupt_incomplete_and_failed_atomic_write(self):
        with self.assertRaises(save_manager.MissingSaveError):
            self.load()
        self.path.write_text("{quebrado", encoding="utf-8")
        original = self.path.read_bytes()
        with self.assertRaises(save_manager.SaveError):
            self.load()
        self.assertEqual(self.path.read_bytes(), original)
        self.path.write_text('{"save_version": 1}', encoding="utf-8")
        with self.assertRaises(save_manager.SaveError):
            self.load()
        player, inventory, quests = self.player(), self.starter(), QuestManager()
        self.save(player, inventory, quests)
        good = self.path.read_bytes()
        with patch("save_manager.os.replace", side_effect=OSError("falha simulada")):
            with self.assertRaises(save_manager.SaveError):
                self.save(player, inventory, quests)
        self.assertEqual(self.path.read_bytes(), good)
        self.assertEqual(list(Path(self.directory.name).glob(".savegame-*.tmp")), [])

    def test_regions_position_fallback_active_quest_and_guardian(self):
        player, inventory, quests = self.player(), self.starter(), QuestManager()
        quests.accept("forest_trouble")
        quests.enemy_defeated("slime")
        for region_id, position in (("village", (1024, 576)), ("forest", (120, 575))):
            player.x, player.y = position
            self.save(player, inventory, quests, region_id)
            loaded = self.load()
            self.assertEqual(loaded.region_id, region_id)
            self.assertEqual((loaded.player.x, loaded.player.y), position)
            self.assertEqual(loaded.quests.get("forest_trouble").state, ACTIVE)
            self.assertEqual(loaded.quests.get("forest_trouble").progress, 1)

        for _ in range(4):
            quests.enemy_defeated("slime")
        player.x, player.y = 1500, 250  # água profunda
        self.save(player, inventory, quests, "forest")
        completed = self.load()
        self.assertEqual(completed.quests.get("forest_trouble").state, COMPLETED)
        self.assertEqual(completed.quests.get("forest_trouble").progress, 5)
        self.assertNotEqual((completed.player.x, completed.player.y), (1500, 250))
        self.assertTrue(completed.quests.claim("forest_trouble", completed.inventory))
        self.assertFalse(completed.quests.claim("forest_trouble", completed.inventory))
        quests.claim("forest_trouble", inventory)
        quests.forest_event_started = True
        player.x, player.y = 1300, 430  # local exato do Guardião: deve cair no spawn seguro
        self.save(player, inventory, quests, "forest")
        loaded = self.load()
        self.assertEqual(loaded.quests.get("forest_trouble").state, REWARDED)
        self.assertTrue(loaded.region["arena_locked"])
        self.assertTrue(loaded.region["north_locked"])
        self.assertEqual([enemy.kind for enemy in loaded.enemies], ["forest_guardian"])
        self.assertNotEqual((loaded.player.x, loaded.player.y), (1300, 430))
        self.assertFalse(loaded.player.hitbox.colliderect(loaded.enemies[0].hitbox))
        returned_region, returned_enemies = save_manager.prepare_region(
            "forest", loaded.quests, set(), main.build_region, main.spawn_enemies,
            lambda: Enemy("forest_guardian", (1300, 430), main.load, seed=77))
        self.assertTrue(returned_region["arena_locked"])
        self.assertEqual([enemy.kind for enemy in returned_enemies], ["forest_guardian"])

    def test_invalid_version_and_equipment_do_not_apply(self):
        player, inventory, quests = self.player(), self.starter(), QuestManager()
        self.save(player, inventory, quests)
        import json
        data = json.loads(self.path.read_text(encoding="utf-8"))
        data["save_version"] = 2
        self.path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(save_manager.SaveError):
            self.load()
        data["save_version"] = 1
        data["equipment"]["Arma"] = "grove_charm"
        self.path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(save_manager.SaveError):
            self.load()
        data["equipment"]["Arma"] = None
        data["player"]["xp_to_next_level"] = 101
        self.path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(save_manager.SaveError):
            save_manager.read_save(self.path)
        self.assertEqual(player.stats["força"], 8)
        self.assertEqual(quests.get("forest_trouble").state, "AVAILABLE")

    def test_main_loop_f5_f9_and_quit(self):
        with patch.object(save_manager, "SAVE_PATH", self.path):
            with patch.object(pygame.event, "get", side_effect=[
                [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F5)],
                [pygame.event.Event(pygame.QUIT)],
            ]):
                self.assertEqual(main.main(), 0)
            with patch.object(pygame.event, "get", side_effect=[
                [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F9)],
                [pygame.event.Event(pygame.QUIT)],
            ]):
                self.assertEqual(main.main(), 0)
        self.assertTrue(self.path.exists())
        self.assertEqual(save_manager.read_save(self.path)["region"], "village")

    def test_autosave_after_region_transition(self):
        def step_to_exit(player, keys, obstacles):
            if player.x == 1024 and player.y == 576:
                player.x, player.y = 1990, 575

        with patch.object(save_manager, "SAVE_PATH", self.path), \
             patch.object(main.Player, "update", step_to_exit), \
             patch.object(pygame.event, "get", side_effect=[[], [pygame.event.Event(pygame.QUIT)]]):
            self.assertEqual(main.main(), 0)
        self.assertEqual(save_manager.read_save(self.path)["region"], "forest")

    def test_corrupt_save_is_not_overwritten_by_autosave(self):
        self.path.write_text("{save interrompido", encoding="utf-8")
        original = self.path.read_bytes()

        def step_to_exit(player, keys, obstacles):
            if player.x == 1024 and player.y == 576:
                player.x, player.y = 1990, 575

        with patch.object(save_manager, "SAVE_PATH", self.path), \
             patch.object(main.Player, "update", step_to_exit), \
             patch.object(pygame.event, "get", side_effect=[[], [pygame.event.Event(pygame.QUIT)]]):
            self.assertEqual(main.main(), 0)
        self.assertEqual(self.path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
