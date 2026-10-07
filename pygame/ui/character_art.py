"""Rendering contract for the original O Vale character pack; no actor logic."""
from functools import lru_cache
import pygame
from core.animation import (BODY_FRAME, BODY_DRAW_SIZE, BODY_PIVOT, HERO_FRAME, HERO_PIVOT, WEAPON_FRAME,
                            WEAPON_PIVOT, HEAVY_WEAPON_FRAME, HEAVY_WEAPON_PIVOT,
                            DASH_TRAIL_FRAMES, DASH_TRAIL_ALPHA)

FRAME = BODY_FRAME
DRAW_SIZE = BODY_DRAW_SIZE
PIVOT = BODY_PIVOT
_sheet_geometry = {}


def character_sheet(load, character, animation="idle"):
    return _character_sheet(getattr(load,'character_source_loader',load),character,animation)


@lru_cache(maxsize=160)
def _character_sheet(load, character, animation="idle"):
    sheet = load(f"assets/vale_characters/{character}_{animation}.png")
    size,pivot=(HERO_FRAME,HERO_PIVOT) if character=='protagonist' else ((FRAME,FRAME),PIVOT)
    _sheet_geometry[sheet]=(size,pivot)
    prepared_frames(sheet, DRAW_SIZE, height=size[1])
    return sheet


@lru_cache(maxsize=192)
def prepared_frames(sheet, draw_size=DRAW_SIZE, cell=FRAME, height=None):
    """Slice and nearest-scale the entire atlas once, including alpha variants."""
    height = height or cell
    return tuple(tuple(pygame.transform.scale(
        sheet.subsurface((index*cell, row*height, cell, height)),
        (draw_size, round(draw_size*height/cell)))
        for index in range(sheet.get_width()//cell))
        for row in range(sheet.get_height()//height))


def character_frame(sheet, index=0, facing=0, draw_size=DRAW_SIZE):
    size,_ = _sheet_geometry.get(sheet,((FRAME,FRAME),PIVOT))
    frames = prepared_frames(sheet, draw_size, height=size[1])
    return frames[facing % len(frames)][index % len(frames[0])]


def draw_character(canvas, camera, sheet, x, y, index=0, facing=0, draw_size=DRAW_SIZE):
    image = character_frame(sheet, index, facing, draw_size)
    _,pivot = _sheet_geometry.get(sheet,((FRAME,FRAME),PIVOT))
    canvas.blit(image, (round(x - draw_size / 2 - camera[0]),
                        round(y - pivot[1] * draw_size / FRAME - camera[1])))


def fallen_image(sheet, index=0, facing=0, draw_size=DRAW_SIZE):
    image = character_frame(sheet, index, facing, draw_size)
    bounds = image.get_bounding_rect()
    # The commander's raised-head reaction must not recenter his body.
    for other in range(sheet.get_width() // FRAME):
        bounds.union_ip(character_frame(sheet, other, facing, draw_size).get_bounding_rect())
    # Wounded actors and battlefield props declare an embedded ground shadow.
    grounded = pygame.Surface(image.get_size(),pygame.SRCALPHA)
    pygame.draw.ellipse(grounded,(22,36,38,38),
                        (bounds.left+2,bounds.bottom-5,max(1,bounds.width-4),6))
    grounded.blit(image,(0,0))
    bounds.union_ip(grounded.get_bounding_rect())
    return grounded.subsurface(bounds).copy()


@lru_cache(maxsize=512)
def alpha_image(image, alpha):
    faded = image.copy()
    faded.set_alpha(alpha)
    return faded


@lru_cache(maxsize=512)
def flash_image(image):
    flash = image.copy()
    flash.fill((140, 115, 82, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return flash


class CharacterVisual:
    """Preloaded states, weapon layers and masks shared by an entity type."""
    def __init__(self, load, look, states, draw_size=DRAW_SIZE, weapon=False):
        self.draw_size = draw_size
        self.scale = draw_size / FRAME
        self.frame_size,self.pivot = (HERO_FRAME,HERO_PIVOT) if look=='protagonist' else ((FRAME,FRAME),PIVOT)
        self.frames = {state: prepared_frames(character_sheet(load, look, state), draw_size,height=self.frame_size[1])
                       for state in states}
        self.weapons = self.hit_masks = self.hit_bounds = None
        if weapon:
            self.weapons = prepared_frames(load(f"assets/vale_characters/{look}_weapon.png"),
                                           round(WEAPON_FRAME*self.scale), cell=WEAPON_FRAME)
            masks = prepared_frames(load(f"assets/vale_characters/{look}_hit.png"),
                                     round(WEAPON_FRAME*self.scale), cell=WEAPON_FRAME)
            self.hit_masks = tuple(tuple(pygame.mask.from_surface(im) for im in row) for row in masks)
            self.hit_bounds = tuple(tuple(im.get_bounding_rect() for im in row) for row in masks)
        self.heavy_weapons = (prepared_frames(load(f"assets/vale_characters/{look}_heavy_weapon.png"),
                                             round(HEAVY_WEAPON_FRAME*self.scale),cell=HEAVY_WEAPON_FRAME)
                              if look in ('red_officer','forest_guardian') else None)
        # Prepare frequent reaction/trail variants before the first draw.
        self.flashes = {state: tuple(tuple(flash_image(im) for im in row) for row in frames)
                        for state, frames in self.frames.items() if state in ('hurt','attack','idle')}
        self.ghosts = {}
        for state in ('dash',):
            for row in self.frames.get(state, ()):
                for im in row:
                    for age in range(1,DASH_TRAIL_FRAMES+1):
                        self.ghosts[im,age] = alpha_image(im,age*DASH_TRAIL_ALPHA)

    def image(self, state, facing, index=0, flash=False):
        frames = self.flashes if flash and state in self.flashes else self.frames
        row = frames[state][facing]
        return row[index % len(row)]

    def draw(self, canvas, camera, x, y, state, facing, index=0, flash=False, weapon_index=None):
        image = self.image(state,facing,index,flash)
        canvas.blit(image,self.body_origin(x,y,camera))
        if weapon_index is not None and self.weapons:
            canvas.blit(self.weapons[facing][weapon_index],
                        self.weapon_origin(x,y,camera))

    def body_origin(self,x,y,camera=(0,0)):
        return (round(x-self.pivot[0]*self.scale-camera[0]),
                round(y-self.pivot[1]*self.scale-camera[1]))

    def weapon_origin(self,x,y,camera=(0,0)):
        return (round(x-WEAPON_PIVOT[0]*self.scale-camera[0]),
                round(y-WEAPON_PIVOT[1]*self.scale-camera[1]))

    def heavy_weapon_origin(self,x,y,camera=(0,0)):
        return (round(x-HEAVY_WEAPON_PIVOT[0]*self.scale-camera[0]),
                round(y-HEAVY_WEAPON_PIVOT[1]*self.scale-camera[1]))


def character_visual(load, look, states, draw_size=DRAW_SIZE, weapon=False):
    return _character_visual(getattr(load,'character_source_loader',load),look,states,draw_size,weapon)


@lru_cache(maxsize=32)
def _character_visual(load, look, states, draw_size=DRAW_SIZE, weapon=False):
    return CharacterVisual(load,look,states,draw_size,weapon)


@lru_cache(maxsize=8)
def effect_frames(load, kind):
    return prepared_frames(load(f"assets/vale_characters/fx_{kind}.png"),48,cell=24)[0]


def draw_effect(canvas, camera, frames, x, y, timer):
    if timer > 0:
        canvas.blit(frames[min(5,(12-timer)//2)],(round(x-24-camera[0]),round(y-24-camera[1])))
