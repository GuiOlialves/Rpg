"""Floating damage feedback used by combat rendering."""
import pygame

class DamageNumber:
    def __init__(self, text, x, y, color, critical=False):
        self.text, self.x, self.y = text, x, y
        self.color, self.critical = color, critical
        self.ticks = 42

    def update(self):
        self.y -= 0.65
        self.ticks -= 1
        return self.ticks > 0

    def draw(self, canvas, camera, font, title_font):
        label = (title_font if self.critical else font).render(self.text, True, self.color)
        label.set_alpha(min(255, self.ticks * 12))
        canvas.blit(label, (round(self.x - camera[0] - label.get_width() / 2),
                            round(self.y - camera[1])))
