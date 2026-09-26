import pygame
from ui.character_menu import wrap_text

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
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((4, 7, 10, 24)); surface.blit(shade, (0, 0))
        lines = self.npc.dialogue_for("default", self.manager)
        wrapped = wrap_text(lines[self.index], font, surface.get_width() - 216, max_lines=100)
        height = max(132, 92 + len(wrapped) * 23)
        box = pygame.Rect(80, surface.get_height() - height - 30, surface.get_width() - 160, height)
        pygame.draw.rect(surface, (10, 16, 21), box.move(0, 5), border_radius=4)
        pygame.draw.rect(surface, (24, 32, 38), box, border_radius=4)
        pygame.draw.rect(surface, (155, 132, 88), box, 2, border_radius=4)
        pygame.draw.line(surface, (56, 65, 65), (box.x + 28, box.y + 44), (box.right - 28, box.y + 44))
        speaker = getattr(self.npc, "speaker_for", lambda _index: self.npc.name)(self.index)
        surface.blit(title_font.render(speaker, True, (234, 207, 151)), (box.x + 28, box.y + 13))
        for row, line in enumerate(wrapped):
            surface.blit(font.render(line, True, (238, 239, 226)), (box.x + 28, box.y + 58 + row * 23))
        hint = "[E] continuar" if self.index + 1 < len(self.npc.dialogue_for("default", self.manager)) else "[E] fechar"
        hint_image = font.render(hint, True, (178, 190, 190))
        surface.blit(hint_image, (box.right - 28 - hint_image.width, box.bottom - 25))
