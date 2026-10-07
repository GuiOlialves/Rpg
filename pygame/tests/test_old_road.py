"""Chapter 1B geometry, combat variation, milestones and actual loop wiring."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
from collections import defaultdict, deque
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pygame
import main
import save_manager
from core.debug_checkpoints import create_checkpoint
from entities.enemy import Enemy
from entities.road_pursuer import RoadPursuer
from story.arrival_scene import restore_resident
from story.prologue import opening_sequence
from story.old_road import RoadMomentScene, moment_at, complete_clue, threatened
from systems.combat import CombatSystem
from systems.dialogue import DialogueBox, DialogueSystem
from systems.inventory import add_inventory_item
from ui.game_renderer import GameRenderer
from world.world_manager import WorldManager
from world.respawn import safe_respawn_position


class OldRoadTests(unittest.TestCase):
    def setUp(self):
        pygame.init(); pygame.display.set_mode((1,1))
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/"road.json"
        self.world = WorldManager.for_game(main.load)
        self.p = create_checkpoint("prologue_2e",load=main.load,
            build_region=self.world.build_region,spawn_enemies=self.world.spawn_enemies,
            restore_resident=restore_resident,opening_sequence=opening_sequence)
        for flag in ("red_officer_met","red_officer_boss_ready","red_officer_defeated",
                     "red_officer_memory_seen","red_officer_escaped","prologue_completed",
                     "chapter1_started","chapter1_returned","chapter1_alden_talk","old_road_unlocked",
                     "old_road_entered"):
            self.p.story.set(flag)
        self.p.region_id = "old_road"
        self.p.region = self.world.build_region("old_road")
        self.p.story.apply_to_region(self.p.region)
        self.p.enemies = self.world.spawn_enemies(self.p.region)
        self.p.player.x,self.p.player.y = self.p.region["spawn"]["village"]

    def tearDown(self):
        self.tmp.cleanup(); pygame.quit()

    def save(self, opened=None):
        save_manager.save_game(self.p.player,self.p.inventory,self.p.quests,self.p.region_id,
            opened or set(),[],self.path,story=self.p.story)

    def reload(self):
        return save_manager.load_game(self.path,
            lambda: main.Player(self.p.player.idle,self.p.player.attack_sheet),
            self.world.build_region,self.world.spawn_enemies,
            lambda: main.Enemy("forest_guardian",(1300,430),main.load))

    def test_connection_round_trip_and_safe_spawns(self):
        village = self.world.build_region("village")
        self.p.story.apply_to_region(village)
        self.assertIn("old_road",village["exits"])
        road = self.world.transition("village","old_road",self.p.quests,set(),
            save_manager.prepare_region,None,source_region=village)
        self.assertEqual(road.spawn,(1910,850))
        self.assertEqual(len(road.enemies),4)
        self.assertFalse(any(self.p.player.hitbox.colliderect(box) for box in road.region["obstacles"]))
        self.assertEqual(safe_respawn_position("old_road",road.region,road.enemies),(1910,850))
        back = self.world.transition("old_road","village",self.p.quests,set(),
            save_manager.prepare_region,None,source_region=road.region)
        self.p.story.apply_to_region(back.region)
        self.assertEqual(back.spawn,(128,575))
        self.assertEqual(back.region["spawn"]["old_road"],(128,575))

    def test_route_and_three_optional_points_are_reachable_with_ground_collision(self):
        boxes = self.p.region["obstacles"]
        def free(node):
            x,y = node[0]*16+8,node[1]*16+8
            return (18<=x<=2030 and 38<=y<=1140
                    and not any(pygame.Rect(x-13,y-9,26,18).colliderect(box) for box in boxes))
        start = (119,53)
        reached, queue = {start},deque([start])
        while queue:
            x,y = queue.popleft()
            for node in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if node not in reached and free(node):
                    reached.add(node); queue.append(node)
        for point in ((1640,809),(850,560),(1250,409),(1155,325),(925,347),
                      (1720,1040),(745,816),(1175,950)):
            node = (point[0]//16,point[1]//16)
            self.assertIn(node,reached,point)
        self.assertGreater(len(self.p.region["main_route"]),12)
        self.assertEqual(len(self.p.region["optional_points"]),3)
        # The actual player stops at a visible cliff, and can walk the approach.
        keys = defaultdict(bool); keys[pygame.K_a] = True
        self.p.player.x,self.p.player.y = 642,800
        for _ in range(50): self.p.player.update(keys,boxes)
        self.assertGreater(self.p.player.x,620)
        self.p.player.x,self.p.player.y = 1910,850
        before = self.p.player.x
        for _ in range(25): self.p.player.update(keys,boxes)
        self.assertLess(self.p.player.x,before-50)

    def test_quiet_approach_and_combat_spaces_have_valid_enemy_feet(self):
        for enemy in self.p.enemies:
            self.assertGreater(pygame.Vector2(enemy.x-1910,enemy.y-850).length(),enemy.config["perception"]+150)
            self.assertFalse(any(enemy.hitbox.colliderect(box) for box in self.p.region["obstacles"]))
        self.assertEqual(sum(isinstance(e,RoadPursuer) for e in self.p.enemies),2)

    def test_variation_reuses_current_art_and_has_readable_attack_and_recovery(self):
        base = Enemy("warrior",(990,710),main.load)
        enemy = RoadPursuer((990,710),main.load)
        self.assertGreater(enemy.speed,base.speed)
        self.assertIs(enemy.visual,base.visual)
        self.p.player.x,self.p.player.y = 1050,710
        actions = []
        for _ in range(3):
            enemy._begin_attack("normal",self.p.player)
            actions.append(enemy.attack_action)
            self.assertEqual(enemy.attack_phase,"windup")
        self.assertEqual(actions,["normal","normal","charged"])
        self.assertEqual(enemy.phase_timer,30)
        self.assertFalse(enemy.attack_box())
        enemy.update(self.p.player,[])
        canvas = pygame.Surface((300,200),pygame.SRCALPHA)
        enemy.draw(canvas,(870,610))
        self.assertTrue(canvas.get_bounding_rect().height)
        for _ in range(29): enemy.update(self.p.player,[])
        self.assertEqual(enemy.attack_phase,"active")
        for _ in range(4): enemy.update(self.p.player,[])
        self.assertEqual(enemy.attack_phase,"recovery")
        self.assertFalse(enemy.attack_box())

    def test_clues_commit_on_closing_and_preserve_ambiguity(self):
        dialogue = DialogueBox()
        system = DialogueSystem()
        for uid, flag in (("road_red_cloth","road_red_clue_found"),
                          ("road_blue_shield","road_blue_trace_found"),
                          ("road_camp_map","road_camp_found")):
            target = next(obj for obj in self.p.region["interactables"] if obj.uid==uid)
            target.begin_interaction(dialogue,self.p.player,self.p.quests)
            self.assertFalse(self.p.story.get(flag))
            while dialogue.active: system.advance(dialogue,self.p.quests,self.p.inventory)
            self.assertTrue(complete_clue(target,self.p.story,self.p.region))
            self.assertFalse(complete_clue(target,self.p.story,self.p.region))
            self.assertFalse(target.available())
        lines = next(obj for obj in self.p.region["interactables"] if obj.uid=="road_aid_remains").dialogue_for("default")
        self.assertIn("cuidar dos feridos",lines[0])
        self.assertEqual(self.p.story.objective_text,"Investigue a antiga estrada.")

    def test_memory_is_short_blocks_combat_and_does_not_repeat(self):
        self.p.player.x,self.p.player.y = 850,560
        scene = moment_at(self.p.player,self.p.region,self.p.story,[])
        self.assertEqual(scene.kind,"memory")
        self.assertEqual(sum(b.duration_ms for b in scene.sequence.beats),1960)
        self.assertEqual(len(scene.world_actors),1)
        self.assertFalse(scene.update(1000,self.p.story,self.p.quests))
        self.assertTrue(scene.update(960,self.p.story,self.p.quests))
        self.assertFalse(scene.world_actors)
        self.assertFalse(scene.finish(self.p.story,self.p.quests))
        self.assertTrue(self.p.story.get("road_memory_seen"))
        self.assertIsNone(moment_at(self.p.player,self.p.region,self.p.story,[]))
        self.p.story.set("road_memory_seen",False)
        enemy = self.p.enemies[2]; enemy.x,enemy.y = 870,560; enemy.state="CHASE"
        self.assertTrue(threatened(self.p.player,[enemy]))
        self.assertIsNone(moment_at(self.p.player,self.p.region,self.p.story,[enemy]))

    def test_camp_and_lookout_update_objective_and_unlock_watchpost_connection(self):
        self.p.player.x,self.p.player.y = 925,347
        self.assertIsNone(moment_at(self.p.player,self.p.region,self.p.story,[]))
        for flag in ("road_red_clue_found","road_memory_seen","road_camp_found"):
            self.p.story.set(flag)
        scene = moment_at(self.p.player,self.p.region,self.p.story,[])
        self.assertEqual(scene.kind,"post")
        self.assertTrue(scene.update(2450,self.p.story,self.p.quests))
        self.assertEqual(self.p.story.objective_text,"Investigue o antigo posto de vigia.")
        self.assertIn("watchpost",self.p.region["exits"])
        self.assertIn("watchpost",self.world.region_ids)
        result = self.world.transition("old_road","watchpost",self.p.quests,set(),
            save_manager.prepare_region,None,source_region=self.p.region)
        self.assertEqual(result.region_id,"watchpost")

    def test_loot_and_defeated_enemies_persist_without_duplicate_reward(self):
        chest = next(obj for obj in self.p.region["interactables"] if obj.uid=="road_chest_turnout")
        chest.opened = True
        add_inventory_item(self.p.inventory,chest.loot)
        enemy = self.p.enemies[0]
        enemy.receive_hit(999,self.p.player.x,self.p.player.y)
        with patch.object(pygame.key,"get_pressed",return_value=defaultdict(bool)):
            result = CombatSystem(main.load).update(self.p.player,"old_road",self.p.region,
                self.p.enemies,[],self.p.inventory,self.p.quests,0)
        self.assertEqual(result.defeated_road_enemies,[0])
        self.p.story.set("road_enemy_0_defeated")
        self.save({chest.uid})
        loaded = self.reload()
        self.assertEqual(len(loaded.enemies),3)
        self.assertTrue(next(obj for obj in loaded.region["interactables"] if obj.uid==chest.uid).opened)
        self.assertEqual(next(item for item in loaded.inventory if item["id"]=="herb")["amount"],10)

    def test_save_reload_restores_each_milestone_and_rejects_bad_order(self):
        for flag in ("road_red_clue_found","road_blue_trace_found","road_memory_seen",
                     "road_camp_found","watchpost_seen"):
            self.p.story.set(flag)
            self.p.story.apply_to_region(self.p.region)
            self.save()
            loaded = self.reload()
            self.assertTrue(loaded.story.get(flag))
            self.assertEqual(loaded.story.objective_text,self.p.story.objective_text)
            self.assertFalse(next(obj for obj in loaded.region["interactables"] if obj.uid=="road_red_cloth").enabled)
            loaded.player.x,loaded.player.y = 850,560
            if loaded.story.get("road_memory_seen"):
                self.assertIsNone(moment_at(loaded.player,loaded.region,loaded.story,[]))
        data = save_manager.read_save(self.path)
        for name in ("old_road_entered","road_camp_found","road_memory_seen"):
            bad = deepcopy(data); bad["story"][name] = False
            with self.assertRaises(save_manager.SaveError): save_manager.validate(bad)

    def test_runtime_loop_wires_entry_clues_memory_loot_post_and_reload(self):
        self.p.region_id = "village"
        self.p.region = self.world.build_region("village")
        self.p.story.set("old_road_entered",False)
        self.p.story.apply_to_region(self.p.region)
        self.p.player.x,self.p.player.y = 128,575
        self.save()
        state = {"poll":0,"stage":"leave","kinds":set(),"fade":False,"reloaded":False}
        current = {}; keys = defaultdict(bool)
        original_draw = GameRenderer.draw

        def events():
            state["poll"] += 1
            self.assertLess(state["poll"],250)
            if state["poll"]==1: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F4)]
            if state["poll"]==2:
                keys[pygame.K_a] = True
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F9)]
            if not current: return []
            if current["dialogue"].active:
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            scene = current.get("old_road_scene")
            if scene is not None and scene.active:
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE)]
            if current["region"]["name"]!="Antiga Estrada": return []
            keys[pygame.K_a] = False
            fade = current["transition_fade"]
            if fade.active: return []
            player, story = current["player"],current["story"]
            stage = state["stage"]
            if stage=="leave":
                # Model the already-cleared encounters; separate tests exercise real combat.
                current["enemies"].clear()
                for i in range(4): story.set(f"road_enemy_{i}_defeated")
                player.x,player.y = 1720,1040
                state["stage"]="red"
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            if stage=="red":
                player.x,player.y = 1640,813
                state["stage"]="blue"
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            if stage=="blue" and story.get("road_red_clue_found"):
                player.x,player.y = 1250,409
                state["stage"]="memory"
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            if stage=="memory" and story.get("road_blue_trace_found"):
                player.x,player.y = 850,560
                state["stage"]="camp"
            elif stage=="camp" and story.get("road_memory_seen"):
                player.x,player.y = 1155,325
                state["stage"]="post"
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            elif stage=="post" and story.get("road_camp_found"):
                player.x,player.y = 925,347
                state["stage"]="save"
            elif stage=="save" and story.get("watchpost_seen"):
                state["stage"]="reload"
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F9)]
            elif stage=="reload":
                self.assertIsNone(current.get("old_road_scene"))
                self.assertEqual(story.objective_text,"Investigue o antigo posto de vigia.")
                self.assertEqual(current["enemies"],[])
                state["reloaded"] = True
                return [pygame.event.Event(pygame.QUIT)]
            return []

        def observe(renderer,canvas,**kwargs):
            current.update(kwargs)
            state["fade"] |= kwargs["transition_fade"].alpha>0
            scene = kwargs.get("old_road_scene")
            if scene is not None:
                state["kinds"].add(scene.kind)
                self.assertEqual(kwargs["player"].attack_timer,0)
            return original_draw(renderer,canvas,**kwargs)

        class FastClock:
            def tick(self,fps): return 100
        with patch.object(save_manager,"SAVE_PATH",self.path), \
             patch("core.game.pygame.time.Clock",FastClock), \
             patch.object(pygame.event,"get",side_effect=events), \
             patch.object(pygame.key,"get_pressed",return_value=keys), \
             patch("ui.game_renderer.GameRenderer.draw",autospec=True,side_effect=observe):
            self.assertEqual(main.main(),0)
        self.assertTrue(state["fade"])
        self.assertEqual(state["kinds"],{"memory","post"})
        self.assertTrue(state["reloaded"])
        saved = save_manager.read_save(self.path)
        self.assertIn("road_chest_turnout",saved["world"]["opened_desert_chests"])
        self.assertTrue(saved["story"]["watchpost_seen"])


if __name__=="__main__": unittest.main()
