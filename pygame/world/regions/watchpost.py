"""A compact road garrison: blocked gate, side breach, functional cutaway rooms."""
import random
import pygame
import environment as env
from entities.enemy import Enemy
from entities.interactable import Interactable
from world.regions.old_road_art import prop as road_prop
from world.regions.watchpost_art import prop, floor, wall

WORLD = (1536, 1024)
SPAWN = (768, 914)
BREACH = pygame.Rect(1164, 664, 32, 80)
POSTERN = pygame.Rect(1164, 280, 32, 80)
ROOMS = {"alojamento": pygame.Rect(454, 370, 278, 292),
         "deposito": pygame.Rect(936, 500, 180, 240),
         "comando": pygame.Rect(780, 210, 328, 230)}


class PostEvidence(Interactable):
    def __init__(self, uid, name, position, image, lines, flag, prompt, speakers=None):
        super().__init__(uid, name, position, image, lines, prompt=prompt, interaction_radius=58)
        self.story_flag = flag
        self.speakers = speakers

    def speaker_for(self, index):
        return self.speakers[index] if self.speakers else self.name


def spawn_post_enemy(kind, position, load, seed=0):
    enemy = Enemy(kind, position, load, seed)
    # Short perception keeps each occupation localized; existing art/attacks stay intact.
    enemy.config = dict(enemy.config, perception=110)
    return enemy


def build(load, _opened_chests=None):
    rng = random.Random(117)
    woods = env.free_woods(load)
    tufts = [env.tint(env.resize(load(f"sprites_meu/vila_tile-set/2 Objects/5 Grass/{i}.png"), 2),
                      (186, 186, 133)) for i in range(1, 7)]
    terrain = env.ground(WORLD, load("sprites_meu/vila_tile-set/1 Tiles/FieldsTile_38.png"),
                         117, ((83, 93, 70), (121, 123, 86)), tufts)
    dirt = env.worn_texture(load("sprites_meu/vila_tile-set/1 Tiles/FieldsTile_11.png"),
                            (133, 119, 89), 24, 117)
    env.paths(terrain, [([(768,1024),(768,850),(765,780)], 80),
                       ([(785,850),(1120,838),(1250,760),(1225,660)], 42),
                       ([(1190,330),(1300,300),(1420,200),(1536,190)], 40)], dirt, 117,
              [((820,590),(530,410)),((1260,690),(175,150))], tufts)
    scenery, obstacles = [], []

    def place(image, foot, box=None, canopy=False):
        obj = env.anchored(image, foot, canopy=canopy)
        scenery.append(obj)
        env.shadow(terrain, foot, max(18, image.width // 2), 10, 30)
        if box: obstacles.append(pygame.Rect(box).move(foot))
        return obj

    def horizontal(x, y, width, seed):
        place(wall(width, seed), (x + width // 2, y + 8))
        obstacles.append(pygame.Rect(x, y - 8, width, 20))

    def vertical(x, y, height):
        box = pygame.Rect(x, y, 20, height)
        pygame.draw.rect(terrain, (41,44,38), box.inflate(8,4).move(3,5))
        pygame.draw.rect(terrain, (128,125,104), box)
        pygame.draw.rect(terrain, (171,157,120), (x,y,4,height))
        for yy in range(y, y+height, 14):
            pygame.draw.line(terrain, (82,87,73), (x+4,yy), (x+19,yy), 2)
        obstacles.append(box)

    # A contained playable area, despite the global player bounds of older maps.
    for box in (pygame.Rect(0,0,1536,32), pygame.Rect(0,0,32,1024),
                pygame.Rect(1504,0,32,1024), pygame.Rect(0,992,694,32),
                pygame.Rect(842,992,694,32)):
        obstacles.append(box)
        pygame.draw.rect(terrain, (76,85,60), box)

    for i, foot in enumerate(((260,860),(435,945),(1010,945),(1370,855),(1340,515),
                              (1350,155),(280,310),(320,590),(1070,110),(580,105))):
        tree = env.tint(env.resize(woods["tree"],2), (212,203,151))
        place(tree, foot, (-12,-8,24,16), True)
        place(env.resize(woods["bush"],2), (foot[0]+36,foot[1]+15), canopy=True)
    for _ in range(50):
        x,y = rng.randrange(70,1460),rng.randrange(60,950)
        if 380<x<1200 and 150<y<820: continue
        place(env.tint(env.resize(woods["rock"],2),(205,197,164)),(x,y))

    # Low outer enclosure, one jammed gate and two distinct service openings.
    horizontal(400,170,784,1)
    horizontal(400,784,300,2); horizontal(836,784,348,3)
    vertical(400,170,614)
    for y,h in ((170,110),(360,304),(744,40)): vertical(1168,y,h)
    gate = place(prop("gate"), (768,790))
    gate_block = pygame.Rect(700,758,136,34)
    obstacles.extend((gate_block, BREACH.copy(), POSTERN.copy()))
    breach_visual = place(prop("breach"), (1180,725))
    postern_visual = place(prop("closed_postern"), (1180,346))
    place(prop("flag"), (660,756), (-8,-8,16,15))
    place(road_prop("broken_crate"), (846,831))
    place(road_prop("blue_shield"), (452,734))
    env.patch(terrain, (540,714), (60,25), (87,58,45,105), 117)
    place(road_prop("watchpost"), (562,340), (-62,-110,124,112))
    place(road_prop("wall"), (650,333), (-28,-8,56,14))

    for index, (name, room) in enumerate(ROOMS.items()):
        floor(terrain, room, wooden=name != "deposito", seed=20+index)
        horizontal(room.x, room.y, room.width, 20+index)
        if name == "alojamento":
            horizontal(room.x, room.bottom, room.width, 24)
            vertical(room.x,room.y,room.height)
            vertical(room.right-16,room.y,170)
            vertical(room.right-16,606,56)
        elif name == "deposito":
            horizontal(room.x, room.bottom, room.width, 25)
            vertical(room.right-16,room.y,room.height)
            vertical(room.x,room.y,124)
            vertical(room.x,684,56)
        else:
            vertical(room.x,room.y,room.height)
            vertical(room.right-16,room.y,room.height)
            horizontal(room.x,room.bottom,128,26)
            horizontal(980,room.bottom,room.right-980,27)
    memory_scenery = list(scenery)
    memory_terrain = terrain.copy()
    memory_scenery.extend((env.anchored(prop("desk"),(967,320)),
                           env.anchored(road_prop("red_cloth"),(1065,265)),
                           env.anchored(prop("bed"),(502,492)),
                           env.anchored(prop("bed"),(555,492))))
    # A lodging, a working store and a command office, connected by the yard.
    for foot in ((502,492),(555,492),(507,617)):
        place(prop("bed"),foot,(-23,-60,46,62))
    place(prop("locker"),(638,455),(-25,-48,50,50))
    place(prop("papers"),(655,505)); place(prop("chair"),(634,563))
    place(road_prop("supplies"),(565,595))
    place(prop("shelf"),(1055,565),(-43,-43,86,46))
    place(road_prop("crate"),(1070,730),(-23,-22,46,24))
    place(road_prop("broken_crate"),(1040,720))
    place(road_prop("supplies"),(1000,698))
    place(prop("desk"),(967,320),(-51,-31,102,32))
    place(prop("chair"),(1050,347)); place(prop("papers"),(1060,394))
    place(prop("shelf"),(838,302),(-43,-43,86,46))
    place(road_prop("red_cloth"),(1065,265))
    env.patch(terrain,(1070,374),(42,25),(115,51,42,105),118)
    # Dragged drawers, clean rectangles in dust, loose leaves: a targeted search.
    for x,y in ((655,488),(1040,360),(1020,403)):
        pygame.draw.rect(terrain,(128,111,81),(x,y,28,10),2)
        pygame.draw.line(terrain,(62,59,46),(x,y+16),(x+26,y+20),2)
    for i in range(11):
        x,y = 1070+i*15,380-i*5
        pygame.draw.ellipse(terrain,(70,67,51),(x,y+(i%2)*8,5,9))
    for foot in ((424,677),(730,720),(1120,463),(1090,181)):
        terrain.blit(tufts[foot[0]%6],(foot[0]-12,foot[1]-20))

    clues = [
        Interactable("post_gate","Protagonista",(768,808),pygame.Surface((1,1),pygame.SRCALPHA),
                     ("O portão cedeu por dentro. Há uma abertura no muro leste.",),
                     prompt="[E] Examinar portão",interaction_radius=50),
        PostEvidence("post_breach","Protagonista",(1216,703),pygame.Surface((1,1),pygame.SRCALPHA),
                     ("Só uma corda segura estas tábuas.","Consigo afastá-las e passar."),
                     "watchpost_entry_open","[E] Afastar tábuas"),
        PostEvidence("post_archive","Livro do Posto",(681,630),prop("archive"),
                     ("Registro antigo — Posto Norte. Abrigo de caravanas e troca de escoltas. Com a guerra, o alojamento passou a receber feridos dos dois lados.",),
                     "watchpost_archive_read","[E] Ler registro antigo"),
        PostEvidence("post_dispatch","Despacho Azul",(995,557),prop("dispatch"),
                     ("Última passagem: uma escolta vermelha deixou o posto antes do amanhecer. Dois batedores azuis vieram depois. Destino não registrado.",
                      "Ordem anterior, selo azul: reter desertores e seus acompanhantes. Interrogar sem água até obter a rota. Não aguardar autorização local.",
                      "Não eram só soldados que podiam acabar presos aqui."),
                     "watchpost_dispatch_read","[E] Ler despacho",("Despacho Azul","Ordem anexada","Protagonista")),
        PostEvidence("post_roster","Registro de Guarnição",(973,341),prop("roster"),
                     ("Guarnição vermelha — R-17. Responsável pela escolta. Acesso ao comando para receber ordens. Assinatura preservada; demais nomes danificados.",
                      "A curva do R. O risco no final... Eu assinei isto."),
                     "watchpost_roster_read","[E] Ler lista da guarnição",("Registro de Guarnição","Protagonista")),
        PostEvidence("post_token","Protagonista",(647,471),prop("token"),
                     ("Uma peça de identificação, gasta onde meu polegar encostava. R-17.","Isso era meu."),
                     "watchpost_personal_item_found","[E] Examinar identificação"),
        PostEvidence("post_trail","Protagonista",(1230,329),pygame.Surface((1,1),pygame.SRCALPHA),
                     ("Pegadas sobre a poeira das tábuas. A porta acabou de ser aberta.",
                      "Alguém saiu por aqui. Preciso alcançá-lo."),
                     "watchpost_trail_found","[E] Examinar pegadas"),
    ]
    # Fresh tracks continue outside the postern to the wounded trail.
    for i in range(13):
        x,y = 1200+i*18,330-i*10
        pygame.draw.ellipse(terrain,(74,70,53),(x,y+(i%2)*7,6,10))
    return {"name":"Posto de Vigia","terrain":terrain,"ambient_kind":"watchpost",
            "houses":[],"objects":[],"nature":[],"scenery":scenery,"npcs":[],
            "obstacles":obstacles,"interactables":clues,
            "exits":{"old_road":pygame.Rect(700,990,136,34)},
            "spawn":{"old_road":SPAWN,"pursuit":(1390,230)},"enemy_spawns":[("warrior",(845,563)),("slime",(1052,663))],
            "enemy_factory":spawn_post_enemy,"rooms":ROOMS,
            "memory_scenery":memory_scenery,
            "memory_terrain":memory_terrain,
            "breach_block":BREACH.copy(),"breach_visual":breach_visual,
            "postern_block":POSTERN.copy(),"postern_visual":postern_visual,
            "presence_trigger":pygame.Rect(450,230,720,550),
            "presence_focus":(1100,330),"gate_block":gate_block,"gate_visual":gate}
