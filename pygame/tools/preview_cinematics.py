"""Checkpoint-based visual rehearsal. Writes PNGs only; never opens a save."""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from core.assets import load
from core.camera import camera_for
from core.debug_checkpoints import create_checkpoint
from entities.red_officer import RedOfficer
from story.alden_scene import AldenScene
from story.arrival_scene import ArrivalScene, restore_resident
from story.blue_march import BlueMarchScene
from story.forest_battle import RedAmbushScene, InsigniaMemoryScene, spawn_red_group
from story.forest_confrontation import RedOfficerScene
from story.house_memory import HouseMemoryScene
from story.prologue import opening_sequence
from story.prologue_3c import Prologue3CScene
from ui.dialogue_box import DialogueBox
from ui.game_renderer import GameRenderer
from world.world_manager import WorldManager


def run(output, only=None):
    pygame.init()
    pygame.display.set_mode((1, 1))
    output.mkdir(parents=True, exist_ok=True)
    world = WorldManager.for_game(load)
    canvas = pygame.Surface((1024, 576))
    font, title = pygame.font.Font(None, 22), pygame.font.Font(None, 30)
    shots = []

    def checkpoint(name):
        return create_checkpoint(name, load=load, build_region=world.build_region,
                                 spawn_enemies=world.spawn_enemies,
                                 restore_resident=restore_resident,
                                 opening_sequence=opening_sequence)

    def shot(name, state, dialogue=None, **scenes):
        if only and name not in only:
            return
        renderer = GameRenderer()
        for _ in range(36):
            renderer.draw(canvas, region=state.region, player=state.player,
                          enemies=state.enemies, drops=[],
                          camera=camera_for(state.player, state.region['terrain'].get_size()),
                          debug=False, damage_numbers=[], hitstop_frames=1,
                          font=font, title_font=title, dialogue=dialogue or DialogueBox(),
                          quest_manager=state.quests, ui_mode=None,
                          inventory=state.inventory, inventory_ui={}, game_over_screen=None,
                          story=state.story, **scenes)
        pygame.image.save(canvas, output / (name + '.png'))
        shots.append((name, pygame.transform.scale(canvas, (384, 216))))

    home = checkpoint('prologue_2b')
    for label, position in [('home_bed', (512, 274)), ('home_table', (845, 460)),
                            ('home_wall', (525, 84))]:
        home.player.x, home.player.y = position
        shot(label, home)
    home.player.x, home.player.y = 845, 460
    dialogue = DialogueBox()
    letter = next(obj for obj in home.region['interactables'] if obj.uid == 'damaged_letter')
    dialogue.open(letter)
    shot('home_letter', home, dialogue)
    pendant = next(obj for obj in home.region['interactables'] if obj.uid == 'broken_pendant')
    scene = HouseMemoryScene('pendant', home.player, pendant.image, dialogue)
    while scene.sequence is not None:
        scene.update(50, home.story, home.region)
    shot('pendant_memory', home, dialogue, house_memory_scene=scene)
    scene.finish(home.story, home.region)
    scene = HouseMemoryScene('cup', home.player, pendant.image, dialogue)
    scene.update(160, home.story, home.region)
    shot('cup_memory', home, dialogue, house_memory_scene=scene)

    village = checkpoint('prologue_2a')
    for label, position in [('village_square', (1024, 576)), ('village_market', (1350, 575))]:
        village.player.x, village.player.y = position
        shot(label, village)
    village.player.x, village.player.y = 1738, 560
    dialogue = DialogueBox()
    alden = next(npc for npc in village.region['npcs'] if npc.uid == 'alden')
    scene = AldenScene(alden, village.player, dialogue)
    shot('alden', village, dialogue, alden_scene=scene)
    scene.finish(dialogue, village.story, village.quests, village.inventory)
    village.player.x, village.player.y = 540, 490
    scene = BlueMarchScene(village.player, dialogue, load)
    while scene.phase == 'approach':
        scene.update(50, village.story)
    shot('march', village, dialogue, blue_march_scene=scene)
    dialogue.index = 5
    shot('march_veiled', village, dialogue, blue_march_scene=scene)
    scene.finish(village.story, dialogue)

    arrival = checkpoint('normal')
    arrival.region = world.build_region('village')
    arrival.enemies = []
    arrival.player.x, arrival.player.y = 540, 490
    scene = ArrivalScene(arrival.player, arrival.region,
                         load('assets/npc/civilian_customer.png'),
                         load('assets/npc/civilian_customer.png'))
    for target in ('silhouette', 'near', 'dialogue'):
        while scene.phase != target:
            scene.update(50, dialogue, arrival.story)
        shot('arrival_' + target, arrival, dialogue, arrival_scene=scene)
    waking = checkpoint('normal')
    opening = waking.narrative
    while opening.current.text != 'Quem sou eu?':
        opening.update(50)
    opening.update(350)
    shot('awakening', waking, narrative=opening)

    forest = checkpoint('prologue_2d')
    forest.player.x, forest.player.y = 360, 575
    shot('battlefield', forest)
    dialogue = DialogueBox()
    contacts = spawn_red_group(0, forest.region, load, forest.story)
    scene = RedAmbushScene(forest.player, dialogue, load,
                           forest.region['red_encounter_groups'][0], contacts)
    shot('red_contact', forest, dialogue, forest_ambush_scene=scene)
    scene.finish(dialogue, forest.story)
    scene = InsigniaMemoryScene(forest.player,
                               forest.region['forest_battlefield_interactables']['insignia'].image,
                               dialogue, load)
    while scene.sequence is not None:
        scene.update(50, forest.story, forest.region)
    shot('insignia_memory', forest, dialogue, insignia_memory_scene=scene)

    forest = checkpoint('prologue_2e')
    forest.player.x, forest.player.y = 1380, 550
    dialogue = DialogueBox()
    scene = RedOfficerScene(forest.player, dialogue, forest.story, forest.region, load)
    captured = set()
    for _ in range(1500):
        if not scene.active:
            break
        key = (scene.phase, scene.continuation_index)
        label = {'revelation': 'commander', 'officer_inspection': 'officer_entry',
                 'officer_dialogue': 'officer_met'}.get(scene.phase)
        if scene.phase == 'confrontation' and scene.continuation_index in (3, 7, 12):
            label = 'confrontation_' + str(scene.continuation_index)
        if label and key not in captured:
            shot(label, forest, dialogue, red_officer_scene=scene)
            captured.add(key)
        scene.advance()
        scene.update(50)
    boss = RedOfficer((1250, 548), load, defeat_hp=1)
    forest.enemies = [boss]
    forest.region['scenery'] = [obj for obj in forest.region['scenery']
                                if obj is not forest.region.get('red_officer_actor')]
    forest.region['red_officer_actor'] = boss
    forest.region['boss_battle_active'] = True
    shot('boss', forest)
    boss.receive_hit(boss.max_hp, forest.player.x, forest.player.y)
    forest.story.set('red_officer_defeated')
    forest.enemies = []
    scene = Prologue3CScene(forest.player, forest.story, forest.region, dialogue, load)
    captured = set()
    for _ in range(1500):
        if not scene.active:
            break
        key = (scene.phase, scene.index)
        label = None
        if scene.phase in {'opening', 'memory', 'after_memory', 'epilogue'}:
            label = f'final_{scene.phase}_{scene.index}'
        elif scene.phase == 'flee' and scene.elapsed_ms >= 700:
            label = 'final_escape'
        elif scene.phase == 'epilogue_looks' and scene.elapsed_ms >= 1200:
            label = 'final_battlefield_silence'
        if label and key not in captured:
            shot(label, forest, dialogue, prologue_3c_scene=scene)
            captured.add(key)
        scene.advance()
        scene.update(50)
    shot('end_card', forest, prologue_end_card=True)
    if not shots:
        raise ValueError('No matching preview names')
    sheet = pygame.Surface((1152, ((len(shots) + 2) // 3) * 240))
    sheet.fill((12, 17, 22))
    for i, (label, preview) in enumerate(shots):
        x, y = (i % 3) * 384, (i // 3) * 240
        sheet.blit(preview, (x, y))
        sheet.blit(font.render(label, True, (235, 223, 197)), (x + 8, y + 218))
    pygame.image.save(sheet, output / 'contact_sheet.png')
    print(f'{len(shots)} visual captures: {output}')
    pygame.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'tools/visual_checks/cinematics')
    parser.add_argument('--only', nargs='+', help='Capture only these named moments')
    args = parser.parse_args()
    run(args.output.resolve(), args.only)
