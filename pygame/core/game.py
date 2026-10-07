"""Application coordinator for the O Vale game loop."""
import pygame

from core.assets import load
from core.camera import camera_for
from core.config import FPS, VIEW, WINDOW
from core.debug_checkpoints import DebugCheckpointMenu, create_checkpoint
from core.input_handler import InputHandler
from entities.enemy import Enemy
from entities.npc import nearest
from entities.player import Player
from systems.dialogue import DialogueBox, DialogueSystem
from systems.combat import CombatSystem
from systems import red_officer_encounter
from systems.equipment import item
from systems.inventory import add_inventory_item, apply_inventory_action
from systems.items import consumable
from systems.quest import QuestManager
from story.fade import FadeOverlay
from story.prologue import opening_sequence
from story.arrival_scene import ArrivalScene, restore_resident
from story.alden_scene import interact_with_alden
from story.house_memory import HouseMemoryScene
from story.blue_march import BlueMarchScene
from story.forest_battle import (
    InsigniaMemoryScene, RedAmbushScene, spawn_red_group,
)
from story.forest_confrontation import RedOfficerScene
from story.prologue_3c import Prologue3CScene
from story.chapter1_return import Chapter1ReturnScene, interact_with_returned_alden
from story.old_road import moment_at, complete_clue, threatened
from story import watchpost as post_story
from story import edrin_encounter as edrin_story
from story.story_manager import StoryManager
from ui import defeat_screen as game_over
from ui.character_menu import attribute_key_at
from ui.damage_number import DamageNumber
from ui.debug_overlay import draw_debug_overlay
from ui.game_renderer import GameRenderer
from ui.inventory_menu import handle_inventory_click
from world.respawn import restore_player_after_death
from world.world_manager import WorldManager
import save_manager


class Game:
    def __init__(self, restore_player=restore_player_after_death):
        self.restore_player_after_death = restore_player

    def run(self):
        self.world = WorldManager.for_game(load)
        combat = CombatSystem(load)
        renderer = GameRenderer()
        build_region = self.world.build_region
        spawn_enemies = self.world.spawn_enemies
        reset_forest_boss_encounter = self.world.reset_forest_boss_encounter
        restore_player_after_death = self.restore_player_after_death
        pygame.init(); pygame.display.set_caption("O Vale RPG | v0.32")
        screen = pygame.display.set_mode(WINDOW); canvas = pygame.Surface(VIEW); clock = pygame.time.Clock()
        player = Player(load("assets/player/f_player_sheet.png"),
                        load("assets/player/f_player_attack_sheet.png"))
        story = StoryManager({
            "woke_up": False,
            "saw_silhouette": False,
            "slime_quest_started": False,
            "blue_army_departed": False,
            "forest_massacre_discovered": False,
            "red_insignia_found": False,
            "red_officer_met": False,
            "red_officer_memory_seen": False,
            "red_officer_escaped": False,
            "prologue_completed": False,
            "forest_battle_progress": 0,
        })
        narrative = opening_sequence()
        transition_fade = FadeOverlay()
        area_transition = None
        arrival_scene = None
        alden_scene = None
        house_memory_scene = None
        blue_march_scene = None
        forest_ambush_scene = None
        insignia_memory_scene = None
        red_officer_scene = None
        prologue_3c_scene = None
        chapter1_return_scene = None
        old_road_scene = None
        watchpost_scene = None
        edrin_scene = None
        prologue_end_card = False
        current_region = "home"
        region = build_region(current_region)
        story.apply_to_region(region)
        player.x, player.y = 512, 288
        enemies = spawn_enemies(region)
        drops = []
        damage_numbers = []
        font = pygame.font.Font(None, 22); title_font = pygame.font.Font(None, 30)
        inventory = [consumable("potion", 3), consumable("ether", 2), consumable("herb", 5), item("iron_blade"), item("reinforced_leather")]
        ui_mode = None
        dialogue = DialogueBox()
        dialogue_system = DialogueSystem()
        quest_manager = QuestManager()
        opened_desert_chests = set()
        inventory_ui = {"tab": "TODOS", "selected": None, "consumable_cooldown": 0}
        debug = False
        hitstop_frames = 0
        game_over_screen = None
        input_handler = InputHandler()
        checkpoint_menu = DebugCheckpointMenu()
        debug_session_active = False
        autosave_allowed = True
        intro_autosave_allowed = not save_manager.SAVE_PATH.exists()
        if save_manager.SAVE_PATH.exists():
            try:
                save_manager.read_save(save_manager.SAVE_PATH)
            except save_manager.SaveError:
                autosave_allowed = False
                quest_manager.notice = "Save inválido encontrado. Autosave pausado; F5 para substituir."
                quest_manager.notice_timer = 360

        def apply_story_region(region_id, story_region, region_enemies):
            if region_id == "pursuit":
                story.set("pursuit_entered")
            if region_id == "watchpost":
                story.set("watchpost_entered")
                region_enemies = [enemy for enemy in region_enemies
                                  if not story.get(f"watchpost_enemy_{enemy.watchpost_id}_defeated")]
            if region_id == "old_road":
                story.set("old_road_entered")
                region_enemies = [enemy for enemy in region_enemies
                                  if not story.get(f"road_enemy_{enemy.road_id}_defeated")]
            if region_id == "village" and story.get("slime_quest_started"):
                restore_resident(story_region, load("assets/npc/civilian_customer.png"))
            story.apply_to_region(story_region)
            if (region_id == "forest" and story.get("blue_army_departed")
                    and not quest_manager.forest_event_started):
                if story.get("red_insignia_found"):
                    return []
                progress = story.get("forest_battle_progress", 0)
                if progress % 2:
                    return spawn_red_group(progress // 2, story_region, load, story)
                return []
            return region_enemies

        def spawn_forest_red_group(index):
            return spawn_red_group(index, region, load, story)

        def load_last_save():
            nonlocal player, inventory, quest_manager, current_region, region, enemies
            nonlocal drops, opened_desert_chests, damage_numbers, hitstop_frames
            nonlocal dialogue, ui_mode, inventory_ui, autosave_allowed, game_over_screen
            nonlocal story, narrative, arrival_scene, alden_scene, house_memory_scene
            nonlocal blue_march_scene
            nonlocal forest_ambush_scene, insignia_memory_scene
            nonlocal red_officer_scene, prologue_3c_scene, prologue_end_card
            nonlocal chapter1_return_scene
            nonlocal old_road_scene
            nonlocal watchpost_scene, edrin_scene
            nonlocal area_transition, transition_fade
            if debug_session_active:
                quest_manager.notice = "Load desativado durante checkpoints de debug."
                quest_manager.notice_timer = 180
                return False
            try:
                loaded = save_manager.load_game(
                    save_manager.SAVE_PATH,
                    lambda: Player(player.idle, player.attack_sheet),
                    build_region, spawn_enemies,
                    lambda: Enemy("forest_guardian", (1300, 430), load, seed=77))
            except save_manager.MissingSaveError:
                quest_manager.notice = "Nenhum save encontrado."
                quest_manager.notice_timer = 180
                return False
            except save_manager.SaveError:
                autosave_allowed = False
                quest_manager.notice = "Save inválido ou corrompido; jogo atual preservado."
                quest_manager.notice_timer = 180
                return False
            red_officer_encounter.stop(region, enemies)
            player, inventory, quest_manager = loaded.player, loaded.inventory, loaded.quests
            current_region, region, enemies = loaded.region_id, loaded.region, loaded.enemies
            story = loaded.story
            arrival_scene = None
            alden_scene = None
            house_memory_scene = None
            blue_march_scene = None
            forest_ambush_scene = None
            insignia_memory_scene = None
            red_officer_scene = None
            prologue_3c_scene = None
            chapter1_return_scene = None
            old_road_scene = None
            watchpost_scene = None
            edrin_scene = None
            prologue_end_card = False
            area_transition = None
            transition_fade = FadeOverlay()
            if current_region == "village" and story.get("slime_quest_started"):
                restore_resident(region, load("assets/npc/civilian_customer.png"))
            if not story.get("woke_up"):
                current_region = "home"
                region = build_region(current_region)
                enemies = []
                player.x, player.y = 512, 288
                narrative = opening_sequence()
            else:
                narrative = None
            enemies = apply_story_region(current_region, region, enemies)
            drops, opened_desert_chests = loaded.drops, loaded.opened_chests
            damage_numbers = []
            hitstop_frames = 0
            dialogue.npc = None
            ui_mode = None
            inventory_ui = {"tab": "TODOS", "selected": None, "consumable_cooldown": 0}
            autosave_allowed = True
            game_over_screen = None
            quest_manager.notice = ("[E] Enfrentar o Oficial Vermelho."
                                    if story.get("red_officer_boss_ready") and not story.get("red_officer_defeated")
                                    else "Jogo carregado.")
            quest_manager.notice_timer = 180
            begin_chapter1()
            return True

        def activate_debug_checkpoint(checkpoint_id):
            nonlocal player, inventory, quest_manager, story, current_region, region, enemies
            nonlocal narrative, opened_desert_chests, drops, damage_numbers
            nonlocal dialogue, ui_mode, inventory_ui, hitstop_frames, game_over_screen
            nonlocal area_transition, transition_fade, arrival_scene, alden_scene
            nonlocal house_memory_scene, blue_march_scene, forest_ambush_scene
            nonlocal insignia_memory_scene, red_officer_scene, prologue_3c_scene, autosave_allowed
            nonlocal debug_session_active
            nonlocal prologue_end_card
            nonlocal chapter1_return_scene
            nonlocal old_road_scene
            nonlocal watchpost_scene, edrin_scene
            preset = create_checkpoint(
                checkpoint_id, load=load, build_region=build_region,
                spawn_enemies=spawn_enemies, restore_resident=restore_resident,
                opening_sequence=opening_sequence)
            player, inventory, quest_manager = preset.player, preset.inventory, preset.quests
            story = preset.story
            current_region, region, enemies = preset.region_id, preset.region, preset.enemies
            narrative = preset.narrative
            opened_desert_chests = preset.opened_chests
            drops, damage_numbers = [], []
            dialogue = DialogueBox()
            ui_mode = None
            inventory_ui = {"tab": "TODOS", "selected": None, "consumable_cooldown": 0}
            hitstop_frames = 0
            game_over_screen = None
            area_transition = None
            transition_fade = FadeOverlay()
            arrival_scene = alden_scene = house_memory_scene = None
            blue_march_scene = forest_ambush_scene = None
            insignia_memory_scene = red_officer_scene = prologue_3c_scene = None
            prologue_end_card = False
            chapter1_return_scene = None
            old_road_scene = None
            watchpost_scene = None
            edrin_scene = None
            checkpoint_menu.checkpoint_id = checkpoint_id
            checkpoint_menu.close()
            debug_session_active = True
            autosave_allowed = False

        def begin_officer_battle():
            nonlocal enemies
            boss = red_officer_encounter.start(region, story, load)
            if boss is not None:
                enemies = [boss]
                return True
            return False

        def continue_after_death():
            nonlocal region, enemies, damage_numbers, hitstop_frames, ui_mode
            nonlocal game_over_screen, inventory_ui
            retry_officer = (current_region == "forest" and story.get("red_officer_boss_ready")
                             and not story.get("red_officer_defeated"))
            if retry_officer:
                region = build_region("forest")
                story.apply_to_region(region)
                region["spawn"]["village"] = (1460, 555)
                enemies = []
            elif (current_region == "forest" and quest_manager.forest_event_started
                    and not quest_manager.forest_boss_defeated):
                region, enemies = reset_forest_boss_encounter()
            restore_player_after_death(player, current_region, region, enemies)
            if retry_officer:
                begin_officer_battle()
            player.sp_idle_frames = 0
            damage_numbers = []
            hitstop_frames = 0
            ui_mode = None
            dialogue.npc = None
            inventory_ui["consumable_cooldown"] = 0
            game_over_screen = None

        def begin_area_transition(destination):
            nonlocal area_transition
            if area_transition is None:
                area_transition = {
                    "destination": destination,
                    "source": current_region,
                    "phase": "out",
                }
                transition_fade.start("out", 320)

        def complete_opening():
            nonlocal narrative
            story.set("woke_up", True)
            narrative = None
            return intro_autosave_allowed

        def complete_arrival():
            nonlocal arrival_scene
            quest = quest_manager.get("forest_trouble")
            if quest.state == "AVAILABLE":
                quest_manager.accept(quest.id)
            story.set("slime_quest_started", True)
            quest_manager.notice = (
                "Missão recebida: Problemas na Floresta — "
                f"Derrote 5 Slimes ({quest.progress}/{quest.required})")
            quest_manager.notice_timer = 300
            arrival_scene = None
            return True

        def return_to_village():
            nonlocal current_region, region, enemies, drops, damage_numbers, hitstop_frames
            nonlocal ui_mode, area_transition, transition_fade
            current_region = "village"
            region = build_region(current_region)
            enemies = apply_story_region(current_region, region, [])
            player.x, player.y = region["spawn"]["forest"]
            drops, damage_numbers = [], []
            hitstop_frames = 0
            dialogue.npc = None
            ui_mode = area_transition = None
            transition_fade = FadeOverlay()
            return region

        def begin_chapter1():
            nonlocal chapter1_return_scene
            if (story.get("prologue_completed") and not story.get("chapter1_returned")
                    and chapter1_return_scene is None):
                chapter1_return_scene = Chapter1ReturnScene(
                    player, story, quest_manager, return_to_village)

        running = True
        while running:
            delta_ms = clock.tick(FPS)
            autosave_pending = False
            if narrative is not None and narrative.active and not checkpoint_menu.active:
                if narrative.update(delta_ms):
                    # Never replace an existing adventure just because this
                    # launch began as a fresh game; F5 remains explicit.
                    autosave_pending = complete_opening()
            if area_transition is not None:
                transition_fade.update(delta_ms)
                if area_transition["phase"] == "out" and not transition_fade.active:
                    result = self.world.transition(
                        current_region, area_transition["destination"], quest_manager,
                        opened_desert_chests, save_manager.prepare_region,
                        lambda: Enemy("forest_guardian", (1300, 430), load, seed=77),
                        source_region=region)
                    if result is None or result.blocked:
                        area_transition = None
                        transition_fade.alpha = 0
                    else:
                        current_region = result.region_id
                        region, enemies = result.region, result.enemies
                        enemies = apply_story_region(current_region, region, enemies)
                        if current_region == "village" and story.get("slime_quest_started"):
                            restore_resident(region, load("assets/npc/civilian_customer.png"))
                        drops, damage_numbers = [], []
                        player.x, player.y = result.spawn
                        player.attack_timer = player.attack_cooldown_timer = 0
                        player.dash_timer = player.dash_iframes = 0
                        player.invulnerability_timer = (
                            0 if area_transition["source"] == "home"
                            and current_region == "village" else 30)
                        area_transition["phase"] = "in"
                        transition_fade.start("in", 360)
                elif area_transition["phase"] == "in" and not transition_fade.active:
                    source = area_transition["source"]
                    area_transition = None
                    if source in {"old_road","watchpost","pursuit"} or current_region in {"old_road","watchpost","pursuit"}:
                        autosave_pending = True
                    if (source == "home" and current_region == "village"
                            and story.get("house_searched")
                            and not story.get("blue_army_departed")):
                        blue_march_scene = BlueMarchScene(player, dialogue, load)
                    elif (source == "home" and current_region == "village"
                            and story.get("woke_up")
                            and not story.get("saw_silhouette")):
                        idle_sprite = load("assets/npc/civilian_customer.png")
                        run_sprite = idle_sprite
                        arrival_scene = ArrivalScene(
                            player, region, idle_sprite, run_sprite)
            if inventory_ui["consumable_cooldown"] > 0:
                inventory_ui["consumable_cooldown"] -= 1
            if game_over_screen is not None:
                game_over_screen.update()
            for event in pygame.event.get():
                if checkpoint_menu.active:
                    if event.type == pygame.QUIT:
                        running = False
                    else:
                        action = checkpoint_menu.handle_event(event)
                        if action is not None:
                            action_name, checkpoint_id = action
                            if action_name == "close":
                                ui_mode = None
                            else:
                                activate_debug_checkpoint(checkpoint_id)
                    continue
                if narrative is not None and narrative.active:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                        if narrative.update(sum(beat.duration_ms for beat in narrative.beats)):
                            autosave_pending |= complete_opening()
                    elif (event.type == pygame.KEYDOWN and event.key == pygame.K_F2
                          and checkpoint_menu.enabled):
                        checkpoint_menu.open()
                        ui_mode = "debug_checkpoints"
                    continue
                if area_transition is not None:
                    if event.type == pygame.QUIT:
                        running = False
                    continue
                if chapter1_return_scene is not None and chapter1_return_scene.active:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                        autosave_pending |= chapter1_return_scene.finish()
                        chapter1_return_scene = None
                    continue
                if old_road_scene is not None and old_road_scene.active:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                        autosave_pending |= old_road_scene.finish(story,quest_manager)
                        old_road_scene = None
                    continue
                if edrin_scene is not None and edrin_scene.active:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                        autosave_pending |= edrin_scene.finish()
                        edrin_scene = None
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                        edrin_scene.advance()
                    continue
                if watchpost_scene is not None and watchpost_scene.active:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                        autosave_pending |= watchpost_scene.finish(story,quest_manager)
                        watchpost_scene = None
                    continue
                if arrival_scene is not None and arrival_scene.active:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                        arrival_scene.finish(dialogue, story)
                        autosave_pending |= complete_arrival()
                    elif (event.type == pygame.KEYDOWN and event.key == pygame.K_e
                          and arrival_scene.phase == "dialogue" and dialogue.active):
                        dialogue_system.advance(dialogue, quest_manager, inventory)
                    continue
                if alden_scene is not None and alden_scene.active:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                        autosave_pending |= alden_scene.finish(
                            dialogue, story, quest_manager, inventory)
                        alden_scene = None
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                        alden_scene.advance(dialogue)
                    continue
                if house_memory_scene is not None and house_memory_scene.active:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                        autosave_pending |= house_memory_scene.finish(story, region)
                        house_memory_scene = None
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                        house_memory_scene.advance()
                    continue
                if blue_march_scene is not None and blue_march_scene.active:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                        autosave_pending |= blue_march_scene.finish(story, dialogue)
                        blue_march_scene = None
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                        blue_march_scene.advance()
                    continue
                if forest_ambush_scene is not None and forest_ambush_scene.active:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                        if forest_ambush_scene.finish(dialogue, story):
                            enemies = spawn_forest_red_group(0)
                            autosave_pending = True
                        forest_ambush_scene = None
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                        if forest_ambush_scene.advance():
                            forest_ambush_scene.finish(dialogue, story)
                            enemies = spawn_forest_red_group(0)
                            autosave_pending = True
                            forest_ambush_scene = None
                    continue
                if insignia_memory_scene is not None and insignia_memory_scene.active:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                        autosave_pending |= insignia_memory_scene.finish(story, region)
                        insignia_memory_scene = None
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                        insignia_memory_scene.advance()
                    continue
                if red_officer_scene is not None and red_officer_scene.active:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                        if red_officer_scene.finish():
                            autosave_pending = True
                            begin_officer_battle()
                        red_officer_scene = None
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                        if red_officer_scene.advance():
                            autosave_pending = True
                            begin_officer_battle()
                            red_officer_scene = None
                    continue
                if prologue_3c_scene is not None and prologue_3c_scene.active:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                        if prologue_3c_scene.finish():
                            autosave_pending = True
                            prologue_3c_scene = None
                            begin_chapter1()
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                        if prologue_3c_scene.advance():
                            autosave_pending = True
                            prologue_3c_scene = None
                            begin_chapter1()
                    continue
                if prologue_end_card:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_ESCAPE):
                        prologue_end_card = False
                    continue
                command = input_handler.route(
                    event, ui_mode=ui_mode, dialogue=dialogue, player=player,
                    inventory=inventory, inventory_ui=inventory_ui,
                    game_over_screen=game_over_screen, view=VIEW)
                if command is None:
                    continue
                if command.name == "quit":
                    running = False
                elif command.name == "defeat_choice":
                    choice = command.value
                    if choice == "continue":
                        continue_after_death()
                    elif choice == "load":
                        load_last_save()
                        if game_over_screen is not None:
                            game_over_screen.notice = quest_manager.notice
                    elif choice == "quit":
                        running = False
                elif command.name == "save":
                    if debug_session_active:
                        quest_manager.notice = "Save desativado durante checkpoints de debug."
                    elif region.get("boss_battle_active"):
                        quest_manager.notice = "Não é possível salvar durante o confronto."
                    elif player.hp <= 0:
                        quest_manager.notice = "Não é possível salvar após a derrota."
                    else:
                        try:
                            save_manager.save_game(player, inventory, quest_manager, current_region,
                                                   opened_desert_chests, drops, story=story)
                        except save_manager.SaveError:
                            quest_manager.notice = "Não foi possível salvar o jogo."
                        else:
                            autosave_allowed = True
                            quest_manager.notice = "Jogo salvo."
                    quest_manager.notice_timer = 180
                elif command.name == "load":
                    load_last_save()
                elif command.name == "escape":
                    if dialogue.active:
                        dialogue.npc = None
                    elif ui_mode is not None:
                        ui_mode = None
                    else:
                        running = False
                elif command.name == "interact":
                    officer = region.get("red_officer_actor")
                    if (not dialogue.active and ui_mode is None and officer is not None
                            and story.get("red_officer_boss_ready")
                            and not story.get("red_officer_defeated")
                            and (player.x - officer.x) ** 2 + (player.y - officer.y) ** 2 <= 160 ** 2
                            and begin_officer_battle()):
                        continue
                    if dialogue.active:
                        closing_target = dialogue.npc
                        quest_state = quest_manager.get("forest_trouble").state
                        closed = dialogue_system.advance(dialogue, quest_manager, inventory)
                        if closed and current_region == "old_road":
                            autosave_pending |= complete_clue(closing_target,story,region)
                        if closed and current_region == "pursuit":
                            autosave_pending |= edrin_story.complete_trace(closing_target,story)
                        if closed and current_region == "watchpost":
                            autosave_pending |= post_story.complete_evidence(
                                closing_target,player,inventory,story,region,quest_manager)
                        if (quest_state != quest_manager.get("forest_trouble").state
                                and quest_manager.get("forest_trouble").state == "REWARDED"):
                            autosave_pending = True
                        if closed and getattr(closing_target, "transition_to", None):
                            begin_area_transition(closing_target.transition_to)
                    elif ui_mode is None:
                        targets = region.get("npcs", []) + [
                            obj for obj in region.get("interactables", []) if not obj.opened]
                        target = nearest(targets, player, quest_manager)
                        if target is not None:
                            if current_region == "watchpost":
                                if post_story.threatened(player,enemies,region):
                                    quest_manager.notice = "Preciso afastar a ameaça antes de examinar isso."
                                    quest_manager.notice_timer = 120
                                elif post_story.can_examine(player,target,region):
                                    target.begin_interaction(dialogue,player,quest_manager)
                            elif current_region == "old_road" and getattr(target,"story_flag",None):
                                if threatened(player,enemies):
                                    quest_manager.notice = "Preciso de um instante de calma para examinar isso."
                                    quest_manager.notice_timer = 120
                                else:
                                    target.begin_interaction(dialogue,player,quest_manager)
                            elif (current_region == "forest" and target.uid == "battlefield_body"
                                    and not story.get("forest_massacre_discovered")):
                                story.set("forest_massacre_discovered")
                                region["interactables"] = [
                                    obj for obj in region["interactables"]
                                    if obj.uid != "battlefield_body"]
                                target.begin_interaction(dialogue, player, quest_manager)
                                autosave_pending = True
                            elif (current_region == "forest" and target.uid == "red_insignia"
                                  and not story.get("red_insignia_found")):
                                region["interactables"] = [
                                    obj for obj in region["interactables"]
                                    if obj.uid != "red_insignia"]
                                insignia_memory_scene = InsigniaMemoryScene(
                                    player, target.image, dialogue, load)
                            elif current_region == "village" and target.uid == "alden":
                                if story.get("chapter1_returned"):
                                    alden_scene = interact_with_returned_alden(
                                        target, player, dialogue, story, region)
                                else:
                                    alden_scene = interact_with_alden(
                                        target, player, dialogue, quest_manager, story)
                            elif (current_region == "home" and target.uid == "broken_pendant"
                                  and story.get("house_investigation_unlocked")
                                  and not story.get("house_searched")):
                                story.set("pendant_found")
                                region["interactables"] = [
                                    obj for obj in region["interactables"]
                                    if obj.uid != "broken_pendant"]
                                house_memory_scene = HouseMemoryScene(
                                    "pendant", player, target.image, dialogue)
                            elif (current_region == "home" and target.uid == "second_mug"
                                  and story.get("house_investigation_unlocked")):
                                house_memory_scene = HouseMemoryScene(
                                    "cup", player, target.image, dialogue)
                            elif getattr(target, "transition_on_interact", False):
                                begin_area_transition(target.transition_to)
                            elif hasattr(target, "begin_interaction"):
                                target.begin_interaction(dialogue, player, quest_manager)
                            elif not target.opened:
                                target.opened = True
                                opened_desert_chests.add(target.uid)
                                loot = target.loot
                                add_inventory_item(inventory, loot)
                                quest_manager.notice = f"Baú: {loot['amount']}x {loot['name']}"
                                quest_manager.notice_timer = 160
                                autosave_pending |= current_region == "old_road"
                elif command.name == "toggle_character":
                    ui_mode = None if ui_mode == "character" else "character"
                elif command.name == "toggle_inventory":
                    ui_mode = None if ui_mode == "inventory" else "inventory"
                elif command.name == "toggle_debug":
                    debug = not debug
                elif command.name == "debug_checkpoints":
                    if (checkpoint_menu.enabled and ui_mode is None and not dialogue.active
                            and area_transition is None and game_over_screen is None):
                        checkpoint_menu.open()
                        ui_mode = "debug_checkpoints"
                elif command.name == "spend_stat":
                    if command.value:
                        player.spend_stat(command.value)
                elif command.name == "use_item":
                    _, notice = apply_inventory_action(
                        command.value, inventory, player, inventory_ui)
                    quest_manager.notice, quest_manager.notice_timer = notice, 150
                elif command.name == "attack":
                    player.attack()
                elif command.name == "dash":
                    player.start_dash(pygame.key.get_pressed())
            if area_transition is not None:
                pass
            elif chapter1_return_scene is not None and chapter1_return_scene.active:
                if chapter1_return_scene.update(delta_ms):
                    autosave_pending = True
                    chapter1_return_scene = None
                elif chapter1_return_scene.autosave_requested:
                    autosave_pending = True
                    chapter1_return_scene.autosave_requested = False
            elif old_road_scene is not None and old_road_scene.active:
                if old_road_scene.update(delta_ms,story,quest_manager):
                    autosave_pending = True
                    old_road_scene = None
            elif edrin_scene is not None and edrin_scene.active:
                if edrin_scene.update(delta_ms):
                    autosave_pending = True
                    edrin_scene = None
                elif edrin_scene.autosave_requested:
                    autosave_pending = True
                    edrin_scene.autosave_requested = False
            elif watchpost_scene is not None and watchpost_scene.active:
                if watchpost_scene.update(delta_ms,story,quest_manager):
                    autosave_pending = True
                    watchpost_scene = None
            elif arrival_scene is not None and arrival_scene.active:
                if arrival_scene.update(delta_ms, dialogue, story):
                    autosave_pending |= complete_arrival()
            elif alden_scene is not None and alden_scene.active:
                if alden_scene.update(delta_ms, dialogue, story, quest_manager, inventory):
                    autosave_pending = True
                    alden_scene = None
            elif house_memory_scene is not None and house_memory_scene.active:
                if house_memory_scene.update(delta_ms, story, region):
                    autosave_pending = True
                    house_memory_scene = None
            elif blue_march_scene is not None and blue_march_scene.active:
                if blue_march_scene.update(delta_ms, story):
                    autosave_pending = True
                    blue_march_scene = None
            elif forest_ambush_scene is not None and forest_ambush_scene.active:
                pass
            elif insignia_memory_scene is not None and insignia_memory_scene.active:
                if insignia_memory_scene.update(delta_ms, story, region):
                    autosave_pending = True
                    insignia_memory_scene = None
            elif red_officer_scene is not None and red_officer_scene.active:
                if red_officer_scene.update(delta_ms):
                    autosave_pending = True
                    begin_officer_battle()
                    red_officer_scene = None
            elif prologue_3c_scene is not None and prologue_3c_scene.active:
                if prologue_3c_scene.update(delta_ms):
                    autosave_pending = True
                    prologue_3c_scene = None
                    begin_chapter1()
                elif prologue_3c_scene.autosave_requested:
                    autosave_pending = True
                    prologue_3c_scene.autosave_requested = False
            elif game_over_screen is not None:
                pass
            elif prologue_end_card:
                pass
            elif hitstop_frames > 0:
                hitstop_frames -= 1
            elif (ui_mode is None and not dialogue.active and player.hp > 0
                  and (narrative is None or not narrative.active)):
                combat_frame = combat.update(
                    player, current_region, region, enemies, drops, inventory,
                    quest_manager, hitstop_frames)
                enemies, drops = combat_frame.enemies, combat_frame.drops
                hitstop_frames = combat_frame.hitstop_frames
                autosave_pending |= combat_frame.autosave_pending
                for soldier_id in combat_frame.defeated_soldiers:
                    story.record_soldier_defeat(soldier_id)
                    autosave_pending = True
                for road_id in combat_frame.defeated_road_enemies:
                    story.set(f"road_enemy_{road_id}_defeated")
                    autosave_pending = True
                for post_id in combat_frame.defeated_watchpost_enemies:
                    story.set(f"watchpost_enemy_{post_id}_defeated")
                    autosave_pending = True
                for feedback in combat_frame.feedback:
                    damage_numbers.append(DamageNumber(
                        feedback.text, *feedback.position, feedback.color, feedback.critical))
                if red_officer_encounter.conclude(region, story, enemies):
                    autosave_pending = True
                if (current_region == "forest" and story.get("red_officer_defeated")
                        and not story.get("prologue_completed")
                        and prologue_3c_scene is None and not enemies
                        and player.hp > 0 and game_over_screen is None):
                    prologue_3c_scene = Prologue3CScene(
                        player, story, region, dialogue, load)
                if combat_frame.player_defeated and game_over_screen is None:
                    red_officer_encounter.stop(region, enemies)
                    game_over_screen = game_over.GameOverScreen()
                    ui_mode = None
                    dialogue.npc = None
                    hitstop_frames = 0
                if (current_region == "forest" and story.get("blue_army_departed")
                        and not story.get("red_insignia_found")
                        and not quest_manager.forest_event_started
                        and player.hp > 0 and game_over_screen is None):
                    progress = story.get("forest_battle_progress", 0)
                    if progress % 2 and not enemies:
                        story.set_forest_battle_progress(progress + 1)
                        story.apply_to_region(region)
                        autosave_pending = True
                        progress += 1
                    if progress < 10 and progress % 2 == 0:
                        group_index = progress // 2
                        group = region["red_encounter_groups"][group_index]
                        trigger_x = sum(position[0] for position in group) / len(group)
                        trigger_y = sum(position[1] for position in group) / len(group)
                        if abs(player.x - trigger_x) ** 2 + abs(player.y - trigger_y) ** 2 <= 158 ** 2:
                            if group_index == 0:
                                forest_ambush_scene = RedAmbushScene(
                                    player, dialogue, load, group,
                                    actors=spawn_forest_red_group(0))
                            else:
                                story.set_forest_battle_progress(progress + 1)
                                enemies = spawn_forest_red_group(group_index)
                                autosave_pending = True
                if (current_region == "forest" and story.wounded_commander_ready
                        and not story.get("red_officer_boss_ready") and not enemies
                        and player.hp > 0 and game_over_screen is None):
                    trigger_x, trigger_y = region["red_officer_trigger"]
                    if ((player.x - trigger_x) ** 2 + (player.y - trigger_y) ** 2
                            <= 108 ** 2):
                        red_officer_scene = RedOfficerScene(
                            player, dialogue, story, region, load)
                if current_region == "old_road" and player.hp > 0 and game_over_screen is None:
                    old_road_scene = moment_at(player,region,story,enemies)
                if current_region == "watchpost" and player.hp > 0 and game_over_screen is None:
                    watchpost_scene = post_story.moment_at(player,region,story,enemies,load)
                if current_region == "pursuit" and player.hp > 0 and game_over_screen is None:
                    edrin_scene = edrin_story.encounter_at(player,region,story,dialogue,quest_manager,load)
                for destination, exit_rect in (region["exits"].items()
                                               if player.hp > 0 and old_road_scene is None and watchpost_scene is None and edrin_scene is None else ()):
                    if player.hitbox.colliderect(exit_rect):
                        if ((current_region,destination) in {("village","old_road"),
                                ("old_road","village"),("old_road","watchpost"),("watchpost","old_road"),
                                ("watchpost","pursuit"),("pursuit","watchpost")}):
                            begin_area_transition(destination)
                            break
                        transition = self.world.transition(
                            current_region, destination, quest_manager,
                            opened_desert_chests, save_manager.prepare_region,
                            lambda: Enemy("forest_guardian", (1300, 430), load, seed=77),
                            source_region=region)
                        if transition is None:
                            continue
                        if transition.notice:
                            quest_manager.notice = transition.notice
                            quest_manager.notice_timer = 150
                        if transition.blocked or transition.region_id == current_region:
                            continue
                        red_officer_encounter.stop(region, enemies)
                        previous_region = current_region
                        current_region = transition.region_id
                        region, enemies = transition.region, transition.enemies
                        enemies = apply_story_region(current_region, region, enemies)
                        if current_region == "village" and story.get("slime_quest_started"):
                            restore_resident(region, load("assets/npc/civilian_customer.png"))
                        drops = []
                        damage_numbers = []
                        player.x, player.y = transition.spawn
                        player.attack_timer = 0
                        player.attack_cooldown_timer = 0
                        player.dash_timer = player.dash_iframes = 0
                        player.invulnerability_timer = 30
                        autosave_pending = True
                        break
            if (autosave_pending and autosave_allowed and not debug_session_active
                    and player.hp > 0 and game_over_screen is None):
                try:
                    save_manager.save_game(player, inventory, quest_manager, current_region,
                                           opened_desert_chests, drops, story=story)
                except save_manager.SaveError:
                    quest_manager.notice, quest_manager.notice_timer = "Autosave falhou.", 180
            camera = camera_for(player, region["terrain"].get_size())
            quest_manager.update()
            renderer.draw(
                canvas, region=region, player=player, enemies=enemies, drops=drops,
                camera=camera, debug=debug, damage_numbers=damage_numbers,
                hitstop_frames=hitstop_frames, font=font, title_font=title_font,
                dialogue=dialogue, quest_manager=quest_manager, ui_mode=ui_mode,
                inventory=inventory, inventory_ui=inventory_ui,
                game_over_screen=game_over_screen, narrative=narrative,
                transition_fade=transition_fade, arrival_scene=arrival_scene,
                alden_scene=alden_scene, house_memory_scene=house_memory_scene,
                blue_march_scene=blue_march_scene,
                forest_ambush_scene=forest_ambush_scene,
                insignia_memory_scene=insignia_memory_scene,
                red_officer_scene=red_officer_scene,
                prologue_3c_scene=prologue_3c_scene, story=story,
                chapter1_return_scene=chapter1_return_scene,
                old_road_scene=old_road_scene,
                watchpost_scene=watchpost_scene, edrin_scene=edrin_scene,
                prologue_end_card=prologue_end_card)
            if debug and not (chapter1_return_scene is not None and chapter1_return_scene.active):
                draw_debug_overlay(
                    canvas, current_region=current_region, region=region,
                    player=player, enemies=enemies, story=story, quests=quest_manager,
                    narrative=narrative,
                    scenes={
                        "arrival_scene": arrival_scene, "alden_scene": alden_scene,
                        "house_memory_scene": house_memory_scene,
                        "blue_march_scene": blue_march_scene,
                        "forest_ambush_scene": forest_ambush_scene,
                        "insignia_memory_scene": insignia_memory_scene,
                        "red_officer_scene": red_officer_scene,
                        "prologue_3c_scene": prologue_3c_scene,
                        "chapter1_return_scene": chapter1_return_scene,
                        "old_road_scene": old_road_scene,
                        "watchpost_scene": watchpost_scene, "edrin_scene": edrin_scene,
                    },
                    dialogue=dialogue, ui_mode=ui_mode,
                    transition_active=area_transition is not None,
                    transition_fade=transition_fade,
                    game_over_screen=game_over_screen,
                    checkpoint_label=(checkpoint_menu.status_label
                                      if debug_session_active else ""))
            checkpoint_menu.draw(canvas)
            pygame.transform.scale(canvas, WINDOW, screen); pygame.display.flip()
        pygame.quit(); return 0
