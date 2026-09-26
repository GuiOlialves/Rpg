"""First arrival in the village: the silhouette and the first request for help."""
import math

import pygame

from entities.npc import NPC
from core.assets import load


RESIDENT_DIALOGUES = {
    "default": ("Os Slimes ainda me preocupam. Fique perto da estrada.",),
    "AVAILABLE": ("Os Slimes estão perto demais. Ainda precisamos de ajuda.",),
    "ACTIVE": ("Você ainda está aqui? Não quero apressar você.",
               "Eles estavam muito perto da vila."),
    "COMPLETED": ("Você voltou. Parece que o perigo imediato passou.",
                  "Precisamos entender o que aconteceu."),
    "REWARDED": ("Obrigado por ter voltado em segurança.",),
}


def enable_resident(actor, region):
    actor.dialogues = RESIDENT_DIALOGUES
    actor.quest_id = "forest_trouble"
    actor.quest_effects_enabled = False
    actor.enabled = True
    actor.running = False
    if actor not in region["npcs"]:
        region["npcs"].append(actor)
    if actor.hitbox not in region["obstacles"]:
        region["obstacles"].append(actor.hitbox)


def restore_resident(region, sprite):
    """Restore the same nearby villager after loading or returning to the village."""
    existing = next((npc for npc in region["npcs"] if npc.uid == "prologue_villager"), None)
    if existing is not None:
        return existing
    actor = NPC("prologue_villager", "Morador", (582, 598), RESIDENT_DIALOGUES,
                sprite, frame_size=32, draw_size=64)
    enable_resident(actor, region)
    return actor


class ScriptedDialogue:
    """DialogueBox-compatible lines with a speaker that can change per line."""

    def __init__(self, lines):
        self.lines = tuple(lines)
        self.dialogues = {"default": tuple(text for _, text in self.lines)}

    def dialogue_for(self, state, manager=None):
        return self.dialogues["default"]

    def speaker_for(self, index):
        return self.lines[index][0]


class Silhouette:
    """Anonymous alpha mask; the world renderer owns its depth and single shadow."""
    def __init__(self, sheet):
        frame = sheet.subsurface((0, 0, 32, 32)).copy()
        frame.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        self.image = pygame.transform.scale_by(frame, 2)
        self.x = self.y = 0
        self.config = {"hitbox_radius": 10}

    def draw(self, canvas, camera):
        canvas.blit(self.image, (round(self.x - 32 - camera[0]),
                                 round(self.y - 58 - camera[1])))


class ArrivalScene:
    PHASES = (
        ("walk", 520), ("silhouette", 1050), ("ei", 850),
        ("flash_near", 140), ("near", 620), ("flash_gone", 140),
        ("ellipsis", 620), ("shout", 650), ("run", 0), ("dialogue", 0),
    )
    LINES = (
        ("Morador", "Ainda bem que acordou!"),
        ("Protagonista", "Você me conhece?"),
        ("Morador", "Eu..."),
        ("Morador", "Não exatamente."),
        ("Protagonista", "Então por que me chamou de aventureiro?"),
        ("Morador", "Olha pra você."),
        ("Morador", "Se não é aventureiro, fez um ótimo trabalho se vestindo como um."),
        ("Protagonista", "Como vim parar aqui?"),
        ("Morador", "Encontraram você ontem à noite."),
        ("Morador", "Caído perto da estrada."),
        ("Protagonista", "Quem me encontrou?"),
        ("Morador", "Alden e mais dois homens."),
        ("Morador", "Você não acordava de jeito nenhum."),
        ("Morador", "Aquela casa estava vazia. Foi o melhor lugar que encontramos."),
        ("Protagonista", "Vazia?"),
        ("Morador", "Há algum problema?"),
        ("Protagonista", "..."),
        ("Protagonista", "Não sei."),
        ("Morador", "Droga, os slimes!"),
        ("Morador", "Estão chegando cada vez mais perto da vila."),
        ("Morador", "Alden mandou todo mundo evitar a floresta, mas..."),
        ("Morador", "Pedimos ajuda aos soldados, mas vão demorar a chegar."),
        ("Morador", "Os Slimes já estão perto demais para esperar."),
        ("Morador", "Você parece saber lutar."),
        ("Protagonista", "Parece."),
        ("Morador", "Pode nos ajudar?"),
    )

    def __init__(self, player, region, idle_sprite, run_sprite):
        self.phase_index = 0
        self.elapsed_ms = 0
        self.active = True
        self.actor_added = False
        self.actor = NPC(
            "prologue_villager", "Morador", (0, 0), {"default": []},
            idle_sprite, run_sprite=run_sprite, frame_size=32,
            draw_size=64)
        self.actor.enabled = False
        self.region = region
        self.dialogue_actor = ScriptedDialogue(self.LINES)
        self.player = player
        self.silhouette = Silhouette(load("assets/npc/civilian_seller.png"))

    @property
    def world_actors(self):
        if not self.active or self.phase not in {"silhouette", "ei", "flash_near", "near", "flash_gone"}:
            return ()
        near = self.phase in {"near", "flash_gone"}
        self.silhouette.x = self.player.x - (36 if near else 100)
        self.silhouette.y = self.player.y + (94 if near else 173)
        return (self.silhouette,)

    @property
    def phase(self):
        return self.PHASES[self.phase_index][0]

    @property
    def text(self):
        return {"ei": "Ei!", "ellipsis": "...", "shout": "AVENTUREIRO!"}.get(self.phase)

    def update(self, delta_ms, dialogue, story):
        if not self.active:
            return False
        phase = self.phase
        duration = self.PHASES[self.phase_index][1]
        elapsed = max(0, int(delta_ms))

        if phase == "walk":
            self._walk(min(elapsed, max(0, duration - self.elapsed_ms)))
        elif phase == "run" and self._run(elapsed):
            self.phase_index += 1
            self.elapsed_ms = 0
            self._on_phase_start(dialogue, story)
            return False

        if phase == "dialogue":
            if not dialogue.active:
                self.finish(dialogue, story)
                return True
            return False

        self.elapsed_ms += elapsed
        if duration and self.elapsed_ms >= duration:
            self.elapsed_ms -= duration
            self.phase_index += 1
            self._on_phase_start(dialogue, story)
            # Normal frame times advance at most one beat; this loop also makes
            # deterministic tests and slow frames safe without dropping flags.
            while self.active and self.phase != "dialogue":
                duration = self.PHASES[self.phase_index][1]
                if not duration or self.elapsed_ms < duration:
                    break
                self.elapsed_ms -= duration
                if self.phase == "walk":
                    self._walk(duration)
                self.phase_index += 1
                self._on_phase_start(dialogue, story)
        return False

    def _on_phase_start(self, dialogue, story):
        if self.phase == "silhouette":
            self.player.walk_frame = 0
        if self.phase == "shout":
            story.set("saw_silhouette", True)
        elif self.phase == "run":
            self.actor.x = self.player.x + 390
            self.actor.y = self.player.y + 8
            self.actor.running = True
            self.actor.enabled = False
            self.region["npcs"].append(self.actor)
            self.actor_added = True
        elif self.phase == "dialogue":
            self.actor.running = False
            self.actor.face_player(self.player)
            self.player.facing = 2
            dialogue.open(self.dialogue_actor)

    def _walk(self, delta_ms):
        direction = delta_ms / (1000 / 60)
        self.player._move(0, self.player.speed * direction, self.region["obstacles"])
        self.player._clamp_world()
        self.player.facing = 0
        self.player.walk_timer += max(1, round(direction))
        self.player.walk_frame = (self.player.walk_timer // 8) % 6

    def _run(self, delta_ms):
        target_x = self.player.x + 42
        distance = self.actor.x - target_x
        step = 4.8 * delta_ms / (1000 / 60)
        self.actor.facing = 1 if distance > 0 else 2
        self.actor.anim_tick += max(1, round(delta_ms / (1000 / 60)))
        self.actor.x = target_x if abs(distance) <= step else self.actor.x - math.copysign(step, distance)
        return abs(self.actor.x - target_x) < 8

    def finish(self, dialogue, story):
        """Apply the same final state after normal dialogue or a development skip."""
        if not self.active:
            return
        if self.phase == "walk":
            self._walk(max(0, self.PHASES[0][1] - self.elapsed_ms))
        self.player.walk_frame = 0
        self.actor.x, self.actor.y = self.player.x + 42, self.player.y + 8
        self.actor.anim_tick = 0
        self.actor.face_player(self.player)
        self.player.facing = 2
        enable_resident(self.actor, self.region)
        if dialogue.npc is self.dialogue_actor:
            dialogue.npc = None
        story.set("saw_silhouette", True)
        self.active = False

    def draw(self, canvas, camera, font):
        phase = self.phase
        if phase in {"flash_near", "flash_gone"}:
            flash = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
            progress = min(1, self.elapsed_ms / self.PHASES[self.phase_index][1])
            flash.fill((240, 236, 215, round(165 * math.sin(math.pi * progress))))
            canvas.blit(flash, (0, 0))

        if self.text:
            rendered = font.render(self.text, True, (255, 246, 219))
            shadow = font.render(self.text, True, (29, 27, 25))
            x = round(self.player.x - camera[0] - rendered.get_width() / 2)
            y = round(self.player.y - camera[1] - 90)
            if phase == "shout":
                x += 220
            canvas.blit(shadow, (x + 2, y + 3))
            canvas.blit(rendered, (x, y))
