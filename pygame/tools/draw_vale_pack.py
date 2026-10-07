"""O Vale: authored pixel geometry; Pillow is a build-time dependency only.

32 px cast / feet (16,28); 32 x 36 hero / feet (16,34); integer 2x.
Independent cardinal drawings preserve lighting and physical accessories.
"""
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw
from hero_pixel_art import hero_sprite, hero_weapon, FRAME as HERO_FRAME, PIVOT as HERO_PIVOT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/vale_characters'
PALETTE = {
    'ink':'#252b3c', 'deep':'#343b4d', 'leather':'#61463f', 'leather_light':'#a07451',
    'skin_shadow':'#b97659', 'skin':'#e4af80', 'skin_light':'#f4cba0', 'linen':'#e1d5af',
    'hair':'#503d45', 'hair_light':'#96614f', 'grey':'#93a3a3',
    'steel':'#b7cfca', 'steel_shadow':'#657e8d', 'steel_light':'#edf0d1',
    'teal':'#3f7a78', 'teal_shadow':'#2e505c', 'teal_light':'#6ca49a',
    'blue':'#4d719a', 'blue_shadow':'#354967', 'blue_light':'#88a8c4',
    'red':'#b85c57', 'red_shadow':'#713d50', 'red_light':'#e18a67',
    'sage':'#778962', 'sage_shadow':'#495b54', 'sage_light':'#a8b57a',
    'ochre':'#c3a066', 'ochre_shadow':'#826b52', 'gold':'#d4ab65',
    'copper':'#c57550', 'copper_shadow':'#834b48', 'copper_light':'#edb26b',
    'violet':'#796786', 'violet_shadow':'#494258',
}
LOOKS = ['protagonist','civilian_man','civilian_woman','civilian_elder','civilian_merchant',
         'civilian_worker','blue_commander',*[f'blue_soldier_{i}' for i in range(3)],
         *[f'red_soldier_{i}' for i in range(3)],'red_officer','warrior','desert_scout',
         'dune_lancer','forest_guardian']
ATTACK_ANGLES = (-106,-82,-58,-12,30,61,74,92)


def attack_motion(look, frame, direction):
    curve=(-2,-3,-1,4,4,2,1,0) if look=='forest_guardian' else (-1,-2,-1,3,3,2,1,0)
    lean=curve[frame]*(-1 if direction==1 else 1)
    drop=(0,1,0,2,1,1,0,0)[frame] if look=='forest_guardian' else (0,1,0,1,1,0,0,0)[frame]
    return lean,drop


class Pen:
    def __init__(self, image): self.d = ImageDraw.Draw(image)
    def rect(self, box, color): self.d.rectangle(tuple(round(v) for v in box),fill=PALETTE.get(color,color))
    def poly(self, pts, color): self.d.polygon([(round(x),round(y)) for x,y in pts],fill=PALETTE.get(color,color))
    def line(self, pts, color, width=1): self.d.line([(round(x),round(y)) for x,y in pts],fill=PALETTE.get(color,color),width=width)


def colors(look):
    if look == 'protagonist': return 'teal','teal_shadow','teal_light'
    if look.startswith('blue'): return 'blue','blue_shadow','blue_light'
    if look.startswith('red'): return 'red','red_shadow','red_light'
    return {'civilian_man':('sage','sage_shadow','sage_light'),
            'civilian_woman':('violet','violet_shadow','linen'),
            'civilian_elder':('ochre','ochre_shadow','linen'),
            'civilian_merchant':('copper','copper_shadow','gold'),
            'civilian_worker':('linen','grey','steel_light'),
            'warrior':('steel_shadow','deep','steel'),
            'desert_scout':('ochre','ochre_shadow','linen'),
            'dune_lancer':('violet','violet_shadow','grey'),
            'forest_guardian':('sage_shadow','deep','sage')}[look]


def sprite(look, action, frame, direction):
    if look == 'protagonist':
        return hero_sprite(action,frame,direction,PALETTE)
    im = Image.new('RGBA',(32,32)); p = Pen(im)
    r, poly, line = p.rect, p.poly, p.line
    main, shade, light = colors(look)
    hero = look == 'protagonist'
    officer, commander = look == 'red_officer', look == 'blue_commander'
    guardian, scout, lancer = (look == n for n in ('forest_guardian','desert_scout','dune_lancer'))
    woman, elder, merchant, worker = (look == 'civilian_'+n for n in ('woman','elder','merchant','worker'))
    military = look.startswith(('blue','red')) or look == 'warrior'
    variant = int(look[-1]) if look[-1].isdigit() else 0
    side, back, face = direction in (1,2), direction == 3, -1 if direction == 1 else 1
    stride = (0,2,4,2,0,-2,-4,-2)[frame%8] if action in ('walk','run') else 0
    lift = int(action in ('walk','run') and frame%4 in (1,2))
    breath = int(action == 'idle' and frame in (1,2))
    lean = ((-1,-2,0,2,2,1,0,0)[frame]*(face if side else 1) if action == 'attack'
            else -face if action == 'windup' else face*2 if action == 'dash' and side
            else -face if action == 'hurt' else 0)
    if action == 'attack': stride = (-1,-2,0,2,2,1,0,0)[frame]
    if action == 'windup': stride = -2
    if action in ('attack','windup'):
        lean,lift=attack_motion(look,frame,direction)
        stride=(-1,-3,-2,3,3,2,1,0)[frame]
    if action == 'dash':
        lean = (0,3,1)[frame] * (face if side else 1)
        lift = (0,-1,0)[frame]
    if action == 'hurt':
        lean = (-2,-1,0)[frame] * (face if side else 1)
        lift = (1,1,0)[frame]
    cx, top = 16+lean, 2+lift
    if guardian: top = 1+lift
    if elder: top+=2
    if merchant: top+=1
    if worker: top-=1
    if action in ('fallen','death') and (action == 'fallen' or frame >= 2):
        poly([(3,23),(7,19),(13,20),(16,23),(25,23),(29,26),(27,29),(8,29),(3,27)],'ink')
        r((5,23,11,27),'skin_shadow'); r((6,22 if frame==1 else 23,10,25),'skin')
        r((4,22,8,23),'grey' if elder else 'hair')
        r((12,23,22,27),shade); r((13,23,19,24),main)
        r((23,25,28,28),'leather'); r((25,26,28,26),'leather_light')
        line([(8,25),(10,25)],'ink')
        if hero: r((11,24,15,25),'copper')
        if military: r((16,24,18,25),'gold')
        if commander: r((4,21,8,22),'blue')
        return im
    if action == 'defeated' or (action == 'death' and frame==1):
        top += 6
        poly([(9,22),(18,22),(23,25),(23,27),(12,27),(8,25)],'ink')
        r((10,23,17,25),'deep'); r((19,26,23,27),'leather_light')
    elif woman or elder:
        poly([(11,18),(20,18),(23,25),(22,27),(9,27),(9,25)],'ink')
        poly([(12,19),(19,19),(21,25),(10,25)],shade)
        line([(12,20),(11,24)],main)
        r((11-stride//2,26-lift,14-stride//2,27-lift),'leather')
        r((18+stride//2,26,21+stride//2,27),'leather')
        r((11-stride//2,26-lift,13-stride//2,26-lift),'leather_light')
    else:
        for leg,step in ((-1,stride),(1,-stride)):
            lx = (13 if leg==-1 else 17) if side else (12 if leg==-1 else 18)
            fx = lx+(step if side else leg*abs(step)//2)
            fy = 27-((0,1,2,1,0,0,0,0)[(frame+(4 if leg<0 else 0))%8] if action in ('walk','run') else 0)
            if action == 'dash': fx += leg*(1,3,1)[frame]; fy -= (0,2,0)[frame] if leg<0 else 0
            poly([(lx,20),(lx+3,20),(fx+3,fy),(fx-1,fy),(fx-1,fy-2)],'ink')
            line([(lx+1,21),(fx+1,fy-3)],'deep',2)
            r((fx-1,fy-2,fx+3,fy-1),'leather'); r((fx,fy-2,fx+2,fy-2),'leather_light')
            if military or lancer: r((lx+1,22,lx+2,23),'steel_shadow')
    y = 12+lift-breath+int(merchant)+2*int(elder)
    if hero or officer or commander or guardian:
        w = 10 if guardian else 9 if officer else 7
        poly([(cx-6,y),(cx+5,y),(cx+w,25),(cx+3,26),(cx,23),(cx-6,25),(cx-w,23)],'ink')
        poly([(cx-5,y+1),(cx+4,y+1),(cx+w-2,24),(cx+3,24),(cx,21),(cx-6,23)],shade)
        line([(cx-4,y+2),(cx-5,21)],main,2)
        if officer: line([(cx+6,19),(cx+7,23)],'gold')
    width = 8 if guardian else 7 if military or merchant else 5 if side else 6
    if look == 'warrior': width = 8
    poly([(cx-width+2,y),(cx+width-2,y),(cx+width,y+3),(cx+width-1,y+9),(cx-3,y+11),(cx-width,y+8),(cx-width,y+3)],'ink')
    poly([(cx-width+2,y+1),(cx+width-2,y+1),(cx+width-1,y+4),(cx+width-2,y+9),(cx-width+1,y+9),(cx-width+1,y+3)],shade)
    poly([(cx-width+2,y+1),(cx+1,y+1),(cx+3,y+6),(cx-1,y+8),(cx-width+2,y+8)],main)
    line([(cx-width+3,y+2),(cx-1,y+2)],light)
    if military or lancer:
        poly([(cx-5,y+1),(cx+4,y+1),(cx+5,y+6),(cx+2,y+8),(cx-4,y+7)],'steel_shadow')
        poly([(cx-4,y+1),(cx+1,y+1),(cx+2,y+6),(cx-3,y+6)],'steel')
        line([(cx-3,y+2),(cx-1,y+2)],'steel_light'); line([(cx-4,y+7),(cx+3,y+7)],'deep')
        r((cx-3,y+8,cx+3,y+10),main)
    if back and hero:
        poly([(cx-4,y+2),(cx+3,y+2),(cx+5,y+8),(cx+1,y+10),(cx-5,y+8)],'ink')
        r((cx-3,y+3,cx+3,y+7),'leather'); r((cx-2,y+3,cx+2,y+4),'leather_light')
        line([(cx-2,y+6),(cx+2,y+6)],'gold')
    elif hero:
        line([(cx-4,y+1),(cx+4,y+8)],'ink',3); line([(cx-4,y+1),(cx+4,y+8)],'linen')
        r((cx,y+4,cx+1,y+5),'gold')
    line([(cx-width+1,y+9),(cx+width-2,y+9)],'leather',2)
    r((cx-1,y+9,cx+1,y+10),'gold'); r((cx,y+9,cx,y+9),'linen')
    if worker:
        r((cx-4,y+3,cx+4,y+9),'leather'); r((cx-3,y+3,cx+3,y+6),'leather_light')
        for xx in (cx-3,cx+3): line([(xx,y),(xx,y+3)],'leather')
        r((cx+1,y+6,cx+3,y+8),'deep'); r((cx+2,y+6,cx+2,y+7),'steel')
    if woman:
        r((cx-3,y+4,cx+3,y+9),'linen'); r((cx-2,y+4,cx+2,y+5),'gold')
        line([(cx-4,y+1),(cx+4,y+1)],'ochre')
    if elder:
        line([(cx-3,y+2),(cx-3,y+8)],'linen'); line([(cx+3,y+2),(cx+3,y+8)],'gold')
    if merchant:
        r((cx-4,y+6,cx-2,y+8),'gold'); r((cx+3,y+6,cx+5,y+10),'leather')
        r((cx+4,y+7,cx+5,y+8),'copper_light')
    if guardian:
        poly([(cx-6,y+1),(cx-1,y),(cx+5,y+2),(cx+6,y+7),(cx+1,y+9),(cx-6,y+7)],'steel_shadow')
        poly([(cx-5,y+2),(cx-1,y+1),(cx+2,y+3),(cx+1,y+7),(cx-4,y+6)],'sage')
        line([(cx-2,y+2),(cx,y+4),(cx-1,y+7)],'deep'); r((cx-3,y+2,cx-2,y+3),'sage_light')
    if scout:
        line([(cx-4,y+1),(cx+5,y+8)],'leather_light',2)
        for qx in (cx-6,cx-4,cx-2): line([(qx,y+2),(qx-1,y-3)],'steel_shadow')
    for arm in (-1,1):
        ax, swing = cx+arm*(width+1), -stride if arm==1 else stride
        elbow, hand = (ax+arm,y+4+swing//2),(ax,y+8+swing)
        if action in ('attack','windup'):
            phase = frame
            if arm==1:
                angle=(math.pi/2,math.pi,0,-math.pi/2)[direction]+math.radians(ATTACK_ANGLES[phase])
                # The same authored grip coordinates as the separate weapon layer.
                hand=(round(cx+math.cos(angle)*8),round(18+lift+math.sin(angle)*8))
                elbow=((ax+hand[0])//2,y+3)
            else: hand=(cx-7,y+5-int(frame in (2,3)))
            if scout:
                bow_x=7 if direction==1 else 25
                hand=(bow_x,y+6) if arm==1 else (cx,y+5+int(frame>1))
                elbow=((ax+hand[0])//2,y+4)
        if action=='dash': hand=(ax-face*(2,5,1)[frame],y+6)
        if action=='hurt': hand=(ax-arm*(2,1,0)[frame],y+(3,4,6)[frame])
        line([(ax,y+2),elbow,hand],'ink',4)
        line([(ax,y+2),elbow],main if arm<0 else shade,2)
        line([elbow,hand],'steel_shadow' if hero and arm==1 else main,2)
        r((hand[0]-1,hand[1]-1,hand[0],hand[1]),'skin')
        r((hand[0]-1,hand[1]-1,hand[0]-1,hand[1]-1),'skin_light')
    if elder:
        line([(24,y+6),(25,27)],'ink',2); line([(24,y+6),(25,26)],'leather_light')
        r((23,y+5,25,y+5),'gold')
    if military and not officer:
        sx = cx-8 if not side else cx+(5 if face<0 else -5)
        sw = 8 if variant==2 else 6
        poly([(sx-3,y+3),(sx+sw-3,y+3),(sx+sw-2,y+8),(sx+1,y+13),(sx-4,y+9)],'ink')
        poly([(sx-2,y+4),(sx+sw-4,y+4),(sx+sw-3,y+8),(sx+1,y+11),(sx-3,y+8)],shade)
        line([(sx-2,y+4),(sx+sw-4,y+4),(sx+sw-3,y+7)],'steel')
        line([(sx,y+5),(sx+1,y+9)],'gold' if commander else light)
        if variant==1: line([(sx-1,y+7),(sx+2,y+7)],'linen')
    hx, hy = cx-5+(face if side else 0), top
    poly([(hx+2,hy),(hx+7,hy),(hx+9,hy+2),(hx+10,hy+5),(hx+9,hy+9),(hx+6,hy+11),(hx+2,hy+10),(hx,hy+7),(hx,hy+3)],'ink')
    r((hx+1,hy+3,hx+8,hy+7),'skin_shadow'); r((hx+2,hy+3,hx+7,hy+8),'skin')
    line([(hx+2,hy+4),(hx+4,hy+3),(hx+6,hy+3)],'skin_light')
    r((hx+4,hy+9,hx+6,hy+9),'skin_shadow')
    if hero or officer or woman or elder or worker or merchant or look=='civilian_man':
        hc='grey' if elder else 'hair'
        poly([(hx,hy+5),(hx,hy+2),(hx+2,hy),(hx+4,hy),(hx+6,hy-1 if hero else hy),(hx+7,hy+1),(hx+9,hy+2),(hx+9,hy+4),(hx+6,hy+3),(hx+5,hy+5),(hx+3,hy+3),(hx+2,hy+6)],hc)
        line([(hx+1,hy+2),(hx+3,hy+1),(hx+5,hy+2)],'linen' if elder else 'hair_light')
        r((hx+6,hy+1,hx+7,hy+2),'linen' if elder else 'leather_light')
        if not side: r((hx,hy+6,hx+1,hy+8),hc)
        if hero: r((hx-1,hy+4,hx,hy+6),'hair'); r((hx+2,hy+3,hx+3,hy+4),'hair_light')
        if woman:
            poly([(hx-1,hy+4),(hx,hy+3),(hx+1,hy+9),(hx,hy+13),(hx-2,hy+11)],'ink')
            line([(hx-1,hy+5),(hx-1,hy+10),(hx,hy+11)],'hair_light',2)
            r((hx-1,hy+9,hx,hy+9),'gold')
        if elder:
            poly([(hx+2,hy+8),(hx+7,hy+8),(hx+6,hy+12),(hx+3,hy+11)],'linen')
            line([(hx+4,hy+9),(hx+5,hy+11)],'grey')
        if officer:
            r((hx,hy+5,hx+1,hy+7),'grey'); line([(hx+3,hy+9),(hx+6,hy+9)],'hair')
            line([(hx+6,hy+4),(hx+8,hy+4)],'hair')
        if merchant:
            poly([(hx-2,hy+3),(hx,hy+2),(hx+1,hy),(hx+8,hy),(hx+9,hy+2),(hx+11,hy+3),(hx+10,hy+4),(hx-2,hy+4)],'ink')
            r((hx+1,hy+1,hx+8,hy+2),'ochre'); line([(hx-1,hy+3),(hx+9,hy+3)],'gold')
        if worker:
            line([(hx+1,hy+3),(hx+8,hy+3)],'teal_light',2); r((hx-1,hy+4,hx,hy+6),'teal_shadow')
    elif scout:
        poly([(hx-1,hy+6),(hx,hy+1),(hx+3,hy),(hx+8,hy),(hx+11,hy+4),(hx+10,hy+9),(hx+6,hy+10),(hx+8,hy+6)],'ink')
        poly([(hx,hy+5),(hx+1,hy+1),(hx+5,hy+1),(hx+8,hy+2),(hx+9,hy+5),(hx+6,hy+4),(hx+2,hy+4)],'ochre')
        line([(hx+2,hy+2),(hx+5,hy+1),(hx+7,hy+2)],'linen')
        r((hx+2,hy+7,hx+9,hy+9),'linen'); r((hx+5,hy+9,hx+9,hy+10),'ochre_shadow')
    elif guardian:
        poly([(hx-2,hy+3),(hx+1,hy),(hx+8,hy),(hx+11,hy+4),(hx+10,hy+10),(hx+1,hy+10)],'ink')
        poly([(hx-1,hy+4),(hx+2,hy+1),(hx+7,hy+1),(hx+9,hy+4),(hx+8,hy+8),(hx,hy+8)],'steel_shadow')
        line([(hx+1,hy+3),(hx+4,hy+1),(hx+6,hy+2)],'sage_light')
        r((hx+1,hy+5,hx+8,hy+6),'deep')
        for xx in (hx+2,hx+6): r((xx,hy+5,xx+1,hy+5),'gold')
        for sign in (-1,1):
            start=hx+4+sign*5
            line([(start,hy+3),(start+sign*3,hy+1),(start+sign*4,hy)],'ink',3)
            line([(start,hy+2),(start+sign*3,hy)],'gold')
    else:
        poly([(hx-1,hy+5),(hx,hy+2),(hx+3,hy),(hx+7,hy),(hx+10,hy+3),(hx+10,hy+8),(hx+8,hy+10),(hx+7,hy+5),(hx+2,hy+5),(hx+1,hy+10),(hx-1,hy+8)],'ink')
        poly([(hx,hy+4),(hx+1,hy+2),(hx+4,hy+1),(hx+7,hy+1),(hx+9,hy+4)],'steel_shadow')
        line([(hx+1,hy+3),(hx+4,hy+2),(hx+6,hy+2)],'steel')
        r((hx-1,hy+5,hx+1,hy+8),main); r((hx+8,hy+5,hx+9,hy+8),shade)
        if lancer:
            poly([(hx+3,hy+1),(hx+5,hy),(hx+7,hy+1),(hx+6,hy+5),(hx+4,hy+5)],'steel')
            r((hx+2,hy+7,hx+8,hy+9),'deep'); line([(hx+3,hy+8),(hx+6,hy+8)],'violet')
        else:
            plume='gold' if commander else 'copper' if look.startswith('red') or look=='warrior' else 'blue_light'
            poly([(hx+3,hy),(hx+3,hy-1),(hx+7,hy-1),(hx+9,hy+1),(hx+7,hy+2),(hx+6,hy+1)],plume)
            if variant==1: line([(hx+4,hy+1),(hx+4,hy+4)],'gold')
            if variant==2: r((hx-2,hy+4,hx-1,hy+6),'steel')
    if back:
        r((hx+1,hy+5,hx+8,hy+8),'grey' if elder else shade if military or lancer else 'ochre_shadow' if scout else 'hair')
        line([(hx+2,hy+6),(hx+5,hy+7)],'grey' if military or lancer else 'hair_light')
    elif not guardian:
        for ex in ((hx+3,hx+7) if not side else (hx+2,) if face<0 else (hx+7,)):
            r((ex,hy+6,ex+1,hy+7),'ink')
            r((ex,hy+6,ex,hy+6),'linen')
            if (action=='hurt' and frame<2) or (action=='idle' and frame==2):
                r((ex,hy+7,ex+1,hy+7),'skin_shadow')
                r((ex,hy+6,ex+1,hy+6),'ink')
        if not side and not elder and not scout:
            r((hx+5,hy+8,hx+5,hy+8),'skin_shadow')
            line([(hx+4,hy+9),(hx+6,hy+9)],'skin_shadow')
    if hero:
        line([(cx-4,hy+11),(cx+3,hy+11)],'copper_shadow',3)
        line([(cx-4,hy+10),(cx+2,hy+10)],'copper',2); r((cx-3,hy+10,cx-2,hy+10),'copper_light')
        tail=(0,2,1)[frame] if action=='dash' else int(action in ('walk','run') or action=='idle' and frame==3)
        poly([(cx-5,hy+11),(cx-2,hy+12),(cx-4-tail,hy+17),(cx-7-tail,hy+16)],'copper_shadow')
        line([(cx-4,hy+12),(cx-5-tail,hy+15)],'copper')
        if action not in ('attack','windup'):
            line([(cx-7,20),(cx-9,25)],'ink',3); line([(cx-7,20),(cx-9,24)],'steel_shadow')
            line([(cx-8,20),(cx-5,21)],'gold')
    if officer or commander:
        r((cx-7,y+1,cx-4,y+3),'gold'); r((cx-6,y+1,cx-5,y+1),'linen')
        line([(cx-5,y+3),(cx+3,y+6)],'gold')
    if officer:
        # An asymmetric command mantle and a long split cloak distinguish the duelist.
        poly([(cx-9,y-1),(cx-5,y-2),(cx-1,y),(cx-2,y+4),(cx-8,y+3)],'ink')
        poly([(cx-8,y),(cx-5,y-1),(cx-2,y+1),(cx-3,y+3),(cx-7,y+2)],'gold')
        line([(cx-7,y),(cx-5,y),(cx-3,y+1)],'linen')
        line([(cx+6,y+4),(cx+8,24),(cx+5,25)],'red_light')
        line([(cx-2,y+3),(cx+3,y+5)],'linen')
        r((hx+7,hy+7,hx+7,hy+8),'copper_shadow')
    if commander:
        r((hx+2,hy,hx+6,hy),'gold')
        r((cx+4,y+3,cx+6,y+5),'gold')
        r((cx+5,y+3,cx+5,y+3),'linen')
    if look == 'warrior':
        # The wandering knight has a closed visor, heavy pauldrons and a battered kite shield.
        r((hx+1,hy+5,hx+8,hy+8),'steel_shadow')
        line([(hx+2,hy+6),(hx+7,hy+6)],'deep',2)
        for xx in (hx+3,hx+6): r((xx,hy+8,xx,hy+9),'deep')
        poly([(cx-9,y),(cx-6,y-1),(cx-3,y+1),(cx-5,y+4),(cx-10,y+3)],'ink')
        poly([(cx-8,y),(cx-6,y),(cx-4,y+2),(cx-6,y+3),(cx-9,y+2)],'steel')
        poly([(cx-12,y+4),(cx-7,y+3),(cx-4,y+6),(cx-7,y+14),(cx-12,y+10)],'ink')
        poly([(cx-11,y+5),(cx-7,y+4),(cx-5,y+6),(cx-7,y+12),(cx-11,y+9)],'ochre_shadow')
        line([(cx-10,y+5),(cx-7,y+5),(cx-6,y+7)],'steel')
        line([(cx-8,y+6),(cx-9,y+9)],'gold')
        r((cx-6,y+8,cx-6,y+8),'deep')
    if scout:
        bx=6 if direction==1 else 25
        line([(bx-2,y+2),(bx+1,y+4),(bx+2,y+8),(bx,y+11),(bx-2,y+12)],'ink',2)
        line([(bx-2,y+2),(bx,y+4),(bx+1,y+8),(bx-2,y+12)],'copper_light')
        if action in ('windup','attack') and frame<3:
            line([(bx-2,y+2),(cx,y+6),(bx-2,y+12)],'linen')
            line([(cx,y+6),(bx+4*face,y+6)],'leather_light')
            r((bx+4*face,y+6,bx+4*face,y+6),'steel_light')
        else: line([(bx-2,y+2),(bx-2,y+12)],'linen')
    elif lancer and action not in ('attack','windup'):
        line([(25,6),(24,27)],'ink',3); line([(25,7),(24,26)],'leather_light')
        poly([(25,1),(22,7),(25,9),(28,6)],'ink'); poly([(25,2),(23,6),(25,7),(26,5)],'steel')
        r((24,9,26,9),'copper')
    elif guardian and action not in ('attack','windup','death'):
        line([(25,22),(26,9)],'ink',3); line([(25,21),(26,10)],'leather_light',2)
        poly([(26,3),(23,9),(23,13),(26,14),(29,11),(28,6)],'ink')
        poly([(26,4),(24,10),(25,12),(27,11),(27,7)],'steel_shadow')
        line([(26,5),(24,10)],'sage_light')
        line([(23,15),(28,15)],'gold')
    if guardian:
        # Asymmetric broken stone shoulders and hanging roots, rather than scaled armour.
        poly([(cx-11,y),(cx-7,y-3),(cx-3,y),(cx-4,y+5),(cx-10,y+4)],'ink')
        poly([(cx-10,y),(cx-7,y-2),(cx-4,y+1),(cx-5,y+3),(cx-9,y+2)],'sage')
        line([(cx-9,y),(cx-7,y-1),(cx-5,y)],'sage_light')
        poly([(cx+4,y),(cx+8,y-1),(cx+10,y+2),(cx+8,y+5),(cx+4,y+3)],'ink')
        poly([(cx+5,y+1),(cx+8,y),(cx+9,y+2),(cx+7,y+3)],'steel_shadow')
        line([(cx-8,y+4),(cx-9,y+7),(cx-8,y+10)],'sage_shadow')
        line([(cx+7,y+4),(cx+6,y+7)],'sage')
    elif military and action not in ('attack','windup'):
        line([(25,22),(28,14)],'ink',3); line([(26,20),(28,14)],'steel')
        line([(24,21),(27,22)],'gold')
    return im


def weapon_sprite(look, frame, direction, collision=False, heavy=False):
    if look == 'protagonist': return hero_weapon(frame,direction,PALETTE,collision)
    size=160 if heavy else 96
    mid=size//2
    im=Image.new('RGBA',(size,size)); p=Pen(im)
    base=(math.pi/2,math.pi,0,-math.pi/2)[direction]
    lean,drop=attack_motion(look,frame,direction)
    old_lean,old_drop=attack_motion(look,max(0,frame-1),direction)
    angle=base+math.radians(ATTACK_ANGLES[frame]); center=(mid+lean,mid+drop)
    # North is foreshortened; south projects into the foreground. These extents
    # keep the old cardinal reach while bringing the hand back to the torso.
    blade_reach={'forest_guardian':36,'red_officer':32,'warrior':30,'dune_lancer':40}.get(look,27)
    blade_reach+=2 if direction==0 else -2 if direction==3 else 0
    reach=blade_reach
    def point(rad,theta): return (center[0]+math.cos(theta)*rad,center[1]+math.sin(theta)*rad)
    prev=base+math.radians(ATTACK_ANGLES[max(2,frame-1)] if collision else ATTACK_ANGLES[max(0,frame-1)])
    if collision:
        if frame not in range(2,7): return im
        p.poly([point(8,prev),*[point(reach,prev+(angle-prev)*i/12) for i in range(13)],point(8,angle)],(255,255,255,255))
        p.line([point(8,angle),point(reach,angle)],(255,255,255,255),4)
        return im
    if frame in (3,4):
        arc=[(mid+old_lean+(lean-old_lean)*i/12+math.cos(prev+(angle-prev)*i/12)*reach,
              mid+old_drop+(drop-old_drop)*i/12+math.sin(prev+(angle-prev)*i/12)*reach) for i in range(13)]
        inner_reach=reach-(4 if heavy else 2)
        inner=[point(inner_reach,prev+(angle-prev)*i/12) for i in range(12,-1,-1)]
        p.poly(arc+inner,(212,171,101,100 if heavy else 75)); p.line(arc[4:],'steel_light')
    # Heavy strikes widen the sweep, keeping the same physical sword in the hand.
    grip,tip=point(8,angle),point(blade_reach-1,angle)
    p.line([point(10,angle),tip],'ink',4)
    if look=='dune_lancer':
        p.line([point(3,angle),point(reach-5,angle)],'leather_light',2)
        p.poly([tip,point(reach-7,angle-.13),point(reach-7,angle+.13)],'steel')
    else:
        perp=(-math.sin(angle),math.cos(angle)); bb=point(12,angle)
        width=3 if look=='forest_guardian' else 2
        near_tip=point(blade_reach-5,angle)
        p.poly([(bb[0]-perp[0]*width,bb[1]-perp[1]*width),
                (near_tip[0]-perp[0],near_tip[1]-perp[1]),tip,
                (near_tip[0]+perp[0],near_tip[1]+perp[1]),
                (bb[0]+perp[0]*width,bb[1]+perp[1]*width)],'steel')
        p.line([(bb[0]+perp[0]*width,bb[1]+perp[1]*width),
                (near_tip[0]+perp[0],near_tip[1]+perp[1])],'steel_shadow')
        p.line([(bb[0]-perp[0],bb[1]-perp[1]),tip],'steel_light'); h=point(11,angle)
        p.line([(h[0]-perp[0]*3,h[1]-perp[1]*3),(h[0]+perp[0]*3,h[1]+perp[1]*3)],'ink',3)
        p.line([(h[0]-perp[0]*2,h[1]-perp[1]*2),(h[0]+perp[0]*2,h[1]+perp[1]*2)],'gold')
        p.line([point(6,angle),point(9,angle)],'leather_light',2)
    p.rect((grip[0]-1,grip[1]-1,grip[0]+1,grip[1]),'skin')
    return im


def effects():
    for name in ('impact','critical','dust'):
        sheet=Image.new('RGBA',(144,24))
        for f in range(6):
            tile=Image.new('RGBA',(24,24)); p=Pen(tile)
            for i in range(7):
                a=i*math.tau/7+.28; rad=2+f*1.5
                x,y=round(12+math.cos(a)*rad),round(12+math.sin(a)*rad*.65)
                col='copper_light' if name=='critical' else 'steel_light' if name=='impact' else 'ochre'
                if name=='dust':
                    rgb=tuple(int(PALETTE[col][j:j+2],16) for j in (1,3,5))
                    p.rect((x,y-f//2,x+1,y+1-f//2),(*rgb,max(20,140-f*25)))
                elif f<4: p.line([(x,y),(x+round(math.cos(a)*2),y+round(math.sin(a)*2))],col,2 if name=='critical' else 1)
                else: p.rect((x,y,x,y),col)
            if f<2 and name!='dust':
                p.line([(8+f,12),(16-f,12)],'linen'); p.line([(12,8+f),(12,16-f)],'linen')
            sheet.paste(tile,(f*24,0))
        sheet.save(OUT/f'fx_{name}.png')


def build(looks=None):
    OUT.mkdir(parents=True,exist_ok=True)
    selected=LOOKS if looks is None else looks
    previous=json.loads((OUT/'manifest.json').read_text(encoding='utf-8')) if looks and (OUT/'manifest.json').exists() else {}
    manifest={'frame_size':[32,32],'pivot':[16,28],'draw_scale':2,
              'directions':['down','left','right','up'],'palette':PALETTE,'characters':{},
              'weapons':{'frame_size':[96,96],'pivot':[48,58],'frames_per_direction':8,
                         'heavy_frame_size':[160,160],'heavy_pivot':[80,90]}}
    manifest['characters'].update(previous.get('characters',{}))
    for look in selected:
        actions={'idle':4,'walk':8}
        armed=look=='protagonist' or look.startswith('red') or look in ('warrior','forest_guardian','dune_lancer','desert_scout')
        if armed: actions.update(attack=8,windup=2,hurt=3,death=4)
        if look=='protagonist': actions.update(dash=5)
        if look.startswith(('blue','red')): actions['fallen']=2 if look=='blue_commander' else 1
        if look=='red_officer': actions['defeated']=1
        manifest['characters'][look]={}
        for action,count in actions.items():
            width,height=HERO_FRAME if look=='protagonist' else (32,32)
            sheet=Image.new('RGBA',(width*count,height*4))
            for direction in range(4):
                for index in range(count): sheet.paste(sprite(look,action,index,direction),(width*index,height*direction))
            filename=f'{look}_{action}.png'; sheet.save(OUT/filename)
            manifest['characters'][look][action]={'file':filename,'frames_per_direction':count}
            if look=='protagonist':
                manifest['characters'][look][action].update(frame_size=list(HERO_FRAME),pivot=list(HERO_PIVOT))
        if armed and look!='desert_scout':
            for suffix,collision in (('weapon',False),('hit',True)):
                sheet=Image.new('RGBA',(96*8,96*4))
                for direction in range(4):
                    for index in range(8): sheet.paste(weapon_sprite(look,index,direction,collision),(96*index,96*direction))
                sheet.save(OUT/f'{look}_{suffix}.png')
            if look in ('red_officer','forest_guardian'):
                sheet=Image.new('RGBA',(160*8,160*4))
                for direction in range(4):
                    for index in range(8): sheet.paste(weapon_sprite(look,index,direction,heavy=True),(160*index,160*direction))
                sheet.save(OUT/f'{look}_heavy_weapon.png')
    for look,filename in (('civilian_man','civilian_customer'),('civilian_woman','civilian_seller')):
        if look in selected: Image.open(OUT/f'{look}_idle.png').save(ROOT/f'assets/npc/{filename}.png')
    for action,count,filename in (('walk',6,'f_player_sheet'),('attack',8,'f_player_attack_sheet')):
        if 'protagonist' not in selected: continue
        compatible=Image.new('RGBA',(64*count,256))
        for direction in range(4):
            for index in range(count):
                compatible.paste(sprite('protagonist','idle' if action=='walk' and index==0 else action,index,direction),(64*index+16,64*direction+48-HERO_PIVOT[1]))
        compatible.save(ROOT/f'assets/player/{filename}.png')
    manifest['player_compatibility']={'cell_size':[64,64],'native_offset':[16,48-HERO_PIVOT[1]],'pivot':[32,48],'walk_columns':6,'attack_columns':8}
    if looks is None: effects()
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f'Built {len(selected)} characters and their weapon layers.')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--look',action='append',choices=LOOKS)
    build(parser.parse_args().look)
