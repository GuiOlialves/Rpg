"""1F progression, exact blade contacts, playable movement and persistent consequences."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from collections import defaultdict,deque
from copy import deepcopy
import math
import unittest
from unittest.mock import patch
import pygame
import main
import save_manager
from tests import test_namar as namar_tests
from story import archive
from systems.dialogue import DialogueBox
from ui.game_renderer import GameRenderer
from world.respawn import restore_player_after_death


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.fixture=namar_tests.NamarTests()
        self.fixture.setUp(); self.fixture.conclude(0)
        self.p,self.world,self.path=self.fixture.p,self.fixture.world,self.fixture.path
        self.dialogue=DialogueBox()
        self.p.story.set('archive_entered')
        self.p.region_id='archive'; self.p.region=self.world.build_region('archive')
        self.p.story.apply_to_region(self.p.region)
        self.p.player.x,self.p.player.y=246,862
        self.lines=[]
    def tearDown(self): self.fixture.tearDown()
    def save(self): self.fixture.save()
    def reload(self): return self.fixture.reload()
    def examine(self,uid):
        obj=next(o for o in self.p.region['interactables'] if o.uid == uid)
        if not obj.enabled: return False
        obj.begin_interaction(self.dialogue,self.p.player,self.p.quests)
        while self.dialogue.active: self.dialogue.advance()
        changed=archive.complete_evidence(obj,self.p.story,self.p.inventory)
        self.p.story.apply_to_region(self.p.region)
        return changed
    def start(self):
        self.scene=archive.moment_at(self.p.player,self.p.region,self.p.story,self.dialogue,self.p.quests,main.load)
        self.assertIsNotNone(self.scene)
        return self.scene
    def drive(self):
        for _ in range(150):
            if not self.scene.active: break
            if self.dialogue.active:
                self.lines.append(self.dialogue.npc.lines[self.dialogue.index]); self.scene.advance()
            self.scene.update(100)
        self.assertFalse(self.scene.active)
    def begin_fight(self):
        self.examine('archive_defense'); self.examine('archive_petition')
        self.p.player.x,self.p.player.y=750,680
        self.start(); self.drive()
        self.enemies=archive.spawn_pending(self.p.region,self.p.story)
        return self.enemies[0]
    def defeat(self):
        boss=self.begin_fight()
        boss.receive_hit(1000,self.p.player.x,self.p.player.y)
        self.assertTrue(archive.complete_combat(self.p.region,self.p.story,self.enemies))
        self.assertFalse(archive.complete_combat(self.p.region,self.p.story,self.enemies))
    def reveal(self):
        self.defeat(); self.examine('archive_order'); self.start(); self.drive()
        self.examine('archive_forgetting'); self.start(); self.drive()

    def test_connected_destination_gated_order_and_both_documentary_perspectives(self):
        namar=self.world.build_region('namar'); self.p.story.apply_to_region(namar)
        self.assertIn('archive',namar['exits'])
        result=self.world.transition('namar','archive',self.p.quests,set(),save_manager.prepare_region,None,namar)
        self.assertEqual(result.spawn,(246,862))
        self.assertEqual(result.enemies,[])
        self.assertFalse(self.examine('archive_order')); self.assertFalse(self.examine('archive_forgetting'))
        self.p.player.x,self.p.player.y=750,680
        self.examine('archive_defense')
        self.assertIsNone(archive.moment_at(self.p.player,self.p.region,self.p.story,self.dialogue,self.p.quests,main.load))
        self.examine('archive_petition'); self.assertEqual(self.start().phase,'challenge')
        text=' '.join(archive.document_lines('archive_defense',self.p.story))
        self.assertIn('Sem observação da outra margem',text)
        self.assertIn('Não tinha acesso aos sinais', ' '.join(archive.document_lines('archive_petition',self.p.story)))

    def test_choices_survive_and_extra_index_does_not_appear_on_protect_path(self):
        for branch in (0,1):
            self.p.story.set('namar_choice_protect',branch==0)
            self.p.story.set('namar_choice_pursue',branch==1)
            self.p.story.set('namar_supplies_lost',branch==1)
            self.p.story.set('namar_dispatch_detail',branch==1)
            self.p.story.apply_to_region(self.p.region)
            self.save(); loaded=self.reload()
            self.assertEqual(loaded.story.get('namar_supplies_lost'),bool(branch))
            text=' '.join(archive.document_lines('archive_defense',loaded.story))
            self.assertEqual('A referência do portador confere.' in text,bool(branch))
            petition=' '.join(archive.document_lines('archive_petition',loaded.story))
            self.assertIn('Deixei a carga' if branch else 'Mara preservou a farinha',petition)

    def test_every_revelation_checkpoint_reload_and_single_order_item(self):
        self.examine('archive_search'); self.save(); self.assertTrue(self.reload().story.get('archive_search_marks'))
        self.defeat(); self.save(); loaded=self.reload()
        self.assertEqual(loaded.enemies,[]); self.assertEqual(loaded.region['veteran'].state,'DEFEATED')
        self.assertEqual(loaded.region['veteran'].hp,1)
        self.assertEqual(loaded.region['veteran'].visual_flash,0)
        self.assertEqual(loaded.region['veteran'].anim_tick,24)
        self.assertIn('namar',loaded.region['exits'])
        self.examine('archive_order'); self.assertFalse(self.examine('archive_order'))
        self.save(); loaded=self.reload()
        scene=archive.moment_at(loaded.player,loaded.region,loaded.story,DialogueBox(),loaded.quests,main.load)
        self.assertEqual(scene.phase,'memory')
        self.start(); self.drive(); self.save(); loaded=self.reload()
        self.assertTrue(loaded.story.get('archive_memory_seen'))
        self.assertIsNone(archive.moment_at(loaded.player,loaded.region,loaded.story,DialogueBox(),loaded.quests,main.load))

        self.examine('archive_forgetting'); self.save(); loaded=self.reload()
        self.assertEqual(archive.moment_at(loaded.player,loaded.region,loaded.story,DialogueBox(),loaded.quests,main.load).phase,'ending')
        self.start(); self.drive(); self.save(); loaded=self.reload()
        self.assertTrue(loaded.story.get('archive_completed'))
        self.assertEqual(sum(i['id']=='namar_order_copy' for i in loaded.inventory),1)
        self.assertIn('Volte ao Vale',loaded.story.objective_text)
        self.assertIsNone(archive.moment_at(loaded.player,loaded.region,loaded.story,DialogueBox(),loaded.quests,main.load))

    def test_physical_namar_link_and_return_exit_are_walkable_after_completion(self):
        region=self.world.build_region('namar'); self.p.story.apply_to_region(region)
        player=self.p.player; player.x,player.y=1230,350
        keys=defaultdict(bool,{pygame.K_w:True})
        for _ in range(170): player.update(keys,region['obstacles'])
        self.assertTrue(player.hitbox.colliderect(region['exits']['archive']))
        transition=self.world.transition('namar','archive',self.p.quests,set(),save_manager.prepare_region,None,region)
        player.x,player.y=transition.spawn
        keys=defaultdict(bool,{pygame.K_s:True})
        for _ in range(50):
            player.update(keys,transition.region['obstacles'])
            if player.hitbox.colliderect(transition.region['exits']['namar']): break
        self.assertTrue(player.hitbox.colliderect(transition.region['exits']['namar']))
        transition=self.world.transition('archive','namar',self.p.quests,set(),save_manager.prepare_region,None,transition.region)
        self.assertEqual(transition.spawn,(1230,90))

    def test_incomplete_memory_shows_hero_issuing_order_before_cut_and_before_forgetting_reveal(self):
        self.defeat(); self.examine('archive_order'); scene=self.start()
        self.assertFalse(scene.commander.order_given)
        scene.update(5900)
        self.assertTrue(scene.commander.order_given)
        self.assertIn('Baixem as grades',scene.sequence.current.text)
        self.assertFalse(self.examine('archive_forgetting'))
        scene.update(3100); self.assertEqual(scene.sequence.current.background,'black')
        scene.update(2100); self.assertTrue(self.p.story.get('archive_memory_seen'))
        self.assertTrue(self.examine('archive_forgetting'))
        text=' '.join(archive.document_lines('archive_forgetting',self.p.story))
        self.assertIn('O pedido veio antes',text)
        self.assertIn('R-17',text); self.assertIn('N-04',text)

    def test_invalid_archive_states_and_missing_physical_order_rejected(self):
        self.save(); baseline=save_manager.read_save(self.path)
        for flag in archive.ARCHIVE_FLAGS[4:]:
            data=deepcopy(baseline); data['story'][flag]=True
            with self.assertRaises(save_manager.SaveError): save_manager.validate(data)
        data=deepcopy(baseline); data['story']['namar_completed']=False
        with self.assertRaises(save_manager.SaveError): save_manager.validate(data)
        self.reveal(); self.save(); data=save_manager.read_save(self.path)
        data['inventory']=[i for i in data['inventory'] if i['id']!='namar_order_copy']
        with self.assertRaises(save_manager.SaveError): save_manager.validate(data)

    def test_actor_sized_routes_reach_evidence_arena_vault_and_return_exit(self):
        def reachable(start):
            obstacles=self.p.region['obstacles']; seen={start}; queue=deque(seen)
            while queue:
                x,y=queue.popleft()
                for dx,dy in ((10,0),(-10,0),(0,10),(0,-10)):
                    p=x+dx,y+dy
                    if p in seen or not (30<p[0]<1240 and 40<p[1]<950): continue
                    if any(pygame.Rect(p[0]-13,p[1]-9,26,18).colliderect(o) for o in obstacles): continue
                    seen.add(p); queue.append(p)
            return seen
        points=reachable((246,862))
        for target in ((335,449),(181,566),(429,635),(750,680),(1090,750)):
            self.assertLess(min(math.dist(target,p) for p in points),40,target)
        self.assertGreater(min(math.dist((865,337),p) for p in points),80)
        self.defeat(); points=reachable((750,680))
        for target in ((865,337),(1050,306),(246,940),(650,760),(1090,750)):
            self.assertLess(min(math.dist(target,p) for p in points),30,target)

    def test_all_three_locked_attacks_can_be_evaded_and_have_punishable_recovery(self):
        boss=self.begin_fight(); player=self.p.player
        keys=defaultdict(bool,{pygame.K_s:True})
        for action in ('normal','charged','charge'):
            boss.x,boss.y=880,610; player.x,player.y=940,610
            player.hp=player.max_hp; player.sp=player.max_sp
            player.invulnerability_timer=player.dash_cooldown=player.dash_timer=player.dash_recovery_timer=0
            boss._begin_attack(action,player); aim=boss.attack_direction
            hp=player.hp
            self.assertGreaterEqual(boss.phase_timer,22)
            self.assertTrue(player.start_dash(keys))
            for _ in range(boss.WINDUP[action]+boss.ACTIVE[action]+1):
                player.update(keys,self.p.region['obstacles']); boss.update(player,self.p.region['obstacles'])
                self.assertEqual(boss.attack_direction,aim)
            self.assertEqual(player.hp,hp,action)
            self.assertEqual(boss.attack_phase,'recovery')
            self.assertGreaterEqual(boss.phase_timer,25)
            self.assertFalse(any(player.hitbox.colliderect(o) for o in self.p.region['obstacles']))

    def test_actual_blade_contact_damage_wall_safe_advance_and_death_retry(self):
        boss=self.begin_fight(); player=self.p.player
        boss.x,boss.y=1100,610; player.x,player.y=1170,610
        boss._begin_attack('charge',player)
        for _ in range(60): boss.update(player,self.p.region['obstacles'])
        self.assertLessEqual(boss.hitbox.right,1180)
        self.assertFalse(any(boss.hitbox.colliderect(o) for o in self.p.region['obstacles']))
        boss.x,boss.y=880,610; player.x,player.y=940,610
        player.invulnerability_timer=0
        hp=player.hp; boss._begin_attack('normal',player)
        for _ in range(boss.WINDUP['normal']+5): boss.update(player,self.p.region['obstacles'])
        self.assertLess(player.hp,hp)
        # Accepted damage cannot interrupt a committed windup or remove its warning.
        boss.hit_resistance_timer=0; boss._begin_attack('charged',player)
        self.assertTrue(boss.receive_hit(20,player.x,player.y))
        self.assertEqual(boss.attack_phase,'windup')
        self.p.region=self.world.build_region('archive'); self.p.story.apply_to_region(self.p.region)
        enemies=archive.spawn_pending(self.p.region,self.p.story)
        restore_player_after_death(player,'archive',self.p.region,enemies)
        self.assertEqual((player.x,player.y),(715,745))
        self.assertEqual(enemies[0].hp,210)
        self.assertFalse(any(player.hitbox.colliderect(o) for o in self.p.region['obstacles']))
        self.p.player.x,self.p.player.y=246,862; self.save(); loaded=self.reload()
        self.assertEqual((loaded.player.x,loaded.player.y),(715,745))

    def test_real_loop_investigation_combat_memory_autosave_and_reload(self):
        self.save(); keys,current=defaultdict(bool),{}
        state={'poll':0,'reloaded':False,'attack':False,'feedback':False,'memory':False,'checked':False}
        original=GameRenderer.draw
        def events():
            state['poll']+=1
            self.assertLess(state['poll'],1000,{'flags':current.get('story').to_dict() if current else {},
                'boss':[(e.state,e.hp) for e in current.get('enemies',[])],
                'hp':getattr(current.get('player'),'hp',None)})
            if state['poll']==1: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F4)]
            if state['poll']==2: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F9)]
            keys.clear()
            if not current: return []
            player,story=current['player'],current['story']
            if story.get('archive_completed'):
                if not state['reloaded']:
                    state['reloaded']=True; return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F9)]
                self.assertEqual(current['enemies'],[])
                self.assertIn('Volte ao Vale',story.objective_text)
                self.assertIsNone(current['archive_scene'])
                state['checked']=True; return [pygame.event.Event(pygame.QUIT)]
            if current.get('archive_scene') or current['dialogue'].active:
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            if current['enemies']:
                boss=current['enemies'][0]
                player.x,player.y=boss.x,boss.y-35; player.facing=0
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE)]
            for uid,flag in (('archive_search','archive_search_marks'),('archive_defense','archive_defense_report'),
                             ('archive_petition','archive_petition'),('archive_order','archive_order_obtained'),
                             ('archive_forgetting','archive_forgetting_record')):
                if not story.get(flag):
                    if uid == 'archive_order' and not story.get('archive_veteran_defeated'):
                        player.x,player.y=750,680; return []
                    obj=next(o for o in current['region']['interactables'] if o.uid == uid)
                    player.x,player.y=obj.x,obj.y+25
                    return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            return []
        def observe(renderer,canvas,**kwargs):
            current.update(kwargs)
            scene=kwargs.get('archive_scene')
            if scene:
                self.assertEqual(kwargs['player'].attack_timer,0)
                state['memory'] |= scene.memory_visible
            state['attack'] |= kwargs['player'].attack_timer>0
            state['feedback'] |= bool(kwargs['damage_numbers'])
            if kwargs['region'].get('boss_battle_active'):
                self.assertEqual(kwargs['camera'],(240,302))
            return original(renderer,canvas,**kwargs)
        class Clock:
            def tick(self,fps): return 100
        with patch.object(save_manager,'SAVE_PATH',self.path), patch('core.game.pygame.time.Clock',Clock), \
             patch.object(pygame.event,'get',side_effect=events), \
             patch.object(pygame.key,'get_pressed',return_value=keys), \
             patch('ui.game_renderer.GameRenderer.draw',autospec=True,side_effect=observe):
            self.assertEqual(main.main(),0)
        self.assertTrue(all(state[k] for k in ('attack','feedback','memory','checked')))
        self.assertTrue(save_manager.read_save(self.path)['story']['archive_completed'])


if __name__=='__main__': unittest.main()
