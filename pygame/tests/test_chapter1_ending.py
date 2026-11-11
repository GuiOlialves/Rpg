"""Chapter I closure: previous choices, short return, responsibility and persistent control."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from collections import defaultdict
from copy import deepcopy
import unittest
from unittest.mock import patch
import pygame
import main
import save_manager
from tests import test_archive as archive_tests
from story import chapter1_ending as ending
from systems.dialogue import DialogueBox
from entities.npc import nearest
from ui.game_renderer import GameRenderer


class Chapter1EndingTests(unittest.TestCase):
    def setUp(self):
        self.fixture=archive_tests.ArchiveTests(); self.fixture.setUp(); self.fixture.reveal()
        from ui import debug_overlay, world_renderer
        debug_overlay._DEBUG_FONT = world_renderer._DEBUG_LABEL_FONT = None
        self.p,self.world,self.path=self.fixture.p,self.fixture.world,self.fixture.path
        self.dialogue=DialogueBox(); self.lines=[]
    def tearDown(self): self.fixture.tearDown()
    def save(self): self.fixture.save()
    def reload(self): return self.fixture.reload()
    def return_homeward(self):
        self.p.region_id='village'; self.p.region=self.world.build_region('village')
        self.p.story.set('chapter1_final_returned'); self.p.story.apply_to_region(self.p.region)
        self.p.player.x,self.p.player.y=1840,610
    def alden_talk(self):
        alden=next(n for n in self.p.region['npcs'] if n.uid=='alden')
        self.scene=ending.FinalAldenScene(alden,self.p.player,self.dialogue,self.p.region)
        for _ in range(300):
            if not self.scene.active: break
            if self.dialogue.active:
                self.lines.append(self.dialogue.npc.lines[self.dialogue.index]); self.scene.advance(self.dialogue)
            self.scene.update(100,self.dialogue,self.p.story,self.p.quests,self.p.inventory)
        self.assertFalse(self.scene.active)
    def examine(self,uid):
        obj=next(o for o in self.p.region['interactables'] if o.uid==uid)
        if not obj.enabled: return False
        obj.begin_interaction(self.dialogue,self.p.player,self.p.quests)
        while self.dialogue.active: self.dialogue.advance()
        changed=ending.complete_evidence(obj,self.p.story,self.p.inventory)
        self.p.story.apply_to_region(self.p.region)
        return changed
    def hook(self):
        self.return_homeward(); self.alden_talk(); self.assertTrue(self.examine('encosta_receipt'))
    def house(self):
        self.p.region_id='home'; self.p.region=self.world.build_region('home')
        self.p.story.apply_to_region(self.p.region)
    def test_optional_return_has_correct_text_and_keeps_original_exit(self):
        self.p.story.apply_to_region(self.p.region)
        marker=next(o for o in self.p.region['interactables'] if o.uid=='chapter1_return_vale')
        self.assertIn('estrada de serviço',marker.dialogues['default'][0])
        self.assertEqual(marker.transition_to,'village')
        self.assertIn('namar',self.p.region['exits'])
        result=self.world.transition('archive','village',self.p.quests,set(),save_manager.prepare_region,None,self.p.region)
        self.assertEqual(result.region_id,'village'); self.assertEqual(result.spawn,(1840,610))
        self.assertEqual(set(self.world.region_ids),set(save_manager.REGIONS))
        self.assertNotIn('forgotten_route',result.region['exits'])
        self.assertFalse(any(o.uid=='encosta_route_marker' and o.enabled for o in result.region['interactables']))
    def test_both_choice_consequences_persist_without_judging_or_reward_duplication(self):
        for branch in (0,1):
            for flag,value in (('namar_choice_protect',branch==0),('namar_choice_pursue',branch==1),
                               ('namar_dispatch_detail',branch==1),('namar_supplies_lost',branch==1)):
                self.p.story.set(flag,value)
            self.return_homeward()
            before=deepcopy(self.p.inventory)
            for _ in range(3): self.p.story.apply_to_region(self.p.region)
            survivors=[n for n in self.p.region['npcs'] if n.uid.startswith('vale_')]
            self.assertEqual(len(survivors),2)
            mara=next(n for n in survivors if n.uid=='vale_mara')
            text=' '.join(mara.dialogue_for('default'))
            self.assertIn('dividir pão' if branch==0 else 'repor',text)
            self.assertTrue(ending.complete_evidence(mara,self.p.story,self.p.inventory))
            self.assertFalse(ending.complete_evidence(mara,self.p.story,self.p.inventory))
            self.assertEqual(self.p.inventory,before)
            self.save(); loaded=self.reload()
            self.assertEqual(loaded.story.get('namar_supplies_lost'),bool(branch))
            self.assertTrue(loaded.story.get('chapter1_consequences_seen'))
            namar=self.world.build_region('namar'); loaded.story.apply_to_region(namar)
            self.assertEqual(namar['npcs'],[])
            self.p.story.set('chapter1_consequences_seen',False)
    def test_alden_has_pause_responsibility_and_hook_requires_conversation(self):
        self.return_homeward(); self.assertFalse(self.examine('encosta_receipt'))
        self.alden_talk()
        text=' '.join(line for _speaker,line in self.lines)
        self.assertIn('Procure as pessoas.',text)
        self.assertIn('Não vou dar uma absolvição',text)
        self.assertIn('Guarde as duas',text)
        self.assertTrue(any(isinstance(s,ending.Beat) and s.duration_ms>=1000 for s in ending.FinalAldenScene.STEPS))
        self.assertTrue(self.examine('encosta_receipt')); self.assertFalse(self.examine('encosta_receipt'))
        self.assertTrue(self.p.story.get('encosta_destination_known'))
        self.assertEqual(sum(i['id']=='encosta_receipt' for i in self.p.inventory),1)
    def test_memory_reflection_title_checkpoints_resume_once_and_preserve_world(self):
        self.hook(); self.house()
        obj=next(o for o in self.p.region['interactables'] if o.uid=='chapter1_final_records')
        self.p.player.x,self.p.player.y=613,409
        self.assertIs(nearest(self.p.region['interactables'],self.p.player,self.p.quests),obj)
        scene=ending.Chapter1EndingScene(self.p.player,self.p.story,self.p.quests)
        self.assertEqual(scene.phase,'memory')
        scene.update(5000); self.assertIn('Tenho',scene.sequence.current.text)
        scene.update(1650); self.assertTrue(self.p.story.get('chapter1_final_memory_seen'))
        self.save(); loaded=self.reload()
        resumed=ending.Chapter1EndingScene(loaded.player,loaded.story,loaded.quests)
        self.assertEqual(resumed.phase,'reflection')
        scene.update(3950); self.assertEqual(scene.phase,'fade')
        self.save(); loaded=self.reload()
        self.assertEqual(ending.Chapter1EndingScene(loaded.player,loaded.story,loaded.quests).phase,'fade')
        scene.update(850); self.assertEqual(scene.phase,'card')
        self.assertFalse(self.p.story.get('chapter1_completed'))
        scene.update(3650); self.assertTrue(self.p.story.get('chapter1_completed'))
        self.assertFalse(self.p.story.get('chapter2_started'))
        self.p.story.apply_to_region(self.p.region); self.assertFalse(obj.enabled)
        self.save(); loaded=self.reload()
        self.assertFalse(ending.Chapter1EndingScene(loaded.player,loaded.story,loaded.quests).active)
        self.assertIn(ending.DESTINATION,loaded.story.objective_text)
        self.assertTrue(loaded.story.get('archive_veteran_defeated'))
        self.assertTrue(loaded.story.get('namar_choice_protect'))
    def test_invalid_order_missing_receipt_future_chapter_and_legacy_flags(self):
        self.save(); baseline=save_manager.read_save(self.path)
        for flag in ending.ENDING_FLAGS:
            if flag=='chapter1_final_returned': continue
            data=deepcopy(baseline); data['story'][flag]=True
            with self.assertRaises(save_manager.SaveError): save_manager.validate(data)
        self.assertFalse(self.reload().story.get('chapter1_completed'))
        self.hook(); self.save(); data=save_manager.read_save(self.path)
        data['inventory']=[i for i in data['inventory'] if i['id']!='encosta_receipt']
        with self.assertRaises(save_manager.SaveError): save_manager.validate(data)
    def test_real_loop_short_return_alden_hook_house_title_and_control_after_load(self):
        self.p.player.x,self.p.player.y=246,817; self.save()
        current={}; keys=defaultdict(bool)
        state={'poll':0,'card':False,'return':False,'reloaded':False,'moved':False,'final_pos':None}
        original=GameRenderer.draw
        def events():
            state['poll']+=1; self.assertLess(state['poll'],700)
            if state['poll']==1: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F4)]
            if state['poll']==2: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F9)]
            if state['poll']==3: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F3)]
            keys.clear()
            if not current: return []
            player,story=current['player'],current['story']
            if current.get('ending_scene'): return []
            if story.get('chapter1_completed'):
                if not state['reloaded']:
                    state['reloaded']=True; return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F9)]
                self.assertIsNone(current['ending_scene'])
                if state['final_pos'] is None:
                    state['final_pos']=(player.x,player.y); keys[pygame.K_a]=True; return []
                state['moved']=(player.x,player.y)!=state['final_pos']
                return [pygame.event.Event(pygame.QUIT)]
            if current.get('alden_scene') or current['dialogue'].active:
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            kind=current['region']['ambient_kind']
            if kind=='archive': return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            if kind=='village':
                state['return']=True
                if not story.get('chapter1_final_alden_talk'):
                    target=next(n for n in current['region']['npcs'] if n.uid=='alden')
                    player.x,player.y=target.x+50,target.y
                elif not story.get('encosta_receipt_found'):
                    player.x,player.y=1780,640
                else:
                    target=next(o for o in current['region']['interactables'] if o.transition_to=='home')
                    player.x,player.y=target.x,target.y+30
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            if kind=='home':
                player.x,player.y=613,409
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            return []
        def observe(renderer,canvas,**kwargs):
            current.update(kwargs)
            if kwargs.get('ending_scene'):
                state['card'] |= kwargs['ending_scene'].phase=='card'
                self.assertEqual(kwargs['player'].attack_timer,0)
            return original(renderer,canvas,**kwargs)
        class Clock:
            def tick(self,fps): return 100
        with patch.object(save_manager,'SAVE_PATH',self.path),patch('core.game.pygame.time.Clock',Clock), \
             patch.object(pygame.event,'get',side_effect=events),patch.object(pygame.key,'get_pressed',return_value=keys), \
             patch('ui.game_renderer.GameRenderer.draw',autospec=True,side_effect=observe):
            self.assertEqual(main.main(),0)
        self.assertTrue(state['card']); self.assertTrue(state['return']); self.assertTrue(state['moved'])
        saved=save_manager.read_save(self.path)
        self.assertTrue(saved['story']['chapter1_completed']); self.assertFalse(saved['story']['chapter2_started'])


if __name__=='__main__': unittest.main()
