"""Dungeon progression, geometry, combat windows, evidence, replay and save contracts."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
from unittest.mock import patch
from collections import defaultdict,deque
from copy import deepcopy
from types import SimpleNamespace
import pygame
import main,save_manager
from tests import test_chapter2 as c2tests
from story import chapter2,lacre
from story.lacre_content import REGIONS,ENTER_FLAGS,PUZZLES,DOCUMENTS
from story.resonance import ResonanceScene,BY_ID
from entities.lacre_actor import LacreActor
from entities.npc import nearest
from systems.combat import CombatSystem
from world.respawn import restore_player_after_death
from ui.game_renderer import GameRenderer

class LacreTests(unittest.TestCase):
    def setUp(self):
        self.f=c2tests.Chapter2Tests();self.f.setUp();self.p=self.f.p;self.world=self.f.world;self.dialogue=self.f.dialogue;self.path=self.f.path
        self.enemies=[]
    def tearDown(self):self.f.tearDown()
    def __getattr__(self,name):
        if name!='f' and 'f' in self.__dict__:return getattr(self.f,name)
        raise AttributeError(name)
    def b(self):
        self.f.destination();self.f.finish_a();self.p.story.set('chapter2_part_b_started');self.enter(REGIONS[0])
    def enter(self,kind):
        self.f.enter(kind,ENTER_FLAGS.get(kind));self.enemies=chapter2.spawn_pending(self.p.region,self.p.story,self.world.spawn_enemies)
        self.p.region['live_enemies']=self.enemies
    def scene(self,kind):return lacre.LacreScene(kind,self.p.player,self.p.story,self.dialogue,self.p.quests,self.p.inventory,self.p.region)
    def echo(self,uid):
        scene=ResonanceScene(BY_ID[uid],self.p.player,self.p.story)
        self.assertTrue(scene.active);scene.update(sum(b.duration_ms for b in scene.point.beats));self.p.story.apply_to_region(self.p.region)
    def examine(self,uid):
        obj=self.f.target(uid);self.assertTrue(obj.enabled,uid);obj.begin_interaction(self.dialogue,self.p.player,self.p.quests)
        while self.dialogue.active:self.dialogue.advance()
        return chapter2.complete_evidence(obj,self.p.story,self.p.inventory,self.p.player,self.p.quests,self.p.region)
    def solve(self,name):
        for uid in PUZZLES[name][0]:lacre.puzzle(uid,self.p.story,self.p.quests,self.p.region)
    def archive(self):
        self.b();self.echo('l_echo_vestibule');self.solve('vestibule');self.enter(REGIONS[1])
        for uid in ('l_echo_seal','l_echo_door','l_echo_hand'):self.echo(uid)
        self.solve('gallery');self.enter(REGIONS[2])
    def kill(self):
        combat=CombatSystem(main.load);hits=[]
        with patch.object(pygame.key,'get_pressed',return_value=defaultdict(bool)):
            for _ in range(450):
                living=[e for e in self.enemies if e.state!='DEAD']
                if not self.enemies:break
                if living:
                    enemy=living[0];self.p.player.x,self.p.player.y=enemy.x-44,enemy.y;self.p.player.facing=2
                    self.p.player.physical_attack=1000;self.p.player.hp=self.p.player.max_hp
                    self.p.player.attack()
                frame=combat.update(self.p.player,self.p.region_id,self.p.region,self.enemies,[],self.p.inventory,self.p.quests,0)
                self.enemies=frame.enemies;hits.extend(frame.defeated_chapter2_enemies)
                chapter2.record_defeats(self.p.story,frame.defeated_chapter2_enemies,self.p.region,self.p.quests)
        self.assertFalse(self.enemies);return hits
    def core(self):
        self.archive()
        for uid in ('lacre_identity','lacre_purpose','lacre_military'):self.examine(uid)
        self.enter(REGIONS[3]);self.kill();self.examine('lacre_checkpoint');self.enter(REGIONS[4])
        self.scene('core_vista').finish();self.scene('custodian_talk').finish()
    def revelation(self):
        self.core();self.kill();self.scene('aftermath').finish()
        self.examine('lacre_second');self.examine('lacre_first');self.echo('l_echo_central')

    def test_vestibule_puzzle_echo_note_retry_and_partial_reload(self):
        self.b();self.assertFalse(self.f.target('lacre_next').enabled)
        lacre.puzzle('v_bowl',self.p.story,self.p.quests,self.p.region);self.assertFalse(self.p.story.get('lacre_vestibule_step1'))
        self.echo('l_echo_vestibule');obj=self.f.target('l_echo_vestibule');self.assertTrue(obj.enabled);self.assertFalse(obj.resonance)
        handled,_,_=chapter2.interact(obj,self.p.player,self.p.story,self.dialogue,self.p.quests,self.p.inventory,self.p.region)
        self.assertFalse(handled);self.assertIn('tigela',' '.join(obj.dialogue_for('default')))
        lacre.puzzle('v_bowl',self.p.story,self.p.quests,self.p.region);self.save();loaded=self.reload()
        self.assertTrue(loaded.story.get('lacre_vestibule_step1'))
        lacre.puzzle('v_name',self.p.story,self.p.quests,self.p.region);self.assertFalse(self.p.story.get('lacre_vestibule_step1'))
        self.assertTrue(self.p.story.get('lacre_vestige_seen'));self.solve('vestibule');self.assertTrue(self.f.target('lacre_next').enabled)

    def test_gallery_clues_free_order_records_unique_and_shortcut_persistent(self):
        self.archive();self.assertTrue(self.p.story.get('lacre_gallery_open'))
        for uid in ('lacre_military','lacre_identity','lacre_purpose'):self.examine(uid)
        self.assertTrue(self.p.story.get('lacre_archive_open'));self.assertFalse(self.examine('lacre_identity'))
        self.assertFalse(self.f.target('lacre_cache').enabled);self.echo('l_echo_secret')
        chapter2.interact(self.f.target('lacre_hidden'),self.p.player,self.p.story,self.dialogue,self.p.quests,self.p.inventory,self.p.region)
        self.examine('lacre_cache');self.examine('lacre_lore');self.examine('lacre_service');self.save();loaded=self.reload()
        self.assertTrue(loaded.story.get('lacre_shortcut_open'));self.assertFalse(next(o for o in loaded.region['interactables'] if o.uid=='lacre_cache').enabled)
        self.assertIn('lacre_lore',[i['id'] for i in loaded.inventory]);self.assertTrue(self.f.target('lacre_shortcut').enabled)

    def test_all_sector_interactions_have_a_connected_free_approach(self):
        self.b()
        for kind in REGIONS:
            self.enter(kind);r=self.p.region;start=(1024,936);seen={start};queue=deque([start])
            def free(x,y):return 440<=x<=1610 and 190<=y<=990 and not any(pygame.Rect(x-13,y-9,26,18).colliderect(o) for o in r['obstacles'])
            while queue:
                x,y=queue.popleft()
                for dx,dy in ((8,0),(-8,0),(0,8),(0,-8)):
                    pos=(x+dx,y+dy)
                    if pos not in seen and free(*pos):seen.add(pos);queue.append(pos)
            for obj in r['interactables']:
                self.assertTrue(any((x-obj.x)**2+(y-obj.y)**2<=obj.interaction_radius**2 for x,y in seen),(kind,obj.uid))
            self.assertFalse(any(self.p.player.hitbox.colliderect(o) for o in r['obstacles']))

    def test_echo_resistance_is_short_and_clear_guardian_recovery_is_vulnerable(self):
        self.b();echo=LacreActor('unstable_echo',(900,700),main.load)
        echo.tick=0;echo.receive_hit(30,850,700);self.assertEqual(echo.hp,echo.max_hp-10)
        echo.tick=70;echo.last_hit_timer=0;echo.receive_hit(30,850,700);self.assertEqual(echo.hp,echo.max_hp-40)
        warden=LacreActor('record_warden',(900,700),main.load);warden.begin_attack(self.p.player,'ward')
        warden.receive_hit(30,850,700);self.assertEqual(warden.hp,warden.max_hp-10)
        warden.last_hit_timer=0;warden.attack_phase='recovery';warden.receive_hit(30,850,700);self.assertEqual(warden.hp,warden.max_hp-40)
        for actor in (echo,warden):
            for rows in actor.frames.values():self.assertTrue(all(im.get_bounding_rect().width>8 for row in rows for im in row))

    def test_miniboss_checkpoint_and_actual_two_phase_sword_victory_persist(self):
        self.core();self.assertTrue(self.p.story.get('lacre_vigia_defeated'));self.assertTrue(self.p.story.get('lacre_checkpoint_found'))
        hits=self.kill();self.assertEqual(hits,[(REGIONS[4],0)])
        self.assertTrue(self.p.story.get('lacre_boss_phase2_seen'));self.assertTrue(self.p.story.get('lacre_custodian_defeated'))
        self.save();loaded=self.reload();self.assertFalse(loaded.enemies);self.assertFalse(loaded.region['boss_battle_active'])
        self.assertTrue(loaded.region['survivor_added'])

    def test_delayed_sector_echo_has_warning_then_one_hit_and_no_hit_behind(self):
        sector=dict(origin=(500,500),direction=(1,0),radius=70,half=.58)
        self.assertFalse(LacreActor.sector_hit(sector,pygame.Rect(455,495,10,10)))
        hits=[];victim=SimpleNamespace(x=548,y=500,hitbox=pygame.Rect(540,492,16,16),take_damage=lambda *args:hits.append(args) or True)
        actor=LacreActor('custodian',(500,500),main.load);actor.phase=2;actor.residuals=[dict(sector,time=34,hit=False)]
        actor.attack_cooldown=999
        for _ in range(33):actor.update(victim,[])
        self.assertFalse(hits)
        for _ in range(9):actor.update(victim,[])
        self.assertEqual(len(hits),1);self.assertFalse(actor.residuals)

    def test_phase_checkpoint_anchors_and_death_restore_safe_fresh_encounter(self):
        self.core();boss=self.enemies[0];boss.receive_hit(1000,980,570);boss.update(self.p.player,[])
        self.assertEqual(boss.state,'TRANSITION');self.assertFalse(boss.attack_box().width)
        for side in ('left','right'):
            obj=self.f.target('anchor_'+side);self.p.story.apply_to_region(self.p.region)
            chapter2.interact(obj,self.p.player,self.p.story,self.dialogue,self.p.quests,self.p.inventory,self.p.region)
        self.save();loaded=self.reload();self.assertEqual(loaded.enemies[0].phase,2);self.assertEqual(loaded.enemies[0].hp,400)
        self.p.story.set('lacre_boss_wounded',False);self.p.story.set('lacre_anchor_left_broken',False);self.p.story.set('lacre_anchor_right_broken',False)
        self.enter(REGIONS[4]);self.p.player.hp=0;restore_player_after_death(self.p.player,REGIONS[4],self.p.region,self.enemies)
        self.assertEqual(self.enemies[0].phase,1);self.assertEqual(self.enemies[0].hp,300);self.assertEqual((self.p.player.x,self.p.player.y),(1024.,900.))
        self.assertFalse(self.enemies[0].residuals);self.assertGreater(self.p.player.hp,0)

    def test_revelation_both_choices_reward_equipment_return_and_final_save(self):
        self.revelation();self.assertFalse(self.p.story.get('chapter2_completed'))
        text=' '.join(DOCUMENTS['lacre_first'][2]);self.assertIn('voluntariamente',text)
        self.assertIn('quinta vigília',' '.join(DOCUMENTS['lacre_second'][2]))
        for choice in (0,1):
            self.p.story.set('lacre_reward_given',False);self.p.inventory[:]=[i for i in self.p.inventory if i['id'] not in ('custody_medallion','lacre_lead')]
            self.assertTrue(self.scene('choice').choose(choice));self.assertFalse(self.scene('choice').choose(choice))
            self.save();loaded=self.reload();self.assertEqual(loaded.story.get('lacre_choice_shared'),choice==1)
            medallion=next(i for i in self.p.inventory if i['id']=='custody_medallion');before=self.p.player.max_hp
            self.p.player.equip(medallion);self.assertGreater(self.p.player.max_hp,before);self.p.player.unequip('Acessório')
        self.enter('encosta');self.scene('return').finish();self.p.story.apply_to_region(self.p.region)
        self.assertIn('cópia',' '.join(self.f.target('ines').dialogue_for('default')))
        final=self.scene('final');final.update(sum(b.duration_ms for b in final.sequence.beats));self.save();loaded=self.reload()
        self.assertTrue(loaded.story.get('chapter2_completed'));self.assertIn('Mosteiro da Vigília',loaded.story.objective_text)
        self.assertFalse(loaded.story.get('chapter3_started'));self.assertIsNone(chapter2.moment_at(loaded.player,loaded.story,self.dialogue,loaded.quests,loaded.inventory,loaded.region))

    def test_invalid_early_completion_missing_papers_or_double_choice_rejected(self):
        self.b();self.save();data=save_manager.read_save(self.path)
        for flag in ('chapter2_completed','lacre_vigia_defeated','lacre_memory_seen','lacre_choice_shared'):
            broken=deepcopy(data);broken['story'][flag]=True
            with self.assertRaises(save_manager.SaveError):save_manager.validate(broken)

    def test_new_atlas_padding_preserves_blades_idle_transition_and_four_directions(self):
        for kind in ('lacre_guard','unstable_echo','record_warden','custodian'):
            actor=LacreActor(kind,(1024,700),main.load)
            for action,rows in actor.frames.items():
                self.assertEqual(len(rows),4)
                for row in rows:
                    for im in row:
                        self.assertEqual(im.get_size(),(160,128))
                        bounds=im.get_bounding_rect(min_alpha=8)
                        self.assertGreater(bounds.left,0,(kind,action))
                        self.assertLess(bounds.right,160,(kind,action))
                        self.assertGreater(bounds.top,0,(kind,action))
                        self.assertLess(bounds.bottom,128,(kind,action))
            for action,minimum in (('idle',2),('transition',3),('cut',4),('sweep',4)):
                unique={pygame.image.tobytes(im,'RGBA') for im in actor.frames[action][0]}
                self.assertGreaterEqual(len(unique),minimum,(kind,action))

    def drive_b(self,current,states,keys):
        player,story,region=current['player'],current['story'],current['region'];kind=region['ambient_kind'];uid=None
        screen=current.get('game_over_screen')
        if screen is not None:
            return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN)] if screen.ready else []
        living=[e for e in current['enemies'] if e.state!='DEAD']
        if kind=='seal_core' and states.get('forced_defeat') and not states.get('continue_checked'):
            self.assertGreater(player.hp,0);self.assertEqual(living[0].phase,1);self.assertEqual(living[0].hp,300)
            self.assertFalse(living[0].residuals);self.assertFalse(story.get('lacre_boss_wounded'))
            self.assertEqual((player.x,player.y),(1024.,900.));states['continue_checked']=True
        if kind in REGIONS and living and (kind!='seal_core' or story.get('lacre_custodian_talk_seen')):
            if kind=='seal_core' and living[0].phase==2 and living[0].state=='TRANSITION' and not states.get('forced_defeat'):
                player.attack_timer=0;return []
            if kind=='seal_core' and living[0].phase==2 and living[0].state!='TRANSITION' and not states.get('forced_defeat'):
                # Force a real residual contact to exercise the production defeat screen.
                player.hp=1;player.invulnerability_timer=player.dash_iframes=0
                living[0].residuals=[dict(origin=(player.x,player.y),direction=(1,0),radius=70,half=.58,time=1,hit=False)]
                states['forced_defeat']=True;return []
            if kind=='seal_core' and story.get('lacre_boss_wounded'):
                side=next((side for side in ('left','right') if not story.get('lacre_anchor_'+side+'_broken')),None)
                if side:uid='anchor_'+side
            if uid is None:
                enemy=living[0];player.x,player.y=enemy.x-44,enemy.y;player.facing=2;player.physical_attack=1000;player.hp=player.max_hp
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE)]
        if uid is None:
            if kind=='threshold':
                if story.get('lacre_reward_given'):player.x,player.y=430,1115;return []
                uid='chamber_entrance'
            elif kind==REGIONS[0]:
                if story.get('lacre_reward_given'):uid='lacre_return'
                else:
                    pending=(('l_echo_vestibule','lacre_vestige_seen'),('v_bowl','lacre_vestibule_step1'),('v_lamp','lacre_vestibule_step2'),('v_name','lacre_vestibule_open'))
                    uid=next((u for u,f in pending if not story.get(f)),'lacre_next')
            elif kind==REGIONS[1]:
                pending=(('l_echo_door','lacre_gallery_door_seen'),('l_echo_hand','lacre_gallery_hand_seen'),('l_echo_seal','lacre_gallery_seal_seen'),
                         ('g_door','lacre_gallery_step1'),('g_hand','lacre_gallery_step2'),('g_seal','lacre_gallery_open'))
                uid=next((u for u,f in pending if not story.get(f)),'lacre_next')
            elif kind==REGIONS[2]:
                pending=(('lacre_identity','lacre_identity_found'),('lacre_military','lacre_military_found'),('lacre_purpose','lacre_purpose_found'),
                    ('l_echo_secret','lacre_secret_seen'),('lacre_hidden','lacre_secret_open'),('lacre_cache','lacre_cache_found'),('lacre_lore','lacre_lore_found'),('lacre_service','lacre_shortcut_open'))
                uid=next((u for u,f in pending if not story.get(f)),'lacre_next')
            elif kind==REGIONS[3]:
                if not story.get('lacre_vigia_defeated'):return []
                uid='lacre_checkpoint' if not story.get('lacre_checkpoint_found') else 'lacre_next'
            elif kind==REGIONS[4]:
                if not story.get('lacre_core_vista_seen'):player.x,player.y=1024,740;return []
                if not story.get('lacre_custodian_talk_seen'):player.x,player.y=1024,670;return []
                if not story.get('lacre_custodian_defeated'):return []
                if not story.get('lacre_aftermath_seen'):return []
                pending=(('lacre_first','lacre_first_found'),('lacre_second','lacre_second_found'),('l_echo_central','lacre_memory_seen'),('lacre_decision','lacre_reward_given'))
                uid=next((u for u,f in pending if not story.get(f)),'lacre_escape')
            elif kind=='encosta':uid='ines' if not story.get('lacre_return_seen') else 'lacre_closing_bench'
        if uid:
            target=next(o for o in region['interactables']+region['npcs'] if o.uid==uid)
            for dx,dy in ((0,35),(35,0),(-35,0),(0,-35),(0,0)):
                player.x,player.y=target.x+dx,target.y+dy
                if not any(player.hitbox.colliderect(o) for o in region['obstacles']) and nearest(region['interactables']+region['npcs'],player,current['quest_manager']) is target:break
            else:self.fail('No reachable B interaction: '+uid)
            return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
        return []

    def test_integrated_entire_chapter_a_through_b_end_reload_and_control(self):
        self.save(); current={}; keys=defaultdict(bool); states={'poll':0,'loaded':False,'movement':None,'frames':set()}
        original=GameRenderer.draw
        def events():
            states['poll']+=1; self.assertLess(states['poll'],3500)
            if states['poll']==1: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F4)]
            if states['poll']==2: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F9)]
            if states['poll']==3: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F3)]
            keys.clear()
            if not current: return []
            player,story,region=current['player'],current['story'],current['region']; kind=region['ambient_kind']
            scene=current.get('chapter2_scene')
            if scene:
                states['frames'].add(scene.phase)
                if scene.phase in ('choice','b_choice'): return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_2)]
                if scene.phase=='departure' or (getattr(scene,'sequence',None) is None and scene.phase!='b_choice'): return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
                return []
            if current['dialogue'].active: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            if story.get('chapter2_part_a_completed') and not story.get('chapter2_completed'):
                return self.drive_b(current,states,keys)
            if story.get('chapter2_completed'):
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
        self.assertTrue(states.get('continue_checked'))
        self.assertTrue({'b_core_vista','b_custodian_talk','b_aftermath','b_choice','b_return','b_final'}<=states['frames'])
        data=save_manager.read_save(self.path)
        self.assertTrue(data['story']['chapter2_part_a_completed']); self.assertTrue(data['story']['encosta_choice_kept'])
        self.assertTrue(data['story']['chapter2_completed']); self.assertTrue(data['story']['chapter2_part_b_started'])
        self.assertTrue(data['story']['lacre_choice_shared']);self.assertTrue(data['story']['lacre_boss_phase2_seen'])
        broken=deepcopy(data); broken['story']['echo_orders_seen']=False
        with self.assertRaises(save_manager.SaveError): save_manager.validate(broken)

if __name__=='__main__':unittest.main()
