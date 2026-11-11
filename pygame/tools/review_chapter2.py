"""Capture the production renderer, complete echoes, creature actions and chapter boundary."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import sys,time,json
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from PIL import Image,ImageDraw
from tests.test_chapter2 import Chapter2Tests
from core.camera import camera_for
from core.config import VIEW
from ui.game_renderer import GameRenderer
from ui.world_renderer import draw_world
from story.resonance import ResonanceScene,BY_ID
from story import chapter2
from entities.encosta_creature import EncostaCreature
import main as game

OUT=Path(__file__).resolve().parent/'visual_checks/chapter2'


def main():
    OUT.mkdir(parents=True,exist_ok=True); f=Chapter2Tests(); f.setUp(); p=f.p
    renderer=GameRenderer(); canvas=pygame.Surface(VIEW); panels=[]; timings={}
    font,title=pygame.font.Font(None,22),pygame.font.Font(None,30)
    enemies=[]
    def draw(name=None,scene=None,capture=True):
        renderer.draw(canvas,region=p.region,player=p.player,enemies=enemies,drops=[],
            camera=camera_for(p.player,p.region['terrain'].get_size()),debug=False,damage_numbers=[],
            hitstop_frames=0,font=font,title_font=title,dialogue=f.dialogue,quest_manager=p.quests,
            ui_mode=None,inventory=p.inventory,inventory_ui={},game_over_screen=None,story=p.story,chapter2_scene=scene)
        if not capture: return
        image=Image.frombytes('RGB',VIEW,pygame.image.tobytes(canvas,'RGB'))
        if name: image.save(OUT/(name+'.png'));panels.append((name,image.copy()))
        return image
    def sequence(scene,name,sample):
        frames=[]
        for i in range(120):
            if not scene.active: break
            scene.update(100); im=draw(scene=scene if scene.active else None)
            frames.append(im.resize((768,432),Image.Resampling.NEAREST))
            if i==sample: im.save(OUT/(name+'.png')); panels.append((name,im.copy()))
        frames[0].save(OUT/(name+'.gif'),save_all=True,append_images=frames[1:],duration=100,loop=0)
    def map_image(kind):
        full=pygame.Surface(p.region['terrain'].get_size())
        draw_world(full,p.region,font,(0,0),p.player,enemies,[],show_controls=False,show_banner=False,story_context=p.story)
        pygame.image.save(full,OUT/(kind+'_map.png'))
    try:
        scene=f.scene('departure'); draw('departure',scene); scene.finish(); sequence(scene,'chapter2_title',20)
        for kind,flag in (('forgotten_route','route_entered'),('encosta','encosta_entered'),('threshold','threshold_entered')):
            if kind=='threshold': continue
            start=time.perf_counter(); f.enter(kind,flag); timings[kind+'_build_ms']=round((time.perf_counter()-start)*1000,2)
            enemies=f.world.spawn_enemies(p.region); map_image(kind)
            if kind=='forgotten_route':
                p.player.x,p.player.y=900,760; draw('bridge')
                p.player.x,p.player.y=1290,345; draw('optional_ford')
                p.player.x,p.player.y=1390,220; f.target('route_record').begin_interaction(f.dialogue,p.player,p.quests)
                draw('hidden_note'); f.dialogue.npc=None
                # Show all states at actual gameplay scale beside the unchanged hero.
                sheet=Image.new('RGB',(960,480),(61,75,64)); d=ImageDraw.Draw(sheet)
                for row,kind2 in enumerate(('reed_stalker','slateback','slate_warden')):
                    actor=EncostaCreature(kind2,(100,100),game.load)
                    for col,action in enumerate(('idle','walk','windup','attack','hurt','death')):
                        im=actor.frames[action][0][min(3,len(actor.frames[action][0])-1)]
                        tile=Image.frombytes('RGBA',im.get_size(),pygame.image.tobytes(im,'RGBA'))
                        sheet.paste(tile,(col*160,row*150+50),tile); d.text((col*160+12,row*150+20),kind2+' / '+action,fill=(228,220,181))
                sheet.save(OUT/'creatures.png')
                for kind2 in ('reed_stalker','slateback','slate_warden'):
                    p.player.x,p.player.y=620,770; actor=EncostaCreature(kind2,(620,820),game.load); enemies=[actor]
                    p.player.hp=p.player.max_hp
                    if kind2=='slate_warden': actor.strikes=1
                    actor._begin_attack(p.player); frames=[]
                    for i in range(actor.windup_frames+actor.config['active']+actor.config['recovery']+(12 if actor.attack_action=='charged' else 0)):
                        p.player.update(defaultdict(bool),p.region['obstacles'])
                        actor.update(p.player,p.region['obstacles']); frames.append(draw().resize((768,432),Image.Resampling.NEAREST))
                    frames[0].save(OUT/(kind2+'_attack.gif'),save_all=True,append_images=frames[1:],duration=17,loop=0)
                enemies=[]; p.player.hp=p.player.max_hp
                p.player.hurt_visual_timer=p.player.invulnerability_timer=0
            else:
                p.player.x,p.player.y=780,710; f.target('ines').begin_interaction(f.dialogue,p.player,p.quests)
                draw('ines'); f.dialogue.npc=None
                p.player.x,p.player.y=1370,655; f.target('breno').begin_interaction(f.dialogue,p.player,p.quests);f.dialogue.index=2
                draw('breno');f.dialogue.npc=None
                for uid in ('ines','breno','encosta_register','encosta_locket','encosta_symbol'): f.examine(uid)
                for uid in ('echo_meal','echo_departure','echo_orders'):
                    point=BY_ID[uid];p.player.x,p.player.y=point.position[0],point.position[1]+35
                    sequence(ResonanceScene(point,p.player,p.story),uid,15);p.story.apply_to_region(p.region)
                p.player.x,p.player.y=1060,600;draw('cabinet_puzzle');f.solve()
                p.player.x,p.player.y=780,710;scene=f.scene('choice');draw('custody_choice',scene);scene.choose(0)
                p.story.apply_to_region(p.region);f.examine('custody_plan')
        start=time.perf_counter();f.enter('threshold','threshold_entered',(1150,635));timings['threshold_build_ms']=round((time.perf_counter()-start)*1000,2)
        enemies=f.world.spawn_enemies(p.region);map_image('threshold');sequence(f.scene('vista'),'chamber_vista',20)
        p.player.x,p.player.y=1070,815;f.target('recent_camp').begin_interaction(f.dialogue,p.player,p.quests);draw('recent_activity');f.dialogue.npc=None
        chapter2.record_defeats(p.story,[('threshold',1)],p.region,p.quests); enemies=[]
        p.player.x,p.player.y=1450,665;sequence(ResonanceScene(BY_ID['echo_threshold'],p.player,p.story),'echo_threshold',20)
        sequence(f.scene('part_a_end'),'part_a_end',20);p.story.apply_to_region(p.region);draw('control_restored')
        # Measure cached frames with no disk reads or region construction during gameplay.
        start=time.perf_counter()
        for _ in range(180): draw(capture=False)
        timings['renderer_cached_ms_per_frame']=round((time.perf_counter()-start)*1000/180,2)
        (OUT/'review.json').write_text(json.dumps({'timings':timings,'flags':{flag:p.story.get(flag) for flag in chapter2.ALL_FLAGS},
            'objective':p.story.objective_text},ensure_ascii=False,indent=2),encoding='utf-8')
    finally:f.tearDown()
    board=Image.new('RGB',(1024,310*((len(panels)+1)//2)),(18,25,27));d=ImageDraw.Draw(board)
    for i,(name,im) in enumerate(panels):
        x,y=i%2*512,i//2*310;board.paste(im.resize((512,288),Image.Resampling.NEAREST),(x,y+22));d.text((x+10,y+5),name,fill=(225,212,176))
    board.save(OUT/'storyboard.png');print(OUT/'storyboard.png');print(timings)


if __name__=='__main__':main()
