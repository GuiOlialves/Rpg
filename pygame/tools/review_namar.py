"""Render the actual 1E region, decision, combat and both outcomes without real saves."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
import pygame
from PIL import Image
from tests.test_namar import NamarTests
from story import namar
from ui.game_renderer import GameRenderer
from ui.world_renderer import draw_world
from core.camera import camera_for
from core.config import VIEW

OUT = Path(__file__).resolve().parent / 'visual_checks/namar'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    images, outcomes, frames = [], {}, []
    for branch in (0, 1):
        fixture = NamarTests(); fixture.setUp()
        p = fixture.p; renderer = GameRenderer(); canvas = pygame.Surface(VIEW)
        p.quests.notice_timer = 0
        font, title = pygame.font.Font(None, 22), pygame.font.Font(None, 30)
        enemies = []

        def draw(name=None, scene=None):
            renderer.draw(canvas, region=p.region, player=p.player, enemies=enemies,
                drops=[], camera=camera_for(p.player,p.region['terrain'].get_size()), debug=False,
                damage_numbers=[], hitstop_frames=0, font=font, title_font=title,
                dialogue=fixture.dialogue, quest_manager=p.quests, ui_mode=None,
                inventory=p.inventory, inventory_ui={}, game_over_screen=None,
                namar_scene=scene, story=p.story)
            im=Image.frombytes('RGB',VIEW,pygame.image.tobytes(canvas,'RGB'))
            if name:
                im.save(OUT/f'{name}.png'); images.append((name,im.copy()))
            return im

        try:
            if branch == 0:
                overview=pygame.Surface(p.region['terrain'].get_size())
                draw_world(overview,p.region,font,(0,0),p.player,[],[],show_controls=False,show_banner=False)
                pygame.image.save(overview,OUT/'region.png')
                draw('investigation')
            fixture.evidence(); fixture.start((742,675)); fixture.scene.finish()
            draw('decision' if branch==0 else None,fixture.scene)
            fixture.scene.choose(branch)
            for _ in range(15):
                fixture.scene.update(100); frames.append(draw(scene=fixture.scene if fixture.scene.active else None))
            enemies=namar.spawn_pending(p.region,p.story,fixture.world.spawn_enemies)
            p.player.x,p.player.y=(860,615) if branch==0 else (1010,355)
            for enemy in enemies: enemy._begin_attack('normal',p.player)
            draw('protect_combat' if branch==0 else 'pursue_combat')
            fixture.defeat_guards(); enemies=[]
            if branch:
                fixture.start((1150,305)); draw('carrier',fixture.scene); fixture.drive(branch)
            fixture.start((p.region['mara'].x,p.region['mara'].y+65))
            draw('protect_aftermath' if branch==0 else 'pursue_aftermath',fixture.scene)
            while fixture.scene.phase == 'aftermath':
                fixture.scene.advance(); fixture.scene.update(100)
            if branch==0:
                for index in range(67):
                    fixture.scene.update(100)
                    im=draw(scene=fixture.scene)
                    frames.append(im)
                    if index in (9,27):
                        im.save(OUT/f'memory_{index}.png'); images.append((f'memory_{index}',im.copy()))
            fixture.drive(branch)
            draw('protect_ending' if branch==0 else 'pursue_ending')
            outcomes['protect' if branch==0 else 'pursue']={
                'flags':{f:p.story.get(f) for f in namar.NAMAR_FLAGS},
                'objective':p.story.objective_text,'survivors':[n.name for n in p.region['npcs']]}
        finally: fixture.tearDown()
    board=Image.new('RGB',(1024,288*((len(images)+1)//2)),(15,20,24))
    for index,(_name,im) in enumerate(images): board.paste(im.resize((512,288)),((index%2)*512,(index//2)*288))
    board.save(OUT/'storyboard.png')
    frames=[im.resize((768,432)) for im in frames]
    frames[0].save(OUT/'choice_and_memory.gif',save_all=True,append_images=frames[1:],duration=100,loop=0)
    (OUT/'review.json').write_text(json.dumps(outcomes,ensure_ascii=False,indent=2),encoding='utf-8')
    print(str(OUT/'storyboard.png'))


if __name__=='__main__': main()
