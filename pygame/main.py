"""Compatibilidade pública e ponto de entrada do O Vale (v0.2)."""
import random  # preserva o ponto de monkeypatch usado por consumidores antigos
import sys

import pygame

from core.assets import ROOT, load
from core.config import *  # noqa: F401,F403 - constantes públicas legadas
from core.camera import camera_for
from entities.enemy import Enemy
from entities.player import Player, frame
from entities.npc import NPC, nearest
from systems import progression as attributes
from systems.dialogue import DialogueBox
from systems.equipment import EQUIPMENT, SLOTS, item
from systems.inventory import add_inventory_item, apply_inventory_action, inventory_kind
from systems.items import CONSUMABLES, consumable
from systems.quest import ACTIVE, AVAILABLE, COMPLETED, REWARDED, QuestManager
from ui import defeat_screen as game_over
from ui.character_menu import (
    attribute_key_at, attribute_preview_lines, character_attribute_layout,
    draw_character_menu, fit_text, wrap_text,
)
from ui.coordinates import logical_mouse_position
from ui.damage_number import DamageNumber
from ui.hud import draw_bar, draw_hud, draw_panel
from ui.inventory_menu import (
    draw_inventory, handle_inventory_click as _select_inventory_item, inventory_action_label,
    inventory_items, inventory_layout,
)
from ui.world_renderer import draw_world
from world.respawn import restore_player_after_death, safe_respawn_position
from world.world_manager import WorldManager
import save_manager


_WORLD_MANAGER = WorldManager.for_game(load)


def build_region(name, opened_chests=None):
    return _WORLD_MANAGER.build_region(name, opened_chests)


def reset_forest_boss_encounter():
    return _WORLD_MANAGER.reset_forest_boss_encounter(load)


def spawn_enemies(region):
    return _WORLD_MANAGER.spawn_enemies(region, load)


def can_transition(source, destination, quest_manager):
    return _WORLD_MANAGER.can_transition(source, destination, quest_manager)


def handle_inventory_click(position, inventory, player, ui_state):
    """Legacy adapter; selection is UI, item effects stay in the inventory system."""
    selected = _select_inventory_item(position, inventory, player, ui_state)
    return apply_inventory_action(selected, inventory, player, ui_state) if selected else None


def handle_character_click(position, player):
    """Legacy API; UI resolves the target and Player owns the stat mutation."""
    key = attribute_key_at(position)
    return player.spend_stat(key) if key else False


def main():
    from core.game import Game
    return Game(restore_player=restore_player_after_death).run()


if __name__ == "__main__":
    sys.exit(main())
