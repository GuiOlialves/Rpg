"""Render all registered maps and compare the pre-polish gameplay contract."""
import json
import os
from pathlib import Path
import sys
import time

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from core.assets import load
from ui.world_renderer import draw_world
from world.world_manager import WorldManager


def contract(region):
    return json.loads(json.dumps({
        'obstacles':[list(v) for v in region['obstacles']], 'spawn':region['spawn'],
        'exits':{k:list(v) for k,v in region['exits'].items()},
        'enemy_spawns':region['enemy_spawns'],
        'interactables':[(a.uid,a.x,a.y,list(a.interaction_rect)) for a in region.get('interactables',[])]}))


def run():
    pygame.init();pygame.display.set_mode((1,1));font=pygame.font.Font(None,22)
    out=ROOT/'tools/visual_checks/world_polish';out.mkdir(parents=True,exist_ok=True)
    baseline_path=out/'contracts.json'
    baseline=json.loads(baseline_path.read_text(encoding='utf8')) if baseline_path.exists() else None
    world=WorldManager.for_game(load); shots=[];report={}
    for name in world.region_ids:
        start=time.perf_counter();region=world.build_region(name)
        build_ms=round((time.perf_counter()-start)*1000,1)
        if baseline is not None:assert contract(region)==baseline[name],f'Gameplay geometry changed: {name}'
        image=pygame.Surface(region['terrain'].get_size())
        draw_world(image,region,font,(0,0),show_controls=False,show_banner=False)
        pygame.image.save(image,out/f'{name}_after.png')
        thumb=pygame.Surface((512,312));thumb.fill((21,28,30))
        thumb.blit(pygame.transform.scale(image,(512,288)),(0,24))
        thumb.blit(font.render(region['name'],True,(231,219,181)),(10,4));shots.append(thumb)
        old=out/f'{name}_before.png'
        if old.exists():
            comparison=pygame.Surface((1536,456));comparison.fill((21,28,30))
            comparison.blit(font.render('ANTES',True,'white'),(12,8))
            comparison.blit(font.render('ASSETS DO ACERVO',True,'white'),(780,8))
            comparison.blit(pygame.transform.scale(pygame.image.load(old),(768,432)),(0,24))
            comparison.blit(pygame.transform.scale(image,(768,432)),(768,24))
            pygame.image.save(comparison,out/f'{name}_comparison.png')
        # Real-size close-up in the central playable area, not only scaled overviews.
        center={'old_road':(1060,520),'watchpost':(810,440),'namar':(940,480),
                'encosta':(960,520),'threshold':(1420,460),'forgotten_route':(1024,680)}.get(name,region['terrain'].get_rect().center)
        camera=(max(0,min(image.width-1024,center[0]-512)),max(0,min(image.height-576,center[1]-288)))
        viewport=pygame.Surface((1024,576))
        enemies=world.spawn_enemies(region)
        draw_world(viewport,region,font,camera,enemies=enemies,show_controls=False,show_banner=False)
        pygame.image.save(viewport,out/f'{name}_detail.png')
        start=time.perf_counter()
        for _ in range(30):draw_world(viewport,region,font,camera,enemies=enemies,show_controls=False,show_banner=False)
        report[name]={'geometry':'unchanged' if baseline is not None else 'no baseline',
                      'build_ms':build_ms,'render_ms':round((time.perf_counter()-start)*1000/30,2)}
        print(name,report[name],flush=True)
    montage=pygame.Surface((1536,312*((len(shots)+2)//3)))
    for i,shot in enumerate(shots):montage.blit(shot,(i%3*512,i//3*312))
    pygame.image.save(montage,out/'all_after.png')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    pygame.quit()


if __name__=='__main__':run()
