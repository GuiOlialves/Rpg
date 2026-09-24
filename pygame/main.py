"""Vila de treino - Pygame com câmera, terreno próprio, decoração e colisões."""
from pathlib import Path
import math
import random
import sys
import pygame
import attributes
import village
import forest
import desert
import ambient
import environment
import game_over
from enemy import Enemy
from npc import NPC, nearest
from dialogue import DialogueBox
from quest import QuestManager
from equipment import item, SLOTS
from items import CONSUMABLES, consumable
import save_manager

ROOT = Path(__file__).parent
WINDOW = (1366, 768)
VIEW = (1024, 576)
WORLD = (2048, 1152)
TILE = 32
FPS = 60
STAT_POINTS_PER_LEVEL = 3
DASH_SP_COST = 10
DASH_FRAMES = 11
DASH_SPEED = 9.0
DASH_COOLDOWN_FRAMES = 39
DASH_IFRAMES = 6
PLAYER_HIT_IFRAMES = 36
RESPAWN_IFRAMES = 60
SP_REGEN_DELAY = 240
SP_REGEN_INTERVAL = 60
CONSUMABLE_COOLDOWN_FRAMES = 90
HITSTOP_NORMAL_FRAMES = 2
HITSTOP_STRONG_FRAMES = 3

def load(path: str) -> pygame.Surface:
    return pygame.image.load(ROOT / path).convert_alpha()

def asset(path):
    return load("sprites_meu/vila_tile-set/" + path)

def frame(sheet, index, direction):
    return sheet.subsurface((index * 64, direction * 64, 64, 64))

def make_tree(seed=0):
    return village.tree(seed)

def make_bush(seed=0):
    s = pygame.Surface((76, 44), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (36, 54, 36, 90), (3, 29, 70, 12))
    for i, (x, y, r) in enumerate([(16, 27, 15), (33, 20, 18), (52, 25, 17), (65, 30, 11)]):
        pygame.draw.circle(s, [(47, 116, 55), (61, 137, 62), (76, 151, 69)][(i + seed) % 3], (x, y), r)
    pygame.draw.circle(s, (135, 184, 78), (30, 15), 4)
    return s

def make_fountain():
    s = pygame.Surface((96, 88), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (48, 76, 54, 100), (5, 70, 86, 14))
    pygame.draw.ellipse(s, (93, 101, 107), (8, 48, 80, 30))
    pygame.draw.ellipse(s, (163, 177, 178), (12, 51, 72, 20))
    pygame.draw.ellipse(s, (56, 154, 190), (19, 54, 58, 13))
    pygame.draw.rect(s, (113, 125, 129), (38, 25, 20, 31), border_radius=4)
    pygame.draw.ellipse(s, (177, 190, 187), (31, 20, 34, 14))
    pygame.draw.arc(s, (169, 231, 241), (30, 4, 36, 44), 3.4, 6.0, 3)
    pygame.draw.arc(s, (169, 231, 241), (42, 7, 36, 42), 3.7, 5.9, 3)
    return s

def make_flowerbed(seed=0):
    s = pygame.Surface((112, 54), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (51, 100, 45, 120), (4, 33, 104, 15))
    pygame.draw.ellipse(s, (75, 126, 58), (7, 22, 98, 23))
    flowers = [(244, 97, 113), (253, 224, 89), (176, 116, 218), (244, 140, 71)]
    for i, x in enumerate(range(15, 101, 17)):
        pygame.draw.circle(s, flowers[(i + seed) % len(flowers)], (x, 25 + (i % 2) * 7), 5)
        pygame.draw.circle(s, (255, 245, 174), (x, 25 + (i % 2) * 7), 2)
    return s

def make_sign():
    return environment.resize(environment.free_woods(load)['sign'],3)

def make_terrain():
    return village.terrain(WORLD,asset)

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
        if self.hp <= 0 or self.dash_timer or self.dash_cooldown or self.sp < DASH_SP_COST:
            return False
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


class DamageNumber:
    def __init__(self, text, x, y, color, critical=False):
        self.text, self.x, self.y = text, x, y
        self.color, self.critical = color, critical
        self.ticks = 42

    def update(self):
        self.y -= 0.65
        self.ticks -= 1
        return self.ticks > 0

    def draw(self, canvas, camera, font, title_font):
        label = (title_font if self.critical else font).render(self.text, True, self.color)
        label.set_alpha(min(255, self.ticks * 12))
        canvas.blit(label, (round(self.x - camera[0] - label.get_width() / 2),
                            round(self.y - camera[1])))

def build_village():
    houses, objects, nature, obstacles = village.build(asset, make_flowerbed, make_fountain, make_sign, make_bush,load)
    objects.append((make_sign(), (1915, 535)))
    npc_sprite = load("sprites_meu/Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/Units/Blue Units/Warrior/Warrior_Idle.png")
    npcs = [
        NPC("alden", "Alden", (1780, 560), {"default": ["Algo estranho está acontecendo na floresta.", "Aceite a missão para investigar os slimes."], "AVAILABLE": ["As criaturas estão se aproximando da vila.", "Derrote 5 slimes na floresta. Pressione E para aceitar."], "ACTIVE": ["Tenha cuidado na floresta. Ainda faltam criaturas."], "COMPLETED": ["Você conseguiu! A vila está mais segura. Tome estas ervas."], "REWARDED": ["Obrigado novamente pela ajuda."], "BOSS_DONE": ["A floresta está mais segura, e o caminho ao norte voltou a ser acessível."]}, npc_sprite),
        NPC("mira", "Mira", (1030, 420), {"default": ["A praça é o coração da Vila do Vale.", "Siga pela estrada quando quiser explorar novas regiões."]}, npc_sprite),
        NPC("tomas", "Tomas", (1430, 540), {"default": ["Leve ervas e éter quando sair da vila.", "Nunca se sabe o que pode aparecer entre as árvores."]}, npc_sprite),
    ]
    for npc in npcs:
        obstacles.append(npc.hitbox)
    npcs[0].quest_id = "forest_trouble"
    return {"name": "Vila do Vale", "terrain": village.terrain(WORLD,asset), "houses": houses,
            "ambient_kind":"village",
            "objects": objects, "nature": nature, "obstacles": obstacles,
            "exits": {"forest": pygame.Rect(1960, 520, 88, 115)},
            "spawn": {"forest": (1850, 575)}, "enemy_spawns": [], "npcs": npcs}

def build_region(name, opened_chests=None):
    if name == "village": return build_village()
    if name == "forest": return forest.build(load)
    if name == "desert": return desert.build(load, opened_chests)
    raise ValueError(f"Região desconhecida: {name}")


def reset_forest_boss_encounter():
    region = build_region("forest")
    region["arena_locked"] = True
    region["north_locked"] = True
    region["obstacles"].append(region["exits"]["desert"].inflate(30, 20))
    boss = Enemy("forest_guardian", (1300, 430), load, seed=77)
    return region, [boss]

def spawn_enemies(region):
    return [Enemy(kind, position, load, seed=index) for index, (kind, position) in enumerate(region.get("enemy_spawns", []))]

def add_inventory_item(inventory, item_data):
    existing = next((entry for entry in inventory if entry.get("id") == item_data["id"] and entry.get("type") != "equipment"), None)
    if existing: existing["amount"] += item_data["amount"]
    else: inventory.append(item_data.copy())

def can_transition(source, destination, quest_manager):
    return not (source == "forest" and destination == "desert" and not quest_manager.forest_boss_defeated)

def draw_world(canvas, region, font, camera, player=None, enemies=None, drops=None, debug=False):
    canvas.blit(region["terrain"], (-camera[0], -camera[1]))
    ambient.draw_water(canvas,region,camera,pygame.time.get_ticks())
    houses, objects, nature = region["houses"], region["objects"], region["nature"]
    entities = [(y + im.get_height() - 10, im, (x, y)) for im, (x, y) in nature + objects + houses]
    for obj in region.get('scenery',[]):
        entities.append((obj.depth,'scenery',obj))
    # Sombras no chão, antes dos corpos e das copas; nunca sobre a interface.
    for actor in ([player] if player else []) + list(enemies or []) + region.get('npcs',[]):
        radius=getattr(actor,'config',{}).get('hitbox_radius',17)
        environment.shadow(canvas,(actor.x-camera[0],actor.y-camera[1]),round(radius*1.6),10,38)
    if player is not None:
        entities.append((player.y, "player", player))
    for enemy in enemies or []:
        entities.append((enemy.y, "enemy", enemy))
    for drop in drops or []:
        entities.append((drop.y, "drop", drop))
    for obj in region.get("interactables", []):
        entities.append((obj.y, "interactable", obj))
    for npc in region.get("npcs", []):
        entities.append((npc.y, "npc", npc))
    for _, image, pos in sorted(entities, key=lambda entry: entry[0]):
        if image == 'scenery':
            pos.draw(canvas,camera,player)
        elif image == "player" or image == "enemy" or image == "drop" or image == "npc" or image == "interactable":
            pos.draw(canvas, camera)
        else:
            canvas.blit(image, (pos[0] - camera[0], pos[1] - camera[1]))
    ambient.draw(canvas,region,camera,pygame.time.get_ticks())
    if debug:
        if player is not None:
            pygame.draw.rect(canvas, (75, 231, 247), player.hitbox.move(-camera[0], -camera[1]), 2)
            if player.attack_box.width:
                pygame.draw.rect(canvas, (255, 250, 112), player.attack_box.move(-camera[0], -camera[1]), 2)
        for enemy in enemies or []:
            pygame.draw.rect(canvas, (235, 75, 75), enemy.hitbox.move(-camera[0], -camera[1]), 1)
            pygame.draw.rect(canvas, (245, 220, 90), enemy.hurtbox.move(-camera[0], -camera[1]), 1)
            if enemy.attack_box().width:
                pygame.draw.rect(canvas, (255, 84, 83), enemy.attack_box().move(-camera[0], -camera[1]), 2)
            if enemy.attack_action == "aoe" and enemy.attack_phase == "windup":
                pygame.draw.circle(canvas, (255, 84, 83), (round(enemy.x - camera[0]), round(enemy.y - camera[1])), 65, 1)
            if enemy.attack_action == "charge" and enemy.attack_phase == "windup":
                dx, dy = enemy.attack_direction
                pygame.draw.line(canvas, (255, 84, 83), (round(enemy.x - camera[0]), round(enemy.y - camera[1])),
                                 (round(enemy.x + dx * 168 - camera[0]), round(enemy.y + dy * 168 - camera[1])), 2)
            pygame.draw.circle(canvas, (240, 145, 70), (round(enemy.spawn_x - camera[0]), round(enemy.spawn_y - camera[1])), 4, 1)
            debug_text = font.render(enemy.state, True, (255, 230, 120))
            canvas.blit(debug_text, (round(enemy.x - camera[0] - 25), round(enemy.y - camera[1] - 48)))
    for exit_name, exit_rect in region["exits"].items():
        viewport = pygame.Rect(camera[0], camera[1], VIEW[0], VIEW[1])
        if viewport.colliderect(exit_rect):
            label = "FLORESTA" if exit_name == "forest" else "VILA" if exit_name == "village" else "DESERTO" if exit_name == "desert" else "RUÍNAS"
            marker = pygame.Surface((150, 28), pygame.SRCALPHA)
            marker.fill((25, 31, 34, 190))
            marker.blit(font.render(f"Saída: {label}", True, (239, 222, 169)), (9, 6))
            canvas.blit(marker, (exit_rect.centerx - camera[0] - 75, exit_rect.top - camera[1] - 34))
    if region.get("arena_locked"):
        lock = region["exits"].get("desert")
        if lock:
            pygame.draw.rect(canvas, (105, 67, 40), lock.move(-camera[0], -camera[1]))
            canvas.blit(font.render("A passagem está bloqueada", True, (245, 212, 148)), (lock.left - camera[0] - 55, lock.bottom - camera[1] + 8))
    panel = pygame.Surface((820, 32), pygame.SRCALPHA)
    panel.fill((25, 31, 34, 210))
    panel.blit(font.render(f"{region['name']} | WASD mover | Espaço atacar | Q Dash | E interagir | V personagem | I inventário", True, (235, 222, 185)), (12, 8))
    canvas.blit(panel, (16, 14))
    targets = region.get("npcs", []) + [obj for obj in region.get("interactables", []) if not obj.opened]
    target = nearest(targets, player) if player is not None else None
    if target is not None:
        prompt = font.render(getattr(target, "prompt", "[E] Interagir"), True, (250, 235, 170))
        canvas.blit(prompt, (round(target.x - prompt.get_width()/2 - camera[0]), round(target.y - 94 - camera[1])))
    if region.get("north_locked") and not region.get("arena_locked") and "desert" in region["exits"]:
        lock = region["exits"]["desert"]
        pygame.draw.rect(canvas, (105, 67, 40), lock.move(-camera[0], -camera[1]))
        canvas.blit(font.render("A passagem está bloqueada", True, (245, 212, 148)), (lock.left - camera[0] - 55, lock.bottom - camera[1] + 8))

def camera_for(player):
    return (max(0, min(WORLD[0] - VIEW[0], round(player.x - VIEW[0] / 2))), max(0, min(WORLD[1] - VIEW[1], round(player.y - VIEW[1] / 2))))


def safe_respawn_position(region_id, region, enemies):
    source = {"forest": "village", "desert": "forest"}.get(region_id)
    preferred = region.get("spawn", {}).get(source, (1024, 576)) if source else (1024, 576)
    candidates = [preferred]
    for distance in (24, 48, 72, 96, 128):
        candidates.extend((preferred[0] + dx, preferred[1] + dy)
                          for dx, dy in ((distance, 0), (-distance, 0), (0, distance), (0, -distance)))
    width, height = region["terrain"].get_size()
    for x, y in candidates:
        box = pygame.Rect(round(x - 13), round(y - 9), 26, 18)
        if not (18 <= x <= width - 18 and 38 <= y <= height - 12):
            continue
        if any(box.colliderect(obstacle) for obstacle in region["obstacles"]):
            continue
        if any(box.colliderect(enemy.hitbox.inflate(18, 18)) for enemy in enemies if enemy.state != "DEAD"):
            continue
        return float(x), float(y)
    return float(preferred[0]), float(preferred[1])


def restore_player_after_death(player, region_id, region, enemies):
    player.x, player.y = safe_respawn_position(region_id, region, enemies)
    player.hp, player.sp = player.max_hp, player.max_sp
    player.attack_timer = player.attack_cooldown_timer = 0
    player.dash_timer = player.dash_cooldown = player.dash_iframes = 0
    player.invulnerability_timer = RESPAWN_IFRAMES
    player.knockback_x = player.knockback_y = 0.0
    player.knockback_frames = 0
    player.attack_serial += 1
    return player.x, player.y

def draw_panel(surface, rect, fill=(35, 43, 50), border=(187, 145, 75), radius=10):
    shadow = rect.move(5, 6)
    pygame.draw.rect(surface, (8, 12, 15, 150), shadow, border_radius=radius)
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, 3, border_radius=radius)
    pygame.draw.line(surface, (82, 92, 96), (rect.x + 12, rect.y + 7), (rect.right - 12, rect.y + 7), 1)

def draw_bar(surface, rect, value, maximum, fill, label, font, icon=None):
    pygame.draw.rect(surface, (17, 22, 27), rect, border_radius=6)
    pygame.draw.rect(surface, (92, 99, 101), rect, 2, border_radius=6)
    inner = rect.inflate(-6, -6)
    pygame.draw.rect(surface, (48, 55, 60), inner, border_radius=3)
    amount = max(0, min(1, value / maximum))
    width = round(inner.width * amount)
    if width:
        filled = pygame.Rect(inner.x, inner.y, width, inner.height)
        pygame.draw.rect(surface, fill, filled, border_radius=3)
        pygame.draw.line(surface, tuple(min(255, c + 45) for c in fill), (filled.x + 3, filled.y + 2), (filled.right - 3, filled.y + 2), 2)
    for marker in range(1, 5):
        x = inner.x + inner.width * marker // 5
        pygame.draw.line(surface, (30, 35, 39), (x, inner.y + 2), (x, inner.bottom - 2), 1)
    prefix = f"{icon}  " if icon else ""
    text = font.render(f"{prefix}{label}", True, (250, 244, 225))
    number = font.render(f"{value} / {maximum}", True, "white")
    surface.blit(text, (rect.x + 9, rect.y + 5))
    surface.blit(number, (rect.right - number.get_width() - 9, rect.y + 5))

def draw_hud(canvas, player, font):
    panel = pygame.Surface((330, 104), pygame.SRCALPHA)
    draw_panel(panel, pygame.Rect(1, 1, 323, 96), fill=(25, 32, 38, 230), radius=10)
    pygame.draw.circle(panel, (176, 137, 72), (52, 49), 37)
    pygame.draw.circle(panel, (43, 61, 52), (52, 49), 33)
    portrait = pygame.transform.scale(frame(player.idle, 0, player.facing), (72, 72))
    panel.blit(portrait, (16, 13))
    panel.blit(font.render("AVENTUREIRO", True, (248, 224, 165)), (94, 9))
    panel.blit(font.render(f"Nv. {player.level}", True, (177, 187, 189)), (267, 9))
    draw_bar(panel, pygame.Rect(91, 32, 220, 25), player.hp, player.max_hp, (185, 51, 62), "HP", font)
    draw_bar(panel, pygame.Rect(91, 63, 220, 25), player.sp, player.max_sp, (54, 112, 196), "SP", font)
    canvas.blit(panel, (16, VIEW[1] - 120))
    xp_rect = pygame.Rect(107, VIEW[1] - 14, 220, 8)
    pygame.draw.rect(canvas, (18, 23, 27), xp_rect, border_radius=3)
    pygame.draw.rect(canvas, (191, 151, 67), (xp_rect.x, xp_rect.y, round(xp_rect.width * player.current_xp / player.xp_to_next_level), xp_rect.height), border_radius=3)

def fit_text(text, font, max_width):
    text = str(text)
    if font.size(text)[0] <= max_width: return text
    while text and font.size(text + "...")[0] > max_width: text = text[:-1]
    return text + "..."

def wrap_text(text, font, max_width, max_lines=3):
    words, lines, current = str(text).split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and font.size(candidate)[0] > max_width:
            lines.append(current); current = word
        else: current = candidate
    if current: lines.append(current)
    return [fit_text(line, font, max_width) for line in lines[:max_lines]]

def character_attribute_layout():
    stats = (("Vitalidade", "vitalidade", (198, 85, 85)),
             ("Força", "força", (214, 143, 69)),
             ("Magia", "magia", (111, 128, 220)),
             ("Agilidade", "agilidade", (84, 177, 113)))
    return [(label, key, color, pygame.Rect(355, 205 + index * 30, 577, 27),
             pygame.Rect(895, 207 + index * 30, 32, 23))
            for index, (label, key, color) in enumerate(stats)]


def attribute_preview_lines(player, key):
    next_stats = player.preview_stat(key)
    if next_stats is None:
        return ["Sem pontos disponíveis."]
    now = player.derived
    if key == "vitalidade":
        return [f"HP máx.: {now['max_hp']} → {next_stats['max_hp']}",
                f"Defesa: {now['defense']:.1f} → {next_stats['defense']:.1f}"]
    if key == "força":
        return [f"Ataque: {now['physical_attack']} → {next_stats['physical_attack']}",
                f"Empurrão: {now['knockback_power']:.2f}x → {next_stats['knockback_power']:.2f}x"]
    if key == "magia":
        return [f"SP máx.: {now['max_sp']} → {next_stats['max_sp']}",
                f"Poder mágico: {now['magic_power']} → {next_stats['magic_power']}"]
    cadence = (f"Cadência: {now['attack_cooldown']} → {next_stats['attack_cooldown']} frames"
               if now["attack_cooldown"] != next_stats["attack_cooldown"] else
               f"Cadência: {now['attack_cooldown']} frames (sem mudança)")
    return [f"Movimento: {now['move_speed']/attributes.BASE_MOVE_SPEED:.1%} → {next_stats['move_speed']/attributes.BASE_MOVE_SPEED:.1%}",
            cadence, f"Crítico: {now['crit_chance']:.1%} → {next_stats['crit_chance']:.1%}"]


def draw_character_menu(canvas, player, font, title_font, mouse_pos=(-1, -1)):
    shade = pygame.Surface(VIEW, pygame.SRCALPHA); shade.fill((5, 9, 12, 155)); canvas.blit(shade, (0, 0))
    panel = pygame.Rect(72, 28, 880, 520)
    draw_panel(canvas, panel, fill=(35, 43, 50), radius=13)
    pygame.draw.rect(canvas, (27, 34, 40), (panel.x + 4, panel.y + 4, panel.width - 8, 58), border_radius=10)
    canvas.blit(title_font.render("PERSONAGEM", True, (248, 224, 165)), (panel.x + 24, panel.y + 17))
    canvas.blit(font.render("V fechar  •  I inventário  •  ESC voltar", True, (180, 190, 193)), (panel.right - 294, panel.y + 23))

    card = pygame.Rect(92, 102, 245, 426)
    pygame.draw.rect(canvas, (25, 32, 38), card, border_radius=9); pygame.draw.rect(canvas, (82, 94, 98), card, 2, border_radius=9)
    pygame.draw.circle(canvas, (183, 143, 74), (card.centerx, card.y + 105), 72)
    pygame.draw.circle(canvas, (60, 91, 70), (card.centerx, card.y + 105), 67)
    sprite = pygame.transform.scale(frame(player.idle, 0, player.facing), (124, 124))
    canvas.blit(sprite, (card.centerx - 62, card.y + 43))
    name = title_font.render("Aventureiro", True, "white"); canvas.blit(name, (card.centerx - name.get_width()//2, card.y + 190))
    cls = font.render("Espadachim", True, (183, 192, 194)); canvas.blit(cls, (card.centerx - cls.get_width()//2, card.y + 221))
    lvl = title_font.render(f"Nível {player.level}", True, (248, 224, 165)); canvas.blit(lvl, (card.centerx - lvl.get_width()//2, card.y + 257))
    canvas.blit(font.render("EXPERIÊNCIA", True, (190, 198, 198)), (card.x + 20, card.y + 310))
    xp = pygame.Rect(card.x + 20, card.y + 339, card.width - 40, 15)
    pygame.draw.rect(canvas, (15, 20, 24), xp, border_radius=5)
    xp_fill = xp.inflate(-4, -4); xp_fill.width = round(xp_fill.width * player.current_xp / player.xp_to_next_level)
    if xp_fill.width: pygame.draw.rect(canvas, (193, 154, 75), xp_fill, border_radius=4)
    xp_text = font.render(f"{player.current_xp} / {player.xp_to_next_level} XP", True, (183, 192, 194))
    canvas.blit(xp_text, (card.centerx - xp_text.get_width()//2, card.y + 365))

    right_x, right_w = 355, 577
    draw_bar(canvas, pygame.Rect(right_x, 104, right_w, 31), player.hp, player.max_hp, (185, 51, 62), "HP", font)
    draw_bar(canvas, pygame.Rect(right_x, 143, right_w, 31), player.sp, player.max_sp, (54, 112, 196), "SP", font)
    canvas.blit(title_font.render("ATRIBUTOS", True, (248, 224, 165)), (right_x, 178))
    hovered_attribute = None
    for i, (label, key, color, row, plus) in enumerate(character_attribute_layout()):
        value = player.final_stats[key]
        hover = row.collidepoint(mouse_pos)
        pygame.draw.rect(canvas, (40, 51, 56) if hover else (27, 34, 40), row, border_radius=6)
        pygame.draw.rect(canvas, (102, 112, 105) if hover else (72, 82, 86), row, 1, border_radius=6)
        pygame.draw.circle(canvas, color, (row.x + 16, row.centery), 6)
        canvas.blit(font.render(label, True, "white"), (row.x + 30, row.y + 5))
        track = pygame.Rect(row.x + 155, row.y + 9, 210, 10)
        pygame.draw.rect(canvas, (17, 22, 26), track, border_radius=4)
        pygame.draw.rect(canvas, color, (track.x, track.y, min(track.width, value * 6), track.height), border_radius=4)
        bonus = player.equipment_bonus[key]
        value_label = f"{value} (+{bonus})" if bonus else str(value)
        value_text = font.render(value_label, True, (248, 224, 165))
        canvas.blit(value_text, (plus.x - value_text.get_width() - 10, row.y + 5))
        enabled = player.stat_points > 0
        pygame.draw.rect(canvas, (184, 145, 74) if enabled and plus.collidepoint(mouse_pos)
                         else (130, 102, 59) if enabled else (66, 73, 74), plus, border_radius=5)
        glyph = font.render("+", True, "white" if enabled else (141, 148, 148))
        canvas.blit(glyph, (plus.centerx - glyph.get_width() // 2, plus.y + 3))
        if hover:
            hovered_attribute = (label, key, plus.collidepoint(mouse_pos))
    canvas.blit(font.render(f"Pontos: {player.stat_points}   •   Clique em + ou use 1–4", True, (248, 224, 165)), (right_x, 331))

    canvas.blit(title_font.render("STATS DE COMBATE", True, (248, 224, 165)), (right_x, 351))
    combat = (("ATAQUE", str(player.physical_attack)), ("DEFESA", f"{player.defense:.1f}"),
              ("CRÍTICO", f"{player.crit_chance:.1%}"),
              ("VELOCIDADE", f"{player.speed/attributes.BASE_MOVE_SPEED:.0%}"),
              ("HP MÁX.", str(player.max_hp)), ("SP MÁX.", str(player.max_sp)),
              ("PODER MÁGICO", str(player.magic_power)),
              ("CADÊNCIA", f"{player.attack_cooldown_frames} frames"))
    for index, (label, value) in enumerate(combat):
        col, row = index % 2, index // 2
        x, y = right_x + col * 288, 379 + row * 18
        canvas.blit(font.render(label, True, (163, 180, 178)), (x, y))
        value_text = font.render(value, True, (244, 226, 176))
        canvas.blit(value_text, (x + 275 - value_text.get_width(), y))

    equip = pygame.Rect(right_x, 450, right_w, 78)
    pygame.draw.rect(canvas, (25, 32, 38), equip, border_radius=8); pygame.draw.rect(canvas, (82, 94, 98), equip, 1, border_radius=8)
    canvas.blit(font.render("EQUIPAMENTOS", True, (248, 224, 165)), (equip.x + 12, equip.y + 5))
    for i, slot in enumerate(SLOTS):
        entry = player.equipment.get(slot)
        label = f"{slot}: {(entry or {}).get('name', 'Nenhum')}"
        if entry and entry.get("bonuses"):
            label += "  " + "  ".join(f"+{amount} {key.title()}" for key, amount in entry["bonuses"].items())
        text = font.render(fit_text(label, font, equip.width - 28), True, (220, 224, 215))
        canvas.blit(text, (equip.x + 12, equip.y + 24 + i * 17))

    if hovered_attribute:
        label, key, on_plus = hovered_attribute
        descriptions = {"vitalidade": "Aumenta HP máximo e Defesa.",
                        "força": "Aumenta dano físico e empurrão.",
                        "magia": "Aumenta SP e Poder Mágico.",
                        "agilidade": "Aumenta movimento, cadência e crítico."}
        lines = attribute_preview_lines(player, key) if on_plus else [descriptions[key]]
        tooltip = pygame.Rect(min(mouse_pos[0] + 15, VIEW[0] - 340),
                              min(mouse_pos[1] + 14, VIEW[1] - 36 - len(lines) * 20),
                              324, 30 + len(lines) * 20)
        pygame.draw.rect(canvas, (18, 27, 32), tooltip, border_radius=7)
        pygame.draw.rect(canvas, (187, 145, 75), tooltip, 2, border_radius=7)
        canvas.blit(font.render(label.upper() + (" • PRÓXIMO PONTO" if on_plus else ""),
                                True, (248, 224, 165)), (tooltip.x + 10, tooltip.y + 6))
        for index, line in enumerate(lines):
            canvas.blit(font.render(line, True, (226, 231, 218)), (tooltip.x + 10, tooltip.y + 27 + index * 20))

def inventory_kind(item):
    if item.get("type") == "equipment" or item.get("slot"): return "equipment"
    if item.get("id") in CONSUMABLES: return "consumable"
    return "item"

def inventory_items(inventory, tab):
    if tab == "CONSUMÍVEIS": return [entry for entry in inventory if inventory_kind(entry) == "consumable"]
    if tab == "EQUIPAMENTO": return [entry for entry in inventory if inventory_kind(entry) == "equipment"]
    return list(inventory)

def inventory_action_label(item, player):
    if not item: return None
    if inventory_kind(item) == "consumable": return "USAR"
    if inventory_kind(item) == "equipment":
        equipped = player.equipment.get(item.get("slot"))
        return "DESEQUIPAR" if equipped and equipped.get("id") == item.get("id") else "EQUIPAR"
    return None

def inventory_layout(inventory, ui_state, player):
    panel = pygame.Rect(70, 34, 884, 508)
    tab_rects = [pygame.Rect(98 + i * 132, 98, 122, 34) for i in range(3)]
    shown = inventory_items(inventory, ui_state["tab"])
    slot_rects = [pygame.Rect(98 + col * 94, 160 + row * 98, 84, 84) for row in range(3) for col in range(5)]
    details = pygame.Rect(594, 148, 340, 323)
    action = pygame.Rect(616, 482, 296, 44)
    return panel, tab_rects, shown, slot_rects, details, action

def draw_inventory(canvas, inventory, font, title_font, player, ui_state, mouse_pos):
    shade = pygame.Surface(VIEW, pygame.SRCALPHA); shade.fill((5, 9, 12, 155)); canvas.blit(shade, (0, 0))
    panel, tab_rects, shown, slot_rects, details, action_rect = inventory_layout(inventory, ui_state, player)
    draw_panel(canvas, panel, fill=(35, 43, 50), radius=13)
    pygame.draw.rect(canvas, (27, 34, 40), (panel.x + 4, panel.y + 4, panel.width - 8, 54), border_radius=10)
    canvas.blit(title_font.render("INVENTÁRIO", True, (248, 224, 165)), (panel.x + 24, panel.y + 14))
    canvas.blit(font.render("I fechar  •  V personagem  •  ESC voltar", True, (180, 190, 193)), (panel.right - 294, panel.y + 21))
    tabs = ["TODOS", "CONSUMÍVEIS", "EQUIPAMENTO"]
    for index, (tab, rect) in enumerate(zip(tabs, tab_rects)):
        active = ui_state["tab"] == tab; hover = rect.collidepoint(mouse_pos)
        color = (178, 137, 69) if active else (66, 78, 84) if hover else (48, 57, 63)
        pygame.draw.rect(canvas, color, rect, border_radius=6)
        pygame.draw.rect(canvas, (218, 185, 112) if active or hover else (82, 94, 98), rect, 1, border_radius=6)
        label = font.render(tab, True, "white" if active or hover else (170, 180, 183))
        canvas.blit(label, (rect.centerx - label.get_width()//2, rect.y + 8))

    grid = pygame.Rect(86, 148, 490, 323)
    pygame.draw.rect(canvas, (26, 33, 39), grid, border_radius=8)
    selected = ui_state.get("selected")
    for index, rect in enumerate(slot_rects):
        item = shown[index] if index < len(shown) else None
        is_selected = item is not None and item is selected
        hovered = rect.collidepoint(mouse_pos)
        fill = (53, 59, 60) if hovered else (35, 42, 47) if is_selected else (22, 28, 33)
        border = (240, 205, 132) if is_selected else (169, 137, 77) if hovered else (82, 94, 98)
        pygame.draw.rect(canvas, fill, rect, border_radius=7); pygame.draw.rect(canvas, border, rect, 2 if is_selected or hovered else 1, border_radius=7)
        if item is None: continue
        color = item.get("color", (110, 130, 130))
        pygame.draw.circle(canvas, (14, 18, 22), (rect.centerx, rect.y + 31), 21)
        pygame.draw.circle(canvas, color, (rect.centerx, rect.y + 31), 17)
        pygame.draw.circle(canvas, (245, 226, 160), (rect.centerx - 5, rect.y + 26), 4)
        name = font.render(fit_text(item.get("name", "Item"), font, rect.width - 8), True, "white")
        canvas.blit(name, (rect.centerx - name.get_width()//2, rect.y + 56))
        amount_count = item.get("amount", 1)
        if amount_count > 1:
            badge = pygame.Rect(rect.right - 23, rect.y + 3, 20, 18)
            pygame.draw.rect(canvas, (178, 137, 69), badge, border_radius=6)
            amount_text = font.render(str(amount_count), True, "white")
            canvas.blit(amount_text, (badge.centerx - amount_text.get_width()//2, badge.y + 1))
        if inventory_kind(item) == "equipment" and any(e and e.get("id") == item.get("id") for e in player.equipment.values()):
            pygame.draw.circle(canvas, (84, 177, 113), (rect.x + 11, rect.y + 11), 9)
            e_text = font.render("E", True, "white"); canvas.blit(e_text, (rect.x + 11 - e_text.get_width()//2, rect.y + 2))

    pygame.draw.rect(canvas, (26, 33, 39), details, border_radius=8); pygame.draw.rect(canvas, (82, 94, 98), details, 1, border_radius=8)
    if selected is not None and selected in inventory:
        kind = inventory_kind(selected)
        pygame.draw.circle(canvas, selected.get("color", (110, 130, 130)), (details.centerx, details.y + 43), 25)
        name_lines = wrap_text(selected.get("name", "Item"), title_font, details.width - 30, 2)
        for i, line in enumerate(name_lines): canvas.blit(title_font.render(line, True, (248, 224, 165)), (details.x + 16, details.y + 78 + i*27))
        kind_y = details.y + 132 if len(name_lines) > 1 else details.y + 108
        sub = f"Equipamento • {selected.get('slot', '')}" if kind == "equipment" else "Consumível" if kind == "consumable" else "Item"
        canvas.blit(font.render(sub, True, (112, 181, 124)), (details.x + 16, kind_y))
        description = selected.get("description") or {"Poção": "Recupera 30 pontos de vida.", "Éter": "Recupera 30 pontos de espírito.", "Erva": "Recupera 15 pontos de vida."}.get(selected.get("name"), "Um item encontrado durante a aventura.")
        desc_y = kind_y + 30
        for i, line in enumerate(wrap_text(description, font, details.width - 32, 3)):
            canvas.blit(font.render(line, True, (210, 216, 216)), (details.x + 16, desc_y + i*22))
        bonus_y = desc_y + 70
        if kind == "equipment":
            bonus_text = ", ".join(f"+{amount} {key.title()}" for key, amount in selected.get("bonuses", {}).items()) or "Sem bônus"
            for i, line in enumerate(wrap_text("Bônus: " + bonus_text, font, details.width - 32, 2)):
                canvas.blit(font.render(line, True, (248, 224, 165)), (details.x + 16, bonus_y + i*22))
        elif kind == "consumable":
            effect = "+30 HP" if selected.get("name") == "Poção" else "+30 SP" if selected.get("name") == "Éter" else "+15 HP"
            canvas.blit(font.render(f"Efeito: {effect}   Quantidade: {selected.get('amount', 1)}", True, (248, 224, 165)), (details.x + 16, bonus_y))
    else:
        canvas.blit(title_font.render("Selecione um item", True, (205, 210, 205)), (details.x + 18, details.y + 30))
        canvas.blit(font.render("Clique em um espaço do inventário", True, (160, 173, 177)), (details.x + 18, details.y + 66))

    action_label = inventory_action_label(selected, player) if selected in inventory else None
    if action_label:
        hover = action_rect.collidepoint(mouse_pos)
        color = (202, 163, 87) if hover else (158, 119, 57)
        pygame.draw.rect(canvas, color, action_rect, border_radius=7)
        pygame.draw.rect(canvas, (238, 208, 150), action_rect, 2, border_radius=7)
        label = title_font.render(action_label, True, (255, 250, 232))
        canvas.blit(label, (action_rect.centerx - label.get_width()//2, action_rect.centery - label.get_height()//2))

def apply_inventory_action(selected, inventory, player, ui_state):
    if player.hp <= 0:
        return False, "Não é possível usar itens agora."
    if selected is None or not any(entry is selected for entry in inventory):
        return False, "Selecione um item primeiro."
    kind = inventory_kind(selected)
    if kind == "equipment":
        slot = selected["slot"]
        equipped = player.equipment.get(slot)
        if equipped and equipped.get("id") == selected.get("id"):
            player.unequip(slot)
            return True, f"{selected['name']} desequipado."
        replaced = player.equip(selected)
        message = f"{selected['name']} equipado."
        if replaced and replaced.get("id") != selected.get("id"):
            message = f"{selected['name']} equipado no lugar de {replaced['name']}."
        return True, message

    if kind == "consumable":
        cooldown = ui_state.get("consumable_cooldown", 0)
        if cooldown > 0:
            return False, f"Aguarde {cooldown / FPS:.1f}s para usar outro consumível."
        name = selected.get("name")
        definition = CONSUMABLES.get(selected.get("id"), {})
        target, amount = definition.get("resource"), definition.get("restore", 0)
        if target is None: return False, "Esse item não pode ser usado agora."
        current, maximum = getattr(player, target), getattr(player, f"max_{target}")
        if current >= maximum:
            return False, "Vida já está cheia." if target == "hp" else "SP já está cheio."
        restored = min(amount, maximum - current)
        setattr(player, target, current + restored)
        ui_state["consumable_cooldown"] = CONSUMABLE_COOLDOWN_FRAMES
        selected["amount"] = selected.get("amount", 1) - 1
        if selected["amount"] <= 0:
            del inventory[next(index for index, entry in enumerate(inventory) if entry is selected)]
            ui_state["selected"] = None
        return True, f"{name}: +{restored} {'HP' if target == 'hp' else 'SP'}."
    return False, "Esse item não possui uma ação disponível."

def handle_inventory_click(pos, inventory, player, ui_state):
    _, tab_rects, shown, slot_rects, _, action_rect = inventory_layout(inventory, ui_state, player)
    tabs = ["TODOS", "CONSUMÍVEIS", "EQUIPAMENTO"]
    for tab, rect in zip(tabs, tab_rects):
        if rect.collidepoint(pos):
            ui_state["tab"] = tab
            if ui_state.get("selected") not in inventory_items(inventory, tab): ui_state["selected"] = None
            return None
    for index, rect in enumerate(slot_rects):
        if rect.collidepoint(pos):
            ui_state["selected"] = shown[index] if index < len(shown) else None
            return None
    selected = ui_state.get("selected")
    if action_rect.collidepoint(pos) and inventory_action_label(selected, player):
        return apply_inventory_action(selected, inventory, player, ui_state)
    return None

def logical_mouse_position(position):
    return (position[0] * VIEW[0] // WINDOW[0], position[1] * VIEW[1] // WINDOW[1])


def handle_character_click(position, player):
    for _, key, _, _, plus in character_attribute_layout():
        if plus.collidepoint(position):
            return player.spend_stat(key)
    return False


def main():
    pygame.init(); pygame.display.set_caption("O Vale RPG | v0.12")
    screen = pygame.display.set_mode(WINDOW); canvas = pygame.Surface(VIEW); clock = pygame.time.Clock()
    player = Player(load("assets/player/f_player_sheet.png"), load("assets/player/f_player_attack_sheet.png"))
    current_region = "village"
    region = build_region(current_region)
    enemies = spawn_enemies(region)
    drops = []
    damage_numbers = []
    font = pygame.font.Font(None, 22); title_font = pygame.font.Font(None, 30)
    inventory = [consumable("potion", 3), consumable("ether", 2), consumable("herb", 5), item("iron_blade"), item("reinforced_leather")]
    ui_mode = None
    dialogue = DialogueBox()
    quest_manager = QuestManager()
    opened_desert_chests = set()
    inventory_ui = {"tab": "TODOS", "selected": None, "consumable_cooldown": 0}
    dialogue.inventory = inventory
    debug = False
    hitstop_frames = 0
    game_over_screen = None
    autosave_allowed = True
    if save_manager.SAVE_PATH.exists():
        try:
            save_manager.read_save(save_manager.SAVE_PATH)
        except save_manager.SaveError:
            autosave_allowed = False
            quest_manager.notice = "Save inválido encontrado. Autosave pausado; F5 para substituir."
            quest_manager.notice_timer = 360

    def load_last_save():
        nonlocal player, inventory, quest_manager, current_region, region, enemies
        nonlocal drops, opened_desert_chests, damage_numbers, hitstop_frames
        nonlocal dialogue, ui_mode, inventory_ui, autosave_allowed, game_over_screen
        try:
            loaded = save_manager.load_game(
                save_manager.SAVE_PATH,
                lambda: Player(player.idle, player.attack_sheet),
                build_region, spawn_enemies,
                lambda: Enemy("forest_guardian", (1300, 430), load, seed=77))
        except save_manager.MissingSaveError:
            quest_manager.notice = "Nenhum save encontrado."
            quest_manager.notice_timer = 180
            return False
        except save_manager.SaveError:
            autosave_allowed = False
            quest_manager.notice = "Save inválido ou corrompido; jogo atual preservado."
            quest_manager.notice_timer = 180
            return False
        player, inventory, quest_manager = loaded.player, loaded.inventory, loaded.quests
        current_region, region, enemies = loaded.region_id, loaded.region, loaded.enemies
        drops, opened_desert_chests = loaded.drops, loaded.opened_chests
        damage_numbers = []
        hitstop_frames = 0
        dialogue.npc = None
        dialogue.inventory = inventory
        ui_mode = None
        inventory_ui = {"tab": "TODOS", "selected": None, "consumable_cooldown": 0}
        autosave_allowed = True
        game_over_screen = None
        quest_manager.notice = "Jogo carregado."
        quest_manager.notice_timer = 180
        return True

    def continue_after_death():
        nonlocal region, enemies, damage_numbers, hitstop_frames, ui_mode
        nonlocal game_over_screen, inventory_ui
        if (current_region == "forest" and quest_manager.forest_event_started
                and not quest_manager.forest_boss_defeated):
            region, enemies = reset_forest_boss_encounter()
        restore_player_after_death(player, current_region, region, enemies)
        player.sp_idle_frames = 0
        damage_numbers = []
        hitstop_frames = 0
        ui_mode = None
        dialogue.npc = None
        inventory_ui["consumable_cooldown"] = 0
        game_over_screen = None

    running = True
    while running:
        autosave_pending = False
        if inventory_ui["consumable_cooldown"] > 0:
            inventory_ui["consumable_cooldown"] -= 1
        if game_over_screen is not None:
            game_over_screen.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif game_over_screen is not None:
                mouse_position = (logical_mouse_position(event.pos)
                                  if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN) else (0, 0))
                choice = game_over_screen.handle_event(event, mouse_position, VIEW)
                if choice == "continue":
                    continue_after_death()
                elif choice == "load":
                    load_last_save()
                    if game_over_screen is not None:
                        game_over_screen.notice = quest_manager.notice
                elif choice == "quit":
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and ui_mode == "character":
                handle_character_click(logical_mouse_position(event.pos), player)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and ui_mode == "inventory":
                result = handle_inventory_click(logical_mouse_position(event.pos), inventory, player, inventory_ui)
                if result:
                    _, notice = result
                    quest_manager.notice, quest_manager.notice_timer = notice, 150
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5:
                    if player.hp <= 0:
                        quest_manager.notice = "Não é possível salvar após a derrota."
                    else:
                        try:
                            save_manager.save_game(player, inventory, quest_manager, current_region,
                                                   opened_desert_chests, drops)
                        except save_manager.SaveError:
                            quest_manager.notice = "Não foi possível salvar o jogo."
                        else:
                            autosave_allowed = True
                            quest_manager.notice = "Jogo salvo."
                    quest_manager.notice_timer = 180
                elif event.key == pygame.K_F9:
                    load_last_save()
                elif event.key == pygame.K_ESCAPE:
                    if dialogue.active: dialogue.npc = None
                    elif ui_mode is not None: ui_mode = None
                    else: running = False
                elif event.key == pygame.K_e:
                    if dialogue.active:
                        quest_state = quest_manager.get("forest_trouble").state
                        dialogue.advance()
                        if quest_state != quest_manager.get("forest_trouble").state and quest_manager.get("forest_trouble").state == "REWARDED":
                            autosave_pending = True
                    elif ui_mode is None:
                        targets = region.get("npcs", []) + [obj for obj in region.get("interactables", []) if not obj.opened]
                        target = nearest(targets, player)
                        if target is not None:
                            if isinstance(target, NPC):
                                target.face_player(player); dialogue.open(target, quest_manager)
                            elif not target.opened:
                                target.opened = True
                                opened_desert_chests.add(target.uid)
                                loot = target.loot
                                add_inventory_item(inventory, loot)
                                quest_manager.notice = f"Baú: {loot['amount']}x {loot['name']}"
                                quest_manager.notice_timer = 160
                elif event.key == pygame.K_v:
                    if not dialogue.active:
                        ui_mode = None if ui_mode == "character" else "character"
                elif event.key == pygame.K_i:
                    if not dialogue.active:
                        ui_mode = None if ui_mode == "inventory" else "inventory"
                elif event.key == pygame.K_F3:
                    debug = not debug
                elif ui_mode == "character" and event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    player.spend_stat(("vitalidade", "força", "magia", "agilidade")[event.key - pygame.K_1])
                elif ui_mode == "inventory" and event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8):
                    shown = inventory_items(inventory, inventory_ui["tab"])
                    index = event.key - pygame.K_1
                    if index < len(shown):
                        inventory_ui["selected"] = shown[index]
                        result = apply_inventory_action(shown[index], inventory, player, inventory_ui)
                        if result: quest_manager.notice, quest_manager.notice_timer = result[1], 150
                elif event.key == pygame.K_SPACE and ui_mode is None and not dialogue.active:
                    player.attack()
                elif event.key == pygame.K_q and ui_mode is None and not dialogue.active:
                    player.start_dash(pygame.key.get_pressed())
        if game_over_screen is not None:
            pass
        elif hitstop_frames > 0:
            hitstop_frames -= 1
        elif ui_mode is None and not dialogue.active and player.hp > 0:
            if current_region == "forest":
                region["north_locked"] = not quest_manager.forest_boss_defeated
            # O encontro só pode nascer depois da recompensa da primeira quest.
            if current_region == "forest" and quest_manager.forest_ready() and not quest_manager.forest_event_started:
                arena = region.get("arena")
                if arena and arena.collidepoint(player.x, player.y):
                    quest_manager.forest_event_started = True
                    region["arena_locked"] = True
                    region["obstacles"].append(region["exits"]["desert"].inflate(30, 20))
                    enemies = [Enemy("forest_guardian", (1300, 430), load, seed=77)]
                    quest_manager.notice, quest_manager.notice_timer = "Algo observa você entre as árvores...", 180
            if current_region == "forest" and quest_manager.forest_event_started and not quest_manager.forest_boss_defeated:
                region["arena_locked"] = True
                enemies = [e for e in enemies if e.kind == "forest_guardian" or e.state != "DEAD"]
            player.update(pygame.key.get_pressed(), region["obstacles"])
            for enemy in enemies:
                hp_before = player.hp
                enemy.update(player, region["obstacles"])
                if player.hp < hp_before:
                    hitstop_frames = max(hitstop_frames, HITSTOP_STRONG_FRAMES
                                         if enemy.attack_action == "charged" else HITSTOP_NORMAL_FRAMES)
                    damage_numbers.append(DamageNumber(str(hp_before - player.hp),
                                                       player.x, player.y - 82, (250, 108, 104)))
                if player.attack_box.colliderect(enemy.hurtbox) and getattr(enemy, "last_player_attack", -1) != player.attack_serial:
                    enemy_hp_before = enemy.hp
                    if enemy.receive_hit(player.current_attack_damage, player.x, player.y,
                                         player.knockback_power):
                        hitstop_frames = max(hitstop_frames, HITSTOP_STRONG_FRAMES
                                             if player.attack_is_critical else HITSTOP_NORMAL_FRAMES)
                        enemy.last_player_attack = player.attack_serial
                        damage_numbers.append(DamageNumber(
                            f"{enemy_hp_before - enemy.hp}{'!' if player.attack_is_critical else ''}",
                            enemy.x, enemy.y - enemy.config["frame_size"] * enemy.config["scale"] * 0.8,
                            (255, 210, 103) if player.attack_is_critical
                            else (238, 239, 223), player.attack_is_critical))
                new_drop = enemy.drop()
                if new_drop is not None:
                    drops.append(new_drop)
                if enemy.state == "DEAD" and enemy.dead_timer == 35:
                    old_level = player.level
                    player.gain_xp(enemy.config.get("xp_reward", 0))
                    quest_manager.notice = f"+{enemy.config.get('xp_reward', 0)} XP"
                    quest_manager.notice_timer = 120
                    if player.level > old_level:
                        quest_manager.notice = f"LEVEL UP! Nível {player.level}  |  +{STAT_POINTS_PER_LEVEL} pontos"
                        quest_manager.notice_timer = 210
                    quest_state = quest_manager.get("forest_trouble").state
                    quest_manager.enemy_defeated(enemy.kind)
                    if quest_state != quest_manager.get("forest_trouble").state and quest_manager.get("forest_trouble").state == "COMPLETED":
                        autosave_pending = True
                    if enemy.kind == "forest_guardian":
                        quest_manager.forest_boss_defeated = True
                        region["arena_locked"] = False
                        region["obstacles"] = [r for r in region["obstacles"] if r != region["exits"]["desert"].inflate(30, 20)]
                        quest_manager.notice, quest_manager.notice_timer = "A clareira está livre. O caminho ao norte foi aberto.", 240
                        if not quest_manager.boss_loot_given:
                            inventory.append(item("grove_charm")); quest_manager.boss_loot_given = True
                            quest_manager.notice = "Amuleto da Clareira recebido!"
                            quest_manager.notice_timer = 210
                        autosave_pending = True
                if player.hp <= 0:
                    break
            enemies = [enemy for enemy in enemies if enemy.state != "DEAD" or enemy.dead_timer > 0]
            if player.hp <= 0 and game_over_screen is None:
                game_over_screen = game_over.GameOverScreen()
                ui_mode = None
                dialogue.npc = None
                hitstop_frames = 0
            drops = [drop for drop in drops if drop.update()]
            for drop in drops[:] if player.hp > 0 else []:
                if player.hitbox.colliderect(drop.hitbox):
                    add_inventory_item(inventory, drop.item)
                    drops.remove(drop)
            for destination, exit_rect in (region["exits"].items() if player.hp > 0 else ()):
                if player.hitbox.colliderect(exit_rect):
                    if not can_transition(current_region, destination, quest_manager):
                        quest_manager.notice = "Derrote o Guardião da Clareira para seguir ao norte."
                        quest_manager.notice_timer = 150
                        continue
                    if destination == "ruins_future":
                        if not region.get("future_exit_notified"):
                            quest_manager.notice = "A estrada continua até as ruínas distantes."
                            quest_manager.notice_timer = 150
                            region["future_exit_notified"] = True
                        continue
                    if destination not in {"village", "forest", "desert"}: continue
                    previous_region = current_region
                    current_region = destination
                    region, enemies = save_manager.prepare_region(
                        current_region, quest_manager, opened_desert_chests,
                        build_region, spawn_enemies,
                        lambda: Enemy("forest_guardian", (1300, 430), load, seed=77))
                    drops = []
                    damage_numbers = []
                    player.x, player.y = region["spawn"].get(previous_region, (1024, 576))
                    player.attack_timer = 0
                    player.attack_cooldown_timer = 0
                    player.dash_timer = player.dash_iframes = 0
                    player.invulnerability_timer = 30
                    autosave_pending = True
                    break
        if autosave_pending and autosave_allowed and player.hp > 0 and game_over_screen is None:
            try:
                save_manager.save_game(player, inventory, quest_manager, current_region,
                                       opened_desert_chests, drops)
            except save_manager.SaveError:
                quest_manager.notice, quest_manager.notice_timer = "Autosave falhou.", 180
        camera = camera_for(player)
        quest_manager.update()
        draw_world(canvas, region, font, camera, player, enemies, drops, debug)
        if hitstop_frames == 0:
            damage_numbers = [number for number in damage_numbers if number.update()]
        for number in damage_numbers:
            number.draw(canvas, camera, font, title_font)
        draw_hud(canvas, player, font)
        dialogue.draw(canvas, font, title_font)
        quest_text = quest_manager.active_text()
        if quest_text:
            canvas.blit(font.render(quest_text, True, (244, 224, 166)), (VIEW[0] - 310, 52))
        if quest_manager.notice_timer:
            canvas.blit(font.render(quest_manager.notice, True, (255, 235, 170)), (VIEW[0]//2 - 110, 42))
        boss = next((e for e in enemies if e.kind == "forest_guardian" and e.state != "DEAD"), None)
        if boss:
            bar = pygame.Rect(280, 78, 464, 22)
            pygame.draw.rect(canvas, (25, 25, 28), bar, border_radius=5)
            pygame.draw.rect(canvas, (166, 50, 62), (bar.x, bar.y, round(bar.width * boss.hp / boss.max_hp), bar.height), border_radius=5)
            pygame.draw.rect(canvas, (235, 207, 142), bar, 2, border_radius=5)
            canvas.blit(font.render(f"{boss.name}  {boss.hp}/{boss.max_hp}", True, "white"), (bar.x + 10, bar.y + 3))
        if ui_mode == "character":
            draw_character_menu(canvas, player, font, title_font,
                                logical_mouse_position(pygame.mouse.get_pos()))
        elif ui_mode == "inventory":
            mouse_pos = logical_mouse_position(pygame.mouse.get_pos())
            draw_inventory(canvas, inventory, font, title_font, player, inventory_ui, mouse_pos)
        if game_over_screen is not None:
            game_over_screen.draw(canvas, font, title_font, logical_mouse_position(pygame.mouse.get_pos()))
        pygame.transform.scale(canvas, WINDOW, screen); pygame.display.flip(); clock.tick(FPS)
    pygame.quit(); return 0

if __name__ == "__main__": sys.exit(main())
