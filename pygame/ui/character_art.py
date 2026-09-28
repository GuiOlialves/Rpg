"""Rendering contract for the original O Vale character pack; no actor logic."""
import pygame

FRAME = 32
DRAW_SIZE = 48
PIVOT = (16, 28)


def character_sheet(load, character, animation="idle"):
    return load(f"assets/vale_characters/{character}_{animation}.png")


def character_frame(sheet, index=0, facing=0, draw_size=DRAW_SIZE):
    count = sheet.get_width() // FRAME
    frame = sheet.subsurface(((index % count) * FRAME, facing * FRAME, FRAME, FRAME))
    return pygame.transform.scale(frame, (draw_size, draw_size))


def draw_character(canvas, camera, sheet, x, y, index=0, facing=0, draw_size=DRAW_SIZE):
    image = character_frame(sheet, index, facing, draw_size)
    canvas.blit(image, (round(x - draw_size / 2 - camera[0]),
                        round(y - PIVOT[1] * draw_size / FRAME - camera[1])))


def fallen_image(sheet, index=0, facing=0, draw_size=DRAW_SIZE):
    image = character_frame(sheet, index, facing, draw_size)
    bounds = image.get_bounding_rect()
    # The commander's raised-head reaction must not recenter his body.
    for other in range(sheet.get_width() // FRAME):
        bounds.union_ip(character_frame(sheet, other, facing, draw_size).get_bounding_rect())
    return image.subsurface(bounds).copy()
