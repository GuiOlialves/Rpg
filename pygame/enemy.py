"""Inimigos reutilizáveis: IA simples, combate, estados e drops físicos."""
from dataclasses import dataclass
import math
import random
import pygame

ENEMY_CONFIGS = {
    "slime": {
        "name": "Slime", "max_hp": 28, "damage": 5, "speed": 1.15,
        "perception": 220, "attack_range": 34, "cooldown": 70,
        # O spritesheet possui quantidades diferentes por animação:
        # idle = 4, movimento = 6, ataque = 7, dano = 3, morte = 5.
        # Ler colunas além desses limites captura frames vazios.
        "frame_size": 32, "scale": 3, "hitbox_radius": 18, "idle_frames": 4, "move_frames": 6,
        "attack_frames": 7, "hurt_frames": 3, "death_frames": 5,
        "drop": {"name": "Erva", "color": (84, 177, 113), "chance": 0.55, "min": 1, "max": 2}, "xp_reward": 18,
    },
    "warrior": {
        "name": "Guardião Errante", "max_hp": 64, "damage": 9, "speed": 0.78,
        "perception": 260, "attack_range": 52, "cooldown": 92,
        "frame_size": 192, "scale": 0.65, "hitbox_radius": 23, "idle_frames": 8, "move_frames": 6,
        "attack_frames": 4, "hurt_frames": 1, "death_frames": 1,
        "drop": {"name": "Éter", "color": (62, 128, 207), "chance": 0.45, "min": 1, "max": 1}, "xp_reward": 42,
    },
    "forest_guardian": {
        "name": "Guardião da Clareira", "max_hp": 180, "damage": 18, "speed": 0.9,
        "perception": 420, "attack_range": 58, "cooldown": 70,
        "frame_size": 192, "scale": 1.0, "hitbox_radius": 30, "idle_frames": 8, "move_frames": 6,
        "attack_frames": 4, "hurt_frames": 1, "death_frames": 1,
        "drop": {"name": "Éter", "color": (62, 128, 207), "chance": 1.0, "min": 2, "max": 2}, "xp_reward": 180,
    },
    "desert_scout": {
        "name": "Batedor das Dunas", "max_hp": 82, "damage": 13, "speed": 1.32,
        "perception": 330, "attack_range": 190, "cooldown": 105,
        "frame_size": 192, "scale": 0.58, "hitbox_radius": 21, "idle_frames": 6, "move_frames": 4,
        "attack_frames": 8, "hurt_frames": 1, "death_frames": 1,
        "sprite_team": "Yellow Units", "sprite_unit": "Archer",
        "animations": {"Idle": "Idle", "Run": "Run", "Attack": "Shoot"},
        "drop": {"name": "Erva", "color": (84, 177, 113), "chance": 0.50, "min": 1, "max": 2}, "xp_reward": 58,
    },
    "dune_lancer": {
        "name": "Lanceiro das Ruínas", "max_hp": 112, "damage": 16, "speed": 0.82,
        "perception": 300, "attack_range": 76, "cooldown": 92,
        "frame_size": 320, "scale": 0.42, "hitbox_radius": 25, "idle_frames": 12, "move_frames": 6,
        "attack_frames": 3, "hurt_frames": 1, "death_frames": 1,
        "sprite_team": "Black Units", "sprite_unit": "Lancer",
        "animations": {"Idle": "Idle", "Run": "Run", "Attack": "Right_Attack"},
        "drop": {"name": "Éter", "color": (62, 128, 207), "chance": 0.38, "min": 1, "max": 1}, "xp_reward": 78,
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
        self.charge_timer = 0
        self.charge_hit = False
        self.charge_dx = self.charge_dy = 0.0
        self.telegraph_target = None
        self.rng = random.Random(seed + 300)
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
        if any(self.hitbox.colliderect(rect) for rect in obstacles):
            self.x -= dx; self.y -= dy
            return False
        return True

    def _choose_wander(self):
        angle = self.rng.random() * math.tau
        self.wander_dx, self.wander_dy = math.cos(angle), math.sin(angle)
        self.state = "WANDER"
        self.state_timer = self.rng.randrange(35, 100)

    def update(self, player, obstacles):
        self.anim_tick += 1
        if self.state == "DEAD":
            self.dead_timer -= 1
            return self.dead_timer > 0
        if self.kind in {"forest_guardian", "dune_lancer"} and self.charge_timer > 0:
            self.charge_timer -= 1
            self.state = "ATTACK"
            if self.kind == "dune_lancer" and 20 >= self.charge_timer > 8:
                self._move(self.charge_dx * 5.5, self.charge_dy * 5.5, obstacles)
            if self.charge_timer == 8 and not self.charge_hit:
                self.charge_hit = True
                reach = 44 if self.kind == "dune_lancer" else 34
                if self.hitbox.inflate(reach, reach).colliderect(player.hitbox): player.take_damage(self.damage)
            if self.charge_timer == 0:
                self.state = "IDLE"; self.attack_cooldown = 80; self.state_timer = 30
            return True
        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
            self._move(self.knockback_x, self.knockback_y, obstacles)
            self.knockback_x *= 0.75; self.knockback_y *= 0.75
            if self.hurt_timer == 0: self.state = "IDLE"; self.state_timer = 20
            return True
        distance_player = math.hypot(player.x - self.x, player.y - self.y)
        distance_home = math.hypot(self.spawn_x - self.x, self.spawn_y - self.y)
        if self.state == "ATTACK":
            self.state_timer -= 1
            if self.state_timer == 10 and not self.attack_hit:
                self.attack_hit = True
                if distance_player <= self.config["attack_range"] + 10:
                    player.take_damage(self.damage)
            if self.state_timer <= 0:
                self.state = "IDLE"; self.state_timer = 30; self.attack_cooldown = self.config["cooldown"]
            return True
        if distance_player <= self.config["perception"] and distance_home <= 360:
            if self.kind == "desert_scout" and distance_player < 105 and self.attack_cooldown > 0:
                angle = math.atan2(self.y - player.y, self.x - player.x)
                self._move(math.cos(angle) * self.speed, math.sin(angle) * self.speed, obstacles)
                self.facing = -1 if player.x < self.x else 1
                return True
            if distance_player <= self.config["attack_range"] and self.attack_cooldown <= 0:
                if self.kind == "forest_guardian":
                    self.charge_timer = 42; self.charge_hit = False
                elif self.kind == "dune_lancer":
                    self.charge_timer = 40; self.charge_hit = False
                    length = max(1, distance_player)
                    self.charge_dx = (player.x - self.x) / length
                    self.charge_dy = (player.y - self.y) / length
                elif self.kind == "desert_scout":
                    self.telegraph_target = (player.x, player.y)
                self.state = "ATTACK"; self.state_timer = 28; self.attack_hit = False
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

    def receive_hit(self, damage, from_x, from_y):
        if self.state == "DEAD" or self.hurt_timer > 0: return False
        self.hp = max(0, self.hp - damage)
        angle = math.atan2(self.y - from_y, self.x - from_x)
        force = 1.5 if self.kind == "forest_guardian" else 5
        self.knockback_x, self.knockback_y = math.cos(angle) * force, math.sin(angle) * force
        self.hurt_timer = 12
        self.state = "HURT"
        if self.hp <= 0:
            self.state = "DEAD"; self.dead_timer = 36; self.hurt_timer = 0
        return True

    def attack_box(self):
        r = self.config["attack_range"]
        return pygame.Rect(round(self.x + (r if self.facing > 0 else -r - 28)), round(self.y - 18), 42, 36)

    def drop(self):
        if self.state != "DEAD" or self.dead_timer != 35: return None
        data = self.config["drop"]
        if random.random() > data["chance"]: return None
        item = {"name": data["name"], "amount": random.randint(data["min"], data["max"]), "color": data["color"]}
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
        if self.kind == "dune_lancer" and self.charge_timer > 20:
            center = (round(self.x - camera[0]), round(self.y - camera[1]))
            pygame.draw.circle(canvas, (238, 161, 68), center, 62, 2)
            pygame.draw.circle(canvas, (248, 211, 130), center, 48, 1)
        elif self.kind == "desert_scout" and self.state == "ATTACK" and self.telegraph_target:
            tx, ty = self.telegraph_target[0] - camera[0], self.telegraph_target[1] - camera[1]
            origin = (round(self.x - camera[0]), round(self.y - camera[1] - 20))
            pygame.draw.line(canvas, (255, 209, 105), origin, (round(tx), round(ty)), 2)
            pygame.draw.circle(canvas, (255, 224, 143), (round(tx), round(ty)), 24, 2)
        if self.state == "HURT":
            flash=image.copy()
            flash.fill((90,25,12,0),special_flags=pygame.BLEND_RGBA_ADD)
            flash.set_alpha(90)
            canvas.blit(flash,(draw_x,draw_y))
