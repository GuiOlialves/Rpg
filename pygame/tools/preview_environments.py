"""Local environment previews and a small collision/transition walking smoke.

No saves, combat simulation or gameplay test suite. Uses existing world rendering.
"""
import argparse
from collections import deque
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
from core.assets import load
from entities.player import Player
from ui.world_renderer import draw_world
from world.world_manager import WorldManager


def run(output):
    pygame.init()
    pygame.display.set_mode((1, 1))
    output.mkdir(parents=True, exist_ok=True)
    font = pygame.font.Font(None, 22)
    world = WorldManager.for_game(load)
    regions = {name: world.build_region(name) for name in ("home", "village", "forest")}
    player = Player(load("assets/player/f_player_sheet.png"), load("assets/player/f_player_attack_sheet.png"))
    for name, region in regions.items():
        preview = dict(region)
        preview["objects"] = list(region["objects"])
        preview["interactables"] = list(region.get("interactables", []))
        if name == "home":
            preview["interactables"] += region["investigation_interactables"]
        if name == "forest":
            preview["objects"] += region["forest_battlefield_objects"] + [region["wounded_commander_object"]]
            preview["interactables"] += list(region["forest_battlefield_interactables"].values())
        player.x, player.y = {"home": (512,288), "village": (1020,565), "forest": (1300,560)}[name]
        canvas = pygame.Surface(region["terrain"].get_size())
        draw_world(canvas, preview, font, (0,0), player=player,
                   show_controls=False, show_banner=False)
        pygame.image.save(canvas, output / f"{name}_full.png")
        pygame.image.save(pygame.transform.scale(canvas, (1024,576)), output / f"{name}.png")
        shots = {"home": [("interior",(0,0))],
                 "village": [("praca",(540,240)),("casas",(150,380)),("comercio",(1024,470))],
                 "forest": [("entrada",(0,240)),("lago",(1024,0)),("clareiras",(550,560))]}[name]
        for label, camera in shots:
            shot = pygame.Surface((1024,576))
            draw_world(shot, preview, font, camera, player=player,
                       show_controls=False, show_banner=False)
            pygame.image.save(shot,output / f"{name}_{label}.png")
            draw_world(shot, preview, font, camera, player=player, debug=True,
                       show_controls=False, show_banner=False)
            pygame.image.save(shot,output / f"{name}_{label}_debug.png")

    report = {}
    for name, region in regions.items():
        start = {"home":(512,288), "village":(544,496), "forest":(120,576)}[name]
        width,height = region["terrain"].get_size()
        def clear(p):
            x,y=p
            box=pygame.Rect(x-13,y-9,26,18)
            return (box.left>=0 and box.top>=0 and box.right<=width and box.bottom<=height
                    and not any(box.colliderect(r) for r in region["obstacles"]))
        assert clear(start), (name,"blocked start",start)
        parents={start:None}; queue=deque([start])
        while queue:
            x,y=queue.popleft()
            for nxt in ((x+8,y),(x-8,y),(x,y+8),(x,y-8)):
                if nxt not in parents and clear(nxt):
                    parents[nxt]=(x,y);queue.append(nxt)
        targets=[(f"spawn_{source}",pygame.Rect(x-5,y-5,10,10))
                 for source,(x,y) in region["spawn"].items()]
        targets += [(f"exit_{dest}",rect) for dest,rect in region["exits"].items()]
        actors=list(region.get("interactables", []))+list(region.get("investigation_interactables",[]))+region.get("npcs",[])
        if name=="forest":
            actors+=list(region["forest_battlefield_interactables"].values())
            targets += [("commander",pygame.Rect(1420,490,80,70))]
            for i,group in enumerate(region["red_encounter_groups"]):
                for j,(x,y) in enumerate(group):
                    targets.append((f"battle_{i}_{j}",pygame.Rect(x-16,y-16,32,32)))
        targets += [(actor.uid,actor.interaction_rect) for actor in actors]
        reached=[]
        for label, rect in targets:
            candidates=[p for p in parents if pygame.Rect(p[0]-13,p[1]-9,26,18).colliderect(rect)]
            assert candidates,(name,"unreachable",label)
            end=min(candidates,key=lambda p:abs(p[0]-rect.centerx)+abs(p[1]-rect.centery))
            route=[]; node=end
            while parents[node] is not None:
                route.append(node);node=parents[node]
            player.x,player.y=start
            for x,y in reversed(route):
                # Replay with the actual player collision method, <= walk speed.
                while (player.x,player.y)!=(x,y):
                    dx=max(-3,min(3,x-player.x));dy=max(-3,min(3,y-player.y))
                    assert player._move(dx,dy,region["obstacles"]),(name,label,x,y)
            reached.append(label)
        for source,position in region["spawn"].items():
            assert clear(position),(name,"blocked spawn",source)
        report[name]={"reachable":reached,"solid_footprints":len(region["obstacles"])}

    quests=SimpleNamespace(forest_boss_defeated=True)
    def prepare(destination, *_args):
        return world.build_region(destination),[]
    for source,destination in (("home","village"),("village","home"),
                               ("village","forest"),("forest","village"),
                               ("forest","desert"),("desert","forest")):
        transition=world.transition(source,destination,quests,set(),prepare,None)
        assert transition and not transition.blocked and transition.region_id==destination
        player.x,player.y=transition.spawn
        assert not any(player.hitbox.colliderect(box) for box in transition.region["obstacles"])
    report["transitions"]="home/village, village/forest, forest/desert: both directions OK"
    (output/"smoke.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    pygame.quit()


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=ROOT/"tools/visual_checks/environments/after")
    run(parser.parse_args().output.resolve())
