"""Optional house memories and the mandatory memory tied to the broken pendant."""
import math

import pygame

from core.assets import load
from story.arrival_scene import ScriptedDialogue, Silhouette
from story.sequence import Beat, NarrativeSequence


class HeldPendant:
    has_embedded_shadow = True

    def __init__(self, player, image):
        self.player, self.image = player, image
        self.x, self.y = player.x, player.y

    def draw(self, canvas, camera):
        self.x, self.y = self.player.x + 7, self.player.y + 3
        canvas.blit(self.image,
                    (round(self.x - self.image.get_width() / 2 - camera[0]),
                     round(self.y - self.image.get_height() - camera[1])))


class HouseMemoryScene:
    """Small timed beats share NarrativeSequence and the ordinary dialogue box."""

    PAST_LINES = (
        ("Silhueta", "Você sempre demora demais!"),
        ("Protagonista do passado", "Espera!"),
        ("Silhueta", "..."),
    )
    CUP_LINES = (("Voz", "Essa é minha."), ("Protagonista", "Quem..."))
    PRESENT_LINES = (
        ("Protagonista", "Eu conhecia você."),
        ("Protagonista", "Então por que..."),
        ("Protagonista", "Por que não consigo lembrar?"),
    )
    PENDANT_STEPS = (
        ("sequence", (
            Beat(None, 300, background="world"),
            Beat(None, 760, background="world", fade_in_ms=260),
        ), True, "out"),
        ("dialogue", PAST_LINES, True, False),
        ("sequence", (
            Beat("*****", 1100, background="world", fade_in_ms=100),
        ), True, "in"),
        ("sequence", (
            Beat(None, 380, background="world", fade_in_ms=300),
        ), False, "in"),
        ("dialogue", PRESENT_LINES, False, False),
    )
    CUP_STEPS = (
        ("sequence", (Beat(None, 300, background="world"),), False, False),
        ("dialogue", CUP_LINES, False, False),
    )

    def __init__(self, kind, player, image, dialogue):
        self.kind = kind
        self.player = player
        self.dialogue = dialogue
        self.index = 0
        self.sequence = None
        self.active = True
        self._actors_visible = False
        self._warm_flash = False
        self._silhouette = None
        self._held_pendant = HeldPendant(player, image) if kind == "pendant" else None
        self.steps = self.PENDANT_STEPS if kind == "pendant" else self.CUP_STEPS
        if kind == "pendant":
            player.walk_frame = 0
            player.invulnerability_timer = 0
            self._silhouette = Silhouette(load("assets/npc/civilian_seller.png"))
        self._open_step()

    def _open_step(self):
        step_kind, content, self._actors_visible, fade_mode = self.steps[self.index]
        self.sequence = None
        self._warm_flash = self.kind == "cup" and step_kind == "sequence"
        if step_kind == "sequence":
            self.sequence = NarrativeSequence(content)
            self.sequence.start()
            if fade_mode:
                duration = content[0].fade_in_ms or 220
                self.sequence.fade.start(fade_mode, duration)
        else:
            self.dialogue.open(ScriptedDialogue(content))

    @property
    def world_actors(self):
        actors = []
        if self._actors_visible and self._silhouette is not None:
            directions = {0: (0, 1), 1: (-1, 0), 2: (1, 0), 3: (0, -1)}
            dx, dy = directions.get(self.player.facing, (0, -1))
            progress = 0
            if self.sequence is not None and self.sequence.current is not None:
                beat = self.sequence.current
                progress = max(0, beat.duration_ms - self.sequence.remaining_ms)
            distance = 42 + min(34, progress * 0.045)
            self._silhouette.x = self.player.x + dx * distance
            self._silhouette.y = self.player.y + dy * distance
            actors.append(self._silhouette)
        if self.kind == "pendant" and self.index == len(self.PENDANT_STEPS) - 1:
            actors.append(self._held_pendant)
        return tuple(actors)

    def advance(self):
        if self.active and self.sequence is None:
            self.dialogue.advance()

    def update(self, delta_ms, story, region):
        if not self.active:
            return False
        if self.sequence is not None:
            if self._warm_flash and self.sequence.current is not None:
                beat = self.sequence.current
                elapsed = beat.duration_ms - self.sequence.remaining_ms
                self._flash_alpha = round(70 * max(0, math.sin(math.pi * elapsed / beat.duration_ms)))
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
        if self._warm_flash and getattr(self, "_flash_alpha", 0):
            veil = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
            veil.fill((255, 191, 112, self._flash_alpha))
            canvas.blit(veil, (0, 0))

        if (self.kind == "pendant" and self.sequence is not None
                and self.sequence.current is not None
                and self.sequence.current.text == "*****"):
            elapsed = (self.sequence.current.duration_ms
                       - self.sequence.remaining_ms)
            if elapsed < 150:
                veil = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
                veil.fill((217, 207, 231, 32))
                canvas.blit(veil, (0, 0))

    def finish(self, story, region):
        if not self.active:
            return False
        completed_investigation = self.kind == "pendant"
        if completed_investigation:
            self.player.walk_frame = 0
            self.player.invulnerability_timer = 0
            story.set("house_searched")
            story.apply_to_region(region)
        self.dialogue.npc = None
        self.sequence = None
        self.active = False
        return completed_investigation
