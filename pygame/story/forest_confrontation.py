"""The wounded blue commander and the red officer's final line of 2E."""
import pygame

from entities.npc import NPC
from story.arrival_scene import ScriptedDialogue
from story.sequence import Beat, NarrativeSequence


REVELATION_LINES = (
    ("Comandante Azul", "..."),
    ("Comandante Azul", "Então era você."),
    ("Protagonista", "Você sabe quem eu sou."),
    ("Comandante Azul", "Eu reconheci um fantasma."),
    ("Protagonista", "Isso era meu?"),
    ("Protagonista", "Quem sou eu?"),
    ("Comandante Azul", "Isso importa?"),
    ("Protagonista", "É a única coisa que importa."),
    ("Comandante Azul", "Não."),
    ("Comandante Azul", "Você acha que quer saber."),
    ("Protagonista", "Tiraram minhas memórias."),
    ("Comandante Azul", "Tiraram?"),
    ("Comandante Azul", "Foi isso que disseram para você?"),
    ("Protagonista", "Quem?"),
    ("Comandante Azul", "Você não perdeu suas memórias."),
    ("Comandante Azul", "Você pediu para esquecê-las."),
)

OFFICER_LINES = (
    ("Protagonista", "Você também me conhece?"),
    ("Oficial Vermelho", "Conhecer você?"),
    ("Oficial Vermelho", "Eu enterrei você."),
)


class _WoundedCommander:
    has_embedded_shadow = True
    config = {"hitbox_radius": 22}

    def __init__(self, sprite, position):
        self.frame = sprite.subsurface((0, 0, 32, 32)).copy()
        self.x, self.center_y = position
        self.y = self.center_y + 26
        self.image = pygame.transform.rotate(
            pygame.transform.scale(self.frame, (72, 72)), -76)

    def look_back(self):
        # A slight lift/turn is enough to make his reaction readable while prone.
        self.image = pygame.transform.rotate(
            pygame.transform.scale(self.frame, (72, 72)), -48)

    def draw(self, canvas, camera):
        canvas.blit(self.image, (round(self.x - self.image.get_width() / 2 - camera[0]),
                                 round(self.center_y - self.image.get_height() / 2 - camera[1])))


class _ShownInsignia:
    has_embedded_shadow = True

    def __init__(self, player, image):
        self.player = player
        self.image = pygame.transform.scale(image, (20, 25))
        self.x = self.y = self.draw_x = self.draw_y = 0

    def draw(self, canvas, camera):
        self.draw_x = self.player.x + 16
        self.draw_y = self.player.y - 31
        canvas.blit(self.image, (round(self.draw_x - camera[0]),
                                 round(self.draw_y - camera[1])))


class _RedOfficer(NPC):
    """Tiny Swords officer sprite with explicit left/right inspection turns."""

    def draw(self, canvas, camera):
        sheet = self.run_sprite if self.running and self.run_sprite else self.sprite
        frame_count = max(1, sheet.get_width() // self.frame_size)
        frame_index = (self.anim_tick // 5) % frame_count if self.running else 0
        frame = sheet.subsurface((frame_index * self.frame_size, 0,
                                  self.frame_size, self.frame_height)).copy()
        if self.facing == 1:
            frame = pygame.transform.flip(frame, True, False)
        source_foot = frame.get_bounding_rect().bottom
        scaled_height = max(1, round(self.draw_size * self.frame_height / self.frame_size))
        frame = pygame.transform.scale(frame, (self.draw_size, scaled_height))
        foot = round(source_foot * scaled_height / self.frame_height)
        canvas.blit(frame, (round(self.x - self.draw_size / 2 - camera[0]),
                            round(self.y - foot - camera[1])))


class RedOfficerScene:
    """Runs once after the insignia memory; F4 applies its completed state."""

    def __init__(self, player, dialogue, story, region, load):
        self.player = player
        self.dialogue = dialogue
        self.story = story
        self.region = region
        self.active = True
        self.phase = "revelation"
        self.sequence = None
        self.elapsed_ms = 0
        self.dialogue_actor = ScriptedDialogue(REVELATION_LINES)
        self.reaction_actor = ScriptedDialogue((("Comandante Azul", "Não..."),))
        self.officer_dialogue = ScriptedDialogue(OFFICER_LINES)
        self.commander = _WoundedCommander(
            region["wounded_commander_sprite"], region["red_officer_trigger"])
        commander_prop = region.get("wounded_commander_object")
        if commander_prop in region.get("objects", []):
            region["objects"].remove(commander_prop)
        badge = region["forest_battlefield_interactables"]["insignia"].image
        self.shown_insignia = _ShownInsignia(player, badge)
        idle = load("sprites_meu/Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/Units/Red Units/Warrior/Warrior_Idle.png")
        run = load("sprites_meu/Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/Units/Red Units/Warrior/Warrior_Run.png")
        self.officer = _RedOfficer(
            "red_officer_scene", "Oficial Vermelho", (0, 0), {},
            idle, run_sprite=run, frame_size=192, draw_size=94)
        self.officer.x = player.x - 260
        self.officer.y = player.y - 4
        self.officer.running = False
        self.officer_target_x = player.x - 112
        self.player.facing = 2
        self.player.walk_frame = 0
        self.dialogue.open(self.dialogue_actor)

    @property
    def world_actors(self):
        if not self.active:
            return ()
        actors = [self.commander]
        if (self.phase == "revelation" and self.dialogue.active
                and self.dialogue.npc is self.dialogue_actor
                and self.dialogue.index >= 4):
            self.shown_insignia.x = self.player.x + 16
            self.shown_insignia.y = self.player.y + 1
            actors.append(self.shown_insignia)
        if self.phase in {"officer_approach", "officer_inspection", "officer_dialogue"}:
            actors.append(self.officer)
        return tuple(actors)

    def advance(self):
        if not self.active or self.sequence is not None or not self.dialogue.active:
            return False
        closed = self.dialogue.advance()
        if closed is self.dialogue_actor:
            self.phase = "footsteps"
            self.sequence = NarrativeSequence((Beat("Passos...", 1050, background="world"),))
            self.sequence.start()
        elif closed is self.reaction_actor:
            self.phase = "officer_approach"
            self.elapsed_ms = 0
            self.officer.x = self.player.x - 260
            self.officer.y = self.player.y - 4
            self.officer.running = True
        elif closed is self.officer_dialogue:
            return self.finish()
        return False

    def update(self, delta_ms):
        if not self.active:
            return False
        delta_ms = max(0, int(delta_ms))
        if self.sequence is not None:
            if self.sequence.update(delta_ms):
                self.sequence = None
                self.commander.look_back()
                self.phase = "commander_reaction"
                self.dialogue.open(self.reaction_actor)
            return False
        if self.phase == "officer_approach":
            self.elapsed_ms = min(900, self.elapsed_ms + delta_ms)
            progress = self.elapsed_ms / 900
            self.officer.x = self.player.x - 260 + 148 * progress
            self.officer.anim_tick += max(1, round(delta_ms / (1000 / 60)))
            if self.elapsed_ms >= 900:
                self.officer.running = False
                self.phase = "officer_inspection"
                self.elapsed_ms = 0
                self.inspection_index = 0
                self.officer.facing = 2  # Commander.
        elif self.phase == "officer_inspection":
            self.elapsed_ms += delta_ms
            while self.elapsed_ms >= 310 and self.inspection_index < 3:
                self.elapsed_ms -= 310
                self.inspection_index += 1
                if self.inspection_index == 1:
                    self.officer.facing = 1  # Fallen soldiers.
                elif self.inspection_index == 2:
                    self.officer.facing = 2  # The protagonist.
                else:
                    self.phase = "officer_dialogue"
                    self.dialogue.open(self.officer_dialogue)
                    break
        return False

    def finish(self):
        if not self.active:
            return False
        if self.dialogue.npc in (self.dialogue_actor, self.reaction_actor,
                                 self.officer_dialogue):
            self.dialogue.npc = None
        self.story.set("red_officer_met", True)
        self.story.apply_to_region(self.region)
        self.sequence = None
        self.active = False
        self.player.attack_timer = 0
        self.player.dash_timer = self.player.dash_iframes = 0
        return True
