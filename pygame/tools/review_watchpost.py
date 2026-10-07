"""Render the 1C investigation and complete memory, using the real game renderer."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
from pathlib import Path
import sys
import json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from PIL import Image, ImageDraw
from core.assets import load
from core.camera import camera_for
from core.debug_checkpoints import create_checkpoint
from story.arrival_scene import restore_resident
from story.prologue import opening_sequence
from story import watchpost as post
from systems.dialogue import DialogueBox
from ui.game_renderer import GameRenderer
from ui.world_renderer import draw_world
from world.world_manager import WorldManager


def run():
    pygame.init(); pygame.display.set_mode((1,1))
    out=ROOT/"tools/visual_checks/watchpost"; out.mkdir(parents=True,exist_ok=True)
    world=WorldManager.for_game(load)
    p=create_checkpoint("prologue_2e",load=load,build_region=world.build_region,
        spawn_enemies=world.spawn_enemies,restore_resident=restore_resident,opening_sequence=opening_sequence)
    for flag in ("red_officer_met","red_officer_boss_ready","red_officer_defeated",
                 "red_officer_memory_seen","red_officer_escaped","prologue_completed",
                 "chapter1_started","chapter1_returned","chapter1_alden_talk","old_road_unlocked",
                 "old_road_entered","road_red_clue_found","road_memory_seen","road_camp_found",
                 "watchpost_seen","watchpost_entered"):
        p.story.set(flag)
    region=world.build_region("watchpost"); p.story.apply_to_region(region)
    enemies=world.spawn_enemies(region)
    p.quests.notice=""; p.quests.notice_timer=0
    renderer,dialogue=GameRenderer(),DialogueBox()
    font,title=pygame.font.Font(None,22),pygame.font.Font(None,30)
    canvas=pygame.Surface((1024,576))
    def draw(scene=None,foes=()):
        renderer.draw(canvas,region=region,player=p.player,enemies=list(foes),drops=[],
            camera=camera_for(p.player,region["terrain"].get_size()),debug=False,
            damage_numbers=[],hitstop_frames=0,font=font,title_font=title,dialogue=dialogue,
            quest_manager=p.quests,ui_mode=None,inventory=p.inventory,inventory_ui={},
            game_over_screen=None,story=p.story,watchpost_scene=scene)
        return Image.frombytes("RGB",canvas.get_size(),pygame.image.tobytes(canvas,"RGB"))
    def examine(uid):
        target=next(o for o in region["interactables"] if o.uid==uid)
        post.complete_evidence(target,p.player,p.inventory,p.story,region,p.quests)
    full=pygame.Surface(region["terrain"].get_size())
    draw_world(full,region,font,(0,0),None,enemies,[],show_controls=False,story_context=p.story)
    pygame.image.save(full,out/"map_full.png")
    overview=Image.open(out/"map_full.png").resize((768,512),Image.Resampling.NEAREST)
    labels=ImageDraw.Draw(overview)
    for text,point in (("ESTRADA",(350,466)),("PORTAO",(350,389)),("PASSAGEM",(608,365)),
                       ("ALOJAMENTO",(239,186)),("DEPOSITO",(480,255)),
                       ("COMANDO",(420,102)),("TORRE",(249,85)),("PORTA LATERAL",(598,165))):
        box=labels.textbbox(point,text)
        labels.rectangle((box[0]-4,box[1]-3,box[2]+4,box[3]+3),fill="#172127")
        labels.text(point,text,fill="#ead8b0")
    overview.save(out/"map_overview.png")
    p.player.x,p.player.y=768,865; p.player.facing=3
    draw(foes=enemies).save(out/"exterior.png")
    p.player.x,p.player.y=1240,703; p.player.facing=1
    draw(foes=enemies).save(out/"breach.png")
    examine("post_breach")
    p.player.x,p.player.y=820,661
    draw(foes=enemies).save(out/"courtyard.png")
    for name,pos,uid in (("lodging",(650,518),"post_archive"),
                         ("dispatch",(996,594),"post_dispatch"),
                         ("roster",(974,359),"post_roster")):
        p.player.x,p.player.y=pos; p.player.facing=3
        draw().save(out/(name+".png"))
        if name in {"dispatch","roster"}:
            target=next(o for o in region["interactables"] if o.uid==uid)
            dialogue.open(target,p.quests)
            if name=="dispatch": dialogue.index=1
            draw().save(out/(name+"_document.png")); dialogue.npc=None
        examine(uid)
    p.player.x,p.player.y=650,485; examine("post_token")
    p.quests.notice_timer=0
    scene=post.PostMomentScene("memory",p.player,region,load)
    frames=[draw(scene)]; elapsed=0
    while scene.active:
        scene.update(50,p.story,p.quests); elapsed+=50
        im=draw(scene if scene.active else None)
        frames.append(im)
        if elapsed in (1100,2550,4050,5950): im.save(out/f"memory_{elapsed}.png")
    frames.extend([frames[-1]]*10)
    indexed=[im.convert("P",palette=Image.Palette.ADAPTIVE,colors=128) for im in frames]
    indexed[0].save(out/"memory.gif",save_all=True,append_images=indexed[1:],duration=50,loop=0,optimize=True)
    p.player.x,p.player.y=970,452
    scene=post.PostMomentScene("presence",p.player,region,load)
    scene.update(700,p.story,p.quests)
    draw(scene).save(out/"presence.png")
    scene.finish(p.story,p.quests)
    p.player.x,p.player.y=1230,329; p.player.facing=2; examine("post_trail")
    draw().save(out/"departure.png")
    token=next(i for i in p.inventory if i["id"]=="escort_token")
    renderer.draw(canvas,region=region,player=p.player,enemies=[],drops=[],
        camera=camera_for(p.player,region["terrain"].get_size()),debug=False,
        damage_numbers=[],hitstop_frames=0,font=font,title_font=title,dialogue=dialogue,
        quest_manager=p.quests,ui_mode="inventory",inventory=p.inventory,
        inventory_ui={"tab":"TODOS","selected":token,"consumable_cooldown":0},
        game_over_screen=None,story=p.story)
    pygame.image.save(canvas,out/"personal_item.png")
    board=Image.new("RGB",(1024,924),"#111a20"); labels=ImageDraw.Draw(board)
    for i,(name,label) in enumerate((("exterior","Exterior / portao"),("courtyard","Patio"),
            ("lodging","Alojamento"),("roster_document","Registro R-17"),
            ("memory_4050","Fragmento de memoria"),("departure","Saida / novo objetivo"))):
        x,y=i%2*512,i//2*308
        board.paste(Image.open(out/(name+".png")).resize((512,288),Image.Resampling.NEAREST),(x,y))
        labels.text((x+12,y+290),label,fill="#ead8b0")
    board.save(out/"storyboard.png")
    report={"region":region["name"],"rooms":list(region["rooms"]),"enemies":region["enemy_spawns"],
            "memory_ms":6950,"objective":p.story.objective_text,"item":"escort_token",
            "flags":{f:p.story.get(f) for f in post.POST_FLAGS},"encounter_1d":False}
    (out/"validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False)); pygame.quit()


if __name__=="__main__": run()
