"""Presentation-only rendering for timed narrative beats."""
import pygame


def draw_narrative(canvas, sequence, world_renderer=None):
    beat = sequence.current
    if beat is None:
        return
    if beat.background == "world" and world_renderer is not None:
        world_renderer()
    else:
        canvas.fill((0, 0, 0))

    if beat.text:
        font = pygame.font.Font(None, 38 if beat.background == "black" else 30)
        text = font.render(beat.text, True, (237, 232, 217))
        position = (canvas.get_width() // 2 - text.get_width() // 2,
                    round(canvas.get_height() * (0.5 if beat.background == "black" else 0.72)) - text.get_height() // 2)
        shadow = font.render(beat.text, True, (34, 31, 31))
        elapsed = beat.duration_ms - sequence.remaining_ms
        opacity = round(255 * min(1, elapsed / 220, sequence.remaining_ms / 160))
        text.set_alpha(opacity)
        shadow.set_alpha(opacity)
        canvas.blit(shadow, (position[0] + 2, position[1] + 3))
        canvas.blit(text, position)
    sequence.fade.draw(canvas)
