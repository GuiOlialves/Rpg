"""Stage-specific reviews at game scale and enlarged nearest pixel scale."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw
from draw_vale_pack import PALETTE
from hero_pixel_art import PIVOT as HERO_PIVOT

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tools/visual_checks/staged_overhaul'
ASSETS=ROOT/'assets/vale_characters'


def pose(state,frame,direction):
    sheet=Image.open(ASSETS/f'protagonist_{state}.png')
    height=sheet.height//4
    return sheet.crop((frame*32,direction*height,(frame+1)*32,(direction+1)*height))


def combined(state,frame,direction,scale=3):
    tile=Image.new('RGBA',(96,96))
    body=pose(state,frame,direction)
    tile.paste(body,(32,58-(body.height-2)))
    if state=='attack':
        sheet=Image.open(ASSETS/'protagonist_weapon.png')
        weapon=sheet.crop((frame*96,direction*96,(frame+1)*96,(direction+1)*96))
        tile=Image.alpha_composite(tile,weapon)
    return tile.resize((96*scale,96*scale),Image.Resampling.NEAREST)


def review(stage):
    OUT.mkdir(parents=True,exist_ok=True)
    states={'base':(('idle',4),('walk',8)), 'attack':(('attack',8),), 'dash':(('dash',5),)}[stage]
    gap=180 if stage=='attack' else 145
    canvas=Image.new('RGB',(max(1120,144+8*gap),210+len(states)*4*gap),(30,36,45)); d=ImageDraw.Draw(canvas)
    d.text((20,14),f'PROTAGONISTA / {stage} / pixel 2x e 3x / pivo dos pes {HERO_PIVOT}',fill='#e1d5af')
    for direction,label in enumerate(('Sul','Oeste','Leste','Norte')):
        im=pose('idle',0,direction)
        im=im.resize((128,im.height*4),Image.Resampling.NEAREST)
        canvas.paste(im,(60+direction*240,34),im)
        d.text((60+direction*240,194),label,fill='#e1d5af')
    row=0
    for state,count in states:
        for direction in range(4):
            y=210+row*gap; row+=1
            d.text((12,y+8),f'{state}/{direction}',fill='#e1d5af')
            for frame in range(count):
                im=pose(state,frame,direction); size=96; x=144+frame*gap
                tile=im.resize((size,im.height*3),Image.Resampling.NEAREST)
                floor=56 if stage=='attack' else HERO_PIVOT[1]*3
                d.line((x,y+floor,x+96,y+floor),fill='#485457')
                if stage=='attack':
                    full=combined(state,frame,direction,2); canvas.paste(full,(x-64,y-60),full)
                else: canvas.paste(tile,(x,y),tile)
                d.text((x+42,y+floor+14),str(frame),fill='#93a3a3')
    canvas.save(OUT/f'{stage}_poses.png')
    silhouette=Image.new('RGB',(640,184),'#e1d5af')
    for facing in range(4):
        im=pose('idle',0,facing); black=Image.new('RGBA',im.size,'#252b3c'); black.putalpha(im.getchannel('A'))
        black=black.resize((128,im.height*4),Image.Resampling.NEAREST)
        silhouette.paste(black,(16+facing*160,12),black)
    silhouette.save(OUT/'hero_silhouettes.png')
    frames=[]
    from sys import path
    path.insert(0,str(ROOT))
    from core.animation import IDLE_DURATIONS, ATTACK_DURATIONS, timed_frame, DASH_POSE_DURATIONS, DASH_RECOVERY_DURATIONS
    for tick in range(120):
        im=Image.new('RGB',(760,340),(30,36,45)); draw=ImageDraw.Draw(im)
        for facing in range(4):
            x=50+facing*180
            draw.line((x-15,130,x+100,130),fill='#485457')
            draw.line((x-15,276,x+100,276),fill='#485457')
            idle=pose('idle',timed_frame(tick,IDLE_DURATIONS),facing)
            idle=idle.resize((96,idle.height*3),Image.Resampling.NEAREST)
            im.paste(idle,(x,130-HERO_PIVOT[1]*3),idle)
            state='walk' if stage=='base' else stage
            frame=(tick//3)%8 if stage=='base' else timed_frame(tick%32,ATTACK_DURATIONS,False) if stage=='attack' else min(2,(tick%24)//4)
            if stage=='attack' and tick%32>=16: state,frame='idle',timed_frame(tick,IDLE_DURATIONS)
            if stage=='dash':
                elapsed=tick%32
                if elapsed<11: frame=timed_frame(elapsed,DASH_POSE_DURATIONS,False)
                elif elapsed<16: frame=3+timed_frame(elapsed-11,DASH_RECOVERY_DURATIONS,False)
                else: state,frame='idle',timed_frame(tick,IDLE_DURATIONS)
            if stage=='attack':
                body=combined(state,frame,facing,2); im.paste(body,(x-64,132),body)
            else:
                body=pose(state,frame,facing)
                body=body.resize((96,body.height*3),Image.Resampling.NEAREST)
                im.paste(body,(x,276-HERO_PIVOT[1]*3),body)
        frames.append(im)
    frames[0].save(OUT/f'{stage}.gif',save_all=True,append_images=frames[1:],duration=[10,20,20]*40,loop=0,disposal=2)
    print(OUT/f'{stage}_poses.png')


def review_motion():
    """Render the actual controller, including motion, trails, reactions and defeat."""
    import os,sys
    os.environ.setdefault('SDL_VIDEODRIVER','dummy')
    os.environ.setdefault('SDL_AUDIODRIVER','dummy')
    sys.path.insert(0,str(ROOT))
    from collections import defaultdict
    from unittest.mock import patch
    import pygame
    from core.assets import load
    from entities.player import Player
    pygame.init(); pygame.display.set_mode((1,1))
    font=pygame.font.Font(None,22)
    panels=[]
    for facing,(key,pos,label) in enumerate(((pygame.K_s,(235,90),'Sul'),(pygame.K_a,(365,235),'Oeste'),
                                           (pygame.K_d,(100,235),'Leste'),(pygame.K_w,(235,320),'Norte'))):
        player=Player(load('assets/player/f_player_sheet.png'),load('assets/player/f_player_attack_sheet.png'))
        player.x=player.y=500; player.facing=facing
        panels.append((player,key,(500-pos[0],500-pos[1]),label))
    movie=[]
    for tick in range(184):
        canvas=pygame.Surface((960,720)); canvas.fill((25,32,40))
        with patch.object(pygame.time,'get_ticks',return_value=tick*1000//60):
            for i,(player,key,camera,label) in enumerate(panels):
                tile=pygame.Surface((480,360)); tile.fill((34,44,48))
                for yy in range(40,360,24):
                    for xx in range(0,480,24): pygame.draw.rect(tile,(39,50,52),(xx,yy,1,1))
                keys=defaultdict(bool,{key:18<=tick<43})
                if tick==43: player.attack()
                if tick==80: player.start_dash(defaultdict(bool,{key:True}))
                if tick==106: player.take_damage(12,player.x+25,player.y+10)
                if tick==126: player.hp=0; player.death_started=tick*1000//60
                if player.hp>0: player.update(keys,[])
                fx,fy=round(player.x-camera[0]),round(player.y-camera[1])
                pygame.draw.ellipse(tile,(22,34,38),(fx-19,fy-3,38,8))
                player.draw(tile,camera)
                state=('Derrota' if tick>=126 else 'Dano' if tick>=106 else 'Dash / retorno' if 80<=tick<99
                       else 'Espada' if 43<=tick<60 else 'Passos' if 18<=tick<43 else 'Idle')
                tile.blit(font.render(f'{label} - {state}',False,(225,213,175)),(18,15))
                tile.blit(font.render('Escala do jogo: 2x / controle real',False,(142,167,162)),(18,337))
                canvas.blit(tile,((i%2)*480,(i//2)*360))
        if tick%2==0: movie.append(Image.frombytes('RGB',canvas.get_size(),pygame.image.tobytes(canvas,'RGB')))
    OUT.mkdir(parents=True,exist_ok=True)
    movie[0].save(OUT/'hero_in_motion.gif',save_all=True,append_images=movie[1:],duration=[30,30,40]*31,loop=0,disposal=2)
    # One decisive contact and one real dash frame for static QA.
    movie[24].save(OUT/'real_attack.png'); movie[43].save(OUT/'real_dash.png')
    pygame.quit(); print(OUT/'hero_in_motion.gif')


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('stage',choices=('base','attack','dash','motion','all'))
    stage=parser.parse_args().stage
    if stage in ('motion','all'): review_motion()
    if stage=='all':
        for part in ('base','attack','dash'): review(part)
    elif stage!='motion': review(stage)
