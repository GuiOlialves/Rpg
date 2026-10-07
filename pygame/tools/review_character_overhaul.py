"""Focused, headless visual review and movement/map smoke. No save writes."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import json
import sys
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from PIL import Image
from core.assets import load
from entities.player import Player
from entities.enemy import Enemy
from entities.red_officer import RedOfficer
from ui.character_art import character_sheet, character_frame, draw_character
from ui.world_renderer import draw_world
from world.world_manager import WorldManager
from systems.quest import QuestManager
from systems.combat import CombatSystem
from ui.damage_number import DamageNumber
from core.animation import (ATTACK_DURATIONS, IDLE_DURATIONS, timed_frame,
                            DASH_POSE_DURATIONS, DASH_RECOVERY_DURATIONS)

OUT=ROOT/'tools/visual_checks/character_overhaul'


def save(surface,name): pygame.image.save(surface,OUT/name)


def run(output=None):
    global OUT
    if output is not None: OUT=Path(output).resolve()
    pygame.init(); pygame.display.set_mode((1,1)); OUT.mkdir(parents=True,exist_ok=True)
    font=pygame.font.Font(None,19)
    player=Player(load('assets/player/f_player_sheet.png'),load('assets/player/f_player_attack_sheet.png'))
    world=WorldManager.for_game(load)
    build_region=world.build_region
    quests=QuestManager()
    quests.forest_boss_defeated=True
    def prepare(destination,quests,opened,build,spawn,guardian):
        region=build(destination,opened)
        return region,spawn(region)
    manifest=json.loads((ROOT/'assets/vale_characters/manifest.json').read_text())
    cast=pygame.Surface((1080,660)); cast.fill((30,36,45))
    for i,look in enumerate(manifest['characters']):
        x,y=(i%6)*180,(i//6)*220
        cast.blit(character_frame(character_sheet(load,look),draw_size=128),(x+24,y+8))
        cast.blit(font.render(look,False,(224,208,170)),(x+8,y+143))
        draw_character(cast,(0,0),character_sheet(load,look),x+48,y+207)
        draw_character(cast,(0,0),character_sheet(load,look),x+117,y+207,facing=2)
    save(cast,'cast.png')
    poses=pygame.Surface((1100,820)); poses.fill((30,36,45))
    for row,(state,count) in enumerate((('idle',4),('walk',8),('attack',8),('dash',5),('hurt',3),('death',4))):
        y=130+row*132
        poses.blit(font.render(state,False,(224,208,170)),(8,y-60))
        for index in range(count):
            x=132+index*124
            pygame.draw.line(poses,(65,77,80),(x-44,y),(x+44,y))
            player.visual.draw(poses,(0,0),x,y,state,2,index,weapon_index=index if state=='attack' else None)
            poses.blit(font.render(str(index),False,(160,177,180)),(x-4,y+7))
    save(poses,'hero_states.png')
    attacks=pygame.Surface((1120,640)); attacks.fill((30,36,45))
    for direction,label in enumerate(('baixo','esquerda','direita','cima')):
        y=136+direction*158
        attacks.blit(font.render(label,False,(224,208,170)),(8,y-70))
        for index in range(8):
            x=148+index*132
            pygame.draw.line(attacks,(65,77,80),(x-32,y),(x+32,y))
            player.visual.draw(attacks,(0,0),x,y,'attack',direction,index,weapon_index=index)
    save(attacks,'sword_directions.png')
    # Lossless animation at actual authored timings; includes fixed-camera walking.
    gif=[]
    for tick in range(0,120,2):
        surface=pygame.Surface((760,270)); surface.fill((30,36,45))
        for x,label in ((90,'Idle'),(250,'Passos'),(450,'Espada'),(650,'Dash')):
            surface.blit(font.render(label,False,(224,208,170)),(x-25,25))
            pygame.draw.line(surface,(65,77,80),(x-60,182),(x+60,182))
        player.visual.draw(surface,(0,0),90,182,'idle',0,timed_frame(tick,IDLE_DURATIONS))
        player.visual.draw(surface,(0,0),250,182,'walk',2,(tick//4)%8)
        attack_tick=tick%32
        if attack_tick<16:
            index=timed_frame(attack_tick,ATTACK_DURATIONS,loop=False)
            player.visual.draw(surface,(0,0),450,182,'attack',2,index,weapon_index=index)
        else: player.visual.draw(surface,(0,0),450,182,'idle',2)
        elapsed=tick%32
        if elapsed<11: dash_state,dash_index='dash',timed_frame(elapsed,DASH_POSE_DURATIONS,False)
        elif elapsed<16: dash_state,dash_index='dash',3+timed_frame(elapsed-11,DASH_RECOVERY_DURATIONS,False)
        else: dash_state,dash_index='idle',timed_frame(tick,IDLE_DURATIONS)
        player.visual.draw(surface,(0,0),650,182,dash_state,2,dash_index)
        gif.append(Image.frombytes('RGB',surface.get_size(),pygame.image.tobytes(surface,'RGB')))
    gif[0].save(OUT/'animations.gif',save_all=True,append_images=gif[1:],duration=[30,30,40]*20,loop=0,disposal=2)
    # Render real regions and exercise unchanged transition/ground collision contracts.
    report={'regions':{},'transitions':[]}
    for region_id,position in (('village',(1430,590)),('forest',(780,530)),('desert',(1030,540)),('home',(512,400))):
        region=build_region(region_id); player.x,player.y=position
        before=player.hitbox.size
        keys=defaultdict(bool,{pygame.K_d:True})
        for _ in range(20): player.update(keys,region['obstacles'])
        player.attack()
        for _ in range(6): player.update(defaultdict(bool),region['obstacles'])
        camera=(max(0,round(player.x-512)),max(0,round(player.y-288)))
        canvas=pygame.Surface((1024,576))
        enemies=[]
        if region_id=='forest':
            enemies=[Enemy('slime',(player.x+58,player.y+20),load),
                     Enemy('warrior',(player.x+155,player.y+60),load),
                     RedOfficer((player.x+270,player.y+10),load,defeat_hp=40)]
        if region_id=='desert':
            enemies=[Enemy('desert_scout',(player.x+110,player.y+50),load),
                     Enemy('dune_lancer',(player.x+220,player.y+60),load)]
        for enemy in enemies: enemy.update(player,region['obstacles'])
        draw_world(canvas,region,font,camera,player,enemies,[],show_controls=False)
        save(canvas,f'{region_id}.png')
        assert player.hitbox.size==before==(26,18)
        player.attack_timer=0; player.dash_cooldown=0; player.sp=player.max_sp
        assert player.start_dash(keys)
        for _ in range(11): player.update(keys,region['obstacles'])
        report['regions'][region_id]={'rendered':True,'move_attack_dash':True,'player_hitbox':list(before)}
        for exit_id,trigger in region['exits'].items():
            if exit_id not in ('village','forest','desert'): continue
            # Test the real resolver; story locks remain respected by the game.
            region['north_locked']=region['arena_locked']=False
            player.x,player.y=trigger.center
            transition=world.transition(region_id,exit_id,quests,set(),prepare,None,region)
            if transition:
                report['transitions'].append([region_id,transition.region_id])
                destination=build_region(transition.region_id)
                player.x,player.y=transition.spawn
                player.draw(canvas,(0,0))
    # An actual combat-system hit: sword mask, one hit per serial, flash and burst.
    region=build_region('forest')
    fighter=Player(load('assets/player/f_player_sheet.png'),load('assets/player/f_player_attack_sheet.png'))
    fighter.x,fighter.y,fighter.facing=780,530,2
    fighter.crit_chance=1
    target=Enemy('red_soldier',(825,530),load)
    target.attack_cooldown=999
    combat=CombatSystem(load)
    fighter.attack()
    for _ in range(16):
        frame=combat.update(fighter,'forest',region,[target],[],[],QuestManager(),0)
        if frame.feedback:
            canvas=pygame.Surface((1024,576)); camera=(268,242)
            draw_world(canvas,region,font,camera,fighter,[target],[],show_controls=False)
            for feedback in frame.feedback:
                DamageNumber(feedback.text,*feedback.position,feedback.color,feedback.critical).draw(
                    canvas,camera,font,pygame.font.Font(None,30))
            save(canvas,'impact.png')
            break
    assert target.hp < target.max_hp
    report['actual_sword_hit']={'damage':target.max_hp-target.hp,'hitstop':frame.hitstop_frames,
                                'flash':target.visual_flash>0,'burst':fighter.impact_timer>0}
    bosses=pygame.Surface((1040,540)); bosses.fill((30,36,45))
    for row,kind in enumerate(('red_officer','forest_guardian')):
        y=235+row*260
        bosses.blit(font.render(kind,False,(224,208,170)),(8,y-160))
        boss=RedOfficer((0,0),load,defeat_hp=40) if kind=='red_officer' else Enemy(kind,(0,0),load)
        for col,phase in enumerate(('windup','active','recovery')):
            boss.x,boss.y=200+col*320,y
            boss.state='ATTACK'; boss.attack_action='charged'; boss.attack_phase=phase
            boss.attack_direction=(1,0); boss.anim_tick=12; boss.phase_timer=3
            pygame.draw.line(bosses,(65,77,80),(boss.x-44,y),(boss.x+44,y))
            boss.draw(bosses,(0,0))
            bosses.blit(font.render(phase,False,(160,177,180)),(boss.x-35,y+14))
    save(bosses,'boss_states.png')
    (OUT/'smoke.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2)); pygame.quit()


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=OUT)
    run(parser.parse_args().output)
