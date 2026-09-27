"""Development-only prologue checkpoints and their isolated runtime presets."""
from dataclasses import dataclass
import os

import pygame

from entities.player import Player
from story.story_manager import StoryManager
from systems.equipment import item
from systems.items import consumable
from systems.quest import QuestManager


CHECKPOINTS = (
    ("normal", "Início normal", "Início normal"),
    ("prologue_2a", "Prólogo 2A — Retorno dos Slimes", "Prólogo 2A"),
    ("prologue_2b", "Prólogo 2B — Investigação da casa", "Prólogo 2B"),
    ("prologue_2c", "Prólogo 2C — Marcha Azul", "Prólogo 2C"),
    ("prologue_2d", "Prólogo 2D — Campo de batalha", "Prólogo 2D"),
    ("prologue_2e", "Prólogo 2E — O Fantasma", "Prólogo 2E"),
    ("reset", "Resetar estado de teste", ""),
)

DEBUG_CHECKPOINTS_ENABLED = (
    __debug__ and os.environ.get("OVALE_DEBUG_CHECKPOINTS", "1").lower()
    not in {"0", "false", "off", "no"}
)


@dataclass
class CheckpointRuntime:
    player: object
    inventory: list
    quests: QuestManager
    story: StoryManager
    region_id: str
    region: dict
    enemies: list
    narrative: object
    opened_chests: set


def _new_inventory():
    return [consumable("potion", 3), consumable("ether", 2),
            consumable("herb", 5), item("iron_blade"), item("reinforced_leather")]


def create_checkpoint(checkpoint_id, *, load, build_region, spawn_enemies,
                      restore_resident, opening_sequence):
    """Construct one complete, self-contained story state without touching saves."""
    if checkpoint_id not in {entry[0] for entry in CHECKPOINTS[:-1]}:
        raise ValueError(f"Checkpoint desconhecido: {checkpoint_id}")

    player = Player(load("assets/player/f_player_sheet.png"),
                    load("assets/player/f_player_attack_sheet.png"))
    inventory = _new_inventory()
    quests = QuestManager()
    flags = {
        "woke_up": checkpoint_id != "normal",
        "saw_silhouette": checkpoint_id != "normal",
        "slime_quest_started": checkpoint_id != "normal",
        "alden_post_slimes_talk": checkpoint_id in {
            "prologue_2b", "prologue_2c", "prologue_2d", "prologue_2e"},
        "house_investigation_unlocked": checkpoint_id in {
            "prologue_2b", "prologue_2c", "prologue_2d", "prologue_2e"},
        "pendant_found": checkpoint_id in {
            "prologue_2c", "prologue_2d", "prologue_2e"},
        "house_searched": checkpoint_id in {
            "prologue_2c", "prologue_2d", "prologue_2e"},
        "blue_army_departed": checkpoint_id in {"prologue_2d", "prologue_2e"},
        "forest_massacre_discovered": checkpoint_id == "prologue_2e",
        "red_insignia_found": checkpoint_id == "prologue_2e",
        "red_officer_met": False,
        "red_officer_memory_seen": False,
        "red_officer_escaped": False,
        "prologue_completed": False,
        "red_officer_defeated": False,
        "forest_battle_progress": 10 if checkpoint_id == "prologue_2e" else 0,
    }
    story = StoryManager(flags)

    if checkpoint_id != "normal":
        quests.accept("forest_trouble")
        for _ in range(5):
            quests.enemy_defeated("slime")
        if checkpoint_id != "prologue_2a":
            # Use the normal claim path so both quest status and the 3-herb
            # reward match a real playthrough (base 5 herbs + reward 3).
            quests.claim("forest_trouble", inventory)

    region_id, position = {
        "normal": ("home", (512, 288)),
        "prologue_2a": ("village", (1738, 560)),
        "prologue_2b": ("home", (512, 448)),
        "prologue_2c": ("home", (512, 448)),
        "prologue_2d": ("forest", (120, 575)),
        "prologue_2e": ("forest", (1460, 520)),
    }[checkpoint_id]
    player.x, player.y = position

    region = build_region(region_id)
    story.apply_to_region(region)
    if region_id == "village" and story.get("slime_quest_started"):
        restore_resident(region, load("assets/npc/civilian_customer.png"))
    enemies = spawn_enemies(region)
    narrative = opening_sequence() if checkpoint_id == "normal" else None
    return CheckpointRuntime(
        player=player, inventory=inventory, quests=quests, story=story,
        region_id=region_id, region=region, enemies=enemies,
        narrative=narrative, opened_chests=set())


class DebugCheckpointMenu:
    """Small keyboard menu and status tag for development checkpoint sessions."""

    def __init__(self):
        self.enabled = DEBUG_CHECKPOINTS_ENABLED
        self.active = False
        self.selected_index = 0
        self.checkpoint_id = None

    @property
    def status_label(self):
        if not self.checkpoint_id:
            return ""
        label = next((entry[2] for entry in CHECKPOINTS
                      if entry[0] == self.checkpoint_id), "Início normal")
        return f"DEBUG — {label}"

    def open(self):
        if self.enabled:
            self.active = True

    def close(self):
        self.active = False

    def handle_event(self, event):
        """Return ('close'|'select'|'reset', checkpoint_id) for menu actions."""
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_ESCAPE, pygame.K_F2):
            self.close()
            return ("close", None)
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(CHECKPOINTS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(CHECKPOINTS)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            checkpoint_id = CHECKPOINTS[self.selected_index][0]
            self.close()
            if checkpoint_id == "reset":
                return ("reset", self.checkpoint_id or "normal")
            return ("select", checkpoint_id)
        return None

    def draw(self, surface):
        if not self.enabled:
            return
        if self.status_label:
            font = pygame.font.Font(None, 18)
            label = font.render(self.status_label, True, (236, 229, 204))
            rect = pygame.Rect(12, 10, label.get_width() + 20, 28)
            pygame.draw.rect(surface, (15, 20, 24, 205), rect, border_radius=4)
            surface.blit(label, (rect.x + 10, rect.y + 6))
        if not self.active:
            return

        width, height = surface.get_size()
        panel = pygame.Rect(width // 2 - 238, height // 2 - 185, 476, 370)
        shade = pygame.Surface((width, height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 145))
        surface.blit(shade, (0, 0))
        pygame.draw.rect(surface, (29, 35, 40), panel, border_radius=8)
        pygame.draw.rect(surface, (174, 157, 117), panel, 2, border_radius=8)
        title = pygame.font.Font(None, 30).render(
            "CHECKPOINTS DE DEBUG", True, (239, 225, 188))
        surface.blit(title, (panel.x + 24, panel.y + 18))
        font = pygame.font.Font(None, 23)
        for index, (_, label, _) in enumerate(CHECKPOINTS):
            y = panel.y + 62 + index * 38
            if index == self.selected_index:
                pygame.draw.rect(surface, (71, 78, 76),
                                 (panel.x + 15, y - 4, panel.width - 30, 31),
                                 border_radius=4)
            color = (250, 237, 204) if index == self.selected_index else (205, 207, 198)
            surface.blit(font.render(label, True, color), (panel.x + 27, y))
        hint = pygame.font.Font(None, 18).render(
            "↑/↓ selecionar   Enter confirmar   Esc fechar", True, (179, 185, 183))
        surface.blit(hint, (panel.x + 24, panel.bottom - 27))
