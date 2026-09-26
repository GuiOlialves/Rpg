"""Layout, apresentação e seleção visual do inventário."""
import pygame
from core.config import VIEW
from systems.items import CONSUMABLES
from systems.inventory import inventory_kind
from ui.character_menu import fit_text, wrap_text
from ui.hud import ACCENT, draw_panel

def inventory_items(inventory, tab):
    if tab == "CONSUMÍVEIS": return [entry for entry in inventory if inventory_kind(entry) == "consumable"]
    if tab == "EQUIPAMENTO": return [entry for entry in inventory if inventory_kind(entry) == "equipment"]
    return list(inventory)

def inventory_action_label(item, player):
    if not item: return None
    if inventory_kind(item) == "consumable": return "USAR"
    if inventory_kind(item) == "equipment":
        equipped = player.equipment.get(item.get("slot"))
        return "DESEQUIPAR" if equipped and equipped.get("id") == item.get("id") else "EQUIPAR"
    return None

def inventory_layout(inventory, ui_state, player):
    panel = pygame.Rect(70, 34, 884, 508)
    tab_rects = [pygame.Rect(98 + i * 132, 98, 122, 34) for i in range(3)]
    shown = inventory_items(inventory, ui_state["tab"])
    slot_rects = [pygame.Rect(98 + col * 94, 160 + row * 98, 84, 84) for row in range(3) for col in range(5)]
    details = pygame.Rect(594, 148, 340, 323)
    action = pygame.Rect(616, 482, 296, 44)
    return panel, tab_rects, shown, slot_rects, details, action


def draw_item_icon(canvas, item, center, size=34):
    """Tiny hard-edged icons; this project currently ships no inventory art."""
    center = (round(center[0]), round(center[1]))
    half = size // 2
    color = item.get("color", (118, 139, 135))
    plate = pygame.Rect(center[0] - half - 5, center[1] - half - 5,
                        size + 10, size + 10)
    pygame.draw.rect(canvas, (20, 28, 33), plate, border_radius=5)
    pygame.draw.rect(canvas, (76, 91, 92), plate, 1, border_radius=5)
    item_id = item.get("id", "")
    kind = inventory_kind(item)
    if kind == "consumable" and item_id in {"potion", "ether"}:
        body = pygame.Rect(center[0] - 7, center[1] - 7, 14, 17)
        neck = pygame.Rect(center[0] - 4, center[1] - 13, 8, 7)
        pygame.draw.rect(canvas, (36, 35, 31), body.inflate(4, 4), border_radius=3)
        pygame.draw.rect(canvas, color, body, border_radius=3)
        pygame.draw.rect(canvas, (220, 206, 163), neck, border_radius=1)
        pygame.draw.rect(canvas, (36, 35, 31), neck, 1)
        pygame.draw.line(canvas, tuple(min(255, c + 55) for c in color),
                         (body.x + 3, body.y + 4), (body.x + 3, body.bottom - 4), 2)
        pygame.draw.rect(canvas, (52, 43, 34),
                         pygame.Rect(center[0] - 5, center[1] - 15, 10, 3))
    elif kind == "consumable" and item_id == "herb":
        pygame.draw.polygon(canvas, (43, 112, 70), [
            (center[0] - 13, center[1] + 9), (center[0] - 11, center[1] - 8),
            (center[0] - 1, center[1] - 14), (center[0] + 1, center[1] - 2),
            (center[0] + 12, center[1] - 9), (center[0] + 10, center[1] + 4),
            (center[0] + 1, center[1] + 5), (center[0] - 6, center[1] + 14),
        ])
        pygame.draw.line(canvas, (178, 194, 115),
                         (center[0] - 8, center[1] + 10),
                         (center[0] + 7, center[1] - 7), 2)
    elif kind == "equipment" and item.get("slot") == "Arma":
        pygame.draw.line(canvas, (39, 36, 32),
                         (center[0] - 11, center[1] + 12),
                         (center[0] + 11, center[1] - 10), 7)
        pygame.draw.line(canvas, color,
                         (center[0] - 7, center[1] + 6),
                         (center[0] + 10, center[1] - 11), 4)
        pygame.draw.line(canvas, (213, 194, 146),
                         (center[0] - 13, center[1] + 3),
                         (center[0] - 3, center[1] + 13), 3)
    elif kind == "equipment" and item.get("slot") == "Armadura":
        pygame.draw.polygon(canvas, (42, 37, 32), [
            (center[0] - 12, center[1] - 10), (center[0] + 12, center[1] - 10),
            (center[0] + 9, center[1] + 5), (center[0], center[1] + 14),
            (center[0] - 9, center[1] + 5),
        ])
        pygame.draw.polygon(canvas, color, [
            (center[0] - 9, center[1] - 7), (center[0] + 9, center[1] - 7),
            (center[0] + 7, center[1] + 3), (center[0], center[1] + 10),
            (center[0] - 7, center[1] + 3),
        ])
    else:
        pygame.draw.circle(canvas, (35, 40, 37), center, 11)
        pygame.draw.circle(canvas, color, center, 7)
        pygame.draw.rect(canvas, (233, 217, 168),
                         pygame.Rect(center[0] - 2, center[1] - 2, 4, 4))

def draw_inventory(canvas, inventory, font, title_font, player, ui_state, mouse_pos):
    shade = pygame.Surface(VIEW, pygame.SRCALPHA)
    shade.fill((5, 9, 12, 182))
    canvas.blit(shade, (0, 0))
    panel, tab_rects, shown, slot_rects, details, action_rect = inventory_layout(inventory, ui_state, player)
    draw_panel(canvas, panel, fill=(25, 34, 40), radius=8)
    header = pygame.Rect(panel.x + 5, panel.y + 5, panel.width - 10, 50)
    pygame.draw.rect(canvas, (31, 41, 47), header, border_radius=6)
    pygame.draw.line(canvas, (78, 91, 91),
                     (header.x + 18, header.bottom - 1),
                     (header.right - 18, header.bottom - 1), 1)
    canvas.blit(title_font.render("INVENTÁRIO", True, (248, 224, 165)), (panel.x + 24, panel.y + 14))
    hint = pygame.font.Font(None, 17).render(
        "I fechar   ·   V personagem   ·   ESC voltar", True, (172, 185, 185))
    canvas.blit(hint, (panel.right - hint.get_width() - 22,
                       header.centery - hint.get_height() // 2))
    tabs = ["TODOS", "CONSUMÍVEIS", "EQUIPAMENTO"]
    for index, (tab, rect) in enumerate(zip(tabs, tab_rects)):
        active = ui_state["tab"] == tab; hover = rect.collidepoint(mouse_pos)
        color = (111, 83, 48) if active else (49, 61, 65) if hover else (37, 47, 52)
        pygame.draw.rect(canvas, color, rect, border_radius=6)
        pygame.draw.rect(canvas, (211, 177, 111) if active or hover else (72, 86, 89), rect, 1, border_radius=6)
        label = font.render(tab, True, "white" if active or hover else (170, 180, 183))
        canvas.blit(label, (rect.centerx - label.get_width()//2, rect.y + 8))

    grid = pygame.Rect(86, 148, 490, 323)
    pygame.draw.rect(canvas, (23, 31, 36), grid, border_radius=7)
    pygame.draw.rect(canvas, (68, 82, 84), grid, 1, border_radius=7)
    selected = ui_state.get("selected")
    for index, rect in enumerate(slot_rects):
        item = shown[index] if index < len(shown) else None
        is_selected = item is not None and item is selected
        hovered = rect.collidepoint(mouse_pos)
        fill = (43, 53, 56) if hovered else (35, 45, 49) if is_selected else (27, 36, 41)
        border = (231, 198, 128) if is_selected else (151, 125, 79) if hovered else (65, 79, 82)
        pygame.draw.rect(canvas, fill, rect, border_radius=5)
        pygame.draw.rect(canvas, border, rect,
                         2 if is_selected or hovered else 1, border_radius=5)
        if item is None: continue
        draw_item_icon(canvas, item, (rect.centerx, rect.y + 30), size=30)
        name = font.render(fit_text(item.get("name", "Item"), font, rect.width - 8), True, "white")
        canvas.blit(name, (rect.centerx - name.get_width()//2, rect.y + 56))
        amount_count = item.get("amount", 1)
        if amount_count > 1:
            badge = pygame.Rect(rect.right - 23, rect.y + 3, 20, 18)
            pygame.draw.rect(canvas, (178, 137, 69), badge, border_radius=6)
            amount_text = font.render(str(amount_count), True, "white")
            canvas.blit(amount_text, (badge.centerx - amount_text.get_width()//2, badge.y + 1))
        if inventory_kind(item) == "equipment" and any(e and e.get("id") == item.get("id") for e in player.equipment.values()):
            pygame.draw.circle(canvas, (84, 177, 113), (rect.x + 11, rect.y + 11), 9)
            e_text = font.render("E", True, "white"); canvas.blit(e_text, (rect.x + 11 - e_text.get_width()//2, rect.y + 2))

    pygame.draw.rect(canvas, (26, 35, 40), details, border_radius=7)
    pygame.draw.rect(canvas, (75, 90, 91), details, 1, border_radius=7)
    if selected is not None and selected in inventory:
        kind = inventory_kind(selected)
        draw_item_icon(canvas, selected, (details.x + 46, details.y + 47), size=38)
        name_lines = wrap_text(selected.get("name", "Item"), title_font,
                               details.width - 96, 2)
        for i, line in enumerate(name_lines):
            canvas.blit(title_font.render(line, True, ACCENT),
                        (details.x + 90, details.y + 20 + i * 25))
        kind_y = details.y + 70 if len(name_lines) > 1 else details.y + 54
        sub = f"Equipamento • {selected.get('slot', '')}" if kind == "equipment" else "Consumível" if kind == "consumable" else "Item"
        canvas.blit(font.render(sub, True, (133, 192, 145)),
                    (details.x + 90, kind_y))
        pygame.draw.line(canvas, (69, 84, 85),
                         (details.x + 14, details.y + 91),
                         (details.right - 14, details.y + 91), 1)
        description = selected.get("description") or {"Poção": "Recupera 30 pontos de vida.", "Éter": "Recupera 30 pontos de espírito.", "Erva": "Recupera 15 pontos de vida."}.get(selected.get("name"), "Um item encontrado durante a aventura.")
        desc_y = details.y + 104
        for i, line in enumerate(wrap_text(description, font, details.width - 32, 3)):
            canvas.blit(font.render(line, True, (207, 216, 212)),
                        (details.x + 16, desc_y + i * 21))
        bonus_y = desc_y + 70
        if kind == "equipment":
            bonus_text = ", ".join(f"+{amount} {key.title()}" for key, amount in selected.get("bonuses", {}).items()) or "Sem bônus"
            for i, line in enumerate(wrap_text("Bônus: " + bonus_text, font, details.width - 32, 2)):
                canvas.blit(font.render(line, True, ACCENT),
                            (details.x + 16, bonus_y + i * 21))
        elif kind == "consumable":
            effect = "+30 HP" if selected.get("name") == "Poção" else "+30 SP" if selected.get("name") == "Éter" else "+15 HP"
            effect_image = font.render(
                f"Efeito: {effect}   Quantidade: {selected.get('amount', 1)}",
                True, ACCENT)
            canvas.blit(effect_image, (details.x + 16, bonus_y))
    else:
        canvas.blit(title_font.render("Selecione um item", True, (205, 210, 205)), (details.x + 18, details.y + 30))
        canvas.blit(font.render("Clique em um espaço do inventário", True, (160, 173, 177)), (details.x + 18, details.y + 66))

    action_label = inventory_action_label(selected, player) if selected in inventory else None
    if action_label:
        hover = action_rect.collidepoint(mouse_pos)
        color = (202, 163, 87) if hover else (158, 119, 57)
        pygame.draw.rect(canvas, color, action_rect, border_radius=6)
        pygame.draw.rect(canvas, (224, 192, 127), action_rect, 2, border_radius=6)
        label = title_font.render(action_label, True, (255, 250, 232))
        canvas.blit(label, (action_rect.centerx - label.get_width()//2, action_rect.centery - label.get_height()//2))

def handle_inventory_click(pos, inventory, player, ui_state):
    _, tab_rects, shown, slot_rects, _, action_rect = inventory_layout(inventory, ui_state, player)
    tabs = ["TODOS", "CONSUMÍVEIS", "EQUIPAMENTO"]
    for tab, rect in zip(tabs, tab_rects):
        if rect.collidepoint(pos):
            ui_state["tab"] = tab
            if ui_state.get("selected") not in inventory_items(inventory, tab): ui_state["selected"] = None
            return None
    for index, rect in enumerate(slot_rects):
        if rect.collidepoint(pos):
            ui_state["selected"] = shown[index] if index < len(shown) else None
            return None
    selected = ui_state.get("selected")
    if action_rect.collidepoint(pos) and inventory_action_label(selected, player):
        return selected
    return None
