"""Focused 1C entry, navigation, investigation, combat and save/loop validation."""
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
from story.arrival_scene import restore_resident
from story.prologue import opening_sequence
from story import watchpost as post
from systems.combat import CombatSystem
from systems.dialogue import DialogueBox, DialogueSystem
from systems.inventory import apply_inventory_action
from ui.game_renderer import GameRenderer
from ui.inventory_menu import inventory_action_label, draw_inventory
from world.world_manager import WorldManager
from world.respawn import safe_respawn_position


class WatchpostTests(unittest.TestCase):
    def setUp(self):
        pygame.init(); pygame.display.set_mode((1,1))
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/"post.json"
        self.world = WorldManager.for_game(main.load)
        self.p = create_checkpoint("prologue_2e",load=main.load,
            build_region=self.world.build_region,spawn_enemies=self.world.spawn_enemies,
            restore_resident=restore_resident,opening_sequence=opening_sequence)
        for flag in ("red_officer_met","red_officer_boss_ready","red_officer_defeated",
                     "red_officer_memory_seen","red_officer_escaped","prologue_completed",
                     "chapter1_started","chapter1_returned","chapter1_alden_talk","old_road_unlocked",
                     "old_road_entered","road_red_clue_found","road_memory_seen","road_camp_found",
                     "watchpost_seen","watchpost_entered"):
            self.p.story.set(flag)
        self.p.region_id = "watchpost"
        self.p.region = self.world.build_region("watchpost")
        self.p.story.apply_to_region(self.p.region)
        self.p.enemies = self.world.spawn_enemies(self.p.region)
        self.p.player.x,self.p.player.y = self.p.region["spawn"]["old_road"]

    def tearDown(self):
        from ui import world_renderer, debug_overlay
        world_renderer._DEBUG_LABEL_FONT = None
        debug_overlay._DEBUG_FONT = None
        self.tmp.cleanup(); pygame.quit()

    def target(self, uid):
        return next(obj for obj in self.p.region["interactables"] if obj.uid==uid)

    def examine(self, uid):
        target = self.target(uid)
        dialogue = DialogueBox(); system = DialogueSystem()
        target.begin_interaction(dialogue,self.p.player,self.p.quests)
        while dialogue.active: system.advance(dialogue,self.p.quests,self.p.inventory)
        return post.complete_evidence(target,self.p.player,self.p.inventory,self.p.story,self.p.region,self.p.quests)

    def save(self):
        save_manager.save_game(self.p.player,self.p.inventory,self.p.quests,self.p.region_id,
            set(),[],self.path,story=self.p.story)

    def reload(self):
        return save_manager.load_game(self.path,
            lambda: main.Player(self.p.player.idle,self.p.player.attack_sheet),
            self.world.build_region,self.world.spawn_enemies,
            lambda: main.Enemy("forest_guardian",(1300,430),main.load))

    def main_evidence(self):
        for uid in ("post_breach","post_dispatch","post_roster","post_token"):
            self.examine(uid)
        scene = post.PostMomentScene("memory",self.p.player,self.p.region,main.load)
        scene.finish(self.p.story,self.p.quests)

    def test_connection_and_safe_return_to_post(self):
        road = self.world.build_region("old_road")
        self.p.story.apply_to_region(road)
        self.assertIn("watchpost",road["exits"])
        result = self.world.transition("old_road","watchpost",self.p.quests,set(),
                                      save_manager.prepare_region,None,source_region=road)
        self.assertEqual(result.spawn,(768,914))
        self.assertEqual(len(result.enemies),2)
        self.assertEqual(safe_respawn_position("watchpost",result.region,result.enemies),(768,914))
        back = self.world.transition("watchpost","old_road",self.p.quests,set(),
                                    save_manager.prepare_region,None,source_region=self.p.region)
        self.assertEqual(back.spawn,(920,340))
        self.assertNotIn("pursuit",self.p.region["exits"])
        self.assertIn("pursuit",self.world.region_ids)

    def test_layout_breach_rooms_gate_and_departure_have_real_collision(self):
        def reachable():
            boxes = self.p.region["obstacles"]
            def free(node):
                x,y = node[0]*16+8,node[1]*16+8
                return (18<x<1518 and 38<y<1012 and
                        not any(pygame.Rect(x-13,y-9,26,18).colliderect(b) for b in boxes))
            start=(48,57); found={start}; queue=deque([start])
            while queue:
                x,y=queue.popleft()
                for n in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if n not in found and free(n): found.add(n); queue.append(n)
            return found
        before=reachable()
        self.assertIn((77,43),before)  # Approach to the side breach.
        self.assertNotIn((52,36),before)
        keys=defaultdict(bool); keys[pygame.K_w]=True
        self.p.player.x,self.p.player.y=768,844
        for _ in range(40): self.p.player.update(keys,self.p.region["obstacles"])
        self.assertGreaterEqual(self.p.player.y,801)
        self.examine("post_breach")
        found=reachable()
        for point in ((681,630),(995,589),(973,341),(647,471),(850,610),(1230,329),(1480,190)):
            self.assertTrue((point[0]//16,point[1]//16) in found,point)
        self.assertIn(self.p.region["postern_block"],self.p.region["obstacles"])
        self.p.story.set("watchpost_presence_seen"); self.p.story.apply_to_region(self.p.region)
        self.assertNotIn(self.p.region["postern_block"],self.p.region["obstacles"])
        self.p.player.x,self.p.player.y=1130,328
        keys=defaultdict(bool); keys[pygame.K_d]=True
        for _ in range(45): self.p.player.update(keys,self.p.region["obstacles"])
        self.assertGreater(self.p.player.x,1196)
        self.p.player.x,self.p.player.y=1480,190
        for _ in range(90): self.p.player.update(keys,self.p.region["obstacles"])
        self.assertLessEqual(self.p.player.x,1491)
        # An archive cannot be read through the lodging wall.
        self.p.player.x,self.p.player.y=750,630
        self.assertFalse(post.can_examine(self.p.player,self.target("post_archive"),self.p.region))

    def test_three_short_documents_reread_without_recommitting(self):
        self.examine("post_breach")
        for uid,flag in (("post_archive","watchpost_archive_read"),
                         ("post_dispatch","watchpost_dispatch_read"),
                         ("post_roster","watchpost_roster_read")):
            target=self.target(uid)
            self.assertLessEqual(len(target.dialogue_for("default")),3)
            self.assertFalse(self.p.story.get(flag))
            self.assertTrue(self.examine(uid)); self.assertTrue(self.p.story.get(flag))
            self.assertTrue(target.available())
            self.assertFalse(self.examine(uid))
        self.assertTrue(self.p.story.get("watchpost_blue_order_found"))
        self.assertFalse(self.p.story.get("watchpost_identity_confirmed"))
        self.assertIn("receber feridos dos dois lados",self.target("post_archive").dialogue_for("default")[0])
        self.assertIn("sem água",self.target("post_dispatch").dialogue_for("default")[1])
        self.assertIn("R-17",self.target("post_roster").dialogue_for("default")[0])

    def test_personal_item_is_unique_proves_identity_and_cannot_be_consumed(self):
        self.examine("post_breach"); self.examine("post_roster")
        self.assertTrue(self.examine("post_token"))
        self.assertFalse(self.examine("post_token"))
        self.assertTrue(self.p.story.get("watchpost_identity_confirmed"))
        token=next(i for i in self.p.inventory if i["id"]=="escort_token")
        self.assertEqual(token["amount"],1); self.assertEqual(token["type"],"quest")
        self.assertIsNone(inventory_action_label(token,self.p.player))
        self.assertFalse(apply_inventory_action(token,self.p.inventory,self.p.player,{})[0])
        ui={"tab":"TODOS","selected":token,"consumable_cooldown":0}
        draw_inventory(pygame.Surface((1024,576)),self.p.inventory,pygame.font.Font(None,22),
                       pygame.font.Font(None,30),self.p.player,ui,(0,0))
        self.save(); loaded=self.reload()
        self.assertEqual(next(i for i in loaded.inventory if i["id"]=="escort_token"),token)
        self.assertFalse(next(o for o in loaded.region["interactables"] if o.uid=="post_token").available())

    def test_pickup_reload_resumes_memory_and_reverse_document_order(self):
        self.examine("post_breach"); self.examine("post_token")
        self.p.player.x,self.p.player.y=650,480
        self.save(); loaded=self.reload()
        scene=post.moment_at(loaded.player,loaded.region,loaded.story,[],main.load)
        self.assertEqual(scene.kind,"memory")
        self.assertTrue(scene.update(6950,loaded.story,loaded.quests))
        self.assertIsNone(post.moment_at(loaded.player,loaded.region,loaded.story,[],main.load))
        self.examine("post_roster")
        self.assertTrue(self.p.story.get("watchpost_identity_confirmed"))

    def test_memory_is_fragmented_uses_current_actors_and_commits_once(self):
        self.examine("post_breach"); self.examine("post_token")
        self.p.player.x,self.p.player.y=650,480
        self.p.player.attack_timer=12; self.p.player.dash_timer=7
        scene=post.moment_at(self.p.player,self.p.region,self.p.story,[],main.load)
        self.assertEqual(sum(b.duration_ms for b in scene.sequence.beats),6950)
        self.assertEqual(self.p.player.attack_timer,0); self.assertEqual(self.p.player.dash_timer,0)
        scene.update(1000,self.p.story,self.p.quests)
        self.assertTrue(scene.memory_visible); self.assertEqual(len(scene.world_actors),3)
        self.assertTrue(all(s.own_art for s in scene.soldiers))
        canvas=pygame.Surface((768,432)); scene.past.draw(canvas,(560,200))
        scene.update(3000,self.p.story,self.p.quests)
        self.assertEqual(scene.sequence.index,6)
        scene.past.draw(canvas,(560,200))  # Actual authored hand/weapon pose.
        self.assertFalse(self.p.story.get("watchpost_flashback_seen"))
        self.assertTrue(scene.update(2950,self.p.story,self.p.quests))
        self.assertTrue(self.p.story.get("watchpost_search_noticed"))
        self.assertFalse(scene.finish(self.p.story,self.p.quests))

    def test_presence_waits_for_main_evidence_and_a_safe_room(self):
        self.p.player.x,self.p.player.y=850,470
        self.assertIsNone(post.moment_at(self.p.player,self.p.region,self.p.story,[],main.load))
        self.main_evidence()
        foe=self.p.enemies[0]; foe.x,foe.y=850,530; foe.state="CHASE"
        self.assertTrue(post.threatened(self.p.player,[foe],self.p.region))
        self.assertIsNone(post.moment_at(self.p.player,self.p.region,self.p.story,[foe],main.load))
        scene=post.moment_at(self.p.player,self.p.region,self.p.story,[],main.load)
        self.assertEqual(scene.kind,"presence")
        closed_door=pygame.image.tobytes(self.p.region["postern_visual"].image,"RGBA")
        self.assertFalse(scene.update(700,self.p.story,self.p.quests))
        self.assertNotEqual(pygame.image.tobytes(self.p.region["postern_visual"].image,"RGBA"),closed_door)
        self.assertIn(self.p.region["postern_block"],self.p.region["obstacles"])
        self.assertTrue(scene.update(1900,self.p.story,self.p.quests))
        self.assertTrue(self.p.story.get("watchpost_presence_seen"))
        self.assertTrue(self.target("post_trail").available())
        self.assertEqual(self.p.story.objective_text,"Investigue o antigo posto de vigia.")
        self.examine("post_trail")
        self.assertEqual(self.p.story.objective_text,"Encontre quem estava no posto.")
        future=self.world.transition("watchpost","pursuit",self.p.quests,set(),
                                     save_manager.prepare_region,None,source_region=self.p.region)
        self.assertEqual(future.region_id,"pursuit")

    def test_save_each_discovery_and_reject_impossible_or_duplicate_states(self):
        for uid in ("post_breach","post_archive","post_dispatch","post_roster","post_token"):
            self.examine(uid); self.save(); loaded=self.reload()
            self.assertEqual(loaded.story.to_dict(),self.p.story.to_dict())
        scene=post.PostMomentScene("memory",self.p.player,self.p.region,main.load)
        scene.finish(self.p.story,self.p.quests)
        post.PostMomentScene("presence",self.p.player,self.p.region,main.load).finish(self.p.story,self.p.quests)
        self.examine("post_trail"); self.save(); loaded=self.reload()
        self.assertEqual(loaded.story.objective_text,"Encontre quem estava no posto.")
        self.assertIn("pursuit",loaded.region["exits"])
        self.assertIsNone(post.moment_at(loaded.player,loaded.region,loaded.story,[],main.load))
        data=save_manager.read_save(self.path)
        for flag in ("watchpost_entered","watchpost_entry_open","watchpost_personal_item_found",
                     "watchpost_roster_read","watchpost_blue_order_found","watchpost_flashback_seen",
                     "watchpost_presence_seen"):
            bad=deepcopy(data); bad["story"][flag]=False
            with self.assertRaises(save_manager.SaveError): save_manager.validate(bad)
        bad=deepcopy(data)
        next(i for i in bad["inventory"] if i["id"]=="escort_token")["amount"]=2
        with self.assertRaises(save_manager.SaveError): save_manager.validate(bad)

    def test_localized_existing_enemies_take_real_sword_hits_and_stay_defeated(self):
        self.examine("post_breach")
        self.assertEqual([e.kind for e in self.p.enemies],["warrior","slime"])
        combat=CombatSystem(main.load); defeated=[]
        with patch.object(pygame.key,"get_pressed",return_value=defaultdict(bool)):
            for enemy in self.p.enemies:
                self.assertFalse(any(enemy.hitbox.colliderect(b) for b in self.p.region["obstacles"]))
                self.assertLessEqual(enemy.config["perception"],110)
                self.p.player.x,self.p.player.y=enemy.x,enemy.y+44
                for _ in range(280):
                    self.p.player.facing=3; self.p.player.attack()
                    frame=combat.update(self.p.player,"watchpost",self.p.region,[enemy],[],
                                        self.p.inventory,self.p.quests,0)
                    defeated.extend(frame.defeated_watchpost_enemies)
                    if frame.defeated_watchpost_enemies: break
                self.assertEqual(enemy.state,"DEAD")
                self.assertGreater(self.p.player.hp,0)
                for index in frame.defeated_watchpost_enemies:
                    self.p.story.set(f"watchpost_enemy_{index}_defeated")
        self.assertEqual(defeated,[0,1])
        self.save(); self.assertEqual(self.reload().enemies,[])

    def test_runtime_entry_investigation_memory_departure_autosave_and_reload(self):
        self.p.region_id="old_road"; self.p.region=self.world.build_region("old_road")
        self.p.story.set("watchpost_entered",False)
        for i in range(4): self.p.story.set(f"road_enemy_{i}_defeated")
        self.p.story.apply_to_region(self.p.region)
        self.p.player.x,self.p.player.y=889,330; self.save()
        current={}; keys=defaultdict(bool)
        state={"poll":0,"stage":"entry","kinds":set(),"fade":False,"reloaded":False}
        original_draw=GameRenderer.draw
        def events():
            state["poll"]+=1; self.assertLess(state["poll"],230)
            if state["poll"]==1: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F4)]
            if state["poll"]==2:
                keys[pygame.K_w]=True
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F9)]
            if not current: return []
            if current["dialogue"].active: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            if current.get("watchpost_scene") is not None: return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE)]
            if current["region"]["name"]!="Posto de Vigia": return []
            keys[pygame.K_w]=False
            if current["transition_fade"].active: return []
            player,story=current["player"],current["story"]
            stage=state["stage"]
            points={"entry":((768,840),"breach"),"breach":((1240,703),"archive"),
                    "archive":((681,630),"dispatch"),"dispatch":((995,587),"roster"),
                    "roster":((973,341),"token"),"token":((647,480),"end")}
            if stage in points:
                if stage=="entry": current["enemies"].clear()  # Combat has its own real-hit test.
                if story.get("watchpost_entry_open"):
                    for i in range(2): story.set(f"watchpost_enemy_{i}_defeated")
                player.x,player.y=points[stage][0]; state["stage"]=points[stage][1]
                if stage=="entry":
                    return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F3),
                            pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            if stage=="end" and story.get("watchpost_presence_seen"):
                player.x,player.y=1230,329; state["stage"]="reload"
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)]
            if stage=="reload" and story.get("watchpost_trail_found"):
                state["stage"]="check"
                return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F9)]
            if stage=="check":
                self.assertEqual(story.objective_text,"Encontre quem estava no posto.")
                self.assertIsNone(current.get("watchpost_scene"))
                self.assertEqual(sum(i["amount"] for i in current["inventory"] if i["id"]=="escort_token"),1)
                self.assertEqual(current["enemies"],[])
                state["reloaded"]=True
                return [pygame.event.Event(pygame.QUIT)]
            return []
        def observe(renderer,canvas,**kwargs):
            current.update(kwargs); state["fade"]|=kwargs["transition_fade"].alpha>0
            scene=kwargs.get("watchpost_scene")
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
        self.assertTrue(state["fade"]); self.assertTrue(state["reloaded"])
        self.assertEqual(state["kinds"],{"memory","presence"})
        self.assertTrue(save_manager.read_save(self.path)["story"]["watchpost_trail_found"])


if __name__=="__main__": unittest.main()
