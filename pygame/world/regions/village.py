"""Cenário determinístico: terreno pré-renderizado e objetos ordenados pelos pés."""
import random
import pygame
import environment as env
from core.config import WORLD
from entities.interactable import Interactable
from entities.npc import NPC
from ui.civilian_art import civilian_sheet

HOMES = [(4, 740, 325), (3, 1160, 310), (2, 1370, 230),
         (1, 730, 665), (3, 1170, 730), (1, 475, 345), (2, 1510, 725)]


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


def build(asset, flowerbed, sign, load):
    houses = [(asset(f'2 Objects/7 House/{i}.png'), (x, y)) for i, x, y in HOMES]
    objects, nature = [], []
    exterior = load('assets/prologue/exterior.png')
    fence_sheet = load('assets/prologue/fences.png')
    bench_image = pygame.transform.scale_by(
        load('assets/prologue/mystic_objects.png').subsurface((160, 0, 32, 16)), 2)

    def picket(width):
        image = pygame.Surface((width, 32), pygame.SRCALPHA)
        middle = pygame.transform.scale_by(fence_sheet.subsurface((32, 0, 16, 16)), 2)
        for x in range(0, width, 32):
            image.blit(middle, (x, 0))
        image.blit(pygame.transform.scale_by(fence_sheet.subsurface((16, 0, 16, 16)), 2), (0, 0))
        image.blit(pygame.transform.scale_by(fence_sheet.subsurface((48, 0, 16, 16)), 2), (width - 32, 0))
        return image
    woods=env.free_woods(load)
    tree_sprite=env.tint(env.resize(woods['tree'],2),(222,237,205))
    bush_sprite=env.tint(env.resize(woods['bush'],1.5),(227,238,202))
    obstacles = []
    for (house_id, x, y), (image, _) in zip(HOMES, houses):
        width, height = image.get_size()
        if (house_id, x, y) == (1, 475, 345):
            # Split the front wall around its doorway and keep only visible
            # wall/foundation footprints solid.
            obstacles.extend((
                pygame.Rect(x + 10, y + height - 40, width - 20, 10),
                pygame.Rect(x + 10, y + height - 29, 25, 20),
                pygame.Rect(x + 83, y + height - 29, width - 93, 20),
            ))
        else:
            # Decorative houses collide at their foundation, not across a
            # large rectangle covering empty facade space.
            obstacles.append(pygame.Rect(x + 12, y + height - 25,
                                         width - 24, 16))
    def solid(image, pos, box):
        objects.append((image, pos))
        obstacles.append(pygame.Rect(box).move(pos))
    well = pygame.transform.scale_by(exterior.subsurface((0, 496, 40, 44)), 2)
    solid(well, (984, 442), (10, 59, 60, 28))
    for pos in [(902, 615), (1090, 615), (893, 452), (1098, 451)]:
        solid(bench_image, pos, (4, 20, 56, 10))
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
        objects.append((asset(f'2 Objects/4 Box/{1+n%3}.png'),(x+12,y+house.height-29)))
        if n % 2:
            objects.append((asset(f'2 Objects/4 Box/{3+n%3}.png'),(x+house.width-29,y+house.height-25)))
        for j in range(2):
            plant=env.resize(asset(f'2 Objects/5 Grass/{j+1}.png'),2)
            nature.append((plant,(x+5+j*(house.width-20),y+house.height-19)))
    objects.append((env.resize(asset('2 Objects/3 Decor/1.png'),1.5),(1490,608)))
    objects.append((env.resize(asset('2 Objects/3 Decor/6.png'),1.5),(1330,716)))
    for pos, width in [((698, 640), 120), ((842, 640), 66), ((1305, 757), 208), ((1315, 622), 62)]:
        solid(picket(width), pos, (0, 27, width, 6))
    # Front garden frames the starting house without crossing the exit lane.
    for pos, width in [((412, 456), 72), ((587, 456), 64)]:
        solid(picket(width), pos, (0, 27, width, 6))
    for pos in [(433, 435), (593, 437), (704, 417), (879, 390)]:
        nature.append((bush_sprite, pos))
    for n, pos in enumerate([(421, 475), (599, 475), (672, 506), (807, 486)]):
        nature.append((flowerbed(n), pos))
    rng = random.Random(24)
    tree_positions = [(628, 348), (675, 251), (873, 298), (1293, 349), (1330, 228),
                      (608, 679), (630, 797), (866, 784), (1296, 816), (1480, 392), (1505, 640),
                      (260, 350), (245, 680)]
    for x in range(180, 1900, 95):
        tree_positions.extend([(x, rng.randrange(35, 140)), (x, rng.randrange(990, 1020))])
    for i, pos in enumerate(tree_positions):
        im = tree_sprite
        nature.append((im, (pos[0]+49-im.width//2,pos[1]+118-im.height)))
        obstacles.append(pygame.Rect(pos[0] + 40, pos[1] + 108, 18, 10))
        if i % 2 == 0:
            nature.append((bush_sprite, (pos[0] - 19, pos[1] + 80)))
    return houses, objects, nature, obstacles


def build_playable(load):
    """Assemble the existing village map with its current NPCs and exits."""
    def asset(path):
        return load("sprites_meu/vila_tile-set/" + path)

    def make_flowerbed(seed=0):
        sheet = load('assets/prologue/exterior.png')
        surface = pygame.Surface((96, 42), pygame.SRCALPHA)
        for i in range(4):
            flower = sheet.subsurface((144 + (i + seed) % 3 * 16, 768, 16, 32))
            surface.blit(flower, (i * 22 + 4, (i % 2) * 6))
        return surface

    def make_sign():
        return env.resize(env.free_woods(load)["sign"], 3)

    houses, objects, nature, obstacles = build(asset, make_flowerbed, make_sign, load)
    objects.append((make_sign(), (1915, 535)))
    entry = Interactable(
        "starting_house_entry", "Casa", (540, 470),
        pygame.Surface((1, 1), pygame.SRCALPHA), (),
        prompt="[E] Entrar", interaction_radius=76, transition_to="home",
        transition_on_interact=True)
    entry.visual_depth = 470
    npcs = [
        NPC("alden", "Alden", (1780, 560), {
            "default": ["A estrada da floresta está inquieta."],
            "AVAILABLE": ["Pedi ajuda, mas ela ainda não chegou.", "Evitem a trilha da floresta por enquanto."],
            "ACTIVE": ["O morador contou sobre os Slimes? Fique nos caminhos abertos."],
            "COMPLETED": ["Você voltou. Preciso conferir a situação antes de conversarmos melhor."],
            "REWARDED": ["Obrigado novamente pela ajuda."],
            "BOSS_DONE": ["A floresta está mais segura, e o caminho ao norte voltou a ser acessível."]
        }, civilian_sheet(load, "elder"), frame_size=32, draw_size=64),
        NPC("mira", "Mira", (1030, 420), {
            "default": ["Encontraram um estranho desacordado perto da estrada ontem.",
                        "Hoje a praça está mais quieta do que de costume."]
        }, civilian_sheet(load, "shopkeeper"), frame_size=32, draw_size=64),
        NPC("tomas", "Tomas", (1430, 540), {
            "default": ["Os Slimes têm rondado a trilha da floresta.",
                        "Ouvi que pediram ajuda, mas ainda vai demorar."]
        }, civilian_sheet(load, "worker"), frame_size=32, draw_size=64),
    ]
    for npc in npcs:
        obstacles.append(npc.hitbox)
    npcs[0].quest_id = "forest_trouble"
    npcs[0].quest_effects_enabled = False
    return {
        "name": "Vila do Vale", "terrain": terrain(WORLD, asset), "houses": houses,
        "ambient_kind": "village", "objects": objects, "nature": nature,
        "fountain_effect": False,
        "obstacles": obstacles,
        "exits": {"forest": pygame.Rect(1960, 520, 88, 115)},
        "spawn": {"forest": (1850, 575), "home": (540, 490)},
        "enemy_spawns": [], "npcs": npcs, "interactables": [entry],
    }
