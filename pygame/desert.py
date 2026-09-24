"""Deserto das Dunas: região explorável montada com o pacote Craftpix desértico."""
import random
import pygame
import environment as env
from items import consumable

WORLD = (2048, 1152)
ROOT = "sprites_meu/craftpix-891121-free-2d-rpg-desert-tileset/PNG/"

class Chest:
    def __init__(self, uid, position, loot, opened=False):
        self.uid, self.x, self.y, self.loot, self.opened = uid, *position, loot, opened

    @property
    def interaction_rect(self):
        return pygame.Rect(round(self.x - 30), round(self.y - 25), 60, 50).inflate(74, 74)

    @property
    def prompt(self):
        return "[E] Abrir baú" if not self.opened else "Baú já aberto"

    @property
    def hitbox(self):
        return pygame.Rect(round(self.x - 22), round(self.y - 14), 44, 28)

    def draw(self, canvas, camera):
        x, y = round(self.x - camera[0]), round(self.y - camera[1])
        env.shadow(canvas,(x,y+8),42,12)
        canvas.blit(self.frames[1 if self.opened else 0],(x-24,y-34))

def build(load, opened_chests=None):
    opened_chests = opened_chests or set()
    bg = load(ROOT + "bg.png")
    terrain = env.ground(WORLD,bg,391,((180,130,73),(226,186,117)))
    # Ondulações, cascalho e tufos secos em marcas determinísticas na areia.
    rng = random.Random(391)
    for _ in range(620):
        x, y = rng.randrange(WORLD[0]), rng.randrange(WORLD[1])
        shade = rng.choice([(197, 151, 83), (219, 174, 105), (231, 192, 126)])
        pygame.draw.arc(terrain, shade, (x, y, rng.randrange(12, 34), rng.randrange(5, 13)), .15, 2.8, 1)
        if rng.random() < .19:
            pygame.draw.ellipse(terrain, (152, 116, 70), (x + 3, y + 4, 3, 2))

    objects, nature, obstacles, scenery = [], [], [], []
    def sprite(file, scale=1.0):
        image = load(ROOT + file)
        if scale != 1:
            image = pygame.transform.scale(image, (round(image.width * scale), round(image.height * scale)))
        return image
    def place(image, pos, solid=None, layer=None):
        (nature if layer == "nature" else objects).append((image, pos))
        if solid:
            box=pygame.Rect(pos[0] + solid[0], pos[1] + solid[1], solid[2], solid[3])
            obstacles.append(box)
            env.patch(terrain,box.center,(max(35,image.width+25),max(25,image.height//3)),(131,105,65,42),pos[0])
            env.shadow(terrain,box.center,max(20,round(box.width*1.2)),max(8,box.height//2),37)

    # Estrada sinuosa desde a passagem da floresta, pelo oásis e ruínas, até o norte.
    main_path = [(1024, 0), (1010, 180), (780, 260), (620, 430), (670, 560), (900, 630), (1180, 650), (1450, 700), (1620, 870), (1720, 1152)]
    side_paths = [[(700, 500), (490, 650), (470, 760)], [(1220, 610), (1280, 440), (1370, 280)],
                  [(1450, 700), (1660, 610), (1880, 530)]]
    sand=env.worn_texture(bg,(215,174,108),42,18)
    path_mask=env.paths(terrain,[(main_path,90),*[(line,43) for line in side_paths]],sand,83)
    # Lajes desgastadas apenas junto às ruínas, em transição com a estrada de areia.
    env.paths(terrain,[([(1460,700),(1535,714),(1610,757)],45)],sprite('road_5.png',.5),92)

    # Dunas orgânicas usando as formações grandes do conjunto.
    for file, pos, scale in [("stones_10.png", (50, 110), .48), ("stones_11.png", (1280, 40), .42),
                              ("stones_12.png", (120, 765), .40), ("stones_10.png", (1580, 770), .35)]:
        image = sprite(file, scale); place(image, pos, (20, image.get_height() * .68, image.get_width() - 40, image.get_height() * .25), "nature")
    # Pedras e vegetação seca em margens e gargalos, mantendo corredores largos.
    for i, (file, x, y) in enumerate([
        ("stones_1.png", 350, 330), ("stones_2.png", 520, 510), ("stones_3.png", 700, 820),
        ("stones_4.png", 1770, 320), ("stones_5.png", 1840, 760), ("stones_6.png", 390, 970),
        ("stones_7.png", 1080, 840), ("stones_8.png", 600, 250), ("stones_9.png", 1500, 470),
    ]):
        image = sprite(file, .60); place(image, (x, y), (8, image.get_height() * .55, image.get_width() - 16, image.get_height() * .35))
    for i, (file, x, y) in enumerate([
        ("greenery_2.png", 300, 430), ("greenery_3.png", 470, 230), ("greenery_4.png", 780, 170),
        ("greenery_5.png", 650, 650), ("greenery_6.png", 1120, 760), ("greenery_7.png", 1860, 410),
        ("greenery_8.png", 350, 830), ("greenery_9.png", 1450, 930), ("greenery_10.png", 930, 720),
        ("tree_10.png", 250, 610), ("tree_11.png", 1710, 460),
    ]):
        image = sprite(file, .48 if "tree_" in file else .80)
        place(image, (x, y), (image.get_width() * .28, image.get_height() * .72, image.get_width() * .45, image.get_height() * .22), "nature")

    # Oásis central: margem decorativa e água profunda sólida.
    oasis = sprite("lake.png", .82); oasis_pos = (730, 315)
    env.patch(terrain,(oasis_pos[0]+oasis.width//2,oasis_pos[1]+oasis.height//2),(oasis.width+140,oasis.height+100),(114,131,68,40),771)
    terrain.blit(oasis,oasis_pos)
    obstacles.append(pygame.Rect(oasis_pos[0] + 55, oasis_pos[1] + 50, oasis.get_width() - 110, oasis.get_height() - 98))
    palms = [sprite("tree_2.png", .38), sprite("tree_5.png", .38), sprite("tree_7.png", .34)]
    for image, pos in zip(palms, [(690, 290), (1190, 340), (900, 505)]):
        place(image, pos, (image.get_width() * .35, image.get_height() * .76, image.get_width() * .3, image.get_height() * .18), "nature")
    # A terceira variação era um tronco cortado: usa uma palmeira na mesma base.
    old,palm_pos=nature[-1]
    palm=sprite('tree_2.png',.32)
    foot=(palm_pos[0]+old.width*.5,palm_pos[1]+old.height*.85)
    nature[-1]=(palm,(round(foot[0]-palm.width*.5),round(foot[1]-palm.height*.9)))

    # Ruínas antigas: ponto de interesse reservado para missão/evento futuro.
    ruin = sprite("building_3.png", .58); ruin_pos = (1435, 510)
    place(ruin, ruin_pos, (28, ruin.get_height() * .70, ruin.get_width() - 56, ruin.get_height() * .26))
    # Pequena construção secundária e carroça abandonada dão escala ao caminho.
    shelter = sprite("decor_1.png", .43); place(shelter, (290, 700), (22, shelter.get_height() * .76, shelter.get_width() - 44, shelter.get_height() * .18))
    wagon = sprite("decor_8.png", .50); place(wagon, (1730, 620), (18, wagon.get_height() * .72, wagon.get_width() - 36, wagon.get_height() * .22))

    # Grupos de cascalho e vegetação baixa acompanham as formações já sólidas.
    pebbles=[sprite(f'stones_{i}.png',.14) for i in (1,3,5)]
    dry=[sprite('greenery_6.png',.28),sprite('greenery_10.png',.25)]
    for i,(cx,cy) in enumerate([(400,380),(555,549),(740,861),(1810,365),(1880,801),
                               (430,1006),(1120,878),(636,290),(1540,514),(320,740),(1810,700)]):
        env.patch(terrain,(cx,cy),(140,75),(153,113,62,44),i)
        for j,(dx,dy) in enumerate([(-38,8),(-20,25),(42,-5),(56,18),(19,34)]):
            foot=(cx+dx,cy+dy)
            if path_mask.get_at(foot): continue
            im=pebbles[j%3] if j%2 else dry[j%2]
            scenery.append(env.anchored(im,foot,False,1 if j%2==0 else 0,i))
    for i,foot in enumerate([(730,482),(792,520),(870,530),(1090,535),(1200,470),(1130,324),(878,310)]):
        for j in range(3):
            im=dry[j%2]
            scenery.append(env.anchored(im,(foot[0]+j*14,foot[1]+(j%2)*9),False,1,i))
    # Madeira, ânfora e ossada usam os PNGs existentes; ficam junto às composições.
    for file,scale,foot in [('decor_4.png',.24,(372,816)),('decor_6.png',.26,(1508,824)),
                            ('decor_4.png',.18,(1795,730))]:
        scenery.append(env.anchored(sprite(file,scale),foot))

    # Baús isolados em desvios que recompensam exploração.
    chest_data = [
        Chest("desert_chest_oasis", (1215, 365), consumable("herb", 2), "desert_chest_oasis" in opened_chests),
        Chest("desert_chest_ruins", (1580, 660), consumable("ether", 2), "desert_chest_ruins" in opened_chests),
        Chest("desert_chest_hidden", (480, 745), consumable("herb", 2), "desert_chest_hidden" in opened_chests),
    ]
    for chest in chest_data:
        sheet=load('assets/shared/chest_01.png')
        chest.frames=[env.crop(sheet,(0,0,16,16),3),env.crop(sheet,(48,0,16,16),3)]
        obstacles.append(chest.hitbox)

    # Limite norte aponta às ruínas da próxima região; acesso não implementado.
    exits = {"forest": pygame.Rect(965, 0, 120, 50), "ruins_future": pygame.Rect(1650, WORLD[1] - 48, 150, 48)}
    return {
        "name": "Deserto das Dunas", "terrain": terrain, "houses": [], "objects": objects,
        "scenery":scenery,"ambient_kind":"desert",
        "water":[{"rect":pygame.Rect(oasis_pos[0]+90,oasis_pos[1]+75,oasis.width-180,oasis.height-142),"color":(165,224,219),"seed":91}],
        "nature": nature, "obstacles": obstacles, "exits": exits,
        "spawn": {"forest": (1025, 105)}, "enemy_spawns": [
            ("desert_scout", (670, 560)), ("desert_scout", (1690, 390)),
            ("dune_lancer", (1300, 780)), ("dune_lancer", (1890, 900)),
        ], "interactables": chest_data, "future_poi": pygame.Rect(1380, 475, 300, 300),
        "future_exit_notified": False,
    }
