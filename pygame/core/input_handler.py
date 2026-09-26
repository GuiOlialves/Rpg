"""Translate raw Pygame events into game-level input commands."""
from dataclasses import dataclass

import pygame

from ui.character_menu import attribute_key_at
from ui.coordinates import logical_mouse_position
from ui.inventory_menu import handle_inventory_click, inventory_items


@dataclass(frozen=True)
class InputCommand:
    name: str
    value: object = None


class InputHandler:
    """Own keyboard/mouse mapping; gameplay effects stay in Game/systems."""

    def route(self, event, *, ui_mode, dialogue, player, inventory,
              inventory_ui, game_over_screen, view):
        if event.type == pygame.QUIT:
            return InputCommand("quit")

        if game_over_screen is not None:
            mouse = (logical_mouse_position(event.pos)
                     if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN)
                     else (0, 0))
            choice = game_over_screen.handle_event(event, mouse, view)
            return InputCommand("defeat_choice", choice) if choice else None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            position = logical_mouse_position(event.pos)
            if ui_mode == "character":
                key = attribute_key_at(position)
                return InputCommand("spend_stat", key) if key else None
            if ui_mode == "inventory":
                selected = handle_inventory_click(position, inventory, player, inventory_ui)
                return InputCommand("use_item", selected) if selected is not None else None

        if event.type != pygame.KEYDOWN:
            return None

        key = event.key
        if key == pygame.K_F5:
            return InputCommand("save")
        if key == pygame.K_F9:
            return InputCommand("load")
        if key == pygame.K_ESCAPE:
            return InputCommand("escape")
        if key == pygame.K_e:
            return InputCommand("interact")
        if key == pygame.K_v and not dialogue.active:
            return InputCommand("toggle_character")
        if key == pygame.K_i and not dialogue.active:
            return InputCommand("toggle_inventory")
        if key == pygame.K_F3:
            return InputCommand("toggle_debug")

        if ui_mode == "character" and pygame.K_1 <= key <= pygame.K_4:
            return InputCommand("spend_stat", ("vitalidade", "força", "magia", "agilidade")[key - pygame.K_1])
        if ui_mode == "inventory" and pygame.K_1 <= key <= pygame.K_8:
            shown = inventory_items(inventory, inventory_ui["tab"])
            index = key - pygame.K_1
            if index < len(shown):
                inventory_ui["selected"] = shown[index]
                return InputCommand("use_item", shown[index])
            return None
        if key == pygame.K_SPACE and ui_mode is None and not dialogue.active:
            return InputCommand("attack")
        if key == pygame.K_q and ui_mode is None and not dialogue.active:
            return InputCommand("dash")
        return None
