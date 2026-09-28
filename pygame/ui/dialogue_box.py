import pygame
from ui.hud import draw_key_prompt, draw_panel
from ui.narrative_overlay import _wrap
from ui.text_rendering import draw_veiled_text

class DialogueBox:
    def __init__(self):
        self.npc = None
        self.manager = None
        self.index = 0

    @property
    def active(self):
        return self.npc is not None

    def open(self, npc, manager=None):
        self.npc, self.index, self.manager = npc, 0, manager

    def advance(self):
        if not self.active:
            return None
        lines = self.npc.dialogue_for("default", self.manager)
        if self.index + 1 < len(lines):
            self.index += 1
            return None
        else:
            closed_npc = self.npc
            self.npc = None
            return closed_npc

    def draw(self, surface, font, title_font):
        if not self.active:
            return
        if not hasattr(self, "shade") or self.shade.get_size() != surface.get_size():
            self.shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            self.shade.fill((4, 7, 10, 32))
            self.speaker_font = pygame.font.Font(None, 24)
            self.hint_font = pygame.font.Font(None, 30)
        surface.blit(self.shade, (0, 0))
        lines = self.npc.dialogue_for("default", self.manager)
        width = min(800, surface.get_width() - 96)
        wrapped = _wrap(lines[self.index], font, width - 48)
        row_height = max(23, font.get_height() + 3)
        height = 76 + len(wrapped) * row_height
        box = pygame.Rect((surface.get_width() - width) // 2,
                          surface.get_height() - height - 32, width, height)
        draw_panel(surface, box, fill=(20, 28, 34), border=(155, 127, 83),
                   radius=7, shadow=True)
        pygame.draw.line(surface, (67, 81, 84),
                         (box.x + 22, box.y + 36),
                         (box.right - 22, box.y + 36), 1)
        speaker = getattr(self.npc, "speaker_for", lambda _index: self.npc.name)(self.index)
        speaker_image = self.speaker_font.render(speaker.upper(), True, (240, 209, 151))
        surface.blit(speaker_image, (box.x + 24, box.y + 13))
        for row, line in enumerate(wrapped):
            draw_veiled_text(surface, line, font, (239, 238, 225),
                             (box.x + 24, box.y + 46 + row * row_height))
        continuing = self.index + 1 < len(lines) or getattr(self.npc, "scripted", False)
        hint = "[E] continuar" if continuing else "[E] fechar"
        draw_key_prompt(surface, hint, self.hint_font, box.right - 75, box.bottom - 28)
