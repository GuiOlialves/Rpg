"""Five coherent sectors of a custody installation, with legible doors and footprints."""
import pygame
import environment as env
from entities.interactable import Interactable
from entities.lacre_actor import LacreActor
from world.regions import lacre_art as art
from story.lacre_content import REGIONS,NAMES,DOCUMENTS
from story.resonance import POINTS

def place(r,kind,foot,solid=False):
    im=art.prop(kind);obj=env.anchored(im,foot);r['scenery'].append(obj)
    if solid:r['obstacles'].append(pygame.Rect(foot[0]-42,foot[1]-24,84,24))
    env.shadow(r['terrain'],foot,40,9,35)
    return obj

def interact(r,uid,pos,kind,lines=(),prompt='Examinar',destination=None):
    obj=Interactable(uid,'Protagonista',pos,art.prop(kind),lines,prompt='[E] '+prompt,
        transition_to=destination,transition_on_interact=bool(destination))
    r['interactables'].append(obj);return obj

def build(kind,load,opened_chests=None):
    index=REGIONS.index(kind);terrain=pygame.Surface((2048,1152));terrain.fill((21,29,36))
    room=(420,180,1208,828) if index==1 else (500,180,1048,828)
    art.floor(terrain,room,'gallery' if index==1 else kind,index+410)
    r=dict(name=NAMES[index],ambient_kind=kind,terrain=terrain,houses=[],objects=[],nature=[],scenery=[],
        obstacles=[],npcs=[],interactables=[],exits={},spawn={},enemy_spawns=[],enemy_factory=LacreActor,
        water=[],ambient_centers=[(1024,540)],lighting=None)
    left,top,w,h=room;right=left+w
    # Stepped buttresses make the circulation octagonal, with wider gallery bays.
    cut=192 if index in (1,4) else 120
    for step in range(6):
        depth=(6-step)*cut//6
        for corner_x in (left,right-depth):
            for corner_y in (top+step*16,top+h-(step+1)*16):
                box=pygame.Rect(corner_x,corner_y,depth,16)
                pygame.draw.rect(terrain,(28,39,47),box)
                pygame.draw.line(terrain,art.EDGE,(box.left,box.bottom-1),(box.right,box.bottom-1),2)
                r['obstacles'].append(box)
    # Visible wall strips, with the north aperture occupied by a real door.
    for box in ((left-28,top-28,w+56,28),(left-28,top,28,h+24),(right,top,28,h+24),(left-28,top+h,w+56,28)):
        pygame.draw.rect(terrain,art.INK,box);pygame.draw.rect(terrain,art.STONE,pygame.Rect(box).inflate(-4,-4))
        r['obstacles'].append(pygame.Rect(box))
    for x in range(left, right,42):
        pygame.draw.line(terrain,art.EDGE,(x,top-24),(x+34,top-24),2)
    # Routes use short E transitions; no walkable destination lies beyond a wall.
    previous='threshold' if index==0 else REGIONS[index-1]
    r['spawn'][previous]=(1024,940)
    if index<4:r['spawn'][REGIONS[index+1]]=(1024,390)
    for source in REGIONS:r['spawn'].setdefault(source,(1024,940))
    interact(r,'lacre_return',(1024,966),'door',prompt='Voltar ao setor anterior',destination=previous)
    r['next_door']=env.anchored(art.door(False),(1024,316))
    r['scenery'].append(r['next_door']);r['door_box']=pygame.Rect(932,180,184,140)
    if index<4:
        interact(r,'lacre_next',(1024,362),'seal',prompt='Abrir passagem',destination=REGIONS[index+1])
    for x,y in ((left+85,420),(right-85,420),(left+85,755),(right-85,755)):
        place(r,'pillar',(x,y),True)
    for x,y in ((left+70,300),(right-70,300)):
        pygame.draw.circle(terrain,(108,100,69),(x,y),7)
    r['fires']=[(left+70,300),(right-70,300)]
    if index==0:
        interact(r,'vestibule_inscription',(720,800),'record',('Não apagar. Não devolver sem cotejo. Os mesmos três sinais do posto aparecem no batente.',
            'Há cinza recente na lamparina. Alguém voltou a usar este corredor.'))
        for uid,x,k in (('v_bowl',810,'bowl'),('v_lamp',1024,'lamp'),('v_name',1238,'name')):
            interact(r,uid,(x,560),k,prompt='Acionar '+{'bowl':'tigela','lamp':'lamparina','name':'nome'}[k])
        r['enemy_spawns']=[('lacre_guard',(1350,850)),('unstable_echo',(700,630))]
    elif index==1:
        for x,y in ((680,600),(1370,600)):place(r,'pillar',(x,y),True)
        for uid,x,k in (('g_door',800,'door'),('g_hand',1024,'hand'),('g_seal',1248,'seal')):
            interact(r,uid,(x,435),k,prompt='Acionar '+{'door':'passagem','hand':'acionamento','seal':'custódia'}[k])
        r['enemy_spawns']=[('unstable_echo',(640,830)),('lacre_guard',(1400,860)),('unstable_echo',(1280,620))]
    elif index==2:
        for x in (650,835,1200,1390):
            for y in (450,705):place(r,'searched' if x>1100 else 'shelf',(x,y),True)
        for uid,pos in (('lacre_purpose',(900,760)),('lacre_military',(1120,760)),('lacre_identity',(1040,500))):
            name,flag,lines=DOCUMENTS[uid];interact(r,uid,pos,'record',lines,prompt='Ler '+name)
        place(r,'desk',(1024,600),True)
        interact(r,'lacre_hidden',(590,850),'seal',('Uma fita cortada sai do rodapé. O desgaste contorna um painel removível.',),prompt='Examinar rodapé')
        interact(r,'lacre_cache',(650,850),'relic',('Sob o painel: duas poções, um éter e o caderno de uma conservadora.',),prompt='Abrir compartimento')
        name,flag,lines=DOCUMENTS['lacre_lore'];interact(r,'lacre_lore',(710,850),'record',lines,prompt='Ler caderno da conservadora')
        interact(r,'lacre_service',(1470,820),'key',('Trava de manutenção. A escada acompanha os depósitos até o vestíbulo, sem atravessar a galeria.',),prompt='Destravar escada de serviço')
        interact(r,'lacre_shortcut',(1470,920),'door',prompt='Descer escada de serviço',destination=REGIONS[0])
        r['enemy_spawns']=[('lacre_guard',(1280,800)),('unstable_echo',(780,520))]
    elif index==3:
        place(r,'desk',(730,610),True);place(r,'shelf',(1370,640),True)
        interact(r,'vigia_warning',(790,880),'record',('Protocolo de guarda: o vigia cobre a abertura do peito ao fechar as lâminas. A descarga expõe o encaixe.',))
        interact(r,'lacre_checkpoint',(1024,780),'rest',('O vigia desligado deixou livre o banco de manutenção. Há água e espaço para preparar a subida.',),prompt='Descansar antes do núcleo')
        r['enemy_spawns']=[('record_warden',(1024,510))]
    else:
        r['scenery'].append(env.anchored(art.core(),(1024,425)))
        r['obstacles'].append(pygame.Rect(844,220,360,200))
        for uid,pos in (('anchor_left',(760,610)),('anchor_right',(1288,610))):
            interact(r,uid,pos,'anchor',prompt='Romper conexão da âncora')
        for uid,pos in (('lacre_first',(920,470)),('lacre_second',(1128,470))):
            name,flag,lines=DOCUMENTS[uid];interact(r,uid,pos,'record',lines,prompt='Cotejar '+name)
        interact(r,'lacre_decision',(1024,545),'copy',prompt='Decidir a guarda dos registros')
        interact(r,'lacre_escape',(600,865),'door',('Passagem de manutenção liberada. A escada desce pelo exterior dos depósitos até o vestíbulo.',),prompt='Descer pela manutenção',destination=REGIONS[0])
        r['enemy_spawns']=[('custodian',(1024,570))]
    # Processional strips and repair marks differ by function, leaving combat lanes clear.
    for x in (985,1062):
        pygame.draw.line(terrain,(135,125,95),(x,390),(x,905),2)
        for y in range(430,890,76):pygame.draw.line(terrain,art.INK,(x-3,y),(x+4,y+5),2)
    if index==2:
        for x,y in ((1375,722),(1390,737),(1220,715),(1360,754)):
            pygame.draw.rect(terrain,art.PAPER,(x,y,12,8));pygame.draw.line(terrain,art.DARK,(x+2,y+3),(x+9,y+3),1)
    if index==3:
        for x,y in ((880,580),(940,680),(1140,640)):
            pygame.draw.line(terrain,art.INK,(x,y),(x+24,y-13),3)
    if index==4:
        for x in (850,1170):
            pygame.draw.lines(terrain,(138,129,103),False,[(x,465),(x,750),(1024,835)],2)
    for point in POINTS:
        if point.region==kind:
            obj=interact(r,point.uid,point.position,'seal',prompt='Escutar vestígio');obj.resonance=True
    return r
