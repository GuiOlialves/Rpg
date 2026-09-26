"""Shared visual language for HUD panels, meters and contextual information."""
from functools import lru_cache

import pygame

from core.config import VIEW
from entities.player import frame


PANEL = (27, 36, 42)
EDGE = (144, 116, 73)
EDGE_LIGHT = (205, 174, 112)
TEXT = (239, 237, 222)
MUTED = (167, 180, 180)
ACCENT = (239, 205, 139)


@lru_cache(maxsize=64)
def _panel_shadow(size, radius):
    shade = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(shade, (2, 6, 9, 165), shade.get_rect(),
                     border_radius=radius)
    return shade


def draw_panel(surface, rect, fill=PANEL, border=EDGE, radius=7, shadow=True):
    """Draw a crisp, shared pixel-friendly panel with a restrained frame."""
    rect = pygame.Rect(rect)
    if shadow:
        surface.blit(_panel_shadow(rect.size, radius), rect.move(4, 5))
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, 2, border_radius=radius)
    inner = rect.inflate(-5, -5)
    if inner.width > 3 and inner.height > 3:
        pygame.draw.rect(surface, (63, 76, 81), inner, 1,
                         border_radius=max(2, radius - 2))
    if rect.width > 24:
        pygame.draw.line(surface, (91, 101, 99),
                         (rect.x + radius + 4, rect.y + 4),
                         (rect.right - radius - 4, rect.y + 4), 1)


def draw_bar(surface, rect, value, maximum, fill, label, font, icon=None):
    """Draw an inset meter with compact labels that remain legible over fills."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, (12, 18, 22), rect, border_radius=4)
    pygame.draw.rect(surface, (86, 101, 105), rect, 1, border_radius=4)
    inner = rect.inflate(-4, -4)
    pygame.draw.rect(surface, (42, 51, 55), inner, border_radius=2)
    ratio = max(0.0, min(1.0, value / maximum if maximum else 0.0))
    fill_width = round(inner.width * ratio)
    if fill_width:
        filled = pygame.Rect(inner.x, inner.y, fill_width, inner.height)
        pygame.draw.rect(surface, fill, filled, border_radius=2)
        if fill_width > 8 and inner.height > 5:
            highlight = tuple(min(255, channel + 34) for channel in fill)
            pygame.draw.line(surface, highlight,
                             (filled.x + 2, filled.y + 1),
                             (max(filled.x + 2, filled.right - 2), filled.y + 1), 1)
    if inner.width > 100:
        for marker in range(1, 5):
            x = inner.x + inner.width * marker // 5
            pygame.draw.line(surface, (31, 39, 42),
                             (x, inner.y + 2), (x, inner.bottom - 2), 1)
    compact = pygame.font.Font(None, max(14, min(18, rect.height - 4)))
    prefix = f"{icon}  " if icon else ""
    label_image = compact.render(f"{prefix}{label}", True, TEXT)
    value_image = compact.render(f"{value}/{maximum}", True, TEXT)
    label_y = rect.centery - label_image.get_height() // 2
    value_y = rect.centery - value_image.get_height() // 2
    surface.blit(label_image, (rect.x + 7, label_y))
    surface.blit(value_image, (rect.right - value_image.get_width() - 7, value_y))


def portrait_image(sheet, direction, size):
    """Scale only the visible sprite pixels, preserving crisp pixel edges."""
    pose = frame(sheet, 0, direction)
    bounds = pose.get_bounding_rect(min_alpha=8)
    if bounds.width == 0 or bounds.height == 0:
        return pygame.transform.scale(pose, size)
    sprite = pose.subsurface(bounds)
    pad = max(2, min(size) // 10)
    available = (max(1, size[0] - pad * 2), max(1, size[1] - pad * 2))
    scale = min(available[0] / sprite.get_width(),
                available[1] / sprite.get_height())
    scaled_size = (max(1, round(sprite.get_width() * scale)),
                   max(1, round(sprite.get_height() * scale)))
    result = pygame.Surface(size, pygame.SRCALPHA)
    scaled = pygame.transform.scale(sprite, scaled_size)
    result.blit(scaled, (size[0] // 2 - scaled_size[0] // 2,
                         size[1] // 2 - scaled_size[1] // 2))
    return result


def _wrap_words(text, font, width, max_lines=2):
    lines = []
    current = ""
    for word in str(text).split():
        candidate = f"{current} {word}".strip()
        if current and font.size(candidate)[0] > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and font.size(last + "…")[0] > width:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    return lines


def draw_objective_tracker(surface, text, font):
    """Present the current objective as a compact, labeled HUD card."""
    small = pygame.font.Font(None, 17)
    body = pygame.font.Font(None, max(18, font.get_height() - 2))
    max_width = min(340, surface.get_width() - 42)
    lines = _wrap_words(text, body, max_width - 28, 2)
    panel_width = max(228, max(body.size(line)[0] for line in lines) + 28)
    panel_height = 39 + len(lines) * (body.get_height() + 1)
    panel = pygame.Rect(surface.get_width() - panel_width - 16, 52,
                        panel_width, panel_height)
    draw_panel(surface, panel, fill=(25, 34, 40), radius=6, shadow=True)
    title = small.render("OBJETIVO ATUAL", True, ACCENT)
    surface.blit(title, (panel.x + 12, panel.y + 7))
    for index, line in enumerate(lines):
        text_image = body.render(line, True, TEXT)
        surface.blit(text_image, (panel.x + 12,
                                  panel.y + 23 + index * (body.get_height() + 1)))
    return panel


def draw_notice(surface, text, font):
    """Show quest/save notices as a short-lived toast, separate from the objective."""
    small = pygame.font.Font(None, max(16, font.get_height() - 2))
    width = min(440, surface.get_width() - 32)
    lines = _wrap_words(text, small, width - 24, 2)
    panel = pygame.Rect(16, 54, width,
                        18 + len(lines) * (small.get_height() + 2))
    draw_panel(surface, panel, fill=(30, 39, 42), radius=6, shadow=True)
    pygame.draw.rect(surface, EDGE_LIGHT,
                     pygame.Rect(panel.x + 1, panel.y + 8, 3, panel.height - 16))
    for index, line in enumerate(lines):
        image = small.render(line, True, TEXT)
        surface.blit(image, (panel.x + 13,
                             panel.y + 8 + index * (small.get_height() + 2)))
    return panel


def draw_key_prompt(surface, text, font, center, top):
    """Render interaction prompts with a warm keycap and a quiet backing."""
    small = pygame.font.Font(None, max(14, font.get_height() - 1))
    key = None
    action = str(text)
    if len(action) >= 4 and action.startswith("[") and action[2] == "]":
        key, action = action[1:2], action[4:].strip()
    padding = max(5, small.get_height() // 3)
    key_image = small.render(key, True, (31, 30, 26)) if key else None
    action_image = small.render(action, True, TEXT)
    key_width = max(0, key_image.get_width() + 8) if key_image else 0
    gap = 6 if key_image else 0
    height = max(small.get_height(), key_image.get_height() if key_image else 0) + padding * 2
    width = padding * 2 + key_width + gap + action_image.get_width()
    rect = pygame.Rect(round(center - width / 2), round(top), width, height)
    rect.x = max(8, min(surface.get_width() - rect.width - 8, rect.x))
    rect.y = max(8, min(surface.get_height() - rect.height - 8, rect.y))
    draw_panel(surface, rect, fill=(21, 29, 34), radius=5, shadow=True)
    cursor_x = rect.x + padding
    if key_image:
        cap = pygame.Rect(cursor_x, rect.centery - (key_image.get_height() + 4) // 2,
                          key_width, key_image.get_height() + 4)
        pygame.draw.rect(surface, EDGE_LIGHT, cap, border_radius=3)
        surface.blit(key_image, (cap.centerx - key_image.get_width() // 2,
                                 cap.centery - key_image.get_height() // 2))
        cursor_x = cap.right + gap
    surface.blit(action_image,
                 (cursor_x, rect.centery - action_image.get_height() // 2))
    return rect


def draw_hud(canvas, player, font):
    panel = pygame.Surface((356, 128), pygame.SRCALPHA)
    draw_panel(panel, pygame.Rect(1, 1, 348, 120), fill=(24, 33, 39), radius=8,
               shadow=False)
    pygame.draw.circle(panel, EDGE, (51, 56), 40)
    pygame.draw.circle(panel, (48, 70, 59), (51, 56), 36)
    portrait = portrait_image(player.idle, player.facing, (64, 64))
    mask = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (32, 32), 31)
    portrait.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    panel.blit(portrait, (19, 24))
    pygame.draw.circle(panel, EDGE_LIGHT, (51, 56), 40, 1)
    pygame.draw.line(panel, (65, 79, 81), (100, 12), (100, 108), 1)

    name_font = pygame.font.Font(None, 20)
    level_font = pygame.font.Font(None, 16)
    panel.blit(name_font.render("AVENTUREIRO", True, ACCENT), (112, 10))
    level_badge = pygame.Rect(287, 8, 49, 22)
    pygame.draw.rect(panel, (45, 55, 58), level_badge, border_radius=4)
    pygame.draw.rect(panel, (91, 105, 103), level_badge, 1, border_radius=4)
    level = level_font.render(f"NV. {player.level}", True, TEXT)
    panel.blit(level, (level_badge.centerx - level.get_width() // 2,
                       level_badge.centery - level.get_height() // 2))

    draw_bar(panel, pygame.Rect(108, 37, 229, 24), player.hp, player.max_hp,
             (186, 57, 67), "HP", font)
    draw_bar(panel, pygame.Rect(108, 66, 229, 24), player.sp, player.max_sp,
             (61, 123, 191), "SP", font)
    if player.dash_feedback_timer > 0:
        color = (238, 104, 83) if player.dash_feedback_kind == "sp" else (234, 186, 91)
        pygame.draw.rect(panel, color, pygame.Rect(106, 64, 233, 28), 1,
                         border_radius=5)

    xp_label = level_font.render("XP", True, MUTED)
    panel.blit(xp_label, (108, 101))
    xp_rect = pygame.Rect(134, 104, 143, 10)
    pygame.draw.rect(panel, (12, 18, 22), xp_rect, border_radius=3)
    pygame.draw.rect(panel, (83, 94, 94), xp_rect, 1, border_radius=3)
    xp_ratio = max(0.0, min(1.0, player.current_xp / player.xp_to_next_level
                           if player.xp_to_next_level else 0.0))
    xp_width = round((xp_rect.width - 2) * xp_ratio)
    if xp_width:
        pygame.draw.rect(panel, (197, 157, 71),
                         (xp_rect.x + 1, xp_rect.y + 1, xp_width, xp_rect.height - 2),
                         border_radius=2)
    xp_text = level_font.render(f"{player.current_xp}/{player.xp_to_next_level}",
                                True, TEXT)
    panel.blit(xp_text, (337 - xp_text.get_width(), 101))
    canvas.blit(panel, (16, VIEW[1] - 136))
