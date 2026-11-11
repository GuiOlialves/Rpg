"""The dry bank of Namar: occupied masonry, civilian ruins and two short routes."""
import random
import pygame
import environment as env
from world import asset_art
from entities.interactable import Interactable
from entities.namar_survivor import NamarSurvivor, RecordsCarrier
from world.regions import namar_art as art
from world.regions.watchpost_art import floor, wall, prop as post_prop
from world.regions.old_road_art import prop as road_prop

WORLD = (1536, 960)
PROTECT_SPAWNS = ((820, 510), (1130, 680))
PURSUE_SPAWNS = ((900, 350), (1130, 310))


def build(load, opened_chests=None):
    rng = random.Random(121)
    tile = load('sprites_meu/vila_tile-set/1 Tiles/FieldsTile_11.png')
    terrain = env.ground(WORLD, tile, 121, ((98, 94, 77), (147, 139, 108)))
    scenery, obstacles = [], []

    def place(image, foot, box=None):
        scenery.append(env.anchored(image, foot))
        env.shadow(terrain, foot, max(15, image.width//2), 9, 30)
        if box: obstacles.append(pygame.Rect(box).move(foot))

    def masonry(rect):
        rect = pygame.Rect(rect)
        image = wall(rect.width, rect.x)
        if rect.height > 40:
            # Tall side walls must fill their collision footprints.
            image = pygame.Surface((rect.width, rect.height+20), pygame.SRCALPHA)
            image.fill((44, 48, 43))
            for y in range(18, image.height, 12):
                for x in range(-14 if y//12 % 2 else 0, rect.width, 28):
                    pygame.draw.rect(image, (106, 110, 99), (x+2,y,24,10))
                    pygame.draw.line(image, (151, 145, 119), (x+3,y), (x+23,y), 2)
            pygame.draw.rect(image, (151, 145, 119), (0,8,rect.width,8))
        place(image, (rect.centerx, rect.bottom),
              (-rect.width//2, -rect.height, rect.width, rect.height))

    # River and a clearly collapsed bridge are the eastern skyline, not a woodland.
    river = pygame.Rect(1300, 0, 236, 960)
    asset_art.water(terrain,river,121)
    asset_art.bank(terrain,1272,0,960)
    obstacles += [pygame.Rect(1276, 0, 260, 960)]
    floor(terrain, pygame.Rect(1138, 455, 134, 142), seed=5)
    for x, y in ((1320, 506), (1382, 542), (1450, 501)):
        pygame.draw.polygon(terrain, (23, 44, 49), [(x+7,y+41),(x+58,y+34),(x+64,y+77),(x+12,y+84)])
        pygame.draw.polygon(terrain, (63, 72, 67), [(x,y+28),(x+47,y+20),(x+58,y+63),(x+9,y+70)])
        pygame.draw.polygon(terrain, (93, 99, 88), [(x, y), (x+44, y-12), (x+58, y+38), (x+9, y+45)])
        pygame.draw.lines(terrain, (154, 149, 125), False, [(x+3, y+4), (x+38, y-4), (x+47, y+12)], 3)
        for sy in (13,25,38):
            pygame.draw.line(terrain,(56,66,62),(x+12,y+sy),(x+43,y+sy-5),2)
        pygame.draw.lines(terrain,(49,56,51),False,[(x+20,y),(x+26,y+12),(x+17,y+24),(x+27,y+38)],3)
    # Stone route, roofless tollhouse, former bakery and shelter behind a low wall.
    floor(terrain, pygame.Rect(150, 770, 940, 94), seed=1)
    floor(terrain, pygame.Rect(680, 408, 460, 372), seed=2)
    floor(terrain, pygame.Rect(574, 166, 608, 253), seed=3)
    floor(terrain, pygame.Rect(244, 473, 300, 230), seed=4)
    floor(terrain, pygame.Rect(544, 722, 206, 113), wooden=True, seed=6)
    floor(terrain, pygame.Rect(226, 281, 276, 143), wooden=True, seed=7)
    floor(terrain,pygame.Rect(1195,40,76,160),seed=9)
    for rect in ((0, 0, 1188, 40), (1264,0,272,40), (0, 916, 1536, 44), (0, 0, 32, 775),
                 (0, 875, 32, 85)):
        obstacles.append(pygame.Rect(rect)); pygame.draw.rect(terrain, (73, 77, 67), rect)
    for rect in ((574, 164, 610, 38), (574, 202, 46, 94), (574, 370, 46, 50),
                 (1150, 202, 32, 98), (1150, 365, 32, 55),
                 (244, 466, 298, 36), (244, 500, 38, 90), (244, 650, 38, 54),
                 (210, 250, 302, 30), (210, 280, 24, 140),
                 (546, 705, 78, 26), (695, 705, 63, 26)):
        masonry(rect)
    for foot in ((555, 345), (615, 414), (1110, 420), (530, 688)):
        place(road_prop('wall'), foot, (-28, -16, 56, 22))
    for foot in ((1025, 572), (720, 469)):
        place(art.prop('barricade'), foot, (-58, -24, 116, 24))
    # Gaps around barricades permit a flank, and the upper ruined doorway opens a second approach.
    place(art.prop('oven'), (334, 565), (-32, -38, 64, 38))
    place(post_prop('desk'), (736, 253), (-57, -35, 114, 35))
    place(post_prop('shelf'), (1066, 231), (-40, -20, 80, 20))
    place(road_prop('cart'), (875, 776), (-58, -45, 116, 45))
    supplies = env.anchored(art.prop('sacks'), (942, 790)); scenery.append(supplies)
    for kind, foot in (('broken_crate', (438, 385)), ('wheel', (490, 796)),
                       ('red_cloth', (966, 220)), ('blue_shield', (1224, 675)),
                       ('bedroll', (602, 812)), ('crate', (1110, 742)), ('milestone', (165, 738))):
        place(road_prop(kind), foot)
    place(art.prop('sign'), (654, 164))
    place(art.prop('standard'), (1080, 197), (-8,-12,16,12))
    for foot in ((239, 431), (510, 447), (602, 322), (1178, 444), (1215, 550)):
        place(road_prop('wall'), foot)
    for x,y in ((293,320),(474,400),(938,389)):
        pygame.draw.line(terrain,(65,55,43),(x-35,y-21),(x+31,y+24),9)
        pygame.draw.line(terrain,(133,104,65),(x-35,y-24),(x+29,y+21),3)
        pygame.draw.line(terrain,(50,48,39),(x+8,y-21),(x-19,y+29),6)
    for i in range(110):
        x,y=rng.choice(((rng.randrange(548,630),rng.randrange(290,440)),
                        (rng.randrange(1130,1220),rng.randrange(375,455)),
                        (rng.randrange(232,510),rng.randrange(421,459))))
        pygame.draw.rect(terrain,(91,96,84),(x,y,6,4))
        pygame.draw.line(terrain,(153,146,117),(x,y),(x+4,y),2)
    # Scorch marks, dropped nails, bullet chips and household shards.
    for i in range(85):
        x, y = rng.randint(285, 1180), rng.randint(215, 860)
        pygame.draw.line(terrain, rng.choice(((81, 77, 63), (173, 151, 103), (60, 64, 59))),
                         (x, y), (x+rng.randint(3, 10), y+2), 2)
    for pos in ((505, 609), (844, 424), (1050, 830)):
        env.patch(terrain, pos, (74, 37), (38, 36, 30, 130), 22)
    clues = [
        Interactable('namar_military', 'Protagonista', (905, 276), art.prop('ledger'),
            ('Namar. Controle de travessia. A marca da escolta vermelha é a mesma da placa R-17.',
             'A página da operação foi arrancada. Resta uma anotação: "ordens — guardar segunda via".'),
            prompt='[E] Examinar livro de travessia'),
        Interactable('namar_civilian', 'Protagonista', (451, 611), art.prop('civilian'),
            ('Contas de uma padaria. Farinha, lenha, nomes de famílias. A última entrega nunca foi paga.',
             'Sob os números: "a travessia fechou com gente ainda na fila". A tinta termina numa mancha.'),
            prompt='[E] Examinar contas da padaria'),
        Interactable('namar_cache', 'Protagonista', (371, 339), road_prop('supplies'),
            ('Um embrulho escondido sob a calha caída. As ervas ainda estão secas.',),
            prompt='[E] Examinar embrulho'),
    ]
    mara = NamarSurvivor('mara', 'Mara', (820, 660), load)
    teo = NamarSurvivor('teo', 'Téo', (920, 700), load)
    carrier = RecordsCarrier('namar_carrier', 'Portador de registros', (1150, 270), {'default': ()},
                  load('assets/vale_characters/red_soldier_2_idle.png'),
                  run_sprite=load('assets/vale_characters/red_soldier_2_walk.png'), frame_size=32, draw_size=64)
    carrier.enabled = False
    return {'name': 'Ponte de Namar — Margem Seca', 'ambient_kind': 'namar', 'terrain': terrain,
            'houses': [], 'objects': [], 'nature': [], 'scenery': scenery,
            'obstacles': obstacles, 'water': [{'rect': river, 'color': (78, 125, 123)}],
            'npcs': [mara, teo], 'mara': mara, 'teo': teo, 'carrier': carrier,
            'supplies_prop': supplies, 'interactables': clues, 'enemy_spawns': [],
            'exits': {'pursuit': pygame.Rect(0, 780, 32, 90)},
            'spawn': {'pursuit': (120, 825), 'archive':(1230,90)}, 'choice_trigger': pygame.Rect(700, 600, 325, 142),
            'memory_center': (857, 308)}
