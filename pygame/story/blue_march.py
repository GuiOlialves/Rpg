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


def _blue_uniform(sheet, palette):
    """Recolor uniform pixels on a supplied character sheet, retaining its art."""
    result = sheet.copy()
    with pygame.PixelArray(result) as pixels:
        for source, target in palette.items():
            pixels.replace(source, target)
    return result


def blue_commander_sprite(load):
    """Return the same blue-uniform civilian sprite used for the 2C commander."""
    return _blue_uniform(load("assets/npc/civilian_customer.png"), {
        (175, 63, 39): (35, 83, 151),
        (160, 49, 38): (22, 57, 111),
        (194, 78, 41): (45, 104, 191),
        (132, 38, 38): (16, 42, 91),
        (209, 94, 37): (67, 128, 206),
        (225, 116, 33): (94, 151, 224),
    })


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
        seller = _blue_uniform(load("assets/npc/civilian_seller.png"), {
            (69, 49, 98): (30, 62, 130),
            (101, 59, 130): (48, 91, 176),
            (90, 55, 118): (36, 76, 154),
            (146, 70, 167): (72, 119, 211),
            (127, 68, 155): (59, 102, 191),
            (55, 45, 81): (23, 48, 105),
            (84, 25, 31): (22, 49, 105),
            (96, 26, 29): (29, 63, 132),
            (114, 30, 28): (35, 76, 155),
        })
        customer = blue_commander_sprite(load)
        commander = NPC("blue_march_commander", "Comandante Azul", (0, 0), {},
                        customer, frame_size=32, draw_size=64)
        troops = [NPC(f"blue_march_soldier_{index}", "Soldado Azul", (0, 0), {},
                      seller, frame_size=32, draw_size=64)
                  for index in range(1, 4)]
        return [commander, *troops]

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
