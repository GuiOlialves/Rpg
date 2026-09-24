"""Água no plano do chão e efeitos locais no mundo, sempre abaixo do HUD."""
import math
import random
import pygame


def _prepare(region):
    if '_ambient' in region: return region['_ambient']
    kind=region.get('ambient_kind','village')
    rng=random.Random({'forest':29,'desert':43,'village':17}[kind])
    waters=[]
    for zone in region.get('water',[]):
        rect=zone['rect'].inflate(-16,-12)
        for i in range(max(4,rect.width//45)):
            waters.append((rng.randrange(rect.left,rect.right-22),rng.randrange(rect.top,rect.bottom),rng.random()*math.tau,zone['color']))
    centers={'forest':[(240,280),(580,470),(970,940),(1620,700)],
             'desert':[(490,700),(1420,850),(1830,360)],'village':[(780,480),(1200,896)]}[kind]
    particles=[]
    for cx,cy in centers:
        for i in range(3):
            particles.append((cx+rng.randrange(-48,49),cy+rng.randrange(-22,23),rng.random()*9,7+rng.random()*4))
    frames=[]
    color={'forest':(184,198,110),'desert':(244,210,151),'village':(239,212,151)}[kind]
    for alpha in range(0,151,15):
        im=pygame.Surface((10,6),pygame.SRCALPHA)
        if kind=='forest': pygame.draw.polygon(im,(*color,alpha),[(1,2),(5,0),(8,2),(4,4)])
        else: pygame.draw.line(im,(*color,alpha),(1,3),(6,2),1)
        frames.append(im)
    data={'waters':waters,'particles':particles,'frames':frames,'kind':kind}
    region['_ambient']=data
    return data


def draw_water(canvas,region,camera,ticks):
    data=_prepare(region); t=ticks*.001
    viewport=pygame.Rect(camera,canvas.get_size())
    for x,y,phase,color in data['waters']:
        if not viewport.collidepoint(x,y): continue
        drift=math.sin(t*.65+phase)*6
        width=8+round((1+math.sin(t*.9+phase))*7)
        px,py=round(x+drift-camera[0]),round(y-camera[1])
        shade=tuple(round(c*(.68+.12*math.sin(t+phase))) for c in color)
        pygame.draw.line(canvas,shade,(px,py),(px+width,py),1)
        pygame.draw.line(canvas,shade,(px+4,py+3),(px+width-2,py+3),1)


def draw(canvas,region,camera,ticks):
    data=_prepare(region); t=ticks*.001
    view=pygame.Rect(camera,canvas.get_size()).inflate(60,60)
    for x,y,phase,life in data['particles']:
        age=(t+phase)%life; u=age/life
        px=x+u*(80 if data['kind']=='desert' else 40)
        py=y+math.sin(u*math.tau+phase)*7+u*18
        if not view.collidepoint(px,py): continue
        alpha=round(math.sin(u*math.pi)*10)
        canvas.blit(data['frames'][alpha],(round(px-camera[0]),round(py-camera[1])))
    if data['kind']=='village':
        x,y=1024-camera[0],512-camera[1]
        if canvas.get_rect().inflate(90,90).collidepoint(x,y):
            for i in range(3):
                radius=6+((t*6+i*7)%20)
                pygame.draw.arc(canvas,(122,198,213),(x-radius,y-3-radius*.12,radius*2,5+radius*.24),.1,2.9,1)
            for i in range(4):
                u=(t*1.1+i*.25)%1
                px=x-13+26*(i%2)+math.sin(u*math.pi)*5
                py=y-32+u*28
                pygame.draw.line(canvas,(169,223,231),(round(px),round(py)),(round(px),round(py)+2),1)
