"""A faster wandering swordsman, reusing the current warrior art and combat."""
from entities.enemy import Enemy


class RoadPursuer(Enemy):
    def __init__(self, position, load, seed=0):
        super().__init__("warrior", position, load, seed)
        self.config = dict(self.config, name="Errante da Estrada", max_hp=72, damage=6,
                           speed=2.05, perception=190, cooldown=48, attack_range=78,
                           xp_reward=32)
        self.name = self.config["name"]
        self.max_hp = self.hp = self.config["max_hp"]
        self.damage, self.speed = self.config["damage"], self.config["speed"]
        self.road_attack_count = 0

    def _begin_attack(self, action, player):
        self.road_attack_count += 1
        # Two quick cuts, then a longer, clearly telegraphed committed cut.
        if action == "normal" and self.road_attack_count % 3 == 0:
            action = "charged"
        super()._begin_attack(action, player)


def spawn_road_enemy(kind, position, load, seed=0):
    return (RoadPursuer(position, load, seed) if kind == "road_pursuer"
            else Enemy(kind, position, load, seed))
