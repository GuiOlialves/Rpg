"""Curated original atlas art. Render-time crops never modify source PNGs."""
from functools import lru_cache
import random
import pygame
from core.assets import load


@lru_cache(maxsize=128)
def sprite(name, crop=None, color=None):
    path = name if '/' in name else 'assets/world_polish/' + name + '.png'
    image = load(path)
    if crop:
        image = image.subsurface(crop).copy()
    bounds = image.get_bounding_rect()
    if bounds.width:
        image = image.subsurface(bounds).copy()
    if color:
        image.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return image


@lru_cache(maxsize=256)
def fitted(name, size, crop=None, color=None):
    """Original prop canvas and foot position stay stable across art replacement."""
    source = sprite(name, crop, color)
    scale = min((size[0]-4)/source.width, (size[1]-4)/source.height)
    source = pygame.transform.scale(source, (max(1, round(source.width*scale)), max(1, round(source.height*scale))))
    image = pygame.Surface(size, pygame.SRCALPHA)
    image.blit(source, ((size[0]-source.width)//2, size[1]-source.height-4))
    return image


def furniture(kind, size):
    crops = {'bed': (48,0,32,40), 'shelf': (160,80,32,48),
             'locker': (0,0,48,80),
             'desk': (112,176,48,32), 'chair': (8,216,16,24),
             'rest': (48,0,32,40)}
    if kind in crops:
        return fitted('assets/prologue/interior.png', size, crops[kind], (235,228,204))
    return None


def prop(family, kind, size):
    if family in ('post', 'lacre', 'encosta'):
        image = furniture(kind, size)
        if image is not None:
            return image
    if kind == 'watchpost':
        return fitted('tower', size, color=(216,213,189))
    names = {'cart': 'village_decor_1', 'wall': 'Brown_ruins2', 'well': 'village_decor_13'}
    if kind in names:
        return fitted(names[kind], size)
    if kind == 'crate':
        return fitted('sprites_meu/vila_tile-set/2 Objects/4 Box/3.png', size)
    if family == 'lacre' and kind == 'pillar':
        return fitted('temple_exterior', size, (232,224,24,32), (173,196,193))
    return None


@lru_cache(maxsize=32)
def tree(variant=0, size=(132,178), dry=False):
    names = ('Willow1', 'Curved_tree1', 'Luminous_tree3', 'Swirling tree1', 'White_tree1')
    return fitted(names[variant % len(names)], size, color=(231,216,168) if dry else None)


def bush(variant=0, size=(48,40), dry=False):
    names = ('Bush_blue_flowers2', 'Fern1_1', 'Bush_simple2_2', 'Bush_pink_flowers2')
    return fitted('Autumn_bush2' if dry else names[variant % 4], size)


def rock(variant=0, size=(108,78)):
    return fitted(('Rock4_1_no_shadow', 'Rock4_2_no_shadow', 'Rock1_3_no_shadow')[variant % 3], size)


@lru_cache(maxsize=8)
def building(style):
    sizes = ((240,244),(194,276),(260,224))
    if style % 3 == 0:
        image = fitted('workshop', sizes[0], (0,0,144,160), (211,218,186)).copy()
    elif style % 3 == 1:
        image = fitted('sprites_meu/vila_tile-set/2 Objects/7 House/1.png', sizes[1], color=(209,220,190)).copy()
    else:
        image = fitted('temple_exterior', sizes[2], (112,224,112,64), (224,231,203)).copy()
    # Ivy from the atlas, placed against walls; open wards retain their posts.
    ivy = fitted('Fern1_1', (42,38))
    for x in (4, image.width-46):
        image.blit(ivy, (x,image.height-42))
    return image


@lru_cache(maxsize=1)
def chamber():
    image = pygame.Surface((712,552),pygame.SRCALPHA)
    # The old doorway stays centered at x=356, with its threshold at the base.
    temple = fitted('temple_exterior',(580,500),(0,0,160,144),(207,222,204))
    image.blit(temple,(66,48))
    for x in (6,594):
        image.blit(fitted('White_ruins3',(112,140)),(x,400))
    return image


@lru_cache(maxsize=16)
def tile(wooden=False, cool=False):
    if wooden:
        source = load('assets/prologue/wooden.png')
    else:
        source = load('assets/world_polish/temple_walls.png').subsurface((16,112,32,16)).copy()
    source = pygame.transform.scale_by(source, 2)
    source.fill((151,174,180,255) if cool else (205,203,179,255),special_flags=pygame.BLEND_RGBA_MULT)
    return source


def floor(surface, rect, wooden=False, cool=False, seed=0):
    rect = pygame.Rect(rect)
    old_clip = surface.get_clip()
    surface.set_clip(rect.clip(old_clip))
    source = tile(wooden, cool)
    for y in range(rect.top,rect.bottom,source.height):
        for x in range(rect.left,rect.right,source.width):
            surface.blit(source,(x,y))
    # Thin dust along the wall keeps circulation and elevations readable.
    shade = pygame.Surface(rect.size,pygame.SRCALPHA)
    pygame.draw.rect(shade,(18,28,27,42),(0,0,rect.width,6))
    pygame.draw.rect(shade,(18,28,27,28),(0,0,6,rect.height))
    surface.blit(shade,rect)
    surface.set_clip(old_clip)


def water(surface, rect, seed=0):
    rect=pygame.Rect(rect)
    source=load('assets/world_polish/lake.png')
    crop=source.subsurface((source.width*3//8,source.height*3//8,source.width//4,source.height//4)).copy()
    crop.fill((105,165,155,255),special_flags=pygame.BLEND_RGBA_MULT)
    old=surface.get_clip();surface.set_clip(rect.clip(old))
    rng=random.Random(seed)
    variants=[crop,pygame.transform.flip(crop,True,False),pygame.transform.flip(crop,False,True)]
    for y in range(rect.top,rect.bottom,crop.height):
        for x in range(rect.left,rect.right,crop.width):
            surface.blit(rng.choice(variants),(x,y))
    surface.set_clip(old)


def bank(surface, x, top, bottom, flip=False):
    # Vertical riverbank from the temple coast atlas; water has a visible edge.
    source=sprite('river_banks',(336,16,32,64))
    source=pygame.transform.scale(source,(32,64))
    if flip: source=pygame.transform.flip(source,True,False)
    old=surface.get_clip();surface.set_clip(pygame.Rect(x,top,32,bottom-top).clip(old))
    for y in range(top,bottom,64):surface.blit(source,(x,y))
    surface.set_clip(old)
