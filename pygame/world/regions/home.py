"""Quiet, furnished home. Atlas art and solid footprints are kept separate."""
import pygame

from core.assets import load
from core.config import VIEW
from entities.interactable import Interactable
from ui.text_rendering import draw_veiled_text


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
    floor = pygame.transform.scale_by(load("assets/prologue/wooden.png"), 2)
    terrain = pygame.Surface(VIEW)
    terrain.fill((30, 29, 33))
    room = pygame.Rect(288, 80, 480, 464)
    terrain.set_clip(room.inflate(-64, -64))
    for y in range(112, 512, floor.get_height()):
        for x in range(320, 736, floor.get_width()):
            terrain.blit(floor, (x, y))
    terrain.set_clip(None)
    wall_tile = piece(walls, (48, 64, 16, 16))
    for x in range(room.left, room.right, 32):
        terrain.blit(wall_tile, (x, room.top))
        terrain.blit(wall_tile, (x, 512))
    for y in range(room.top, 512, 32):
        terrain.blit(wall_tile, (room.left, y))
        terrain.blit(wall_tile, (736, y))
    terrain.blit(piece(interior, (0, 272, 108, 98), scale=1, isolate=True), (338, 248))
    terrain.blit(piece(walls, (86, 66, 18, 24)), (350, 92))
    terrain.blit(piece(walls, (86, 66, 18, 24)), (595, 92))
    light = pygame.Surface(VIEW, pygame.SRCALPHA)
    for origin in (368, 613):
        for row in range(100):
            spread = row // 5
            pygame.draw.line(light, (247, 222, 167, round(20 * (1 - row / 100))),
                             (origin - 11 + row // 4 - spread, 140 + row),
                             (origin + 11 + row // 4 + spread, 140 + row))
    terrain.blit(light, (0, 0))
    obstacles = [pygame.Rect(0, 0, width, 112),
                 pygame.Rect(0, 512, width, height - 512),
                 pygame.Rect(0, 0, 320, height),
                 pygame.Rect(736, 0, width - 736, height)]
    objects = []

    def furniture(rect, pos, footprint=None):
        image = piece(interior, rect)
        objects.append((image, pos))
        if footprint is not None:
            obstacles.append(pygame.Rect(footprint).move(pos))

    furniture((48, 0, 32, 40), (348, 136), (8, 8, 48, 68))
    furniture((160, 80, 32, 48), (650, 115), (10, 70, 45, 17))
    furniture((120, 4, 20, 28), (416, 158), (6, 37, 24, 15))
    furniture((112, 176, 48, 32), (570, 340), (8, 16, 80, 40))
    # These chair crops stop before the atlas's rug row below them.
    furniture((8, 216, 16, 24), (530, 344), (3, 34, 22, 14))
    furniture((36, 216, 16, 24), (678, 344), (3, 34, 22, 14))
    furniture((48, 48, 32, 32), (346, 414), (5, 43, 49, 17))
    furniture((152, 0, 28, 32), (410, 414), (10, 42, 29, 17))
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
        "mirror", "Protagonista", (306, 238), mirror_art,
        ["Esse sou eu?", "Não sinto que estou olhando para um estranho.",
         "Mas também não lembro desse rosto."], interaction_radius=70)
    sword = Interactable(
        "sword", "Protagonista", (708, 238),
        piece(interior, (104, 368, 28, 14), scale=2),
        ["Sei como segurar isso.", "Só não sei quem me ensinou."], interaction_radius=70)
    door = Interactable(
        "house_door", "Protagonista", (512, 500), piece(walls, (112, 96, 32, 32)),
        ["Talvez alguém aqui saiba alguma coisa."], prompt="[E] Sair",
        interaction_radius=82, transition_to="village")
    mirror.visual_depth, sword.visual_depth, door.visual_depth = 40, 40, 457
    door_frame = pygame.Surface((64, 88), pygame.SRCALPHA)
    door_frame.blit(door.image, (0, 24))
    door.image = door_frame

    def hotspot(uid, position, lines, radius=76):
        return Interactable(
            uid, "Protagonista", position, pygame.Surface((1, 1), pygame.SRCALPHA),
            lines, interaction_radius=radius)

    # Reuse atlas props; the pack has no standalone paper graphic.
    mug = piece(interior, (80, 372, 20, 24), scale=1)
    pendant = piece(interior, (176, 368, 16, 28), scale=1)
    mug = pygame.transform.scale(mug, (14, 17))
    pendant = pygame.transform.scale(pendant, (12, 21))

    wall_font = pygame.font.Font(None, 15)
    height_marks = pygame.Surface((173, 17), pygame.SRCALPHA)
    draw_veiled_text(height_marks, "|  |   | |  ***** — 8 anos", wall_font,
                     (205, 187, 151), (0, 0))
    # No standalone letter art exists in this pack; a small parchment prop fits the table.
    letter_image = pygame.Surface((34, 22), pygame.SRCALPHA)
    letter_image.fill((214, 196, 153))
    pygame.draw.rect(letter_image, (111, 82, 52), letter_image.get_rect(), 1)
    for row, width_px in ((5, 25), (9, 22), (13, 24), (17, 17)):
        pygame.draw.line(letter_image, (116, 88, 59), (4, row), (4 + width_px, row), 1)
    letter_image = pygame.transform.scale(letter_image, (24, 16))

    mug_point = Interactable("second_mug", "Protagonista", (591, 360), mug,
                             (), interaction_radius=38)
    mug_point.visual_depth = 395
    letter_point = Interactable(
        "damaged_letter", "Protagonista", (617, 358), letter_image,
        ("Se você conseguir chegar ao Vale, não deixe que eles...",
         "Chegar ao Vale...", "Então alguém sabia que eu viria para cá."),
        interaction_radius=38)
    letter_point.visual_depth = 396
    height_point = Interactable(
        "height_marks", "Protagonista", (505, 104), height_marks,
        ("Consigo ler tudo.", "...", "Menos isso."), interaction_radius=72)
    height_point.visual_depth = 112
    pendant_point = Interactable(
        "broken_pendant", "Protagonista", (645, 363), pendant,
        (), interaction_radius=74)
    pendant_point.visual_depth = 397
    investigation_interactables = [
        hotspot("two_chairs", (609, 372),
                ("Duas.", "...", "Eu costumava sentar aqui.", "...", "Como sei disso?"), 78),
        mug_point,
        height_point,
        letter_point,
        pendant_point,
    ]
    investigation_objects = []

    lighting = pygame.Surface(VIEW, pygame.SRCALPHA)
    for inset in range(0, 64, 4):
        pygame.draw.rect(lighting, (16, 21, 30, round(34 * (1 - inset / 64))),
                         (inset, inset, width - inset * 2, height - inset * 2), 4)
    return {"name": "Casa", "terrain": terrain, "ambient_kind": "home",
            "story_phase": "home_initial",
            "houses": [], "objects": objects, "nature": [], "obstacles": obstacles,
            "exits": {}, "spawn": {"village": (512, 288)},
            "enemy_spawns": [], "npcs": [],
            "interactables": [mirror, sword, door],
            "investigation_interactables": investigation_interactables,
            "investigation_objects": investigation_objects,
            "water": [], "lighting": lighting}
