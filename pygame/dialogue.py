import pygame

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
            return
        lines = self.npc.dialogue_for("default", self.manager)
        if self.index + 1 < len(lines):
            self.index += 1
        else:
            if self.manager and getattr(self.npc, "quest_id", None):
                q = self.manager.get(self.npc.quest_id)
                if q.state == "AVAILABLE": self.manager.accept(q.id)
                elif q.state == "COMPLETED": self.manager.claim(q.id, self.inventory)
            self.npc = None

    def draw(self, surface, font, title_font):
        if not self.active:
            return
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((4, 7, 10, 55)); surface.blit(shade, (0, 0))
        box = pygame.Rect(42, surface.get_height() - 158, surface.get_width() - 84, 126)
        pygame.draw.rect(surface, (22, 29, 35), box, border_radius=12)
        pygame.draw.rect(surface, (190, 151, 79), box, 3, border_radius=12)
        surface.blit(title_font.render(self.npc.name, True, (248, 224, 165)), (box.x + 20, box.y + 13))
        line = self.npc.dialogue_for("default", self.manager)[self.index]
        surface.blit(font.render(line, True, (238, 239, 226)), (box.x + 20, box.y + 52))
        hint = "[E] continuar" if self.index + 1 < len(self.npc.dialogue_for("default")) else "[E] fechar"
        surface.blit(font.render(hint, True, (178, 190, 190)), (box.right - 130, box.bottom - 28))
