"""Investigation milestones, a brief fragmented memory and an unseen departure."""
from array import array
import math
import random
import pygame
from entities.npc import NPC
from story.chapter1_return import settle_player
from story.sequence import Beat, NarrativeSequence
from systems.inventory import add_inventory_item
from systems.items import quest_item
from world.regions.watchpost_art import prop

POST_FLAGS = (
    "watchpost_entered", "watchpost_entry_open", "watchpost_archive_read",
    "watchpost_dispatch_read", "watchpost_roster_read", "watchpost_personal_item_found",
    "watchpost_identity_confirmed", "watchpost_blue_order_found", "watchpost_flashback_seen",
    "watchpost_search_noticed", "watchpost_presence_seen", "watchpost_trail_found",
    "watchpost_enemy_0_defeated", "watchpost_enemy_1_defeated",
)
MAIN_EVIDENCE = ("watchpost_identity_confirmed", "watchpost_flashback_seen",
                 "watchpost_blue_order_found")


def apply_post_state(region, story):
    region["story_phase"] = "post_departure" if story.get("watchpost_trail_found") else "post_investigation"
    for flag, key, visual in (("watchpost_entry_open", "breach_block", "breach_visual"),
                              ("watchpost_presence_seen", "postern_block", "postern_visual")):
        block = region[key]
        if story.get(flag):
            region["obstacles"] = [box for box in region["obstacles"] if box != block]
            if visual == "breach_visual" and region[visual] in region["scenery"]:
                region["scenery"].remove(region[visual])
            if visual == "postern_visual":
                region[visual].image = prop("postern")
        elif block not in region["obstacles"]:
            region["obstacles"].append(block.copy())
    for target in region["interactables"]:
        flag = getattr(target, "story_flag", None)
        if not flag: continue
        if target.uid == "post_trail":
            target.enabled = story.get("watchpost_presence_seen") and not story.get(flag)
        elif target.uid in {"post_archive", "post_dispatch", "post_roster"}:
            target.enabled = story.get("watchpost_entry_open")  # Documents remain rereadable.
        else:
            target.enabled = not story.get(flag)
        if target.uid == "post_token" and story.get(flag):
            target.image = pygame.Surface((1,1),pygame.SRCALPHA)
    if story.get("watchpost_trail_found"):
        region["exits"]["pursuit"] = pygame.Rect(1480, 152, 56, 96)


def can_examine(player, target, region):
    return not any(box.clipline((player.x,player.y),(target.x,target.y))
                   for box in region["obstacles"])


def complete_evidence(target, player, inventory, story, region, quests):
    flag = getattr(target, "story_flag", None)
    if not flag or story.get(flag): return False
    story.set(flag)
    if flag == "watchpost_personal_item_found":
        add_inventory_item(inventory, quest_item("escort_token"))
    if flag == "watchpost_dispatch_read":
        story.set("watchpost_blue_order_found")
    if story.get("watchpost_roster_read") and story.get("watchpost_personal_item_found"):
        story.set("watchpost_identity_confirmed")
        quests.notice, quests.notice_timer = "R-17: o registro e a identificação pertencem a você.", 240
    if flag == "watchpost_trail_found":
        quests.notice, quests.notice_timer = "Ecos da Guerra: encontre quem estava no posto.", 300
    story.apply_to_region(region)
    settle_player(player)
    return True


def threatened(player, enemies, region=None):
    # Do not suspend an occupied fight, even while a nearby enemy is recovering.
    return any(enemy.alive and math.dist((enemy.x,enemy.y),(player.x,player.y)) < 210
               and (region is None or not any(box.clipline((player.x,player.y),(enemy.x,enemy.y))
                                             for box in region["obstacles"]))
               for enemy in enemies)


def moment_at(player, region, story, enemies, load):
    if threatened(player, enemies, region): return None
    if (story.get("watchpost_personal_item_found") and not story.get("watchpost_flashback_seen")
            and math.dist((player.x,player.y),(647,471)) < 120):
        return PostMomentScene("memory", player, region, load)
    if (not story.get("watchpost_presence_seen") and all(story.get(f) for f in MAIN_EVIDENCE)
            and region["presence_trigger"].collidepoint(player.x,player.y)):
        return PostMomentScene("presence", player, region, load)
    return None


class _PastPlayer:
    uid = "post_memory_protagonist"
    def __init__(self, scene):
        self.scene = scene
        self.x, self.y = 948, 402

    def draw(self, canvas, camera):
        visual = self.scene.player.visual
        holding = self.scene.sequence.index == 6
        state, index, facing = ("attack", 1, 2) if holding else ("idle", 0, 0)
        canvas.blit(visual.image(state, facing, index), visual.body_origin(self.x,self.y,camera))
        if holding:
            canvas.blit(visual.weapons[facing][index], visual.weapon_origin(self.x,self.y,camera))


class _PassingShadow:
    uid = "post_departure_shadow"
    has_embedded_shadow = True
    def __init__(self, scene):
        self.scene = scene
        self.x, self.y = 1164, 340
        self.image = pygame.Surface((44,14), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (18,23,22,130), (0,3,40,9))
        pygame.draw.rect(self.image, (18,23,22,110), (21,0,6,6))

    def draw(self, canvas, camera):
        beat = self.scene.sequence
        if beat.index != 1: return
        t = (beat.current.duration_ms - beat.remaining_ms) / beat.current.duration_ms
        canvas.blit(self.image, (round(self.x-camera[0]-14+t*55), round(self.y-camera[1])))


def _footsteps():
    """Soft distant impacts; optional if the machine has no audio device."""
    settings = pygame.mixer.get_init()
    if not settings or settings[1] != -16: return None
    rate, _, channels = settings
    rng, samples = random.Random(17), array("h")
    for i in range(round(rate*.52)):
        t = i / rate
        value = 0
        for start in (0.0,.24):
            elapsed = t-start
            if 0 <= elapsed < .10:
                value += (math.sin(elapsed*math.tau*95)*.65 + rng.uniform(-.35,.35)) * math.exp(-elapsed*42)
        samples.extend([round(value*2600)]*channels)
    return pygame.mixer.Sound(buffer=samples)


class PostMomentScene:
    def __init__(self, kind, player, region, load):
        self.kind, self.player, self.region = kind, player, region
        self.active, self.elapsed_ms = True, 0
        settle_player(player)
        self.focus = (player.x, player.y) if kind == "memory" else region["presence_focus"]
        self.sequence = NarrativeSequence((
            Beat("Isso era meu.",650,"world"), Beat(None,180),
            Beat("Você recebeu suas ordens.",1250,"world"), Beat(None,180),
            Beat("Se eles chegarem antes de nós...",1000,"world"), Beat(None,180),
            Beat("Não hesite desta vez.",1250,"world"), Beat(None,240),
            Beat(None,420,"world"),
            Beat("O posto foi revistado. Alguém procurava alguma coisa.",1600,"world"))
            if kind == "memory" else (
                Beat(None,350,"world"), Beat("...Passos?",850,"world"),
                Beat("A porta lateral. Alguém acabou de sair.",1400,"world")))
        self.sequence.start()
        self.past = _PastPlayer(self)
        self.shadow = _PassingShadow(self)
        self.soldiers = []
        if kind == "memory":
            for i, pos in enumerate(((860,492),(1058,458))):
                actor = NPC(f"post_memory_red_{i}","Soldado Vermelho",pos,{},
                            load(f"assets/vale_characters/red_soldier_{i}_idle.png"),frame_size=32,draw_size=48)
                actor.enabled = False
                actor.facing = 2 if i == 0 else 1
                self.soldiers.append(actor)
        self.sound = _footsteps() if kind == "presence" else None
        self.open_door_image = prop("postern") if kind == "presence" else None
        self.sound_played = False

    @property
    def memory_visible(self):
        return self.active and self.kind == "memory" and self.sequence.index in (2,4,6)

    @property
    def world_actors(self):
        if self.memory_visible: return (*self.soldiers, self.past)
        return (self.shadow,) if self.active and self.kind == "presence" else ()

    def update(self, delta_ms, story, quests):
        if not self.active: return False
        self.elapsed_ms += max(0,delta_ms)
        if self.sound and not self.sound_played and self.elapsed_ms >= 350:
            self.sound.play(); self.sound_played = True
        if self.open_door_image is not None and self.elapsed_ms >= 550:
            self.region["postern_visual"].image = self.open_door_image
        if self.sequence.update(delta_ms): return self.finish(story,quests)
        if self.memory_visible:
            self.focus = ((925,434),(971,477),(948,374))[(self.sequence.index-2)//2]
        else:
            self.focus = (self.player.x,self.player.y) if self.kind == "memory" else self.region["presence_focus"]
        return False

    def finish(self, story, quests):
        if not self.active: return False
        if self.kind == "memory":
            story.set("watchpost_flashback_seen")
            story.set("watchpost_search_noticed")
        else:
            story.set("watchpost_presence_seen")
        if self.sound: self.sound.stop()
        story.apply_to_region(self.region)
        settle_player(self.player)
        self.active = False
        self.sequence = None
        return True

    def draw_overlay(self, canvas):
        if not self.memory_visible: return
        veil = pygame.Surface(canvas.get_size(),pygame.SRCALPHA)
        veil.fill((36,28,25,62)); canvas.blit(veil,(0,0))
        # Fixed pixel bands and brief black cuts keep the image fragmented.
        if self.sequence.remaining_ms > self.sequence.current.duration_ms-90:
            pygame.draw.rect(canvas,(20,23,23),(0,132,canvas.width,8))
            pygame.draw.rect(canvas,(20,23,23),(0,410,canvas.width,5))
