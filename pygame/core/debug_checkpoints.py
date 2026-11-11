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
    ("chapter1_a", "Capítulo I — 1A: O Retorno", "Capítulo I 1A"),
    ("chapter1_b", "Capítulo I — 1B: A Antiga Estrada", "Capítulo I 1B"),
    ("chapter1_c", "Capítulo I — 1C: O Posto de Vigia", "Capítulo I 1C"),
    ("chapter1_d", "Capítulo I — 1D: Edrin", "Capítulo I 1D"),
    ("chapter1_e", "Capítulo I — 1E: Namar", "Capítulo I 1E"),
    ("chapter1_f", "Capítulo I — 1F: O Depósito", "Capítulo I 1F"),
    ("chapter1_g", "Capítulo I — 1G: O Retorno ao Vale", "Capítulo I 1G"),
    ("chapter2_part_a", "Capítulo II — início da Parte A", "Capítulo II A"),
    ("chapter2_part_b", "Capítulo II — início da Parte B", "Capítulo II B"),
    ("chapter2_iriel", "Capítulo II — luta contra Iriel", "Luta contra Iriel"),
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


def _story_checkpoint(checkpoint_id, *, load, build_region, spawn_enemies):
    """Create isolated entry points for Chapter I and the Iriel boss test."""
    from systems.inventory import add_inventory_item
    from systems.items import quest_item
    from story.watchpost import POST_FLAGS
    from story.lacre_content import ENTER_FLAGS as LACRE_ENTER_FLAGS, DOCUMENTS
    from story.chapter2 import DUNGEON_REGIONS, spawn_pending as chapter2_spawn

    common = {"prologue_completed": True, "chapter1_started": True}
    stages = {
        "chapter1_a": ("village", (1850, 575), {
            "chapter1_returned": True,
        }),
        "chapter1_b": ("old_road", (1910, 850), {
            "chapter1_returned": True, "chapter1_alden_talk": True,
            "old_road_unlocked": True, "old_road_entered": True,
        }),
        "chapter1_c": ("watchpost", (850, 690), {
            "chapter1_returned": True, "chapter1_alden_talk": True,
            "old_road_unlocked": True, "old_road_entered": True,
            "road_camp_found": True, "road_red_clue_found": True,
            "road_memory_seen": True, "watchpost_seen": True,
            "watchpost_entered": True,
        }),
        "chapter1_d": ("pursuit", (900, 400), {
            "chapter1_returned": True, "chapter1_alden_talk": True,
            "old_road_unlocked": True, "old_road_entered": True,
            "road_camp_found": True, "road_red_clue_found": True,
            "road_memory_seen": True, "watchpost_seen": True,
            "pursuit_entered": True,
            **{flag: True for flag in POST_FLAGS},
        }),
        "chapter1_e": ("namar", (120, 825), {
            "chapter1_returned": True, "chapter1_alden_talk": True,
            "old_road_unlocked": True, "old_road_entered": True,
            "road_camp_found": True, "road_red_clue_found": True,
            "road_memory_seen": True, "watchpost_seen": True,
            **{flag: True for flag in POST_FLAGS},
            "edrin_escaped": True, "edrin_encounter_completed": True,
            "namar_clue_received": True, "namar_entered": True,
        }),
        "chapter1_f": ("archive", (246, 817), {
            "chapter1_returned": True, "chapter1_alden_talk": True,
            "old_road_unlocked": True, "old_road_entered": True,
            "road_camp_found": True, "road_red_clue_found": True,
            "road_memory_seen": True, "watchpost_seen": True,
            **{flag: True for flag in POST_FLAGS},
            "edrin_escaped": True, "edrin_encounter_completed": True,
            "namar_clue_received": True, "namar_entered": True,
            "namar_military_clue": True, "namar_civilian_clue": True,
            "namar_survivors_met": True, "namar_choice_protect": True,
            "namar_enemy_0_defeated": True, "namar_enemy_1_defeated": True,
            "namar_combat_completed": True, "namar_aftermath_seen": True,
            "namar_memory_seen": True, "namar_record_lead_found": True,
            "namar_completed": True, "archive_entered": True,
        }),
        "chapter1_g": ("village", (1770, 610), {
            "chapter1_returned": True, "chapter1_alden_talk": False,
            "old_road_unlocked": True, "old_road_entered": True,
            "road_camp_found": True, "road_red_clue_found": True,
            "road_memory_seen": True, "watchpost_seen": True,
            **{flag: True for flag in POST_FLAGS},
            "edrin_escaped": True, "edrin_encounter_completed": True,
            "namar_clue_received": True, "namar_entered": True,
            "namar_military_clue": True, "namar_civilian_clue": True,
            "namar_survivors_met": True, "namar_choice_protect": True,
            "namar_enemy_0_defeated": True, "namar_enemy_1_defeated": True,
            "namar_combat_completed": True, "namar_aftermath_seen": True,
            "namar_memory_seen": True, "namar_record_lead_found": True,
            "namar_completed": True,
            "archive_entered": True, "archive_search_marks": True,
            "archive_defense_report": True, "archive_petition": True,
            "archive_confrontation_started": True,
            "archive_veteran_defeated": True, "archive_order_obtained": True,
            "archive_memory_seen": True, "archive_forgetting_record": True,
            "archive_completed": True, "chapter1_final_returned": True,
        }),
    }
    if checkpoint_id == "chapter2_iriel":
        region_id = "seal_core"
        flags = {
            "chapter1_completed": True, "chapter2_started": True,
            "chapter2_part_a_completed": True, "chapter2_part_b_started": True,
            "lacre_vestibule_open": True, "lacre_gallery_open": True,
            "lacre_archive_open": True, "lacre_vigia_defeated": True,
            "lacre_core_vista_seen": True, "lacre_custodian_talk_seen": True,
            LACRE_ENTER_FLAGS[region_id]: True,
        }
        flags.update({flag: True for flag in LACRE_ENTER_FLAGS.values()})
        player = Player(load("assets/player/f_player_sheet.png"),
                        load("assets/player/f_player_attack_sheet.png"))
        player.x, player.y = 1024, 740
        story = StoryManager(flags)
        inventory = _new_inventory()
        for uid in ("lacre_purpose", "lacre_military", "lacre_identity"):
            _name, flag, *_rest = DOCUMENTS[uid]
            story.set(flag)
            add_inventory_item(inventory, quest_item(uid))
        region = build_region(region_id)
        story.apply_to_region(region)
        enemies = chapter2_spawn(region, story, spawn_enemies)
    else:
        region_id, position, stage_flags = stages[checkpoint_id]
        flags = {**common, **stage_flags}
        player = Player(load("assets/player/f_player_sheet.png"),
                        load("assets/player/f_player_attack_sheet.png"))
        player.x, player.y = position
        story = StoryManager(flags)
        inventory = _new_inventory()
        if checkpoint_id in {"chapter1_d", "chapter1_e", "chapter1_f", "chapter1_g"}:
            add_inventory_item(inventory, quest_item("escort_token"))
        if checkpoint_id in {"chapter1_f", "chapter1_g"}:
            add_inventory_item(inventory, quest_item("namar_order_copy"))
        region = build_region(region_id)
        story.apply_to_region(region)
        if region_id == "watchpost":
            player.x, player.y = region.get("spawn", {}).get("old_road", (player.x, player.y))
        enemies = spawn_enemies(region)
        if region_id == "archive":
            from story.archive import spawn_pending as archive_spawn
            enemies = archive_spawn(region, story)
    return CheckpointRuntime(
        player=player, inventory=inventory, quests=QuestManager(), story=story,
        region_id=region_id, region=region, enemies=enemies, narrative=None,
        opened_chests=set())


def create_checkpoint(checkpoint_id, *, load, build_region, spawn_enemies,
                      restore_resident, opening_sequence):
    """Construct one complete, self-contained story state without touching saves."""
    if checkpoint_id not in {entry[0] for entry in CHECKPOINTS[:-1]}:
        raise ValueError(f"Checkpoint desconhecido: {checkpoint_id}")

    if checkpoint_id in {"chapter2_part_a", "chapter2_part_b"}:
        from story.chapter2 import DUNGEON_REGIONS, ENTER_FLAGS, spawn_pending

        player = Player(load("assets/player/f_player_sheet.png"),
                        load("assets/player/f_player_attack_sheet.png"))
        region_id = "forgotten_route" if checkpoint_id == "chapter2_part_a" else DUNGEON_REGIONS[0]
        position = (120, 575) if checkpoint_id == "chapter2_part_a" else (1024, 940)
        flags = {
            "chapter1_completed": True,
            "chapter2_started": True,
            "chapter2_departure_seen": True,
            "chapter2_title_seen": True,
            "chapter2_part_a_completed": checkpoint_id == "chapter2_part_b",
            "chapter2_part_b_started": checkpoint_id == "chapter2_part_b",
            ("route_entered" if checkpoint_id == "chapter2_part_a" else ENTER_FLAGS[region_id]): True,
        }
        story = StoryManager(flags)
        region = build_region(region_id)
        story.apply_to_region(region)
        enemies = spawn_pending(region, story, spawn_enemies)
        return CheckpointRuntime(
            player=player, inventory=_new_inventory(), quests=QuestManager(),
            story=story, region_id=region_id, region=region, enemies=enemies,
            narrative=None, opened_chests=set())
    if checkpoint_id.startswith("chapter1_") or checkpoint_id == "chapter2_iriel":
        return _story_checkpoint(checkpoint_id, load=load,
                                 build_region=build_region, spawn_enemies=spawn_enemies)

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
        self.scroll_offset = 0
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
        if event.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
            visible_count = 9
            self.scroll_offset = min(self.scroll_offset, max(0, len(CHECKPOINTS) - visible_count))
            if self.selected_index < self.scroll_offset:
                self.scroll_offset = self.selected_index
            elif self.selected_index >= self.scroll_offset + visible_count:
                self.scroll_offset = self.selected_index - visible_count + 1
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
        visible_count = min(9, len(CHECKPOINTS))
        panel_height = 104 + visible_count * 34
        panel = pygame.Rect(width // 2 - 238, height // 2 - panel_height // 2,
                            476, panel_height)
        shade = pygame.Surface((width, height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 145))
        surface.blit(shade, (0, 0))
        pygame.draw.rect(surface, (29, 35, 40), panel, border_radius=8)
        pygame.draw.rect(surface, (174, 157, 117), panel, 2, border_radius=8)
        title = pygame.font.Font(None, 30).render(
            "ATALHOS DE DEBUG", True, (239, 225, 188))
        surface.blit(title, (panel.x + 24, panel.y + 18))
        font = pygame.font.Font(None, 23)
        visible = CHECKPOINTS[self.scroll_offset:self.scroll_offset + visible_count]
        for row, (_, label, _) in enumerate(visible):
            index = self.scroll_offset + row
            y = panel.y + 62 + row * 34
            if index == self.selected_index:
                pygame.draw.rect(surface, (71, 78, 76),
                                 (panel.x + 15, y - 4, panel.width - 30, 31),
                                 border_radius=4)
            color = (250, 237, 204) if index == self.selected_index else (205, 207, 198)
            surface.blit(font.render(label, True, color), (panel.x + 27, y))
        hint = pygame.font.Font(None, 18).render(
            "↑/↓ navegar lista   Enter escolher   Esc fechar", True, (179, 185, 183))
        surface.blit(hint, (panel.x + 24, panel.bottom - 27))
