"""Cenários determinísticos para alcance, padrões, esquiva e pressão."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from collections import defaultdict
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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

    def setUp(self):
        if not pygame.display.get_init():
            pygame.init()
            pygame.display.set_mode((1, 1))

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
        self.assertEqual((player.dash_feedback_kind, player.dash_feedback_timer), ("sp", 18))
        player.sp = 20
        player.dash_cooldown = 5
        self.assertFalse(player.start_dash(defaultdict(bool)))
        self.assertEqual((player.dash_feedback_kind, player.dash_feedback_timer), ("cooldown", 18))
        canvas = pygame.Surface(main.VIEW, pygame.SRCALPHA)
        main.draw_hud(canvas, player, pygame.font.Font(None, 20))
        self.assertEqual(canvas.get_at((216, main.VIEW[1] - 120 + 61))[:3], (241, 190, 91))
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
        ui_state = {"selected": ether}
        accepted, _ = main.apply_inventory_action(ether, inventory, player, ui_state)
        self.assertTrue(accepted)
        self.assertEqual(player.sp, 41)
        self.assertEqual(ether["amount"], 1)
        potion = main.consumable("potion", 2)
        player.hp = 40
        inventory.append(potion)
        accepted, notice = main.apply_inventory_action(potion, inventory, player, ui_state)
        self.assertFalse(accepted)
        self.assertIn("Aguarde", notice)
        ui_state["consumable_cooldown"] = 0
        accepted, _ = main.apply_inventory_action(potion, inventory, player, ui_state)
        self.assertTrue(accepted)
        self.assertEqual(player.hp, 70)
        self.assertEqual(ui_state["consumable_cooldown"], main.CONSUMABLE_COOLDOWN_FRAMES)

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

    def test_balanced_attack_counts_and_nonlethal_normal_enemy_damage(self):
        player = self.player()
        self.assertEqual(player.attack_damage, 13)
        self.assertEqual(main.item("iron_blade")["bonuses"]["força"], 2)
        counts = {}
        for kind in ("slime", "warrior"):
            enemy = self.enemy(kind)
            hits = 0
            while enemy.hp > 0:
                self.assertTrue(enemy.receive_hit(player.attack_damage, 0, 0))
                hits += 1
                if enemy.hp > 0:
                    enemy.state = "IDLE"
                    enemy.hurt_timer = enemy.hit_resistance_timer = 0
            counts[kind] = hits
        self.assertGreaterEqual(counts["slime"], 3)
        self.assertLessEqual(counts["slime"], 5)
        self.assertGreaterEqual(counts["warrior"], 6)
        self.assertLessEqual(counts["warrior"], 10)
        player = self.player()
        self.assertTrue(player.take_damage(4))
        slime_damage = 100 - player.hp
        player = self.player()
        self.assertTrue(player.take_damage(7))
        warrior_damage = 100 - player.hp
        self.assertLess(slime_damage, 10)
        self.assertLess(warrior_damage, 10)

    def test_enemy_opening_attacks_are_staggered_and_hitstun_has_recovery(self):
        group = [Enemy("slime", (450 + index * 40, 500), main.load, seed=index)
                 for index in range(8)]
        opening_delays = [enemy.attack_cooldown for enemy in group]
        self.assertTrue(all(0 <= delay < 24 for delay in opening_delays))
        self.assertGreater(len(set(opening_delays)), 1)

        enemy = self.enemy("slime", 560, 500)
        hp = enemy.hp
        self.assertTrue(enemy.receive_hit(1, 500, 500))
        self.assertFalse(enemy.receive_hit(1, 500, 500))
        self.assertEqual(enemy.hp, hp - 1)
        for _ in range(9):
            enemy.update(self.player(), [])
        self.assertEqual(enemy.state, "IDLE")
        self.assertTrue(enemy.receive_hit(1, 500, 500))

    def test_continue_restores_resources_but_keeps_progress(self):
        player = self.player()
        player.gain_xp(140)
        player.stat_points = 2
        blade = main.item("iron_blade")
        player.equip(blade)
        player.hp, player.sp = 0, 3
        player.x, player.y = 1300, 430
        region = main.build_region("village")
        saved = (player.level, player.current_xp, player.stat_points, dict(player.stats), player.equipment["Arma"])
        main.restore_player_after_death(player, "village", region, [])
        self.assertEqual((player.hp, player.sp), (player.max_hp, player.max_sp))
        self.assertEqual((player.level, player.current_xp, player.stat_points,
                          player.stats, player.equipment["Arma"]), saved)
        self.assertTrue(18 <= player.x <= main.WORLD[0] - 18)
        self.assertFalse(player.hitbox.collidelist(region["obstacles"]) >= 0)

    def test_safe_respawn_points_exist_in_each_region(self):
        for region_id in ("village", "forest", "desert"):
            with self.subTest(region=region_id):
                region = main.build_region(region_id)
                position = main.safe_respawn_position(region_id, region, [])
                box = pygame.Rect(round(position[0] - 13), round(position[1] - 9), 26, 18)
                self.assertFalse(any(box.colliderect(obstacle) for obstacle in region["obstacles"]))
                self.assertTrue(18 <= position[0] <= region["terrain"].get_width() - 18)
                self.assertTrue(38 <= position[1] <= region["terrain"].get_height() - 12)

    def test_game_over_screen_controls_fade_and_drawing(self):
        screen = main.game_over.GameOverScreen()
        canvas = pygame.Surface(main.VIEW)
        font, title = pygame.font.Font(None, 22), pygame.font.Font(None, 30)
        self.assertIsNone(screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
                                              (0, 0), main.VIEW))
        for _ in range(main.game_over.FADE_FRAMES): screen.update()
        screen.draw(canvas, font, title)
        self.assertTrue(screen.ready)
        self.assertEqual(screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
                                             (0, 0), main.VIEW), "continue")
        screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN), (0, 0), main.VIEW)
        self.assertEqual(screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
                                             (0, 0), main.VIEW), "load")
        rect = screen.button_rects(main.VIEW)[2]
        click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)
        self.assertEqual(screen.handle_event(click, rect.center, main.VIEW), "quit")

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

    def test_main_death_flow_ignores_combat_and_saving_then_continues(self):
        batches = [[] for _ in range(37)] + [
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F5)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)],
            [pygame.event.Event(pygame.QUIT)],
        ]
        died = False

        def die_once(player, keys, obstacles):
            nonlocal died
            if not died:
                died = True
                player.hp = 0

        with tempfile.TemporaryDirectory() as directory:
            save_path = Path(directory) / "savegame.json"
            with patch.object(main.Player, "update", die_once), \
                 patch.object(main.Player, "start_dash") as dash, \
                 patch.object(main, "restore_player_after_death", wraps=main.restore_player_after_death) as respawn, \
                 patch("story.sequence.NarrativeSequence.update", return_value=True), \
                 patch.object(main.save_manager, "SAVE_PATH", save_path), \
                 patch.object(pygame.event, "get", side_effect=batches):
                self.assertEqual(main.main(), 0)
            dash.assert_not_called()
            respawn.assert_called_once()
            self.assertFalse(save_path.exists(), "F5 durante Game Over não pode salvar HP zero")

    def test_death_reset_restarts_unfinished_guardian_arena(self):
        region, enemies = main.reset_forest_boss_encounter()
        self.assertEqual(len(enemies), 1)
        self.assertEqual((enemies[0].kind, enemies[0].hp), ("forest_guardian", enemies[0].max_hp))
        self.assertTrue(region["arena_locked"])
        self.assertTrue(region["north_locked"])
        self.assertIn(region["exits"]["desert"].inflate(30, 20), region["obstacles"])


if __name__ == "__main__": unittest.main()
