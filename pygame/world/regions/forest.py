"""Floresta Mística: trilhas texturizadas, bosques e margens compostas."""
import math
import random
import pygame
import environment as env
from entities.interactable import Interactable
from story.blue_march import blue_commander_sprite

WORLD=(2048,1152)
TREES=[(175,120),(320,245),(525,72),(820,155),(1060,105),(1120,270),(450,410),
       (170,780),(390,930),(900,950),(1130,790),(1570,680),(1840,770),(1930,980)]
ROCKS=[(405,470),(780,620),(610,770),(1160,520),(1290,760),(1800,530),(1570,890),(420,1070)]
ROUTES=[([(0,575),(290,575),(505,520),(730,480),(930,490),(1080,420),(1210,300),(1170,205),(1170,70),(1245,45),(1250,0)],68),
        ([(690,485),(680,300),(590,185)],36), ([(930,490),(760,650),(690,855)],42),
        ([(1080,420),(1320,485),(1650,520)],40)]


def build(load):
    rng=random.Random(77)
    woods=env.free_woods(load)
    grass_details=[env.tint(env.resize(load(f'sprites_meu/vila_tile-set/2 Objects/5 Grass/{i}.png'),2),(162,205,183)) for i in range(1,7)]
    terrain=env.ground(WORLD,load('sprites_meu/mystic_woods_free_2.2/sprites/tilesets/grass.png'),77,
                       ((43,78,55),(91,119,68)),grass_details)
    dirt=env.worn_texture(load('sprites_meu/vila_tile-set/1 Tiles/FieldsTile_11.png'),(141,122,85),24,77)
    path_mask=env.paths(terrain,ROUTES,dirt,77,
        [((680,840),(260,150)),((1020,690),(225,135)),((470,190),(190,115))],grass_details)
    objects,nature,obstacles,scenery=[],[],[],[]
    trunk=env.tint(env.resize(woods['tree'],3),(192,220,195))
    tree=pygame.Surface((248,270),pygame.SRCALPHA)
    crown=trunk.subsurface((0,0,144,138)).copy()
    tree.blit(env.tint(crown,(190,215,205)),(0,54))
    tree.blit(env.tint(crown,(215,229,211)),(104,34))
    tree.blit(trunk,(52,78))
    tree.blit(crown,(46,2))
    groves=[tree,env.resize(pygame.transform.flip(tree,True,False),.9),env.resize(tree,1.08)]
    sapling=env.tint(env.resize(woods['sapling'],2),(194,224,194))
    bush=env.tint(env.resize(woods['bush'],1.5),(188,213,180))
    # Troncos ancorados exatamente nos antigos pontos de colisão.
    for i,(x,y) in enumerate(TREES):
        box=pygame.Rect(x+14,y+52,25,16); obstacles.append(box)
        foot=box.center
        env.patch(terrain,foot,(245,125),(23,55,39,42),i)
        env.shadow(terrain,foot,100,26,42)
        scenery.append(env.anchored(groves[i%3],foot,True,1,i))
        if i%3!=1:
            scenery.append(env.anchored(sapling,(foot[0]-10,foot[1]-4),True,1,i+2))
        for j in range(21):
            angle=rng.uniform(0,math.tau); radius=rng.randrange(35,135)
            px,py=round(foot[0]+math.cos(angle)*radius),round(foot[1]+math.sin(angle)*radius*.5)
            if 0<=px<WORLD[0] and 0<=py<WORLD[1] and not path_mask.get_at((px,py)):
                plant=bush if j%3==0 else grass_details[j%6]
                scenery.append(env.anchored(plant,(px,py),False,1 if j%4==0 else 0,j))
    # Copas periféricas têm raízes fora do mapa, sem novos bloqueios de circulação.
    for side in ('north','south','west','east'):
        span=WORLD[0] if side in ('north','south') else WORLD[1]
        for i,v in enumerate(range(-35,span+80,83)):
            if side=='north' and 1130<v<1360: continue
            if side=='west' and 440<v<730: continue
            if side=='north': foot=(v,-8)
            elif side=='south': foot=(v,WORLD[1]+45+rng.randrange(30))
            elif side=='west': foot=(-38,v)
            else: foot=(WORLD[0]+38,v)
            im=trunk if i%3 else env.resize(trunk,1.2)
            if side=='north':
                crown=im.subsurface((0,0,im.width,im.height*2//3)).copy()
                scenery.append(env.Scenery(crown,(v-crown.width//2,-55),-10,False))
            else: scenery.append(env.anchored(im,foot,True))
    for x,y in [(275,520),(570,410),(840,275),(1180,720),(1460,570),(1730,650),(510,1000),(1320,900),(1870,550),(300,865)]:
        env.patch(terrain,(x+35,y+35),(110,65),(27,61,40,38),x)
        scenery.append(env.anchored(env.resize(bush,.75),(x+13,y+26)))
        scenery.append(env.anchored(env.resize(bush,.8),(x+59,y+29)))
        scenery.append(env.anchored(bush,(x+35,y+40),False,1,x*.1))
        for dx,dy in [(-27,12),(34,-7),(55,17)]:
            scenery.append(env.anchored(grass_details[(x+dx)%6],(x+35+dx,y+40+dy)))
    rock=env.resize(woods['rock'],2)
    for x,y in ROCKS:
        box=pygame.Rect(x+4,y+18,24,12); obstacles.append(box)
        env.patch(terrain,box.center,(68,37),(107,113,71,65),x)
        env.shadow(terrain,box.center,29,9,45)
        scenery.append(env.anchored(rock,box.center))
        scenery.append(env.anchored(grass_details[x%6],(x-10,y+29)))
    lake=pygame.Rect(1360,120,540,330); shallow=pygame.Rect(1200,95,210,92)
    water=[env.lake(terrain,lake.inflate(-30,-24),310),env.lake(terrain,shallow.inflate(-20,-12),311,(30,20))]
    for x,y in [(1390,155),(1700,270),(1510,420),(1810,385)]:
        obstacles.append(pygame.Rect(x,y,28,22))
        scenery.append(env.anchored(rock,(x+14,y+22)))
    for x,y in [(1352,211),(1342,399),(1530,487),(1750,485),(1930,229),(1870,105),(1590,88),(1320,213)]:
        env.patch(terrain,(x,y),(75,38),(73,132,91,75),x)
        for j in range(4):
            scenery.append(env.anchored(grass_details[j],(x+j*9-15,y+rng.randrange(-6,7)),False,1,j))
        if x%3==0: scenery.append(env.anchored(bush,(x+22,y-3)))

    blue_idle = load('sprites_meu/Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/Units/Blue Units/Warrior/Warrior_Idle.png')
    red_idle = load('sprites_meu/Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/Units/Red Units/Warrior/Warrior_Idle.png')
    blue_frame = blue_idle.subsurface((0, 0, 192, 192)).copy()
    red_frame = red_idle.subsurface((0, 0, 192, 192)).copy()
    commander_sheet = blue_commander_sprite(load)
    commander_frame = commander_sheet.subsurface((0, 0, 32, 32)).copy()
    commander_fallen = pygame.transform.rotate(
        pygame.transform.scale(commander_frame, (72, 72)), -76)
    fallen_blue = pygame.transform.rotate(
        pygame.transform.scale_by(blue_frame, 0.48), 72)
    blue_sword = pygame.transform.rotate(
        pygame.transform.scale_by(blue_frame.subsurface((116, 66, 36, 54)), 0.9), 48)
    blue_shield = pygame.transform.rotate(
        pygame.transform.scale_by(blue_frame.subsurface((56, 88, 42, 48)), 0.86), -24)
    red_insignia = pygame.transform.scale(
        red_frame.subsurface((59, 91, 34, 42)), (24, 30))
    transparent = pygame.Surface((1, 1), pygame.SRCALPHA)
    battlefield_body = Interactable(
        'battlefield_body', 'Protagonista', (310, 565), transparent,
        ('Eles passaram por mim há pouco tempo.', 'O que aconteceu aqui?'),
        prompt='[E] Examinar corpo', interaction_radius=76)
    insignia_prop = Interactable(
        'red_insignia', 'Protagonista', (1280, 492), red_insignia, (),
        prompt='[E] Pegar insígnia', interaction_radius=70)
    battlefield_objects = [
        (fallen_blue, (246, 541)),
        (blue_sword, (370, 532)),
        (blue_shield, (453, 554)),
        (fallen_blue, (634, 463)),
        (fallen_blue, (1090, 412)),
    ]
    red_encounter_groups = (
        ((550, 536), (620, 566)),
        ((790, 488), (852, 470)),
        ((756, 662), (820, 680)),
        ((1018, 432), (1080, 453)),
        ((1228, 470), (1292, 500)),
    )
    # Nenúfares são pequenos detalhes limpos; os previews de água não são usados.
    lily=pygame.Surface((28,18),pygame.SRCALPHA)
    pygame.draw.ellipse(lily,(48,105,94),(0,4,27,13))
    pygame.draw.ellipse(lily,(100,159,108),(1,2,25,11))
    pygame.draw.polygon(lily,(44,111,131),[(14,8),(27,3),(22,12)])
    pygame.draw.rect(lily,(230,201,144),(9,1,4,3))
    for pos in [(1460,240),(1610,350),(1790,200),(1670,198)]:objects.append((lily,pos))
    chest=env.crop(load('assets/shared/chest_01.png'),(0,0,16,16),2)
    for pos in [(730,165),(1590,770)]: objects.append((chest,pos))
    obstacles.extend([lake.inflate(-30,-24),shallow.inflate(-20,-12)])
    return {'name':'Floresta Mística','terrain':terrain,'houses':[],'objects':objects,'nature':nature,
            'scenery':scenery,'water':water,'ambient_kind':'forest','obstacles':obstacles,
            'exits':{'village':pygame.Rect(0,520,76,115),'desert':pygame.Rect(1185,0,125,46)},
            'spawn':{'village':(120,575),'desert':(1245,82)},'arena':pygame.Rect(1040,220,520,420),
            'story_phase':'forest_initial',
            'enemy_spawns': [('slime',(560,365)),('slime',(820,300)),('slime',(530,760)),
                             ('slime',(1120,690)),('slime',(960,560))],
            'future_enemy_spawns': {'forest_post_army': [('warrior',(720,835)),
                                                          ('warrior',(1530,590))]},
            'forest_battlefield_objects': battlefield_objects,
            'forest_battlefield_interactables': {
                'body': battlefield_body, 'insignia': insignia_prop},
            'red_encounter_groups': red_encounter_groups,
            'wounded_commander_object': (
                commander_fallen,
                (1460 - commander_fallen.get_width() // 2,
                 520 - commander_fallen.get_height() // 2)),
            'wounded_commander_sprite': commander_sheet,
            'red_officer_trigger': (1460, 520)}
