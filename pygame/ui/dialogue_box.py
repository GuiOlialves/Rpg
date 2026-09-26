import pygame
from ui.character_menu import wrap_text
from ui.hud import draw_key_prompt, draw_panel
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
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((4, 7, 10, 68))
        surface.blit(shade, (0, 0))
        lines = self.npc.dialogue_for("default", self.manager)
        wrapped = wrap_text(lines[self.index], font, surface.get_width() - 192,
                            max_lines=4)
        row_height = max(23, font.get_height() + 3)
        height = 103 + len(wrapped) * row_height
        box = pygame.Rect(64, surface.get_height() - height - 24,
                          surface.get_width() - 128, height)
        draw_panel(surface, box, fill=(20, 28, 34), border=(155, 127, 83),
                   radius=7, shadow=True)
        pygame.draw.line(surface, (67, 81, 84),
                         (box.x + 22, box.y + 43),
                         (box.right - 22, box.y + 43), 1)
        speaker = getattr(self.npc, "speaker_for", lambda _index: self.npc.name)(self.index)
        speaker_font = pygame.font.Font(None, max(22, title_font.get_height() - 2))
        speaker_image = speaker_font.render(speaker.upper(), True, (240, 209, 151))
        nameplate = pygame.Rect(box.x + 20, box.y + 9,
                                speaker_image.get_width() + 20, 27)
        pygame.draw.rect(surface, (39, 49, 53), nameplate, border_radius=4)
        pygame.draw.rect(surface, (100, 87, 62), nameplate, 1, border_radius=4)
        surface.blit(speaker_image,
                     (nameplate.x + 10,
                      nameplate.centery - speaker_image.get_height() // 2))
        for row, line in enumerate(wrapped):
            draw_veiled_text(surface, line, font, (239, 238, 225),
                             (box.x + 25, box.y + 56 + row * row_height))
        hint = "[E] continuar" if self.index + 1 < len(self.npc.dialogue_for("default", self.manager)) else "[E] fechar"
        draw_key_prompt(surface, hint, font, box.right - 100, box.bottom - 43)
