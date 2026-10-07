"""A short, readable wounded trail between the post and Edrin's encounter."""
import random
import pygame
import environment as env
from entities.edrin import Edrin
from entities.interactable import Interactable
from world.regions.old_road_art import prop

WORLD = (1280, 768)
TRAIL = [(0, 600), (170, 600), (340, 530), (510, 455), (690, 425), (860, 390), (1030, 380)]


def build(load, opened_chests=None):
    rng = random.Random(119)
    woods = env.free_woods(load)
    tile = load('sprites_meu/vila_tile-set/1 Tiles/FieldsTile_38.png')
    tufts = [env.tint(env.resize(load(f'sprites_meu/vila_tile-set/2 Objects/5 Grass/{i}.png'), 2),
                      (199, 190, 146)) for i in range(1, 7)]
    terrain = env.ground(WORLD, tile, 119, ((78, 87, 64), (135, 129, 88)), tufts)
    dirt = env.worn_texture(load('sprites_meu/vila_tile-set/1 Tiles/FieldsTile_11.png'),
                            (147, 126, 89), 28, 119)
    env.paths(terrain, [(TRAIL, 58)], dirt, 119,
              [((1000, 385), (245, 165))], tufts)
    scenery, obstacles = [], []

    def place(image, foot, box=None, canopy=False):
        scenery.append(env.anchored(image, foot, canopy))
        if box:
            obstacles.append(pygame.Rect(box).move(foot))
        env.shadow(terrain, foot, max(20, image.width // 2), 10, 32)

    # Visible banks and their matching perimeter keep the small area enclosed.
    for box in ((0, 0, 1280, 64), (0, 704, 1280, 64), (1216, 0, 64, 768),
                (0, 0, 32, 554), (0, 646, 32, 122)):
        rect = pygame.Rect(box)
        pygame.draw.rect(terrain, (88, 86, 65), rect)
        pygame.draw.rect(terrain, (123, 115, 83), rect, 8)
        obstacles.append(rect)
    rock = env.tint(env.resize(woods['rock'], 2), (209, 203, 172))
    for x in range(35, 1260, 52):
        for y in (rng.randint(32, 75), rng.randint(699, 751)):
            place(rock, (x, y))
    # The upper stand partly hides the distant patrol; the east stand hides
    # Edrin's separation without making him disappear in the open clearing.
    tree = env.resize(woods['tree'], 2)
    for foot in ((80, 220), (250, 340), (360, 250), (535, 275), (760, 220),
                 (910, 190), (1125, 290), (1175, 385), (1190, 520),
                 (220, 685), (510, 690), (740, 600), (960, 610)):
        place(tree, foot, (-17, -15, 34, 30), True)
    log = pygame.Surface((56, 15), pygame.SRCALPHA)
    pygame.draw.polygon(log, (46, 42, 35), [(1, 5), (48, 1), (55, 5), (55, 12), (5, 14), (0, 10)])
    pygame.draw.polygon(log, (99, 75, 48), [(3, 6), (48, 3), (52, 6), (50, 11), (5, 12)])
    for y in (7, 10): pygame.draw.line(log, (142, 113, 66), (6, y), (47, y-2))
    pygame.draw.ellipse(log, (160, 133, 85), (47, 3, 8, 10))
    pygame.draw.ellipse(log, (91, 70, 45), (49, 5, 4, 6), 1)
    place(pygame.transform.scale_by(log, 2), (1078, 460), (-54, -17, 108, 34))
    # Distinct fresh contacts, one dragging foot, broken twigs and blood.
    route = list(env.curve(TRAIL, 14))
    for index, (x, y) in enumerate(route[::2]):
        side = -8 if index % 2 else 8
        pygame.draw.ellipse(terrain, (68, 63, 47), (round(x), round(y + side), 5, 9))
        if index % 3 == 0:
            pygame.draw.line(terrain, (78, 70, 51), (x - 11, y + 11), (x + 5, y + 8), 2)
        if index % 5 == 3:
            env.patch(terrain, (x + 9, y + 6), (12, 6), (136, 46, 38, 180), index)
    for x, y in ((305, 551), (590, 443), (842, 402)):
        pygame.draw.lines(terrain, (80, 62, 42), False, [(x - 14, y + 3), (x, y), (x + 12, y - 8)], 3)
        pygame.draw.line(terrain, (167, 141, 92), (x - 2, y - 1), (x + 3, y + 2), 2)
    clues = [
        Interactable('pursuit_tracks', 'Protagonista', (315, 544), pygame.Surface((1, 1), pygame.SRCALPHA),
                     ('Uma passada funda, outra arrastada. O sangue ainda não secou.',
                      'Quem saiu do posto está ferido. Não pode estar longe.'),
                     prompt='[E] Examinar rastro'),
        Interactable('pursuit_bandage', 'Protagonista', (647, 454), prop('red_cloth'),
                     ('Uma tira de uniforme usada como curativo. O tecido rasgou há pouco.',),
                     prompt='[E] Examinar tecido'),
    ]
    edrin = Edrin((1020, 386), load)
    return {'name': 'Trilha do Posto', 'ambient_kind': 'pursuit', 'terrain': terrain,
            'houses': [], 'objects': [], 'nature': [], 'scenery': scenery,
            'npcs': [edrin], 'edrin': edrin, 'interactables': clues, 'obstacles': obstacles,
            'enemy_spawns': [], 'exits': {'watchpost': pygame.Rect(0, 555, 32, 90)},
            'spawn': {'watchpost': (110, 600)},
            'edrin_trigger': pygame.Rect(882, 320, 230, 152)}
