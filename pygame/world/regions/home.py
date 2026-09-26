"""Quiet, furnished home. Atlas art and solid footprints are kept separate."""
import pygame

from core.assets import load
from core.config import VIEW
from entities.interactable import Interactable


def piece(sheet, rect, scale=2, isolate=False):
    image = sheet.subsurface(rect).copy()
    if isolate:
        mask = pygame.mask.from_surface(image).connected_component()
        image.blit(mask.to_surface(setcolor=(255, 255, 255, 255),
                                   unsetcolor=(0, 0, 0, 0)), (0, 0),
                   special_flags=pygame.BLEND_RGBA_MULT)
    return pygame.transform.scale_by(image, scale)


def build():
    width, height = VIEW
    interior = load("assets/prologue/interior.png")
    walls = load("assets/prologue/walls_floor.png")
    floor = load("assets/prologue/wooden.png")
    terrain = pygame.Surface(VIEW)
    terrain.fill((30, 29, 33))
    for y in range(40, height - 40, floor.get_height()):
        for x in range(40, width - 40, floor.get_width()):
            terrain.blit(floor, (x, y))
    wall_tile = piece(walls, (48, 64, 16, 16))
    for x in range(40, width - 40, 32):
        terrain.blit(wall_tile, (x, 8))
        terrain.blit(wall_tile, (x, height - 32))
    for y in range(8, height, 32):
        terrain.blit(wall_tile, (8, y))
        terrain.blit(wall_tile, (width - 40, y))
    terrain.blit(piece(interior, (0, 272, 108, 98), scale=1, isolate=True), (460, 303))
    terrain.blit(piece(interior, (126, 288, 54, 82), scale=1), (805, 340))
    terrain.blit(piece(walls, (86, 66, 18, 24)), (650, 34))
    terrain.blit(piece(walls, (86, 66, 18, 24)), (365, 34))
    light = pygame.Surface(VIEW, pygame.SRCALPHA)
    for origin in (383, 668):
        for row in range(100):
            spread = row // 5
            pygame.draw.line(light, (247, 222, 167, round(20 * (1 - row / 100))),
                             (origin - 11 + row // 4 - spread, 72 + row),
                             (origin + 11 + row // 4 + spread, 72 + row))
    terrain.blit(light, (0, 0))
    wall = 40
    obstacles = [pygame.Rect(0, 0, width, wall),
                 pygame.Rect(0, height - wall, width, wall),
                 pygame.Rect(0, 0, wall, height),
                 pygame.Rect(width - wall, 0, wall, height)]
    objects = []

    def furniture(rect, pos, footprint=None):
        image = piece(interior, rect)
        objects.append((image, pos))
        if footprint is not None:
            obstacles.append(pygame.Rect(footprint).move(pos))

    furniture((48, 0, 32, 40), (480, 146), (10, 42, 44, 34))
    furniture((64, 80, 48, 64), (102, 46), (10, 98, 76, 20))
    furniture((160, 80, 32, 48), (892, 48), (10, 70, 45, 17))
    furniture((112, 80, 48, 48), (748, 48), (6, 76, 82, 15))
    furniture((120, 4, 20, 28), (554, 172), (6, 37, 24, 15))
    furniture((112, 176, 48, 32), (817, 382), (8, 34, 80, 18))
    furniture((0, 240, 16, 32), (826, 347), (3, 42, 22, 14))
    furniture((16, 240, 16, 32), (881, 435), (3, 42, 22, 14))
    furniture((48, 48, 32, 32), (104, 430), (5, 43, 49, 17))
    furniture((152, 0, 28, 32), (162, 429), (10, 42, 29, 17))
    furniture((36, 368, 24, 32), (88, 325), (8, 47, 26, 12))
    mirror_art = piece(walls, (86, 66, 18, 24))
    mirror_pixels = pygame.PixelArray(mirror_art)
    for source, target in {
        (86, 90, 101): (48, 70, 79), (79, 82, 93): (58, 83, 92),
        (99, 96, 159): (83, 111, 127), (123, 133, 195): (136, 169, 177),
        (138, 177, 219): (202, 217, 201), (100, 110, 121): (74, 101, 110),
        (108, 122, 134): (108, 147, 153),
    }.items():
        mirror_pixels.replace(source, target)
    del mirror_pixels
    mirror = Interactable(
        "mirror", "Protagonista", (252, 191), mirror_art,
        ["Esse sou eu?", "Não sinto que estou olhando para um estranho.",
         "Mas também não lembro desse rosto."], interaction_radius=70)
    sword = Interactable(
        "sword", "Protagonista", (757, 313), piece(interior, (148, 134, 34, 36)),
        ["Sei como segurar isso.", "Só não sei quem me ensinou."], interaction_radius=70)
    door = Interactable(
        "house_door", "Protagonista", (512, 500), piece(walls, (112, 96, 32, 32)),
        ["Talvez alguém aqui saiba alguma coisa."], prompt="[E] Sair",
        interaction_radius=82, transition_to="village")
    mirror.visual_depth, sword.visual_depth, door.visual_depth = 228, 337, 457
    door_frame = pygame.Surface((64, 88), pygame.SRCALPHA)
    door_frame.blit(door.image, (0, 24))
    door.image = door_frame
    obstacles.append(pygame.Rect(734, 331, 46, 24))
    lighting = pygame.Surface(VIEW, pygame.SRCALPHA)
    for inset in range(0, 64, 4):
        pygame.draw.rect(lighting, (16, 21, 30, round(34 * (1 - inset / 64))),
                         (inset, inset, width - inset * 2, height - inset * 2), 4)
    return {"name": "Casa", "terrain": terrain, "ambient_kind": "home",
            "houses": [], "objects": objects, "nature": [], "obstacles": obstacles,
            "exits": {}, "spawn": {"village": (512, 288)},
            "enemy_spawns": [], "npcs": [],
            "interactables": [mirror, sword, door], "water": [], "lighting": lighting}
