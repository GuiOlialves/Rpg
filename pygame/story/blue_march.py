"""One-time blue-army march through the village after the house investigation."""
import pygame

from entities.npc import NPC
from story.arrival_scene import ScriptedDialogue


COMMANDER_LINES = (
    ("Comandante Azul", "Você."),
    ("Comandante Azul", "Saia da estrada."),
    ("Protagonista", "O que está acontecendo?"),
    ("Comandante Azul", "Não é problema seu."),
    ("Protagonista", "Um exército atravessando a vila parece problema de todo mundo."),
    ("Comandante Azul", "Encontramos tropas de █████ além da floresta."),
    ("Protagonista", "De quem?"),
    ("Comandante Azul", "█████."),
    ("Protagonista", "Não ouvi."),
    ("Comandante Azul", "Eu disse █████."),
    ("Comandante Azul", "..."),
    ("Comandante Azul", "Já nos encontramos?"),
    ("Protagonista", "Eu não sei."),
    ("Comandante Azul", "Espero que continue assim."),
    ("Comandante Azul", "Companhia! Em marcha!"),
)


BLUE_FRAME = 192
BLUE_SIZES = (88, 82, 80, 84)
BLUE_TINTS = ((255, 242, 206), (255, 255, 255),
              (220, 235, 255), (245, 235, 220))


def blue_troop_sprite(load, variant=0, animation="Idle"):
    """One military atlas, with subtle uniform variations shared by fallen poses."""
    sheet = load("sprites_meu/Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/"
                 f"Units/Blue Units/Warrior/Warrior_{animation}.png").copy()
    sheet.fill(BLUE_TINTS[variant], special_flags=pygame.BLEND_RGB_MULT)
    return sheet


def blue_commander_sprite(load):
    return blue_troop_sprite(load, 0)


def blue_fallen_sprite(sheet, draw_size=BLUE_SIZES[0], angle=-76):
    frame = pygame.transform.scale(sheet.subsurface((0, 0, BLUE_FRAME, BLUE_FRAME)),
                                   (draw_size, draw_size))
    return pygame.transform.rotate(frame.subsurface(frame.get_bounding_rect()), angle)


class BlueTrooper(NPC):
    """Stable foot pivot and facing across the military idle/run animations."""
    def draw(self, canvas, camera):
        sheet = self.run_sprite if self.running else self.sprite
        index = (self.anim_tick // 8) % (sheet.get_width() // BLUE_FRAME) if self.running else 0
        frame = sheet.subsurface((index * BLUE_FRAME, 0, BLUE_FRAME, BLUE_FRAME))
        if self.facing == 1:
            frame = pygame.transform.flip(frame, True, False)
        frame = pygame.transform.scale(frame, (self.draw_size, self.draw_size))
        foot = self.sprite.subsurface((0, 0, BLUE_FRAME, BLUE_FRAME)).get_bounding_rect().bottom
        canvas.blit(frame, (round(self.x - self.draw_size / 2 - camera[0]),
                            round(self.y - foot * self.draw_size / BLUE_FRAME - camera[1])))


class BlueMarchScene:
    """A short fixed-route column, a dialogue pause, then a march toward the forest."""

    APPROACH_X = 480
    ROAD_Y = 550
    DEPARTURE_X = 2140

    def __init__(self, player, dialogue, load):
        self.player = player
        self.dialogue = dialogue
        self.active = True
        self.phase = "approach"
        self.lead_x = 280.0
        self.dialogue_actor = ScriptedDialogue(COMMANDER_LINES)
        self.actors = self._make_column(load)
        self.player.walk_frame = 0
        self.player.facing = 1
        self._place_column()

    @staticmethod
    def _make_column(load):
        return [BlueTrooper(
            "blue_march_commander" if index == 0 else f"blue_march_soldier_{index}",
            "Comandante Azul" if index == 0 else "Soldado Azul", (0, 0), {},
            blue_troop_sprite(load, index), run_sprite=blue_troop_sprite(load, index, "Run"),
            frame_size=BLUE_FRAME, draw_size=size)
            for index, size in enumerate(BLUE_SIZES)]

    @property
    def world_actors(self):
        return tuple(self.actors) if self.active else ()

    def _place_column(self):
        for index, actor in enumerate(self.actors):
            actor.x = self.lead_x - index * 58
            actor.y = self.ROAD_Y + (index % 2) * 12
            actor.facing = 2

    def _start_dialogue(self):
        self.phase = "dialogue"
        for actor in self.actors:
            actor.running = False
        self.actors[0].face_player(self.player)
        self.dialogue.open(self.dialogue_actor)

    def advance(self):
        if self.active and self.phase == "dialogue":
            closed = self.dialogue.advance()
            if closed is self.dialogue_actor:
                self.phase = "departing"
                for actor in self.actors:
                    actor.running = True

    def update(self, delta_ms, story):
        if not self.active:
            return False
        delta_ms = max(0, int(delta_ms))
        if self.phase == "approach":
            self.lead_x = min(self.APPROACH_X, self.lead_x + delta_ms * 0.16)
            for actor in self.actors:
                actor.running = True
                actor.anim_tick += max(1, round(delta_ms / (1000 / 60)))
            self._place_column()
            if self.lead_x >= self.APPROACH_X:
                self._start_dialogue()
        elif self.phase == "departing":
            self.lead_x += delta_ms * 0.30
            for actor in self.actors:
                actor.anim_tick += max(1, round(delta_ms / (1000 / 60)))
            self._place_column()
            if self.lead_x >= self.DEPARTURE_X:
                return self.finish(story, self.dialogue)
        return False

    def finish(self, story, dialogue):
        """Apply the same departed state from the normal ending and F4 skip."""
        if not self.active:
            return False
        if dialogue.npc is self.dialogue_actor:
            dialogue.npc = None
        self.lead_x = self.DEPARTURE_X + len(self.actors) * 58
        self._place_column()
        for actor in self.actors:
            actor.running = False
        story.set("blue_army_departed", True)
        self.phase = "finished"
        self.active = False
        return True
