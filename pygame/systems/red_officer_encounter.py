"""Runtime-only boss lifecycle; story stores only the non-lethal outcome."""
from entities.red_officer import RedOfficer


def start(region, story, load):
    if (region.get("ambient_kind") != "forest" or not story.get("red_officer_boss_ready")
            or story.get("red_officer_defeated") or region.get("boss_battle_active")):
        return None
    actor = region.get("red_officer_actor")
    position = (actor.x, actor.y) if actor is not None else (1348, 516)
    boss = RedOfficer(position, load, defeat_hp=1)
    if actor in region.get("scenery", []):
        region["scenery"].remove(actor)
    region["red_officer_actor"] = boss
    region["boss_battle_active"] = True
    return boss


def conclude(region, story, enemies):
    boss = next((e for e in enemies if e.kind == "red_officer" and e.state == "DEFEATED"), None)
    if boss is None:
        return False
    region["boss_battle_active"] = False
    story.set("red_officer_defeated")
    if boss not in region.setdefault("scenery", []):
        region["scenery"].append(boss)
    enemies.remove(boss)
    return True


def stop(region, enemies):
    region["boss_battle_active"] = False
    for boss in enemies:
        if boss.kind == "red_officer":
            boss.hostile = boss.boss_battle_active = False
            boss.attack_zone = None
