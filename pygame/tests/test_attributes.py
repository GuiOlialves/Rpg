"""Cobertura das fórmulas, combate e controles do menu de atributos."""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame

import attributes
from equipment import item
from enemy import Enemy
import main
import save_manager


class AttributeTests(unittest.TestCase):
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

    def player(self):
        return main.Player(self.idle, self.attack)

    def test_each_primary_stat_changes_derived_without_full_heal(self):
        player = self.player()
        self.assertEqual((player.max_hp, player.max_sp, player.physical_attack, player.magic_power),
                         (100, 60, 13, 13))
        player.hp, player.sp = 72, 24
        player.stat_points = 4
        before_defense = player.defense
        before_knockback = player.knockback_power
        before_speed = player.speed
        before_crit = player.crit_chance
        self.assertTrue(player.spend_stat("vitalidade"))
        self.assertEqual((player.hp, player.max_hp), (77, 105))
        self.assertGreater(player.defense, before_defense)
        self.assertTrue(player.spend_stat("força"))
        self.assertEqual(player.physical_attack, 14)
        self.assertGreater(player.knockback_power, before_knockback)
        self.assertTrue(player.spend_stat("magia"))
        self.assertEqual((player.sp, player.max_sp), (28, 64))
        self.assertGreater(player.magic_power, 13)
        self.assertTrue(player.spend_stat("agilidade"))
        self.assertGreater(player.speed, before_speed)
        self.assertGreater(player.crit_chance, before_crit)
        self.assertEqual(player.stat_points, 0)
        self.assertFalse(player.spend_stat("força"))
        self.assertEqual(player.stat_points, 0)

    def test_equipment_and_modifiers_recalculate_without_accumulating(self):
        player = self.player()
        base = dict(player.stats)
        player.hp, player.sp = 61, 22
        blade, armor, charm = item("iron_blade"), item("reinforced_leather"), item("grove_charm")
        player.equip(blade)
        self.assertEqual((player.final_stats["força"], player.physical_attack), (10, 15))
        self.assertEqual(player.equipment_bonus["força"], 2)
        player.equip(armor)
        self.assertEqual((player.max_hp, player.hp), (110, 71))
        self.assertGreater(player.defense, 8.5)
        player.equip(charm)
        self.assertEqual((player.max_hp, player.hp), (115, 76))
        previous = (dict(player.final_stats), player.physical_attack, player.defense)
        for _ in range(3):
            player.recalculate_stats()
            self.assertEqual((player.final_stats, player.physical_attack, player.defense), previous)
        player.modifiers["physical_attack"] = 3
        player.recalculate_stats()
        self.assertEqual(player.physical_attack, 18)
        self.assertEqual(player.stats, base)
        player.unequip("Armadura")
        self.assertEqual(player.max_hp, 105)
        self.assertEqual(player.stats, base)

    def test_agility_bounds_crit_cooldown_and_full_animation(self):
        player = self.player()
        initial_cooldown = player.attack_cooldown_frames
        player.stats["agilidade"] = 14
        player.recalculate_stats()
        self.assertLess(player.attack_cooldown_frames, initial_cooldown)
        player.stats["agilidade"] = 1000
        player.recalculate_stats()
        self.assertEqual(player.speed, attributes.MAX_MOVE_SPEED)
        self.assertEqual(player.crit_chance, attributes.MAX_CRIT_CHANCE)
        self.assertEqual(player.attack_cooldown_frames, attributes.ATTACK_ANIMATION_FRAMES)
        with patch("main.random.random", return_value=0.0):
            self.assertTrue(player.attack())
        self.assertTrue(player.attack_is_critical)
        self.assertEqual(player.current_attack_damage, round(player.attack_damage * 1.5))
        self.assertFalse(player.attack())
        for _ in range(attributes.ATTACK_ANIMATION_FRAMES):
            player.update(pygame.key.get_pressed(), [])
        self.assertEqual(player.attack_timer, 0)
        self.assertEqual(player.attack_cooldown_timer, 0)
        with patch("main.random.random", return_value=1.0):
            self.assertTrue(player.attack())
        self.assertFalse(player.attack_is_critical)
        self.assertEqual(player.current_attack_damage, player.attack_damage)

    def test_defense_reduces_damage_and_feedback_fades(self):
        player = self.player()
        initial_hp = player.hp
        self.assertTrue(player.take_damage(18))
        taken = initial_hp - player.hp
        self.assertLess(taken, 18)
        self.assertGreaterEqual(taken, 1)
        self.assertEqual(attributes.physical_damage_after_defense(3, 100000), 1)
        self.assertFalse(player.take_damage(18))  # janela de invulnerabilidade existente

        enemy = Enemy("slime", (500, 500), main.load)
        before = enemy.hp
        self.assertTrue(enemy.receive_hit(12, 470, 500, player.knockback_power))
        self.assertEqual(before - enemy.hp, 12)
        canvas = pygame.Surface(main.VIEW, pygame.SRCALPHA)
        number = main.DamageNumber("12!", 500, 440, (255, 210, 103), critical=True)
        number.draw(canvas, (0, 0), pygame.font.Font(None, 22), pygame.font.Font(None, 30))
        self.assertIsNotNone(canvas.get_bounding_rect())
        for _ in range(42):
            alive = number.update()
        self.assertFalse(alive)

    def test_preview_mouse_keyboard_menu_save_and_regions(self):
        player = self.player()
        player.stat_points = 1
        before = dict(player.derived)
        preview = player.preview_stat("vitalidade")
        self.assertEqual(preview["max_hp"], before["max_hp"] + 5)
        self.assertEqual(player.stats["vitalidade"], 10)
        plus = main.character_attribute_layout()[0][4]
        self.assertTrue(main.handle_character_click(plus.center, player))
        self.assertEqual((player.stats["vitalidade"], player.stat_points), (11, 0))
        self.assertFalse(main.handle_character_click(plus.center, player))
        self.assertIsNone(player.preview_stat("vitalidade"))
        canvas = pygame.Surface(main.VIEW, pygame.SRCALPHA)
        main.draw_character_menu(canvas, player, pygame.font.Font(None, 22),
                                 pygame.font.Font(None, 30), plus.center)
        self.assertTrue(canvas.get_bounding_rect().width > 0)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "savegame.json"
            original_init = main.Player.__init__

            def leveled_player(character, idle, attack):
                original_init(character, idle, attack)
                character.gain_xp(275)

            def step_to_exit(character, keys, obstacles):
                if character.x == 1024 and character.y == 576:
                    character.x, character.y = 1990, 575

            plus_window = (plus.centerx * main.WINDOW[0] // main.VIEW[0],
                           plus.centery * main.WINDOW[1] // main.VIEW[1])
            events = [
                [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_v),
                 pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=plus_window),
                 pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1),
                 pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2),
                 pygame.event.Event(pygame.KEYDOWN, key=pygame.K_3),
                 pygame.event.Event(pygame.KEYDOWN, key=pygame.K_4)],
                [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_v)],
                [pygame.event.Event(pygame.QUIT)],
            ]
            with patch.object(main.Player, "__init__", leveled_player), \
                 patch.object(main.Player, "update", step_to_exit), \
                 patch("story.sequence.NarrativeSequence.update", return_value=True), \
                 patch.object(save_manager, "SAVE_PATH", path), \
                 patch.object(pygame.event, "get", side_effect=events):
                self.assertEqual(main.main(), 0)
            saved = save_manager.read_save(path)
            self.assertEqual(saved["region"], "home")
            self.assertEqual(saved["player"]["stats"]["vitalidade"], 12)
            self.assertEqual(saved["player"]["stats"]["força"], 9)
            self.assertEqual(saved["player"]["stats"]["magia"], 7)
            self.assertEqual(saved["player"]["stats"]["agilidade"], 10)
            self.assertEqual(saved["player"]["stat_points"], 1)

        stable = (dict(player.stats), dict(player.final_stats), dict(player.derived))
        pygame.init()
        pygame.display.set_mode((1, 1))
        main.build_region("village")
        main.build_region("forest")
        self.assertEqual((player.stats, player.final_stats, player.derived), stable)


if __name__ == "__main__":
    unittest.main()
