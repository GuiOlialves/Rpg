"""Focused regressions for the final prologue audit; no real save is touched."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

import pygame
import main
import save_manager
from core.debug_checkpoints import create_checkpoint, CHECKPOINTS
from entities.red_officer import RedOfficer
from systems import red_officer_encounter
from systems.combat import CombatSystem
from systems.dialogue import DialogueBox
from story.alden_scene import interact_with_alden
from story.arrival_scene import restore_resident
from story.blue_march import BlueMarchScene
from story.forest_battle import RedAmbushScene, InsigniaMemoryScene, spawn_red_group
from story.forest_confrontation import RedOfficerScene
from story.house_memory import HouseMemoryScene
from story.prologue import opening_sequence
from story.prologue_3c import Prologue3CScene
from ui.game_renderer import GameRenderer


class PrologueAuditTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((1, 1))
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'save.json'

    def tearDown(self):
        self.tmp.cleanup()
        pygame.quit()

    def preset(self, name='prologue_2e'):
        return create_checkpoint(name, load=main.load, build_region=main.build_region,
                                 spawn_enemies=main.spawn_enemies,
                                 restore_resident=restore_resident,
                                 opening_sequence=opening_sequence)

    def roundtrip(self, p):
        save_manager.save_game(p.player, p.inventory, p.quests, p.region_id, set(), [],
                               self.path, p.story)
        return save_manager.load_game(self.path,
            lambda: main.Player(p.player.idle, p.player.attack_sheet),
            main.build_region, main.spawn_enemies,
            lambda: main.Enemy('forest_guardian', (1300,430), main.load))

    def drive(self, scene, dialogue, update):
        for _ in range(1200):
            if not scene.active:
                return
            if dialogue.active:
                scene.advance()
            update(200)
        self.fail(f'Scene stuck: {type(scene).__name__} {getattr(scene, "phase", "")}')

    def boss_ready(self, p):
        p.story.set('red_officer_met')
        p.story.set('red_officer_boss_ready')
        p.story.apply_to_region(p.region)
        return red_officer_encounter.start(p.region, p.story, main.load)

    def defeated(self, p):
        boss = self.boss_ready(p)
        boss.receive_hit(100000, 0, 0)
        enemies = [boss]
        self.assertTrue(red_officer_encounter.conclude(p.region, p.story, enemies))
        self.assertEqual(enemies, [])
        return boss

    def test_checkpoint_roundtrips_and_region_idempotence(self):
        for key, _, _ in CHECKPOINTS[:-1]:
            with self.subTest(checkpoint=key):
                p = self.preset(key)
                restored = self.roundtrip(p)
                self.assertEqual(restored.region_id, p.region_id)
                for flag, value in p.story.to_dict().items():
                    self.assertEqual(restored.story.get(flag), value)
                self.assertFalse(any(restored.player.hitbox.colliderect(o)
                                     for o in restored.region['obstacles']))
                p.story.apply_to_region(p.region)
                sizes = tuple(len(p.region.get(k, [])) for k in ('objects','scenery','interactables'))
                p.story.apply_to_region(p.region)
                self.assertEqual(sizes, tuple(len(p.region.get(k, []))
                                             for k in ('objects','scenery','interactables')))
                self.assertFalse(p.quests.forest_event_started)
                self.assertFalse(p.story.get('red_officer_defeated'))

    def test_alden_normal_and_skip_reward_once(self):
        results = []
        for skip in (False, True):
            p = self.preset('prologue_2a'); d = DialogueBox()
            alden = next(n for n in p.region['npcs'] if n.uid == 'alden')
            scene = interact_with_alden(alden, p.player, d, p.quests, p.story)
            if skip:
                scene.finish(d, p.story, p.quests, p.inventory)
            else:
                for _ in range(250):
                    if not scene.active: break
                    scene.advance(d)
                    scene.update(1000, d, p.story, p.quests, p.inventory)
            self.assertFalse(scene.active)
            herbs = next(i['amount'] for i in p.inventory if i['id']=='herb')
            self.assertEqual(herbs, 8)
            self.assertFalse(scene.finish(d, p.story, p.quests, p.inventory))
            self.assertEqual(p.story.objective_text, 'Investigue a casa.')
            results.append(p.story.to_dict())
        self.assertEqual(*results)

    def test_house_recover_interrupted_pendant_and_finish_parity(self):
        outcomes = []
        for skip in (False, True):
            p = self.preset('prologue_2b'); d = DialogueBox()
            p.story.set('pendant_found')
            restored = self.roundtrip(p)
            obj = next(o for o in restored.region['interactables'] if o.uid=='broken_pendant')
            scene = HouseMemoryScene('pendant', restored.player, obj.image, d)
            if skip: scene.finish(restored.story, restored.region)
            else: self.drive(scene, d, lambda dt: scene.update(dt, restored.story, restored.region))
            self.assertTrue(restored.story.get('pendant_found'))
            self.assertTrue(restored.story.get('house_searched'))
            self.assertFalse(any(o.uid=='broken_pendant' for o in restored.region['interactables']))
            self.assertFalse(d.active)
            outcomes.append(restored.story.to_dict())
        self.assertEqual(*outcomes)

    def test_blue_march_and_insignia_skip_parity(self):
        for kind in ('march','insignia'):
            outcomes = []
            for skip in (False, True):
                p = self.preset('prologue_2c' if kind=='march' else 'prologue_2e')
                d=DialogueBox(); p.player.invulnerability_timer=4
                if kind=='march':
                    scene=BlueMarchScene(p.player,d,main.load)
                    finish=lambda: scene.finish(p.story,d)
                    update=lambda dt: scene.update(dt,p.story)
                else:
                    p.story.set('red_insignia_found',False)
                    scene=InsigniaMemoryScene(p.player,p.region['forest_battlefield_interactables']['insignia'].image,d,main.load)
                    finish=lambda: scene.finish(p.story,p.region)
                    update=lambda dt: scene.update(dt,p.story,p.region)
                self.assertEqual(p.player.invulnerability_timer,0)
                if skip: finish()
                else: self.drive(scene,d,update)
                self.assertFalse(d.active)
                self.assertFalse(finish())
                outcomes.append(p.story.to_dict())
            self.assertEqual(*outcomes)

    def test_partial_red_group_save_and_reentry_do_not_resurrect(self):
        p=self.preset('prologue_2d'); d=DialogueBox()
        actors=spawn_red_group(0,p.region,main.load,p.story)
        scene=RedAmbushScene(p.player,d,main.load,p.region['red_encounter_groups'][0],actors)
        scene.finish(d,p.story)
        actors[0].receive_hit(100000,0,0)
        combat=CombatSystem(main.load)
        p.player.x,p.player.y=120,575
        result=combat.update(p.player,'forest',p.region,actors,[],p.inventory,p.quests,0)
        self.assertEqual(result.defeated_soldiers,[0])
        for index in result.defeated_soldiers: p.story.record_soldier_defeat(index)
        restored=self.roundtrip(p)
        self.assertEqual([e.scripted_id for e in restored.enemies],[1])
        fresh=main.build_region('forest'); restored.story.apply_to_region(fresh)
        self.assertEqual([e.scripted_id for e in spawn_red_group(0,fresh,main.load,restored.story)],[1])
        restored.story.set_forest_battle_progress(2)
        restored.story.apply_to_region(fresh)
        self.assertFalse(any(c.visible for c in fresh['red_contacts'] if c.group_index==0))

    def test_officer_dialogue_normal_and_skip_match(self):
        outcomes=[]
        for skip in (False,True):
            p=self.preset(); d=DialogueBox(); p.player.invulnerability_timer=4
            scene=RedOfficerScene(p.player,d,p.story,p.region,main.load)
            self.assertEqual(p.player.invulnerability_timer,0)
            if skip: scene.finish()
            else: self.drive(scene,d,scene.update)
            self.assertTrue(p.story.get('red_officer_boss_ready'))
            self.assertEqual(p.region['scenery'].count(scene.officer),1)
            outcomes.append((p.story.to_dict(),scene.officer.x,scene.officer.y))
        self.assertEqual(*outcomes)

    def test_boss_nonlethal_phases_retry_and_defeated_load(self):
        p=self.preset(); boss=self.boss_ready(p)
        for hp,phase in ((320,0),(224,1),(128,2)):
            boss.hp=hp; self.assertEqual(boss.phase,phase)
        boss.attack_zone=pygame.Rect(1,1,40,40)
        boss.hp=2
        self.assertTrue(boss.receive_hit(100000,0,0))
        self.assertEqual((boss.hp,boss.state,boss.alive,boss.hostile),(1,'DEFEATED',True,False))
        self.assertIsNone(boss.attack_zone)
        self.assertFalse(boss.receive_hit(100000,0,0))
        self.assertIsNone(boss.drop())
        xp=p.player.current_xp
        result=CombatSystem(main.load).update(p.player,'forest',p.region,[boss],[],p.inventory,p.quests,0)
        self.assertEqual(p.player.current_xp,xp)
        self.assertEqual(result.drops,[])
        red_officer_encounter.conclude(p.region,p.story,result.enemies)
        p.story.apply_to_region(p.region)  # Enemy.alive must not be assigned.
        restored=self.roundtrip(p)
        actor=restored.region['red_officer_actor']
        self.assertEqual((actor.state,actor.hp,actor.alive),('DEFEATED',1,True))
        self.assertIsNone(red_officer_encounter.start(restored.region,restored.story,main.load))
        p=self.preset(); old=self.boss_ready(p); old.hp=10
        red_officer_encounter.stop(p.region,[old])
        p.region=main.build_region('forest'); p.story.apply_to_region(p.region)
        retry=red_officer_encounter.start(p.region,p.story,main.load)
        self.assertEqual(retry.hp,retry.max_hp)
        self.assertTrue(retry.hostile)

    def test_promise_normal_skip_and_safe_save_milestones(self):
        outcomes=[]
        for skip_phase in (None,'opening','memory','after_memory'):
            p=self.preset(); boss=self.defeated(p); d=DialogueBox()
            original_position=(boss.x,boss.y)
            scene=Prologue3CScene(p.player,p.story,p.region,d,main.load)
            self.assertEqual((scene.officer.x,scene.officer.y),original_position)
            self.assertEqual(scene.officer.hp,1)
            saved=set()
            for _ in range(1200):
                if not scene.active: break
                if scene.phase==skip_phase:
                    self.assertTrue(scene.finish()); break
                if scene.phase=='throw': self.assertTrue(scene.sequence.fade.active)
                if scene.phase=='memory' and 'hold' not in saved:
                    scene.update(600000)
                    self.assertLessEqual(scene.officer.x,p.player.x+150)
                    saved.add('hold')
                for flag in ('red_officer_memory_seen','red_officer_escaped'):
                    if p.story.get(flag) and flag not in saved:
                        loaded=self.roundtrip(p)
                        self.assertTrue(loaded.story.get(flag))
                        if flag=='red_officer_escaped': self.assertNotIn('red_officer_actor',loaded.region)
                        saved.add(flag)
                if d.active: scene.advance()
                scene.update(200)
            self.assertFalse(scene.active)
            self.assertTrue(p.story.get('prologue_completed'))
            self.assertNotIn('red_officer_actor',p.region)
            self.assertFalse(p.region.get('boss_battle_active'))
            self.assertFalse(scene.finish())
            self.assertFalse(d.active)
            loaded=self.roundtrip(p)
            self.assertTrue(loaded.story.get('prologue_completed'))
            self.assertEqual(loaded.enemies,[])
            self.assertNotIn('red_officer_actor',loaded.region)
            outcomes.append((p.story.to_dict(),p.player.facing))
        self.assertTrue(all(item==outcomes[0] for item in outcomes))


if __name__=='__main__': unittest.main()
