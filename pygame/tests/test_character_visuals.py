"""Focused sprite contracts: movement, masks, pivots and prepared rendering."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from collections import defaultdict
from unittest.mock import patch
import unittest
import pygame
from core.assets import load
from core.animation import ATTACK_DURATIONS, HERO_WALK_STRIDE_PIXELS
from entities.player import Player
from entities.enemy import Enemy, ENEMY_CONFIGS
from entities.red_officer import RedOfficer
from entities.npc import NPC
from ui.character_art import character_sheet, DRAW_SIZE
from story.forest_confrontation import create_waiting_officer
from story.blue_march import BlueTrooper
from story.forest_battle import RedContact, prepare_red_contacts


class CharacterVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init(); pygame.display.set_mode((1,1))
        cls.idle=load('assets/player/f_player_sheet.png')
        cls.attack=load('assets/player/f_player_attack_sheet.png')

    @classmethod
    def tearDownClass(cls): pygame.quit()

    def player(self):
        p=Player(self.idle,self.attack); p.x=p.y=500
        return p

    def test_gait_tracks_actual_distance_and_stops_at_wall(self):
        p=self.player(); keys=defaultdict(bool,{pygame.K_d:True})
        p.update(keys,[])
        self.assertAlmostEqual(p.walk_distance,p.speed)
        self.assertEqual(p.hitbox.size,(26,18))
        wall=pygame.Rect(514,400,20,200)
        before=p.walk_distance
        # Put the feet against the wall. Animation must not advance on blocked input.
        p.x=501
        for _ in range(20): p.update(keys,[wall])
        self.assertEqual(p.walk_distance,before)
        self.assertFalse(p.moving)
        self.assertEqual(p.walk_frame,0)
        p.update(defaultdict(bool),[])
        self.assertFalse(p.moving)
        p=self.player()
        for _ in range(25): p.update(keys,[])
        self.assertAlmostEqual(p.walk_distance,(25*p.speed)%HERO_WALK_STRIDE_PIXELS)

    def test_hero_keeps_pixel_scale_face_and_ground_anchor(self):
        p=self.player()
        self.assertEqual(p.visual.image('idle',0).get_size(),(64,72))
        self.assertEqual(p.visual.body_origin(500,500),(468,432))
        mouth=(139,86,77)
        for state,rows in p.visual.frames.items():
            for facing,row in enumerate(rows):
                for image in row:
                    self.assertEqual(image.get_size(),(64,72))
                    if facing!=3 and state!='death':
                        self.assertTrue(any(image.get_at((x,y))[:3]==mouth
                            for x in range(64) for y in range(40)),(state,facing))
                    # Integer nearest scaling preserves every 2 x 2 pixel cluster.
                    for x,y in ((24,20),(32,24),(36,46),(24,64)):
                        self.assertEqual(image.get_at((x,y)),image.get_at((x+1,y+1)))
        for facing in range(4):
            image=p.visual.image('idle',facing)
            self.assertEqual(image.get_bounding_rect().bottom,68)
            self.assertEqual(pygame.image.tobytes(p.visual.image('dash',facing,4),'RGBA'),
                             pygame.image.tobytes(image,'RGBA'))
        from story.prologue_3c import _PastProtagonist
        reflection=_PastProtagonist(p)
        canvas=pygame.Surface((1024,576),pygame.SRCALPHA)
        reflection.draw(canvas,(0,0))
        self.assertEqual(canvas.get_bounding_rect().bottom,round(reflection.y))

    def test_sword_masks_reach_front_in_four_directions_and_exclude_back(self):
        self.assertEqual(sum(ATTACK_DURATIONS),16)
        for facing,(dx,dy) in enumerate(((0,1),(-1,0),(1,0),(0,-1))):
            p=self.player(); p.facing=facing; p.attack()
            distance=32 if facing==0 else 42
            front=pygame.Rect(round(p.x+dx*distance-14),round(p.y+dy*distance-14),28,28)
            back=pygame.Rect(round(p.x-dx*65-8),round(p.y-dy*65-8),16,16)
            seen=False
            for _ in range(16):
                seen |= p.attack_hits(front)
                self.assertFalse(p.attack_hits(back))
                p.update(defaultdict(bool),[])
            self.assertTrue(seen,facing)
            self.assertEqual(p.attack_box.size,(0,0))

    def test_dash_recovery_keeps_controls_responsive_and_trail_short(self):
        for key in (pygame.K_s,pygame.K_a,pygame.K_d,pygame.K_w):
            p=self.player(); keys=defaultdict(bool,{key:True})
            self.assertTrue(p.start_dash(keys))
            for _ in range(11):
                p.update(keys,[])
                self.assertLessEqual(len(p.dash_trail),2)
                self.assertTrue(all(age<=5 for _,_,age,_,_ in p.dash_trail))
            self.assertEqual(p.dash_recovery_timer,5)
            before=(p.x,p.y)
            p.update(keys,[])
            self.assertAlmostEqual(((p.x-before[0])**2+(p.y-before[1])**2)**.5,p.speed)
            self.assertTrue(p.attack(),'Visual recovery must not delay an attack input')
            self.assertEqual(p.dash_recovery_timer,0)

    def test_down_cut_sweeps_both_front_flanks_without_extra_reach(self):
        p=self.player(); p.facing=0; p.attack()
        probes=[pygame.Rect(p.x+dx-5,p.y+dy-5,10,10) for dx,dy in ((-26,12),(0,22),(28,10))]
        seen=[False]*3
        beyond=pygame.Rect(p.x-5,p.y+50,10,10)
        behind=pygame.Rect(p.x-5,p.y-60,10,10)
        for _ in range(16):
            hits=[p.attack_hits(box) for box in probes]
            if not p.attack_active: self.assertFalse(any(hits),'Preparation/recovery cannot deal damage')
            seen=[old or hit for old,hit in zip(seen,hits)]
            self.assertFalse(p.attack_hits(beyond),'Short sword must not gain long forward reach')
            self.assertFalse(p.attack_hits(behind))
            p.update(defaultdict(bool),[])
        self.assertEqual(seen,[True,True,True],'Lateral cut must cover left, centre and right of its frontal arc')

    def test_actor_collisions_are_independent_of_art(self):
        expected={'slime':18,'warrior':23,'red_soldier':20,'red_officer':20,
                  'forest_guardian':30,'desert_scout':21,'dune_lancer':25}
        for kind,radius in expected.items():
            e=Enemy(kind,(500,500),load)
            self.assertEqual(e.hitbox,pygame.Rect(500-radius,500-radius,radius*2,radius*2))
            self.assertEqual(e.hitbox.size,(radius*2,radius*2))
        contacts=prepare_red_contacts([[(500,500),(560,500)]],load)
        original=Enemy('red_soldier',(500,500),load,seed=0)
        self.assertIs(contacts[0].actor.visual,original.visual)
        canvas=pygame.Surface((1024,576),pygame.SRCALPHA)
        contacts[0].draw_fallen(canvas,(0,0))
        self.assertLess(canvas.get_bounding_rect().height,32,'A recorded casualty must remain prone')
        npc=NPC('test','Test',(500,500),{},character_sheet(load,'civilian_elder'),frame_size=32)
        self.assertEqual(npc.hitbox.size,(36,24))
        self.assertEqual(npc.draw_size,DRAW_SIZE)

    def test_draw_uses_prepared_images_and_all_states_are_visible(self):
        p=self.player(); canvas=pygame.Surface((1024,576),pygame.SRCALPHA)
        actors=[Enemy(kind,(500,500),load) for kind in ENEMY_CONFIGS]
        actors.append(RedOfficer((500,500),load,defeat_hp=40))
        for state,count in (('dash',5),('hurt',3)):
            self.assertEqual(len({pygame.image.tobytes(im,'RGBA') for im in p.visual.frames[state][2]}),count)
        npc=NPC('test','Test',(500,500),{},character_sheet(load,'civilian_worker'),
                run_sprite=character_sheet(load,'civilian_worker','walk'),frame_size=32)
        officer=create_waiting_officer(load,(500,500))
        trooper=BlueTrooper('test_blue','Test',(500,500),{},character_sheet(load,'blue_commander'),
                           run_sprite=character_sheet(load,'blue_commander','walk'),frame_size=32)
        # No slicing/scaling/flipping occurs in steady-state actor drawing.
        with patch.object(pygame.transform,'scale',side_effect=AssertionError('runtime scale')), \
             patch.object(pygame.transform,'flip',side_effect=AssertionError('runtime flip')):
            for direction in range(4):
                p.facing=direction
                for state,frames in p.visual.frames.items():
                    for index in range(len(frames[0])):
                        canvas.fill((0,0,0,0))
                        p.visual.draw(canvas,(0,0),500,500,state,direction,index,
                                      weapon_index=index if state=='attack' else None)
                        self.assertGreater(canvas.get_bounding_rect().height,0)
                for e in actors:
                    e.attack_direction=((0,1),(-1,0),(1,0),(0,-1))[direction]
                    for state in ('IDLE','CHASE','HURT','DEAD','ATTACK'):
                        e.state=state; e.dead_timer=36; e.visual_facing=direction
                        for phase in ('windup','active','recovery'):
                            e.attack_phase=phase; e.attack_action='normal'; e.phase_timer=3
                            e.draw(canvas,(0,0))
                npc.facing=direction; npc.draw(canvas,(0,0))
                trooper.facing=direction; trooper.running=True; trooper.x+=3
                trooper.draw(canvas,(0,0))
                officer.facing=direction; officer.running=True; officer.x+=3
                officer.guarded=False; officer.state='IDLE'; officer.draw(canvas,(0,0))
                officer.guarded=True; officer.draw(canvas,(0,0))
                officer.state='DEFEATED'; officer.draw(canvas,(0,0))
            p.attack(); p.update(defaultdict(bool),[]); p.draw(canvas,(0,0))
            p.start_dash(defaultdict(bool,{pygame.K_d:True}))
            for _ in range(11):
                p.update(defaultdict(bool),[]); p.draw(canvas,(0,0))
            p.take_damage(10); p.draw(canvas,(0,0))
            p.hp=0; p.impact_timer=p.dust_timer=12
            position=(p.x,p.y)
            for _ in range(12): p.draw(canvas,(0,0))
            self.assertEqual(p.dash_trail,[])
            self.assertEqual((p.impact_timer,p.dust_timer),(0,0))
            self.assertEqual((p.x,p.y),position)
        # Both feet remain below the clothing hem, with a stable source pivot.
        for look in ('civilian_man','civilian_woman','civilian_worker','civilian_elder'):
            sheet=character_sheet(load,look)
            for direction in range(4):
                pose=sheet.subsurface((0,direction*32,32,32))
                self.assertEqual(pose.get_bounding_rect().bottom,28)


if __name__=='__main__': unittest.main()
