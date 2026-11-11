"""Native actors for the memory installation; no previous atlas is modified."""
import sys,math
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from core.lacre_motion import COUNTS,pose
OUT=ROOT/'assets/vale_characters'
INK='#202c38';STONE='#697d82';LIGHT='#b8c5b8';GOLD='#bba36c';SKIN='#c59976'
def sprite(kind,action,i,facing):
    im=Image.new('RGBA',(80,64));d=ImageDraw.Draw(im)
    (x,foot,stride,lean),grip,tip=pose(action,i,facing)
    human=kind=='custodian';echo=kind=='unstable_echo';elite=kind=='record_warden'
    top=foot-(34 if human else 29)
    if action=='idle' and i%4 in (1,2):top-=1
    if action=='death':top+=min(17,i*3);foot=46
    if action=='hurt':
        shift=2-i;x-=shift;grip=(grip[0]-shift,grip[1]);tip=(tip[0]-shift,tip[1])
    # Legs move independently; robes split over the knees rather than stretching.
    for xx,step in ((x-5,stride),(x+3,-stride)):
        d.polygon([(xx,foot-13),(xx+4,foot-13),(xx+4+step,foot-2),(xx-1+step,foot-2)],fill=INK)
        d.line([(xx+2,foot-12),(xx+2+step,foot-4)],fill='#7c8f8c',width=3)
        d.line([(xx-1+step,foot-2),(xx+5+step,foot-2)],fill='#a79774',width=2)
    if human:
        d.polygon([(x-9,top+12),(x+8,top+12),(x+11,foot-8),(x+3,foot-5),(x,foot-11),(x-8,foot-6)],fill=INK)
        d.polygon([(x-7,top+13),(x+6,top+13),(x+8,foot-9),(x+3,foot-7),(x,foot-13),(x-7,foot-8)],fill='#4c6970')
        d.polygon([(x-5,top+13),(x-1,top+13),(x,foot-12),(x-5,foot-9)],fill='#cabd94')
        d.line([(x-7,top+14),(x+4,top+18),(x+7,top+14)],fill=GOLD,width=2)
        d.rectangle((x-4,top+2,x+3,top+8),fill=SKIN)
        d.polygon([(x-5,top+3),(x-3,top),(x+3,top),(x+5,top+3),(x+4,top+7),(x+2,top+2),(x-2,top+2),(x-4,top+8)],fill='#a8b2ac')
        if facing==3:d.rectangle((x-4,top+1,x+3,top+8),fill='#a8b2ac')
        elif facing in (1,2):
            sign=-1 if facing==1 else 1;d.point((x+sign*2,top+5),fill=INK);d.point((x+sign*4,top+6),fill='#dfb48a')
        else:
            d.point((x-2,top+5),fill=INK);d.point((x+2,top+5),fill=INK)
            d.line([(x+2,top+3),(x+1,top+8)],fill='#805d54');d.line([(x-1,top+9),(x+2,top+9)],fill='#75574f')
    elif echo:
        # Broken layered mantle and a ceramic face, never a featureless silhouette.
        d.polygon([(x-9,top+11),(x-5,top+8),(x+6,top+8),(x+10,foot-8),(x+4,foot-11),(x-1,foot-6),(x-8,foot-9)],fill=INK)
        d.polygon([(x-6,top+10),(x+5,top+10),(x+7,foot-10),(x+2,foot-12),(x-3,foot-8),(x-6,foot-11)],fill='#657e83')
        d.rectangle((x-4,top+2,x+4,top+9),fill='#b7b29c')
        for xx in (x-2,x+2):d.point((xx,top+5),fill=INK)
        d.line([(x,top+2),(x-1,top+8),(x+2,top+9)],fill='#4b6069')
        for xx,yy in ((x-9,top+18),(x+8,top+14),(x-3,foot-7)):d.rectangle((xx,yy,xx+2,yy+1),fill=GOLD)
        if action=='transition':d.line([(x-8,top+16+i),(x+8,top+16+i)],fill=LIGHT)
    else:
        # Jointed stone body with a central register slot and a protective left shutter.
        d.polygon([(x-10,top+9),(x-7,top+6),(x+8,top+6),(x+11,top+17),(x+7,foot-10),(x-7,foot-10)],fill=INK)
        d.polygon([(x-8,top+10),(x-5,top+8),(x+6,top+8),(x+8,top+17),(x+5,foot-12),(x-5,foot-12)],fill=STONE)
        d.rectangle((x-2,top+11,x+3,top+19),fill='#d0bc7d');d.line([(x,top+12),(x,top+18)],fill=INK)
        d.rectangle((x-5,top,x+5,top+6),fill=INK);d.rectangle((x-3,top+1,x+4,top+5),fill=LIGHT)
        d.line([(x-2,top+3),(x+3,top+3)],fill='#3f565f')
        shutter=10 if elite and (action=='windup' or (action in ('cut','sweep','charge') and i<6)) else 0
        d.polygon([(x-14+shutter,top+8),(x-8+shutter,top+7),(x-6+shutter,top+18),(x-11+shutter,top+22),(x-16+shutter,top+17)],fill=INK)
        d.polygon([(x-13+shutter,top+9),(x-9+shutter,top+9),(x-8+shutter,top+17),(x-12+shutter,top+19),(x-14+shutter,top+16)],fill='#a89c78')
        if elite:
            d.polygon([(x-11,top+2),(x-9,top-3),(x-3,top-1),(x+3,top-1),(x+9,top-3),(x+11,top+3)],fill=GOLD)
            d.line([(x-9,top+7),(x+8,top+7)],fill=LIGHT,width=2)
    shoulder=(x+6,top+12);hand=tuple(map(round,grip));elbow=(round((shoulder[0]+hand[0])/2+2),round((shoulder[1]+hand[1])/2+2))
    d.line([shoulder,elbow,hand],fill=INK,width=5);d.line([shoulder,elbow],fill=STONE,width=3)
    d.line([elbow,hand],fill='#a89c78',width=3);d.rectangle((hand[0]-1,hand[1]-1,hand[0]+1,hand[1]+1),fill=SKIN if human else LIGHT)
    if not echo:
        d.line([hand,tuple(map(round,tip))],fill=INK,width=4);d.line([hand,tuple(map(round,tip))],fill=LIGHT,width=2)
        d.line([(hand[0]-2,hand[1]+2),(hand[0]+2,hand[1]-2)],fill=GOLD,width=2)
    if action=='death':
        # Every subsequent pose settles lower, with no disappearance or execution.
        bounds=im.getbbox()
        if bounds:
            cut=im.crop(bounds);height=max(14,min(42,cut.height)-i*4);cut=cut.resize((cut.width,height),Image.Resampling.NEAREST)
            im=Image.new('RGBA',(80,64));im.paste(cut,(bounds[0],46-height))
    return im
def main():
    for kind in ('lacre_guard','unstable_echo','record_warden','custodian'):
        for action,count in COUNTS.items():
            sheet=Image.new('RGBA',(80*count,64*4))
            for facing in range(4):
                for i in range(count):sheet.paste(sprite(kind,action,i,facing),(80*i,64*facing))
            sheet.save(OUT/f'{kind}_{action}.png')
    print('Built 40 native dungeon atlases; cells 80x64, feet 46, scale 2.')
if __name__=='__main__':main()
