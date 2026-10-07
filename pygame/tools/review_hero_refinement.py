"""Focused comparison and controller playback for the protagonist.

Run from pygame/: python tools/review_hero_refinement.py
Source geometry comes from each atlas; comparisons keep the same pixel scale.
"""
import json
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tools/visual_checks/hero_refinement'
ASSETS=ROOT/'assets/vale_characters'
sys.path.insert(0,str(ROOT))
from core.animation import (IDLE_DURATIONS,ATTACK_DURATIONS,DASH_POSE_DURATIONS,
                            DASH_RECOVERY_DURATIONS,HERO_FRAME,HERO_PIVOT,WEAPON_PIVOT,timed_frame)


def pose(state,frame,direction,source=ASSETS):
    sheet=Image.open(source/f'protagonist_{state}.png').convert('RGBA')
    height=sheet.height//4
    return sheet.crop((frame*32,direction*height,(frame+1)*32,(direction+1)*height))


def combined(state,frame,direction):
    tile=Image.new('RGBA',(96,96))
    tile.paste(pose(state,frame,direction),(32,WEAPON_PIVOT[1]-HERO_PIVOT[1]))
    if state=='attack':
        sheet=Image.open(ASSETS/'protagonist_weapon.png').convert('RGBA')
        weapon=sheet.crop((frame*96,direction*96,(frame+1)*96,(direction+1)*96))
        tile=Image.alpha_composite(tile,weapon)
    return tile


def plates():
    OUT.mkdir(parents=True,exist_ok=True)
    image=Image.new('RGB',(1000,400),'#202a32'); d=ImageDraw.Draw(image)
    d.text((18,12),'ANTES / DEPOIS - mesma escala inteira, pes no mesmo chao',fill='#e1d5af')
    metrics={}
    for direction,label in enumerate(('Sul','Oeste','Leste','Norte')):
        x=20+direction*245
        d.text((x,36),label,fill='#e1d5af')
        for col,source in enumerate((OUT/'before',ASSETS)):
            body=pose('idle',0,direction,source)
            height=body.height
            manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
            pivot=manifest['characters']['protagonist']['idle'].get('pivot',manifest['pivot'])[1]
            enlarged=body.resize((128,height*4),Image.Resampling.NEAREST)
            image.paste(enlarged,(x+col*112-12,235-pivot*4),enlarged)
            d.text((x+col*112+30,249),'Antes' if col==0 else 'Depois',fill='#93a3a3')
            metrics[f'{direction}/{col}']={'native_bounds':body.getbbox()}
            face_top=body.getbbox()[1]
            face=body.crop((8,face_top,24,face_top+14)).resize((96,84),Image.Resampling.NEAREST)
            image.paste(face,(x+col*112,285),face)
        d.line((x-10,235,x+220,235),fill='#56605e')
    image.save(OUT/'before_after.png')
    silhouettes=Image.new('RGB',(600,180),'#d9d2b5')
    for direction in range(4):
        body=pose('idle',0,direction)
        black=Image.new('RGBA',body.size,'#202a32'); black.putalpha(body.getchannel('A'))
        black=black.resize((128,body.height*4),Image.Resampling.NEAREST)
        silhouettes.paste(black,(direction*150+8,8),black)
    silhouettes.save(OUT/'silhouettes.png')
    for state,count in (('idle',4),('walk',8),('attack',8),('dash',5)):
        plate=Image.new('RGB',(count*160+65,4*170+30),'#202a32'); d=ImageDraw.Draw(plate)
        for direction in range(4):
            d.text((5,direction*170+20),str(direction),fill='#e1d5af')
            for frame in range(count):
                tile=combined(state,frame,direction).resize((192,192),Image.Resampling.NEAREST)
                # Keep the same floor, including sword positions outside the body cell.
                x=65+frame*160; y=direction*170+10
                d.line((x,y+126,x+145,y+126),fill='#485457')
                plate.paste(tile,(x-24,y+10),tile)
                d.text((x+65,y+144),f'{state} {frame}',fill='#93a3a3')
        plate.save(OUT/f'{state}_poses.png')
    for version,source in (('before',OUT/'before'),('after',ASSETS)):
        atlas=Image.open(source/'protagonist_hit.png')
        for direction in range(4):
            row=atlas.crop((0,direction*96,atlas.width,(direction+1)*96))
            bounds=[row.crop((i*96,0,(i+1)*96,96)).getbbox() for i in range(8)]
            bounds=[b for b in bounds if b]
            metrics[f'hit/{version}/{direction}']=[2*(min(b[0] for b in bounds)-48),
                2*(min(b[1] for b in bounds)-58),2*(max(b[2] for b in bounds)-48),2*(max(b[3] for b in bounds)-58)]
    (OUT/'proportions.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8')


def playback():
    os.environ.setdefault('SDL_VIDEODRIVER','dummy')
    os.environ.setdefault('SDL_AUDIODRIVER','dummy')
    import pygame
    from collections import defaultdict
    from unittest.mock import patch
    from core.assets import load
    from entities.player import Player
    pygame.init(); pygame.display.set_mode((1,1))
    font=pygame.font.Font(None,22)
    actors=[]
    for direction,(key,start,label) in enumerate(((pygame.K_s,(160,100),'Sul'),
                 (pygame.K_a,(255,195),'Oeste'),(pygame.K_d,(65,195),'Leste'),(pygame.K_w,(160,290),'Norte'))):
        player=Player(load('assets/player/f_player_sheet.png'),load('assets/player/f_player_attack_sheet.png'))
        player.x=player.y=500; player.facing=direction
        actors.append((player,key,(500-start[0],500-start[1]),label))
    movie=[]
    for tick in range(168):
        canvas=pygame.Surface((640,720)); canvas.fill((30,42,46))
        with patch.object(pygame.time,'get_ticks',return_value=tick*1000//60):
            for direction,(player,key,camera,label) in enumerate(actors):
                tile=pygame.Surface((320,360)); tile.fill((30,42,46))
                for yy in range(40,360,24):
                    for xx in range(0,320,24): pygame.draw.rect(tile,(45,56,57),(xx,yy,1,1))
                keys=defaultdict(bool,{key:24<=tick<48})
                if tick==50: player.attack()
                if tick==92: player.start_dash(defaultdict(bool,{key:True}))
                player.update(keys,[])
                fx,fy=round(player.x-camera[0]),round(player.y-camera[1])
                pygame.draw.ellipse(tile,(22,34,38),(fx-16,fy-3,32,7))
                player.draw(tile,camera)
                state='Dash / retorno' if 92<=tick<108 else 'Espada' if 50<=tick<66 else 'Passos' if 24<=tick<48 else 'Idle'
                tile.blit(font.render(f'{label} / {state}',False,(225,213,175)),(14,14))
                tile.blit(font.render('Controle real / escala 2x',False,(142,167,162)),(14,335))
                canvas.blit(tile,((direction%2)*320,(direction//2)*360))
        frame=Image.frombytes('RGB',canvas.get_size(),pygame.image.tobytes(canvas,'RGB'))
        movie.append(frame)
        if tick in (54,55,56,95,100): frame.save(OUT/f'controller_{tick}.png')
    movie[0].save(OUT/'hero_in_motion.gif',save_all=True,append_images=movie[1:],
                  duration=[10,20,20]*56,loop=0,disposal=2)
    # A enlarged looping downward cut retains the runtime timing, including recovery.
    cut=[]
    for tick in range(48):
        state='attack' if tick<16 else 'idle'
        index=timed_frame(tick,ATTACK_DURATIONS,False) if state=='attack' else timed_frame(tick,IDLE_DURATIONS)
        tile=combined(state,index,0).resize((384,384),Image.Resampling.NEAREST)
        background=Image.new('RGB',tile.size,'#202a32'); background.paste(tile,(0,0),tile); cut.append(background)
    cut[0].save(OUT/'front_cut.gif',save_all=True,append_images=cut[1:],duration=[10,20,20]*16,loop=0,disposal=2)
    # One real region checks the new height against NPCs, walls and scenery.
    from ui.world_renderer import draw_world
    from world.world_manager import WorldManager
    from entities.enemy import Enemy
    from systems.combat import CombatSystem
    from systems.quest import QuestManager
    region=WorldManager.for_game(load).build_region('village')
    player=Player(load('assets/player/f_player_sheet.png'),load('assets/player/f_player_attack_sheet.png'))
    player.x,player.y,player.facing=1340,590,0
    camera=(828,302)
    canvas=pygame.Surface((1024,576))
    draw_world(canvas,region,font,camera,player,[],[],show_controls=False)
    pygame.image.save(canvas,str(OUT/'village.png'))
    # Stationary target: one contact per swing, with existing combat feedback.
    fighter=Player(load('assets/player/f_player_sheet.png'),load('assets/player/f_player_attack_sheet.png'))
    fighter.x=fighter.y=500; fighter.facing=0; fighter.crit_chance=0
    target=Enemy('red_soldier',(500,536),load); target.update=lambda *args: None
    combat=CombatSystem(load); contacts=0; hitstop=0; fighter.attack()
    for _ in range(16):
        result=combat.update(fighter,'forest',{'obstacles':[]},[target],[],[],QuestManager(),0)
        contacts+=len(result.feedback); hitstop=max(hitstop,result.hitstop_frames)
    assert target.hp<target.max_hp and contacts==1
    report={'down_combat':{'damage':target.max_hp-target.hp,'contacts':contacts,'hitstop':hitstop},
            'hero_cell':list(HERO_FRAME),'game_scale':2,'ground_hitbox':list(fighter.hitbox.size),
            'village_rendered':True}
    old_mask=Image.open(OUT/'before/protagonist_hit.png')
    new_mask=Image.open(ASSETS/'protagonist_hit.png')
    report['attack_masks_unchanged']=old_mask.tobytes()==new_mask.tobytes()
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    pygame.quit()


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=OUT)
    parser.add_argument('--base-only',action='store_true')
    args=parser.parse_args(); OUT=args.output.resolve()
    plates()
    if not args.base_only: playback()
    print(OUT)
