"""Small campaign registry: reception, sorting yard and the protected seventh drawer."""
import random
import pygame
import environment as env
from entities.interactable import Interactable
from entities.archive_veteran import ArchiveVeteran
from world.regions.watchpost_art import floor, wall, prop as furniture
from world.regions.old_road_art import prop as road_prop
from world.regions import archive_art as art

WORLD=(1280,960)


def build(load, opened_chests=None):
    terrain=env.ground(WORLD,load('sprites_meu/vila_tile-set/1 Tiles/FieldsTile_11.png'),161,
                       ((94,91,76),(140,134,104)))
    scenery,obstacles=[],[]
    def place(image,foot,box=None):
        obj=env.anchored(image,foot); scenery.append(obj)
        env.shadow(terrain,foot,image.width//2,8,30)
        if box: obstacles.append(pygame.Rect(box).move(foot))
        return obj
    def masonry(bounds):
        r=pygame.Rect(bounds)
        image=wall(r.width,r.x+r.y)
        if r.height > 40:
            image=pygame.Surface((r.width,r.height+20),pygame.SRCALPHA)
            image.fill((45,48,43))
            for y in range(16,image.height,12):
                for x in range(-14 if y//12%2 else 0,r.width,28):
                    pygame.draw.rect(image,(108,109,98),(x+2,y,24,10))
                    pygame.draw.line(image,(151,145,119),(x+3,y),(x+23,y),2)
        place(image,(r.centerx,r.bottom),(-r.width//2,-r.height,r.width,r.height))
    floor(terrain,pygame.Rect(166,730,434,160),seed=2)
    floor(terrain,pygame.Rect(90,310,450,400),wooden=True,seed=3)
    floor(terrain,pygame.Rect(600,400,580,440),seed=4)
    floor(terrain,pygame.Rect(650,130,520,270),wooden=True,seed=5)
    # Service counter -> open-air sorting yard -> dry strongroom. Wide doors, no narrow maze.
    for bounds in ((0,0,1280,28),(0,0,28,960),(1252,0,28,960),
                   (0,920,178,40),(310,920,970,40),
                   (90,310,450,30),(90,340,28,370),(510,340,30,265),
                   (90,710,130,28),(362,710,178,28),
                   (570,400,30,220),(570,730,30,130),(600,840,580,30),
                   (1180,130,30,740),(650,130,530,30),(650,160,30,240),
                   (600,400,254,30),(1004,400,176,30)):
        masonry(bounds)
    place(art.prop('sign'),(247,888))
    for foot in ((162,917),(325,917)):
        place(road_prop('milestone'),foot,(-15,-15,30,18))
    place(furniture('desk'),(260,414),(-55,-28,110,28))
    place(furniture('shelf'),(450,370),(-43,-20,86,20))
    place(furniture('locker'),(151,386),(-25,-20,50,20))
    place(art.prop('burner'),(150,598),(-36,-20,72,20))
    place(road_prop('broken_crate'),(417,535),(-20,-14,40,20))
    place(furniture('chair'),(302,560))
    for kind,foot in (('red_cloth',(225,560)),('blue_shield',(488,650)),
                      ('wheel',(512,826)),('cart',(450,823)),('crate',(1128,471)),
                      ('crate',(651,478)),('supplies',(1118,790))):
        place(road_prop(kind),foot,(-24,-15,48,22) if kind=='crate' else None)
    place(furniture('desk'),(915,205),(-57,-30,114,30))
    for foot in ((730,203),(1097,205)): place(furniture('shelf'),foot,(-42,-20,84,20))
    place(art.prop('drawer'),(865,306),(-58,-30,116,30))
    gate=place(art.prop('gate'),(585,733))
    vault_gate=place(furniture('gate'),(929,432))
    rng=random.Random(161)
    for _ in range(95):
        x,y=rng.randrange(130,490),rng.randrange(440,675)
        pygame.draw.line(terrain,(167,150,111),(x,y),(x+7,y+2),2)
    env.patch(terrain,(150,601),(68,38),(29,27,26,125),5)
    # Boot marks from both search parties, with a dragged bundle leading to the burn pile.
    for i in range(18):
        pygame.draw.line(terrain,(72,64,50),(160+i*8,620-i*7),(165+i*8,621-i*7),3)
    clues=[
        Interactable('archive_search','Protagonista',(181,566),art.prop('papers'),(),prompt='[E] Examinar papéis queimados'),
        Interactable('archive_defense','Protagonista',(335,449),art.prop('defense'),(),prompt='[E] Ler relatório da retaguarda'),
        Interactable('archive_petition','Protagonista',(429,635),art.prop('petition'),(),prompt='[E] Ler petição dos atravessadores'),
        Interactable('archive_order','Protagonista',(865,321),art.prop('order'),(),prompt='[E] Abrir Gaveta 7'),
        Interactable('archive_forgetting','Protagonista',(1050,289),art.prop('forgetting'),(),prompt='[E] Examinar ficha chamuscada'),
    ]
    veteran=ArchiveVeteran((970,552),load)
    return {'name':'Depósito de Registros da Margem Seca','ambient_kind':'archive','terrain':terrain,
            'houses':[],'objects':[],'nature':[],'scenery':scenery,'npcs':[],
            'interactables':clues,'obstacles':obstacles,'base_obstacles':tuple(obstacles),
            'enemy_spawns':[],'exits':{'namar':pygame.Rect(178,930,132,30)},
            'spawn':{'namar':(246,862)},'veteran':veteran,'yard_gate':gate,'vault_gate':vault_gate,
            'yard_lock':pygame.Rect(570,620,30,110),'vault_lock':pygame.Rect(854,400,150,30),
            'arena_trigger':pygame.Rect(640,475,455,305),'combat_camera':(240,302),
            'memory_center':(870,287)}


def prepare_memory(region,load):
    """The old tollhouse command room, not a claim that the order was issued at the depot."""
    terrain=region['terrain'].copy(); terrain.fill((51,47,42))
    floor(terrain,pygame.Rect(615,120,585,340),wooden=True,seed=7)
    scenery=[]
    for image,foot in ((wall(585),(907,156)),(furniture('desk'),(865,235)),
                       (furniture('flag'),(1110,230)),(furniture('shelf'),(697,216))):
        scenery.append(env.anchored(image,foot))
    # A tactical bridge diagram on the table grounds the fragment in Namar.
    pygame.draw.lines(terrain,(180,156,108),False,[(809,243),(825,236),(853,243)],2)
    region['memory_terrain'],region['memory_scenery']=terrain,scenery
