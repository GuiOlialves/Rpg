"""Capture the actual 1F renderer and full attacks/flashback without touching player saves."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import pygame
from PIL import Image
from tests.test_archive import ArchiveTests
from story import archive
from ui.game_renderer import GameRenderer
from ui.world_renderer import draw_world
from core.camera import camera_for
from core.config import VIEW

OUT=Path(__file__).resolve().parent/'visual_checks/archive'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f=ArchiveTests(); f.setUp()
    p=f.p; renderer=GameRenderer(); canvas=pygame.Surface(VIEW)
    font,title=pygame.font.Font(None,22),pygame.font.Font(None,30)
    enemies=[]; panels=[]
    def draw(name=None,scene=None):
        camera=p.region['combat_camera'] if p.region.get('boss_battle_active') else camera_for(p.player,p.region['terrain'].get_size())
        renderer.draw(canvas,region=p.region,player=p.player,enemies=enemies,drops=[],camera=camera,
            debug=False,damage_numbers=[],hitstop_frames=0,font=font,title_font=title,dialogue=f.dialogue,
            quest_manager=p.quests,ui_mode=None,inventory=p.inventory,inventory_ui={},game_over_screen=None,
            archive_scene=scene,story=p.story)
        im=Image.frombytes('RGB',VIEW,pygame.image.tobytes(canvas,'RGB'))
        if name: im.save(OUT/f'{name}.png'); panels.append((name,im.copy()))
        return im
    try:
        overview=pygame.Surface(p.region['terrain'].get_size())
        draw_world(overview,p.region,font,(0,0),p.player,[],[],show_controls=False,show_banner=False)
        pygame.image.save(overview,OUT/'region.png')
        p.quests.notice_timer=0
        p.player.x,p.player.y=325,620; draw('investigation')
        obj=next(o for o in p.region['interactables'] if o.uid=='archive_defense')
        obj.begin_interaction(f.dialogue,p.player,p.quests)
        f.dialogue.index=1; draw('military_document'); f.dialogue.npc=None
        f.examine('archive_defense'); f.examine('archive_petition')
        p.player.x,p.player.y=750,680
        scene=f.start(); draw('challenge',scene); f.drive()
        boss=p.region['veteran']; enemies=[boss]
        action_frames=[]; motion_panels=[]
        for action in ('normal','charged','charge'):
            boss.x,boss.y=880,615; p.player.x,p.player.y=985,615
            boss._begin_attack(action,p.player)
            draw(f'{action}_windup')
            # Actual AI phase progression at 60 Hz, with frames sampled at 30 Hz.
            for tick in range(boss.WINDUP[action]+boss.ACTIVE[action]+boss.RECOVERY[action]+6):
                boss.update(p.player,p.region['obstacles'])
                if tick%2==0: action_frames.append(draw().resize((768,432)))
                w,a,r=boss.WINDUP[action],boss.ACTIVE[action],boss.RECOVERY[action]
                if tick in (0,w//2,w-2,w,w+a//2,w+a-1,w+a+8,w+a+r-2):
                    motion_panels.append(draw().crop((535,235,890,425)).resize((355,190)))
                if boss.attack_phase=='active' and boss.phase_timer==boss.ACTIVE[action]//2:
                    draw(f'{action}_strike')
        action_frames[0].save(OUT/'three_attacks.gif',save_all=True,append_images=action_frames[1:],duration=33,loop=0)
        motion_board=Image.new('RGB',(355*8,190*3),(15,20,24))
        for i,im in enumerate(motion_panels): motion_board.paste(im,((i%8)*355,(i//8)*190))
        motion_board.save(OUT/'attack_phases.png')
        boss.hit_resistance_timer=0; boss.receive_hit(1000,p.player.x,p.player.y)
        archive.complete_combat(p.region,p.story,enemies)
        draw('surrender')
        p.player.x,p.player.y=915,345
        f.examine('archive_order'); scene=f.start()
        memory=[]
        for tick in range(112):
            scene.update(100)
            im=draw(scene=scene if scene.active else None)
            memory.append(im.resize((768,432)))
            if tick in (30,63): im.save(OUT/f'memory_{tick}.png'); panels.append((f'memory_{tick}',im.copy()))
        memory[0].save(OUT/'order_memory.gif',save_all=True,append_images=memory[1:],duration=100,loop=0)
        f.examine('archive_forgetting'); scene=f.start(); draw('ending',scene); f.drive()
        p.quests.notice_timer=0; draw('return_objective')
        (OUT/'review.json').write_text(json.dumps({'flags':{k:p.story.get(k) for k in archive.ARCHIVE_FLAGS},
            'objective':p.story.objective_text,'veteran_hp':boss.hp,'order_items':sum(i['id']=='namar_order_copy' for i in p.inventory)},ensure_ascii=False,indent=2),encoding='utf-8')
        board=Image.new('RGB',(1024,288*((len(panels)+1)//2)),(15,20,24))
        for i,(_name,im) in enumerate(panels): board.paste(im.resize((512,288)),((i%2)*512,(i//2)*288))
        board.save(OUT/'storyboard.png')
        print(OUT/'storyboard.png')
    finally: f.tearDown()


if __name__=='__main__': main()
