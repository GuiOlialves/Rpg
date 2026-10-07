"""A named survivor with his own atlas, reactions and wounded walk."""
import pygame
from ui.character_art import prepared_frames


class Edrin:
    uid = 'edrin'
    name = 'Edrin'
    enabled = False  # The encounter owns dialogue and movement.
    has_embedded_shadow = False

    def __init__(self, position, load):
        self.x, self.y = map(float, position)
        self.frames = {mode: prepared_frames(load(f'assets/vale_characters/edrin_{mode}.png'),
                                             64, 32, 36)
                       for mode in ('idle', 'guard', 'alert', 'recoil', 'walk')}
        self.mode, self.facing, self.elapsed_ms = 'idle', 1, 0
        self.visible = True

    def available(self, context=None):
        return False

    @property
    def interaction_rect(self):
        return pygame.Rect(round(self.x - 20), round(self.y - 12), 40, 24)

    def update(self, delta_ms):
        self.elapsed_ms += delta_ms

    def draw(self, canvas, camera):
        if not self.visible:
            return
        row = self.frames[self.mode][self.facing]
        interval = 160 if self.mode == 'recoil' else 145 if self.mode == 'walk' else 320
        frame = row[int(self.elapsed_ms // interval) % len(row)]
        canvas.blit(frame, (round(self.x - 32 - camera[0]), round(self.y - 68 - camera[1])))
