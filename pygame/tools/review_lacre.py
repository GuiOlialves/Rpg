"""Render production sectors, complete memories, animated defenders and the chapter ending."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import sys,json,time
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from PIL import Image,ImageDraw
from tests.test_lacre import LacreTests
from ui.game_renderer import GameRenderer
from ui.world_renderer import draw_world
from core.camera import camera_for
from core.config import VIEW
from story.chapter1_return import settle_player
from story.resonance import ResonanceScene,BY_ID
from story.lacre_content import REGIONS,DOCUMENTS
from story import chapter2
from entities.lacre_actor import LacreActor
import main as game
OUT=Path(__file__).resolve().parent/'visual_checks/lacre'
def main():
    OUT.mkdir(parents=True,exist_ok=True);f=LacreTests();f.setUp();p=f.p
    renderer=GameRenderer();canvas=pygame.Surface(VIEW);font=pygame.font.Font(None,22);title=pygame.font.Font(None,30);panels=[]
    def reset():
        settle_player(p.player);p.player.hurt_visual_timer=p.player.invulnerability_timer=0;p.player.hp=p.player.max_hp
    def draw(name=None,scene=None,capture=True):
        renderer.draw(canvas,region=p.region,player=p.player,enemies=f.enemies,drops=[],camera=camera_for(p.player,p.region['terrain'].get_size()),
            debug=False,damage_numbers=[],hitstop_frames=0,font=font,title_font=title,dialogue=f.dialogue,quest_manager=p.quests,
            ui_mode=None,inventory=p.inventory,inventory_ui={},game_over_screen=None,story=p.story,chapter2_scene=scene)
        if not capture:return
        im=Image.frombytes('RGB',VIEW,pygame.image.tobytes(canvas,'RGB'))
        if name:im.save(OUT/(name+'.png'));panels.append((name,im))
        return im
    def sequence(scene,name,sample=15):
        frames=[]
        for i in range(250):
            if not scene.active:break
            scene.update(100);im=draw(scene=scene if scene.active else None)
            frames.append(im.resize((768,432),Image.Resampling.NEAREST))
            if i==sample:im.save(OUT/(name+'.png'));panels.append((name,im))
        frames[0].save(OUT/(name+'.gif'),save_all=True,append_images=frames[1:],duration=100,loop=0)
    def map_image(kind):
        full=pygame.Surface(p.region['terrain'].get_size());draw_world(full,p.region,font,(0,0),p.player,f.enemies,[],show_banner=False,show_controls=False,story_context=p.story)
        pygame.image.save(full,OUT/(kind+'_map.png'))
    try:
        f.b();reset();p.quests.notice_timer=0;p.player.x,p.player.y=1024,820;draw('vestibule');map_image(REGIONS[0]);f.kill();reset()
        p.player.x,p.player.y=1024,735;sequence(ResonanceScene(BY_ID['l_echo_vestibule'],p.player,p.story),'vestibule_memory');p.story.apply_to_region(p.region)
        f.solve('vestibule');f.enter(REGIONS[1]);reset();p.player.x,p.player.y=1024,700;draw('gallery');map_image(REGIONS[1]);f.kill();reset()
        for uid in ('l_echo_door','l_echo_hand','l_echo_seal'):
            point=BY_ID[uid];p.player.x,p.player.y=point.position[0],point.position[1]+35
            sequence(ResonanceScene(point,p.player,p.story),uid);p.story.apply_to_region(p.region)
        f.solve('gallery');draw('gallery_open');f.enter(REGIONS[2]);reset();p.player.x,p.player.y=1024,740;draw('archive');map_image(REGIONS[2]);f.kill();reset()
        for uid in ('lacre_purpose','lacre_military','lacre_identity'):
            target=f.f.target(uid);p.player.x,p.player.y=target.x,target.y+35
            target.begin_interaction(f.dialogue,p.player,p.quests);f.dialogue.index=1;draw(uid);f.dialogue.npc=None;f.examine(uid)
        p.player.x,p.player.y=625,850;sequence(ResonanceScene(BY_ID['l_echo_secret'],p.player,p.story),'secret_memory')
        chapter2.interact(f.f.target('lacre_hidden'),p.player,p.story,f.dialogue,p.quests,p.inventory,p.region)
        f.examine('lacre_cache');f.examine('lacre_lore');f.examine('lacre_service');draw('secret_and_service')
        f.enter(REGIONS[3]);reset();p.player.x,p.player.y=1024,700;draw('vigia');map_image(REGIONS[3]);f.kill();f.examine('lacre_checkpoint');reset();draw('checkpoint')
        f.enter(REGIONS[4]);reset();p.player.x,p.player.y=1024,740;sequence(f.scene('core_vista'),'core_vista');map_image(REGIONS[4])
        scene=f.scene('custodian_talk');p.player.x,p.player.y=1024,670;f.dialogue.index=4;draw('custodian_conversation',scene);scene.finish()
        # Each complete action runs its telegraph, contact, recovery and delayed residual.
        for kind,actions in (('lacre_guard',('cut',)),('unstable_echo',('cut',)),('record_warden',('cut','sweep','ward')),('custodian',('cut','sweep','charge','echo'))):
            for action in actions:
                actor=LacreActor(kind,(1024,670),game.load);actor.story=p.story;actor.region=p.region;f.enemies=[actor]
                reset();p.player.x,p.player.y=1068,670
                if action=='echo':actor.phase=2
                actor.begin_attack(p.player,'sweep' if action=='echo' else action);frames=[]
                for i in range(actor.prep+actor.active_frames+actor.recovery+45):
                    p.player.update(defaultdict(bool),p.region['obstacles']);actor.update(p.player,p.region['obstacles']);im=draw()
                    frames.append(im.resize((768,432),Image.Resampling.NEAREST))
                frames[0].save(OUT/(kind+'_'+action+'.gif'),save_all=True,append_images=frames[1:],duration=17,loop=0)
                if kind=='custodian' and action=='echo':draw('resonance_duel')
        f.enemies=chapter2.spawn_pending(p.region,p.story,f.world.spawn_enemies);p.region['live_enemies']=f.enemies
        boss=f.enemies[0];reset();p.player.x,p.player.y=980,570;boss.receive_hit(1000,980,570);boss.update(p.player,p.region['obstacles']);p.story.apply_to_region(p.region);draw('phase_transition')
        for side in ('left','right'):chapter2.interact(f.f.target('anchor_'+side),p.player,p.story,f.dialogue,p.quests,p.inventory,p.region)
        f.kill();reset();f.scene('aftermath').finish();p.story.apply_to_region(p.region);draw('custodian_survives')
        for uid in ('lacre_first','lacre_second'):
            target=f.f.target(uid);p.player.x,p.player.y=target.x,target.y+35;target.begin_interaction(f.dialogue,p.player,p.quests);f.dialogue.index=1;draw(uid);f.dialogue.npc=None;f.examine(uid)
        p.player.x,p.player.y=1024,775;sequence(ResonanceScene(BY_ID['l_echo_central'],p.player,p.story),'central_memory',35)
        p.player.x,p.player.y=1024,580;scene=f.scene('choice');draw('record_choice',scene);scene.choose(1)
        f.enter('encosta');reset();p.player.x,p.player.y=780,710;scene=f.scene('return');f.dialogue.index=5;draw('return_to_ines',scene);scene.finish()
        p.player.x,p.player.y=1650,810;sequence(f.scene('final'),'chapter2_completed',100);draw('control_restored')
        start=time.perf_counter()
        for _ in range(180):draw(capture=False)
        (OUT/'review.json').write_text(json.dumps(dict(renderer_ms=(time.perf_counter()-start)*1000/180,chapter2_completed=p.story.get('chapter2_completed'),objective=p.story.objective_text),ensure_ascii=False,indent=2),encoding='utf-8')
    finally:f.tearDown()
    board=Image.new('RGB',(1024,310*((len(panels)+1)//2)),(20,28,35));d=ImageDraw.Draw(board)
    for i,(name,im) in enumerate(panels):
        x,y=i%2*512,i//2*310;board.paste(im.resize((512,288),Image.Resampling.NEAREST),(x,y+22));d.text((x+8,y+5),name,fill=(215,201,161))
    board.save(OUT/'storyboard.png');print(OUT/'storyboard.png')
if __name__=='__main__':main()
