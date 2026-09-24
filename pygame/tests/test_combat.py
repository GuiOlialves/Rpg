"""Cenários determinísticos para alcance, padrões, esquiva e pressão."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from collections import defaultdict
import unittest

import pygame

import main
from enemy import Enemy


class CombatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.idle = main.load("assets/player/f_player_sheet.png")
        cls.attack = main.load("assets/player/f_player_attack_sheet.png")

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def player(self, x=500, y=500):
        player = main.Player(self.idle, self.attack)
        player.x, player.y = x, y
        return player

    def enemy(self, kind, x=500, y=500):
        return Enemy(kind, (x, y), main.load, seed=77)

    def test_dash_directions_cost_cooldown_iframes_and_collision(self):
        for key, vector in ((pygame.K_d, (1, 0)), (pygame.K_a, (-1, 0)),
                            (pygame.K_w, (0, -1)), (pygame.K_s, (0, 1))):
            player = self.player()
            keys = defaultdict(bool, {key: True})
            self.assertTrue(player.start_dash(keys))
            self.assertEqual(player.sp, 50)
            self.assertFalse(player.start_dash(keys))
            self.assertFalse(player.take_damage(10, 400, 500))
            for _ in range(main.DASH_FRAMES): player.update(keys, [])
            self.assertAlmostEqual(player.x, 500 + vector[0] * 99)
            self.assertAlmostEqual(player.y, 500 + vector[1] * 99)
            self.assertEqual(player.dash_timer, 0)
            self.assertTrue(player.take_damage(10, 400, 500))
            self.assertFalse(player.start_dash(keys))
            while player.dash_cooldown: player.update(defaultdict(bool), [])
            self.assertTrue(player.start_dash(keys))
        player = self.player()
        player.facing = 3
        self.assertTrue(player.start_dash(defaultdict(bool)))
        player.update(defaultdict(bool), [])
        self.assertLess(player.y, 500)
        player = self.player()
        wall = pygame.Rect(530, 440, 18, 120)
        self.assertTrue(player.start_dash(defaultdict(bool, {pygame.K_d: True})))
        for _ in range(main.DASH_FRAMES): player.update(defaultdict(bool), [wall])
        self.assertLessEqual(player.hitbox.right, wall.left)
        self.assertEqual(player.dash_iframes, 0)
        player = self.player()
        player.sp = 9
        self.assertFalse(player.start_dash(defaultdict(bool)))
        self.assertEqual(player.sp, 9)
        player = self.player()
        self.assertTrue(player.start_dash(defaultdict(bool, {pygame.K_d: True})))
        for _ in range(main.DASH_IFRAMES):
            player.update(defaultdict(bool), [])
            self.assertFalse(player.take_damage(10))
        player.update(defaultdict(bool), [])
        self.assertTrue(player.take_damage(10))
        player = self.player(main.WORLD[0] - 25)
        self.assertTrue(player.start_dash(defaultdict(bool, {pygame.K_d: True})))
        for _ in range(main.DASH_FRAMES): player.update(defaultdict(bool), [])
        self.assertLessEqual(player.hitbox.right, main.WORLD[0])

    def test_sp_regeneration_and_attack_window(self):
        player = self.player()
        player.sp = 20
        for _ in range(main.SP_REGEN_DELAY - 1): player.update(defaultdict(bool), [])
        self.assertEqual(player.sp, 20)
        player.update(defaultdict(bool), [])
        self.assertEqual(player.sp, 21)
        self.assertTrue(player.attack())
        self.assertEqual(player.attack_box.width, 0)
        for _ in range(4): player.update(defaultdict(bool), [])
        self.assertGreater(player.attack_box.width, 0)
        ether = main.consumable("ether", 2)
        player.sp = 11
        inventory = [ether]
        accepted, _ = main.apply_inventory_action(ether, inventory, player, {"selected": ether})
        self.assertTrue(accepted)
        self.assertEqual(player.sp, 41)
        self.assertEqual(ether["amount"], 1)

    def test_melee_reach_telegraph_and_stationary_damage(self):
        for kind, gap in (("slime", 42), ("warrior", 76), ("forest_guardian", 82)):
            player = self.player(500 + gap)
            enemy = self.enemy(kind)
            enemy.attack_cooldown = 0
            health = player.hp
            seen_windup = False
            for _ in range(65):
                player.update(defaultdict(bool), [])
                enemy.update(player, [])
                if enemy.attack_phase == "windup" and not seen_windup:
                    seen_windup = True
                    self.assertEqual(player.hp, health)
            self.assertTrue(seen_windup, kind)
            self.assertLess(player.hp, health, kind)

    def test_receding_player_is_threatened_but_lateral_dodge_works(self):
        for kind, gap in (("slime", 42), ("warrior", 76)):
            player = self.player(500 + gap)
            enemy = self.enemy(kind)
            enemy._begin_attack("normal", player)
            keys = defaultdict(bool, {pygame.K_d: True})
            for _ in range(23):
                player.update(keys, [])
                enemy.update(player, [])
            self.assertLess(player.hp, player.max_hp, kind)
            player = self.player(500 + gap)
            enemy = self.enemy(kind)
            enemy._begin_attack("normal", player)
            keys = defaultdict(bool, {pygame.K_s: True})
            for _ in range(23):
                player.update(keys, [])
                enemy.update(player, [])
            self.assertEqual(player.hp, player.max_hp, kind)

    def test_guardian_patterns_direction_obstacle_recovery_and_low_hp(self):
        player = self.player(680)
        boss = self.enemy("forest_guardian")
        self.assertEqual(boss._choose_guardian_action(180), "charge")
        boss._begin_attack("charge", player)
        direction = boss.attack_direction
        for _ in range(12):
            player.y += 5
            boss.update(player, [])
        self.assertEqual(boss.attack_direction, direction)
        wall = pygame.Rect(555, 440, 25, 130)
        for _ in range(35): boss.update(player, [wall])
        self.assertLessEqual(boss.hitbox.right, wall.left)
        self.assertIn(boss.attack_phase, ("recovery", None))
        self.assertNotEqual(boss._choose_guardian_action(40), "charge")
        player.x, player.y = 500, 500
        boss.x, boss.y = 500, 500
        boss.hp = 70
        boss._begin_attack("aoe", player)
        self.assertEqual(boss.phase_timer, 26)
        hp = player.hp
        for _ in range(25): boss.update(player, [])
        self.assertEqual(player.hp, hp)
        boss.update(player, [])
        boss.update(player, [])
        self.assertLess(player.hp, hp)
        boss._begin_attack("charged", player)
        self.assertGreater(boss.phase_timer, 20)
        for _ in range(75):
            boss.update(player, [])
            if boss.attack_phase is None: break
        self.assertEqual(boss.attack_cooldown, round(boss.config["cooldown"] * 0.75))

    def test_stationary_attack_spam_has_consequences(self):
        player = self.player(450)
        player.facing = 2
        player.crit_chance = 0
        boss = self.enemy("forest_guardian")
        hits_taken = 0
        for _ in range(400):
            player.update(defaultdict(bool), [])
            player.attack()
            previous_hp = player.hp
            boss.update(player, [])
            if player.hp < previous_hp: hits_taken += 1
            if player.attack_box.colliderect(boss.hurtbox) and getattr(boss, "last_player_attack", -1) != player.attack_serial:
                if boss.receive_hit(player.current_attack_damage, player.x, player.y, player.knockback_power):
                    boss.last_player_attack = player.attack_serial
            if boss.state == "DEAD" or player.hp == 0: break
        self.assertGreaterEqual(hits_taken, 2, f"boss={boss.hp} {boss.state}, player={player.hp}")
        self.assertLess(player.hp, 75)
        if boss.state == "DEAD":
            self.assertLessEqual(player.hp, 25, "Ataque parado não deve vencer sem custo alto")

    def test_dash_and_sidestep_escape_locked_charge(self):
        for use_dash in (False, True):
            player = self.player(680)
            boss = self.enemy("forest_guardian")
            boss._begin_attack("charge", player)
            for _ in range(15):
                player.update(defaultdict(bool), [])
                boss.update(player, [])
            keys = defaultdict(bool, {pygame.K_w: True})
            if use_dash:
                self.assertTrue(player.start_dash(keys))
            for _ in range(27):
                player.update(keys, [])
                boss.update(player, [])
            self.assertEqual(player.hp, player.max_hp)
            self.assertEqual(boss.attack_direction, (1.0, 0.0))

    def test_multiple_enemies_and_zero_hp_remain_safe(self):
        player = self.player()
        enemies = [self.enemy("slime", 450), self.enemy("warrior", 575)]
        for _ in range(260):
            player.update(defaultdict(bool), [])
            for enemy in enemies: enemy.update(player, [])
        self.assertLess(player.hp, player.max_hp)
        player.hp = 0
        self.assertFalse(player.attack())
        self.assertFalse(player.start_dash(defaultdict(bool, {pygame.K_q: True})))
        for enemy in enemies: enemy.update(player, [])

    def test_knockback_recovery_and_combat_drawing(self):
        boss = self.enemy("forest_guardian")
        player = self.player(430)
        boss._begin_attack("charged", player)
        hp = boss.hp
        self.assertTrue(boss.receive_hit(12, player.x, player.y))
        self.assertEqual(boss.hp, hp - 12)
        self.assertEqual(boss.state, "ATTACK")
        self.assertLess(abs(boss.knockback_x), 2)
        # Ataque forte erra; o chefe permanece vulnerável durante a recuperação.
        player.x, player.y = 430, 640
        for _ in range(40): boss.update(player, [])
        self.assertEqual(boss.attack_phase, "recovery")
        self.assertTrue(boss.receive_hit(12, player.x, player.y))
        surface = pygame.Surface(main.VIEW)
        boss.draw(surface, (0, 0))
        player.draw(surface, (0, 0))
        region = main.build_region("forest")
        main.draw_world(surface, region, pygame.font.Font(None, 22), (0, 0), player, [boss], [], True)
        player = self.player(500)
        wall = pygame.Rect(520, 440, 20, 130)
        self.assertTrue(player.take_damage(10, 450, 500, 1.6))
        for _ in range(7): player.update(defaultdict(bool), [wall])
        self.assertLessEqual(player.hitbox.right, wall.left)


if __name__ == "__main__": unittest.main()
