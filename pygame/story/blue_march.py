"""One-time blue-army march through the village after the house investigation."""
from entities.npc import NPC
from story.arrival_scene import ScriptedDialogue
from ui.character_art import character_sheet, fallen_image, DRAW_SIZE


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


BLUE_FRAME = 32
BLUE_SIZES = (DRAW_SIZE,) * 4
COMMANDER_FALLEN_SIZE = DRAW_SIZE


def blue_troop_sprite(load, variant=0, animation="Idle"):
    """The leader and three uniform variants share the same pixel grid."""
    character = "blue_commander" if variant == 0 else f"blue_soldier_{(variant - 1) % 3}"
    action = {"Idle": "idle", "Run": "walk", "Fallen": "fallen"}[animation]
    return character_sheet(load, character, action)


def blue_commander_sprite(load, animation="Idle"):
    return blue_troop_sprite(load, 0, animation)


def blue_fallen_sprite(sheet, draw_size=COMMANDER_FALLEN_SIZE, angle=-76):
    # Keep the scene's existing orientation/reaction calls, using drawn poses.
    return fallen_image(sheet, index=1 if angle == -48 else 0,
                        facing=2 if angle > 0 else 0, draw_size=draw_size)


class BlueTrooper(NPC):
    """Stable foot pivot and facing across the military idle/run animations."""
    def draw(self, canvas, camera):
        super().draw(canvas,camera)


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
        self.lead_x = -80.0
        self.dialogue_actor = ScriptedDialogue(COMMANDER_LINES)
        self.actors = self._make_column(load)
        self.player.walk_frame = 0
        self.player.invulnerability_timer = 0
        self.player.attack_timer = self.player.dash_timer = self.player.dash_iframes = 0
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
            self.lead_x = min(self.APPROACH_X, self.lead_x + delta_ms * 0.24)
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
