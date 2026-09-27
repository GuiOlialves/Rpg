"""The wounded commander, the red officer and the verbal confrontation (2E–3A)."""
import pygame

from entities.npc import NPC
from story.arrival_scene import ScriptedDialogue
from story.sequence import Beat, NarrativeSequence
from story.blue_march import blue_fallen_sprite


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


# Each chunk ends at a deliberate pause or a change in posture/attention.
CONFRONTATION = (
    ("question", (
        ("Oficial Vermelho", "Onde esteve?"),
        ("Protagonista", "Não sei."),
        ("Oficial Vermelho", "O que fizeram com você?"),
        ("Protagonista", "Eu não sei.")), 350),
    ("red_dead", (
        ("Oficial Vermelho", "E eles?"),
        ("Protagonista", "Tentaram me matar."),
        ("Oficial Vermelho", "Claro que tentaram.")), 250),
    ("blue_dead", (
        ("Oficial Vermelho", "Encontraram você caminhando entre aqueles uniformes."),
        ("Protagonista", "Eu não faço parte deles."),
        ("Oficial Vermelho", "Eles não tinham como saber.")), 500),
    ("guilt", (
        ("Oficial Vermelho", "Alguns daqueles homens atravessaram meio continente quando ouviram rumores de que você estava vivo."),
        ("Oficial Vermelho", "Eles conheciam seu nome."),
        ("Oficial Vermelho", "Você matou todos sem conseguir lembrar o deles.")), 450),
    ("name", (
        ("Protagonista", "Existe um nome."),
        ("Protagonista", "Na minha cabeça."),
        ("Protagonista", "Desde que acordei.")), 450),
    ("five", (("Protagonista", "Cinco letras."),), 350),
    ("reaction", (
        ("Oficial Vermelho", "..."),
        ("Oficial Vermelho", "Você ainda consegue senti-lo?"),
        ("Protagonista", "Sentir?"),
        ("Oficial Vermelho", "Não lembrar.")), 350),
    ("feel", (
        ("Oficial Vermelho", "Sentir."),
        ("Protagonista", "Quem é █████?")), 280),
    ("demand", (
        ("Oficial Vermelho", "Então deixaram até isso."),
        ("Protagonista", "Quem é?!")), 100),
    ("commander", (("Comandante Azul", "Não diga."),), 300),
    ("silence", (("Protagonista", "Você sabe também."),), 550),
    ("knows", (("Oficial Vermelho", "Claro que sabe."),), 350),
    ("ready", (("Oficial Vermelho", "Eles sempre souberam."),), 0),
)


class _WoundedCommander:
    has_embedded_shadow = True
    config = {"hitbox_radius": 22}

    def __init__(self, sprite, position):
        self.sheet = sprite
        self.x, self.center_y = position
        self.y = self.center_y + 10
        self.image = blue_fallen_sprite(self.sheet)

    def look_back(self):
        # A slight lift/turn is enough to make his reaction readable while prone.
        self.image = blue_fallen_sprite(self.sheet, angle=-48)

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

    @property
    def depth(self):
        return self.y

    def draw(self, canvas, camera, player=None):
        sheet = self.run_sprite if self.running and self.run_sprite else self.sprite
        frame_count = max(1, sheet.get_width() // self.frame_size)
        frame_index = (self.anim_tick // 5) % frame_count if self.running else 0
        if getattr(self, "guarded", False):
            sheet = self.guard_sprite
            frame_index = 2
        frame = sheet.subsurface((frame_index * self.frame_size, 0,
                                  self.frame_size, self.frame_height)).copy()
        if self.facing == 1:
            frame = pygame.transform.flip(frame, True, False)
        source_foot = frame.get_bounding_rect().bottom
        scaled_height = max(1, round(self.draw_size * self.frame_height / self.frame_size))
        frame = pygame.transform.scale(frame, (self.draw_size, scaled_height))
        if getattr(self, "state", None) == "DEFEATED" and not getattr(self, "standing_up", False):
            frame = pygame.transform.rotate(frame.subsurface(frame.get_bounding_rect()), -55)
            canvas.blit(frame, (round(self.x - frame.get_width() / 2 - camera[0]),
                                round(self.y - frame.get_height() / 2 - camera[1])))
            return
        foot = round(source_foot * scaled_height / self.frame_height)
        canvas.blit(frame, (round(self.x - self.draw_size / 2 - camera[0]),
                            round(self.y - foot - camera[1])))


def create_waiting_officer(load, position):
    base = "sprites_meu/Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/Units/Red Units/Warrior/"
    actor = _RedOfficer("red_officer_scene", "Oficial Vermelho", position, {},
                        load(base + "Warrior_Idle.png"),
                        run_sprite=load(base + "Warrior_Run.png"),
                        frame_size=192, draw_size=94)
    actor.guard_sprite = load(base + "Warrior_Attack1.png")
    actor.guarded = False
    actor.facing = 2
    return actor


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
        self.officer = region.get("red_officer_actor")
        if self.officer is None:
            self.officer = create_waiting_officer(load, (player.x - 260, player.y - 4))
        if self.officer in region.get("scenery", []):
            region["scenery"].remove(self.officer)
        region["red_officer_actor"] = self.officer
        self.officer.running = False
        self.officer_target_x = player.x - 112
        self.continuation_actor = None
        self.continuation_index = -1
        self.player.facing = 2
        self.player.walk_frame = 0
        self.player.invulnerability_timer = 0
        self.player.attack_timer = self.player.dash_timer = self.player.dash_iframes = 0
        if story.get("red_officer_met"):
            self._next_confrontation()
        else:
            self.dialogue.open(self.dialogue_actor)

    def _next_confrontation(self):
        self.phase = "confrontation"
        self.continuation_index += 1
        if self.continuation_index >= len(CONFRONTATION):
            return self.finish()
        action, lines, _ = CONFRONTATION[self.continuation_index]
        self.officer.facing = 1 if action == "red_dead" else 2
        self.officer.guarded = action in {"reaction", "ready"}
        if action == "guilt":
            self.player.facing = 1
        elif action == "commander":
            self.commander.look_back()
        elif action == "silence":
            self.player.facing = 2
        elif action in {"reaction", "ready"}:
            self.officer.guarded = True
        self.continuation_actor = ScriptedDialogue(lines)
        self.dialogue.open(self.continuation_actor)
        return False

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
        if self.phase in {"officer_approach", "officer_inspection", "officer_dialogue", "confrontation"}:
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
            self.story.set("red_officer_met", True)
            return self._next_confrontation()
        elif self.continuation_actor is not None and closed is self.continuation_actor:
            action, _, pause = CONFRONTATION[self.continuation_index]
            if pause:
                self.sequence = NarrativeSequence((Beat(
                    "█████" if action == "feel" else None, pause,
                    background="world", fade_in_ms=100 if action == "feel" else 0),))
                self.sequence.start()
            else:
                return self._next_confrontation()
        return False

    def update(self, delta_ms):
        if not self.active:
            return False
        delta_ms = max(0, int(delta_ms))
        if self.sequence is not None:
            if self.sequence.update(delta_ms):
                self.sequence = None
                if self.phase == "confrontation":
                    return self._next_confrontation()
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

    def draw_overlay(self, canvas):
        # Same brief pale flash used by the pendant's obscured-name memory.
        if self.sequence is not None and self.sequence.current.text == "█████":
            elapsed = self.sequence.current.duration_ms - self.sequence.remaining_ms
            if elapsed < 150:
                veil = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
                veil.fill((217, 207, 231, 32))
                canvas.blit(veil, (0, 0))

    def finish(self):
        if not self.active:
            return False
        if self.dialogue.npc in (self.dialogue_actor, self.reaction_actor,
                                 self.officer_dialogue, self.continuation_actor):
            self.dialogue.npc = None
        self.story.set("red_officer_met", True)
        self.story.set("red_officer_boss_ready", True)
        if self.phase not in {"confrontation", "officer_dialogue"}:
            self.officer.x = self.officer_target_x
            self.officer.y = self.player.y - 4
        self.officer.running = False
        self.officer.facing = 2
        self.officer.guarded = True
        self.story.apply_to_region(self.region)
        self.sequence = None
        self.active = False
        self.player.attack_timer = 0
        self.player.dash_timer = self.player.dash_iframes = 0
        return True
