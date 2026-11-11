"""Small native pixel props for the occupied tollhouse, at integer 2x."""
import pygame
from world.regions.watchpost_art import INK, WOOD, PLANK, STONE, LIGHT


def prop(kind):
    im = pygame.Surface((64, 46) if kind == 'barricade' else (28, 58) if kind == 'standard' else (40, 40), pygame.SRCALPHA)
    rect = lambda c, b: pygame.draw.rect(im, c, b)
    line = lambda c, a, b, w=1: pygame.draw.line(im, c, a, b, w)
    if kind == 'barricade':
        for x in (8, 49):
            line(INK, (x-5, 41), (x+10, 8), 5)
            line(PLANK, (x-5, 40), (x+10, 8), 3)
            line(WOOD, (x+10, 41), (x-4, 10), 4)
        for y in (17, 29):
            line(INK, (3, y), (60, y-3), 6)
            line(WOOD, (4, y), (59, y-3), 4)
            line(PLANK, (5, y-2), (59, y-5))
        for x in (12, 51): rect(LIGHT, (x, 15, 2, 2))
    elif kind == 'standard':
        line(INK, (9, 5), (9, 54), 4); line(PLANK, (9, 6), (9, 53), 2)
        pygame.draw.polygon(im, (108, 53, 51), [(11,6),(26,9),(22,17),(27,21),(16,22),(12,29)])
        line((176, 98, 72), (12,8), (23,11), 2)
        line((201, 163, 99), (16,12), (21,17), 2)
        pygame.draw.polygon(im, STONE, [(2,55),(9,50),(18,56),(13,58),(3,58)])
    elif kind == 'oven':
        rect(INK, (3, 11, 34, 28)); rect(STONE, (5, 13, 30, 23))
        for y in (16, 23, 30): line((72, 76, 70), (5, y), (35, y), 2)
        pygame.draw.ellipse(im, INK, (12, 19, 18, 21))
        rect((32, 35, 33), (13, 29, 17, 8)); line(LIGHT, (4, 12), (35, 12), 2)
        rect((0, 0, 0, 0), (26, 8, 14, 11))
        line((58, 53, 43), (14, 34), (28, 34), 3)
    elif kind == 'ledger':
        rect(INK, (5, 17, 29, 18)); rect((99, 57, 48), (7, 18, 25, 14))
        rect((180, 164, 124), (10, 19, 20, 9))
        for y in (21, 24, 27): line((96, 79, 59), (13, y), (26, y))
        rect((180, 145, 81), (8, 18, 2, 14))
        pygame.draw.circle(im, (120, 48, 42), (27, 29), 3)
        line(INK, (20, 17), (24, 21)); line(INK, (26, 24), (33, 29))
    elif kind == 'civilian':
        rect(INK, (5, 22, 23, 12)); rect((172, 147, 102), (6, 23, 21, 9))
        rect((206, 190, 142), (9, 24, 15, 7))
        line((111, 83, 57), (12, 25), (21, 25)); line((111, 83, 57), (11, 28), (20, 28))
        pygame.draw.circle(im, INK, (31, 21), 6)
        pygame.draw.circle(im, (154, 120, 88), (31, 21), 4)
        line((209, 172, 130), (29, 19), (31, 18))
        line(PLANK, (2, 34), (11, 37), 2)
    elif kind == 'sacks':
        for x, y in ((5, 17), (21, 22), (14, 8)):
            pygame.draw.ellipse(im, INK, (x, y, 15, 18))
            pygame.draw.ellipse(im, (159, 138, 93), (x+1, y+1, 12, 15))
            line((204, 177, 116), (x+3, y+3), (x+2, y+10))
            line(WOOD, (x+4, y+2), (x+10, y+2), 2)
    elif kind == 'lost_sacks':
        for x in range(4, 35, 4): rect((186, 154, 84), (x, 29+(x % 3), 2, 2))
        pygame.draw.polygon(im, (79, 67, 51), [(9, 19), (25, 21), (30, 31), (10, 32)])
        line((119, 93, 58), (10, 19), (18, 23), 2)
    elif kind == 'sign':
        rect(INK, (5, 4, 31, 17)); rect(WOOD, (7, 6, 27, 12))
        line(PLANK, (8, 7), (32, 7)); rect(PLANK, (18, 20, 3, 17))
        for x in (10, 17, 24): line((195, 172, 126), (x, 10), (x+3, 14), 2)
        line(INK, (26, 6), (22, 16))
    return pygame.transform.scale_by(im, 2)
