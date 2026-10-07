"""An abandoned trade route: quiet approach, wrecks, then military traces."""
import math
import random
import pygame
import environment as env
from entities.interactable import Interactable
from entities.road_pursuer import spawn_road_enemy
from systems.items import consumable
from world.regions.desert import Chest
from world.regions.old_road_art import prop

WORLD = (2048, 1152)
MAIN_ROUTE = [(2048,850),(1810,850),(1660,785),(1510,700),(1390,640),
              (1210,700),(1050,730),(885,655),(850,535),(945,470),
              (1080,480),(1230,435),(1310,345),(1240,275),(1110,285),
              (995,335),(920,340)]
SIDE_ROUTES = [([(1760,835),(1790,925),(1720,1000)],36),
               ([(890,655),(780,700),(745,765)],35),
               ([(1190,705),(1200,860),(1280,955)],30)]
MEMORY_POINT = (815, 518)
LOOKOUT = pygame.Rect(865, 290, 130, 110)
ENCOUNTERS = [("slime", (1375,665)), ("slime", (1275,748)),
              ("road_pursuer", (985,715)), ("road_pursuer", (1285,465))]


class RoadClue(Interactable):
    def __init__(self, uid, position, image, lines, flag, prompt):
        super().__init__(uid, "Protagonista", position, image, lines,
                         prompt=prompt, interaction_radius=68)
        self.story_flag = flag


def build(load, opened_chests=None):
    opened_chests = opened_chests or set()
    rng = random.Random(116)
    woods = env.free_woods(load)
    tile = load("sprites_meu/vila_tile-set/1 Tiles/FieldsTile_38.png")
    tufts = [env.tint(env.resize(load(f"sprites_meu/vila_tile-set/2 Objects/5 Grass/{i}.png"),2),
                      (217,200,137)) for i in range(1,7)]
    terrain = env.ground(WORLD,tile,116,((90,100,68),(145,139,89)),tufts)
    dirt = env.worn_texture(load("sprites_meu/vila_tile-set/1 Tiles/FieldsTile_11.png"),
                            (158,135,92),30,116)
    routes = [(MAIN_ROUTE[:6],76),(MAIN_ROUTE[5:10],60),(MAIN_ROUTE[9:],52),*SIDE_ROUTES]
    mask = env.paths(terrain,routes,dirt,116,
        [((1390,660),(245,190)),((985,715),(230,165)),
         ((1280,450),(225,175)),((1190,285),(240,150)),
         ((1730,1000),(180,125)),((745,765),(175,145)),((1280,955),(185,120))],tufts)
    scenery, obstacles = [], []

    def place(image, foot, box=None, canopy=False, sway=0):
        scenery.append(env.anchored(image,foot,canopy,sway,foot[0]*.02))
        if box:
            obstacles.append(pygame.Rect(box).move(foot))
        env.shadow(terrain,foot,max(20,image.width//2),10,32)

    def ridge(points, seed):
        # Visible stepped rock banks carry matching grid footprints.
        edge = [(round(x),round(y)) for x,y in env.curve(points[1:],12)]
        bank = pygame.Surface(WORLD,pygame.SRCALPHA)
        pygame.draw.polygon(bank,(255,255,255),[points[0],*edge])
        top = terrain.copy().convert_alpha()
        top.fill((224,220,185,255),special_flags=pygame.BLEND_RGBA_MULT)
        top.blit(bank,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
        terrain.blit(top,(0,0))
        shade = pygame.Surface(WORLD,pygame.SRCALPHA)
        pygame.draw.lines(shade,(43,48,33,75),False,[(x+5,y+22) for x,y in edge],35)
        terrain.blit(shade,(0,0))
        for offset,width,color in ((10,27,(80,80,63)),(4,23,(126,119,88)),
                                   (0,12,(159,145,105)),(-3,5,(183,165,116))):
            pygame.draw.lines(terrain,color,False,[(x,y+offset) for x,y in edge],width)
        pygame.draw.lines(bank,(255,255,255),False,edge,30)
        solid = pygame.mask.from_surface(bank)
        for y in range(0,WORLD[1],32):
            start = None
            for x in range(0,WORLD[0]+32,32):
                occupied = x < WORLD[0] and solid.get_at((x+16,y+16))
                if occupied and start is None:
                    start = x
                elif not occupied and start is not None:
                    obstacles.append(pygame.Rect(start,y,x-start,32))
                    start = None
        rock = env.tint(env.resize(woods["rock"],2),(217,207,169))
        local = random.Random(seed)
        for i,(x,y) in enumerate(edge[::3]):
            if 15<x<2030 and 16<y<1120:
                pygame.draw.line(terrain,(91,88,68),(x-5,y+8),(x+5,y+14),2)
                if i%2==0:
                    terrain.blit(tufts[i%6],(x-10,y-18))
        for _ in range(180):
            x,y = local.randrange(30,2010),local.randrange(30,1120)
            if solid.get_at((x,y)):
                terrain.blit(rock,(x,y))

    ridge([(0,0),(520,0),(570,160),(540,310),(600,460),(580,600),
           (630,780),(570,960),(460,1152),(0,1152)],18)
    ridge([(1330,0),(2048,0),(2048,620),(1940,655),(1800,612),
           (1730,650),(1600,562),(1560,470),(1500,420),(1490,300),(1380,260)],26)
    # Wheel ruts, irregular weeds and gravel preserve the identity of a road.
    for i,(x,y) in enumerate(env.curve(MAIN_ROUTE,12)):
        if i%3:
            for offset in (-13,13):
                pygame.draw.line(terrain,(133,113,80),(round(x-3),round(y+offset)),
                                 (round(x+5),round(y+offset-1)),2)
        if i%11==0:
            terrain.blit(tufts[i%6],(round(x)-10,round(y)+12))
    for _ in range(440):
        x,y = rng.randrange(630,2010),rng.randrange(230,1120)
        if mask.get_at((x,y)):
            pygame.draw.rect(terrain,rng.choice([(184,166,119),(126,121,94),(114,110,84)]),(x,y,4,2))

    def dry_leaves(source):
        result = source.copy()
        for y in range(result.height):
            for x in range(result.width):
                r,g,b,a = result.get_at((x,y))
                if a and g>r+12 and g>b+15:
                    result.set_at((x,y),(min(255,round(g*1.02)),round(g*.92),round(g*.49),a))
        return result
    tree = env.resize(dry_leaves(woods["tree"]),2)
    bush = env.resize(dry_leaves(woods["bush"]),2)
    rock = env.tint(env.resize(woods["rock"],2),(218,207,170))
    for i,foot in enumerate([(1870,710),(1840,990),(1700,705),(1665,940),
        (1490,535),(1535,850),(1435,915),(1180,595),(1145,815),(1020,590),
        (800,900),(675,680),(760,465),(1010,395),(1180,555),(1375,400),
        (1350,190),(1030,175),(730,360),(675,1020),(1480,1030)]):
        place(tree,foot,(-10,-8,20,14),True,1)
        if i%2==0: place(bush,(foot[0]+40,foot[1]+10),sway=1)
    for foot in [(1760,730),(1590,670),(1480,815),(1320,820),(1110,870),
                 (900,830),(720,615),(905,450),(1150,375),(1390,315),(1040,235)]:
        place(rock,foot,(-13,-9,26,14))
    for foot in [(1880,803),(1640,735),(1550,645),(1395,585),(1325,590),
                 (910,618),(805,675),(1340,390),(1300,235)]:
        place(prop("fence"),foot,(-34,-7,68,10))

    # Wreck: broken cargo, wheel, dry blood and a snapped weapon; no verdict.
    for kind,foot in [("cart",(1450,603)),("wheel",(1512,657)),
                      ("broken_crate",(1390,607)),("broken_crate",(1470,676)),
                      ("supplies",(1430,647))]:
        place(prop(kind),foot,(-30,-12,60,20) if kind=="cart" else None)
    env.patch(terrain,(1412,660),(50,24),(103,57,45,115),19)
    pygame.draw.line(terrain,(150,151,132),(1443,670),(1462,681),3)
    pygame.draw.line(terrain,(89,66,44),(1465,683),(1473,687),3)
    for kind,foot in [("wall",(730,736)),("wall",(802,758)),("bedroll",(730,799)),
                      ("red_cloth",(772,803)),("fire",(1275,943)),
                      ("cart",(1345,964)),("broken_crate",(1240,981))]:
        place(prop(kind),foot,(-34,-8,68,12) if kind=="wall" else None)

    # Recent bivouac: food, wound dressings and supplies left rather than looted.
    for kind,foot in [("fire",(1190,294)),("bedroll",(1140,275)),
                      ("bedroll",(1220,312)),("supplies",(1170,327)),
                      ("crate",(1260,263)),("red_cloth",(1240,303))]:
        place(prop(kind),foot,(-22,-8,44,15) if kind=="crate" else None)
    # Fresh boot marks lead from the fire toward the northern lookout.
    for i in range(17):
        x,y = 1180-i*13,315+round(math.sin(i*.19)*25)
        pygame.draw.ellipse(terrain,(111,96,70),(x,y+(i%2)*8,5,8))
        pygame.draw.line(terrain,(132,115,79),(x,y+2),(x+3,y+2),1)
    for foot in [(830,290),(905,266),(965,250)]:
        place(prop("wall"),foot,(-33,-8,66,14))
    place(prop("watchpost"),(830,228),(-65,-10,130,26))
    # The exterior is a destination tableau; its approach stops at old rubble.
    place(prop("wall"),(880,248),(-34,-8,68,14))

    clues = [
        RoadClue("road_red_cloth",(1640,783),prop("red_cloth"),
                 ("O mesmo símbolo. Eles passaram por aqui.",),
                 "road_red_clue_found","[E] Examinar tecido"),
        RoadClue("road_blue_shield",(1250,409),prop("blue_shield"),
                 ("Azuis também. Mas vieram atrás deles... ou antes?",),
                 "road_blue_trace_found","[E] Examinar escudo"),
        RoadClue("road_camp_map",(1175,282),prop("map"),
                 ("As cinzas ainda estão mornas.","No mapa: ‘Reagrupar. Posto Norte’."),
                 "road_camp_found","[E] Examinar mapa"),
        Interactable("road_aid_remains","Protagonista",(753,801),prop("supplies"),
                     ("Curativos usados. Alguém ficou aqui para cuidar dos feridos.",),
                     prompt="[E] Examinar abrigo"),
        Interactable("road_caravan_note","Protagonista",(1310,974),prop("map"),
                     ("‘Se a passagem fechar, deixe água junto ao marco.’",),
                     prompt="[E] Ler bilhete"),
    ]
    place(prop("milestone"),MEMORY_POINT,(-14,-10,28,18))
    chests = [Chest("road_chest_turnout",(1720,1000),consumable("herb",2)),
              Chest("road_chest_shelter",(773,772),consumable("ether",1)),
              Chest("road_chest_caravan",(1230,941),consumable("potion",1))]
    sheet = load("assets/shared/chest_01.png")
    for chest in chests:
        chest.opened = chest.uid in opened_chests
        chest.frames = [env.crop(sheet,(0,0,16,16),3),env.crop(sheet,(48,0,16,16),3)]
        obstacles.append(chest.hitbox)
    return {"name":"Antiga Estrada","terrain":terrain,"houses":[],"objects":[],
        "nature":[],"scenery":scenery,"obstacles":obstacles,"npcs":[],
        "ambient_kind":"old_road","story_phase":"road_investigation",
        "exits":{"village":pygame.Rect(1996,805,52,115)},
        "spawn":{"village":(1910,850),"watchpost":(920,340)},"enemy_spawns":ENCOUNTERS,
        "enemy_factory":spawn_road_enemy,"interactables":clues+chests,
        "memory_point":MEMORY_POINT,"lookout":LOOKOUT,"watchpost_focus":(850,175),
        "main_route":MAIN_ROUTE,"side_routes":SIDE_ROUTES,
        "optional_points":[(1720,1000),(773,772),(1230,941)]}
