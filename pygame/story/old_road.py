"""Brief road recognition and the exterior reveal; no watchpost interior."""
import math
import pygame
from story.chapter1_return import settle_player
from story.sequence import Beat, NarrativeSequence


class RoadMomentScene:
    def __init__(self, kind, player, region):
        self.kind, self.player, self.region = kind, player, region
        self.active = True
        settle_player(player)
        self.focus = region["watchpost_focus"] if kind == "post" else (player.x,player.y)
        self.flag = "road_memory_seen" if kind == "memory" else "watchpost_seen"
        self.sequence = NarrativeSequence(
            (Beat(None,250,"world"),Beat("Continue andando.",550,"world"),
             Beat(None,260,"world"),Beat("Eu conheço esse caminho...",900,"world"))
            if kind == "memory" else
            (Beat(None,450,"world"),Beat("Deve ser esse o lugar.",1500,"world"),
             Beat(None,500,"world")))
        self.sequence.start()
        self.player.facing = 3 if kind == "post" else 1
        self.boots = [player.visual.image("walk",1,i).subsurface((0,50,64,20)).copy()
                      for i in (2,6)]
        self.echo = _BootEcho(self)

    @property
    def world_actors(self):
        return (self.echo,) if self.active and self.kind == "memory" and self.sequence.index <= 1 else ()

    def update(self, delta_ms, story, quests):
        if self.active and self.sequence.update(delta_ms):
            return self.finish(story,quests)
        return False

    def finish(self, story, quests):
        if not self.active:
            return False
        story.set(self.flag)
        story.apply_to_region(self.region)
        if self.kind == "post":
            quests.notice = "Ecos da Guerra: investigue o antigo posto de vigia."
            quests.notice_timer = 300
        self.active = False
        self.sequence = None
        return True

    def draw_overlay(self, canvas):
        if self.kind != "memory" or self.sequence.index > 1:
            return
        veil = pygame.Surface(canvas.get_size(),pygame.SRCALPHA)
        veil.fill((37,43,47,62))
        canvas.blit(veil,(0,0))


class _BootEcho:
    has_embedded_shadow = True
    def __init__(self, scene):
        self.scene = scene
        self.x, self.y = scene.player.x-40,scene.player.y-8
        self.depth = self.y

    def draw(self, canvas, camera):
        # The only remembered image is an anonymous pair of walking boots.
        sequence = self.scene.sequence
        elapsed = 250-sequence.remaining_ms if sequence.index==0 else 800-sequence.remaining_ms
        boots = self.scene.boots[elapsed//140%2].copy()
        boots.set_alpha(105)
        canvas.blit(boots,(round(self.x-camera[0]-32-elapsed*.022),
                           round(self.y-camera[1]-20)))


def threatened(player, enemies):
    return any(enemy.state not in {"DEAD","DEFEATED"}
               and enemy.state in {"CHASE","ATTACK"}
               and math.hypot(player.x-enemy.x,player.y-enemy.y)<240 for enemy in enemies)


def moment_at(player, region, story, enemies):
    if threatened(player,enemies):
        return None
    if (not story.get("road_memory_seen")
            and math.dist((player.x,player.y),region["memory_point"])<75):
        return RoadMomentScene("memory",player,region)
    if (not story.get("watchpost_seen") and story.get("road_camp_found")
            and story.get("road_red_clue_found") and story.get("road_memory_seen")
            and region["lookout"].collidepoint(player.x,player.y)):
        return RoadMomentScene("post",player,region)
    return None


def apply_road_state(region, story):
    region["story_phase"] = "road_watchpost" if story.get("watchpost_seen") else "road_investigation"
    for clue in region.get("interactables",()):
        flag = getattr(clue,"story_flag",None)
        if flag:
            clue.enabled = not story.get(flag)
    if story.get("watchpost_seen"):
        region["exits"].pop("watchpost_future", None)
        region["exits"]["watchpost"] = pygame.Rect(810,248,100,38)


def complete_clue(target, story, region):
    flag = getattr(target,"story_flag",None)
    if not flag or story.get(flag):
        return False
    story.set(flag)
    story.apply_to_region(region)
    return True
