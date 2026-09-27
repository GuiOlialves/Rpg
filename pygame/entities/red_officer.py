"""Sword duelist built on Enemy's movement, sprites and player damage contract."""
import math
import pygame
from entities.enemy import Enemy


class RedOfficer(Enemy):
    # Frames at the existing 60 Hz combat rate. Every strike locks its aim
    # when its visible windup begins; follow-ups have their own warning.
    PHASES = (
        {"speed": 3.25, "cooldown": 18, "quick": 22, "heavy": 36, "lunge": 30, "recovery": 32},
        {"speed": 3.65, "cooldown": 11, "quick": 19, "heavy": 32, "lunge": 27, "recovery": 27},
        {"speed": 4.0, "cooldown": 6, "quick": 17, "heavy": 29, "lunge": 25, "recovery": 23},
    )

    def __init__(self, position, load, *, defeat_hp):
        super().__init__("red_officer", position, load, seed=303)
        if not 0 < defeat_hp < self.max_hp:
            raise ValueError("The officer must stop fighting at a positive HP threshold.")
        self.defeat_hp = defeat_hp
        self.hostile = True
        self.boss_battle_active = True
        self.attack_cooldown = 45
        self.combo_remaining = 0
        self.reposition_timer = 0
        self.reposition_direction = (0, 0)
        self.actions_taken = 0
        self.observed_attack_serial = -1

    @property
    def phase(self):
        return 0 if self.hp > self.max_hp * .7 else 1 if self.hp > self.max_hp * .4 else 2

    @property
    def tuning(self):
        return self.PHASES[self.phase]

    def drop(self):
        return None

    def receive_hit(self, damage, from_x, from_y, knockback=1.0):
        if self.state == "DEFEATED" or self.hit_resistance_timer > 0:
            return False
        self.hp = max(self.defeat_hp, self.hp - damage)
        self.hit_resistance_timer = 7
        # A committed attack can take damage but cannot be stun-locked.
        # Recovery remains stationary and fully punishable.
        if self.hp <= self.defeat_hp:
            self.state = "DEFEATED"
            self.hostile = self.boss_battle_active = False
            self.attack_zone = self.attack_action = self.attack_phase = None
            self.combo_remaining = self.reposition_timer = 0
        return True

    def _start_strike(self, action, player):
        self.state = "ATTACK"
        self.attack_action = action
        self.attack_phase = "windup"
        self.attack_direction = self._direction_to(player)
        self.facing = -1 if self.attack_direction[0] < 0 else 1
        self.phase_timer = self.tuning[{"normal": "quick", "charged": "heavy", "charge": "lunge"}[action]]
        self.attack_hit = False
        self.attack_zone = None
        self.anim_tick = 0

    def _strike_box(self, action=None):
        reach = 112 if (action or self.attack_action) == "charged" else 72
        dx, dy = self.attack_direction
        # Same cardinal direction is used for the warning and the live hitbox.
        if abs(dx) >= abs(dy):
            return pygame.Rect(round(self.x + (10 if dx >= 0 else -reach - 10)), round(self.y - 26), reach, 52)
        return pygame.Rect(round(self.x - 26), round(self.y + (10 if dy >= 0 else -reach - 10)), 52, reach)

    def _approach(self, player, obstacles, speed):
        dx, dy = self._direction_to(player)
        if not self._move(dx * speed, dy * speed, obstacles):
            # Sliding along either axis avoids getting stuck on a corner.
            if not self._move(dx * speed, 0, obstacles):
                self._move(0, dy * speed, obstacles)
        self.facing = -1 if dx < 0 else 1

    def update(self, player, obstacles):
        if self.state == "DEFEATED" or not self.hostile:
            return True
        self.anim_tick += 1
        self.hit_resistance_timer = max(0, self.hit_resistance_timer - 1)
        if self.state == "ATTACK":
            self.phase_timer -= 1
            if self.attack_phase == "windup":
                if self.phase_timer <= 0:
                    self.attack_phase = "active"
                    self.phase_timer = 12 if self.attack_action == "charge" else 5
                return True
            if self.attack_phase == "active":
                if self.attack_action == "charge":
                    dx, dy = self.attack_direction
                    # Small substeps prevent crossing walls during the advance.
                    for _ in range(2):
                        if not self._move(dx * 5.5, dy * 5.5, obstacles):
                            self.phase_timer = 0
                            break
                    zone = self.hitbox.inflate(12, 12)
                else:
                    zone = self._strike_box()
                self.attack_zone = zone
                power = 1.45 if self.attack_action == "charged" else 1.15 if self.attack_action == "charge" else 1
                if not self.attack_hit and zone.colliderect(player.hitbox):
                    if player.take_damage(round(self.damage * power), self.x, self.y, 1):
                        self.attack_hit = True
                if self.phase_timer <= 0:
                    self.attack_phase = "recovery"
                    self.attack_zone = None
                    self.phase_timer = 12 if self.combo_remaining else self.tuning["recovery"]
                return True
            if self.phase_timer <= 0:
                if self.combo_remaining:
                    self.combo_remaining -= 1
                    self._start_strike("charged" if not self.combo_remaining else "normal", player)
                else:
                    self.state = "CHASE"
                    self.attack_phase = self.attack_action = None
                    self.attack_cooldown = self.tuning["cooldown"]
            return True
        if self.reposition_timer:
            self.reposition_timer -= 1
            dx, dy = self.reposition_direction
            self._move(dx * 4, dy * 4, obstacles)
            return True
        self.attack_cooldown = max(0, self.attack_cooldown - 1)
        distance = math.hypot(player.x - self.x, player.y - self.y)
        self.state = "CHASE"
        if (player.attack_timer > 0 and player.attack_serial != self.observed_attack_serial
                and distance < 95 and self.attack_cooldown == 0):
            self.observed_attack_serial = player.attack_serial
            dx, dy = self._direction_to(player)
            self.reposition_direction = (-dy, dx) if self.actions_taken % 2 else (dy, -dx)
            self.reposition_timer = 7 + self.phase * 2
            return True
        if not self.attack_cooldown and distance < 235:
            self.actions_taken += 1
            if distance > 112:
                action = "charge"
            else:
                action = "charged" if self.actions_taken % (3 - min(1, self.phase)) == 0 else "normal"
            self.combo_remaining = (self.phase if action == "normal" else 0)
            self._start_strike(action, player)
        else:
            self._approach(player, obstacles, self.tuning["speed"])
        return True

    @property
    def depth(self):
        return self.y

    def draw(self, canvas, camera, player=None):
        if self.state == "DEFEATED":
            size = self.config["frame_size"]
            frame = self.idle_sheet.subsurface((0, 0, size, size))
            image = pygame.transform.scale(frame, (94, 94))
            image = pygame.transform.rotate(image.subsurface(image.get_bounding_rect()), -55)
            canvas.blit(image, (round(self.x - image.get_width() / 2 - camera[0]),
                                round(self.y - image.get_height() / 2 - camera[1])))
        else:
            super().draw(canvas, camera)
