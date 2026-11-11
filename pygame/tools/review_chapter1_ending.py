"""Capture 1G's actual renderer, two civilian outcomes and the complete final sequence."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import pygame
from PIL import Image
from tests.test_chapter1_ending import Chapter1EndingTests
from story import chapter1_ending as ending
from ui.game_renderer import GameRenderer
from core.camera import camera_for
from core.config import VIEW

OUT=Path(__file__).resolve().parent/'visual_checks/chapter1_ending'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    panels=[]; outcomes={}
    for branch in (0,1):
        f=Chapter1EndingTests(); f.setUp(); p=f.p
        for flag,value in (('namar_choice_protect',branch==0),('namar_choice_pursue',branch==1),
                           ('namar_supplies_lost',branch==1),('namar_dispatch_detail',branch==1)):
            p.story.set(flag,value)
        renderer=GameRenderer(); canvas=pygame.Surface(VIEW)
        font,title=pygame.font.Font(None,22),pygame.font.Font(None,30)
        def draw(name=None,alden=None,final=None):
            renderer.draw(canvas,region=p.region,player=p.player,enemies=[],drops=[],
                camera=camera_for(p.player,p.region['terrain'].get_size()),debug=False,
                damage_numbers=[],hitstop_frames=0,font=font,title_font=title,dialogue=f.dialogue,
                quest_manager=p.quests,ui_mode=None,inventory=p.inventory,inventory_ui={},
                game_over_screen=None,story=p.story,alden_scene=alden,ending_scene=final)
            im=Image.frombytes('RGB',VIEW,pygame.image.tobytes(canvas,'RGB'))
            if name: im.save(OUT/f'{name}.png'); panels.append(im.copy())
            return im
        try:
            if branch==0:
                p.story.apply_to_region(p.region); p.player.x,p.player.y=246,847
                draw('return_route')
            f.return_homeward(); p.player.x,p.player.y=1635,740
            mara=next(n for n in p.region['npcs'] if n.uid=='vale_mara')
            mara.begin_interaction(f.dialogue,p.player,p.quests)
            draw('protect_consequence' if branch==0 else 'pursue_consequence'); f.dialogue.npc=None
            p.player.x,p.player.y=1830,560
            alden=next(n for n in p.region['npcs'] if n.uid=='alden')
            scene=ending.FinalAldenScene(alden,p.player,f.dialogue,p.region)
            if branch==0:
                scene.index=4; scene._open_step(f.dialogue); draw('alden_responsibility',alden=scene)
            scene.finish(f.dialogue,p.story,p.quests,p.inventory)
            receipt=next(o for o in p.region['interactables'] if o.uid=='encosta_receipt')
            p.player.x,p.player.y=1780,640
            receipt.begin_interaction(f.dialogue,p.player,p.quests); f.dialogue.index=1
            if branch==0: draw('receipt_hook')
            f.dialogue.npc=None; ending.complete_evidence(receipt,p.story,p.inventory)
            f.house(); p.quests.notice_timer=0
            scene=ending.Chapter1EndingScene(p.player,p.story,p.quests)
            frames=[]
            for tick in range(180):
                if not scene.active: break
                scene.update(100)
                im=draw(final=scene if scene.active else None)
                if branch==0:
                    frames.append(im.resize((768,432)))
                    if tick in (4,22,54,76,121,144):
                        im.save(OUT/f'final_{tick}.png'); panels.append(im.copy())
            if branch==0:
                frames[0].save(OUT/'complete_ending.gif',save_all=True,append_images=frames[1:],duration=100,loop=0)
                p.story.apply_to_region(p.region); draw('exploration_restored')
            outcomes['protect' if branch==0 else 'pursue']={
                'flags':{flag:p.story.get(flag) for flag in ending.ENDING_FLAGS},
                'choice':branch,'objective':p.story.objective_text}
        finally: f.tearDown()
    board=Image.new('RGB',(1024,288*((len(panels)+1)//2)),(15,20,24))
    for i,im in enumerate(panels): board.paste(im.resize((512,288)),((i%2)*512,(i//2)*288))
    board.save(OUT/'storyboard.png')
    (OUT/'review.json').write_text(json.dumps(outcomes,ensure_ascii=False,indent=2),encoding='utf-8')
    print(OUT/'storyboard.png')


if __name__=='__main__': main()
