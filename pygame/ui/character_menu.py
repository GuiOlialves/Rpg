"""Renderização e geometria do menu de personagem."""
import pygame
from core.config import VIEW
from entities.player import frame
from systems import progression as attributes
from systems.equipment import SLOTS
from ui.hud import draw_bar, draw_panel

def fit_text(text, font, max_width):
    text = str(text)
    if font.size(text)[0] <= max_width: return text
    while text and font.size(text + "...")[0] > max_width: text = text[:-1]
    return text + "..."

def wrap_text(text, font, max_width, max_lines=3):
    words, lines, current = str(text).split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and font.size(candidate)[0] > max_width:
            lines.append(current); current = word
        else: current = candidate
    if current: lines.append(current)
    return [fit_text(line, font, max_width) for line in lines[:max_lines]]

def character_attribute_layout():
    stats = (("Vitalidade", "vitalidade", (198, 85, 85)),
             ("Força", "força", (214, 143, 69)),
             ("Magia", "magia", (111, 128, 220)),
             ("Agilidade", "agilidade", (84, 177, 113)))
    return [(label, key, color, pygame.Rect(355, 205 + index * 30, 577, 27),
             pygame.Rect(895, 207 + index * 30, 32, 23))
            for index, (label, key, color) in enumerate(stats)]


def attribute_key_at(position):
    """Return the stat represented by a clicked plus button, if any."""
    for _, key, _, _, plus in character_attribute_layout():
        if plus.collidepoint(position):
            return key
    return None

def attribute_preview_lines(player, key):
    next_stats = player.preview_stat(key)
    if next_stats is None:
        return ["Sem pontos disponíveis."]
    now = player.derived
    if key == "vitalidade":
        return [f"HP máx.: {now['max_hp']} → {next_stats['max_hp']}",
                f"Defesa: {now['defense']:.1f} → {next_stats['defense']:.1f}"]
    if key == "força":
        return [f"Ataque: {now['physical_attack']} → {next_stats['physical_attack']}",
                f"Empurrão: {now['knockback_power']:.2f}x → {next_stats['knockback_power']:.2f}x"]
    if key == "magia":
        return [f"SP máx.: {now['max_sp']} → {next_stats['max_sp']}",
                f"Poder mágico: {now['magic_power']} → {next_stats['magic_power']}"]
    cadence = (f"Cadência: {now['attack_cooldown']} → {next_stats['attack_cooldown']} frames"
               if now["attack_cooldown"] != next_stats["attack_cooldown"] else
               f"Cadência: {now['attack_cooldown']} frames (sem mudança)")
    return [f"Movimento: {now['move_speed']/attributes.BASE_MOVE_SPEED:.1%} → {next_stats['move_speed']/attributes.BASE_MOVE_SPEED:.1%}",
            cadence, f"Crítico: {now['crit_chance']:.1%} → {next_stats['crit_chance']:.1%}"]

def draw_character_menu(canvas, player, font, title_font, mouse_pos=(-1, -1)):
    shade = pygame.Surface(VIEW, pygame.SRCALPHA); shade.fill((5, 9, 12, 155)); canvas.blit(shade, (0, 0))
    panel = pygame.Rect(72, 28, 880, 520)
    draw_panel(canvas, panel, fill=(35, 43, 50), radius=13)
    pygame.draw.rect(canvas, (27, 34, 40), (panel.x + 4, panel.y + 4, panel.width - 8, 58), border_radius=10)
    canvas.blit(title_font.render("PERSONAGEM", True, (248, 224, 165)), (panel.x + 24, panel.y + 17))
    canvas.blit(font.render("V fechar  •  I inventário  •  ESC voltar", True, (180, 190, 193)), (panel.right - 294, panel.y + 23))

    card = pygame.Rect(92, 102, 245, 426)
    pygame.draw.rect(canvas, (25, 32, 38), card, border_radius=9); pygame.draw.rect(canvas, (82, 94, 98), card, 2, border_radius=9)
    pygame.draw.circle(canvas, (183, 143, 74), (card.centerx, card.y + 105), 72)
    pygame.draw.circle(canvas, (60, 91, 70), (card.centerx, card.y + 105), 67)
    sprite = pygame.transform.scale(frame(player.idle, 0, player.facing), (124, 124))
    canvas.blit(sprite, (card.centerx - 62, card.y + 43))
    name = title_font.render("Aventureiro", True, "white"); canvas.blit(name, (card.centerx - name.get_width()//2, card.y + 190))
    cls = font.render("Espadachim", True, (183, 192, 194)); canvas.blit(cls, (card.centerx - cls.get_width()//2, card.y + 221))
    lvl = title_font.render(f"Nível {player.level}", True, (248, 224, 165)); canvas.blit(lvl, (card.centerx - lvl.get_width()//2, card.y + 257))
    canvas.blit(font.render("EXPERIÊNCIA", True, (190, 198, 198)), (card.x + 20, card.y + 310))
    xp = pygame.Rect(card.x + 20, card.y + 339, card.width - 40, 15)
    pygame.draw.rect(canvas, (15, 20, 24), xp, border_radius=5)
    xp_fill = xp.inflate(-4, -4); xp_fill.width = round(xp_fill.width * player.current_xp / player.xp_to_next_level)
    if xp_fill.width: pygame.draw.rect(canvas, (193, 154, 75), xp_fill, border_radius=4)
    xp_text = font.render(f"{player.current_xp} / {player.xp_to_next_level} XP", True, (183, 192, 194))
    canvas.blit(xp_text, (card.centerx - xp_text.get_width()//2, card.y + 365))

    right_x, right_w = 355, 577
    draw_bar(canvas, pygame.Rect(right_x, 104, right_w, 31), player.hp, player.max_hp, (185, 51, 62), "HP", font)
    draw_bar(canvas, pygame.Rect(right_x, 143, right_w, 31), player.sp, player.max_sp, (54, 112, 196), "SP", font)
    canvas.blit(title_font.render("ATRIBUTOS", True, (248, 224, 165)), (right_x, 178))
    hovered_attribute = None
    for i, (label, key, color, row, plus) in enumerate(character_attribute_layout()):
        value = player.final_stats[key]
        hover = row.collidepoint(mouse_pos)
        pygame.draw.rect(canvas, (40, 51, 56) if hover else (27, 34, 40), row, border_radius=6)
        pygame.draw.rect(canvas, (102, 112, 105) if hover else (72, 82, 86), row, 1, border_radius=6)
        pygame.draw.circle(canvas, color, (row.x + 16, row.centery), 6)
        canvas.blit(font.render(label, True, "white"), (row.x + 30, row.y + 5))
        track = pygame.Rect(row.x + 155, row.y + 9, 210, 10)
        pygame.draw.rect(canvas, (17, 22, 26), track, border_radius=4)
        pygame.draw.rect(canvas, color, (track.x, track.y, min(track.width, value * 6), track.height), border_radius=4)
        bonus = player.equipment_bonus[key]
        value_label = f"{value} (+{bonus})" if bonus else str(value)
        value_text = font.render(value_label, True, (248, 224, 165))
        canvas.blit(value_text, (plus.x - value_text.get_width() - 10, row.y + 5))
        enabled = player.stat_points > 0
        pygame.draw.rect(canvas, (184, 145, 74) if enabled and plus.collidepoint(mouse_pos)
                         else (130, 102, 59) if enabled else (66, 73, 74), plus, border_radius=5)
        glyph = font.render("+", True, "white" if enabled else (141, 148, 148))
        canvas.blit(glyph, (plus.centerx - glyph.get_width() // 2, plus.y + 3))
        if hover:
            hovered_attribute = (label, key, plus.collidepoint(mouse_pos))
    canvas.blit(font.render(f"Pontos: {player.stat_points}   •   Clique em + ou use 1–4", True, (248, 224, 165)), (right_x, 331))

    canvas.blit(title_font.render("STATS DE COMBATE", True, (248, 224, 165)), (right_x, 351))
    combat = (("ATAQUE", str(player.physical_attack)), ("DEFESA", f"{player.defense:.1f}"),
              ("CRÍTICO", f"{player.crit_chance:.1%}"),
              ("VELOCIDADE", f"{player.speed/attributes.BASE_MOVE_SPEED:.0%}"),
              ("HP MÁX.", str(player.max_hp)), ("SP MÁX.", str(player.max_sp)),
              ("PODER MÁGICO", str(player.magic_power)),
              ("CADÊNCIA", f"{player.attack_cooldown_frames} frames"))
    for index, (label, value) in enumerate(combat):
        col, row = index % 2, index // 2
        x, y = right_x + col * 288, 379 + row * 18
        canvas.blit(font.render(label, True, (163, 180, 178)), (x, y))
        value_text = font.render(value, True, (244, 226, 176))
        canvas.blit(value_text, (x + 275 - value_text.get_width(), y))

    equip = pygame.Rect(right_x, 450, right_w, 78)
    pygame.draw.rect(canvas, (25, 32, 38), equip, border_radius=8); pygame.draw.rect(canvas, (82, 94, 98), equip, 1, border_radius=8)
    canvas.blit(font.render("EQUIPAMENTOS", True, (248, 224, 165)), (equip.x + 12, equip.y + 5))
    for i, slot in enumerate(SLOTS):
        entry = player.equipment.get(slot)
        label = f"{slot}: {(entry or {}).get('name', 'Nenhum')}"
        if entry and entry.get("bonuses"):
            label += "  " + "  ".join(f"+{amount} {key.title()}" for key, amount in entry["bonuses"].items())
        text = font.render(fit_text(label, font, equip.width - 28), True, (220, 224, 215))
        canvas.blit(text, (equip.x + 12, equip.y + 24 + i * 17))

    if hovered_attribute:
        label, key, on_plus = hovered_attribute
        descriptions = {"vitalidade": "Aumenta HP máximo e Defesa.",
                        "força": "Aumenta dano físico e empurrão.",
                        "magia": "Aumenta SP e Poder Mágico.",
                        "agilidade": "Aumenta movimento, cadência e crítico."}
        lines = attribute_preview_lines(player, key) if on_plus else [descriptions[key]]
        tooltip = pygame.Rect(min(mouse_pos[0] + 15, VIEW[0] - 340),
                              min(mouse_pos[1] + 14, VIEW[1] - 36 - len(lines) * 20),
                              324, 30 + len(lines) * 20)
        pygame.draw.rect(canvas, (18, 27, 32), tooltip, border_radius=7)
        pygame.draw.rect(canvas, (187, 145, 75), tooltip, 2, border_radius=7)
        canvas.blit(font.render(label.upper() + (" • PRÓXIMO PONTO" if on_plus else ""),
                                True, (248, 224, 165)), (tooltip.x + 10, tooltip.y + 6))
        for index, line in enumerate(lines):
            canvas.blit(font.render(line, True, (226, 231, 218)), (tooltip.x + 10, tooltip.y + 27 + index * 20))
