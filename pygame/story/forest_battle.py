"""Short scripted red-soldier encounters and the insignia memory."""
import pygame

from entities.enemy import Enemy
from entities.npc import NPC
from story.arrival_scene import ScriptedDialogue, Silhouette
from story.sequence import Beat, NarrativeSequence


AMBUSH_LINES = (
    ("Soldado Vermelho 1", "Espera."),
    ("Soldado Vermelho 1", "..."),
    ("Soldado Vermelho 1", "Não pode ser."),
    ("Soldado Vermelho 2", "O quê?"),
    ("Soldado Vermelho 1", "É ele."),
    ("Protagonista", "Você me conhece?"),
    ("Soldado Vermelho 2", "Ele está com eles!"),
    ("Protagonista", "Espera—"),
    ("Soldado Vermelho 2", "PEGA ELE!"),
)

INSIGNIA_MEMORY_LINES = (
    ("Voz masculina", "Pronto."),
    ("Voz masculina", "Agora você faz parte de nós."),
)

PRESENT_LINES = (
    ("Protagonista", "Eu..."),
    ("Protagonista", "Era um deles?"),
)


def spawn_red_group(index, region, load):
    positions = region["red_encounter_groups"][index]
    return [Enemy("red_soldier", position, load, seed=720 + index * 3 + offset)
            for offset, position in enumerate(positions)]


class RedAmbushScene:
    """The first two soldiers identify the protagonist before combat begins."""

    def __init__(self, player, dialogue, load, positions):
        self.player = player
        self.dialogue = dialogue
        self.active = True
        self.dialogue_actor = ScriptedDialogue(AMBUSH_LINES)
        idle = load("sprites_meu/Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/Units/Red Units/Warrior/Warrior_Idle.png")
        self.actors = [
            NPC(f"red_ambush_{index}", f"Soldado Vermelho {index + 1}", position,
                {}, idle, frame_size=192, draw_size=86)
            for index, position in enumerate(positions)
        ]
        for actor in self.actors:
            actor.face_player(player)
        self.player.walk_frame = 0
        self.dialogue.open(self.dialogue_actor)

    @property
    def world_actors(self):
        return tuple(self.actors) if self.active else ()

    def advance(self):
        if self.active and self.dialogue.advance() is self.dialogue_actor:
            return True
        return False

    def finish(self, dialogue, story):
        """F4 skips the exchange but still starts the first scripted fight."""
        if not self.active:
            return False
        if dialogue.npc is self.dialogue_actor:
            dialogue.npc = None
        story.set_forest_battle_progress(1)
        self.active = False
        return True


class _PlacedInsignia:
    has_embedded_shadow = True

    def __init__(self, player, image):
        self.player = player
        self.image = image
        self.x = player.x
        self.y = player.y
        self.center_y = player.y

    def place(self, elapsed_ms):
        progress = min(1.0, elapsed_ms / 430)
        self.x = self.player.x + 48 * (1 - progress)
        self.center_y = self.player.y - 47 + 20 * progress
        self.y = self.player.y + 1  # draw over the player's sprite at chest height

    def draw(self, canvas, camera):
        canvas.blit(self.image, (round(self.x - self.image.get_width() / 2 - camera[0]),
                                 round(self.center_y - self.image.get_height() / 2 - camera[1])))


class InsigniaMemoryScene:
    """A brief flash of an anonymous figure placing the found red insignia."""

    STEPS = (
        ("sequence", (Beat(None, 260, background="world"),
                       Beat(None, 520, background="world", fade_in_ms=200)), False, "out"),
        ("sequence", (Beat(None, 620, background="world", fade_in_ms=220),), True, "in"),
        ("dialogue", INSIGNIA_MEMORY_LINES, True, False),
        ("sequence", (Beat(None, 320, background="world", fade_in_ms=220),), False, "out"),
        ("dialogue", PRESENT_LINES, False, False),
    )

    def __init__(self, player, image, dialogue, load):
        self.player = player
        self.dialogue = dialogue
        self.image = image
        self.steps = self.STEPS
        self.index = 0
        self.sequence = None
        self.active = True
        self._memory_visible = False
        self._flash_alpha = 0
        self._memory_silhouette = Silhouette(load("assets/npc/civilian_seller.png"))
        self._placed_insignia = _PlacedInsignia(player, image)
        self._open_step()

    def _open_step(self):
        step_kind, content, self._memory_visible, fade_mode = self.steps[self.index]
        self.sequence = None
        if step_kind == "sequence":
            self.sequence = NarrativeSequence(content)
            self.sequence.start()
            if fade_mode:
                self.sequence.fade.start(fade_mode, 220)
        else:
            self.dialogue.open(ScriptedDialogue(content))

    @property
    def world_actors(self):
        if not self._memory_visible:
            return ()
        self._memory_silhouette.x = self.player.x + 44
        self._memory_silhouette.y = self.player.y + 2
        if self.sequence is not None and self.sequence.current is not None:
            beat = self.sequence.current
            self._placed_insignia.elapsed_ms = beat.duration_ms - self.sequence.remaining_ms
        else:
            self._placed_insignia.elapsed_ms = 500
        self._placed_insignia.place(self._placed_insignia.elapsed_ms)
        return self._memory_silhouette, self._placed_insignia

    def advance(self):
        if self.active and self.sequence is None:
            self.dialogue.advance()

    def update(self, delta_ms, story, region):
        if not self.active:
            return False
        if self._memory_visible:
            self._flash_alpha = min(44, self._flash_alpha + max(0, int(delta_ms)) // 18)
        if self.sequence is not None:
            if not self.sequence.update(delta_ms):
                return False
        elif self.dialogue.active:
            return False
        self.index += 1
        if self.index >= len(self.steps):
            return self.finish(story, region)
        self._open_step()
        return False

    def draw_overlay(self, canvas):
        if self._memory_visible:
            veil = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
            veil.fill((142, 35, 43, self._flash_alpha))
            canvas.blit(veil, (0, 0))

    def finish(self, story, region):
        if not self.active:
            return False
        if self.dialogue.npc is not None:
            self.dialogue.npc = None
        story.set("red_insignia_found", True)
        story.apply_to_region(region)
        self.sequence = None
        self.active = False
        return True
