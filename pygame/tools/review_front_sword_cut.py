"""Focused before/after, actual attack timing, masks and a stationary combat hit."""
import os,sys,json
from pathlib import Path
from collections import defaultdict
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
import pygame
from core.assets import load
from entities.player import Player
from entities.enemy import Enemy
from systems.combat import CombatSystem
from systems.quest import QuestManager
from hero_pixel_art import sword_points, PIVOT as HERO_PIVOT
from core.animation import ATTACK_DURATIONS

OUT=ROOT/'tools/visual_checks/front_sword_cut'
ASSETS=ROOT/'assets/vale_characters'


def composite(folder,frame,scale=2):
    sheet=Image.open(folder/'protagonist_attack.png')
    height=sheet.height//4
    body=sheet.crop((frame*32,0,(frame+1)*32,height))
    tile=Image.new('RGBA',(96,96)); tile.paste(body,(32,58-(height-2)))
    sword=Image.open(folder/'protagonist_weapon.png').crop((frame*96,0,(frame+1)*96,96))
    return Image.alpha_composite(tile,sword).resize((96*scale,96*scale),Image.Resampling.NEAREST)


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    board=Image.new('RGB',(1280,470),(30,36,45)); draw=ImageDraw.Draw(board)
    for row,(folder,label) in enumerate(((OUT/'before','ANTES: golpe alto'),(ASSETS,'DEPOIS: corte lateral frontal'))):
        y=35+row*224; draw.text((10,y),label,fill='#e1d5af')
        for frame in range(8):
            tile=composite(folder,frame); x=frame*158-14
            board.paste(tile,(x,y+4),tile)
            draw.text((x+92,y+190),f'{frame} / {ATTACK_DURATIONS[frame]} ticks',fill='#93a3a3')
    board.save(OUT/'before_after.png')
    # Same scale and anchor for each frame: the U-shaped tip path stays below the torso.
    path=Image.new('RGB',(480,384),(30,36,45)); d=ImageDraw.Draw(path)
    tile=composite(ASSETS,3,4); path.paste(tile,(48,0),tile)
    points=[(48+(sword_points(f,0)[2][0]+32)*4,(sword_points(f,0)[2][1]+58-HERO_PIVOT[1])*4) for f in range(1,6)]
    d.line(points,fill='#c57550',width=2)
    for i,(x,y) in enumerate(points,1): d.ellipse((x-3,y-3,x+3,y+3),fill='#edb26b'); d.text((x+5,y+5),str(i),fill='#e1d5af')
    path.save(OUT/'tip_path.png')
    report={'other_directions_unchanged':{}}
    for name,cell in (('attack',32),('weapon',96),('hit',96)):
        old=Image.open(OUT/'before'/f'protagonist_{name}.png')
        new=Image.open(ASSETS/f'protagonist_{name}.png')
        old_height,new_height=old.height//4,new.height//4
        report['other_directions_unchanged'][name]=old.crop((0,old_height,old.width,old.height)).tobytes()==new.crop((0,new_height,new.width,new.height)).tobytes()
    pygame.init(); pygame.display.set_mode((1,1)); font=pygame.font.Font(None,20)
    actors=[]
    for facing in range(4):
        p=Player(load('assets/player/f_player_sheet.png'),load('assets/player/f_player_attack_sheet.png'))
        p.x,p.y,p.facing=500,500,facing; actors.append(p)
    frames=[]
    for tick in range(144):
        canvas=pygame.Surface((960,260)); canvas.fill((30,36,45))
        with patch.object(pygame.time,'get_ticks',return_value=tick*1000//60):
            for facing,p in enumerate(actors):
                if p.attack_timer==0 and p.attack_cooldown_timer==0: p.attack()
                p.update(defaultdict(bool),[])
                x=120+facing*240
                pygame.draw.line(canvas,(65,77,80),(x-80,172),(x+80,172))
                p.draw(canvas,(500-x,328))
                canvas.blit(font.render(('Sul','Oeste','Leste','Norte')[facing],False,(225,213,175)),(x-25,15))
                canvas.blit(font.render(f'frame {p.attack_frame} - '+('contato' if p.attack_active else 'preparo/retorno'),False,(147,163,163)),(x-90,224))
        frames.append(Image.frombytes('RGB',canvas.get_size(),pygame.image.tobytes(canvas,'RGB')))
    frames[0].save(OUT/'attack.gif',save_all=True,append_images=frames[1:],duration=[10,20,20]*48,loop=0,disposal=2)
    closeups=[im.crop((40,94,200,222)).resize((320,256),Image.Resampling.NEAREST) for im in frames]
    closeups[0].save(OUT/'front_cut.gif',save_all=True,append_images=closeups[1:],duration=[10,20,20]*48,loop=0,disposal=2)
    p=actors[0]; p.x=p.y=500; p.attack_timer=p.attack_cooldown_timer=0; p.crit_chance=0
    target=Enemy('red_soldier',(500,536),load); target.update=lambda *args: None
    combat=CombatSystem(load); feedbacks=0; hitstop=0
    region={'obstacles':[]}
    p.attack()
    for _ in range(16):
        result=combat.update(p,'forest',region,[target],[],[],QuestManager(),0)
        feedbacks+=len(result.feedback); hitstop=max(hitstop,result.hitstop_frames)
    assert target.hp<target.max_hp and feedbacks==1
    report['down_combat']={'damage':target.max_hp-target.hp,'hits_per_swing':feedbacks,'hitstop':hitstop,
                           'ground_hitbox':list(p.hitbox.size)}
    (OUT/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2)); pygame.quit()


if __name__=='__main__': run()
