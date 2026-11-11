"""Build only Mara/Téo from the existing native cast geometry; other art is untouched."""
from PIL import Image, ImageDraw
from draw_vale_pack import ROOT, sprite


def frame(uid, action, index, direction):
    im = sprite('civilian_woman' if uid == 'mara' else 'civilian_worker', action, index, direction)
    d = ImageDraw.Draw(im)
    back, side = direction == 3, direction in (1, 2)
    lift = int(action == 'walk' and index % 4 in (1, 2))
    y = -lift
    if uid == 'mara':
        # Rust shawl, flour apron, braid and a tiny patched carrying pouch.
        d.polygon([(10, 13+y), (20, 13+y), (22, 18+y), (17, 17+y), (10, 18+y)], fill='#a87851')
        d.line([(11, 14+y), (19, 14+y)], fill='#d4ab65')
        if not back:
            d.rectangle((14, 18+y, 19, 24+y), fill='#d0c5a5')
            d.point((17, 20+y), fill='#eee2bc')
        bx = 11 if direction == 1 else 20
        d.rectangle((bx, 9+y, bx+1, 14+y), fill='#503d45')
        d.point((bx, 14+y), fill='#d4ab65')
        if not side: d.rectangle((21, 21+y, 23, 24+y), fill='#61463f')
    else:
        # Short red head wrap, indigo vest and linen work apron; no army insignia.
        d.rectangle((12, 3+y, 20, 4+y), fill='#96594b')
        d.line([(12, 3+y), (19, 3+y)], fill='#c78869')
        d.rectangle((10, 14+y, 13, 20+y), fill='#3e5c72')
        if not side: d.rectangle((20, 14+y, 22, 20+y), fill='#3e5c72')
        if not back: d.rectangle((14, 19+y, 19, 24+y), fill='#c5b995')
        wx = 9 if direction == 1 else 22
        d.rectangle((wx, 20+y, wx+1, 22+y), fill='#e1d5af')
    return im


def main():
    out = ROOT / 'assets/vale_characters'
    for uid in ('mara', 'teo'):
        for action, count in (('idle', 4), ('walk', 8)):
            sheet = Image.new('RGBA', (32*count, 128))
            for direction in range(4):
                for index in range(count): sheet.paste(frame(uid, action, index, direction), (index*32, direction*32))
            sheet.save(out / f'{uid}_{action}.png')
    print('Mara/Téo: four native atlases generated; existing sprites preserved.')


if __name__ == '__main__': main()
