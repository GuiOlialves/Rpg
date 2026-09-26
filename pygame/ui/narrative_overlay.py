"""Presentation-only rendering for timed narrative beats."""
import pygame

from ui.text_rendering import draw_veiled_text, veiled_text_width


def _wrap(text, font, max_width):
    lines = []
    current = ""
    for word in str(text).split():
        candidate = f"{current} {word}".strip()
        if current and veiled_text_width(candidate, font) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def draw_narrative(canvas, sequence, world_renderer=None):
    beat = sequence.current
    if beat is None:
        return
    if beat.background == "world" and world_renderer is not None:
        world_renderer()
    else:
        canvas.fill((0, 0, 0))

    world_backdrop = beat.background == "world"
    if world_backdrop:
        bar_height = 27
        pygame.draw.rect(canvas, (10, 13, 17),
                         (0, 0, canvas.get_width(), bar_height))
        pygame.draw.rect(canvas, (10, 13, 17),
                         (0, canvas.get_height() - bar_height,
                          canvas.get_width(), bar_height))

    if beat.text:
        font = pygame.font.Font(None, 38 if not world_backdrop else 30)
        wrapped = _wrap(beat.text, font, canvas.get_width() - 112)
        line_height = font.get_height() + 3
        text_height = len(wrapped) * line_height - 3
        center_y = round(canvas.get_height() * (0.5 if not world_backdrop else 0.72))
        position = (canvas.get_width() // 2, center_y)
        elapsed = beat.duration_ms - sequence.remaining_ms
        opacity = round(255 * min(1, elapsed / 220,
                                  sequence.remaining_ms / 160))
        if world_backdrop:
            panel_width = min(canvas.get_width() - 64,
                              max(veiled_text_width(line, font)
                                  for line in wrapped) + 44)
            panel = pygame.Surface((panel_width, text_height + 22), pygame.SRCALPHA)
            panel.fill((8, 12, 15, round(166 * opacity / 255)))
            canvas.blit(panel, (canvas.get_width() // 2 - panel_width // 2,
                                center_y - text_height // 2 - 11))
        top = center_y - text_height // 2
        for index, line in enumerate(wrapped):
            line_width = veiled_text_width(line, font)
            x = canvas.get_width() // 2 - line_width // 2
            y = top + index * line_height
            line_layer = pygame.Surface((line_width + 3, font.get_height() + 4),
                                        pygame.SRCALPHA)
            draw_veiled_text(line_layer, line, font, (34, 31, 31), (2, 3))
            draw_veiled_text(line_layer, line, font, (237, 232, 217), (0, 0))
            line_layer.set_alpha(opacity)
            canvas.blit(line_layer, (x, y))
    sequence.fade.draw(canvas)
