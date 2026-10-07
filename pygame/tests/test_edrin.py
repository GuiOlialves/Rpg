"""Focused chapter 1D route, complete dialogue, input lock and save validation."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import math
import tempfile
import unittest
from unittest.mock import patch
import pygame
import main
import save_manager
from core.debug_checkpoints import create_checkpoint
from story.arrival_scene import restore_resident
from story.prologue import opening_sequence
from story.watchpost import POST_FLAGS
from story import edrin_encounter as encounter
from systems.dialogue import DialogueBox
from systems.inventory import add_inventory_item
from systems.items import quest_item
from ui.game_renderer import GameRenderer
from world.world_manager import WorldManager


class EdrinTests(unittest.TestCase):
    def setUp(self):
        pygame.init(); pygame.display.set_mode((1, 1))
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'edrin.json'
        self.world = WorldManager.for_game(main.load)
        self.p = create_checkpoint('prologue_2e', load=main.load,
            build_region=self.world.build_region, spawn_enemies=self.world.spawn_enemies,
            restore_resident=restore_resident, opening_sequence=opening_sequence)
        for flag in ('red_officer_met', 'red_officer_boss_ready', 'red_officer_defeated',
                     'red_officer_memory_seen', 'red_officer_escaped', 'prologue_completed',
                     'chapter1_started', 'chapter1_returned', 'chapter1_alden_talk', 'old_road_unlocked',
                     'old_road_entered', 'road_red_clue_found', 'road_memory_seen', 'road_camp_found',
                     'watchpost_seen', *POST_FLAGS, 'pursuit_entered'):
            self.p.story.set(flag)
        add_inventory_item(self.p.inventory, quest_item('escort_token'))
        self.p.region_id = 'pursuit'
        self.p.region = self.world.build_region('pursuit')
        self.p.story.apply_to_region(self.p.region)
        self.p.player.x, self.p.player.y = 900, 400
        self.dialogue = DialogueBox()
        self.scene = None

    def tearDown(self):
        from ui import world_renderer, debug_overlay
        world_renderer._DEBUG_LABEL_FONT = debug_overlay._DEBUG_FONT = None
        self.tmp.cleanup(); pygame.quit()

    def start(self):
        self.scene = encounter.encounter_at(self.p.player, self.p.region, self.p.story,
                                            self.dialogue, self.p.quests, main.load)
        self.assertIsNotNone(self.scene)
        return self.scene

    def save(self):
        save_manager.save_game(self.p.player, self.p.inventory, self.p.quests, self.p.region_id,
                               set(), [], self.path, story=self.p.story)

    def reload(self):
        return save_manager.load_game(self.path,
            lambda: main.Player(self.p.player.idle, self.p.player.attack_sheet),
            self.world.build_region, self.world.spawn_enemies,
            lambda: main.Enemy('forest_guardian', (1300, 430), main.load))

    def drive(self, checkpoint=None):
        lines, phases = [], set()
        for _ in range(1000):
            if not self.scene.active:
                break
            phases.add(self.scene.phase)
            if self.dialogue.active:
                lines.append(self.dialogue.npc.lines[self.dialogue.index])
                self.scene.advance()
            self.scene.update(50)
            if self.scene.autosave_requested:
                self.scene.autosave_requested = False
                if checkpoint:
                    checkpoint()
        self.assertFalse(self.scene.active)
        return lines, phases

    def test_post_exit_short_tracking_route_and_safe_return(self):
        post = self.world.build_region('watchpost'); self.p.story.apply_to_region(post)
        self.assertIn('pursuit', post['exits'])
        result = self.world.transition('watchpost', 'pursuit', self.p.quests, set(),
                                       save_manager.prepare_region, None, source_region=post)
        self.assertEqual(result.spawn, (110, 600))
        self.assertEqual(result.enemies, [])
        self.assertEqual(result.region['terrain'].get_size(), (1280, 768))
        player = self.p.player
        player.x, player.y = result.spawn
        frames = 0
        for tx, ty in ((170, 600), (340, 530), (510, 455), (690, 425), (900, 390)):
            for _ in range(200):
                dx, dy = tx-player.x, ty-player.y
                if math.hypot(dx, dy) < 7: break
                keys = defaultdict(bool)
                keys[pygame.K_d if dx > 0 else pygame.K_a] = abs(dx) > 3
                keys[pygame.K_s if dy > 0 else pygame.K_w] = abs(dy) > 3
                player.update(keys, result.region['obstacles']); frames += 1
            self.assertLess(math.hypot(tx-player.x, ty-player.y), 7)
        self.assertLess(frames, 480)  # Under eight seconds at the normal 60 Hz.
        self.assertTrue(result.region['edrin_trigger'].colliderect(player.hitbox))
        back = self.world.transition('pursuit', 'watchpost', self.p.quests, set(),
                                     save_manager.prepare_region, None, source_region=result.region)
        self.assertEqual(back.spawn, (1390, 230))
        self.assertFalse(any(player.hitbox.move(1390-player.x, 230-player.y).colliderect(b)
                             for b in back.region['obstacles']))

    def test_trace_is_readable_repeatable_and_committed_only_on_close(self):
        target = self.p.region['interactables'][0]
        target.begin_interaction(self.dialogue, self.p.player, self.p.quests)
        self.assertFalse(self.p.story.get('pursuit_trace_found'))
        while self.dialogue.active: self.dialogue.advance()
        self.assertTrue(encounter.complete_trace(target, self.p.story))
        self.assertFalse(encounter.complete_trace(target, self.p.story))
        self.assertTrue(target.available())
        self.save(); self.assertTrue(self.reload().story.get('pursuit_trace_found'))

    def test_recognition_has_silences_and_continuous_recoil(self):
        scene = self.start()
        self.assertFalse(self.dialogue.active)
        scene.advance(); self.assertEqual(scene.index, 0)
        scene.update(799); self.assertFalse(self.dialogue.active)
        scene.update(1); self.assertEqual(self.dialogue.npc.dialogue_for('default'), ('Não.',))
        scene.advance(); scene.update(1)
        self.assertFalse(self.dialogue.active)
        scene.update(850)
        scene.advance(); scene.advance(); scene.update(1)
        self.assertEqual(scene.steps[scene.index][1], 'recoil')
        scene.update(325); self.assertAlmostEqual(scene.edrin.x, 1034)
        scene.update(325); self.assertAlmostEqual(scene.edrin.x, 1048)
        self.assertEqual(self.dialogue.npc.dialogue_for('default'), ('Você está morto.',))
        self.assertEqual(scene.edrin.mode, 'guard')

    def test_full_dialogue_patrol_living_escape_and_objective(self):
        self.start(); witnessed = {'patrol': False, 'escape': False, 'alone': False}
        def inspect():
            if self.p.story.get('pursuit_patrol_heard'): witnessed['patrol'] = True
            if self.p.story.get('edrin_escaped'):
                witnessed['escape'] = True
                self.assertFalse(self.scene.edrin.visible)
                self.assertEqual(self.p.region['npcs'], [])
            if self.scene.active and self.scene.phase == 'alone':
                witnessed['alone'] = True
                self.assertIn(self.scene.token, self.scene.world_actors)
        lines, phases = self.drive(inspect)
        text = ' '.join(line for speaker, line in lines)
        for phrase in ('Você está morto.', 'Eu vi você morrer.', 'Você dava as ordens.',
                       'Você já estava procurando um jeito de esquecer.', 'Do que eu estava fugindo?'):
            self.assertIn(phrase, text)
        self.assertEqual(phases, set(encounter.PHASE_FLAGS))
        self.assertTrue(all(witnessed.values()))
        self.assertEqual(self.p.story.objective_title, 'Ecos da Guerra')
        self.assertEqual(self.p.story.objective_text, 'Descubra o que aconteceu na Ponte de Namar.')
        self.assertNotIn('namar', self.world.region_ids)
        self.assertEqual(self.world.spawn_enemies(self.p.region), [])
        self.assertTrue(all(self.p.story.get(f) for f in encounter.EDRIN_FLAGS if f != 'pursuit_trace_found'))
        self.assertIsNone(encounter.encounter_at(self.p.player, self.p.region, self.p.story,
                                                self.dialogue, self.p.quests, main.load))

    def test_save_load_each_revelation_resumes_without_repeating_committed_phases(self):
        self.start(); saved = []
        def checkpoint():
            self.save(); loaded = self.reload()
            saved.append(loaded.story.to_dict())
            self.assertEqual(loaded.story.to_dict(), self.p.story.to_dict())
            resumed = encounter.encounter_at(loaded.player, loaded.region, loaded.story,
                                             DialogueBox(), loaded.quests, main.load)
            if loaded.story.get('edrin_encounter_completed'):
                self.assertIsNone(resumed)
                self.assertEqual(loaded.region['npcs'], [])
                self.assertEqual(loaded.story.objective_text, self.p.story.objective_text)
            else:
                self.assertEqual(resumed.phase, self.scene.phase)
                for phase in {step[0] for step in resumed.steps}:
                    self.assertFalse(all(loaded.story.get(f) for f in encounter.PHASE_FLAGS[phase]))
        self.drive(checkpoint)
        self.assertEqual(len(saved), len(encounter.PHASE_FLAGS))

    def test_save_rejects_unearned_identity_and_out_of_order_clue(self):
        self.save(); baseline = save_manager.read_save(self.path)
        for flag in ('edrin_name_known', 'edrin_forgetting_revealed', 'namar_clue_received',
                     'edrin_escaped', 'edrin_encounter_completed'):
            invalid = deepcopy(baseline); invalid['story'][flag] = True
            with self.assertRaises(save_manager.SaveError): save_manager.validate(invalid)
        invalid = deepcopy(baseline); invalid['story']['watchpost_trail_found'] = False
        with self.assertRaises(save_manager.SaveError): save_manager.validate(invalid)

    def test_scene_shortcut_is_atomic_and_idempotent(self):
        scene = self.start()
        self.assertTrue(scene.finish()); self.assertFalse(scene.finish())
        self.assertFalse(self.dialogue.active)
        self.save(); loaded = self.reload()
        self.assertTrue(loaded.story.get('edrin_name_known'))
        self.assertTrue(loaded.story.get('edrin_escaped'))
        self.assertEqual(loaded.region['npcs'], [])

    def test_real_loop_post_departure_tracking_dialogue_lock_autosave_and_reload(self):
        self.p.region_id = 'watchpost'; self.p.story.set('pursuit_entered', False)
        self.p.player.x, self.p.player.y = 1410, 196; self.save()
        keys, current = defaultdict(bool), {}
        state = {'poll': 0, 'waypoint': 0, 'reload': False, 'checked': False, 'phases': set(), 'fade': False}
        original = GameRenderer.draw
        waypoints = ((315, 544), (647, 454), (910, 386))
        def events():
            state['poll'] += 1; self.assertLess(state['poll'], 1000)
            if state['poll'] == 1: return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F4)]
            if state['poll'] == 2: return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F9)]
            if not current: return []
            scene = current.get('edrin_scene')
            if scene is not None:
                state['phases'].add(scene.phase)
                return [pygame.event.Event(pygame.KEYDOWN, key=k)
                        for k in (pygame.K_SPACE, pygame.K_q, pygame.K_i, pygame.K_e)]
            if current['story'].get('edrin_encounter_completed'):
                keys.clear()
                if not state['reload']:
                    state['reload'] = True
                    return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F9)]
                self.assertEqual(current['region']['npcs'], [])
                self.assertEqual(current['story'].objective_text, 'Descubra o que aconteceu na Ponte de Namar.')
                state['checked'] = True
                return [pygame.event.Event(pygame.QUIT)]
            if current['dialogue'].active:
                keys.clear()
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)]
            keys.clear()
            if current['transition_fade'].active: return []
            if current['region']['ambient_kind'] == 'watchpost':
                keys[pygame.K_d] = True
            elif current['region']['ambient_kind'] == 'pursuit':
                player = current['player']; tx, ty = waypoints[state['waypoint']]
                if math.dist((player.x, player.y), (tx, ty)) < 10:
                    state['waypoint'] += 1
                    if state['waypoint'] < 3:
                        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)]
                else:
                    dx, dy = tx-player.x, ty-player.y
                    keys[pygame.K_d if dx > 0 else pygame.K_a] = abs(dx) > 3
                    keys[pygame.K_s if dy > 0 else pygame.K_w] = abs(dy) > 3
            return []
        frozen = []
        def observe(renderer, canvas, **kwargs):
            current.update(kwargs); state['fade'] |= kwargs['transition_fade'].alpha > 0
            if kwargs.get('edrin_scene'):
                player = kwargs['player']
                frozen.append((player.x, player.y))
                self.assertEqual(player.attack_timer, 0)
                self.assertEqual(player.dash_timer, 0)
                self.assertIsNone(kwargs['ui_mode'])
            return original(renderer, canvas, **kwargs)
        class FastClock:
            def tick(self, fps): return 100
        with patch.object(save_manager, 'SAVE_PATH', self.path), \
             patch('core.game.pygame.time.Clock', FastClock), \
             patch.object(pygame.event, 'get', side_effect=events), \
             patch.object(pygame.key, 'get_pressed', return_value=keys), \
             patch('ui.game_renderer.GameRenderer.draw', autospec=True, side_effect=observe):
            self.assertEqual(main.main(), 0)
        self.assertTrue(state['checked']); self.assertTrue(state['fade'])
        self.assertEqual(state['phases'], set(encounter.PHASE_FLAGS))
        self.assertEqual(len(set(frozen)), 1)
        data = save_manager.read_save(self.path)
        self.assertTrue(data['story']['pursuit_trace_found'])
        self.assertTrue(data['story']['edrin_encounter_completed'])


if __name__ == '__main__': unittest.main()
