"""Native pixel architecture and hillside flora; surfaces are cached at integer 2x."""
from functools import lru_cache
import random
import pygame
from world import asset_art

INK=(37,43,52); DARK=(53,62,63); STONE=(112,123,116); LIGHT=(167,170,143)
WOOD=(103,79,61); PLANK=(158,122,80); PAPER=(212,195,152)
MOSS=(91,109,76); TEAL=(69,107,109); RUST=(140,86,67)


def _canvas(size): return pygame.Surface(size,pygame.SRCALPHA)
def _finish(im): return pygame.transform.scale_by(im,2)


@lru_cache(maxsize=1)
def north_barrier():
    im=_canvas((85,26))
    for x in (0,40,81):
        pygame.draw.rect(im,INK,(x,0,4,26))
        pygame.draw.rect(im,PLANK,(x+1,1,2,24))
    for y in (14,21):
        pygame.draw.rect(im,INK,(0,y,85,4))
        pygame.draw.line(im,WOOD,(3,y+1),(81,y+1))
    pygame.draw.line(im,PLANK,(4,23),(39,14),2)
    pygame.draw.line(im,PLANK,(44,14),(80,23),2)
    pygame.draw.rect(im,STONE,(39,17,6,4))
    return _finish(im)


@lru_cache(maxsize=100)
def prop(kind):
    replacement=asset_art.prop('encosta',kind,(128,104))
    if replacement is not None: return replacement
    im=_canvas((64,52)); r=lambda c,b:pygame.draw.rect(im,c,b)
    line=lambda c,a,b,w=1:pygame.draw.line(im,c,a,b,w)
    if kind in ('route_sign','post_sign'):
        r(INK,(28,10,5,40)); r(WOOD,(29,12,3,36)); r(INK,(5,7,54,20)); r(PLANK,(7,9,50,16))
        font=pygame.font.Font(None,10)
        label=font.render('ENCOSTA' if kind=='route_sign' else 'CONVALESCENÇA',False,PAPER)
        im.blit(label,label.get_rect(center=(32,18)))
        line(PAPER,(47,23),(54,18)); line(PAPER,(54,18),(49,15))
    elif kind=='well':
        pygame.draw.ellipse(im,INK,(7,19,50,26)); pygame.draw.ellipse(im,STONE,(9,18,46,22))
        pygame.draw.ellipse(im,DARK,(15,20,34,12)); pygame.draw.ellipse(im,TEAL,(18,23,28,7))
        for x in (11,49): r(INK,(x,1,4,28)); r(WOOD,(x+1,2,2,25))
        r(PLANK,(9,0,46,4)); line(PAPER,(32,4),(32,25)); r(WOOD,(27,25,10,7))
        for x in range(12,56,11): line(LIGHT,(x,33),(x+6,32)); line(DARK,(x,35),(x,40))
    elif kind in ('cabinet','cabinet_open'):
        r(INK,(9,2,46,47)); r(WOOD,(11,4,42,43)); r(PLANK,(14,6,36,3))
        for y in (12,24,36):
            r(DARK,(14,y,36,10)); r(PLANK,(16,y+2,32,6)); r(PAPER,(29,y+4,6,2))
        for x in (16,47): line(LIGHT,(x,9),(x,45))
        if kind=='cabinet_open': r(INK,(14,35,36,11)); r(PAPER,(22,38,20,6))
    elif kind in ('register','record','plan'):
        r(INK,(17,22,31,22)); r(WOOD,(19,24,27,18)); r(PAPER,(21,25,23,15))
        for y in (28,32,36): line(WOOD,(24,y),(39 if y!=36 else 35,y))
        if kind=='plan':
            line(TEAL,(23,35),(30,28)); line(TEAL,(30,28),(41,35)); r(RUST,(37,29,3,3))
        else: line(RUST,(24,40),(40,40))
    elif kind=='meal':
        pygame.draw.ellipse(im,INK,(3,14,58,25)); pygame.draw.ellipse(im,PLANK,(5,13,54,23))
        for x in (12,46): r(WOOD,(x,31,4,18))
        for x,y in ((19,20),(43,21),(31,16)):
            pygame.draw.ellipse(im,INK,(x-6,y-3,12,7)); pygame.draw.ellipse(im,PAPER,(x-5,y-3,10,5))
        r(TEAL,(28,25,5,7)); line(LIGHT,(11,31),(50,31))
    elif kind in ('bowl','lamp','name'):
        r(INK,(18,26,28,20)); r(STONE,(20,28,24,16)); line(LIGHT,(20,28),(44,28))
        if kind=='bowl':
            pygame.draw.arc(im,PAPER,(24,29,16,10),3.1,6.3,2); line(PAPER,(24,33),(40,33))
        elif kind=='lamp':
            r(PAPER,(29,29,6,8)); line(PAPER,(26,39),(38,39)); line(RUST,(32,26),(32,29),2)
        else:
            r(PAPER,(25,30,14,10)); line(WOOD,(28,34),(36,34)); line(WOOD,(28,37),(34,37))
    elif kind in ('seal','locket'):
        if kind=='seal':
            r(INK,(12,9,40,38)); r(STONE,(14,11,36,34)); line(LIGHT,(15,12),(49,12))
            # Three open brackets around a missing centre: same custody seal everywhere.
            for box,start,end in (((21,18,12,13),1.6,4.7),((31,18,12,13),4.7,7.8),((26,28,12,10),0,3.1)):
                pygame.draw.arc(im,PAPER,box,start,end,2)
            line(TEAL,(31,20),(32,35),1)
        else:
            pygame.draw.ellipse(im,INK,(22,18,21,24)); pygame.draw.ellipse(im,(182,142,88),(24,20,17,20))
            pygame.draw.ellipse(im,PLANK,(27,23,11,14)); line(PAPER,(27,26),(38,26)); line(PAPER,(28,29),(35,29))
            line(LIGHT,(32,18),(43,10)); line(LIGHT,(43,10),(51,19))
    elif kind=='camp':
        for x,y in ((19,36),(27,38),(35,37),(43,34),(17,28)):
            pygame.draw.ellipse(im,STONE,(x-4,y-3,8,6))
        line(INK,(20,33),(42,28),4); line(WOOD,(22,30),(40,35),3)
        r(RUST,(29,27,5,6)); r((205,143,81),(30,26,3,5)); r(PAPER,(31,26,1,2))
        r(DARK,(47,30,10,13)); r(WOOD,(49,31,7,10))
    elif kind=='rest':
        r(INK,(4,28,56,8)); r(PLANK,(6,29,52,5)); r(WOOD,(9,35,5,14)); r(WOOD,(50,35,5,14))
        r(DARK,(9,17,25,12)); line(LIGHT,(10,18),(31,18)); r(TEAL,(40,21,6,7))
    elif kind=='supplies':
        for x,y in ((11,24),(25,20),(38,29)):
            r(INK,(x,y,15,17)); r(PLANK,(x+1,y+1,13,15)); line(PAPER,(x+2,y+4),(x+12,y+4))
            line(WOOD,(x+3,y+6),(x+12,y+13)); r(RUST,(x+9,y+2,3,3))
    elif kind=='cart':
        r(INK,(5,22,47,18)); r(WOOD,(7,24,43,14))
        for y in (25,30,35): line(PLANK,(8,y),(48,y))
        for x in (14,43):
            pygame.draw.circle(im,INK,(x,42),9); pygame.draw.circle(im,PLANK,(x,42),7,2)
            for d in (-1,1): line(WOOD,(x-4,42+d*4),(x+4,42-d*4))
        line(WOOD,(50,31),(63,43),3); r(PAPER,(20,18,13,12))
    elif kind=='fence':
        for x in range(3,63,12):
            r(INK,(x,21,5,29)); r(WOOD,(x+1,23,3,26)); line(PLANK,(x+1,23),(x+3,23))
        for y in (29,40): r(PLANK,(2,y,61,3))
    elif kind=='tools':
        line(INK,(15,19),(46,41),4); line(PLANK,(16,19),(45,40),2)
        line(STONE,(12,17),(21,14),3); r(WOOD,(29,33,15,10)); line(PAPER,(31,34),(41,34))
        line(INK,(49,26),(42,46),3); line(STONE,(43,23),(55,28),3)
    return _finish(im)


@lru_cache(maxsize=24)
def tree(variant=0):
    return asset_art.tree(variant)


@lru_cache(maxsize=24)
def rock(variant=0):
    return asset_art.rock(variant)


@lru_cache(maxsize=24)
def building(style=0):
    return asset_art.building(style)


@lru_cache(maxsize=1)
def chamber():
    return asset_art.chamber()
