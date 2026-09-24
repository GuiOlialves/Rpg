"""Fórmulas únicas dos atributos e dos stats derivados do personagem."""

PRIMARY = ("vitalidade", "força", "magia", "agilidade")

BASE_HP = 50
HP_PER_VITALITY = 5
BASE_SP = 36
SP_PER_MAGIC = 4
BASE_PHYSICAL_ATTACK = 8
DAMAGE_PER_STRENGTH = 2
BASE_MAGIC_POWER = 4
MAGIC_POWER_PER_MAGIC = 1.5
BASE_DEFENSE = 1.0
DEFENSE_PER_VITALITY = 0.75
DEFENSE_CURVE = 60.0
BASE_MOVE_SPEED = 3.0
SPEED_PER_AGILITY = 0.025
MAX_MOVE_SPEED = 3.5
ATTACK_ANIMATION_FRAMES = 16
BASE_ATTACK_COOLDOWN = 20
MIN_ATTACK_COOLDOWN = ATTACK_ANIMATION_FRAMES
AGILITY_PER_COOLDOWN_FRAME = 7
BASE_CRIT_CHANCE = 0.02
CRIT_PER_AGILITY = 0.004
MAX_CRIT_CHANCE = 0.30
BASE_CRIT_MULTIPLIER = 1.5
MAX_CRIT_MULTIPLIER = 2.0
KNOCKBACK_PER_STRENGTH = 0.008
MAX_KNOCKBACK_POWER = 1.25


def calculate(base_stats, equipment, modifiers=None):
    """Retorna atributos finais, bônus de equipamento e derivados sem mutar a origem."""
    equipment_bonus = {name: 0 for name in PRIMARY}
    flat_bonus = {}
    for equipped in equipment.values():
        if not equipped:
            continue
        for name, value in equipped.get("bonuses", {}).items():
            if name in equipment_bonus:
                equipment_bonus[name] += value
            else:
                flat_bonus[name] = flat_bonus.get(name, 0) + value
    for name, value in (modifiers or {}).items():
        flat_bonus[name] = flat_bonus.get(name, 0) + value

    final = {name: base_stats[name] + equipment_bonus[name] + flat_bonus.get(name, 0)
             for name in PRIMARY}
    vitality, strength, magic, agility = (final[name] for name in PRIMARY)
    weapon = equipment.get("Arma") or {}
    derived = {
        "max_hp": max(1, round(BASE_HP + vitality * HP_PER_VITALITY + flat_bonus.get("max_hp", 0))),
        "max_sp": max(1, round(BASE_SP + magic * SP_PER_MAGIC + flat_bonus.get("max_sp", 0))),
        "physical_attack": max(1, round(BASE_PHYSICAL_ATTACK + strength * DAMAGE_PER_STRENGTH
                                        + weapon.get("base_attack", 0) + flat_bonus.get("physical_attack", 0))),
        "magic_power": max(0, round(BASE_MAGIC_POWER + magic * MAGIC_POWER_PER_MAGIC
                                    + flat_bonus.get("magic_power", 0))),
        "defense": max(0.0, BASE_DEFENSE + vitality * DEFENSE_PER_VITALITY
                       + flat_bonus.get("defense", 0)),
        "move_speed": max(2.5, min(MAX_MOVE_SPEED, BASE_MOVE_SPEED + agility * SPEED_PER_AGILITY
                                    + flat_bonus.get("move_speed", 0))),
        "attack_cooldown": max(MIN_ATTACK_COOLDOWN, min(BASE_ATTACK_COOLDOWN,
                               BASE_ATTACK_COOLDOWN - int(agility // AGILITY_PER_COOLDOWN_FRAME)
                               - int(flat_bonus.get("attack_speed", 0)))),
        "crit_chance": max(0.0, min(MAX_CRIT_CHANCE, BASE_CRIT_CHANCE + agility * CRIT_PER_AGILITY
                                   + flat_bonus.get("crit_chance", 0))),
        "crit_multiplier": max(1.0, min(MAX_CRIT_MULTIPLIER, BASE_CRIT_MULTIPLIER
                                       + flat_bonus.get("crit_multiplier", 0))),
        "knockback_power": max(1.0, min(MAX_KNOCKBACK_POWER, 1.0 + strength * KNOCKBACK_PER_STRENGTH
                                         + flat_bonus.get("knockback_power", 0))),
    }
    return final, equipment_bonus, derived


def physical_damage_after_defense(amount, defense):
    """A redução é proporcional; um golpe válido sempre causa ao menos 1 dano."""
    return max(1, round(max(0, amount) * DEFENSE_CURVE / (DEFENSE_CURVE + max(0, defense))))
