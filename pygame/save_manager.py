"""Save/Load transacional em JSON para o estado persistente do RPG."""

from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import tempfile

import pygame

from enemy import Drop
from equipment import EQUIPMENT, SLOTS, item as equipment_item
from items import CONSUMABLES, consumable
from quest import ACTIVE, AVAILABLE, COMPLETED, REWARDED, QuestManager


SAVE_VERSION = 1
SAVE_PATH = Path(__file__).with_name("savegame.json")
REGIONS = {"village", "forest", "desert"}
CHESTS = {"desert_chest_oasis", "desert_chest_ruins", "desert_chest_hidden"}
STATS = ("vitalidade", "força", "magia", "agilidade")
SAFE_SPAWNS = {
    "village": ((1024, 576), (1850, 575)),
    "forest": ((120, 575), (1245, 82)),
    "desert": ((1025, 105),),
}


class SaveError(Exception):
    """O arquivo não pôde ser salvo ou carregado sem risco ao estado atual."""


class MissingSaveError(SaveError):
    pass


@dataclass
class LoadedGame:
    player: object
    inventory: list
    quests: QuestManager
    region_id: str
    region: dict
    enemies: list
    drops: list
    opened_chests: set


def _object(value, label):
    if not isinstance(value, dict):
        raise SaveError(f"Save inválido: {label} não é um objeto.")
    return value


def _integer(value, label, minimum=0, maximum=1_000_000):
    if type(value) is not int or not minimum <= value <= maximum:
        raise SaveError(f"Save inválido: {label} fora dos limites.")
    return value


def _number(value, label, minimum=0, maximum=2048):
    if type(value) not in (int, float) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise SaveError(f"Save inválido: {label} fora dos limites.")
    return value


def _boolean(value, label):
    if type(value) is not bool:
        raise SaveError(f"Save inválido: {label} não é booleano.")
    return value


def _position(value, label):
    if not isinstance(value, list) or len(value) != 2:
        raise SaveError(f"Save inválido: {label} precisa de duas coordenadas.")
    return (_number(value[0], label + ".x"), _number(value[1], label + ".y", maximum=1152))


def _item_record(value, label, equipment_allowed=True):
    data = _object(value, label)
    item_id = data.get("id")
    if type(item_id) is not str or item_id not in CONSUMABLES and (not equipment_allowed or item_id not in EQUIPMENT):
        raise SaveError(f"Save inválido: ID de item desconhecido em {label}.")
    amount = _integer(data.get("amount"), label + ".amount", 1, 9999)
    if item_id in EQUIPMENT and amount != 1:
        raise SaveError(f"Save inválido: equipamento empilhado em {label}.")
    return item_id, amount


def validate(data):
    data = _object(data, "raiz")
    if _integer(data.get("save_version"), "save_version", 1, 999) != SAVE_VERSION:
        raise SaveError("Versão de save não suportada.")
    region_id = data.get("region")
    if region_id not in REGIONS:
        raise SaveError("Save inválido: região desconhecida.")

    character = _object(data.get("player"), "player")
    level = _integer(character.get("level"), "level", 1, 10000)
    xp_to_next = _integer(character.get("xp_to_next_level"), "xp_to_next_level", 1)
    if xp_to_next != 100 + (level - 1) * 55:
        raise SaveError("Save inválido: XP necessária não corresponde ao nível.")
    _integer(character.get("current_xp"), "current_xp", 0, xp_to_next - 1)
    _integer(character.get("stat_points"), "stat_points")
    stats = _object(character.get("stats"), "stats")
    if set(stats) != set(STATS):
        raise SaveError("Save inválido: atributos incompletos.")
    for name in STATS:
        _integer(stats[name], name, 1, 10000)
    _integer(character.get("hp"), "hp")
    _integer(character.get("sp"), "sp")
    _position(character.get("position"), "position")
    inventory = data.get("inventory")
    if not isinstance(inventory, list) or len(inventory) > 1000:
        raise SaveError("Save inválido: inventário.")
    inventory_ids = set()
    for index, entry in enumerate(inventory):
        item_id, _ = _item_record(entry, f"inventory[{index}]")
        if item_id in inventory_ids:
            raise SaveError("Save inválido: item duplicado no inventário.")
        inventory_ids.add(item_id)

    equipment = _object(data.get("equipment"), "equipment")
    if set(equipment) != set(SLOTS):
        raise SaveError("Save inválido: espaços de equipamento incompletos.")
    for slot in SLOTS:
        item_id = equipment[slot]
        if item_id is not None and (type(item_id) is not str or item_id not in EQUIPMENT
                                    or EQUIPMENT[item_id]["slot"] != slot or item_id not in inventory_ids):
            raise SaveError(f"Save inválido: equipamento de {slot}.")

    quest_data = _object(data.get("quests"), "quests")
    definitions = QuestManager().quests
    if set(quest_data) != set(definitions):
        raise SaveError("Save inválido: quests incompletas.")
    for quest_id, definition in definitions.items():
        entry = _object(quest_data[quest_id], quest_id)
        if entry.get("id") != quest_id or entry.get("state") not in {AVAILABLE, ACTIVE, COMPLETED, REWARDED}:
            raise SaveError(f"Save inválido: estado da quest {quest_id}.")
        progress = _integer(entry.get("progress"), quest_id + ".progress", 0, definition.required)
        rewarded = _boolean(entry.get("rewarded"), quest_id + ".rewarded")
        state = entry["state"]
        if rewarded != (state == REWARDED) or (state == AVAILABLE and progress != 0) or (state in {COMPLETED, REWARDED} and progress != definition.required):
            raise SaveError(f"Save inválido: progresso da quest {quest_id}.")

    world = _object(data.get("world"), "world")
    started = _boolean(world.get("forest_event_started"), "forest_event_started")
    defeated = _boolean(world.get("forest_boss_defeated"), "forest_boss_defeated")
    loot_given = _boolean(world.get("boss_loot_given"), "boss_loot_given")
    passage = _boolean(world.get("north_passage_open"), "north_passage_open")
    if defeated and not started or loot_given != defeated or passage != defeated:
        raise SaveError("Save inválido: evento do Guardião inconsistente.")
    if started and quest_data["forest_trouble"]["state"] != REWARDED:
        raise SaveError("Save inválido: Guardião ativado antes da quest.")
    if region_id == "desert" and not defeated:
        raise SaveError("Save inválido: passagem para o deserto bloqueada.")
    if loot_given and "grove_charm" not in inventory_ids:
        raise SaveError("Save inválido: recompensa do Guardião ausente.")
    chests = world.get("opened_desert_chests")
    if not isinstance(chests, list) or len(chests) != len(set(chests)) or any(type(chest) is not str or chest not in CHESTS for chest in chests):
        raise SaveError("Save inválido: baús abertos.")

    drops = data.get("drops")
    if not isinstance(drops, list) or len(drops) > 1000:
        raise SaveError("Save inválido: drops.")
    for index, entry in enumerate(drops):
        drop = _object(entry, f"drops[{index}]")
        _item_record(drop, f"drops[{index}]", equipment_allowed=False)
        _position(drop.get("position"), f"drops[{index}].position")
        _integer(drop.get("lifetime"), f"drops[{index}].lifetime", 1, 60 * 90)
    return data


def snapshot(player, inventory, quests, region_id, opened_chests, drops):
    data = {
        "save_version": SAVE_VERSION,
        "region": region_id,
        "player": {
            "level": player.level, "current_xp": player.current_xp,
            "xp_to_next_level": player.xp_to_next_level, "stat_points": player.stat_points,
            "stats": dict(player.stats), "hp": player.hp, "sp": player.sp,
            "position": [player.x, player.y],
        },
        "inventory": [{"id": entry["id"], "amount": entry.get("amount", 1)} for entry in inventory],
        "equipment": {slot: equipped["id"] if equipped else None for slot, equipped in player.equipment.items()},
        "quests": {quest_id: {"id": quest_id, "state": quest.state, "progress": quest.progress,
                               "rewarded": quest.state == REWARDED} for quest_id, quest in quests.quests.items()},
        "world": {
            "forest_event_started": quests.forest_event_started,
            "forest_boss_defeated": quests.forest_boss_defeated,
            "boss_loot_given": quests.boss_loot_given,
            "north_passage_open": quests.forest_boss_defeated,
            "opened_desert_chests": sorted(opened_chests),
        },
        "drops": [{"id": drop.item["id"], "amount": drop.item.get("amount", 1),
                   "position": [drop.x, drop.y], "lifetime": drop.lifetime} for drop in drops],
    }
    return validate(data)


def save_game(player, inventory, quests, region_id, opened_chests, drops, path=None):
    data = snapshot(player, inventory, quests, region_id, opened_chests, drops)
    path = Path(path or SAVE_PATH)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=".savegame-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise SaveError(f"Não foi possível salvar: {exc}") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_save(path=SAVE_PATH):
    try:
        content = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise MissingSaveError("Nenhum save encontrado.") from exc
    except (OSError, UnicodeError) as exc:
        raise SaveError("Não foi possível ler o save.") from exc
    try:
        return validate(json.loads(content))
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        raise SaveError("Save corrompido: JSON inválido.") from exc


def prepare_region(region_id, quests, opened_chests, build_region, spawn_enemies, guardian_factory):
    region = build_region(region_id, opened_chests)
    enemies = spawn_enemies(region)
    if region_id == "forest":
        region["north_locked"] = not quests.forest_boss_defeated
        if quests.forest_event_started and not quests.forest_boss_defeated:
            region["arena_locked"] = True
            region["obstacles"].append(region["exits"]["desert"].inflate(30, 20))
            enemies = [guardian_factory()]
    return region, enemies


def _safe_position(saved_position, region_id, region, enemies):
    width, height = region["terrain"].get_size()

    def free(position):
        x, y = position
        if not 18 <= x <= width - 18 or not 38 <= y <= height - 12:
            return False
        hitbox = pygame.Rect(round(x - 13), round(y - 9), 26, 18)
        return not (any(hitbox.colliderect(obstacle) for obstacle in region["obstacles"])
                    or any(hitbox.colliderect(exit_rect.inflate(36, 36)) for exit_rect in region["exits"].values())
                    or any(hitbox.colliderect(enemy.hitbox.inflate(36, 36)) for enemy in enemies))

    for position in (saved_position, *SAFE_SPAWNS[region_id]):
        if free(position):
            return position
    raise SaveError("Não há um ponto seguro para carregar nesta região.")


def load_game(path, player_factory, build_region, spawn_enemies, guardian_factory):
    data = read_save(path)
    character = data["player"]
    inventory = [consumable(entry["id"], entry["amount"]) if entry["id"] in CONSUMABLES
                 else equipment_item(entry["id"]) for entry in data["inventory"]]
    by_id = {entry["id"]: entry for entry in inventory}

    player = player_factory()
    player.stats = dict(character["stats"])
    player.level = character["level"]
    player.current_xp = character["current_xp"]
    player.xp_to_next_level = character["xp_to_next_level"]
    player.stat_points = character["stat_points"]
    player.equipment = {slot: by_id.get(item_id) for slot, item_id in data["equipment"].items()}
    player.recalculate_stats()
    if character["hp"] > player.max_hp or character["sp"] > player.max_sp:
        raise SaveError("Save inválido: HP ou SP excede o máximo calculado.")
    player.hp, player.sp = character["hp"], character["sp"]
    player.attack_timer = 0
    player.invulnerability_timer = 30

    quests = QuestManager()
    for quest_id, entry in data["quests"].items():
        quests.quests[quest_id].state = entry["state"]
        quests.quests[quest_id].progress = entry["progress"]
    world = data["world"]
    quests.forest_event_started = world["forest_event_started"]
    quests.forest_boss_defeated = world["forest_boss_defeated"]
    quests.boss_loot_given = world["boss_loot_given"]
    opened_chests = set(world["opened_desert_chests"])
    region_id = data["region"]
    region, enemies = prepare_region(region_id, quests, opened_chests, build_region,
                                     spawn_enemies, guardian_factory)
    player.x, player.y = _safe_position(tuple(character["position"]), region_id, region, enemies)
    drops = [Drop(consumable(entry["id"], entry["amount"]), *entry["position"], entry["lifetime"])
             for entry in data["drops"]]
    return LoadedGame(player, inventory, quests, region_id, region, enemies, drops, opened_chests)
