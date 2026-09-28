"""Small text helpers for narrative glyphs unsupported by the bundled font."""
import re

import pygame


_VEIL = re.compile(r"(█+|\*{5})")


def veiled_text_width(text, font):
    block_width = max(1, font.size("M")[0])
    return sum((len(part) * block_width if part.startswith("█")
                else font.size(part)[0]) for part in _VEIL.split(str(text)))


def draw_veiled_text(surface, text, font, color, position):
    """Draw ordinary copy normally and full-block censorship as crisp glyphs."""
    x, y = round(position[0]), round(position[1])
    block_width = max(1, font.size("M")[0])
    block_height = max(4, round(font.get_height() * 0.58))
    block_y = y + round((font.get_height() - block_height) / 2)
    for part in _VEIL.split(str(text)):
        if not part:
            continue
        if part.startswith("█"):
            width = block_width * len(part)
            pygame.draw.rect(surface, color,
                             (x, block_y, width, block_height))
            x += width
        else:
            image = font.render(part, True, color)
            surface.blit(image, (x, y))
            if part == "*****":
                # The same absence motif, while retaining the approved stars.
                pygame.draw.line(surface, color, (x, block_y + block_height),
                                 (x + image.get_width() - 1, block_y + block_height))
            x += image.get_width()


def draw_veil_pulse(canvas, elapsed_ms):
    """One soft 150 ms pulse shared by every obscured-name beat."""
    if 0 <= elapsed_ms < 150:
        veil = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
        veil.fill((217, 207, 231, round(26 * (1 - elapsed_ms / 150))))
        canvas.blit(veil, (0, 0))
