"""The voluntary return to Alden ends at the house investigation objective."""
from story.arrival_scene import ScriptedDialogue
from story.sequence import Beat, NarrativeSequence
from systems.quest import COMPLETED, REWARDED


ALDEN_CONTEXT = (
    ("Alden", "Dê uma boa olhada naquela casa. Talvez alguma coisa lá desperte sua memória."),
)


def post_slimes_available(quests, story):
    quest = quests.get("forest_trouble")
    return (quest.progress == quest.required
            and quest.state in {COMPLETED, REWARDED}
            and not story.get("alden_post_slimes_talk"))


def interact_with_alden(alden, player, dialogue, quests, story):
    """Called only by the normal E interaction with the existing village NPC."""
    alden.face_player(player)
    if post_slimes_available(quests, story):
        return AldenScene(alden, player, dialogue)
    if story.get("alden_post_slimes_talk"):
        dialogue.open(ScriptedDialogue(ALDEN_CONTEXT))
    else:
        alden.begin_interaction(dialogue, player, quests)
    return None


class AldenScene:
    # Tuples are E-advanced dialogue; Beats are short, unskippable-by-E pauses.
    # The masked name uses precisely the opening's world-overlay presentation.
    STEPS = (
        (("Alden", "Então era verdade."),
         ("Protagonista", "O quê?"),
         ("Alden", "Que você sabe usar essa espada."),
         ("Protagonista", "Meu corpo sabe."),
         ("Alden", "E você não?"),
         ("Protagonista", "Não lembro de nada.")),
        Beat(None, 550, background="world"),
        (("Alden", "Nada?"),
         ("Protagonista", "Acordei naquela casa."),
         ("Protagonista", "Não sei meu nome."),
         ("Protagonista", "Não sei de onde vim."),
         ("Protagonista", "Não sei por que sei lutar.")),
        Beat(None, 800, background="world"),  # Alden observes the protagonist.
        (("Alden", "Há alguma coisa que lembra?"),
         ("Protagonista", "Um nome."),
         ("Alden", "De quem?"),
         ("Protagonista", "Não sei."),
         ("Alden", "Qual?")),
        Beat(None, 600, background="world"),  # He tries to answer.
        (("Protagonista", "..."),),
        Beat("*****", 2600, background="world"),
        (("Protagonista", "Não consigo dizer."),),
        Beat(None, 700, background="world"),  # A concerned silence.
        (("Alden", "Talvez não devesse forçar."),
         ("Protagonista", "Preciso descobrir quem sou.")),
        Beat(None, 700, background="world"),  # Alden looks toward the house.
        (("Alden", "Quando trouxemos você, encontramos algumas coisas lá dentro."),
         ("Protagonista", "Você disse que ela estava vazia."),
         ("Alden", "Estava.")),
        Beat(None, 700, background="world"),
        (("Alden", "É justamente isso que me incomoda."),),
    )

    def __init__(self, alden, player, dialogue):
        self.alden = alden
        self.player = player
        self.index = 0
        self.active = True
        self.sequence = None
        self.dialogue_actor = None
        player.walk_frame = 0
        player.attack_timer = player.dash_timer = player.dash_iframes = 0
        # A paused arrival-protection blink must not hide the speaker.
        player.invulnerability_timer = 0
        dx, dy = alden.x - player.x, alden.y - player.y
        player.facing = (2 if dx > 0 else 1) if abs(dx) > abs(dy) else (0 if dy > 0 else 3)
        self._open_step(dialogue)

    def _open_step(self, dialogue):
        step = self.STEPS[self.index]
        self.sequence = None
        if self.index == 11:
            self.alden.facing = 1  # The starting house is west of Alden.
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
        """Normal completion and F4 share this single, idempotent finalization."""
        if not self.active:
            return False
        quests.claim("forest_trouble", inventory)
        story.set("alden_post_slimes_talk")
        story.set("house_investigation_unlocked")
        quests.notice = "Problemas na Floresta concluída. Investigue a casa."
        quests.notice_timer = 300
        if dialogue.npc is self.dialogue_actor:
            dialogue.npc = None
        self.alden.face_player(self.player)
        self.sequence = None
        self.active = False
        return True
