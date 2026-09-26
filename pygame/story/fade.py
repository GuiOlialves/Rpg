"""Fade-to/from-black overlay shared by short narrative sequences."""
import pygame


class FadeOverlay:
    def __init__(self):
        self.alpha = 0
        self.start_alpha = 0
        self.target_alpha = 0
        self.duration_ms = 0
        self.elapsed_ms = 0
        self.active = False

    def start(self, direction, duration_ms=900):
        if direction not in {"in", "out"}:
            raise ValueError("O fade deve ser 'in' ou 'out'.")
        self.start_alpha, self.target_alpha = ((255, 0) if direction == "in" else (0, 255))
        self.alpha = self.start_alpha
        self.duration_ms = max(1, int(duration_ms))
        self.elapsed_ms = 0
        self.active = True

    def update(self, delta_ms):
        if not self.active:
            return
        self.elapsed_ms = min(self.duration_ms, self.elapsed_ms + max(0, int(delta_ms)))
        progress = self.elapsed_ms / self.duration_ms
        self.alpha = round(self.start_alpha + (self.target_alpha - self.start_alpha) * progress)
        if self.elapsed_ms >= self.duration_ms:
            self.alpha = self.target_alpha
            self.active = False

    def draw(self, canvas):
        if self.alpha <= 0:
            return
        overlay = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.alpha))
        canvas.blit(overlay, (0, 0))
