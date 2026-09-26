"""HUD e componentes visuais reutilizáveis."""
import pygame
from core.config import VIEW
from entities.player import frame

def draw_panel(surface, rect, fill=(35, 43, 50), border=(187, 145, 75), radius=10):
    shadow = rect.move(5, 6)
    pygame.draw.rect(surface, (8, 12, 15, 150), shadow, border_radius=radius)
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, 3, border_radius=radius)
    pygame.draw.line(surface, (82, 92, 96), (rect.x + 12, rect.y + 7), (rect.right - 12, rect.y + 7), 1)

def draw_bar(surface, rect, value, maximum, fill, label, font, icon=None):
    pygame.draw.rect(surface, (17, 22, 27), rect, border_radius=6)
    pygame.draw.rect(surface, (92, 99, 101), rect, 2, border_radius=6)
    inner = rect.inflate(-6, -6)
    pygame.draw.rect(surface, (48, 55, 60), inner, border_radius=3)
    amount = max(0, min(1, value / maximum))
    width = round(inner.width * amount)
    if width:
        filled = pygame.Rect(inner.x, inner.y, width, inner.height)
        pygame.draw.rect(surface, fill, filled, border_radius=3)
        pygame.draw.line(surface, tuple(min(255, c + 45) for c in fill), (filled.x + 3, filled.y + 2), (filled.right - 3, filled.y + 2), 2)
    for marker in range(1, 5):
        x = inner.x + inner.width * marker // 5
        pygame.draw.line(surface, (30, 35, 39), (x, inner.y + 2), (x, inner.bottom - 2), 1)
    prefix = f"{icon}  " if icon else ""
    text = font.render(f"{prefix}{label}", True, (250, 244, 225))
    number = font.render(f"{value} / {maximum}", True, "white")
    surface.blit(text, (rect.x + 9, rect.y + 5))
    surface.blit(number, (rect.right - number.get_width() - 9, rect.y + 5))

def draw_hud(canvas, player, font):
    panel = pygame.Surface((330, 104), pygame.SRCALPHA)
    draw_panel(panel, pygame.Rect(1, 1, 323, 96), fill=(25, 32, 38, 230), radius=10)
    pygame.draw.circle(panel, (176, 137, 72), (52, 49), 37)
    pygame.draw.circle(panel, (43, 61, 52), (52, 49), 33)
    portrait = pygame.transform.scale(frame(player.idle, 0, player.facing), (72, 72))
    panel.blit(portrait, (16, 13))
    panel.blit(font.render("AVENTUREIRO", True, (248, 224, 165)), (94, 9))
    panel.blit(font.render(f"Nv. {player.level}", True, (177, 187, 189)), (267, 9))
    draw_bar(panel, pygame.Rect(91, 32, 220, 25), player.hp, player.max_hp, (185, 51, 62), "HP", font)
    draw_bar(panel, pygame.Rect(91, 63, 220, 25), player.sp, player.max_sp, (54, 112, 196), "SP", font)
    if player.dash_feedback_timer > 0:
        color = (245, 102, 82) if player.dash_feedback_kind == "sp" else (241, 190, 91)
        pygame.draw.rect(panel, color, pygame.Rect(89, 61, 224, 29), 2, border_radius=8)
    canvas.blit(panel, (16, VIEW[1] - 120))
    xp_rect = pygame.Rect(107, VIEW[1] - 14, 220, 8)
    pygame.draw.rect(canvas, (18, 23, 27), xp_rect, border_radius=3)
    pygame.draw.rect(canvas, (191, 151, 67), (xp_rect.x, xp_rect.y, round(xp_rect.width * player.current_xp / player.xp_to_next_level), xp_rect.height), border_radius=3)
