"""Inimigos reutilizáveis: IA simples, combate, estados e drops físicos."""
from dataclasses import dataclass
import math
import random
import pygame
from items import consumable

ENEMY_CONFIGS = {
    "slime": {
        "name": "Slime", "max_hp": 48, "damage": 4, "speed": 1.45,
        "perception": 245, "attack_range": 48, "cooldown": 62,
        # O spritesheet possui quantidades diferentes por animação:
        # idle = 4, movimento = 6, ataque = 7, dano = 3, morte = 5.
        # Ler colunas além desses limites captura frames vazios.
        "frame_size": 32, "scale": 3, "hitbox_radius": 18, "idle_frames": 4, "move_frames": 6,
        "attack_frames": 7, "hurt_frames": 3, "death_frames": 5,
        "drop": {"id": "herb", "chance": 0.55, "min": 1, "max": 2}, "xp_reward": 18,
    },
    "warrior": {
        "name": "Guardião Errante", "max_hp": 96, "damage": 7, "speed": 1.55,
        "perception": 290, "attack_range": 82, "cooldown": 72,
        "frame_size": 192, "scale": 0.65, "hitbox_radius": 23, "idle_frames": 8, "move_frames": 6,
        "attack_frames": 4, "hurt_frames": 1, "death_frames": 1,
        "drop": {"id": "ether", "chance": 0.45, "min": 1, "max": 1}, "xp_reward": 42,
    },
    "forest_guardian": {
        "name": "Guardião da Clareira", "max_hp": 180, "damage": 12, "speed": 0.9,
        "perception": 420, "attack_range": 92, "cooldown": 26,
        "frame_size": 192, "scale": 1.0, "hitbox_radius": 30, "idle_frames": 8, "move_frames": 6,
        "attack_frames": 4, "hurt_frames": 1, "death_frames": 1,
        "drop": {"id": "ether", "chance": 1.0, "min": 2, "max": 2}, "xp_reward": 180,
    },
    "desert_scout": {
        "name": "Batedor das Dunas", "max_hp": 82, "damage": 9, "speed": 1.32,
        "perception": 330, "attack_range": 190, "cooldown": 105,
        "frame_size": 192, "scale": 0.58, "hitbox_radius": 21, "idle_frames": 6, "move_frames": 4,
        "attack_frames": 8, "hurt_frames": 1, "death_frames": 1,
        "sprite_team": "Yellow Units", "sprite_unit": "Archer",
        "animations": {"Idle": "Idle", "Run": "Run", "Attack": "Shoot"},
        "drop": {"id": "herb", "chance": 0.50, "min": 1, "max": 2}, "xp_reward": 58,
    },
    "dune_lancer": {
        "name": "Lanceiro das Ruínas", "max_hp": 112, "damage": 12, "speed": 1.3,
        "perception": 300, "attack_range": 76, "cooldown": 92,
        "frame_size": 320, "scale": 0.42, "hitbox_radius": 25, "idle_frames": 12, "move_frames": 6,
        "attack_frames": 3, "hurt_frames": 1, "death_frames": 1,
        "sprite_team": "Black Units", "sprite_unit": "Lancer",
        "animations": {"Idle": "Idle", "Run": "Run", "Attack": "Right_Attack"},
        "drop": {"id": "ether", "chance": 0.38, "min": 1, "max": 1}, "xp_reward": 78,
    },
}


@dataclass
class Drop:
    item: dict
    x: float
    y: float
    lifetime: int = 60 * 90

    @property
    def hitbox(self):
        return pygame.Rect(round(self.x - 12), round(self.y - 12), 24, 24)

    def update(self):
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, canvas, camera):
        x, y = round(self.x - camera[0]), round(self.y - camera[1])
        pygame.draw.ellipse(canvas, (27, 47, 31, 100), (x - 15, y + 7, 30, 8))
        pygame.draw.circle(canvas, self.item["color"], (x, y), 9)
        pygame.draw.circle(canvas, (252, 229, 157), (x - 3, y - 3), 3)
        pygame.draw.circle(canvas, (230, 215, 129), (x, y), 11, 1)


class Enemy:
    STATES = {"IDLE", "WANDER", "CHASE", "ATTACK", "HURT", "DEAD"}

    def __init__(self, kind, position, load, seed=0):
        self.kind = kind
        self.config = ENEMY_CONFIGS[kind]
        self.name = self.config["name"]
        self.x, self.y = map(float, position)
        self.spawn_x, self.spawn_y = self.x, self.y
        self.max_hp = self.hp = self.config["max_hp"]
        self.damage = self.config["damage"]
        self.speed = self.config["speed"]
        self.state = "IDLE"
        self.facing = 1
        self.state_timer = random.Random(seed).randrange(25, 80)
        self.attack_cooldown = 0
        self.attack_hit = False
        self.hurt_timer = 0
        self.dead_timer = 0
        self.knockback_x = self.knockback_y = 0.0
        self.anim_tick = 0
        self.telegraph_target = None
        self.attack_action = None
        self.attack_phase = None
        self.phase_timer = 0
        self.attack_direction = (0.0, 1.0)
        self.last_action = None
        self.attack_zone = None
        self.hit_confirmed = False
        self.retreat_timer = 0
        self.hit_resistance_timer = 0
        self.rng = random.Random(seed + 300)
        # Leve defasagem inicial evita que grupos comecem o primeiro golpe juntos.
        self.attack_cooldown = self.rng.randrange(0, 24)
        self.idle_sheet = load(self._path("Idle"))
        self.move_sheet = load(self._path("Run"))
        self.attack_sheet = load(self._path("Attack"))
        self.hurt_sheet = self.idle_sheet
        self.death_sheet = self.idle_sheet
        size=self.config['frame_size']
        # Pivô constante: não reposicionar cada frame pelo bounding box variável.
        self.visual_foot=self.idle_sheet.subsurface((0,0,size,size)).get_bounding_rect().bottom

    def _path(self, animation):
        if self.kind == "slime":
            return "sprites_meu/mystic_woods_free_2.2/sprites/characters/slime.png"
        if "sprite_unit" in self.config:
            unit = self.config["sprite_unit"]
            action = self.config.get("animations", {}).get(animation, animation)
            base = f"sprites_meu/Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/Units/{self.config['sprite_team']}/{unit}/{unit}_"
            return base + action + ".png"
        color = "Blue Units" if self.kind == "forest_guardian" else "Red Units"
        base = f"sprites_meu/Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/Units/{color}/Warrior/Warrior_"
        return base + ("Attack1.png" if animation == "Attack" else "Run.png" if animation == "Run" else "Idle.png")

    @property
    def hitbox(self):
        radius = self.config.get("hitbox_radius", 23)
        return pygame.Rect(round(self.x - radius), round(self.y - radius), radius * 2, radius * 2)

    @property
    def hurtbox(self):
        return self.hitbox.inflate(8, 8)

    @property
    def alive(self):
        return self.state != "DEAD" or self.dead_timer > 0

    def _move(self, dx, dy, obstacles):
        self.x += dx; self.y += dy
        box = self.hitbox
        outside = box.left < 0 or box.top < 0 or box.right > 2048 or box.bottom > 1152
        if outside or any(box.colliderect(rect) for rect in obstacles):
            self.x -= dx; self.y -= dy
            return False
        return True

    def _choose_wander(self):
        angle = self.rng.random() * math.tau
        self.wander_dx, self.wander_dy = math.cos(angle), math.sin(angle)
        self.state = "WANDER"
        self.state_timer = self.rng.randrange(35, 100)

    def _direction_to(self, player):
        dx, dy = player.x - self.x, player.y - self.y
        length = max(1.0, math.hypot(dx, dy))
        return dx / length, dy / length

    def _strike_box(self, action=None):
        action = action or self.attack_action or "normal"
        reach = {"slime": 46, "warrior": 80, "forest_guardian": 88,
                 "dune_lancer": 83, "desert_scout": 190}.get(self.kind, 70)
        if action == "charged": reach = 115
        dx, dy = self.attack_direction
        width = 56 if self.kind == "forest_guardian" else 40 if self.kind == "slime" else 48
        if abs(dx) >= abs(dy):
            left = self.x + (17 if dx >= 0 else -reach - 17)
            return pygame.Rect(round(left), round(self.y - width / 2), reach, width)
        top = self.y + (12 if dy >= 0 else -reach - 12)
        return pygame.Rect(round(self.x - width / 2), round(top), width, reach)

    def _begin_attack(self, action, player):
        self.attack_action = action
        self.last_action = action
        self.attack_phase = "windup"
        self.attack_direction = self._direction_to(player)
        self.facing = -1 if self.attack_direction[0] < 0 else 1
        self.attack_hit = False
        self.hit_confirmed = False
        self.attack_zone = None
        self.state = "ATTACK"
        self.anim_tick = 0
        low_hp = self.kind == "forest_guardian" and self.hp <= self.max_hp * 0.4
        windups = {"normal": 13 if self.kind == "slime" else 12,
                   "charged": 30, "charge": 24, "aoe": 29, "ranged": 25}
        self.phase_timer = windups[action] - (3 if low_hp else 0)
        if action == "ranged": self.telegraph_target = (player.x, player.y)

    def _choose_guardian_action(self, distance):
        if distance > 145:
            # Depois da investida, aproxima-se antes de repetir o mesmo aviso.
            return None if self.last_action == "charge" else "charge"
        if distance > 115:
            return "charge" if self.last_action == "charged" else "charged"
        elif distance < 62:
            candidates = ("aoe", "normal", "charged")
        else:
            candidates = ("normal", "charged", "charge")
        if self.last_action == candidates[0] and len(candidates) > 1:
            return candidates[1]
        if distance < 62 and self.last_action == "aoe": return "normal"
        return candidates[0]

    def _attack_update(self, player, obstacles):
        action = self.attack_action
        self.phase_timer -= 1
        if self.attack_phase == "windup":
            if action == "normal":
                dx, dy = self.attack_direction
                windup_step = 1.4 if self.kind == "slime" else 1.6 if self.kind == "warrior" else 1.0
                self._move(dx * windup_step, dy * windup_step, obstacles)
            if self.phase_timer <= 0:
                self.attack_phase = "active"
                self.phase_timer = 12 if action == "charge" else 5 if action == "aoe" else 4
                self.attack_zone = None
            return
        if self.attack_phase == "active":
            dx, dy = self.attack_direction
            if action == "charge":
                # Rota travada no início; pequenos passos impedem atravessar sólidos.
                if not self._move(dx * 7, dy * 7, obstacles) or not self._move(dx * 7, dy * 7, obstacles):
                    self.phase_timer = 0
                zone = self.hitbox.inflate(20, 20)
            elif action in {"normal", "charged"}:
                step = 5 if self.kind == "slime" else 4 if action == "normal" else 3
                self._move(dx * step, dy * step, obstacles)
                zone = self._strike_box(action)
            elif action == "aoe":
                zone = pygame.Rect(round(self.x - 65), round(self.y - 65), 130, 130)
            else:
                zone = pygame.Rect(round(self.telegraph_target[0] - 25),
                                   round(self.telegraph_target[1] - 25), 50, 50)
            self.attack_zone = zone
            in_zone = zone.colliderect(player.hitbox)
            if action == "aoe":
                in_zone = math.hypot(player.x - self.x, player.y - self.y) <= 65 + 10
            if not self.attack_hit and in_zone:
                power = 1.6 if action == "charged" else 1.25 if action in {"charge", "aoe"} else 1.0
                if player.take_damage(round(self.damage * power), self.x, self.y, power):
                    self.attack_hit = self.hit_confirmed = True
            if self.phase_timer <= 0:
                self.attack_phase = "recovery"
                self.phase_timer = {"normal": 22 if self.kind == "forest_guardian" else 15, "charged": 30, "charge": 28,
                                    "aoe": 25, "ranged": 20}[action]
                self.retreat_timer = 18 if self.kind == "forest_guardian" and self.hit_confirmed else 0
                self.attack_zone = None
            return
        if self.retreat_timer > 0:
            dx, dy = self._direction_to(player)
            self._move(-dx * 3.4, -dy * 3.4, obstacles)
            self.retreat_timer -= 1
        if self.phase_timer <= 0:
            self.state = "IDLE"; self.state_timer = 8
            self.attack_phase = None; self.attack_action = None
            cooldown = self.config["cooldown"]
            if self.kind == "forest_guardian" and self.hp <= self.max_hp * 0.4:
                cooldown = round(cooldown * 0.75)
            self.attack_cooldown = cooldown

    def update(self, player, obstacles):
        self.anim_tick += 1
        if self.hit_resistance_timer > 0:
            self.hit_resistance_timer -= 1
        if self.state == "DEAD":
            self.dead_timer -= 1
            return self.dead_timer > 0
        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
            self._move(self.knockback_x, self.knockback_y, obstacles)
            self.knockback_x *= 0.75; self.knockback_y *= 0.75
            if self.hurt_timer == 0: self.state = "IDLE"; self.state_timer = 20
            return True
        if self.kind == "forest_guardian" and self.state == "ATTACK" and abs(self.knockback_x) + abs(self.knockback_y) > 0.1:
            self._move(self.knockback_x, self.knockback_y, obstacles)
            self.knockback_x *= 0.5; self.knockback_y *= 0.5
        distance_player = math.hypot(player.x - self.x, player.y - self.y)
        distance_home = math.hypot(self.spawn_x - self.x, self.spawn_y - self.y)
        if self.state == "ATTACK":
            self._attack_update(player, obstacles)
            return True
        if distance_player <= self.config["perception"] and distance_home <= 360:
            if self.kind == "desert_scout" and distance_player < 105 and self.attack_cooldown > 0:
                angle = math.atan2(self.y - player.y, self.x - player.x)
                self._move(math.cos(angle) * self.speed, math.sin(angle) * self.speed, obstacles)
                self.facing = -1 if player.x < self.x else 1
                return True
            trigger_range = 195 if self.kind == "forest_guardian" else 160 if self.kind == "dune_lancer" else self.config["attack_range"]
            if distance_player <= trigger_range and self.attack_cooldown <= 0:
                action = (self._choose_guardian_action(distance_player) if self.kind == "forest_guardian"
                          else "charge" if self.kind == "dune_lancer" and distance_player > 85
                          else "ranged" if self.kind == "desert_scout" else "normal")
                if action:
                    self._begin_attack(action, player)
                    return True
            self.state = "CHASE"
            angle = math.atan2(player.y - self.y, player.x - self.x)
            moved = self._move(math.cos(angle) * self.speed, math.sin(angle) * self.speed, obstacles)
            self.facing = -1 if player.x < self.x else 1
            if not moved:
                self._choose_wander()
            return True
        if distance_home > 300:
            self.state = "CHASE"
            angle = math.atan2(self.spawn_y - self.y, self.spawn_x - self.x)
            self._move(math.cos(angle) * self.speed, math.sin(angle) * self.speed, obstacles)
            return True
        self.state_timer -= 1
        if self.state_timer <= 0:
            if self.state == "IDLE": self._choose_wander()
            else: self.state = "IDLE"; self.state_timer = self.rng.randrange(30, 85)
        if self.state == "WANDER":
            if not self._move(self.wander_dx * self.speed * 0.55, self.wander_dy * self.speed * 0.55, obstacles): self._choose_wander()
        return True

    def receive_hit(self, damage, from_x, from_y, knockback=1.0):
        if self.state == "DEAD" or self.hurt_timer > 0 or self.hit_resistance_timer > 0: return False
        self.hp = max(0, self.hp - damage)
        angle = math.atan2(self.y - from_y, self.x - from_x)
        special = self.kind == "forest_guardian" and self.state == "ATTACK"
        force = (0.45 if special else 0.75 if self.kind == "forest_guardian"
                 else 2.6 if self.kind == "slime" else 1.7) * knockback
        self.knockback_x, self.knockback_y = math.cos(angle) * force, math.sin(angle) * force
        self.hit_resistance_timer = {"slime": 5, "warrior": 11, "forest_guardian": 13,
                                     "desert_scout": 8, "dune_lancer": 11}[self.kind]
        if not special:
            self.hurt_timer = {"slime": 9, "warrior": 8, "forest_guardian": 6,
                               "desert_scout": 7, "dune_lancer": 8}[self.kind]
            self.state = "HURT"
            self.attack_zone = None
            self.attack_phase = self.attack_action = None
            self.attack_cooldown = max(self.attack_cooldown, 12)
        if self.hp <= 0:
            self.state = "DEAD"; self.dead_timer = 36; self.hurt_timer = 0
            self.attack_zone = None
        return True

    def attack_box(self):
        return self.attack_zone if self.state == "ATTACK" and self.attack_zone else pygame.Rect(0, 0, 0, 0)

    def drop(self):
        if self.state != "DEAD" or self.dead_timer != 35: return None
        data = self.config["drop"]
        if random.random() > data["chance"]: return None
        item = consumable(data["id"], random.randint(data["min"], data["max"]))
        return Drop(item, self.x, self.y)

    def draw(self, canvas, camera):
        cfg = self.config
        if self.state == "DEAD":
            sheet, row, count = self.death_sheet, 12 if self.kind == "slime" else 0, cfg["death_frames"]
        elif self.state == "ATTACK": sheet, row, count = self.attack_sheet, 6 if self.kind == "slime" else 0, cfg["attack_frames"]
        elif self.state == "WANDER" or self.state == "CHASE": sheet, row, count = self.move_sheet, 3 if self.kind == "slime" else 0, cfg["move_frames"]
        elif self.state == "HURT": sheet, row, count = self.hurt_sheet, 9 if self.kind == "slime" else 0, cfg["hurt_frames"]
        else: sheet, row, count = self.idle_sheet, 0, cfg["idle_frames"]
        # Cada inimigo possui seu próprio relógio de animação. Usar o relógio
        # global fazia os frames reiniciarem de forma irregular durante HURT.
        index = (self.anim_tick // 8) % max(1, count)
        size = cfg["frame_size"]
        rect = pygame.Rect(index * size, row * size, size, size)
        if self.kind == "warrior": rect = pygame.Rect(index * size, 0, size, size)
        image = sheet.subsurface(rect).copy()
        if self.facing < 0: image = pygame.transform.flip(image, True, False)
        scale = cfg["scale"]
        image = pygame.transform.scale(image, (round(image.width * scale), round(image.height * scale)))
        draw_x = round(self.x - image.width / 2 - camera[0])
        draw_y = round(self.y - self.visual_foot * scale - camera[1])
        if self.state == "DEAD" and self.dead_timer < 8:
            image.set_alpha(max(0, self.dead_timer * 32))
        canvas.blit(image, (draw_x, draw_y))
        if self.state == "ATTACK" and self.attack_phase == "windup":
            center = (round(self.x - camera[0]), round(self.y - camera[1]))
            if self.attack_action == "aoe":
                pygame.draw.circle(canvas, (255, 167, 73), center, 65, 3)
                pygame.draw.circle(canvas, (255, 218, 133), center, 53, 1)
            elif self.attack_action == "charge":
                dx, dy = self.attack_direction
                target = (round(center[0] + dx * 168), round(center[1] + dy * 168))
                pygame.draw.line(canvas, (255, 169, 78), center, target, 4)
                pygame.draw.circle(canvas, (255, 218, 133), target, 8, 2)
            elif self.attack_action == "ranged" and self.telegraph_target:
                tx, ty = self.telegraph_target[0] - camera[0], self.telegraph_target[1] - camera[1]
                origin = (round(self.x - camera[0]), round(self.y - camera[1] - 20))
                pygame.draw.line(canvas, (255, 209, 105), origin, (round(tx), round(ty)), 2)
                pygame.draw.circle(canvas, (255, 224, 143), (round(tx), round(ty)), 25, 2)
            else:
                warning = self._strike_box(self.attack_action).move(-camera[0], -camera[1])
                pygame.draw.rect(canvas, (255, 112, 75) if self.attack_action == "charged" else (255, 174, 87),
                                 warning, 3 if self.attack_action == "charged" else 2)
                if self.attack_action == "charged":
                    pygame.draw.circle(canvas, (255, 212, 126), center, 38, 2)
        if self.state == "HURT":
            flash=image.copy()
            flash.fill((90,25,12,0),special_flags=pygame.BLEND_RGBA_ADD)
            flash.set_alpha(90)
            canvas.blit(flash,(draw_x,draw_y))
