"""Cenário determinístico: terreno pré-renderizado e objetos ordenados pelos pés."""
import math
import random
import pygame
import environment as env

HOMES = [(4, 740, 325), (3, 1160, 310), (2, 1370, 230),
         (1, 730, 665), (3, 1170, 730), (1, 420, 345), (2, 1510, 725)]


def terrain(size, asset):
    rng = random.Random(41)
    grass=[env.resize(asset(f'2 Objects/5 Grass/{i}.png'),2) for i in range(1,7)]
    ground=env.ground(size,asset('1 Tiles/FieldsTile_38.png'),41,((67,98,57),(114,140,73)),grass)
    routes = [([(0, 570), (550, 570), (850, 565), (1030, 565), (1430, 565), (2048, 600)], 68),
              ([(1020, 0), (1020, 390), (1030, 565), (1020, 840), (980, 1152)], 64)]
    for _, x, y in HOMES:
        door = (x + 65, y + 125)
        routes.append(([door, (door[0], 565)], 30))
    routes.append(([(1300, 520), (1320, 670), (1450, 690)], 36))
    paving=env.worn_texture(asset('1 Tiles/FieldsTile_11.png'),(171,148,104),65,41)
    env.paths(ground,routes,paving,41,edge_tiles=grass)
    plaza=pygame.transform.grayscale(asset('1 Tiles/FieldsTile_11.png'))
    plaza.fill((22,23,8),special_flags=pygame.BLEND_RGB_ADD)
    plaza=env.worn_texture(plaza,(163,166,145),105,42)
    env.paths(ground,[],plaza,45,[((1025,561),(265,205))])
    for i,x,y in HOMES:
        house=asset(f'2 Objects/7 House/{i}.png')
        foot=(x+house.width//2,y+house.height-20)
        env.patch(ground,foot,(house.width+44,58),(116,106,70,95),x)
        env.shadow(ground,(foot[0]+8,foot[1]),house.width-8,28,45)
    # Um piso gasto sob as bancas liga comércio e horta à estrada.
    env.paths(ground,[],paving,55,[((1388,665),(245,70))])
    # Horta ao lado da feira: sulcos e folhas em fileiras.
    pygame.draw.rect(ground, (100, 77, 48), (1350, 650, 155, 85), border_radius=6)
    for y in range(661, 730, 17):
        pygame.draw.line(ground, (72, 59, 41), (1358, y + 7), (1497, y + 7), 3)
        for x in range(1361, 1495, 16):
            pygame.draw.ellipse(ground, (52, 98, 58), (x, y, 10, 7))
            pygame.draw.line(ground, (146, 168, 80), (x + 5, y + 5), (x + 3, y - 2), 2)
    return ground


def tree(seed):
    rng = random.Random(seed)
    s = pygame.Surface((100, 126), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (27, 43, 30, 75), (8, 105, 88, 16))
    pygame.draw.polygon(s, (65, 48, 35), [(40, 117), (58, 117), (53, 56), (44, 56)])
    pygame.draw.line(s, (145, 101, 57), (48, 112), (48, 66), 4)
    pygame.draw.line(s, (86, 63, 39), (47, 88), (30, 65), 6)
    for x, y, r in [(30, 67, 25), (68, 63, 25), (48, 38, 31), (45, 66, 32)]:
        pygame.draw.circle(s, (35, 70, 47), (x, y), r)
        pygame.draw.circle(s, (48, 92, 52), (x - 2, y - 5), r - 4)
    for _ in range(220):
        x, y = rng.randrange(8, 90), rng.randrange(10, 96)
        if s.get_at((x, y)).a and s.get_at((x, y)).g > 65:
            pygame.draw.rect(s, rng.choice([(65, 112, 59), (82, 130, 67), (111, 148, 75), (39, 83, 48)]), (x, y, rng.randrange(2, 6), 3))
    return s


def bench():
    s = pygame.Surface((60, 40), pygame.SRCALPHA)
    for x in (9, 47):
        pygame.draw.rect(s, (57, 47, 34), (x, 14, 5, 23))
    for y in (4, 12, 23):
        pygame.draw.rect(s, (89, 59, 36), (4, y, 52, 7))
        pygame.draw.line(s, (179, 131, 76), (5, y), (54, y), 2)
    return s


def fence(width):
    s = pygame.Surface((width, 34), pygame.SRCALPHA)
    for y in (12, 23):
        pygame.draw.rect(s, (111, 76, 44), (0, y, width, 5))
    for x in range(4, width - 4, 16):
        pygame.draw.polygon(s, (167, 125, 74), [(x, 32), (x, 7), (x + 3, 2), (x + 7, 7), (x + 7, 32)])
        pygame.draw.line(s, (202, 161, 102), (x + 1, 8), (x + 1, 29))
    return s


def build(asset, flowerbed, fountain, sign, bush, load):
    houses = [(asset(f'2 Objects/7 House/{i}.png'), (x, y)) for i, x, y in HOMES]
    objects, nature = [], []
    woods=env.free_woods(load)
    tree_sprite=env.tint(env.resize(woods['tree'],2),(222,237,205))
    bush_sprite=env.tint(env.resize(woods['bush'],1.5),(227,238,202))
    obstacles = [pygame.Rect(x + 14, y + im.get_height() - 48, im.get_width() - 28, 35) for im, (x, y) in houses]
    def solid(image, pos, box):
        objects.append((image, pos))
        obstacles.append(pygame.Rect(box).move(pos))
    solid(fountain(), (976, 452), (10, 49, 76, 28))
    for pos in [(902, 615), (1090, 615), (893, 452), (1098, 451)]:
        solid(bench(), pos, (4, 24, 52, 12))
    for pos in [(870, 495), (1160, 493), (915, 659), (1110, 659)]:
        objects.append((asset('2 Objects/3 Decor/10.png'), pos))
    for i, pos in enumerate([(1270, 600), (1400, 593)]):
        im = asset(f'2 Objects/6 Tent/{i + 1}.png')
        solid(im, pos, (9, im.get_height() - 24, im.get_width() - 18, 20))
        for j in range(3):
            objects.append((asset(f'2 Objects/4 Box/{j + 1}.png'), (pos[0] + j * 23, pos[1] + 67)))
    objects.append((sign(), (1240, 640)))
    for i, (x, y) in enumerate([(735, 465), (1175, 471), (731, 808), (1180, 887), (864, 694), (1075, 696)]):
        nature.append((flowerbed(i), (x, y)))
    # Objetos junto às paredes, contidos no footprint sólido existente das casas.
    for n,(house,(x,y)) in enumerate(houses):
        objects.append((env.resize(asset('2 Objects/4 Box/1.png'),1.4),(x+16,y+house.height-29)))
        objects.append((env.resize(asset(f'2 Objects/4 Box/{3+n%3}.png'),1.25),(x+house.width-39,y+house.height-25)))
        for j in range(4):
            plant=env.resize(asset(f'2 Objects/5 Grass/{j+1}.png'),2)
            nature.append((plant,(x+20+j*(house.width-35)//4,y+house.height-19)))
    objects.append((env.resize(asset('2 Objects/3 Decor/1.png'),1.5),(1490,608)))
    objects.append((env.resize(asset('2 Objects/3 Decor/6.png'),1.5),(1330,716)))
    for pos, width in [((698, 640), 120), ((842, 640), 66), ((1305, 757), 208), ((1315, 622), 62)]:
        solid(fence(width), pos, (0, 27, width, 6))
    rng = random.Random(24)
    tree_positions = [(628, 348), (675, 251), (873, 298), (1293, 349), (1330, 228),
                      (608, 679), (630, 797), (866, 784), (1296, 816), (1480, 392), (1505, 640)]
    for x in range(180, 1900, 95):
        tree_positions.extend([(x, rng.randrange(35, 140)), (x, rng.randrange(990, 1020))])
    for i, pos in enumerate(tree_positions):
        im = tree_sprite
        nature.append((im, (pos[0]+49-im.width//2,pos[1]+118-im.height)))
        obstacles.append(pygame.Rect(pos[0] + 40, pos[1] + 108, 18, 10))
        if i % 2 == 0:
            nature.append((bush_sprite, (pos[0] - 19, pos[1] + 80)))
    return houses, objects, nature, obstacles
