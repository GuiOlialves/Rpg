"""Per-frame combat, enemy rewards and combat feedback data."""
from dataclasses import dataclass, field

import pygame

from core.config import HITSTOP_NORMAL_FRAMES, HITSTOP_STRONG_FRAMES, STAT_POINTS_PER_LEVEL
from systems.equipment import item
from systems.inventory import add_inventory_item


@dataclass(frozen=True)
class CombatFeedback:
    text: str
    position: tuple
    color: tuple
    critical: bool = False


@dataclass
class CombatFrame:
    enemies: list
    drops: list
    hitstop_frames: int
    autosave_pending: bool = False
    player_defeated: bool = False
    feedback: list = field(default_factory=list)


class CombatSystem:
    def __init__(self, load):
        self.load = load

    def update(self, player, region_id, region, enemies, drops, inventory,
               quests, hitstop_frames):
        feedback = []
        autosave_pending = False
        if region_id == "forest":
            region["north_locked"] = not quests.forest_boss_defeated

        # Encontros futuros dependem do estado narrativo explícito, não da
        # conclusão da primeira missão de Slimes.
        if region_id == "forest" and quests.forest_event_started and not quests.forest_boss_defeated:
            region["arena_locked"] = True
            enemies = [enemy for enemy in enemies
                       if enemy.kind == "forest_guardian" or enemy.state != "DEAD"]

        player.update(pygame.key.get_pressed(), region["obstacles"])
        for enemy in enemies:
            hp_before = player.hp
            enemy.update(player, region["obstacles"])
            if player.hp < hp_before:
                hitstop_frames = max(
                    hitstop_frames,
                    HITSTOP_STRONG_FRAMES if enemy.attack_action == "charged"
                    else HITSTOP_NORMAL_FRAMES)
                feedback.append(CombatFeedback(
                    str(hp_before - player.hp), (player.x, player.y - 82),
                    (250, 108, 104)))

            if (player.attack_box.colliderect(enemy.hurtbox)
                    and getattr(enemy, "last_player_attack", -1) != player.attack_serial):
                enemy_hp_before = enemy.hp
                if enemy.receive_hit(player.current_attack_damage, player.x, player.y,
                                     player.knockback_power):
                    hitstop_frames = max(
                        hitstop_frames,
                        HITSTOP_STRONG_FRAMES if player.attack_is_critical
                        else HITSTOP_NORMAL_FRAMES)
                    enemy.last_player_attack = player.attack_serial
                    feedback.append(CombatFeedback(
                        f"{enemy_hp_before - enemy.hp}{'!' if player.attack_is_critical else ''}",
                        (enemy.x, enemy.y - enemy.config["frame_size"]
                         * enemy.config["scale"] * 0.8),
                        (255, 210, 103) if player.attack_is_critical else (238, 239, 223),
                        player.attack_is_critical))

            new_drop = enemy.drop()
            if new_drop is not None:
                drops.append(new_drop)
            if enemy.state == "DEAD" and enemy.dead_timer == 35:
                old_level = player.level
                reward_xp = enemy.config.get("xp_reward", 0)
                player.gain_xp(reward_xp)
                quests.notice, quests.notice_timer = f"+{reward_xp} XP", 120
                if player.level > old_level:
                    quests.notice = f"LEVEL UP! Nível {player.level}  |  +{STAT_POINTS_PER_LEVEL} pontos"
                    quests.notice_timer = 210
                quest_state = quests.get("forest_trouble").state
                quests.enemy_defeated(enemy.kind)
                if (quest_state != quests.get("forest_trouble").state
                        and quests.get("forest_trouble").state == "COMPLETED"):
                    autosave_pending = True
                if enemy.kind == "forest_guardian":
                    quests.forest_boss_defeated = True
                    region["arena_locked"] = False
                    lock = region["exits"]["desert"].inflate(30, 20)
                    region["obstacles"] = [obstacle for obstacle in region["obstacles"]
                                           if obstacle != lock]
                    quests.notice = "A clareira está livre. O caminho ao norte foi aberto."
                    quests.notice_timer = 240
                    if not quests.boss_loot_given:
                        inventory.append(item("grove_charm"))
                        quests.boss_loot_given = True
                        quests.notice = "Amuleto da Clareira recebido!"
                        quests.notice_timer = 210
                    autosave_pending = True
            if player.hp <= 0:
                break

        enemies = [enemy for enemy in enemies
                   if enemy.state != "DEAD" or enemy.dead_timer > 0]
        drops = [drop for drop in drops if drop.update()]
        for drop in drops[:] if player.hp > 0 else []:
            if player.hitbox.colliderect(drop.hitbox):
                add_inventory_item(inventory, drop.item)
                drops.remove(drop)
        return CombatFrame(enemies, drops, hitstop_frames, autosave_pending,
                           player.hp <= 0, feedback)
