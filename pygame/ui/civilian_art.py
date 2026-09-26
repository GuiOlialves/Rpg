"""Small reversible palette variants of the supplied civilian sheets."""
import pygame


def civilian_sheet(load, look):
    base = "customer" if look in {"resident", "elder"} else "seller"
    sheet = load(f"assets/npc/civilian_{base}.png").copy()
    palettes = {
        "elder": {
            (175, 63, 39): (132, 134, 126), (160, 49, 38): (109, 115, 109),
            (194, 78, 41): (153, 155, 143), (132, 38, 38): (80, 91, 87),
            (209, 94, 37): (178, 177, 158), (225, 116, 33): (207, 201, 175),
            (85, 47, 44): (56, 72, 57), (99, 59, 57): (74, 93, 69),
        },
        "worker": {
            (69, 49, 98): (67, 55, 45), (101, 59, 130): (116, 88, 59),
            (90, 55, 118): (95, 74, 52), (146, 70, 167): (160, 119, 70),
            (127, 68, 155): (139, 105, 66), (55, 45, 81): (48, 44, 38),
            (84, 25, 31): (31, 57, 61), (96, 26, 29): (38, 73, 77),
            (114, 30, 28): (47, 87, 90),
        },
    }
    with pygame.PixelArray(sheet) as pixels:
        for source, target in palettes.get(look, {}).items():
            pixels.replace(source, target)
    return sheet
