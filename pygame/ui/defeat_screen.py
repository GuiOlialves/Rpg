"""Transição e interface da tela de derrota."""
import pygame


FADE_FRAMES = 36
OPTIONS = (
    ("Continuar", "continue"),
    ("Carregar último save", "load"),
    ("Sair", "quit"),
)


class GameOverScreen:
    def __init__(self):
        self.timer = 0
        self.selected = 0
        self.notice = ""

    @property
    def ready(self):
        return self.timer >= FADE_FRAMES

    def update(self):
        self.timer = min(FADE_FRAMES, self.timer + 1)

    def button_rects(self, size):
        width, height = size
        button_w, button_h, gap = 340, 46, 12
        top = height // 2 - 48
        left = (width - button_w) // 2
        return [pygame.Rect(left, top + i * (button_h + gap), button_w, button_h)
                for i in range(len(OPTIONS))]

    def handle_event(self, event, mouse_position, size):
        if not self.ready:
            return None
        if event.type == pygame.MOUSEMOTION:
            for index, rect in enumerate(self.button_rects(size)):
                if rect.collidepoint(mouse_position):
                    self.selected = index
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.button_rects(size)):
                if rect.collidepoint(mouse_position):
                    self.selected = index
                    return OPTIONS[index][1]
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % len(OPTIONS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(OPTIONS)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            return OPTIONS[self.selected][1]
        elif event.key == pygame.K_ESCAPE:
            return "quit"
        elif event.key == pygame.K_F9:
            return "load"
        return None

    def draw(self, canvas, font, title_font, mouse_position=(0, 0)):
        width, height = canvas.get_size()
        alpha = round(215 * min(1.0, self.timer / FADE_FRAMES))
        shade = pygame.Surface((width, height), pygame.SRCALPHA)
        shade.fill((7, 10, 16, alpha))
        canvas.blit(shade, (0, 0))
        if not self.ready:
            return

        panel = pygame.Rect(width // 2 - 245, height // 2 - 185, 490, 370)
        pygame.draw.rect(canvas, (7, 10, 16, 110), panel.move(7, 8), border_radius=18)
        pygame.draw.rect(canvas, (31, 39, 47), panel, border_radius=16)
        pygame.draw.rect(canvas, (180, 137, 82), panel, 3, border_radius=16)
        title = title_font.render("Você caiu...", True, (245, 220, 181))
        canvas.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 28))
        subtitle = font.render("Escolha como deseja continuar", True, (188, 198, 198))
        canvas.blit(subtitle, (panel.centerx - subtitle.get_width() // 2, panel.y + 76))

        for index, ((label, _), rect) in enumerate(zip(OPTIONS, self.button_rects((width, height)))):
            hovered = rect.collidepoint(mouse_position)
            active = index == self.selected or hovered
            fill = (113, 80, 47) if active else (47, 57, 64)
            border = (242, 203, 131) if active else (93, 106, 110)
            pygame.draw.rect(canvas, fill, rect, border_radius=8)
            pygame.draw.rect(canvas, border, rect, 2, border_radius=8)
            text = font.render(label, True, (255, 247, 226) if active else (209, 215, 212))
            canvas.blit(text, (rect.centerx - text.get_width() // 2,
                               rect.centery - text.get_height() // 2))

        if self.notice:
            notice = font.render(self.notice, True, (246, 151, 137))
            canvas.blit(notice, (panel.centerx - notice.get_width() // 2, panel.bottom - 40))
        else:
            hint = font.render("↑/↓ selecionar  •  Enter confirmar  •  Esc sair", True, (154, 168, 169))
            canvas.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 31))
