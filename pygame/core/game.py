"""Application coordinator for the O Vale game loop."""
import pygame

from core.assets import load
from core.camera import camera_for
from core.config import FPS, VIEW, WINDOW
from core.input_handler import InputHandler
from entities.enemy import Enemy
from entities.npc import nearest
from entities.player import Player
from systems.dialogue import DialogueBox, DialogueSystem
from systems.combat import CombatSystem
from systems.equipment import item
from systems.inventory import add_inventory_item, apply_inventory_action
from systems.items import consumable
from systems.quest import QuestManager
from story.fade import FadeOverlay
from story.prologue import opening_sequence
from story.arrival_scene import ArrivalScene, restore_resident
from story.story_manager import StoryManager
from ui import defeat_screen as game_over
from ui.character_menu import attribute_key_at
from ui.damage_number import DamageNumber
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
        pygame.init(); pygame.display.set_caption("O Vale RPG | v0.13")
        screen = pygame.display.set_mode(WINDOW); canvas = pygame.Surface(VIEW); clock = pygame.time.Clock()
        player = Player(load("assets/player/f_player_sheet.png"), load("assets/player/f_player_attack_sheet.png"))
        story = StoryManager({
            "woke_up": False,
            "saw_silhouette": False,
            "slime_quest_started": False,
        })
        narrative = opening_sequence()
        transition_fade = FadeOverlay()
        area_transition = None
        arrival_scene = None
        current_region = "home"
        region = build_region(current_region)
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
        autosave_allowed = True
        intro_autosave_allowed = not save_manager.SAVE_PATH.exists()
        if save_manager.SAVE_PATH.exists():
            try:
                save_manager.read_save(save_manager.SAVE_PATH)
            except save_manager.SaveError:
                autosave_allowed = False
                quest_manager.notice = "Save inválido encontrado. Autosave pausado; F5 para substituir."
                quest_manager.notice_timer = 360

        def load_last_save():
            nonlocal player, inventory, quest_manager, current_region, region, enemies
            nonlocal drops, opened_desert_chests, damage_numbers, hitstop_frames
            nonlocal dialogue, ui_mode, inventory_ui, autosave_allowed, game_over_screen
            nonlocal story, narrative, arrival_scene
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
            player, inventory, quest_manager = loaded.player, loaded.inventory, loaded.quests
            current_region, region, enemies = loaded.region_id, loaded.region, loaded.enemies
            story = loaded.story
            arrival_scene = None
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
            drops, opened_desert_chests = loaded.drops, loaded.opened_chests
            damage_numbers = []
            hitstop_frames = 0
            dialogue.npc = None
            ui_mode = None
            inventory_ui = {"tab": "TODOS", "selected": None, "consumable_cooldown": 0}
            autosave_allowed = True
            game_over_screen = None
            quest_manager.notice = "Jogo carregado."
            quest_manager.notice_timer = 180
            return True

        def continue_after_death():
            nonlocal region, enemies, damage_numbers, hitstop_frames, ui_mode
            nonlocal game_over_screen, inventory_ui
            if (current_region == "forest" and quest_manager.forest_event_started
                    and not quest_manager.forest_boss_defeated):
                region, enemies = reset_forest_boss_encounter()
            restore_player_after_death(player, current_region, region, enemies)
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

        running = True
        while running:
            delta_ms = clock.tick(FPS)
            autosave_pending = False
            if narrative is not None and narrative.active:
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
                    if (source == "home" and current_region == "village"
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
                if narrative is not None and narrative.active:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                        if narrative.update(sum(beat.duration_ms for beat in narrative.beats)):
                            autosave_pending |= complete_opening()
                    continue
                if area_transition is not None:
                    if event.type == pygame.QUIT:
                        running = False
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
                    if player.hp <= 0:
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
                    if dialogue.active:
                        closing_target = dialogue.npc
                        quest_state = quest_manager.get("forest_trouble").state
                        closed = dialogue_system.advance(dialogue, quest_manager, inventory)
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
                            if getattr(target, "transition_on_interact", False):
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
                elif command.name == "toggle_character":
                    ui_mode = None if ui_mode == "character" else "character"
                elif command.name == "toggle_inventory":
                    ui_mode = None if ui_mode == "inventory" else "inventory"
                elif command.name == "toggle_debug":
                    debug = not debug
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
            elif arrival_scene is not None and arrival_scene.active:
                if arrival_scene.update(delta_ms, dialogue, story):
                    autosave_pending |= complete_arrival()
            elif game_over_screen is not None:
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
                for feedback in combat_frame.feedback:
                    damage_numbers.append(DamageNumber(
                        feedback.text, *feedback.position, feedback.color, feedback.critical))
                if combat_frame.player_defeated and game_over_screen is None:
                    game_over_screen = game_over.GameOverScreen()
                    ui_mode = None
                    dialogue.npc = None
                    hitstop_frames = 0
                for destination, exit_rect in (region["exits"].items() if player.hp > 0 else ()):
                    if player.hitbox.colliderect(exit_rect):
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
                        previous_region = current_region
                        current_region = transition.region_id
                        region, enemies = transition.region, transition.enemies
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
            if autosave_pending and autosave_allowed and player.hp > 0 and game_over_screen is None:
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
                transition_fade=transition_fade, arrival_scene=arrival_scene)
            pygame.transform.scale(canvas, WINDOW, screen); pygame.display.flip()
        pygame.quit(); return 0
