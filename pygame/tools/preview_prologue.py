"""Repeatable visual rehearsal of the real game loop; never touches the user save.

Run: python tools/preview_prologue.py --output tools/visual_checks/before
No cutscene skip: captures opening, interactions, arrival beats and free gameplay.
"""
import argparse
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
import main
import save_manager
from ui.game_renderer import GameRenderer


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    state = {"frame": 0, "view": None, "stage": 0, "keys": set()}
    captured = set()
    original_draw = GameRenderer.draw
    targets = [(300, 260), (690, 313), (512, 470)]

    class Clock:
        def tick(self, fps):
            return 17

    class Keys:
        def __getitem__(self, key):
            return key in state["keys"]

    def events():
        state["frame"] += 1
        state["keys"] = set()
        view = state["view"]
        if state["frame"] > 8500:
            raise RuntimeError(f"Rehearsal stalled: stage {state['stage']}")
        if view is None or view["narrative"] is not None:
            return []
        dialogue = view["dialogue"]
        if dialogue.active:
            return ([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)]
                    if state["frame"] % 30 == 0 else [])
        if view["region"]["name"] == "Casa" and state["stage"] < 3:
            player = view["player"]
            x, y = targets[state["stage"]]
            dx, dy = x - player.x, y - player.y
            if abs(dx) < 5 and abs(dy) < 5:
                state["stage"] += 1
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)]
            if abs(dx) > 4:
                state["keys"].add(pygame.K_d if dx > 0 else pygame.K_a)
            if abs(dy) > 4:
                state["keys"].add(pygame.K_s if dy > 0 else pygame.K_w)
        if (view["region"]["name"] == "Vila do Vale"
                and view["arrival_scene"] is None
                and view["quest_manager"].get("forest_trouble").state == "ACTIVE"):
            return [pygame.event.Event(pygame.QUIT)]
        return []

    def draw(renderer, canvas, **view):
        state["view"] = view
        original_draw(renderer, canvas, **view)
        narrative = view["narrative"]
        scene = view["arrival_scene"]
        if narrative is not None:
            name = "opening" if state["frame"] == 60 else None
        elif scene is not None:
            name = "arrival_" + scene.phase
            if scene.phase == "dialogue":
                name += f"_{view['dialogue'].index:02d}"
            if scene.elapsed_ms < 100 and scene.phase not in ("flash_near", "flash_gone", "dialogue"):
                name = None
        elif view["dialogue"].active:
            name = "home_" + view["dialogue"].npc.uid
        elif view["region"]["name"] == "Casa":
            name = "home"
        else:
            name = "village_free" if view["quest_manager"].get("forest_trouble").state == "ACTIVE" else None
        if name and name not in captured:
            pygame.image.save(canvas, output / (name + ".png"))
            captured.add(name)

    with tempfile.TemporaryDirectory(dir=ROOT / "tools") as directory:
        with patch.object(save_manager, "SAVE_PATH", Path(directory) / "save.json"), \
             patch("core.game.pygame.time.Clock", Clock), \
             patch.object(pygame.event, "get", events), \
             patch.object(pygame.key, "get_pressed", return_value=Keys()), \
             patch.object(GameRenderer, "draw", draw):
            main.main()
    print(f"Rehearsal complete: {state['frame']} frames, captures: {sorted(captured)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "tools/visual_checks/current")
    run(parser.parse_args().output.resolve())
