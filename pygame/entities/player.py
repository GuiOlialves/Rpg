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
from core.assets import load
from core.animation import (ATTACK_DURATIONS, ATTACK_ACTIVE_ELAPSED, IDLE_DURATIONS,
                            HERO_WALK_STRIDE_PIXELS, HURT_FRAMES, DEATH_DURATIONS, timed_frame,
                            DASH_POSE_DURATIONS, DASH_RECOVERY_DURATIONS,
                            DASH_TRAIL_FRAMES, DASH_TRAIL_SPACING)
from ui.character_art import character_visual, effect_frames, draw_effect, alpha_image


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
        self.dash_recovery_timer = 0
        self.dash_dx = self.dash_dy = 0.0
        self.dash_trail = []
        self.dash_feedback_timer = 0
        self.dash_feedback_kind = ""
        self.sp_idle_frames = 0
        self.knockback_x = self.knockback_y = 0.0
        self.knockback_frames = 0
        self.attack_serial = 0
        self.visual = character_visual(load, 'protagonist',
            ('idle','walk','attack','dash','hurt','death'), weapon=True)
        self.moving = False
        self.walk_distance = 0.0
        self.hurt_visual_timer = self.impact_timer = self.dust_timer = 0
        self.impact_position = self.dust_position = (self.x, self.y)
        self.impact_critical = False
        self.impact_serial = self.impact_strength = 0
        self.death_started = None
        self.impact_fx = effect_frames(load, 'impact')
        self.critical_fx = effect_frames(load, 'critical')
        self.dust_fx = effect_frames(load, 'dust')
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
        self.moving = False
        self.hurt_visual_timer = max(0, self.hurt_visual_timer - 1)
        self.impact_timer = max(0, self.impact_timer - 1)
        self.dust_timer = max(0, self.dust_timer - 1)
        self.dash_recovery_timer = max(0,self.dash_recovery_timer-1)
        if self.invulnerability_timer > 0:
            self.invulnerability_timer -= 1
        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= 1
        if self.dash_cooldown > 0: self.dash_cooldown -= 1
        if self.dash_iframes > 0: self.dash_iframes -= 1
        if self.dash_feedback_timer > 0: self.dash_feedback_timer -= 1
        self.dash_trail = [(x,y,age-1,direction,index) for x,y,age,direction,index in self.dash_trail if age>1]
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
            else:
                if (DASH_FRAMES-self.dash_timer)%DASH_TRAIL_SPACING==0:
                    index=timed_frame(max(0,DASH_FRAMES-self.dash_timer-1),DASH_POSE_DURATIONS,False)
                    self.dash_trail.append((*old_position,DASH_TRAIL_FRAMES,self.facing,index))
            if self.dash_timer==0:
                self.dash_recovery_timer=sum(DASH_RECOVERY_DURATIONS)
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
        old_x, old_y = self.x, self.y
        self._move(dx, 0, obstacles); self._move(0, dy, obstacles)
        self._clamp_world()
        self.facing = 2 if abs(mx) > abs(my) and mx > 0 else 1 if abs(mx) > abs(my) else 0 if my > 0 else 3
        distance = math.hypot(self.x-old_x, self.y-old_y)
        self.moving = distance > .01
        if self.moving:
            self.walk_distance = (self.walk_distance + distance) % HERO_WALK_STRIDE_PIXELS
            self.walk_frame = int(self.walk_distance / HERO_WALK_STRIDE_PIXELS * 8) % 8
        else:
            self.walk_frame = 0

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
        self.dash_recovery_timer = 0
        self.dust_position,self.dust_timer=(self.x,self.y),12
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
            self.dash_recovery_timer = 0
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
        if not self.attack_active:
            return pygame.Rect(0, 0, 0, 0)
        return self.visual.hit_bounds[self.facing][self.attack_frame].move(
            self.visual.weapon_origin(self.x,self.y))

    @property
    def attack_frame(self):
        return timed_frame(attributes.ATTACK_ANIMATION_FRAMES-self.attack_timer,
                           ATTACK_DURATIONS, loop=False)

    @property
    def attack_active(self):
        elapsed = attributes.ATTACK_ANIMATION_FRAMES-self.attack_timer
        return self.attack_timer > 0 and ATTACK_ACTIVE_ELAPSED[0] <= elapsed <= ATTACK_ACTIVE_ELAPSED[1]

    def attack_hits(self, hurtbox):
        """Test the authored sword sweep, excluding empty corners of its bounds."""
        if not self.attack_box.colliderect(hurtbox):
            return False
        origin = self.visual.weapon_origin(self.x,self.y)
        local = hurtbox.move(-origin[0], -origin[1])
        mask = self.visual.hit_masks[self.facing][self.attack_frame]
        return mask.overlap(pygame.mask.Mask(local.size, fill=True), local.topleft) is not None

    def confirm_impact(self, x, y, critical=False, strong=False):
        self.impact_position = (x, y-12)
        self.impact_timer = 12
        self.impact_critical = critical
        if critical or strong:
            self.impact_serial += 1
            self.impact_strength = 2 if strong else 1

    def take_damage(self, amount, from_x=None, from_y=None, knockback=1.0):
        if self.invulnerability_timer > 0 or self.dash_iframes > 0 or self.hp <= 0:
            return False
        reduced = attributes.physical_damage_after_defense(amount, self.defense)
        self.hp = max(0, self.hp - reduced)
        self.invulnerability_timer = PLAYER_HIT_IFRAMES
        self.hurt_visual_timer = HURT_FRAMES
        if self.hp <= 0:
            self.death_started = pygame.time.get_ticks()
        if from_x is not None and from_y is not None:
            length = max(1.0, math.hypot(self.x - from_x, self.y - from_y))
            self.knockback_x = (self.x - from_x) / length * 3.8 * knockback
            self.knockback_y = (self.y - from_y) / length * 3.8 * knockback
            self.knockback_frames = 7
        return True

    def draw(self, canvas, camera):
        state, index = 'idle', timed_frame(pygame.time.get_ticks()*60//1000, IDLE_DURATIONS)
        weapon_index = None
        if self.hp <= 0:
            # Combat pauses on defeat; finish transient visuals while the fall plays.
            self.dash_trail.clear()
            self.impact_timer = max(0,self.impact_timer-1)
            self.dust_timer = max(0,self.dust_timer-1)
            if self.death_started is None: self.death_started = pygame.time.get_ticks()
            state, index = 'death', timed_frame((pygame.time.get_ticks()-self.death_started)*60//1000,
                                                DEATH_DURATIONS, loop=False)
        elif self.dash_timer:
            state, index = 'dash', timed_frame(max(0,DASH_FRAMES-self.dash_timer-1),DASH_POSE_DURATIONS,False)
        elif self.attack_timer:
            state, index = 'attack', self.attack_frame
            weapon_index = index
        elif self.hurt_visual_timer:
            state, index = 'hurt', min(2,(HURT_FRAMES-self.hurt_visual_timer)//3)
        elif self.dash_recovery_timer:
            state, index = 'dash', 3+timed_frame(sum(DASH_RECOVERY_DURATIONS)-self.dash_recovery_timer,
                                               DASH_RECOVERY_DURATIONS,False)
        elif self.moving or self.walk_frame:
            state, index = 'walk', self.walk_frame
        sprite = self.visual.image(state,self.facing,index,flash=self.hurt_visual_timer > 5)
        for trail_x,trail_y,age,trail_facing,trail_index in self.dash_trail[-2:]:
            dash_image = self.visual.image('dash',trail_facing,trail_index)
            canvas.blit(self.visual.ghosts[dash_image,age],
                        self.visual.body_origin(trail_x,trail_y,camera))
        # Damage remains readable: bright reaction, then a subtle blink, never invisible.
        if self.invulnerability_timer and not self.hurt_visual_timer and self.hp > 0:
            sprite = alpha_image(sprite,145 if (self.invulnerability_timer//4)%2 else 255)
        canvas.blit(sprite,self.visual.body_origin(self.x,self.y,camera))
        if weapon_index is not None:
            canvas.blit(self.visual.weapons[self.facing][weapon_index],
                        self.visual.weapon_origin(self.x,self.y,camera))
        draw_effect(canvas,camera,self.dust_fx,*self.dust_position,self.dust_timer)

    def draw_impact(self,canvas,camera):
        draw_effect(canvas,camera,self.critical_fx if self.impact_critical else self.impact_fx,
                    *self.impact_position,self.impact_timer)
