"""Author Edrin's compact, unarmoured 32x36 pixel atlas. Run from pygame/."""
from pathlib import Path
from PIL import Image, ImageDraw

INK = '#302e31'
COAT, LIT, SHADE = '#756956', '#94846b', '#534d45'
RED, RED_DARK = '#86514f', '#603d40'
SKIN, SKIN_DARK = '#c09d7b', '#92765f'


def sprite(mode, frame, facing):
    image = Image.new('RGBA', (32, 36))
    d = ImageDraw.Draw(image)
    walking = mode in ('walk', 'recoil')
    step = ((0, -2, -3, -1)[frame] if mode == 'recoil' else
            (0, 2, 3, 1, 0, -1, -2, -1)[frame] if walking else 0)
    bob = -int(walking and frame in (2, 6)) + int(mode == 'idle' and frame in (1, 2))
    # Uneven contacts and a compressed injured knee give the escape a limp.
    d.line([(13, 24), (12, 29), (11 + step, 33)], fill=INK, width=4)
    d.line([(18, 24), (19, 28), (20 - step, 32)], fill=INK, width=4)
    d.line([(13, 24), (12, 29), (11 + step, 32)], fill=SHADE, width=2)
    d.line([(18, 24), (19, 28), (20 - step, 31)], fill='#666150', width=2)
    d.rectangle((18, 27, 21, 29), fill='#beb39a')
    d.line([(18, 28), (21, 28)], fill='#8f8978')
    d.rectangle((9 + step, 33, 13 + step, 34), fill=INK)
    d.rectangle((18 - step, 32, 22 - step, 33), fill=INK)
    lean = -1 if mode == 'idle' else 0
    # No helmet or plate: a faded single red sleeve, torn insignia stitches,
    # a short open coat, old leather pouch and a sheathed, chipped sidearm.
    d.polygon([(10, 13 + bob), (19, 12 + bob), (22, 17), (20, 24),
               (22, 27), (17, 28), (15, 25), (10, 27), (9, 19)], fill=INK)
    d.polygon([(11, 14 + bob), (18, 13 + bob), (20, 17), (18, 24),
               (20, 26), (17, 26), (15, 23), (11, 25), (10, 18)], fill=COAT)
    d.polygon([(12, 15), (15, 14), (16, 22), (13, 24), (11, 23)], fill=LIT)
    d.line([(16, 14), (18, 22)], fill='#c1b69b', width=2)
    d.line([(11, 16), (18, 22)], fill=SHADE, width=2)
    d.line([(11, 23), (19, 22)], fill='#493d34', width=2)
    d.rectangle((11, 23, 14, 26), fill='#58483b')
    d.point((15, 23), fill='#b09b72')
    d.rectangle((18, 16, 20, 20), fill=SHADE)
    d.line([(18, 16), (20, 16)], fill='#b09a7b')
    d.point((18, 19), fill='#b09a7b')
    d.line([(21, 23), (25, 31)], fill=INK, width=3)
    d.line([(21, 24), (25, 30)], fill='#59554c')
    d.line([(19, 21), (23, 20)], fill='#9f977e')
    swing = step // 2 if walking else 0
    guarded = mode in ('guard', 'alert', 'recoil')
    far_hand = (20, 21) if guarded else (22 - swing, 24)
    d.line([(20, 15), (23, 19), far_hand], fill=INK, width=3)
    d.line([(20, 16), (22, 19)], fill=SHADE, width=2)
    d.rectangle((far_hand[0] - 1, far_hand[1], far_hand[0], far_hand[1] + 1), fill=SKIN_DARK)
    near_hand = (13, 22) if mode == 'idle' else (12 + swing, 24)
    d.line([(10, 16), (8, 20), near_hand], fill=INK, width=4)
    d.line([(10, 16), (9, 20)], fill=RED, width=2)
    d.line([(9, 21), near_hand], fill=RED_DARK, width=2)
    d.rectangle((near_hand[0] - 1, near_hand[1], near_hand[0], near_hand[1] + 1), fill=SKIN)
    # Older face: cropped silver hair, stubble, an oblique cheek scar. Tiny
    # dark eyes stay legible without large white sockets or an elongated jaw.
    hx, hy = lean, bob + int(mode == 'idle')
    d.polygon([(12 + hx, 4 + hy), (14 + hx, 2 + hy), (18 + hx, 2 + hy),
               (20 + hx, 4 + hy), (20 + hx, 10 + hy), (18 + hx, 12 + hy),
               (14 + hx, 11 + hy), (12 + hx, 8 + hy)], fill=INK)
    d.rectangle((13 + hx, 5 + hy, 19 + hx, 9 + hy), fill=SKIN_DARK)
    d.rectangle((14 + hx, 5 + hy, 18 + hx, 9 + hy), fill=SKIN)
    d.line([(13 + hx, 4 + hy), (19 + hx, 4 + hy)], fill='#aea997', width=2)
    d.point((14 + hx, 3 + hy), fill='#d0c7ad')
    d.line([(13 + hx, 9 + hy), (15 + hx, 11 + hy), (18 + hx, 10 + hy)], fill='#6c665d')
    if facing == 3:
        d.rectangle((13 + hx, 5 + hy, 19 + hx, 9 + hy), fill='#827f70')
        d.line([(14 + hx, 5 + hy), (18 + hx, 5 + hy)], fill='#aaa38f')
    elif facing in (1, 2):
        d.rectangle((17 + hx, 6 + hy, 19 + hx, 6 + hy), fill='#715847')
        d.point((19 + hx, 7 + hy), fill=INK)
        d.point((20 + hx, 8 + hy), fill=SKIN)
        d.line([(17 + hx, 7 + hy), (18 + hx, 9 + hy)], fill='#8a5148')
        d.point((19 + hx, 10 + hy), fill='#79574c')
    else:
        for x in (14, 18):
            d.point((x + hx, 7 + hy), fill=INK)
        d.point((16 + hx, 8 + hy), fill=SKIN_DARK)
        d.line([(17 + hx, 8 + hy), (18 + hx, 9 + hy)], fill='#8a5148')
        d.point((15 + hx, 10 + hy), fill='#79574c')
    if facing == 1:
        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return image


def build():
    root = Path(__file__).resolve().parents[1] / 'assets' / 'vale_characters'
    for mode, count in (('idle', 4), ('guard', 4), ('alert', 4), ('recoil', 4), ('walk', 8)):
        sheet = Image.new('RGBA', (32 * count, 36 * 4))
        for direction in range(4):
            for frame in range(count):
                sheet.paste(sprite(mode, frame, direction), (32 * frame, 36 * direction))
        sheet.save(root / f'edrin_{mode}.png')


if __name__ == '__main__':
    build()
