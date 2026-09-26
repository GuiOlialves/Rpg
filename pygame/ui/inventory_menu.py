"""Layout, apresentação e seleção visual do inventário."""
import pygame
from core.config import VIEW
from systems.items import CONSUMABLES
from systems.inventory import inventory_kind
from ui.character_menu import fit_text, wrap_text
from ui.hud import draw_panel

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

def draw_inventory(canvas, inventory, font, title_font, player, ui_state, mouse_pos):
    shade = pygame.Surface(VIEW, pygame.SRCALPHA); shade.fill((5, 9, 12, 155)); canvas.blit(shade, (0, 0))
    panel, tab_rects, shown, slot_rects, details, action_rect = inventory_layout(inventory, ui_state, player)
    draw_panel(canvas, panel, fill=(35, 43, 50), radius=13)
    pygame.draw.rect(canvas, (27, 34, 40), (panel.x + 4, panel.y + 4, panel.width - 8, 54), border_radius=10)
    canvas.blit(title_font.render("INVENTÁRIO", True, (248, 224, 165)), (panel.x + 24, panel.y + 14))
    canvas.blit(font.render("I fechar  •  V personagem  •  ESC voltar", True, (180, 190, 193)), (panel.right - 294, panel.y + 21))
    tabs = ["TODOS", "CONSUMÍVEIS", "EQUIPAMENTO"]
    for index, (tab, rect) in enumerate(zip(tabs, tab_rects)):
        active = ui_state["tab"] == tab; hover = rect.collidepoint(mouse_pos)
        color = (178, 137, 69) if active else (66, 78, 84) if hover else (48, 57, 63)
        pygame.draw.rect(canvas, color, rect, border_radius=6)
        pygame.draw.rect(canvas, (218, 185, 112) if active or hover else (82, 94, 98), rect, 1, border_radius=6)
        label = font.render(tab, True, "white" if active or hover else (170, 180, 183))
        canvas.blit(label, (rect.centerx - label.get_width()//2, rect.y + 8))

    grid = pygame.Rect(86, 148, 490, 323)
    pygame.draw.rect(canvas, (26, 33, 39), grid, border_radius=8)
    selected = ui_state.get("selected")
    for index, rect in enumerate(slot_rects):
        item = shown[index] if index < len(shown) else None
        is_selected = item is not None and item is selected
        hovered = rect.collidepoint(mouse_pos)
        fill = (53, 59, 60) if hovered else (35, 42, 47) if is_selected else (22, 28, 33)
        border = (240, 205, 132) if is_selected else (169, 137, 77) if hovered else (82, 94, 98)
        pygame.draw.rect(canvas, fill, rect, border_radius=7); pygame.draw.rect(canvas, border, rect, 2 if is_selected or hovered else 1, border_radius=7)
        if item is None: continue
        color = item.get("color", (110, 130, 130))
        pygame.draw.circle(canvas, (14, 18, 22), (rect.centerx, rect.y + 31), 21)
        pygame.draw.circle(canvas, color, (rect.centerx, rect.y + 31), 17)
        pygame.draw.circle(canvas, (245, 226, 160), (rect.centerx - 5, rect.y + 26), 4)
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

    pygame.draw.rect(canvas, (26, 33, 39), details, border_radius=8); pygame.draw.rect(canvas, (82, 94, 98), details, 1, border_radius=8)
    if selected is not None and selected in inventory:
        kind = inventory_kind(selected)
        pygame.draw.circle(canvas, selected.get("color", (110, 130, 130)), (details.centerx, details.y + 43), 25)
        name_lines = wrap_text(selected.get("name", "Item"), title_font, details.width - 30, 2)
        for i, line in enumerate(name_lines): canvas.blit(title_font.render(line, True, (248, 224, 165)), (details.x + 16, details.y + 78 + i*27))
        kind_y = details.y + 132 if len(name_lines) > 1 else details.y + 108
        sub = f"Equipamento • {selected.get('slot', '')}" if kind == "equipment" else "Consumível" if kind == "consumable" else "Item"
        canvas.blit(font.render(sub, True, (112, 181, 124)), (details.x + 16, kind_y))
        description = selected.get("description") or {"Poção": "Recupera 30 pontos de vida.", "Éter": "Recupera 30 pontos de espírito.", "Erva": "Recupera 15 pontos de vida."}.get(selected.get("name"), "Um item encontrado durante a aventura.")
        desc_y = kind_y + 30
        for i, line in enumerate(wrap_text(description, font, details.width - 32, 3)):
            canvas.blit(font.render(line, True, (210, 216, 216)), (details.x + 16, desc_y + i*22))
        bonus_y = desc_y + 70
        if kind == "equipment":
            bonus_text = ", ".join(f"+{amount} {key.title()}" for key, amount in selected.get("bonuses", {}).items()) or "Sem bônus"
            for i, line in enumerate(wrap_text("Bônus: " + bonus_text, font, details.width - 32, 2)):
                canvas.blit(font.render(line, True, (248, 224, 165)), (details.x + 16, bonus_y + i*22))
        elif kind == "consumable":
            effect = "+30 HP" if selected.get("name") == "Poção" else "+30 SP" if selected.get("name") == "Éter" else "+15 HP"
            canvas.blit(font.render(f"Efeito: {effect}   Quantidade: {selected.get('amount', 1)}", True, (248, 224, 165)), (details.x + 16, bonus_y))
    else:
        canvas.blit(title_font.render("Selecione um item", True, (205, 210, 205)), (details.x + 18, details.y + 30))
        canvas.blit(font.render("Clique em um espaço do inventário", True, (160, 173, 177)), (details.x + 18, details.y + 66))

    action_label = inventory_action_label(selected, player) if selected in inventory else None
    if action_label:
        hover = action_rect.collidepoint(mouse_pos)
        color = (202, 163, 87) if hover else (158, 119, 57)
        pygame.draw.rect(canvas, color, action_rect, border_radius=7)
        pygame.draw.rect(canvas, (238, 208, 150), action_rect, 2, border_radius=7)
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
