"""Both priorities, actual input/combat integration and checkpoint persistence in 1E."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from collections import defaultdict, deque
from copy import deepcopy
import math
from unittest.mock import patch
import unittest
import pygame
import main
import save_manager
from tests import test_edrin as edrin_tests
from story import namar
from story.edrin_encounter import PHASE_FLAGS
from systems.dialogue import DialogueBox
from systems.combat import CombatSystem
from ui.game_renderer import GameRenderer


class NamarTests(unittest.TestCase):
    save = edrin_tests.EdrinTests.save
    reload = edrin_tests.EdrinTests.reload

    def setUp(self):
        edrin_tests.EdrinTests.setUp(self)
        for flags in PHASE_FLAGS.values():
            for flag in flags: self.p.story.set(flag)
        self.p.story.set('namar_entered')
        self.p.region_id = 'namar'
        self.p.region = self.world.build_region('namar')
        self.p.story.apply_to_region(self.p.region)
        self.p.player.x, self.p.player.y = 120, 825
        self.lines = []

    def tearDown(self): edrin_tests.EdrinTests.tearDown(self)

    def examine(self, uid):
        obj = next(o for o in self.p.region['interactables'] if o.uid == uid)
        obj.begin_interaction(self.dialogue, self.p.player, self.p.quests)
        while self.dialogue.active: self.dialogue.advance()
        changed = namar.complete_evidence(obj, self.p.story, self.p.inventory)
        self.p.story.apply_to_region(self.p.region)
        return changed

    def evidence(self):
        for uid in ('namar_military', 'namar_civilian'): self.examine(uid)

    def start(self, position=None):
        if position: self.p.player.x, self.p.player.y = position
        self.scene = namar.moment_at(self.p.player, self.p.region, self.p.story,
            self.dialogue, self.p.quests, self.p.inventory, main.load)
        self.assertIsNotNone(self.scene)
        return self.scene

    def drive(self, branch=0, checkpoint=None):
        for _ in range(300):
            if not self.scene.active: break
            if self.scene.phase == 'choice': self.scene.choose(branch)
            elif self.dialogue.active:
                self.lines.append(self.dialogue.npc.lines[self.dialogue.index])
                self.scene.advance()
            self.scene.update(100)
            if self.scene.autosave_requested:
                self.scene.autosave_requested = False
                if checkpoint: checkpoint()
        self.assertFalse(self.scene.active)

    def select(self, branch=0, checkpoint=None):
        self.evidence()
        self.start((800, 650)); self.drive(branch, checkpoint)
        self.assertEqual(namar.choice(self.p.story), 'protect' if branch == 0 else 'pursue')

    def defeat_guards(self):
        for i in range(2): self.p.story.set(f'namar_enemy_{i}_defeated')
        self.assertTrue(namar.complete_combat(self.p.story, self.p.region))
        self.assertFalse(namar.complete_combat(self.p.story, self.p.region))

    def conclude(self, branch, checkpoint=None):
        self.select(branch, checkpoint); self.defeat_guards()
        if branch:
            self.start((1150, 305)); self.drive(branch, checkpoint)
        self.start((self.p.region['mara'].x, self.p.region['mara'].y+65))
        self.drive(branch, checkpoint)

    def test_both_evidence_required_exploration_optional_cache_and_legacy_connection(self):
        self.p.player.x, self.p.player.y = 800, 650
        self.assertIsNone(namar.moment_at(self.p.player,self.p.region,self.p.story,
            self.dialogue,self.p.quests,self.p.inventory,main.load))
        self.examine('namar_military')
        self.assertIsNone(namar.moment_at(self.p.player,self.p.region,self.p.story,
            self.dialogue,self.p.quests,self.p.inventory,main.load))
        herbs = next(i['amount'] for i in self.p.inventory if i['id'] == 'herb')
        self.assertTrue(self.examine('namar_cache')); self.assertFalse(self.examine('namar_cache'))
        self.assertEqual(next(i['amount'] for i in self.p.inventory if i['id']=='herb'), herbs+2)
        self.examine('namar_civilian'); self.start()
        self.assertEqual(self.scene.phase, 'intro')
        pursuit = self.world.build_region('pursuit'); self.p.story.apply_to_region(pursuit)
        self.assertIn('namar', pursuit['exits'])
        result = self.world.transition('pursuit','namar',self.p.quests,set(),save_manager.prepare_region,None,pursuit)
        self.assertEqual(result.spawn, (120,825)); self.assertEqual(result.enemies, [])
        self.assertEqual(self.p.region['terrain'].get_size(), (1536,960))

    def test_choice_requires_explicit_number_and_cannot_be_changed_or_skipped(self):
        self.evidence(); scene = self.start((800,650))
        scene.finish(); self.assertEqual(scene.phase,'choice')
        self.assertEqual(len(self.dialogue.choices),2)
        self.save(); loaded=self.reload()
        resumed=namar.moment_at(loaded.player,loaded.region,loaded.story,DialogueBox(),loaded.quests,loaded.inventory,main.load)
        self.assertEqual(resumed.phase,'choice')
        scene.advance(); scene.finish()
        self.assertIsNone(namar.choice(self.p.story))
        for value in (-1,2,True,None): self.assertFalse(scene.choose(value))
        self.assertTrue(scene.choose(1)); self.assertFalse(scene.choose(0))
        self.assertEqual(namar.choice(self.p.story),'pursue')
        self.save(); loaded = self.reload()
        self.assertTrue(loaded.story.get('namar_supplies_lost'))
        self.assertEqual(len(loaded.enemies),2)
        self.assertEqual(loaded.region['exits'],{})

    def test_protect_outcome_preserves_civilians_reward_memory_and_shared_record(self):
        before = next(i['amount'] for i in self.p.inventory if i['id']=='potion')
        self.conclude(0)
        self.assertEqual(next(i['amount'] for i in self.p.inventory if i['id']=='potion'),before+2)
        self.assertFalse(self.p.story.get('namar_dispatch_detail'))
        self.assertFalse(self.p.story.get('namar_supplies_lost'))
        text=' '.join(line for _speaker,line in self.lines)
        self.assertIn('A roda aguentou.',text); self.assertIn('Perdi a chance de perguntar.',text)
        self.assertIn('Segunda via: Depósito de Registros da Margem Seca. Gaveta 7.',text)
        self.assertTrue(self.p.story.get('namar_memory_seen'))
        self.assertTrue(self.p.story.get('namar_completed'))
        self.assertEqual([n.uid for n in self.p.region['npcs']],['mara','teo'])
        self.save(); loaded=self.reload()
        self.assertEqual(loaded.enemies,[])
        self.assertEqual(loaded.story.objective_title,'Ecos da Guerra')
        self.assertIn('segunda via da ordem de Namar',loaded.story.objective_text)
        self.assertIsNone(namar.moment_at(loaded.player,loaded.region,loaded.story,DialogueBox(),loaded.quests,loaded.inventory,main.load))
        self.assertEqual(loaded.region['mara'].dialogue_for('default')[0],'A farinha chegou ao abrigo. Desta vez, pelo menos.')

    def test_pursue_outcome_extra_reference_loss_return_and_same_next_objective(self):
        before=next(i['amount'] for i in self.p.inventory if i['id']=='potion')
        self.conclude(1)
        text=' '.join(line for _speaker,line in self.lines)
        self.assertIn('N-04. Série da retaguarda.',text)
        self.assertIn('Estamos vivos. A farinha ficou no chão.',text)
        self.assertTrue(self.p.story.get('namar_dispatch_detail'))
        self.assertTrue(self.p.story.get('namar_supplies_lost'))
        self.assertEqual(next(i['amount'] for i in self.p.inventory if i['id']=='potion'),before)
        self.save(); loaded=self.reload()
        self.assertIn('segunda via da ordem de Namar',loaded.story.objective_text)
        self.assertEqual([n.uid for n in loaded.region['npcs']],['mara','teo'])
        self.assertIn('Perdemos as sacas',loaded.region['mara'].dialogue_for('default')[0])
        self.assertIn('pursuit',loaded.region['exits'])
        self.assertNotIn('namar_archive',self.world.region_ids)

    def test_save_load_at_every_checkpoint_both_branches_no_reward_duplication(self):
        for branch in (0,1):
            with self.subTest(branch=branch):
                for f in namar.NAMAR_FLAGS: self.p.story.flags.pop(f,None)
                self.p.story.set('namar_entered'); self.p.region=self.world.build_region('namar')
                self.p.story.apply_to_region(self.p.region); self.dialogue=DialogueBox()
                checkpoints=[]
                def checkpoint():
                    self.save(); loaded=self.reload(); checkpoints.append(loaded.story.to_dict())
                    self.assertEqual(loaded.story.to_dict(),self.p.story.to_dict())
                    self.assertEqual(loaded.story.objective_text,self.p.story.objective_text)
                    if loaded.story.get('namar_aftermath_seen') and not loaded.story.get('namar_completed'):
                        at=(loaded.region['mara'].x,loaded.region['mara'].y+60)
                        loaded.player.x,loaded.player.y=at
                        resumed=namar.moment_at(loaded.player,loaded.region,loaded.story,DialogueBox(),loaded.quests,loaded.inventory,main.load)
                        self.assertIn(resumed.phase,('memory','ending'))
                        self.assertNotEqual(resumed.phase,'aftermath')
                self.conclude(branch,checkpoint)
                self.assertGreaterEqual(len(checkpoints),5)
                # A defeated guard must stay gone even when the other encounter is pending.
        for f in namar.NAMAR_FLAGS: self.p.story.flags.pop(f,None)
        self.p.story.set('namar_entered'); self.p.region=self.world.build_region('namar')
        self.p.story.apply_to_region(self.p.region); self.dialogue=DialogueBox()
        self.select(0); self.p.story.set('namar_enemy_0_defeated'); self.save()
        loaded=self.reload(); self.assertEqual([e.namar_id for e in loaded.enemies],[1])

    def test_save_rejects_conflicting_choices_unearned_clues_and_future_completion(self):
        self.save(); baseline=save_manager.read_save(self.path)
        for flag in ('namar_survivors_met','namar_choice_pursue','namar_enemy_0_defeated',
                     'namar_dispatch_detail','namar_aftermath_seen','namar_memory_seen','namar_completed'):
            invalid=deepcopy(baseline); invalid['story'][flag]=True
            with self.assertRaises(save_manager.SaveError): save_manager.validate(invalid)
        self.select(0); self.save(); selected=save_manager.read_save(self.path)
        invalid=deepcopy(selected); invalid['story']['namar_choice_pursue']=True
        with self.assertRaises(save_manager.SaveError): save_manager.validate(invalid)
        invalid=deepcopy(baseline); invalid['story']['edrin_encounter_completed']=False
        with self.assertRaises(save_manager.SaveError): save_manager.validate(invalid)

    def test_all_clues_flanks_survivors_carrier_and_exits_reachable_on_collision_map(self):
        # Actor-sized grid navigation checks the actual walls, props, and river bank.
        obstacles=self.p.region['obstacles']
        def free(x,y):
            return (20<=x<1270 and 50<=y<910 and not any(
                pygame.Rect(x-13,y-9,26,18).colliderect(o) for o in obstacles))
        seen={(120,825)}; queue=deque(seen)
        while queue:
            x,y=queue.popleft()
            for dx,dy in ((10,0),(-10,0),(0,10),(0,-10)):
                point=(x+dx,y+dy)
                if point not in seen and free(*point): seen.add(point); queue.append(point)
        for point in ((905,276),(451,611),(371,339),(820,660),(605,773),(1150,305),
                      (790,550),(1120,600),(850,360),(1080,340),(55,825)):
            self.assertLess(min(math.dist(point,p) for p in seen),25,point)

    def test_guard_telegraph_allows_dash_on_real_courtyard_obstacles(self):
        self.select(0)
        enemy = namar.spawn_pending(self.p.region,self.p.story,self.world.spawn_enemies)[0]
        player=self.p.player; player.x,player.y=enemy.x+60,enemy.y
        player.invulnerability_timer=0
        enemy._begin_attack('normal',player)
        self.assertEqual(enemy.attack_phase,'windup')
        before_hp,before_sp=player.hp,player.sp
        keys=defaultdict(bool,{pygame.K_s:True})
        self.assertTrue(player.start_dash(keys))
        trail=False
        for _ in range(24):
            player.update(keys,self.p.region['obstacles']); enemy.update(player,self.p.region['obstacles'])
            trail |= bool(player.dash_trail)
        self.assertTrue(trail)
        self.assertEqual(player.hp,before_hp)
        self.assertEqual(player.sp,before_sp-10)
        self.assertFalse(any(player.hitbox.colliderect(o) for o in self.p.region['obstacles']))

    def test_lower_ledge_connects_edrin_to_namar_without_crossing_log_or_bank(self):
        region=self.world.build_region('pursuit'); self.p.story.apply_to_region(region)
        player=self.p.player; player.x,player.y=910,386
        for tx,ty in ((940,420),(960,520),(1105,565),(1170,565)):
            for _ in range(200):
                dx,dy=tx-player.x,ty-player.y
                if math.hypot(dx,dy)<7: break
                keys=defaultdict(bool)
                keys[pygame.K_d if dx>0 else pygame.K_a]=abs(dx)>3
                keys[pygame.K_s if dy>0 else pygame.K_w]=abs(dy)>3
                player.update(keys,region['obstacles'])
            self.assertLess(math.dist((player.x,player.y),(tx,ty)),7,(tx,ty))
        self.assertTrue(player.hitbox.colliderect(region['exits']['namar']))

    def _real_loop(self, branch):
        self.evidence(); self.p.player.x,self.p.player.y=800,650; self.save()
        keys,current=defaultdict(bool),{}
        state={'poll':0,'reload':False,'verified':False,'attack':False,'dash':False,'feedback':False,'choice':False}
        original=GameRenderer.draw
        def events():
            state['poll']+=1
            self.assertLess(state['poll'],800, {
                'flags':current.get('story').to_dict() if current else {},
                'enemies':[(e.hp,e.state) for e in current.get('enemies',[])],
                'scene':getattr(current.get('namar_scene'),'phase',None),
                'hp':getattr(current.get('player'),'hp',None)})
            if state['poll']==1: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F4)]
            if state['poll']==2: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F9)]
            keys.clear()
            if not current: return []
            scene=current.get('namar_scene')
            if scene:
                if scene.phase=='choice':
                    state['choice']=True
                    return [pygame.event.Event(pygame.KEYDOWN,key=k) for k in
                            (pygame.K_SPACE,pygame.K_q,pygame.K_i,pygame.K_1 if branch==0 else pygame.K_2)]
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            story,player=current['story'],current['player']
            if story.get('namar_completed'):
                if not state['reload']:
                    state['reload']=True
                    return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F9)]
                self.assertEqual(namar.choice(story),'protect' if branch==0 else 'pursue')
                self.assertEqual(current['enemies'],[])
                self.assertIn('segunda via',story.objective_text)
                self.assertIsNone(current.get('namar_scene'))
                state['verified']=True
                return [pygame.event.Event(pygame.QUIT)]
            live=next((e for e in current['enemies'] if e.state!='DEAD'),None)
            if live is not None:
                player.x,player.y=live.x,live.y-30; player.facing=0
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE)]
            if story.get('namar_combat_completed'):
                target=current['region']['carrier'] if branch and not story.get('namar_dispatch_detail') else current['region']['mara']
                player.x,player.y=target.x,target.y+45
            elif not story.get('namar_survivors_met'):
                player.x,player.y=800,650
            return []
        def observe(renderer,canvas,**kwargs):
            current.update(kwargs)
            scene=kwargs.get('namar_scene')
            if scene:
                self.assertEqual(kwargs['player'].attack_timer,0)
                self.assertEqual(kwargs['player'].dash_timer,0)
                self.assertIsNone(kwargs['ui_mode'])
            state['attack'] |= kwargs['player'].attack_timer>0
            state['feedback'] |= bool(kwargs['damage_numbers'])
            return original(renderer,canvas,**kwargs)
        class Clock:
            def tick(self,fps): return 100
        with patch.object(save_manager,'SAVE_PATH',self.path), patch('core.game.pygame.time.Clock',Clock), \
             patch.object(pygame.event,'get',side_effect=events), \
             patch.object(pygame.key,'get_pressed',return_value=keys), \
             patch('ui.game_renderer.GameRenderer.draw',autospec=True,side_effect=observe):
            self.assertEqual(main.main(),0)
        self.assertTrue(state['choice']); self.assertTrue(state['verified'])
        self.assertTrue(state['attack']); self.assertTrue(state['feedback'])
        self.assertTrue(save_manager.read_save(self.path)['story']['namar_completed'])

    def test_real_loop_protect_combat_checkpoint_and_reload(self): self._real_loop(0)
    def test_real_loop_pursue_combat_carrier_return_and_reload(self): self._real_loop(1)


if __name__=='__main__': unittest.main()
