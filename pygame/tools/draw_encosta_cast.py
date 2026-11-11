"""Build only the new Encosta actors. Existing protagonist/cast atlases are untouched."""
import math
from pathlib import Path
from PIL import Image,ImageDraw
from draw_vale_pack import sprite

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/vale_characters'
COUNTS={'idle':4,'walk':8,'windup':3,'attack':8,'hurt':3,'death':4}
INK='#252b34'; LIGHT='#d9d1af'; FUR='#8b775b'; SHADE='#514c45'


def npc(uid,action,i,direction):
    im=sprite('civilian_woman' if uid=='ines' else 'civilian_worker',action,i,direction)
    d=ImageDraw.Draw(im); lift=int(action=='walk' and i%4 in (1,2)); y=-lift
    back=direction==3; side=direction in (1,2)
    if uid=='ines':
        # Silver braid, olive mantle, a registry satchel and hands holding a folio.
        d.rectangle((11,2+y,21,5+y),fill='#939c94')
        for x,yy in ((10,4),(11,7),(21,5),(22,8),(21,11)):
            d.rectangle((x,yy+y,x+1,yy+2+y),fill='#b9b9a6')
        d.polygon([(10,13+y),(21,13+y),(23,22+y),(19,24+y),(11,23+y)],fill='#566b5a')
        d.line([(11,14+y),(17,16+y),(21,14+y)],fill='#a5b188')
        if not back:
            d.rectangle((13,18+y,20,24+y),fill='#b49c74'); d.rectangle((14,19+y,19,23+y),fill='#e1d5af')
            d.line([(15,20+y),(18,20+y)],fill='#76614a')
            d.point((13,9+y),fill='#ad785d'); d.point((19,9+y),fill='#ad785d')
            if not side: d.line([(13,8+y),(19,8+y)],fill='#58675c')
        else: d.rectangle((18,5+y,20,15+y),fill='#b9b9a6')
    else:
        # Rough cropped hair, stubble, a patched sleeveless coat and a sling strap.
        d.rectangle((12,3+y,20,5+y),fill='#726656')
        if not back: d.rectangle((13,10+y,19,12+y),fill='#6e5b4e')
        d.polygon([(10,14+y),(21,14+y),(23,23+y),(19,25+y),(10,24+y)],fill='#6c6c68')
        d.line([(11,14+y),(20,24+y)],fill='#b49c74',width=2)
        d.rectangle((10,18+y,12,21+y),fill='#927858'); d.point((11,19+y),fill=LIGHT)
        if not back:
            d.rectangle((14,22+y,20,25+y),fill='#544c42'); d.line([(15,23+y),(19,23+y)],fill='#aa9270')
            d.point((19 if direction!=1 else 12,8+y),fill=INK)
    return im


def creature(kind,action,i,direction):
    im=Image.new('RGBA',(80,40)); d=ImageDraw.Draw(im)
    robust=kind!='reed_stalker'; elite=kind=='slate_warden'
    side=direction in (1,2); back=direction==3
    phase=math.sin(i*math.pi/2) if action=='walk' else 0
    bob=round(abs(phase)); lean=0; squash=0
    if action=='windup': lean=(-1,-2,-3)[i]; squash=1+i//2
    if action=='attack': lean=(-3,-2,1,4,5,3,1,0)[i]; squash=(2,2,0,0,1,1,0,0)[i]
    if action=='hurt': lean=(-2,-1,0)[i]; squash=1
    if action=='death': squash=2+i*2; bob=-i
    cx=40+lean*(1 if direction!=1 else -1); y=24+bob+squash
    def poly(points,c): d.polygon([(cx+x,y+yy) for x,yy in points],fill=c)
    def rect(b,c): d.rectangle((cx+b[0],y+b[1],cx+b[2],y+b[3]),fill=c)
    def line(points,c,w=1): d.line([(cx+x,y+yy) for x,yy in points],fill=c,width=w)
    if robust:
        poly([(-19,-3),(-14,-15),(0,-18),(15,-12),(19,2),(13,9),(-13,9)],INK)
        poly([(-17,-3),(-12,-13),(0,-16),(13,-11),(17,2),(11,7),(-12,7)],'#697369')
        for x,yy in ((-12,-9),(-3,-13),(6,-10),(-13,0),(-3,-3),(8,0)):
            poly([(x-4,yy+3),(x-2,yy-3),(x+4,yy-4),(x+7,yy+2),(x+2,yy+5)],'#9aa396')
            line([(x-2,yy-2),(x+4,yy-3),(x+6,yy+1)],'#c5c4a3')
            line([(x-3,yy+3),(x+2,yy+4)],'#414e4c')
        if elite:
            for x in (-10,-2,7):
                poly([(x-3,-12),(x-1,-22),(x+4,-14),(x+3,-9)],INK)
                line([(x-1,-20),(x+1,-13)],'#c5c4a3',2)
        if side:
            poly([(12,-4),(22,0),(21,5),(13,7),(9,2)],INK)
            rect((14,0,20,4),'#8b8267'); rect((17,-1,18,0),'#dfb168')
            poly([(-17,1),(-23,3),(-19,6),(-13,5)],'#4c5e55')
        elif not back:
            poly([(-9,0),(-5,-4),(7,-4),(11,2),(6,9),(-6,9)],INK)
            rect((-6,0,7,6),'#a29b7c'); rect((-5,1,-3,2),'#dfb168'); rect((4,1,6,2),'#dfb168')
            rect((-1,5,2,6),INK)
        else: line([(-6,4),(0,8),(7,5)],'#414e4c',2)
        for x in (-13,11):
            dx=round(phase*2)*(1 if x<0 else -1)
            rect((x+dx,5,x+5+dx,10-squash//3),INK); rect((x+dx+1,6,x+4+dx,8),'#9d9c80')
            line([(x+dx,10-squash//3),(x+5+dx,10-squash//3)],LIGHT)
        if action=='attack' and 2<=i<=5:
            # Forelimb sweep follows the body instead of a stationary pose plus effect.
            extension=(3,7,9,5)[i-2]
            if side:
                poly([(8,2),(18+extension,2),(20+extension,6),(12,8)],INK)
                line([(13,4),(18+extension,4)],'#9aa396',3)
                for yy in (3,5): line([(19+extension,yy),(22+extension,yy)],LIGHT)
            elif not back:
                for x in (-11,8):
                    rect((x,5,x+5,10+extension//2),INK)
                    line([(x+1,7),(x+4,10+extension//2)],'#9aa396',2)
    else:
        poly([(-15,-2),(-12,-9),(6,-11),(15,-5),(13,4),(-12,5)],INK)
        poly([(-13,-2),(-10,-7),(5,-9),(13,-4),(10,3),(-11,3)],FUR)
        line([(-11,-6),(-4,-8),(5,-8)],'#c2ad7c',2)
        for x in (-9,-1,7): line([(x,-5),(x+2,-1)],SHADE,2)
        poly([(-12,0),(-22,-5),(-20,1),(-13,6)],INK)
        line([(-14,2),(-19,0),(-21,-3)],FUR,2)
        if side:
            poly([(8,-6),(11,-13),(16,-8),(20,-9),(24,-3),(22,3),(13,4)],INK)
            poly([(11,-6),(13,-10),(16,-6),(20,-7),(22,-2),(20,1),(13,2)],'#b9a27a')
            rect((18,-5,19,-4),LIGHT); rect((21,-1,23,0),INK); rect((18,3,19,5),LIGHT)
        elif not back:
            poly([(-10,-8),(-8,-15),(-3,-9),(4,-9),(9,-15),(11,-8),(9,0),(4,5),(-4,5),(-10,0)],INK)
            poly([(-8,-7),(-6,-11),(-2,-7),(4,-7),(8,-11),(9,-6),(7,0),(2,3),(-3,3),(-8,-1)],'#b9a27a')
            rect((-6,-5,-4,-4),LIGHT); rect((4,-5,6,-4),LIGHT); rect((-1,0,2,1),INK)
            rect((-4,2,-3,5),LIGHT); rect((4,2,5,5),LIGHT)
        else:
            poly([(-8,-8),(-7,-14),(-2,-9),(5,-9),(9,-14),(10,-6)],SHADE)
        for x in (-10,6):
            step=round(phase*3)*(1 if x<0 else -1)
            line([(x,2),(x+step,9-squash//3),(x+step+4,9-squash//3)],INK,3)
            line([(x+step,8-squash//3),(x+step+3,8-squash//3)],FUR)
    if action=='death':
        # A deliberate collapse, not a shrinking standing frame.
        bounds=im.getbbox()
        crop=im.crop(bounds); crop=crop.resize((crop.width,max(9,crop.height-i*4)),Image.Resampling.NEAREST)
        im=Image.new('RGBA',(80,40)); im.paste(crop,(max(0,min(80-crop.width,bounds[0])),36-crop.height))
    if direction==1: im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return im


def main():
    OUT.mkdir(exist_ok=True)
    for uid in ('ines','breno'):
        for action,count in (('idle',4),('walk',8)):
            sheet=Image.new('RGBA',(count*32,128))
            for direction in range(4):
                for i in range(count): sheet.paste(npc(uid,action,i,direction),(i*32,direction*32))
            sheet.save(OUT/f'{uid}_{action}.png')
    for kind in ('reed_stalker','slateback','slate_warden'):
        for action,count in COUNTS.items():
            sheet=Image.new('RGBA',(count*80,160))
            for direction in range(4):
                for i in range(count): sheet.paste(creature(kind,action,i,direction),(i*80,direction*40))
            sheet.save(OUT/f'{kind}_{action}.png')
    print('Encosta: 4 NPC atlases and 18 creature atlases; existing art preserved.')


if __name__=='__main__': main()
