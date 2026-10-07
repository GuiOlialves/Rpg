"""Authored 32 x 36 protagonist with compact joints and independent profiles.

Body pivot (16,34) maps to (48,58) in the separate sword atlas.
"""
import math
from PIL import Image, ImageDraw

FRAME = (32,36)
PIVOT = (16,34)
# Shorter legs use ten native pixels between contacts, a 40 world-pixel cycle.
WALK_STEPS = (5,2,0,-3,-5,-2,0,3)
WALK_LIFT = (0,0,0,0,1,3,2,1)
SWORD_TIP = 14
SWORD_GRIPS = (
    ((10,23),(9,23),(10,25),(15,29),(21,27),(23,24),(17,23),(13,18)),
    ((19,17),(19,15),(14,16),(8,20),(8,23),(11,25),(12,23),(13,18)),
    ((12,17),(12,15),(17,16),(23,20),(23,23),(20,25),(16,23),(13,18)),
    ((21,23),(22,23),(21,18),(17,15),(11,16),(9,20),(16,21),(19,18)),
)
SWORD_ANGLES = (
    (180,170,145,90,35,5,60,115),
    (-45,-65,-115,-170,-210,-250,-255,-245),
    (-135,-115,-65,-10,30,70,100,115),
    (60,85,140,200,240,285,350,425),
)
LIPS = '#8b564d'


def compact_y(y):
    """Shorten torso and legs around the existing foot pivot, on the pixel grid."""
    if y <= 12: return round(y + 6)
    if y <= 24: return round(18 + (y - 12) * .75)
    return round(27 + (y - 24) * .7)


class Brush:
    def __init__(self,image,palette,compact=True):
        self.image,self.compact=image,compact
        self.d,self.palette=ImageDraw.Draw(image),palette
    def color(self,value): return self.palette.get(value,value)
    def point(self,point): return (point[0],compact_y(point[1])) if self.compact else point
    def rect(self,box,color): self.d.rectangle((*self.point(box[:2]),*self.point(box[2:])),fill=self.color(color))
    def poly(self,points,color): self.d.polygon([self.point(pt) for pt in points],fill=self.color(color))
    def line(self,points,color,width=1): self.d.line([self.point(pt) for pt in points],fill=self.color(color),width=width)


def head(p,direction,x=0,y=0,blink=False,tense=False):
    """Small eyes without white blocks; a short nose, soft jaw and quiet mouth."""
    if p.compact:
        # Keep every facial feature at its authored size while lowering the head.
        p=Brush(p.image,p.palette,compact=False)
        y+=6
    r=lambda box,c: p.rect(tuple(v+(x if i%2==0 else y) for i,v in enumerate(box)),c)
    poly=lambda pts,c: p.poly([(a+x,b+y) for a,b in pts],c)
    line=lambda pts,c,w=1: p.line([(a+x,b+y) for a,b in pts],c,w)
    if direction==3:
        poly([(11,4),(12,2),(16,1),(19,2),(21,4),(21,8),(19,11),(14,11),(11,8)],'ink')
        poly([(12,4),(14,2),(18,2),(20,4),(20,8),(18,10),(14,10)],'hair')
        line([(12,5),(14,3),(17,3)],'hair_light')
        line([(13,7),(15,9),(19,7)],'leather')
        r((11,7,11,8),'skin_shadow'); r((21,7,21,8),'skin')
        r((15,11,18,11),'hair'); return
    if direction==0:
        poly([(11,4),(12,2),(15,1),(18,1),(20,3),(21,5),(21,8),(19,11),(14,11),(12,9),(11,7)],'ink')
        poly([(12,4),(18,4),(20,5),(20,8),(18,10),(14,10),(12,8)],'skin_shadow')
        poly([(13,5),(18,5),(19,6),(19,9),(17,10),(14,9),(13,7)],'skin')
        r((13,6,13,7),'skin_light'); r((15,10,17,10),'skin_light')
        line([(14,5),(15,5+int(tense))],'#91634c')
        line([(17,5+int(tense)),(18,5)],'#91634c')
        for ex in (14,18):
            if blink: line([(ex-1,7),(ex,7)],'#805344')
            else: r((ex,6,ex,6),'#49362f')
        r((16,8,16,8),'skin_shadow'); r((15,8,15,8),'skin_light')
        line([(15,9),(16,9)],LIPS)
        poly([(11,6),(11,4),(12,2),(15,1),(18,1),(20,3),(20,5),
              (18,4),(17,5),(16,3),(14,4),(13,5),(12,7)],'hair')
        line([(12,3),(15,2),(17,2)],'hair_light')
        r((18,3,19,3),'hair_light'); return
    if direction==2:
        poly([(12,3),(14,1),(18,1),(20,3),(20,5),(21,7),(21,8),(20,9),(19,11),(15,11),(12,9)],'ink')
        poly([(16,4),(19,4),(20,6),(21,7),(20,8),(20,9),(18,10),(15,9)],'skin_shadow')
        poly([(17,5),(19,5),(19,6),(20,7),(20,8),(19,8),(19,9),(17,10),(16,8)],'skin')
        r((18,5,19,5),'#91634c')
        r((19,6 if not blink else 7,19,6 if not blink else 7),'#49362f')
        r((20,7,20,7),'skin_light'); r((19,9,20,9),LIPS)
        r((18,10,19,10),'skin_light')
        poly([(12,8),(12,3),(14,1),(18,1),(20,3),(20,4),(18,4),
              (17,6),(16,5),(15,9),(14,10)],'hair')
        line([(13,3),(15,2),(18,2)],'hair_light')
        r((15,7,16,8),'skin_shadow'); r((15,7,15,7),'skin_light')
        r((13,6,13,8),'hair_light')
    else:
        poly([(11,4),(13,2),(16,1),(19,2),(20,4),(20,8),(18,11),(14,11),
              (12,10),(11,8),(10,8),(10,7),(11,6)],'ink')
        poly([(12,4),(16,4),(18,6),(17,9),(15,10),(13,9),(12,8),(11,7),(12,6)],'skin_shadow')
        poly([(13,5),(15,5),(16,7),(15,9),(13,9),(12,8),(11,7),(13,7)],'skin')
        r((12,5,13,5),'#91634c')
        r((12,6 if not blink else 7,12,6 if not blink else 7),'#49362f')
        r((11,7,11,7),'skin_light'); r((12,9,13,9),LIPS); r((14,10,16,10),'skin_light')
        poly([(11,5),(11,3),(13,2),(16,1),(19,2),(20,4),(20,8),(18,10),
              (17,8),(17,5),(16,4),(15,5),(14,4),(13,5),(12,4)],'hair')
        line([(12,3),(14,2),(16,2)],'hair_light')
        line([(19,5),(19,8)],'hair_light')
        r((17,7,18,8),'skin_shadow'); r((17,7,17,7),'skin')


def leg(p,hip,knee,foot,far=False):
    """Fitted trousers, articulated knee, five-pixel boot and a flat sole."""
    hx,hy=hip; kx,ky=knee; fx,fy=foot
    p.line([hip,knee,(fx,fy-3)],'ink',4)
    p.line([hip,knee,(fx,fy-4)],'deep',2)
    if not far: p.line([(hx-1,hy+1),(kx-1,ky)],'steel_shadow')
    p.poly([(fx-2,fy-5),(fx+1,fy-5),(fx+1,fy-2),(fx+2,fy-1),(fx+2,fy),(fx-2,fy)],'ink')
    p.rect((fx-1,fy-4,fx,fy-1),'leather')
    p.line([(fx-1,fy-4),(fx,fy-4)],'leather_light')
    p.line([(fx-1,fy-1),(fx+1,fy-1)],'leather' if far else 'leather_light')


def arm(p,shoulder,elbow,hand,far=False,bracer=False):
    p.line([shoulder,elbow,hand],'ink',3)
    p.line([shoulder,elbow],'teal_shadow' if far else 'teal',2)
    p.line([elbow,hand],'steel_shadow' if bracer else 'teal_shadow',2)
    if not far: p.rect((shoulder[0]-1,shoulder[1],shoulder[0]-1,shoulder[1]+1),'teal_light')
    p.rect((hand[0]-1,hand[1]-1,hand[0],hand[1]),'skin_shadow' if far else 'skin')
    if not far: p.rect((hand[0]-1,hand[1]-1,hand[0]-1,hand[1]-1),'skin_light')


def scabbard(p,direction,hip=16,waist=21):
    sign=1 if direction==3 else -1; sx=hip+4*sign
    p.line([(sx,waist),(sx+sign*5,waist+10)],'ink',3)
    p.line([(sx,waist+1),(sx+sign*4,waist+9)],'teal_shadow')
    p.line([(sx-sign,waist-3),(sx,waist-1)],'leather_light',2)
    p.line([(sx-sign*2,waist),(sx+sign*2,waist-1)],'gold')
    p.rect((sx+sign*4,waist+9,sx+sign*4+1,waist+9),'steel_shadow')


def torso(p,direction,cx=16,y=13,hip=16,waist=23,turn=0,tail=0):
    """Narrow waist, tailored split coat, shirt, single strap and satchel."""
    left,right=cx-4,cx+4
    p.poly([(left,y),(right-1,y),(right+1,y+3),(hip+3,waist),
            (hip+4+tail,waist+4),(hip+1,waist+5),(hip,waist+3),
            (hip-3,waist+5),(hip-5-tail,waist+4),(hip-3,waist),(left-1,y+3)],'ink')
    p.poly([(left+1,y+1),(right-1,y+1),(right,y+3),(hip+2,waist),
            (hip+3+tail,waist+3),(hip+1,waist+3),(hip,waist+1),
            (hip-3,waist+3),(hip-3,waist),(left,y+3)],'teal_shadow')
    p.poly([(left+1,y+1),(cx,y+1),(cx,y+5),(hip-1,waist),
            (hip-3,waist+3),(hip-3,waist),(left,y+3)],'teal')
    p.line([(left+1,y+2),(left+1,y+5)],'teal_light')
    if direction==3:
        p.poly([(cx-2,y+3),(cx+2,y+2),(cx+3,y+5),(hip+2,waist-1),(hip-3,waist-1)],'ink')
        p.poly([(cx-1,y+3),(cx+1,y+3),(cx+2,y+5),(hip+1,waist-2),(hip-2,waist-2)],'leather')
        p.line([(cx-1,y+3),(cx+1,y+3)],'leather_light')
        p.rect((hip-1,waist-4,hip,waist-3),'gold')
    else:
        shirt=cx+turn//2
        p.poly([(shirt-1,y+1),(shirt+1,y+1),(hip+1,waist-1),(hip-1,waist-1)],'linen')
        p.line([(shirt,y+3),(hip,waist-2)],'ochre')
        if direction==0:
            p.line([(cx+3-turn//2,y+1),(hip-2,waist-1)],'ink',3)
            p.line([(cx+3-turn//2,y+1),(hip-2,waist-1)],'leather_light')
        elif direction==1:
            p.rect((cx+3,y+4,cx+4,waist-1),'leather')
            p.line([(cx+3,y+4),(cx+4,y+4)],'leather_light')
        else:
            p.line([(cx-3,y+1),(hip+1,waist-1)],'ink',3)
            p.line([(cx-3,y+1),(hip+1,waist-1)],'leather_light')
    p.line([(hip-3,waist),(hip+3,waist)],'leather',2)
    p.rect((hip,waist,hip+1,waist+1),'gold'); p.rect((hip,waist,hip,waist),'linen')
    p.line([(hip+2,waist+2),(hip+2+tail,waist+3)],'teal')


def scarf(p,direction,cx=16,y=13,tail=0):
    p.line([(cx-3,y),(cx+3,y)],'copper_shadow',3)
    p.line([(cx-2,y),(cx+2,y)],'copper',2)
    p.line([(cx-2,y-1),(cx,y-1)],'copper_light')
    sx=cx+3 if direction in (1,3) else cx-4
    sign=1 if direction==1 else -1
    p.poly([(sx,y+1),(sx+1,y+1),(sx+sign*tail,y+5),
            (sx-1+sign*tail,y+6),(sx-1,y+3)],'copper_shadow')
    p.line([(sx,y+2),(sx+sign*tail,y+4)],'copper')


def hero_sprite(action,frame,direction,palette):
    if action in ('attack','windup'): return attack_sprite(frame,direction,palette)
    if action=='dash': return dash_sprite(frame,direction,palette)
    if action=='death': return fallen_sprite(frame,direction,palette)
    image=Image.new('RGBA',FRAME); p=Brush(image,palette)
    side=direction in (1,2); sign=-1 if direction==1 else 1
    walking=action=='walk'; phase=frame%8
    step=WALK_STEPS[phase] if walking else 0
    bob=-int(walking and phase in (2,6))
    lean=(-1,-1,0)[frame]*sign if action=='hurt' else 0
    drop=(1,1,0)[frame] if action=='hurt' else bob
    cx=16+lean; y=13+drop
    breath=int(action=='idle' and frame in (1,2))
    if side:
        for far,s in ((True,-step),(False,step)):
            lift=WALK_LIFT[(phase+(4 if far else 0))%8] if walking else 0
            leg(p,(16 if far else 15,24),(16+s//2,28-lift//2),(16+s,33-lift),far)
    else:
        for index,(hx,fx) in enumerate(((13,12),(18,19))):
            lift=WALK_LIFT[(phase+index*4)%8] if walking else 0
            advance=(1 if phase in (0,1,2) else -1) if walking else 0
            leg(p,(hx,24),(hx+advance*(1 if index==0 else -1),28-lift//2),
                (fx,33-lift),index==(0 if direction==3 else 1))
    scabbard(p,direction)
    sway=(0,-1,-2,-1,0,1,2,1)[phase] if walking else (3,1,0)[frame] if action=='hurt' else 0
    if side: arm(p,(cx+3,y+2),(cx+4,y+7),(cx+2-sign*sway,y+12),True)
    else: arm(p,(cx+4,y+2),(cx+5,y+7+breath),(cx+4,y+12-sway),True)
    torso(p,direction,cx,y,tail=int(walking and phase in (3,7)))
    if side: arm(p,(cx-3,y+2),(cx-4+sign*sway,y+7+breath),(cx-3+sign*sway,y+12),bracer=True)
    else: arm(p,(cx-4,y+2),(cx-5,y+7+breath),(cx-4,y+12+sway),direction==3,True)
    head(p,direction,lean,drop,blink=action=='idle' and frame==2 or action=='hurt' and frame<2,tense=action=='hurt')
    scarf(p,direction,cx,y,tail=int(walking and phase in (2,3,6,7) or action=='idle' and frame==3))
    return image


def attack_sprite(frame,direction,palette):
    image=Image.new('RGBA',FRAME); p=Brush(image,palette)
    side=direction in (1,2); sign=-1 if direction==1 else 1
    lean=(-1,-2,-1,2,2,1,0,0)[frame]*(sign if side else 1)
    drop=(0,1,0,2,1,0,0,0)[frame]
    turn=(-1,-1,0,1,2,2,1,0)[frame] if direction==0 else 0
    if direction==0:
        lean=(-1,-1,0,1,1,1,0,0)[frame]; drop=(0,0,0,2,1,0,0,0)[frame]
    cx=16+lean; y=13+drop
    opening=(0,1,1,2,2,1,0,0)[frame]
    if side:
        leg(p,(17,24),(17-sign*opening,28),(17-sign*(1+opening),33),True)
        leg(p,(14,24),(14+sign*opening,28),(14+sign*(1+opening),33))
    else:
        leg(p,(13,24),(13,28),(12-opening//2,33),direction==3)
        leg(p,(18,24),(18,28),(19+opening//2,33),direction!=3)
    far_hand=(cx+4,y+10)
    if side: far_hand=(cx-sign*3,y+8-int(frame in (2,3)))
    if direction==3: far_hand=(cx-5,y+8)
    if direction==0: far_hand=((21,23),(21,22),(22,21),(22,21),(22,22),(22,23),(21,24),(20,24))[frame]
    arm(p,(cx+3-turn//2,y+2),(cx+5,y+6),far_hand,True)
    torso(p,direction,cx,y,turn=turn,tail=int(frame in (3,4)))
    grip=SWORD_GRIPS[direction][frame]
    shoulder=(cx-3 if direction in (0,2) else cx+3,y+2)
    elbow=((shoulder[0]+grip[0])//2,min(25,max(y+3,(shoulder[1]+grip[1])//2+2)))
    if direction==0:
        shoulder=(cx-3+turn,y+2+int(frame in (2,3,4)))
        elbow=((9,18),(9,18),(10,21),(12,24),(18,23),(21,20),(16,21),(11,19))[frame]
    arm(p,shoulder,elbow,grip,bracer=True)
    head(p,direction,lean,drop,tense=frame in (2,3,4))
    scarf(p,direction,cx,y,tail=int(frame in (3,4,5)))
    return image


def sword_points(frame,direction):
    gx,gy=SWORD_GRIPS[direction][frame]
    grip=(gx,compact_y(gy))
    theta=math.radians(SWORD_ANGLES[direction][frame])
    def point(distance):
        return (round(grip[0]+math.cos(theta)*distance),round(grip[1]+math.sin(theta)*distance))
    return grip,point(4),point(SWORD_TIP),(-math.sin(theta),math.cos(theta))


def hero_weapon(frame,direction,palette,collision=False):
    image=Image.new('RGBA',(96,96)); p=Brush(image,palette,compact=False)
    offset=(32,24)
    def shift(pt): return (pt[0]+offset[0],pt[1]+offset[1])
    grip,base,tip,perp=sword_points(frame,direction)
    prev_grip,prev_base,_,_=sword_points(max(0,frame-1),direction)
    old_theta=math.radians(SWORD_ANGLES[direction][max(0,frame-1)])
    theta=math.radians(SWORD_ANGLES[direction][frame])
    def trail(radius):
        return [shift((prev_grip[0]+(grip[0]-prev_grip[0])*i/10+math.cos(old_theta+(theta-old_theta)*i/10)*radius,
                       prev_grip[1]+(grip[1]-prev_grip[1])*i/10+math.sin(old_theta+(theta-old_theta)*i/10)*radius)) for i in range(11)]
    if collision:
        if frame not in (2,3,4,5): return image
        if frame in (3,4): p.poly([shift(prev_base),*trail(SWORD_TIP),shift(base)],'white')
        p.line([shift(base),shift(tip)],'white',3)
        return image
    if frame in (3,4):
        p.poly(trail(SWORD_TIP)+list(reversed(trail(SWORD_TIP-2))),(237,240,209,110))
        p.line(trail(SWORD_TIP),'steel_light')
    p.line([shift(base),shift(tip)],'ink',3)
    p.poly([shift((base[0]-perp[0],base[1]-perp[1])),shift(tip),shift((base[0]+perp[0],base[1]+perp[1]))],'steel')
    p.line([shift((base[0]-perp[0],base[1]-perp[1])),shift(tip)],'steel_light')
    p.line([shift(grip),shift((grip[0]+math.cos(theta)*3,grip[1]+math.sin(theta)*3))],'ink',3)
    p.line([shift(grip),shift(base)],'leather_light')
    guard=(grip[0]+math.cos(theta)*3,grip[1]+math.sin(theta)*3)
    p.line([shift((guard[0]-perp[0]*2,guard[1]-perp[1]*2)),shift((guard[0]+perp[0]*2,guard[1]+perp[1]*2))],'gold')
    gx,gy=shift(grip); p.rect((gx-1,gy-1,gx,gy),'skin'); p.rect((gx-1,gy-1,gx-1,gy-1),'skin_light')
    return image


def dash_sprite(frame,direction,palette):
    if frame==4: return hero_sprite('idle',0,direction,palette)
    image=Image.new('RGBA',FRAME); p=Brush(image,palette)
    side=direction in (1,2); sign=-1 if direction==1 else 1
    lean=(0,3,4,1)[frame]*(sign if side else 0)
    drop=(3,3,2,1)[frame]; cx=16+lean; y=13+drop
    if side:
        leg(p,(15,25),(14-sign*(1,2,3,1)[frame],29),(14-sign*(1,4,5,1)[frame],33-(0,1,3,0)[frame]),True)
        leg(p,(17,25),(18+sign*(2,3,2,2)[frame],29),(17+sign*(2,1,0,3)[frame],33))
    else:
        spread=(1,2,1,1)[frame]
        leg(p,(13,25),(12,29),(12-spread,33-int(frame==2)*2),direction==3)
        leg(p,(18,25),(19,29),(19+spread,33-int(frame==1)*2),direction==0)
    scabbard(p,direction,waist=22)
    far_hand=(cx+sign*2,y+7) if side else (cx+4,y+10)
    arm(p,(cx+3,y+2),(cx+4,y+5),far_hand,True)
    torso(p,direction,cx,y,waist=24,tail=int(frame==2))
    if side:
        near_hand=(cx-sign*(1,4,5,1)[frame],y+10)
        arm(p,(cx-3,y+2),(cx-sign*4,y+6),near_hand,bracer=True)
    else: arm(p,(cx-4,y+2),(cx-5,y+6),(cx-5,y+10-int(frame==2)),direction==3,True)
    head(p,direction,lean,drop,tense=frame<3)
    scarf(p,direction,cx,y,tail=(0,2,3,1)[frame])
    return image


def fallen_sprite(frame,direction,palette):
    if frame==0: return hero_sprite('hurt',0,direction,palette)
    image=Image.new('RGBA',FRAME); p=Brush(image,palette,compact=frame==1)
    if frame==1:
        p.poly([(11,25),(19,25),(23,31),(22,33),(12,33),(8,31)],'ink')
        p.rect((11,27,18,30),'deep'); p.rect((19,31,22,32),'leather_light')
        torso(p,direction,y=19,waist=27)
        arm(p,(12,21),(10,25),(11,28),bracer=True)
        head(p,direction,y=6,blink=True); scarf(p,direction,y=19)
        return image
    left=direction in (0,1); hx=7 if left else 23
    p.poly([(2,28),(5,25),(11,25),(14,28),(24,28),(28,30),(29,33),(25,34),(8,34),(2,32)],'ink')
    p.rect((5 if left else 21,27,11 if left else 27,32),'skin_shadow')
    p.rect((6 if left else 22,27,10 if left else 26,30),'skin')
    p.poly([(hx-3,26),(hx-2,25),(hx+2,25),(hx+4,27),(hx+1,28),(hx-3,28)],'hair')
    p.line([(hx-2,26),(hx,26)],'hair_light'); p.line([(hx,29),(hx+1,29)],'ink')
    p.rect((hx,31,hx+1,31),LIPS)
    p.rect((12,29,21,32),'teal_shadow'); p.rect((13,28,19,30),'teal')
    p.line([(13,29),(17,31)],'leather_light')
    p.rect((11 if left else 20,29,13 if left else 22,30),'copper')
    p.rect((23 if left else 4,31,27 if left else 8,33),'leather')
    p.line([(24 if left else 5,31),(26 if left else 7,31)],'leather_light')
    if direction==3: p.rect((13,28,18,31),'leather'); p.line([(14,28),(17,28)],'leather_light')
    return image
