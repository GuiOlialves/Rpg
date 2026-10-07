"""Authored cutaway masonry and small pixel props for the road watchpost."""
import random
import pygame

INK = (38, 39, 38)
STONE = (111, 112, 103)
LIGHT = (159, 151, 125)
WOOD = (103, 75, 52)
PLANK = (149, 113, 73)


def wall(width, seed=0):
    im = pygame.Surface((width // 2, 24), pygame.SRCALPHA)
    rng = random.Random(seed)
    im.fill(INK, (0, 5, im.width, 19))
    for row in range(3):
        for x in range(-8 if row % 2 else 0, im.width, 15):
            color = tuple(c + rng.randrange(-6, 7) for c in STONE)
            pygame.draw.rect(im, color, (x + 1, 6 + row * 6, 13, 5))
            pygame.draw.line(im, LIGHT, (x + 2, 6 + row * 6), (x + 10, 6 + row * 6))
    pygame.draw.rect(im, LIGHT, (0, 4, im.width, 3))
    pygame.draw.line(im, (76, 85, 61), (3, 23), (im.width - 3, 23), 2)
    for _ in range(max(1, width // 48)):
        x = rng.randrange(4, max(5, im.width - 4))
        pygame.draw.lines(im, (64, 67, 61), False, [(x, 7), (x - 2, 13), (x + 1, 18)], 1)
        pygame.draw.rect(im, (103, 112, 71), (x, 21, 4, 2))
    return pygame.transform.scale_by(im, 2)


def floor(terrain, rect, *, wooden=False, seed=0):
    rng = random.Random(seed)
    pygame.draw.rect(terrain, (42, 42, 37), rect.inflate(6, 6))
    base = (108, 86, 62) if wooden else (117, 116, 101)
    pygame.draw.rect(terrain, base, rect)
    for y in range(rect.top, rect.bottom, 18 if wooden else 28):
        pygame.draw.line(terrain, (73, 62, 47) if wooden else (79, 82, 74),
                         (rect.left, y), (rect.right - 1, y), 2)
        for x in range(rect.left + (12 if y // 28 % 2 else 0), rect.right, 56):
            pygame.draw.line(terrain, (77, 69, 52) if wooden else (91, 92, 80),
                             (x, y + 2), (x, min(rect.bottom - 1, y + (15 if wooden else 25))), 2)
    for _ in range(rect.width * rect.height // 260):
        x, y = rng.randrange(rect.left, rect.right), rng.randrange(rect.top, rect.bottom)
        pygame.draw.line(terrain, tuple(c + rng.choice((-10, 9)) for c in base), (x, y), (x + 4, y), 2)
    # Dust accumulates against walls; the central circulation stays legible.
    for edge in (pygame.Rect(rect.x, rect.y, rect.width, 8),
                 pygame.Rect(rect.x, rect.y, 8, rect.height)):
        pygame.draw.rect(terrain, (87, 85, 65), edge)


def prop(kind):
    sizes = {"desk": (70, 44), "bed": (34, 42), "locker": (32, 40),
             "gate": (68, 54), "breach": (38, 40), "postern": (32, 44), "closed_postern": (32,44),
             "flag": (34, 58), "shelf": (50, 42), "chair": (28, 32)}
    im = pygame.Surface(sizes.get(kind, (32, 28)), pygame.SRCALPHA)
    def rect(c, b): pygame.draw.rect(im, c, b)
    def line(c, a, b, w=1): pygame.draw.line(im, c, a, b, w)
    def poly(c, p): pygame.draw.polygon(im, c, p)
    if kind == "desk":
        rect(INK, (7, 17, 57, 19)); rect(WOOD, (9, 19, 53, 14))
        poly(INK, [(4, 12), (56, 9), (66, 18), (13, 22)])
        poly(PLANK, [(7, 13), (55, 11), (62, 17), (14, 19)])
        for y in (14, 17): line((177, 134, 81), (12, y), (52, y - 2))
        rect(INK, (10, 30, 5, 10)); rect(INK, (55, 28, 5, 12))
        poly((190, 179, 145), [(23, 13), (39, 12), (43, 16), (26, 18)])
        line((96, 81, 59), (27, 14), (36, 14)); rect((42, 42, 39), (46, 12, 4, 5))
        rect((183, 174, 140), (14, 8, 4, 8)); rect((88, 87, 73), (14, 7, 4, 2))
    elif kind == "bed":
        rect(INK, (4, 7, 25, 30)); rect(WOOD, (6, 9, 21, 26))
        rect((104, 105, 84), (7, 15, 19, 18)); rect((177, 172, 137), (8, 10, 17, 6))
        rect((127, 123, 93), (7, 17, 19, 4)); line((65, 70, 61), (9, 30), (22, 22))
        for x in (4, 27): rect(PLANK, (x, 5, 3, 34))
    elif kind in {"locker", "shelf"}:
        w = im.width - 8
        rect(INK, (4, 5, w, 32)); rect(WOOD, (6, 7, w - 4, 27))
        for y in (8, 17, 27): line(PLANK, (7, y), (w + 1, y), 2)
        if kind == "locker":
            rect((46, 43, 36), (10, 11, 16, 21)); poly(PLANK, [(23, 11), (31, 15), (31, 34), (23, 29)])
            line(INK, (26, 17), (29, 18)); rect(LIGHT, (12, 30, 9, 2))
        else:
            for x in (10, 22, 33): rect((163, 148, 109), (x, 12, 7, 5))
            rect((77, 91, 65), (10, 24, 16, 6)); rect((184, 172, 135), (30, 25, 10, 4))
    elif kind in {"gate", "postern", "closed_postern"}:
        w = im.width - 10
        for x in (3, im.width - 7):
            rect(INK, (x, 5, 5, im.height - 7)); rect(STONE, (x + 1, 7, 3, im.height - 10))
        if kind == "gate":
            rect(INK, (9, 8, w - 6, 39)); rect(WOOD, (11, 10, w - 10, 34))
            for x in range(12, w, 8): line(PLANK, (x, 12), (x, 42), 2)
            line((62, 63, 59), (10, 19), (w, 19), 3)
            line((62, 63, 59), (11, 35), (w, 35), 3)
            poly((0, 0, 0, 0), [(25, 9), (35, 9), (31, 25), (26, 23)])
            line(PLANK, (22, 29), (49, 40), 4); line(INK, (23, 29), (49, 40))
        elif kind == "postern":
            rect((31, 35, 33), (9, 7, 15, 32))
            poly(WOOD, [(22, 8), (30, 12), (30, 39), (22, 35)])
            line(PLANK, (23, 9), (29, 13)); rect(LIGHT, (24, 24, 2, 3))
        else:
            rect(WOOD,(9,7,15,32))
            for x in (10,16,22): line(PLANK,(x,9),(x,36),2)
            line(INK,(9,18),(23,18),2); line(INK,(9,30),(23,30),2)
    elif kind == "breach":
        for x in (5, 25):
            rect(INK, (x, 6, 5, 32)); rect(PLANK, (x + 1, 8, 3, 25))
        line(WOOD, (7, 15), (28, 22), 4); line(LIGHT, (8, 16), (28, 23))
        line((68, 65, 51), (10, 18), (22, 25), 2)
        line(PLANK, (13, 34), (34, 28), 3)
    elif kind == "flag":
        rect(INK, (14, 3, 4, 53)); rect(PLANK, (15, 4, 2, 50))
        poly((75, 75, 59), [(18, 5), (31, 8), (28, 17), (31, 22), (22, 20), (18, 25)])
        line((142, 137, 93), (18, 7), (28, 10)); line((49, 52, 45), (22, 11), (21, 18))
        poly(STONE, [(7, 54), (17, 50), (26, 55), (24, 58), (8, 58)])
    elif kind == "chair":
        poly(INK, [(4, 15), (20, 7), (27, 14), (12, 23)])
        poly(WOOD, [(6, 16), (20, 10), (24, 14), (12, 20)])
        line(PLANK, (5, 13), (15, 5), 3); line(PLANK, (13, 20), (21, 27), 3)
        line(INK, (5, 18), (9, 28), 2)
    elif kind in {"archive", "dispatch", "roster"}:
        poly(INK, [(6, 5), (24, 6), (27, 22), (5, 24)])
        poly((181, 164, 126), [(8, 7), (22, 8), (24, 20), (7, 21)])
        for y in (11, 14, 17): line((102, 87, 66), (10, y), (20, y))
        pygame.draw.circle(im, (124, 56, 48) if kind == "roster" else (56, 79, 108) if kind == "dispatch" else (111, 101, 76), (19, 19), 2)
        if kind == "roster": line((72, 63, 50), (9, 19), (15, 17))
    elif kind == "token":
        line((79, 72, 56), (10, 8), (21, 8), 2)
        poly(INK, [(9, 11), (22, 11), (24, 20), (20, 24), (9, 22)])
        poly((172, 143, 85), [(11, 13), (20, 13), (22, 20), (19, 22), (11, 20)])
        line((224, 193, 117), (12, 13), (19, 13)); line((86, 72, 49), (13, 17), (19, 17))
        rect((65, 58, 45), (17, 19, 2, 2))
    elif kind == "papers":
        for box in ((3, 14, 12, 7), (15, 7, 12, 8), (17, 20, 10, 5)):
            rect(INK, box); rect((172, 155, 118), (box[0] + 1, box[1] + 1, box[2] - 2, box[3] - 2))
            line((103, 90, 63), (box[0] + 3, box[1] + 3), (box[0] + 8, box[1] + 3))
    return pygame.transform.scale_by(im, 2)
