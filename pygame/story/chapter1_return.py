"""Chapter 1A: the journey home and Alden's first lead, using existing scenes."""
import pygame

from story.arrival_scene import ScriptedDialogue
from story.fade import FadeOverlay
from story.sequence import Beat, NarrativeSequence


CHAPTER_NAME = "Ecos da Guerra"
ALDEN_REMINDER = (
    ("Alden", "A estrada antiga sai pelo oeste, atrás das colinas."),
    ("Alden", "Se encontrar alguma coisa... volte para me contar."),
)


def settle_player(player):
    player.walk_frame = 0
    player.attack_timer = player.attack_cooldown_timer = 0
    player.dash_timer = player.dash_iframes = player.dash_recovery_timer = 0
    player.dash_cooldown = player.dash_feedback_timer = 0
    player.invulnerability_timer = 0
    player.dash_trail.clear()
    player.impact_timer = player.dust_timer = player.hurt_visual_timer = 0
    player.knockback_frames = 0
    player.moving = False


class Chapter1ReturnScene:
    # The previous scene has already faded to black. No extra prologue card
    # or key press interrupts the journey between the two chapters.
    TITLE_BEATS = tuple(Beat(None, duration) for duration in (650, 850, 1650, 700, 250))
    RETURN_MS = 1400

    def __init__(self, player, story, quests, return_to_village):
        self.player, self.story, self.quests = player, story, quests
        self.return_to_village = return_to_village
        self.active = story.get("prologue_completed") and not story.get("chapter1_returned")
        self.phase = "resume" if story.get("chapter1_started") else "title"
        self.sequence = NarrativeSequence(self.TITLE_BEATS)
        self.sequence.start()
        self.fade = FadeOverlay()
        self.remaining_ms = self.RETURN_MS
        self.autosave_requested = False
        self.text_images = None
        if self.active:
            settle_player(player)

    @property
    def title_alpha(self):
        index = self.sequence.index
        if index in (0, 4) or not self.sequence.active:
            return 0
        duration = self.TITLE_BEATS[index].duration_ms
        progress = 1 - self.sequence.remaining_ms / duration
        return round(255 * (progress if index == 1 else 1 - progress if index == 3 else 1))

    def _return(self):
        self.story.set("chapter1_started")
        village = self.return_to_village()
        self.story.set("chapter1_returned")
        self.story.apply_to_region(village)
        self.autosave_requested = True
        self.player.facing = 1
        self.phase = "return"
        self.sequence = None
        self.fade.start("in", 1000)

    def update(self, delta_ms):
        if not self.active:
            return False
        if self.phase == "resume":
            self._return()
        elif self.phase == "title":
            if self.sequence.update(delta_ms):
                self._return()
        else:
            self.fade.update(delta_ms)
            self.remaining_ms -= max(0, delta_ms)
            if self.remaining_ms <= 0:
                return self.finish()
        return False

    def finish(self):
        """F4 and normal playback commit the same, idempotent milestones."""
        if not self.active:
            return False
        if not self.story.get("chapter1_returned"):
            self._return()
        self.quests.notice = "Nova missão: Ecos da Guerra. Fale com Alden."
        self.quests.notice_timer = 300
        self.active = False
        self.fade.alpha = 0
        return True

    def draw_title(self, canvas):
        canvas.fill((5, 7, 10))
        if self.text_images is None:
            self.text_images = (
                pygame.font.Font(None, 26).render("CAPÍTULO I", True, (179, 163, 128)),
                pygame.font.Font(None, 46).render("ECOS DA GUERRA", True, (229, 218, 191)),
            )
        center = canvas.get_width() // 2
        y = canvas.get_height() // 2
        for image, offset in zip(self.text_images, (-35, 12)):
            image.set_alpha(self.title_alpha)
            canvas.blit(image, image.get_rect(center=(center, y + offset)))


class Chapter1AldenScene:
    debug_label = "chapter1_alden"
    STEPS = (
        (("Alden", "Você voltou."),),
        Beat(None, 550, background="world"),
        (("Alden", "Essa terra na sua roupa... E o sangue. Você está ferido?"),
         ("Protagonista", "Alden... havia soldados na floresta.")),
        Beat(None, 450, background="world"),
        (("Protagonista", "Muitos. Os azuis estavam mortos."),
         ("Alden", "O barulho chegou até aqui. Ninguém sabia de onde vinha."),
         ("Protagonista", "Depois encontrei os outros."),
         ("Alden", "Que outros?"),
         ("Protagonista", "Usavam este símbolo.")),
        Beat(None, 750, background="world"),  # Alden studies the insignia.
        (("Alden", "Onde encontrou isso?"),
         ("Protagonista", "Na floresta. Mas não foi só isso."),
         ("Protagonista", "Eles me conheciam.")),
        Beat(None, 600, background="world"),
        (("Protagonista", "Um deles falou comigo como se estivesse me esperando."),
         ("Protagonista", "E eu lembrei."),
         ("Alden", "De quê?"),
         ("Protagonista", "Eu fazia parte deles.")),
        Beat(None, 1200, background="world"),  # Let the admission stand alone.
        (("Alden", "... Não sei o que dizer."),
         ("Protagonista", "Você conhece essa insígnia?"),
         ("Alden", "Já vi homens com ela. Há algum tempo."),
         ("Alden", "Não entraram no Vale. Seguiram pela estrada antiga, atrás das colinas."),
         ("Protagonista", "Por onde?")),
        Beat(None, 550, background="world"),
        (("Alden", "A saída a oeste. A estrada contorna a Vila."),
         ("Alden", "Quase ninguém a usa desde que a guerra se aproximou."),
         ("Protagonista", "Vou procurar lá."),
         ("Alden", "Você acabou de voltar. Nem sabemos quem eram esses homens."),
         ("Alden", "Talvez seja melhor esperar."),
         ("Protagonista", "Eles sabem quem eu sou.")),
        Beat(None, 650, background="world"),
        (("Protagonista", "Preciso descobrir o que fiz antes de esquecer."),),
        Beat(None, 800, background="world"),
        (("Alden", "Então vá com cuidado."),
         ("Alden", "Ainda tem gente esperando você voltar.")),
        Beat(None, 650, background="world"),
    )

    def __init__(self, alden, player, dialogue, region):
        self.alden, self.player, self.region = alden, player, region
        self.index, self.active = 0, True
        self.sequence = self.dialogue_actor = None
        settle_player(player)
        alden.face_player(player)
        dx, dy = alden.x - player.x, alden.y - player.y
        player.facing = (2 if dx > 0 else 1) if abs(dx) > abs(dy) else (0 if dy > 0 else 3)
        self._open_step(dialogue)

    def _open_step(self, dialogue):
        step = self.STEPS[self.index]
        self.sequence = None
        if self.index == 11:
            self.alden.facing = 1  # The lead lies west, beyond the village.
        elif self.index == 13:
            self.alden.face_player(self.player)
        elif self.index == len(self.STEPS) - 1:
            self.player.facing = 1
        if isinstance(step, Beat):
            self.sequence = NarrativeSequence((step,))
            self.sequence.start()
        else:
            self.dialogue_actor = ScriptedDialogue(step)
            dialogue.open(self.dialogue_actor)

    def advance(self, dialogue):
        if self.active and self.sequence is None:
            dialogue.advance()

    def update(self, delta_ms, dialogue, story, quests, inventory):
        if not self.active:
            return False
        if self.sequence is not None:
            if not self.sequence.update(delta_ms):
                return False
        elif dialogue.active:
            return False
        self.index += 1
        if self.index == len(self.STEPS):
            return self.finish(dialogue, story, quests, inventory)
        self._open_step(dialogue)
        return False

    def finish(self, dialogue, story, quests, inventory):
        if not self.active:
            return False
        story.set("chapter1_alden_talk")
        story.set("old_road_unlocked")
        story.apply_to_region(self.region)
        quests.notice = "Ecos da Guerra: investigue a antiga estrada, a oeste."
        quests.notice_timer = 300
        if dialogue.npc is self.dialogue_actor:
            dialogue.npc = None
        self.sequence = None
        self.active = False
        self.player.facing = 1
        self.alden.face_player(self.player)
        return True


def interact_with_returned_alden(alden, player, dialogue, story, region):
    if not story.get("chapter1_alden_talk"):
        return Chapter1AldenScene(alden, player, dialogue, region)
    alden.face_player(player)
    dialogue.open(ScriptedDialogue(ALDEN_REMINDER))
    return None


def apply_village_aftermath(region, story):
    """Only two residents regroup; keep their collisions at their new feet."""
    if not region.get("chapter1_aftermath_applied"):
        reactions = {
            "mira": ((1618, 512), ("Ouvimos ferro batendo lá fora. Depois, mais nada.",
                                    "Tomas queria ir até a estrada. Pedi que ficasse.")),
            "tomas": ((1688, 514), ("Parei a carroça quando o barulho começou.",
                                     "Deixei tudo carregado. Se alguém precisar sair depressa...")),
        }
        for npc in region.get("npcs", ()):
            if npc.uid not in reactions:
                continue
            old_hitbox = npc.hitbox
            position, lines = reactions[npc.uid]
            npc.x, npc.y = position
            npc.facing = 2
            npc.last_visual_position = position
            npc.dialogues = {"default": lines}
            region["obstacles"] = [box for box in region["obstacles"] if box != old_hitbox]
            region["obstacles"].append(npc.hitbox)
        region["chapter1_aftermath_applied"] = True
    region["story_phase"] = "village_chapter1"
    # This actor can also be restored later by the existing arrival code.
    resident = next((npc for npc in region.get("npcs", ()) if npc.uid == "prologue_villager"), None)
    if resident is not None:
        lines = ("Achei que os Slimes fossem o pior da estrada. Agora ninguém quer chegar perto dela.",)
        resident.dialogues = {state: lines for state in ("default", "AVAILABLE", "ACTIVE", "COMPLETED", "REWARDED")}
    if story.get("old_road_unlocked"):
        region["exits"].pop("old_road_future",None)
        region["exits"]["old_road"] = pygame.Rect(0, 520, 68, 115)
        region["spawn"]["old_road"] = (128,575)
        marker = region.get("old_road_marker")
        if marker is not None and marker not in region["interactables"]:
            region["interactables"].append(marker)
