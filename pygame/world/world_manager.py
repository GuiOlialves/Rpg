"""Registro e construção uniforme das regiões já existentes."""
from dataclasses import dataclass

from entities.enemy import Enemy
from world.regions import desert, forest, home, village, old_road, watchpost, pursuit


@dataclass
class RegionTransition:
    region_id: str
    region: dict
    enemies: list
    spawn: tuple
    notice: str = ""
    blocked: bool = False


class WorldManager:
    def __init__(self, region_builders, load=None):
        self._region_builders = dict(region_builders)
        self._load = load

    @classmethod
    def for_game(cls, load):
        return cls({
            "home": lambda _opened_chests: home.build(),
            "village": lambda _opened_chests: village.build_playable(load),
            "forest": lambda _opened_chests: forest.build(load),
            "desert": lambda opened_chests: desert.build(load, opened_chests),
            "old_road": lambda opened_chests: old_road.build(load, opened_chests),
            "watchpost": lambda opened_chests: watchpost.build(load, opened_chests),
            "pursuit": lambda opened_chests: pursuit.build(load, opened_chests),
        }, load=load)

    @property
    def region_ids(self):
        return tuple(self._region_builders)

    def build_region(self, region_id, opened_chests=None):
        try:
            builder = self._region_builders[region_id]
        except KeyError as exc:
            raise ValueError(f"Região desconhecida: {region_id}") from exc
        return builder(opened_chests)

    def spawn_enemies(self, region, load=None):
        load = load or self._load
        factory = region.get("enemy_factory", Enemy)
        enemies = [factory(kind, position, load, seed=index)
                   for index, (kind, position) in enumerate(region.get("enemy_spawns", []))]
        if region.get("ambient_kind") == "old_road":
            for index, enemy in enumerate(enemies):
                enemy.road_id = index
        elif region.get("ambient_kind") == "watchpost":
            for index, enemy in enumerate(enemies):
                enemy.watchpost_id = index
        return enemies

    def reset_forest_boss_encounter(self, load=None):
        load = load or self._load
        region = self.build_region("forest")
        region["arena_locked"] = True
        region["north_locked"] = True
        region["obstacles"].append(region["exits"]["desert"].inflate(30, 20))
        boss = Enemy("forest_guardian", (1300, 430), load, seed=77)
        return region, [boss]

    @staticmethod
    def can_transition(source, destination, quest_manager):
        return not (source == "forest" and destination == "desert"
                    and not quest_manager.forest_boss_defeated)

    def transition(self, source, destination, quests, opened_chests,
                   prepare_region, guardian_factory, source_region=None):
        """Resolve an exit and build its destination without owning game state."""
        if not self.can_transition(source, destination, quests):
            return RegionTransition(source, {}, [], (0, 0),
                                    ("Derrote o Guardião da Clareira para seguir ao norte."
                                     if quests.forest_event_started else "O caminho ao norte está bloqueado."), True)
        if destination in {"ruins_future", "namar_future"}:
            region = source_region if source_region is not None else self.build_region(source)
            notice_key = "future_exit_notified" if destination == "ruins_future" else "namar_exit_notified"
            if not region.get(notice_key):
                region[notice_key] = True
                return RegionTransition(source, region, [], (0, 0),
                                        "A trilha termina no barranco. Para Namar, preciso encontrar outro caminho."
                                        if destination == "namar_future" else
                                        "A estrada continua até as ruínas distantes.")
            return RegionTransition(source, region, [], (0, 0))
        if destination not in self._region_builders:
            return None

        region, enemies = prepare_region(
            destination, quests, opened_chests, self.build_region,
            self.spawn_enemies,
            guardian_factory or (lambda: Enemy("forest_guardian", (1300, 430), self._load, seed=77)))
        spawn = region["spawn"].get(source, (1024, 576))
        return RegionTransition(destination, region, enemies, spawn)
