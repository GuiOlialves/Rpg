"""Build only Soren's compact native pixel atlases; existing cast is untouched."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.archive_motion import COUNTS, pose

OUT = ROOT/'assets/vale_characters'
INK = '#252b3c'


def body(action, index, facing):
    im = Image.new('RGBA', (48, 40))
    d = ImageDraw.Draw(im)
    center, grip, tip = pose(action, index, facing)
    x, foot = map(round, center)
    defeated = action == 'defeated'
    top = 6 + (min(6, index*2) if defeated else 0)
    stride = (0,1,2,1,0,-1,-2,-1)[index] if action == 'walk' else 0
    if action in ('quick','wide'): stride=(-1,-2,-1,3,3,2,1,0)[index]
    if action == 'advance': stride=(0,-1,-2,3,-3,2,1,0)[index]
    # Broad split mantle, reinforced left pauldron, unhelmeted grey hair.
    d.polygon([(x-8,top+12),(x+6,top+11),(x+10,foot-5),(x+2,foot-4),
               (x,foot-8),(x-10,foot-6)], fill=INK)
    d.polygon([(x-7,top+13),(x+4,top+12),(x+8,foot-7),(x+2,foot-6),
               (x-1,foot-10),(x-8,foot-7)], fill='#5b414d')
    d.line([(x-7,top+14),(x-8,foot-8)], fill='#b77862', width=2)
    for lx, shift in ((x-5,stride),(x+3,-stride)):
        d.polygon([(lx,top+21),(lx+4,top+21),(lx+4+shift,foot-1),
                   (lx-1+shift,foot-1)], fill=INK)
        d.line([(lx+2,top+22),(lx+1+shift,foot-3)], fill='#697681',width=2)
        d.line([(lx-1+shift,foot-2),(lx+3+shift,foot-2)],fill='#ab825d',width=2)
    d.polygon([(x-6,top+11),(x+5,top+11),(x+7,top+17),(x+4,top+23),
               (x-5,top+23),(x-8,top+16)], fill=INK)
    d.polygon([(x-5,top+12),(x+4,top+12),(x+5,top+17),(x+3,top+21),
               (x-4,top+21),(x-6,top+16)],fill='#788b94')
    d.polygon([(x-4,top+13),(x,top+13),(x+1,top+19),(x-4,top+19)], fill='#b8c7bb')
    d.line([(x-5,top+22),(x+4,top+22)],fill='#6c4d41',width=2)
    d.rectangle((x-1,top+22,x+1,top+23),fill='#d4ab65')
    d.polygon([(x-10,top+12),(x-5,top+10),(x-2,top+13),(x-4,top+17),(x-10,top+16)],fill=INK)
    d.polygon([(x-9,top+12),(x-5,top+11),(x-3,top+13),(x-5,top+15),(x-9,top+15)],fill='#d0c3a0')
    d.line([(x-7,top+12),(x-6,top+14)],fill='#5c6774')
    # No face stretching; profiles have their own nose and visible eye.
    d.polygon([(x-3,top),(x+2,top),(x+4,top+3),(x+3,top+8),
               (x+1,top+10),(x-2,top+9),(x-4,top+7),(x-4,top+2)],fill=INK)
    d.rectangle((x-3,top+2,x+2,top+6),fill='#b98969')
    d.rectangle((x-1,top+2,x+2,top+6),fill='#d2a079')
    if facing in (1,2):
        sign = -1 if facing == 1 else 1
        d.rectangle((x+sign*3,top+4,x+sign*3+1,top+5),fill='#dfb48a')
        d.point((x+sign*2,top+3),fill=INK)
        d.line([(x-sign*2,top+1),(x-sign*2,top+5)],fill='#8b9697',width=2)
    elif facing == 0:
        for xx in (x-2,x+1): d.point((xx,top+4),fill=INK)
        d.point((x+2,top+5),fill='#8b5c57')
    else: d.rectangle((x-3,top+1,x+2,top+7),fill='#8b9697')
    d.line([(x-3,top+1),(x+2,top+1)],fill='#bdc5ba',width=2)
    if facing != 3:
        d.line([(x-2,top+7),(x+2,top+7)],fill='#909a94',width=2)
        d.line([(x-1,top+8),(x+1,top+8)],fill='#bdc5ba')
    shoulder = (x+5,top+13)
    hand = tuple(map(round,grip)) if action in ('quick','wide','advance') else (x+7,top+21)
    if defeated: hand = (x+10,foot-3)
    elbow = ((shoulder[0]+hand[0])//2+2,(shoulder[1]+hand[1])//2+2)
    d.line([shoulder,elbow,hand],fill=INK,width=5)
    d.line([shoulder,elbow],fill='#87989d',width=3)
    d.line([elbow,hand],fill='#5b414d',width=3)
    d.rectangle((hand[0]-1,hand[1]-1,hand[0]+1,hand[1]+1),fill='#d2a079')
    d.line([(x-7,top+17),(x-9,top+21),(x-5,top+22)],fill=INK,width=4)
    d.line([(x-7,top+17),(x-9,top+21)],fill='#899a9a',width=2)
    return im


def build():
    for action,count in COUNTS.items():
        sheet=Image.new('RGBA',(48*count,40*4))
        for facing in range(4):
            for i in range(count): sheet.paste(body(action,i,facing),(48*i,40*facing))
        sheet.save(OUT/f'archive_veteran_{action}.png')
    print('Built 7 archive veteran atlases; native cells 48x40, pivot 24,36.')


if __name__ == '__main__': build()
