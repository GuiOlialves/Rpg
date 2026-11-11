"""Real chapter-II maps, actors, combat, investigation and irreversible checkpoints."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy'); os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from collections import deque,defaultdict
from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import pygame
import main,save_manager
from tests import test_chapter1_ending as ending_tests
from story import chapter1_ending,chapter2
from story.resonance import BY_ID,ResonanceScene
from entities.npc import nearest
from entities.encosta_creature import EncostaCreature
from systems.combat import CombatSystem
from world.respawn import restore_player_after_death
from ui.game_renderer import GameRenderer


class Chapter2Tests(unittest.TestCase):
    def setUp(self):
        self.f=ending_tests.Chapter1EndingTests(); self.f.setUp(); self.f.hook(); self.f.house()
        self.p,self.world,self.path=self.f.p,self.f.world,self.f.path; self.dialogue=self.f.dialogue
        scene=chapter1_ending.Chapter1EndingScene(self.p.player,self.p.story,self.p.quests)
        while scene.active: scene.finish()
        self.enter('village',None,(1830,560))
    def tearDown(self): self.f.tearDown()
    def save(self): self.f.save()
    def reload(self): return self.f.reload()
    def scene(self,kind):
        return chapter2.Chapter2Scene(kind,self.p.player,self.p.story,self.dialogue,self.p.quests,self.p.inventory,self.p.region)
    def start(self):
        scene=self.scene('departure')
        while self.dialogue.active: scene.advance()
        self.assertFalse(scene.update(100)); self.assertEqual(scene.phase,'title')
        self.assertTrue(scene.update(4800)); self.p.story.apply_to_region(self.p.region)
    def enter(self,kind,flag=None,pos=None):
        self.p.region_id=kind; self.p.region=self.world.build_region(kind)
        if flag: self.p.story.set(flag)
        self.p.story.apply_to_region(self.p.region)
        self.p.player.x,self.p.player.y=pos or self.p.region['spawn'][next(iter(self.p.region['spawn']))]
    def encosta(self):
        self.start(); self.enter('forgotten_route','route_entered'); self.enter('encosta','encosta_entered')
    def target(self,uid):
        return next(o for o in self.p.region['interactables']+self.p.region['npcs'] if o.uid==uid)
    def examine(self,uid):
        obj=self.target(uid)
        if not obj.enabled: return False
        obj.begin_interaction(self.dialogue,self.p.player,self.p.quests)
        while self.dialogue.active: self.dialogue.advance()
        changed=chapter2.complete_evidence(obj,self.p.story,self.p.inventory,self.p.player,self.p.quests)
        self.p.story.apply_to_region(self.p.region); return changed
    def echo(self,uid):
        scene=ResonanceScene(BY_ID[uid],self.p.player,self.p.story)
        if not scene.active: return False
        self.assertTrue(scene.update(sum(b.duration_ms for b in scene.point.beats)))
        self.p.story.apply_to_region(self.p.region); return True
    def investigate(self):
        for uid in ('ines','breno','encosta_register','encosta_locket','encosta_symbol'): self.examine(uid)
        for uid in ('echo_meal','echo_departure','echo_orders'): self.echo(uid)
    def solve(self):
        for uid in ('cabinet_bowl','cabinet_lamp','cabinet_name'):
            self.assertTrue(chapter2.puzzle_input(uid,self.p.story,self.p.quests))
        self.p.story.apply_to_region(self.p.region); self.assertTrue(self.examine('sealed_record'))
    def destination(self,choice=0):
        self.encosta(); self.investigate(); self.solve(); self.scene('choice').choose(choice)
        self.p.story.apply_to_region(self.p.region); self.assertTrue(self.examine('custody_plan'))
    def finish_a(self):
        self.enter('threshold','threshold_entered',(1000,820)); self.scene('vista').update(6000)
        self.examine('recent_camp')
        chapter2.record_defeats(self.p.story,[('threshold',1)],self.p.region,self.p.quests)
        self.echo('echo_threshold'); self.scene('part_a_end').update(6000)

    def test_departure_has_single_help_title_fade_unlock_and_resumes_after_load(self):
        marker=self.target('encosta_route_marker'); self.assertFalse(marker.enabled)
        potions=sum(i['amount'] for i in self.p.inventory if i['id']=='potion')
        scene=self.scene('departure'); scene.finish()
        self.assertTrue(self.p.story.get('chapter2_started')); self.assertFalse(self.p.story.get('chapter2_title_seen'))
        self.save(); restored=self.reload()
        pending=chapter2.moment_at(restored.player,restored.story,self.dialogue,restored.quests,restored.inventory,restored.region)
        self.assertEqual(pending.phase,'title'); pending.update(4800)
        self.assertEqual(sum(i['amount'] for i in restored.inventory if i['id']=='potion'),potions+1)
        self.assertFalse(chapter2.interact(next(n for n in restored.region['npcs'] if n.uid=='alden'),
            restored.player,restored.story,self.dialogue,restored.quests,restored.inventory,restored.region)[0])
        restored.story.apply_to_region(restored.region)
        self.assertTrue(next(o for o in restored.region['interactables'] if o.uid==marker.uid).enabled)

    def test_all_routes_rewards_evidence_npcs_echoes_and_exits_reachable_on_real_collision(self):
        self.destination(); self.finish_a()
        for kind,flag in (('forgotten_route','route_entered'),('encosta','encosta_entered'),('threshold','threshold_entered')):
            self.enter(kind,flag); region=self.p.region
            start=tuple(round(v/8)*8 for v in (self.p.player.x,self.p.player.y))
            def free(point):
                box=pygame.Rect(point[0]-13,point[1]-9,26,18)
                return 18<point[0]<2030 and 38<point[1]<1140 and not any(box.colliderect(o) for o in region['obstacles'])
            self.assertTrue(free(start),(kind,start))
            queue=deque([start]); reached={start}
            while queue:
                x,y=queue.popleft()
                for dx,dy in ((8,0),(-8,0),(0,8),(0,-8)):
                    dest=x+dx,y+dy
                    if dest not in reached and free(dest): reached.add(dest); queue.append(dest)
            for obj in region['interactables']+region['npcs']:
                self.assertTrue(any(obj.interaction_rect.colliderect(pygame.Rect(x-13,y-9,26,18)) for x,y in reached),(kind,obj.uid))
            for dest,exit_rect in region['exits'].items():
                self.assertTrue(any(pygame.Rect(x-13,y-9,26,18).colliderect(exit_rect) for x,y in reached),(kind,dest))

    def test_physical_bridge_ford_and_slope_allow_walk_and_dash_without_crossing_stream(self):
        self.start(); self.enter('forgotten_route','route_entered'); player=self.p.player
        player.x,player.y=910,760
        for _ in range(80): player.update(defaultdict(bool,{pygame.K_d:True}),self.p.region['obstacles'])
        self.assertGreater(player.x,1080)
        player.x,player.y=920,540
        for _ in range(80): player.update(defaultdict(bool,{pygame.K_d:True}),self.p.region['obstacles'])
        self.assertLess(player.x,950)
        player.x,player.y=925,345; player.facing=2; player.sp=player.max_sp
        self.assertTrue(player.start_dash(defaultdict(bool)))
        for _ in range(12): player.update(defaultdict(bool),self.p.region['obstacles'])
        self.assertGreater(player.x,1000); self.assertFalse(any(player.hitbox.colliderect(o) for o in self.p.region['obstacles']))

    def test_two_optional_rewards_are_unique_and_rest_is_safe_checkpoint(self):
        self.start(); self.enter('forgotten_route','route_entered')
        self.assertTrue(self.examine('route_cache')); self.assertFalse(self.examine('route_cache'))
        self.assertTrue(self.examine('route_record')); before=deepcopy(self.p.inventory)
        self.p.player.hp=10; self.p.player.sp=0; self.examine('route_rest')
        self.assertEqual(self.p.player.hp,self.p.player.max_hp); self.assertEqual(self.p.inventory,before)
        self.save(); loaded=self.reload(); self.assertTrue(loaded.region['rest_checkpoint'])
        self.assertFalse(next(o for o in loaded.region['interactables'] if o.uid=='route_record').enabled)
        restore_player_after_death(loaded.player,loaded.region_id,loaded.region,loaded.enemies)
        self.assertEqual((loaded.player.x,loaded.player.y),(1760.,610.))
        self.assertFalse(any(loaded.player.hitbox.colliderect(o) for o in loaded.region['obstacles']))

    def test_evidence_order_free_and_witnesses_required_before_puzzle(self):
        self.encosta(); self.assertFalse(self.echo('echo_orders'))
        for uid in ('encosta_symbol','encosta_locket','encosta_register'): self.assertTrue(self.examine(uid))
        self.assertTrue(self.p.story.get('encosta_investigated'))
        for uid in ('echo_orders','echo_departure','echo_meal'): self.assertTrue(self.echo(uid))
        self.assertFalse(chapter2.puzzle_input('cabinet_bowl',self.p.story,self.p.quests))
        self.examine('breno'); self.examine('ines'); self.assertTrue(chapter2.puzzle_ready(self.p.story))
        self.assertFalse(self.examine('encosta_locket')); self.assertEqual(sum(i['id']=='encosta_locket' for i in self.p.inventory),1)

    def test_resonance_config_duration_silhouettes_completion_and_no_combat_buff(self):
        self.encosta(); self.investigate()
        self.assertFalse(self.echo('echo_meal'))
        self.save(); loaded=self.reload(); self.assertFalse(next(o for o in loaded.region['interactables'] if o.uid=='echo_meal').enabled)
        self.assertGreater(len(BY_ID['echo_orders'].silhouettes),1)
        text=' '.join(b.text or '' for b in BY_ID['echo_orders'].beats)
        self.assertIn('Falta o começo',text)
        self.assertEqual(loaded.player.stats,self.p.player.stats)
        self.assertEqual(loaded.player.equipment,self.p.player.equipment)

    def test_puzzle_wrong_order_resets_only_clasps_and_partial_progress_survives_load(self):
        self.encosta(); self.investigate()
        self.assertIn(self.p.region['north_gate'],self.p.region['obstacles'])
        self.assertIn(self.p.region['north_barrier'],self.p.region['scenery'])
        chapter2.puzzle_input('cabinet_name',self.p.story,self.p.quests)
        self.assertFalse(self.p.story.get('encosta_puzzle_step1')); self.assertTrue(self.p.story.get('encosta_investigated'))
        chapter2.puzzle_input('cabinet_bowl',self.p.story,self.p.quests); self.save()
        loaded=self.reload(); self.assertTrue(loaded.story.get('encosta_puzzle_step1'))
        chapter2.puzzle_input('cabinet_bowl',self.p.story,self.p.quests)
        self.assertFalse(self.p.story.get('encosta_puzzle_step1'))
        self.solve(); self.save(); self.assertTrue(self.reload().story.get('encosta_puzzle_solved'))
        self.assertFalse(self.examine('sealed_record'))

    def test_minor_choices_both_persist_change_dialogue_and_keep_namar_branches(self):
        for minor in (0,1):
            if minor: self.p.story.set('encosta_choice_shared',False); self.p.story.set('encosta_choice_kept',False)
            else: self.encosta(); self.investigate(); self.solve()
            scene=self.scene('choice'); self.assertFalse(scene.finish()); self.assertTrue(scene.choose(minor))
            self.p.story.apply_to_region(self.p.region)
            lines=' '.join(self.target('ines').dialogue_for('default'))
            self.assertIn('Minha assinatura' if minor==0 else 'Vai guardar',lines)
            self.save(); loaded=self.reload(); self.assertTrue(loaded.story.get('encosta_choice_shared' if minor==0 else 'encosta_choice_kept'))
            self.assertEqual(loaded.story.get('namar_choice_protect'),self.p.story.get('namar_choice_protect'))
        self.assertTrue(self.examine('custody_plan')); self.assertIn('threshold',self.p.region['exits'])
        self.assertEqual(sum(i['id']=='encosta_sealed_record' for i in self.p.inventory),1)

    def test_breno_partial_knowledge_varies_with_both_original_choices(self):
        self.encosta(); npc=self.target('breno')
        for branch in (0,1):
            self.p.story.set('namar_choice_protect',branch==0); self.p.story.set('namar_choice_pursue',branch==1)
            text=' '.join(npc.dialogue_for('default'))
            self.assertIn('segurou a carroça' if branch==0 else 'carga perdida',text)
            self.assertIn('Não disse que conheço você',text)

    def test_new_creatures_have_different_geometry_attacks_and_all_nonempty_frames(self):
        for kind in ('reed_stalker','slateback','slate_warden'):
            enemy=EncostaCreature(kind,(500,500),main.load)
            for action,rows in enemy.frames.items():
                self.assertTrue(all(im.get_bounding_rect().width>10 for row in rows for im in row),(kind,action))
            self.p.player.x,self.p.player.y=500,565; enemy.attack_cooldown=0
            enemy.update(self.p.player,[]); self.assertEqual(enemy.attack_phase,'windup')
            hp=self.p.player.hp
            for _ in range(enemy.config['windup']-1): enemy.update(self.p.player,[])
            self.assertEqual(self.p.player.hp,hp)
            self.p.player.x=750
            for _ in range(enemy.config['active']+2): enemy.update(self.p.player,[])
            self.assertEqual(self.p.player.hp,hp); self.assertEqual(enemy.attack_phase,'recovery')
            self.assertTrue(enemy.receive_hit(1000,750,565)); self.assertEqual(enemy.state,'DEAD')
        self.assertLess(EncostaCreature('reed_stalker',(0,0),main.load).max_hp,EncostaCreature('slateback',(0,0),main.load).max_hp)

    def test_warden_radial_followup_excludes_square_corners_and_hits_once(self):
        for box,expected in ((pygame.Rect(552,552,24,24),0),(pygame.Rect(488,545,24,24),1)):
            hits=[]
            def damage(*args):
                hits.append(args); return True
            victim=SimpleNamespace(x=box.centerx,y=box.centery,hitbox=box,take_damage=damage)
            enemy=EncostaCreature('slate_warden',(500,500),main.load)
            enemy.strikes=1; enemy._begin_attack(victim)
            self.assertEqual(enemy.attack_action,'charged')
            self.assertEqual(enemy.windup_frames,enemy.config['windup']+14)
            for _ in range(enemy.windup_frames): enemy.update(victim,[])
            self.assertFalse(hits)
            self.assertTrue(enemy._strike().colliderect(box))
            for _ in range(enemy.config['active']): enemy.update(victim,[])
            self.assertEqual(len(hits),expected)
            self.assertEqual(enemy.attack_phase,'recovery')
            self.assertEqual(enemy.phase_timer,enemy.config['recovery']+12)

    def test_actual_sword_contacts_defeat_save_once_and_no_resurrection(self):
        self.start(); self.enter('forgotten_route','route_entered',(680,880))
        enemy=EncostaCreature('reed_stalker',(680,825),main.load,seed=0)
        self.p.player.x,self.p.player.y=680,770; self.p.player.facing=0
        self.p.player.physical_attack=1000
        combat=CombatSystem(main.load); enemies=[enemy]; flags=[]
        with patch.object(pygame.key,'get_pressed',return_value=defaultdict(bool)):
            self.p.player.attack()
            self.p.player.physical_attack=1000
            for _ in range(30):
                result=combat.update(self.p.player,self.p.region_id,self.p.region,enemies,[],self.p.inventory,self.p.quests,0)
                enemies=result.enemies; flags.extend(result.defeated_chapter2_enemies)
                chapter2.record_defeats(self.p.story,result.defeated_chapter2_enemies,self.p.region,self.p.quests)
        self.assertEqual(flags,[('forgotten_route',0)])
        self.save(); loaded=self.reload(); self.assertNotIn(0,[e.chapter2_id for e in loaded.enemies])

    def test_threshold_end_keeps_chapter_open_and_reentry_has_no_repeat(self):
        self.destination(1)
        self.assertNotIn(self.p.region['north_gate'],self.p.region['obstacles'])
        self.assertNotIn(self.p.region['north_barrier'],self.p.region['scenery'])
        self.finish_a(); self.save(); loaded=self.reload()
        for flag in ('threshold_vista_seen','threshold_activity_seen','threshold_guard_defeated','echo_threshold_seen','chapter2_part_a_completed'):
            self.assertTrue(loaded.story.get(flag),flag)
        self.assertTrue(loaded.story.get('chapter2_started')); self.assertFalse(loaded.story.get('chapter2_completed'))
        self.assertFalse(loaded.story.get('chapter2_part_b_started'))
        self.assertNotIn(1,[e.chapter2_id for e in loaded.enemies]); self.assertIn('Câmara dos Testemunhos',loaded.story.objective_text)
        loaded.player.x,loaded.player.y=1450,665
        self.assertIsNone(chapter2.moment_at(loaded.player,loaded.story,self.dialogue,loaded.quests,loaded.inventory,loaded.region))
        self.assertEqual(set(loaded.region['exits']),{'encosta'})

    def test_invalid_saves_reject_conflicting_choice_missing_documents_and_future_content(self):
        self.destination(); self.save(); data=save_manager.read_save(self.path)
        for flag in ('encosta_choice_kept','chapter2_part_b_started','chapter2_completed'):
            broken=deepcopy(data); broken['story'][flag]=True
            with self.assertRaises(save_manager.SaveError): save_manager.validate(broken)
        broken=deepcopy(data); broken['inventory']=[i for i in broken['inventory'] if i['id']!='chamber_plan']
        with self.assertRaises(save_manager.SaveError): save_manager.validate(broken)

    def test_integrated_game_departure_regions_investigation_choice_combat_end_and_reload(self):
        self.save(); current={}; keys=defaultdict(bool); states={'poll':0,'loaded':False,'movement':None,'frames':set()}
        original=GameRenderer.draw
        def events():
            states['poll']+=1; self.assertLess(states['poll'],1100)
            if states['poll']==1: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F4)]
            if states['poll']==2: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F9)]
            if states['poll']==3: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F3)]
            keys.clear()
            if not current: return []
            player,story,region=current['player'],current['story'],current['region']; kind=region['ambient_kind']
            scene=current.get('chapter2_scene')
            if scene:
                states['frames'].add(scene.phase)
                if scene.phase=='choice': return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_2)]
                if scene.phase=='departure': return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
                return []
            if current['dialogue'].active: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            if story.get('chapter2_part_a_completed'):
                if not states['loaded']:
                    states['loaded']=True; return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F9)]
                if states['movement'] is None:
                    states['movement']=(player.x,player.y); keys[pygame.K_d]=True; return []
                self.assertNotEqual(states['movement'],(player.x,player.y))
                return [pygame.event.Event(pygame.QUIT)]
            uid=None
            if kind=='village': uid='alden' if not story.get('chapter2_departure_seen') else 'encosta_route_marker'
            elif kind=='forgotten_route':
                if not story.get('route_cache_found'): uid='route_cache'
                elif not story.get('route_record_found'): uid='route_record'
                elif not story.get('route_rest_found'): uid='route_rest'
                else: player.x,player.y=2012,240; return []
            elif kind=='encosta':
                pending=(( 'ines','ines_met'),('breno','breno_met'),('encosta_register','encosta_register_found'),
                    ('encosta_locket','encosta_locket_found'),('encosta_symbol','encosta_symbol_found'),
                    ('echo_meal','echo_meal_seen'),('echo_departure','echo_departure_seen'),('echo_orders','echo_orders_seen'),
                    ('cabinet_bowl','encosta_puzzle_step1'),('cabinet_lamp','encosta_puzzle_step2'),('cabinet_name','encosta_puzzle_solved'),
                    ('sealed_record','encosta_sealed_record_found'))
                uid=next((uid for uid,flag in pending if not story.get(flag)),None)
                if uid is None:
                    if not story.get('encosta_choice_kept'): uid='ines'
                    elif not story.get('encosta_destination_found'): uid='custody_plan'
                    else: player.x,player.y=1565,40; return []
            elif kind=='threshold':
                if story.get('echo_threshold_seen'): return []
                if not story.get('threshold_vista_seen'): player.x,player.y=1150,635; return []
                if not story.get('threshold_activity_seen'): uid='recent_camp'
                elif not story.get('threshold_guard_defeated'):
                    enemy=next(e for e in current['enemies'] if e.chapter2_id==1)
                    if enemy.state!='DEAD':
                        player.x,player.y=enemy.x-45,enemy.y; player.facing=2; player.physical_attack=1000
                        return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE)]
                    return []
                else: uid='echo_threshold'
            if uid:
                target=next(o for o in region['interactables']+region['npcs'] if o.uid==uid)
                # Use a reachable position at which this object is actually nearest.
                candidates=[(target.x+dx,target.y+dy) for dx,dy in ((0,35),(35,0),(-35,0),(0,-35),(0,0))]
                for pos in candidates:
                    player.x,player.y=pos
                    if (not any(player.hitbox.colliderect(o) for o in region['obstacles'])
                        and nearest(region['interactables']+region['npcs'],player,current['quest_manager']) is target): break
                else: self.fail('No reachable interaction position: '+uid)
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            return []
        def observe(renderer,canvas,**kwargs):
            current.update(kwargs); return original(renderer,canvas,**kwargs)
        class Clock:
            def tick(self,fps): return 100
        with patch.object(save_manager,'SAVE_PATH',self.path),patch('core.game.pygame.time.Clock',Clock), \
             patch.object(pygame.event,'get',side_effect=events),patch.object(pygame.key,'get_pressed',return_value=keys), \
             patch('ui.game_renderer.GameRenderer.draw',autospec=True,side_effect=observe):
            self.assertEqual(main.main(),0)
        self.assertTrue(states['loaded']); self.assertTrue({'departure','title','choice','vista','resonance','part_a_end'}<=states['frames'])
        data=save_manager.read_save(self.path)
        self.assertTrue(data['story']['chapter2_part_a_completed']); self.assertTrue(data['story']['encosta_choice_kept'])
        self.assertFalse(data['story'].get('chapter2_completed',False)); self.assertFalse(data['story'].get('chapter2_part_b_started',False))
        broken=deepcopy(data); broken['story']['echo_orders_seen']=False
        with self.assertRaises(save_manager.SaveError): save_manager.validate(broken)


if __name__=='__main__': unittest.main()
