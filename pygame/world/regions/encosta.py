"""Three traversable chapter-II regions, built once on entry with authored landmarks."""
import math
import random
import pygame
import environment as env
from world import asset_art
from entities.interactable import Interactable
from entities.encosta_actor import EncostaNPC
from entities.encosta_creature import EncostaCreature
from world.regions import encosta_art as art
from story.resonance import POINTS

WORLD=(2048,1152)


class CabinetMarker(Interactable):
    def draw(self,canvas,camera):
        super().draw(canvas,camera)
        if self.opened:
            pygame.draw.line(canvas,art.PAPER,(round(self.x-12-camera[0]),round(self.y-10-camera[1])),
                             (round(self.x+12-camera[0]),round(self.y-10-camera[1])),2)


def load_ground():
    from core.assets import load
    return load('sprites_meu/vila_tile-set/1 Tiles/FieldsTile_38.png')


def _base(kind,name,seed):
    terrain=env.ground(WORLD,load_ground(),seed,((57,83,65),(101,121,78)))
    return {'name':name,'ambient_kind':kind,'terrain':terrain,'houses':[],
            'objects':[],'nature':[],'scenery':[],'obstacles':[],'exits':{},'spawn':{},
            'npcs':[],'interactables':[],'enemy_spawns':[],'enemy_factory':EncostaCreature,
            'water':[],'ambient_centers':[]}


def _place(region,image,foot,box=None):
    region['scenery'].append(env.anchored(image,foot))
    env.shadow(region['terrain'],foot,max(14,image.width//3),8,34)
    if box is not None: region['obstacles'].append(pygame.Rect(box).move(foot))


def _path(region,points,width=104,seed=1):
    from core.assets import load
    texture=env.worn_texture(load('sprites_meu/vila_tile-set/1 Tiles/FieldsTile_11.png'),(145,135,103),75,seed)
    env.paths(region['terrain'],[(points,width)],texture,seed)


def _cliff(region,rect,seed=0):
    box=pygame.Rect(rect); im=pygame.Surface(box.size)
    im.fill((43,57,57)); rng=random.Random(seed)
    # Uneven slate shelves and fractures distinguish the escarpment from masonry.
    for y in range(0,box.height,18):
        x=-rng.randrange(10,35)
        while x<box.width:
            w=rng.randrange(26,70); lift=rng.randrange(0,5)*2
            pygame.draw.polygon(im,rng.choice(((87,105,98),(103,119,105),(65,85,83))),
                [(x,y+lift),(x+w-7,y),(x+w,y+10),(x+w-4,y+16),(x+8,y+18)])
            pygame.draw.line(im,(135,149,120),(x+3,y+lift),(x+w-9,y),2)
            if rng.random()<.6:
                pygame.draw.lines(im,(46,62,61),False,[(x+w//2,y+3),(x+w//2-4,y+10),(x+w//2+1,y+16)],2)
            x+=w-2
    for x in range(0,box.width,8):
        pygame.draw.rect(im,rng.choice((art.MOSS,(119,128,84),(66,86,65))),(x,0,8,rng.randrange(2,7)*2))
    region['terrain'].blit(im,box); region['obstacles'].append(box)


def _edges(region,gaps):
    # Visible stone ledges bound the map; exits have deliberate openings.
    for side,rect in (('top',(0,0,2048,32)),('bottom',(0,1120,2048,32)),
                      ('left',(0,0,32,1152)),('right',(2016,0,32,1152))):
        if side not in gaps: _cliff(region,rect,8); continue
        start,end=gaps[side]
        if side in ('top','bottom'):
            y=0 if side=='top' else 1120
            for x,w in ((0,start),(end,2048-end)):
                if w: _cliff(region,(x,y,w,32),8)
        else:
            x=0 if side=='left' else 2016
            for y,h in ((0,start),(end,1152-end)):
                if h: _cliff(region,(x,y,32,h),8)


def _flora(region,positions):
    for i,foot in enumerate(positions):
        image=art.tree(i%5)
        region['scenery'].append(env.anchored(image,foot,canopy=True,sway=1,phase=i*.7))
        env.shadow(region['terrain'],foot,25,8,34)
        region['obstacles'].append(pygame.Rect(-12,-12,24,14).move(foot))
    terrain=region['terrain']; rng=random.Random(99)
    for _ in range(220):
        x,y=rng.randrange(60,1990),rng.randrange(60,1090)
        if any(pygame.Rect(x-8,y-5,16,10).colliderect(o) for o in region['obstacles']): continue
        for i in range(4): pygame.draw.line(terrain,art.MOSS,(x+i*3,y),(x+i*3-2,y-4-i%3),2)


def _evidence(region,uid,pos,kind,lines,prompt,radius=70):
    obj=Interactable(uid,'Protagonista',pos,art.prop(kind),lines,prompt='[E] '+prompt,interaction_radius=radius)
    region['interactables'].append(obj); return obj


def _echoes(region):
    for point in POINTS:
        if point.region!=region['ambient_kind']: continue
        kind={'echo_meal':'meal','echo_departure':'cart','echo_orders':'seal','echo_threshold':'seal'}[point.uid]
        obj=Interactable(point.uid,'Protagonista',point.position,art.prop(kind),(),
                         prompt='[E] Escutar ressonância',interaction_radius=72)
        if point.uid=='echo_threshold': obj.image=pygame.transform.scale_by(obj.image,.5)
        obj.resonance=True; region['interactables'].append(obj)


def route(load,opened_chests=None):
    r=_base('forgotten_route','Rota das Pedras Afundadas',212); _edges(r,{'left':(850,1050),'right':(160,320)})
    _path(r,[(0,950),(550,950),(680,760),(1470,760),(1730,480),(2048,240)],110,21)
    _path(r,[(590,880),(540,590),(440,390)],72,22)
    _path(r,[(700,760),(770,345),(1350,345),(1450,740)],66,23)
    _path(r,[(1330,345),(1390,180)],38,24)
    creek=pygame.Rect(960,0,120,1152)
    asset_art.water(r['terrain'],creek,212)
    for top,bottom in ((0,300),(394,708),(832,1152)):
        asset_art.bank(r['terrain'],944,top,bottom)
        asset_art.bank(r['terrain'],1064,top,bottom,True)
    r['water']=[{'rect':creek,'color':(100,153,148)}]
    for rect in ((960,0,120,300),(960,394,120,314),(960,820,120,332)):
        r['obstacles'].append(pygame.Rect(rect))
    # A low surviving stone bridge and an optional shallow ford are distinct crossings.
    for y in (708,820):
        _cliff(r,(940,y,160,12),30)
    _path(r,[(924,760),(1110,760)],94,25)
    asset_art.floor(r['terrain'],(940,724,160,84),seed=25)
    for x in range(960,1080,20):
        pygame.draw.ellipse(r['terrain'],art.STONE,(x,322+(x//20%2)*12,18,35))
    for box in ((260,175,430,65),(1720,90,255,70),(1290,940,500,85)):
        _cliff(r,box,11)
    for i,foot in enumerate(((620,420),(823,640),(1260,660),(1430,858),(1690,390),(1190,230))):
        _place(r,art.rock(i),foot,(-40,-26,80,28))
    _flora(r,[(140,750),(220,700),(350,620),(490,340),(630,670),(800,480),
              (865,250),(1150,550),(1280,890),(1400,290),(1600,600),(1850,710),
              (1750,875),(170,1070),(380,1060),(760,1060),(1850,1010)])
    for kind,foot in (('tools',(620,515)),('cart',(833,870)),('seal',(1480,450)),('route_sign',(1840,260))): _place(r,art.prop(kind),foot)
    # Broken abutments provide a vista beneath the bridge without concealing collision.
    for x,y in ((914,1010),(1096,1034)):
        _cliff(r,(x,y,45,55),15)
    _evidence(r,'route_cache',(440,400),'supplies',
        ('A caixa tem o selo do posto, não de um exército. Duas poções e um frasco de éter ainda estão fechados.',),
        'Abrir provisões da equipe de estrada')
    _evidence(r,'route_record',(1390,180),'record',
        ('Nota dobrada dentro de um marco. Antes da quarta vigília: transferir o rol dos acolhidos para custódia. Não juntar nomes à remessa militar.',
         'O carimbo de reenvio é o do recibo de Alden. O pedido antecede a queda da ponte; não diz por que separaram os nomes.'),
        'Examinar nota no marco')
    _evidence(r,'route_rest',(1760,570),'rest',
        ('Uma varanda seca, protegida do vento. Posso descansar antes de seguir a subida.',),'Descansar na varanda')
    _evidence(r,'route_bridge',(880,940),'tools',
        ('A ponte baixa foi remendada por moradores. A passagem antiga cedeu; acima ainda há pedras de vau.',),'Examinar reparos da ponte')
    r['exits']={'village':pygame.Rect(0,870,40,160),'encosta':pygame.Rect(2005,170,43,140)}
    r['spawn']={'village':(120,950),'encosta':(1930,240)}
    r['enemy_spawns']=[('reed_stalker',(680,825)),('slateback',(430,490)),
                       ('reed_stalker',(1290,410)),('reed_stalker',(1420,740)),('slateback',(1550,870))]
    r['ambient_centers']=[(790,360),(1480,710),(1750,535)]
    return r


def settlement(load,opened_chests=None):
    r=_base('encosta','Posto de Convalescença da Encosta',213); _edges(r,{'left':(820,1010),'top':(1460,1630)})
    _path(r,[(0,910),(550,910),(860,700),(1350,690),(1565,360),(1565,0)],120,30)
    _path(r,[(860,700),(720,410),(1110,390),(1300,440)],92,31)
    _path(r,[(920,730),(1180,900)],86,32)
    _path(r,[(600,890),(560,760)],65,33)
    for style,foot in ((0,(430,410)),(1,(770,330)),(0,(1410,940)),(1,(1730,710)),(2,(1100,290))):
        image=art.building(style); _place(r,image,foot,(-image.width//2+24,-image.height+80,image.width-48,image.height-96))
    # A roofless community archive offers a readable interior on the same map.
    room=pygame.Rect(920,345,370,235)
    pygame.draw.rect(r['terrain'],art.DARK,room)
    for y in range(room.top+8,room.bottom-5,12):
        pygame.draw.line(r['terrain'],art.PLANK,(room.left+8,y),(room.right-8,y),8)
        for x in range(room.left+20,room.right-10,44): pygame.draw.line(r['terrain'],art.WOOD,(x,y),(x,y+8),2)
    _cliff(r,(920,328,370,18),52); _cliff(r,(920,345,18,145),53); _cliff(r,(1272,345,18,145),54)
    _place(r,art.prop('well'),(925,660),(-35,-38,70,38))
    _place(r,art.prop('cabinet'),(1030,492),(-40,-55,80,55))
    _place(r,art.prop('tools'),(1380,767))
    _place(r,art.prop('post_sign'),(290,790))
    for x,y in ((350,620),(472,620),(1570,885),(1695,885)):
        _place(r,art.prop('fence'),(x,y),(-61,-12,122,12))
    for kind,foot in (('tools',(435,458)),('supplies',(788,365)),('rest',(1650,760)),
                       ('tools',(1540,900)),('supplies',(1060,310))):
        _place(r,art.prop(kind),foot)
    from world.regions.watchpost_art import prop as post_prop
    _place(r,post_prop('desk'),(1200,557),(-55,-32,110,32))
    for i,pos in enumerate(((235,300),(515,260),(790,540),(1630,260),(1780,440),(1750,1030),(470,1070),(310,720))):
        _place(r,art.rock(i),pos,(-36,-24,72,26))
    _flora(r,[(150,470),(350,570),(590,700),(700,1080),(1780,340),(1900,890),(1840,1050),(1300,170)])
    _evidence(r,'encosta_register',(1200,499),'register',
        ('Livro comunitário. Entradas de feridos, refeições e devolução de objetos. Há nomes sem baixa, mas nenhuma lista de mortos.',
         'Na véspera da retirada: “acolher com a tigela; vigiar com a lamparina; guardar o nome por último”. O rito aparece nos três fechos do armário.',
         'O posto recebeu a remessa R-17/N-04. A coluna de custódia continua em outro livro, separado dos registros militares.'),
        'Ler registro comunitário')
    r['interactables'][-1].image=pygame.transform.scale_by(r['interactables'][-1].image,.6)
    r['interactables'][-1].visual_depth=558
    _evidence(r,'encosta_locket',(580,760),'locket',
        ('Um pingente com duas iniciais. A fita foi cortada, não partida.',
         'Uma etiqueta: “devolver a Lídia quando ela voltar da Câmara”. A linha de entrega está vazia.'),
        'Examinar objeto de Lídia')
    _evidence(r,'encosta_symbol',(1420,480),'seal',
        ('Três arcos abertos em torno de um espaço vazio. O sinal é de custódia, diferente das insígnias dos exércitos.',
         'Uma guia presa à pedra liga o selo ao número da remessa do Vale. “Testemunhos: não anexar o rol à ordem de retirada”.'),
        'Comparar selo de custódia')
    markers=[]
    for uid,kind,pos in (('cabinet_bowl','bowl',(950,555)),('cabinet_lamp','lamp',(1060,565)),('cabinet_name','name',(1170,565))):
        obj=CabinetMarker(uid,'Protagonista',pos,art.prop(kind),(),prompt='[E] Acionar fecho: '+{'bowl':'tigela','lamp':'lamparina','name':'nome'}[kind],interaction_radius=46)
        r['interactables'].append(obj); markers.append(obj)
    r['puzzle_markers']=markers
    _evidence(r,'sealed_record',(1030,510),'record',
        ('Termo de custódia assinado por Inês. Ela entregou o rol dos acolhidos à Câmara dos Testemunhos, sem registrar a saída das pessoas.',
         'A margem acusa “retenção de identidades”. Outra tinta: “evitar requisições de ambas as escoltas”. Não há assinatura no comentário.',
         'Isso pode apontar colaboração ou proteção. Preciso ouvir Inês antes de decidir o que fazer com a folha.'),
        'Retirar folha do compartimento',50)
    _evidence(r,'custody_plan',(1260,575),'plan',
        ('Planta de custódia: Câmara dos Testemunhos, escarpa acima do posto. Entrada pelo arco norte.',
         'Há uma referência R-17 no campo de autorização. O rol foi encaminhado ali; a ficha de esquecimento veio depois. Não sei se são o mesmo procedimento.',
         'Uma pequena chave acompanha a planta. É a do arco norte.'),
        'Conferir planta da Câmara')
    _evidence(r,'closed_gate',(1565,125),'seal',
        ('O arco abre para a escarpa. Antes de subir, preciso compreender o selo e localizar a planta de custódia.',),'Examinar arco norte')
    r['npcs']=[EncostaNPC('ines','Inês',(780,660),load),EncostaNPC('breno','Breno',(1370,610),load)]
    r['obstacles'].extend(n.hitbox for n in r['npcs'])
    r['north_gate']=pygame.Rect(1460,32,170,22); r['north_exit']=pygame.Rect(1460,0,170,45)
    r['north_barrier']=env.anchored(art.north_barrier(),(1545,54))
    r['exits']={'forgotten_route':pygame.Rect(0,840,40,160)}
    r['spawn']={'forgotten_route':(120,910),'threshold':(1565,100)}
    r['ambient_centers']=[(970,690),(490,890),(1430,450)]; _echoes(r)
    return r


def threshold(load,opened_chests=None):
    r=_base('threshold','Escarpa dos Testemunhos',214); _edges(r,{'bottom':(330,535)})
    _path(r,[(430,1152),(430,960),(820,860),(1080,650),(1450,620),(1450,335)],114,41)
    _path(r,[(910,795),(1100,915),(1450,800),(1550,630)],70,42)
    _cliff(r,(70,180,260,550),60); _cliff(r,(390,180,580,95),61)
    _cliff(r,(390,300,290,300),62); _cliff(r,(1785,220,180,650),63)
    _cliff(r,(920,1000,740,70),64)
    # Tall monumental sculpture sits in the rock, with a walkable forecourt.
    im=art.chamber(); _place(r,im,(1450,580))
    # Its recessed doorway is the boundary to Part B. Forecourt remains playable.
    r['obstacles'].append(pygame.Rect(1110,45,680,545))
    for i,pos in enumerate(((800,770),(1220,680),(1510,915),(1730,640))):
        _place(r,art.rock(i+3),pos,(-40,-26,80,28))
    _flora(r,[(170,940),(670,1050),(690,720),(1880,990),(1740,1080)])
    _evidence(r,'recent_camp',(1070,780),'camp',
        ('A cinza está morna. Pegadas sobem à Câmara e não voltam pela escarpa.',
         'Um pedaço de pano sem insígnia prende o cantil. Quem passou aqui cuidou para não deixar uma cor.'),'Examinar sinais recentes')
    entrance=_evidence(r,'chamber_entrance',(1450,600),'seal',
        ('A porta está entreaberta. O selo corresponde ao da planta.',
         'Do outro lado, passos cessam quando encosto na pedra.'),'Examinar entrada da Câmara')
    entrance.image=pygame.Surface((1,1),pygame.SRCALPHA)
    # Visible low fallen stones flank the opening; a territorial creature holds the gap.
    _cliff(r,(980,392,305,24),65); _cliff(r,(1615,392,170,24),66)
    r['exits']={'encosta':pygame.Rect(335,1110,190,42)}
    r['spawn']={'encosta':(430,1030)}
    r['enemy_spawns']=[('reed_stalker',(1050,905)),('slate_warden',(1420,655))]
    r['ambient_centers']=[(1010,790),(1440,545)]; r['fires']=[(1070,758),(1660,480)]
    _echoes(r)
    return r
