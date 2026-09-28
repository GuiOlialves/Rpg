"""Original O Vale pixel art, drawn directly on a 32 px grid (Pillow only).

Run from anywhere: python tools/build_vale_characters.py
No resampled source artwork, antialiasing, gradients or runtime dependency on Pillow.
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/vale_characters"
PALETTE = {
    "ink": "#29242e", "leather": "#574039", "leather_light": "#886047",
    "skin_shadow": "#b87956", "skin": "#e0ad78", "linen": "#d6c6a0",
    "hair": "#4b3742", "hair_light": "#886047", "grey": "#94968b",
    "steel": "#a5b8b6", "steel_shadow": "#94968b",
    "blue": "#48688d", "blue_shadow": "#34455f", "blue_light": "#7595b0",
    "red": "#ad5148", "red_shadow": "#743944", "red_light": "#b87956",
    "sage": "#7d8764", "sage_shadow": "#58644f",
    "ochre": "#d2b06a", "gold": "#d2b06a",
    "hair_glint": "#80687e",
}
LOOKS = {
    "protagonist": ("sage", "sage_shadow"),
    "civilian_man": ("sage", "sage_shadow"),
    "civilian_woman": ("ochre", "leather_light"),
    "civilian_elder": ("sage_shadow", "leather"),
    "civilian_merchant": ("leather_light", "leather"),
    "civilian_worker": ("linen", "grey"),
    **{f"blue_soldier_{i}": ("blue", "blue_shadow") for i in range(3)},
    "blue_commander": ("blue", "blue_shadow"),
    **{f"red_soldier_{i}": ("red", "red_shadow") for i in range(3)},
    "red_officer": ("red", "red_shadow"),
}


def sprite(look, action, frame, direction):
    """Directions: down, left, right, up. Pivot is always (16, 28)."""
    if direction == 1:
        return sprite(look, action, frame, 2).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    im = Image.new("RGBA", (32, 32))
    d = ImageDraw.Draw(im)
    main, shade = LOOKS[look]
    military = look.startswith(("blue", "red"))
    hero = look == "protagonist"
    officer = look == "red_officer"
    commander = look == "blue_commander"
    leader = officer or commander
    variant = int(look[-1]) if look[-1].isdigit() else 0
    side, back = direction == 2, direction == 3
    woman, elder, merchant, worker = (look == "civilian_" + n for n in
                                     ("woman", "elder", "merchant", "worker"))

    def rect(box, color):
        d.rectangle(box, fill=PALETTE[color])

    def poly(points, color):
        d.polygon(points, fill=PALETTE[color])

    def line(points, color, width=1):
        d.line(points, fill=PALETTE[color], width=width)

    def head(x, y, wounded=False):
        # A large twelve-pixel head, like the existing protagonist's proportions.
        poly([(x+3,y),(x+8,y),(x+10,y+2),(x+11,y+4),(x+11,y+8),
              (x+8,y+11),(x+3,y+11),(x,y+8),(x,y+3)], "ink")
        rect((x+1,y+3,x+9,y+8), "skin_shadow")
        rect((x+3,y+4,x+10,y+8), "skin")
        rect((x+4,y+9,x+8,y+10), "skin")
        if military and not officer:
            rect((x+1,y+2,x+10,y+4), main)
            rect((x+3,y+1,x+8,y+1), "steel_shadow")
            rect((x+3,y+2,x+7,y+2), "blue_light" if main == "blue" else "red_light")
            rect((x,y+4,x+1,y+9), shade)
            if not side:
                rect((x+10,y+4,x+11,y+9), shade)
            if variant == 1:
                rect((x+5,y+1,x+6,y+4), "steel")
            if commander:
                rect((x+4,y-1,x+7,y+1), "gold")
                rect((x+5,y-1,x+6,y-1), "linen")
            line([(x+2,y+4),(x+9,y+4)], shade)
            rect((x+8,y+2,x+9,y+2), "steel")
            rect((x+1,y+7,x+1,y+8), "steel_shadow")
        else:
            hair = "grey" if elder else "hair"
            rect((x+1,y+2,x+9,y+4), hair)
            rect((x,y+4,x+2,y+8), hair)
            rect((x+3,y+1,x+8,y+1), hair)
            rect((x+3,y+2,x+6,y+2), "linen" if elder else "hair_light")
            if officer:
                rect((x,y+5,x+1,y+6), "grey")  # Grey temples, uncovered head.
                line([(x+4,y+10),(x+8,y+10)], "hair")
                rect((x+8,y+7,x+8,y+8), "skin_shadow")
                rect((x+4,y+5,x+5,y+5), "hair")
                rect((x+8,y+5,x+9,y+5), "hair")
                line([(x+4,y+2),(x+7,y+2)], "hair_glint")
            if woman:
                rect((x-1,y+4,x,y+12), hair)
                rect((x-1,y+12,x,y+13), "ochre")
                rect((x-1,y+7,x-1,y+8), "hair_glint")
            if elder:
                rect((x+3,y+9,x+8,y+10), "linen")
                rect((x+4,y+11,x+7,y+11), "grey")
            if merchant:
                rect((x,y+2,x+11,y+4), "leather")
                rect((x+3,y,x+8,y+2), "ochre")
                rect((x+2,y+3,x+9,y+3), "linen")
            if worker:
                rect((x+1,y+3,x+10,y+4), "sage")
                rect((x,y+4,x+1,y+5), "sage_shadow")
            if not elder and not merchant:
                rect((x+3,y+4,x+4,y+5), hair)
            if hero:
                # Two stepped tufts and a swept fringe keep the original identity.
                poly([(x,y+3),(x+2,y),(x+4,y+1),(x+6,y-2),
                      (x+7,y),(x+9,y+1),(x+10,y+3),(x+7,y+4),
                      (x+6,y+6),(x+4,y+4),(x+2,y+5)], "hair")
                line([(x+2,y+2),(x+4,y+1),(x+5,y+2)], "hair_glint")
                line([(x+6,y),(x+8,y+2)], "hair_glint")
                rect((x,y+6,x+1,y+8), "hair_glint")
        if back:
            rect((x+1,y+5,x+10,y+8), main if military and not officer else ("grey" if elder else "hair"))
            rect((x+3,y+9,x+8,y+10), shade if military and not officer else ("grey" if elder else "hair"))
            if not military or officer:
                line([(x+3,y+6),(x+5,y+7),(x+7,y+7)], "grey" if elder else "hair_glint")
        else:
            if not side:
                rect((x+4,y+6,x+4,y+6), "ink")
            rect((x+9,y+6,x+9,y+6), "ink")
            rect((x+7,y+8,x+7,y+8), "skin_shadow")
            rect((x+6,y+10,x+7,y+10), "skin_shadow")
            if hero:
                rect((x+9,y+6,x+9,y+6), "blue_shadow")
            if wounded:
                line([(x+8,y+6),(x+10,y+6)], "ink")

    if action == "fallen":
        # A drawn prone body: helmet/face at the left, boots at the right.
        poly([(4,20),(9,18),(17,20),(24,22),(28,23),(28,27),
              (21,27),(18,26),(9,27),(3,25)], "ink")
        if leader:
            poly([(9,20),(16,19),(22,23),(19,27),(9,27)], shade)
        rect((12,21,20,24), main)
        rect((13,25,20,25), shade)
        rect((15,22,18,22), "blue_light" if main == "blue" else "red_light")
        rect((20,23,21,25), "leather_light")
        rect((22,24,26,26), "leather")
        rect((18,22,21,24), "leather")
        head(2, 15 - (2 if frame else 0), True)
        rect((12,25,15,26), "skin_shadow")
        if leader:
            rect((13,21,14,23), "gold")
        if side:
            im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        return im

    if action == "defeated":
        # One knee on the ground, face lowered, sword used as support.
        poly([(10,13),(20,14),(22,23),(20,27),(9,27),(8,22)], "ink")
        poly([(10,16),(13,16),(13,25),(8,26)], shade)
        rect((12,17,19,22), main)
        rect((12,22,18,23), "leather")
        rect((10,24,14,26), shade)
        rect((17,24,21,26), "leather")
        rect((19,18,23,20), "skin_shadow")
        head(11, 8, True)
        line([(25,18),(25,27)], "ink", 3)
        line([(25,20),(25,26)], "steel")
        line([(23,19),(27,19)], "gold")
        rect((22,17,24,18), "skin")
        rect((11,18,12,19), "gold")
        rect((12,20,13,22), "red_shadow")
        rect((18,25,20,25), "steel_shadow")
        return im

    stride = 1 if action == "walk" and frame == 1 else -1 if action == "walk" and frame == 3 else 0
    if hero and action == "walk":
        stride = (0, 1, 1, 0, -1, -1)[frame]
    # Eight existing player attack slots, four drawn poses, identical game timing.
    if hero and action == "attack":
        frame //= 2
    lean = -1 if action == "hurt" else 1 if action == "attack" and frame == 1 else 0
    # Feet share y=27 in every standing frame; the lifted foot moves up by 2.
    left_bottom, right_bottom = 27 - (2 if stride > 0 else 0), 27 - (2 if stride < 0 else 0)
    lx, rx = (10 if stride else 11), (18 if stride else 17)
    rect((lx,20,lx+4,left_bottom), "ink")
    rect((rx,20,rx+4,right_bottom), "ink")
    rect((lx+1,21,lx+3,left_bottom-2), shade if military else "leather")
    rect((rx+1,21,rx+3,right_bottom-2), shade if military else "leather")
    rect((lx+1,left_bottom-1,lx+3,left_bottom-1), "leather_light")
    rect((rx+1,right_bottom-1,rx+3,right_bottom-1), "leather_light")
    if leader:
        poly([(9,11),(21,11),(24,24),(19,25),(17,23),(9,24),(7,22)], "ink")
        poly([(9,13),(13,13),(12,23),(8,22)], shade)
        line([(9,19),(9,22),(11,23)], "gold")
        if back:
            poly([(12,13),(20,13),(22,23),(17,22),(14,24)], main)
            line([(14,16),(14,21)], shade)
            line([(17,22),(21,23)], "gold")
    left, right = 10+lean, 21+lean if leader else 20+lean
    poly([(left+2,12),(right-2,12),(right,14),(right,20),
          (right-1,22),(left,22),(left-1,15)], "ink")
    rect((left+1,14,right-1,19), main)
    rect((left+1,18,left+2,20), shade)
    rect((left+1,21,right-1,22), shade)
    line([(right-2,16),(right-2,19)], shade)
    rect((left,20,right,20), "leather")
    rect((16+lean,20,17+lean,20), "gold" if leader else "ochre")
    if military:
        rect((left+2,13,right-2,14), "blue_light" if main == "blue" else "red_light")
        if variant == 2:
            line([(right-2,14),(left+2,19)], "leather_light")
        if leader:
            rect((left-1,13,left+2,15), "gold")
            rect((left,13,left+1,13), "linen")
        rect((left+3,17,right-3,17), "blue_light" if main == "blue" else "red_light")
        rect((right-1,22,right-1,23), "steel_shadow")
        if officer:
            line([(13,16),(15,18),(18,19)], "gold")
    else:
        line([(13,15),(15,17),(17,15)], "linen")
        rect((12,18,12,19), shade)
        if hero:
            line([(12,16),(18,19)], "leather")
            rect((11,21,13,23), "leather")
            rect((11,21,13,21), "leather_light")
            rect((17,16,18,17), "linen")
    if woman:
        poly([(11,19),(19,19),(22,24),(9,24)], "ink")
        poly([(12,19),(18,19),(20,23),(11,23)], main)
        rect((13,14,17,21), "linen")
        rect((11,23,19,23), "leather_light")
        rect((14,20,16,20), "ochre")
    if merchant:
        rect((12,15,19,22), "linen")
        rect((14,17,17,18), "ochre")
        line([(14,18),(14,20),(17,20),(17,18)], "leather_light")
        rect((12,22,18,22), "grey")
    if worker:
        line([(12,14),(12,19)], "leather")
        line([(18,14),(18,19)], "leather")
        rect((12,18,13,19), "ochre")
        rect((18,18,19,19), "ochre")
        rect((18,21,20,23), "leather_light")
    # Small arm swing; no extra outlines or subpixel smoothing.
    arm_y = 16 + stride
    rect((8+lean,14,10+lean,arm_y+4), "ink")
    rect((9+lean,15,10+lean,arm_y+1), main)
    rect((9+lean,arm_y+2,10+lean,arm_y+3), "skin")
    rect((21+lean,14,23+lean,20-stride), "ink")
    rect((21+lean,15,22+lean,17-stride), main)
    rect((21+lean,18-stride,22+lean,19-stride), "skin")
    rect((9+lean,arm_y+3,9+lean,arm_y+3), "skin_shadow")
    rect((22+lean,19-stride,22+lean,19-stride), "skin_shadow")
    rect((9+lean,16,10+lean,16), shade)
    rect((21+lean,16,22+lean,16), shade)
    if elder:
        line([(23,19),(23,27)], "leather_light")
        rect((22,19,24,19), "leather")
    head(10+lean, 3 if officer else 4, action == "hurt")
    if leader:
        rect((8+lean,15,11+lean,17), "gold")
        rect((9+lean,15,10+lean,15), "linen")
        rect((8+lean,18,10+lean,18), shade)
        rect((8+lean,16,8+lean,16), "linen")
    if military and not back:
        # Compact faction shield. Officers keep the free hand visible.
        if not officer:
            poly([(7,16),(12,16),(13,18),(12,22),(10,24),(7,22)], "ink")
            poly([(8,17),(11,17),(12,18),(11,21),(10,22),(8,21)], main)
            line([(9,18),(9,21)], "gold" if commander else "steel")
            rect((10,18,11,18), "blue_light" if main == "blue" else "red_light")
            rect((8,17,8,17), "steel")
            if variant == 1:
                line([(8,19),(11,19)], "steel")
            elif variant == 2:
                rect((10,21,11,21), "steel")
        if action == "windup" or (action == "attack" and frame == 0):
            line([(23,16),(26,6)], "ink", 3)
            line([(24,13),(26,6)], "steel")
            line([(22,14),(26,15)], "gold" if leader else "leather_light")
        elif action == "attack" and frame == 1:
            line([(23,17),(30,14)], "ink", 3)
            line([(25,16),(30,14)], "steel")
            line([(24,14),(25,18)], "gold" if leader else "leather_light")
        elif action == "attack" and frame == 2:
            line([(23,19),(29,24)], "ink", 3)
            line([(25,21),(29,24)], "steel")
        else:
            line([(24,20),(27,12)], "ink", 3)
            line([(25,18),(27,12)], "steel")
            line([(23,19),(26,20)], "gold" if leader else "leather_light")
            rect((26,14,26,15), "linen")
        if action == "windup" and frame == 1:
            rect((21,15,23,16), "skin")
    if hero:
        # Same compact steel/leather language as the troops, without their shield.
        if action != "attack":
            line([(8,23),(10,19)], "ink", 3)
            line([(8,23),(10,19)], "leather_light")
        else:
            # Separate cardinal trajectories keep north/south attacks readable.
            if back:
                tip = ((25,9),(23,2),(15,2),(23,13))[frame]
                grip = (23,15)
            elif side:
                tip = ((26,6),(30,14),(28,24),(26,15))[frame]
                grip = (23,18)
            else:
                tip = ((26,10),(26,25),(17,26),(25,18))[frame]
                grip = (22,19)
            line([grip,tip], "ink", 3)
            line([grip,tip], "steel")
            rect((grip[0]-2,grip[1]-1,grip[0]+1,grip[1]), "leather_light")
            rect((grip[0]-2,grip[1]+1,grip[0]-1,grip[1]+2), "skin")
    return im


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"frame_size": [32,32], "pivot": [16,28], "draw_scale": 1.5,
                "directions": ["down","left","right","up"], "palette": PALETTE,
                "characters": {}}
    for look in LOOKS:
        actions = {"idle":1, "walk":4}
        if look == "protagonist":
            actions = {"idle":1, "walk":6, "attack":8}
        if look.startswith(("blue", "red")):
            actions["fallen"] = 2 if look == "blue_commander" else 1
        if look.startswith("red"):
            actions.update(attack=3, windup=2 if look == "red_officer" else 1, hurt=1)
        if look == "red_officer":
            actions["defeated"] = 1
        manifest["characters"][look] = {}
        for action, count in actions.items():
            sheet = Image.new("RGBA", (32*count, 128))
            for direction in range(4):
                for frame in range(count):
                    sheet.paste(sprite(look, action, frame, direction), (32*frame,32*direction))
            filename = f"{look}_{action}.png"
            sheet.save(OUT / filename)
            manifest["characters"][look][action] = {"file":filename, "frames_per_direction":count}
    # Existing loading / checkpoint / restore callers retain their public paths.
    # Frame zero is a neutral stance; subsequent columns are the walk cycle.
    Image.open(OUT / "civilian_man_walk.png").save(ROOT / "assets/npc/civilian_customer.png")
    Image.open(OUT / "civilian_woman_idle.png").save(ROOT / "assets/npc/civilian_seller.png")
    # Preserve the player's existing 64 px cell contract and 6/8 animation slots.
    # Native art is pasted 1:1, never upscaled: (16,20)+(16,28)=(32,48),
    # matching the renderer's current (48,72) pivot at 1.5x, and every NPC foot.
    for action, count, filename in (("walk",6,"f_player_sheet.png"),
                                     ("attack",8,"f_player_attack_sheet.png")):
        native = Image.open(OUT / f"protagonist_{action}.png")
        compatible = Image.new("RGBA", (64*count,256))
        for direction in range(4):
            for index in range(count):
                tile = native.crop((32*index,32*direction,32*(index+1),32*(direction+1)))
                compatible.paste(tile,(64*index+16,64*direction+20))
        compatible.save(ROOT / "assets/player" / filename)
    manifest["player_compatibility"] = {"cell_size":[64,64], "native_offset":[16,20],
                                        "pivot":[32,48], "walk_columns":6, "attack_columns":8}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    print(f"Built {len(LOOKS)} characters in {OUT}")


if __name__ == "__main__":
    build()
