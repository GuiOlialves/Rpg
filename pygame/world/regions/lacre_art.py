"""Prepared stone architecture, shelves and mechanisms on a crisp two-pixel grid."""
from functools import lru_cache
import pygame
from world import asset_art
import random
INK=(25,34,42); STONE=(73,91,99); EDGE=(116,133,132); GOLD=(170,148,99)
PAPER=(204,194,154); DARK=(43,56,65); MOSS=(78,95,82)

@lru_cache(maxsize=48)
def prop(kind,lit=False):
    replacement=asset_art.prop('lacre',kind,(128,144))
    if replacement is not None: return replacement
    s=pygame.Surface((64,72),pygame.SRCALPHA)
    r=lambda c,b:pygame.draw.rect(s,c,b)
    line=lambda c,a,b,w=1:pygame.draw.line(s,c,a,b,w)
    if kind in ('pillar','anchor'):
        r(INK,(14,6,36,60));r(STONE,(18,10,28,52));r(EDGE,(19,10,5,52))
        for y in (12,56,64): r(INK,(10,y,44,5));r(EDGE,(12,y,40,2))
        for y in range(19,51,7):line(DARK,(29,y),(37,y+3))
        if kind=='anchor':
            pygame.draw.polygon(s,GOLD if lit else DARK,[(32,19),(42,32),(32,45),(22,32)],2)
            line(PAPER if lit else EDGE,(32,26),(32,38),2)
    elif kind in ('shelf','searched'):
        r(INK,(3,10,58,57));r((92,74,62),(6,12,52,52))
        for y in (14,31,48,63):r((157,130,89),(5,y,54,3))
        for y in (17,34,51):
            for x in range(10,54,7):
                if kind=='searched' and (x+y)%3==0:continue
                r((119+(x%4)*12,123,104),(x,y,5,13));line(GOLD,(x+1,y+3),(x+3,y+3))
        if kind=='searched':r(PAPER,(32,58,15,5));line(DARK,(35,60),(44,60))
    elif kind=='desk':
        r(INK,(4,43,56,23));r((116,92,67),(6,43,52,15));r((164,134,90),(5,42,54,3))
        for x in (7,52):r(DARK,(x,56,5,10))
        r(PAPER,(14,32,22,13));line(DARK,(17,36),(32,36));r(GOLD,(46,33,5,11))
    elif kind in ('record','copy','key','relic'):
        r(INK,(12,40,40,25));r(STONE,(14,42,36,21))
        if kind=='relic':
            pygame.draw.ellipse(s,GOLD,(23,38,18,22),3);line(PAPER,(30,47),(35,52),2)
        else:
            r(PAPER,(22,44,22,14));line(DARK,(25,48),(40,48));line(DARK,(25,52),(37,52))
            if kind=='key':line(GOLD,(20,58),(40,58),2)
    elif kind in ('bowl','lamp','name','door','hand','seal'):
        r(INK,(10,39,44,28));r(STONE,(12,41,40,23));r(EDGE,(13,41,38,2))
        c=PAPER if lit else GOLD
        if kind=='bowl':pygame.draw.arc(s,c,(20,44,24,16),3.14,6.28,2)
        elif kind=='lamp':r(c,(28,44,8,13));line(c,(23,58),(41,58))
        elif kind=='name':r(c,(22,46,20,12));line(DARK,(25,50),(38,50))
        elif kind=='door':pygame.draw.lines(s,c,False,[(23,58),(23,45),(41,45),(41,58)],2)
        elif kind=='hand':pygame.draw.lines(s,c,False,[(21,49),(30,56),(40,46)],2)
        else:
            for x in (20,28,36):pygame.draw.arc(s,c,(x,44,10,15),.3,5.8,2)
    elif kind=='rest':
        r(INK,(3,49,58,16));r((142,116,81),(5,47,54,9));r(PAPER,(8,37,17,11))
        for x in (8,51):r(DARK,(x,56,5,12))
    else:
        r(INK,(16,30,32,35));r(STONE,(18,32,28,31));r(GOLD,(22,40,20,3))
    return pygame.transform.scale_by(s,2)

@lru_cache(maxsize=12)
def door(opened=False):
    s=pygame.Surface((184,178),pygame.SRCALPHA)
    pygame.draw.polygon(s,INK,[(0,178),(0,30),(35,0),(149,0),(184,30),(184,178)])
    pygame.draw.polygon(s,STONE,[(8,178),(8,33),(39,8),(145,8),(176,33),(176,178)])
    pygame.draw.rect(s,INK,(30,38,124,140));pygame.draw.rect(s,DARK,(34,42,116,136))
    if not opened:
        for x in range(36,149,14):pygame.draw.rect(s,EDGE,(x,44,4,132))
        for y in (75,139):pygame.draw.rect(s,GOLD,(34,y,116,4))
    for x in (16,165):
        for y in range(40,167,22):pygame.draw.line(s,EDGE,(x-3,y),(x+3,y+5),2)
    return s

@lru_cache(maxsize=1)
def core():
    s=pygame.Surface((360,210),pygame.SRCALPHA)
    pygame.draw.polygon(s,INK,[(2,210),(22,88),(68,16),(290,16),(338,88),(358,210)])
    pygame.draw.polygon(s,STONE,[(14,205),(35,92),(74,28),(284,28),(325,92),(345,205)])
    for x in (40,292):
        pygame.draw.rect(s,DARK,(x,65,28,124));pygame.draw.rect(s,EDGE,(x+3,69,6,114))
    pygame.draw.ellipse(s,INK,(100,22,160,160));pygame.draw.ellipse(s,GOLD,(104,26,152,152),3)
    pygame.draw.ellipse(s,EDGE,(121,43,118,118),2)
    for x in (144,169,194):pygame.draw.arc(s,GOLD,(x,65,24,62),.4,5.8,3)
    pygame.draw.rect(s,INK,(133,165,94,27));pygame.draw.rect(s,PAPER,(146,172,68,12))
    for y in (194,201):pygame.draw.line(s,EDGE,(87,y),(271,y),3)
    return s

def floor(surface,rect,variant,seed):
    asset_art.floor(surface, rect, cool=True, seed=seed)
    if variant=='gallery':
        for x in (rect[0]+100,rect[0]+rect[2]-140):
            pygame.draw.rect(surface,(52,75,82),(x,rect[1]+60,30,rect[3]-120))
            pygame.draw.line(surface,(109,135,135),(x+3,rect[1]+63),(x+3,rect[1]+rect[3]-63),2)
