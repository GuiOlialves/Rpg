"""Chapter 1D: one living witness, withheld answers and a persistent clue."""
import pygame
from story.arrival_scene import ScriptedDialogue
from story.sequence import Beat, NarrativeSequence
from story.blue_march import BlueTrooper, blue_troop_sprite
from story.watchpost import _footsteps
from world.regions.watchpost_art import prop

EDRIN_FLAGS = (
    'pursuit_entered', 'pursuit_trace_found', 'edrin_met', 'edrin_name_known',
    'edrin_death_revealed', 'namar_event_named', 'edrin_authority_revealed',
    'edrin_officer_recognized', 'edrin_forgetting_revealed', 'pursuit_patrol_heard',
    'namar_clue_received', 'edrin_escaped', 'edrin_encounter_completed',
)
PHASE_FLAGS = {
    'recognition': ('edrin_met',),
    'testimony': ('edrin_name_known', 'edrin_death_revealed', 'namar_event_named'),
    'authority': ('edrin_authority_revealed',),
    'officer': ('edrin_officer_recognized',),
    'forgetting': ('edrin_forgetting_revealed',),
    'patrol': ('pursuit_patrol_heard',),
    'clue': ('namar_clue_received',),
    'escape': ('edrin_escaped',),
    'alone': ('edrin_encounter_completed',),
}
# A phase is committed only after its last line/pause. Loading an unfinished
# scene resumes at the next uncommitted phase, never at an arbitrary text index.
H, P, E = 'Homem ferido', 'Protagonista', 'Edrin'
def pause(duration):
    return Beat(None, duration, background='world')

STEPS = (
    ('recognition', 'guard', pause(800), False),
    ('recognition', 'guard', ((H, 'Não.'),), False),
    ('recognition', 'guard', pause(850), False),
    ('recognition', 'guard', ((H, 'Não pode ser.'), (P, 'Você me conhece?')), False),
    ('recognition', 'recoil', pause(650), False),
    ('recognition', 'guard', ((H, 'Você está morto.'),), False),
    ('recognition', 'guard', pause(1100), False),
    ('testimony', 'guard', ((P, 'Quem sou eu?'), (H, 'Onde conseguiu isso?'),
                          (P, 'No posto. Era meu.'), (H, 'R-17...')), True),
    ('testimony', 'idle', pause(650), True),
    ('testimony', 'idle', ((H, 'Você não lembra.'), (P, 'De quê?'), (H, 'De nada?'),
                         (P, 'Quase nada.'), (H, 'Eu vi você morrer.')), True),
    ('testimony', 'idle', pause(950), True),
    ('testimony', 'idle', ((P, 'Onde?'), (H, 'Na Ponte de Namar.'),
                         (H, 'A travessia cedeu. Você ficou do outro lado, no meio da fumaça.'),
                         (P, 'Encontraram meu corpo?'), (H, 'Não. O rio levou o que caiu.'),
                         (P, 'E você?'), (E, 'Edrin. Eu estava na sua escolta.')), True),
    ('authority', 'idle', ((P, 'Nós servíamos juntos?'), (E, 'Eu guardava a retaguarda.'),
                         (E, 'Você dava as ordens.'), (P, 'Que tipo de ordens?')), False),
    ('authority', 'guard', pause(900), False),
    ('authority', 'guard', ((E, 'Em Namar, eu obedeci à última. Ainda não sei se devia.'),
                          (P, 'O que aconteceu lá?'), (E, 'Eu lembro de cada palavra.'),
                          (E, 'Não me peça para repetir aquela ordem.'),
                          (P, 'Por quê?'), (E, 'Não sei quem você é agora. Nem quem está ouvindo.')), False),
    ('officer', 'guard', ((P, 'Encontrei um oficial vermelho. Armadura pesada. Uma espada longa.'),
                        (P, 'Ele me reconheceu. Disse que eu queria esquecer. Depois foi embora.'),
                        (E, 'Ele viu seu rosto?'), (P, 'Viu.')), False),
    ('officer', 'alert', pause(650), False),
    ('officer', 'guard', ((E, 'Então ele sabe que Namar não acabou com você.'),
                        (P, 'Quem é ele?'), (E, 'Alguém que não deixa uma ponta solta sem motivo.'),
                        (E, 'Se foi embora, ainda espera alguma coisa de você.')), False),
    ('forgetting', 'idle', ((E, 'A ponte não foi o começo disso.'), (P, 'Da minha memória?'),
                          (E, 'Antes da travessia, você me pediu que não usasse mais seu nome.')), False),
    ('forgetting', 'idle', pause(850), False),
    ('forgetting', 'idle', ((E, 'Você já estava procurando um jeito de esquecer.'),), False),
    ('forgetting', 'idle', pause(1100), False),
    ('forgetting', 'idle', ((P, 'Por quê?'), (E, 'Você não quis me dizer.'),
                          (E, 'Eu guardei isso. Mesmo depois de Namar.')), False),
    ('patrol', 'alert', pause(1700), False),
    ('clue', 'alert', ((E, 'Azuis. Vieram pelo alto.'), (P, 'Estão atrás de você?'),
                      (E, 'No posto, procuravam nomes. Não vou esperar que chamem o meu.'),
                      (P, 'Ainda preciso de respostas.')), False),
    ('clue', 'alert', pause(400), False),
    ('clue', 'guard', ((E, 'Ponte de Namar. Procure a casa de pedágio, na margem seca.'),
                      (E, 'Foi ali que você deu a última ordem.'), (P, 'Edrin...'),
                      (E, 'Não me siga. Uma trilha só seria fácil demais.'),
                      (E, 'Se nos virmos de novo, deixe a espada na bainha.')), False),
    ('escape', 'walk', pause(2850), False),
    ('alone', 'idle', pause(1900), True),
    ('alone', 'idle', ((P, 'Do que eu estava fugindo?'),), True),
    ('alone', 'idle', pause(1200), True),
)


def apply_state(region, story):
    region['story_phase'] = 'edrin_departed' if story.get('edrin_encounter_completed') else 'wounded_trail'
    edrin = region['edrin']
    edrin.visible = not story.get('edrin_escaped')
    region['npcs'] = [edrin] if edrin.visible else []
    if story.get('edrin_encounter_completed'):
        # The next destination is deliberately not built in this block.
        region['exits']['namar_future'] = pygame.Rect(1148, 515, 64, 92)


def complete_trace(target, story):
    if getattr(target, 'uid', '') not in {'pursuit_tracks', 'pursuit_bandage'}:
        return False
    changed = not story.get('pursuit_trace_found')
    story.set('pursuit_trace_found')
    return changed


def encounter_at(player, region, story, dialogue, quests, load):
    if (story.get('watchpost_trail_found') and not story.get('edrin_encounter_completed')
            and region['edrin_trigger'].colliderect(player.hitbox)):
        return EdrinEncounter(player, region, story, dialogue, quests, load)
    return None


class HeldIdentification:
    uid = 'held_r17'
    has_embedded_shadow = True

    def __init__(self, player):
        self.player = player
        self.image = pygame.transform.scale(prop('token'), (12, 12))

    @property
    def x(self): return self.player.x + (8 if self.player.facing == 0 else -5)
    @property
    def y(self): return self.player.y + 1

    def draw(self, canvas, camera):
        canvas.blit(self.image, (round(self.x - 6 - camera[0]), round(self.y - 18 - camera[1])))


class EdrinEncounter:
    def __init__(self, player, region, story, dialogue, quests, load):
        self.player, self.region, self.story = player, region, story
        self.dialogue, self.quests = dialogue, quests
        self.edrin = region['edrin']
        self.steps = [step for step in STEPS if not all(story.get(f) for f in PHASE_FLAGS[step[0]])]
        self.index, self.elapsed_ms = 0, 0
        self.active, self.autosave_requested = True, False
        self.sequence, self.dialogue_actor = None, None
        self.token = HeldIdentification(player)
        self.patrol = [BlueTrooper(f'namar_patrol_{i}', 'Soldado Azul', (640 - i * 58, 271 + i * 9), {},
                                  blue_troop_sprite(load, i + 1),
                                  run_sprite=blue_troop_sprite(load, i + 1, 'Run'), frame_size=32, draw_size=64)
                       for i in range(2)]
        self.patrol_ms = 0
        self.footsteps = _footsteps()
        player.attack_timer = player.attack_cooldown_timer = 0
        player.dash_timer = player.dash_iframes = player.dash_recovery_timer = 0
        player.invulnerability_timer = player.hurt_visual_timer = player.impact_timer = 0
        player.moving = False
        player.walk_frame = 0
        player.dash_trail.clear()
        player.facing = 2
        self.edrin.x = 1048 if story.get('edrin_met') else 1020
        self.edrin.facing = 1
        self._open_step()

    @property
    def phase(self):
        return self.steps[self.index][0] if self.active else 'complete'

    @property
    def focus(self):
        return ((self.player.x + 1040) / 2, (self.player.y + 386) / 2 - 15)

    @property
    def world_actors(self):
        actors = ()
        if self.phase in {'patrol', 'clue', 'escape'}:
            actors += tuple(self.patrol)
        if self.active and self.steps[self.index][3]:
            actors += (self.token,)
        return actors

    def _open_step(self):
        phase, pose, content, _held = self.steps[self.index]
        self.elapsed_ms = 0
        self.sequence = None
        self.edrin.mode = pose
        if pose == 'alert':
            self.edrin.facing = 3
        else:
            self.edrin.facing = 2 if phase == 'escape' else 1
        if phase == 'alone':
            self.player.facing = 0
        if phase == 'patrol' and self.footsteps:
            self.footsteps.play()
        if isinstance(content, Beat):
            self.sequence = NarrativeSequence((content,))
            self.sequence.start()
        else:
            self.dialogue_actor = ScriptedDialogue(content)
            self.dialogue_actor.x, self.dialogue_actor.y = 1040, 386
            self.dialogue.open(self.dialogue_actor)

    def advance(self):
        if self.active and self.sequence is None:
            self.dialogue.advance()

    def update(self, delta_ms):
        if not self.active:
            return False
        self.elapsed_ms += delta_ms
        self.edrin.update(delta_ms)
        if self.steps[self.index][1] == 'recoil':
            self.edrin.x = 1020 + 28 * min(1, self.elapsed_ms / 650)
        if self.phase in {'patrol', 'clue', 'escape'}:
            self.patrol_ms += delta_ms
            for i, actor in enumerate(self.patrol):
                actor.x = min(905 - i * 58, 640 - i * 58 + self.patrol_ms * .025)
                actor.facing, actor.running = 2, True
        if self.phase == 'escape':
            t = min(1, self.elapsed_ms / 2550)
            self.edrin.x, self.edrin.y = 1048 + 153 * t, 386 - 59 * t
            self.edrin.visible = t < .90
            if not self.edrin.visible:
                self.region['npcs'] = []
        if self.sequence is not None:
            if not self.sequence.update(delta_ms):
                return False
        elif self.dialogue.active:
            return False
        previous = self.phase
        self.index += 1
        if self.index == len(self.steps) or self.steps[self.index][0] != previous:
            for flag in PHASE_FLAGS[previous]:
                self.story.set(flag)
            self.autosave_requested = True
            if previous == 'escape':
                apply_state(self.region, self.story)
        if self.index == len(self.steps):
            return self.finish()
        self._open_step()
        return False

    def finish(self):
        """Normal completion and the existing F4 scene shortcut are atomic."""
        if not self.active:
            return False
        for flags in PHASE_FLAGS.values():
            for flag in flags:
                self.story.set(flag)
        if self.dialogue.npc is self.dialogue_actor:
            self.dialogue.npc = None
        self.edrin.visible = False
        apply_state(self.region, self.story)
        self.player.facing = 0
        self.sequence, self.active = None, False
        self.quests.notice = 'Ecos da Guerra: descubra o que aconteceu na Ponte de Namar.'
        self.quests.notice_timer = 300
        return True
