"""Estado, movimento e ações do personagem controlado pelo jogador."""
import math
import random
import pygame

from core.config import (
    WORLD, STAT_POINTS_PER_LEVEL, DASH_SP_COST, DASH_FRAMES, DASH_SPEED,
    DASH_COOLDOWN_FRAMES, DASH_IFRAMES, PLAYER_HIT_IFRAMES,
    SP_REGEN_DELAY, SP_REGEN_INTERVAL,
)
from systems import progression as attributes
from systems.equipment import SLOTS


def frame(sheet, index, direction):
    return sheet.subsurface((index * 64, direction * 64, 64, 64))


class Player:
    def __init__(self, idle, attack):
        self.idle, self.attack_sheet = idle, attack
        self.x, self.y = 1024.0, 576.0
        self.facing = 0
        self.walk_frame = self.walk_timer = self.attack_timer = 0
        self.attack_cooldown_timer = 0
        self.attack_is_critical = False
        self.speed = 3.0
        self.max_hp, self.hp = 100, 100
        self.max_sp, self.sp = 60, 60
        self.stats = {"vitalidade": 10, "força": 8, "magia": 6, "agilidade": 9}
        self.level, self.current_xp, self.xp_to_next_level, self.stat_points = 1, 0, 100, 0
        self.equipment = {slot: None for slot in SLOTS}
        self.modifiers = {}  # espaço para buffs e debuffs futuros
        self.invulnerability_timer = 0
        self.dash_timer = self.dash_cooldown = self.dash_iframes = 0
        self.dash_dx = self.dash_dy = 0.0
        self.dash_trail = []
        self.dash_feedback_timer = 0
        self.dash_feedback_kind = ""
        self.sp_idle_frames = 0
        self.knockback_x = self.knockback_y = 0.0
        self.knockback_frames = 0
        self.attack_serial = 0
        self.recalculate_stats()

    def recalculate_stats(self):
        old_hp, old_sp = self.max_hp, self.max_sp
        self.final_stats, self.equipment_bonus, self.derived = attributes.calculate(
            self.stats, self.equipment, self.modifiers)
        self.max_hp, self.max_sp = self.derived["max_hp"], self.derived["max_sp"]
        self.hp = min(self.max_hp, self.hp + max(0, self.max_hp - old_hp))
        self.sp = min(self.max_sp, self.sp + max(0, self.max_sp - old_sp))
        self.speed = self.derived["move_speed"]
        self.physical_attack = self.derived["physical_attack"]
        self.magic_power = self.derived["magic_power"]
        self.defense = self.derived["defense"]
        self.attack_cooldown_frames = self.derived["attack_cooldown"]
        self.crit_chance = self.derived["crit_chance"]
        self.crit_multiplier = self.derived["crit_multiplier"]
        self.knockback_power = self.derived["knockback_power"]

    def recalculate_derived(self):
        self.recalculate_stats()

    def preview_stat(self, name):
        if name not in self.stats or self.stat_points <= 0:
            return None
        preview = dict(self.stats)
        preview[name] += 1
        return attributes.calculate(preview, self.equipment, self.modifiers)[2]

    def equip(self, equipment):
        old = self.equipment.get(equipment["slot"]); self.equipment[equipment["slot"]] = equipment
        self.recalculate_stats(); return old

    def unequip(self, slot):
        old = self.equipment.get(slot); self.equipment[slot] = None; self.recalculate_stats(); return old

    def xp_required(self, level=None):
        return 100 + ((level or self.level) - 1) * 55

    def gain_xp(self, amount):
        self.current_xp += amount; levels = 0
        while self.current_xp >= self.xp_to_next_level:
            self.current_xp -= self.xp_to_next_level; self.level += 1
            self.stat_points += STAT_POINTS_PER_LEVEL; self.xp_to_next_level = self.xp_required(); levels += 1
        if levels: self.recalculate_stats(); self.hp, self.sp = self.max_hp, self.max_sp
        return levels

    def spend_stat(self, name):
        if self.stat_points <= 0 or name not in self.stats: return False
        self.stat_points -= 1; self.stats[name] += 1; self.recalculate_stats(); return True

    @property
    def hitbox(self):
        return pygame.Rect(round(self.x - 13), round(self.y - 9), 26, 18)

    def update(self, keys, obstacles):
        if self.invulnerability_timer > 0:
            self.invulnerability_timer -= 1
        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= 1
        if self.dash_cooldown > 0: self.dash_cooldown -= 1
        if self.dash_iframes > 0: self.dash_iframes -= 1
        if self.dash_feedback_timer > 0: self.dash_feedback_timer -= 1
        self.dash_trail = [(x, y, age - 1) for x, y, age in self.dash_trail if age > 1]
        self.sp_idle_frames += 1
        if self.sp_idle_frames >= SP_REGEN_DELAY and (self.sp_idle_frames - SP_REGEN_DELAY) % SP_REGEN_INTERVAL == 0:
            self.sp = min(self.max_sp, self.sp + 1)
        if self.knockback_frames > 0:
            self._move(self.knockback_x, 0, obstacles); self._move(0, self.knockback_y, obstacles)
            self.knockback_x *= 0.67; self.knockback_y *= 0.67
            self.knockback_frames -= 1
        if self.dash_timer > 0:
            self.dash_timer -= 1
            old_position = (self.x, self.y)
            horizontal_ok = self._move(self.dash_dx * DASH_SPEED, 0, obstacles)
            vertical_ok = self._move(0, self.dash_dy * DASH_SPEED, obstacles)
            self._clamp_world()
            if not horizontal_ok or not vertical_ok or (self.x, self.y) == old_position:
                self.dash_timer = 0
                self.dash_iframes = 0
            else: self.dash_trail.append((*old_position, 7))
            return
        if self.attack_timer > 0:
            self.attack_timer -= 1
            return
        mx = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])
        my = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP])
        if not (mx or my):
            self.walk_frame = 0
            return
        length = math.hypot(mx, my)
        dx, dy = mx / length * self.speed, my / length * self.speed
        self._move(dx, 0, obstacles); self._move(0, dy, obstacles)
        self._clamp_world()
        self.facing = 2 if abs(mx) > abs(my) and mx > 0 else 1 if abs(mx) > abs(my) else 0 if my > 0 else 3
        self.walk_timer += 1
        if self.walk_timer >= 8:
            self.walk_timer = 0; self.walk_frame = (self.walk_frame + 1) % 6

    def _move(self, dx, dy, obstacles):
        self.x += dx; self.y += dy
        if any(self.hitbox.colliderect(rect) for rect in obstacles):
            self.x -= dx; self.y -= dy
            return False
        return True

    def _clamp_world(self):
        self.x = max(18, min(WORLD[0] - 18, self.x))
        self.y = max(38, min(WORLD[1] - 12, self.y))

    def start_dash(self, keys):
        if self.hp <= 0:
            return False
        if self.dash_timer or self.dash_cooldown:
            self.dash_feedback_timer = 18
            self.dash_feedback_kind = "cooldown"
            return False
        if self.sp < DASH_SP_COST:
            self.dash_feedback_timer = 18
            self.dash_feedback_kind = "sp"
            return False
        self.dash_feedback_timer = 0
        self.dash_feedback_kind = ""
        mx = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])
        my = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP])
        if not (mx or my):
            mx, my = {0: (0, 1), 1: (-1, 0), 2: (1, 0), 3: (0, -1)}[self.facing]
        length = math.hypot(mx, my)
        self.dash_dx, self.dash_dy = mx / length, my / length
        self.facing = 2 if abs(mx) > abs(my) and mx > 0 else 1 if abs(mx) > abs(my) else 0 if my > 0 else 3
        self.sp -= DASH_SP_COST
        self.sp_idle_frames = 0
        self.dash_timer = DASH_FRAMES
        # update() roda no mesmo frame do KEYDOWN; +1 preserva seis frames úteis.
        self.dash_iframes = DASH_IFRAMES + 1
        self.dash_cooldown = DASH_COOLDOWN_FRAMES
        self.attack_timer = 0
        return True

    def attack(self):
        if self.hp > 0 and self.dash_timer <= 0 and self.attack_timer <= 0 and self.attack_cooldown_timer <= 0:
            self.attack_timer = attributes.ATTACK_ANIMATION_FRAMES
            self.attack_cooldown_timer = self.attack_cooldown_frames
            self.attack_serial += 1
            self.attack_is_critical = random.random() < self.crit_chance
            return True
        return False

    @property
    def attack_damage(self):
        return self.physical_attack

    @property
    def current_attack_damage(self):
        return round(self.attack_damage * self.crit_multiplier) if self.attack_is_critical else self.attack_damage

    @property
    def attack_box(self):
        if not 3 <= self.attack_timer <= 12:
            return pygame.Rect(0, 0, 0, 0)
        reach = 52
        if self.facing == 1: return pygame.Rect(round(self.x - reach - 18), round(self.y - 35), reach, 52)
        if self.facing == 2: return pygame.Rect(round(self.x + 18), round(self.y - 35), reach, 52)
        if self.facing == 3: return pygame.Rect(round(self.x - 25), round(self.y - reach - 18), 50, reach)
        return pygame.Rect(round(self.x - 25), round(self.y + 17), 50, reach)

    def take_damage(self, amount, from_x=None, from_y=None, knockback=1.0):
        if self.invulnerability_timer > 0 or self.dash_iframes > 0 or self.hp <= 0:
            return False
        reduced = attributes.physical_damage_after_defense(amount, self.defense)
        self.hp = max(0, self.hp - reduced)
        self.invulnerability_timer = PLAYER_HIT_IFRAMES
        if from_x is not None and from_y is not None:
            length = max(1.0, math.hypot(self.x - from_x, self.y - from_y))
            self.knockback_x = (self.x - from_x) / length * 3.8 * knockback
            self.knockback_y = (self.y - from_y) / length * 3.8 * knockback
            self.knockback_frames = 7
        return True

    def draw(self, canvas, camera):
        index = max(0, min(7, (16 - self.attack_timer) // 2)) if self.attack_timer else self.walk_frame
        sprite = pygame.transform.scale(frame(self.attack_sheet if self.attack_timer else self.idle, index, self.facing), (96, 96))
        for trail_x, trail_y, age in self.dash_trail[-4:]:
            ghost = sprite.copy(); ghost.set_alpha(age * 20)
            canvas.blit(ghost, (round(trail_x - 48 - camera[0]), round(trail_y - 72 - camera[1])))
        if self.invulnerability_timer == 0 or (self.invulnerability_timer // 4) % 2 == 0:
            if self.dash_timer > 0: sprite.set_alpha(195)
            canvas.blit(sprite, (round(self.x - 48 - camera[0]), round(self.y - 72 - camera[1])))
