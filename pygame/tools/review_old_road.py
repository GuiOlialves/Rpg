"""Focused Chapter 1B map and cinematic previews; never writes a game save."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from PIL import Image, ImageDraw
from core.assets import load
from core.camera import camera_for
from core.debug_checkpoints import create_checkpoint
from story.arrival_scene import restore_resident
from story.prologue import opening_sequence
from story.old_road import RoadMomentScene
from systems.dialogue import DialogueBox
from ui.game_renderer import GameRenderer
from ui.world_renderer import draw_world
from world.world_manager import WorldManager


def run():
    pygame.init(); pygame.display.set_mode((1,1))
    out = ROOT/"tools/visual_checks/old_road"
    out.mkdir(parents=True,exist_ok=True)
    world = WorldManager.for_game(load)
    p = create_checkpoint("prologue_2e",load=load,build_region=world.build_region,
        spawn_enemies=world.spawn_enemies,restore_resident=restore_resident,opening_sequence=opening_sequence)
    for flag in ("red_officer_met","red_officer_boss_ready","red_officer_defeated",
                 "red_officer_memory_seen","red_officer_escaped","prologue_completed",
                 "chapter1_started","chapter1_returned","chapter1_alden_talk","old_road_unlocked",
                 "old_road_entered"):
        p.story.set(flag)
    region = world.build_region("old_road")
    p.quests.notice = ""
    p.quests.notice_timer = 0
    p.story.apply_to_region(region)
    enemies = world.spawn_enemies(region)
    renderer, dialogue = GameRenderer(), DialogueBox()
    font,title_font = pygame.font.Font(None,22),pygame.font.Font(None,30)
    canvas = pygame.Surface((1024,576))

    def draw(scene=None,foes=None):
        renderer.draw(canvas,region=region,player=p.player,enemies=enemies if foes is None else foes,
            drops=[],camera=camera_for(p.player,region["terrain"].get_size()),debug=False,
            damage_numbers=[],hitstop_frames=0,font=font,title_font=title_font,dialogue=dialogue,
            quest_manager=p.quests,ui_mode=None,inventory=p.inventory,inventory_ui={},
            game_over_screen=None,story=p.story,old_road_scene=scene)
        return Image.frombytes("RGB",canvas.get_size(),pygame.image.tobytes(canvas,"RGB"))

    full = pygame.Surface(region["terrain"].get_size())
    draw_world(full,region,font,(0,0),None,enemies,[],show_controls=False,story_context=p.story)
    Image.frombytes("RGB",full.get_size(),pygame.image.tobytes(full,"RGB")).save(out/"map_full.png")
    overview = Image.open(out/"map_full.png").resize((1024,576),Image.Resampling.NEAREST)
    labels = ImageDraw.Draw(overview)
    for text,point in (("VALE",(970,435)),("CARROCA",(710,325)),
                       ("ABRIGO",(350,405)),("ACAMPAMENTO",(570,175)),
                       ("POSTO NORTE",(375,50)),("DESVIO",(840,525)),("CARAVANA",(610,505))):
        box = labels.textbbox(point,text)
        labels.rectangle((box[0]-5,box[1]-4,box[2]+5,box[3]+4),fill="#172127")
        labels.text(point,text,fill="#ead8b0")
    overview.save(out/"map_overview.png")
    for name,point,facing in (("approach",(1820,850),1),("wreck",(1440,710),1),
                               ("shelter",(752,828),3),("camp",(1175,350),3)):
        p.player.x,p.player.y = point; p.player.facing = facing
        draw().save(out/(name+".png"))

    p.player.x,p.player.y = 850,560
    scene = RoadMomentScene("memory",p.player,region)
    frames = [draw(scene,[])]
    elapsed = 0
    while scene.active:
        scene.update(50,p.story,p.quests); elapsed += 50
        im = draw(scene if scene.active else None,[])
        frames.append(im)
        if elapsed==600: im.save(out/"memory.png")
    frames.extend([frames[-1]]*10)
    frames = [im.convert("P",palette=Image.Palette.ADAPTIVE,colors=128) for im in frames]
    frames[0].save(out/"memory.gif",save_all=True,append_images=frames[1:],duration=50,loop=0,optimize=True)
    for flag in ("road_red_clue_found","road_blue_trace_found","road_camp_found"):
        p.story.set(flag)
    p.story.apply_to_region(region)
    p.player.x,p.player.y = 925,347
    scene = RoadMomentScene("post",p.player,region)
    scene.update(850,p.story,p.quests)
    draw(scene,[]).save(out/"watchpost_reveal.png")
    scene.finish(p.story,p.quests)
    draw(None,[]).save(out/"watchpost_objective.png")
    plate = Image.new("RGB",(1024,616),"#111a20")
    labels = ImageDraw.Draw(plate)
    for i,name in enumerate(("approach","wreck","camp","watchpost_reveal")):
        x,y = i%2*512,i//2*308
        plate.paste(Image.open(out/(name+".png")).resize((512,288),Image.Resampling.NEAREST),(x,y))
        labels.text((x+12,y+290),name.replace("_"," "),fill="#ead8b0")
    plate.save(out/"storyboard.png")
    report = {"region":region["name"],"encounters":region["enemy_spawns"],
              "optional_points":region["optional_points"],"obstacles":len(region["obstacles"]),
              "memory_ms":1960,"objective":p.story.objective_text,"watchpost_interior":False}
    (out/"validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    pygame.quit()


if __name__=="__main__": run()
