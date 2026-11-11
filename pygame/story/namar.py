"""Chapter 1E: one irreversible priority, two small outcomes and a shared lead."""
import math
import pygame
from entities.enemy import Enemy
from entities.npc import NPC
from story.arrival_scene import ScriptedDialogue
from story.sequence import Beat, NarrativeSequence
from systems.inventory import add_inventory_item
from systems.items import consumable
from world.regions.namar import PROTECT_SPAWNS, PURSUE_SPAWNS
from world.regions.namar_art import prop

NAMAR_FLAGS = (
    'namar_entered', 'namar_military_clue', 'namar_civilian_clue', 'namar_cache_found',
    'namar_survivors_met', 'namar_choice_protect', 'namar_choice_pursue',
    'namar_supplies_lost', 'namar_enemy_0_defeated', 'namar_enemy_1_defeated',
    'namar_combat_completed', 'namar_dispatch_detail', 'namar_aftermath_seen',
    'namar_memory_seen', 'namar_record_lead_found', 'namar_completed',
)
CHOICES = (
    ('Proteger Mara e Téo.', 'Ficar na carroça; o portador seguirá sem ser alcançado.'),
    ('Interceptar o portador.', 'Buscar os registros; Mara e Téo tentarão chegar ao abrigo.'),
)
P, M, T, C = 'Protagonista', 'Mara', 'Téo', 'Portador de registros'
INTRO = (
    (T, 'A roda só precisa aguentar até a muralha. Mara, empurre quando eu disser.'),
    (M, 'Se as sacas caírem, o abrigo fica sem farinha.'),
    (P, 'Posso ajudar.'),
    (M, 'R-17. Essa marca era dos homens que fecharam a travessia.'),
    (P, 'Ainda estou tentando descobrir o que fizeram aqui.'),
    (M, 'Eu tinha uma padaria na outra margem. Não sei qual deles deu a ordem.'),
    (T, 'O portão! Estão trazendo a barricada.'),
    (C, 'Deixem a carga. Preciso passar com os índices antes que fechem a margem.'),
    (P, 'Índices de Namar?'),
    (C, 'Não vou parar aqui. Os guardas estão recolhendo tudo.'),
    (T, 'Dois descendo. Querem nossa carroça também.'),
    (M, 'Se correr atrás dele, nós tentamos a passagem baixa. Sem as sacas, é possível.'),
    (T, 'Se ficar, seguramos a carga juntos. Mas ele atravessa o portão.'),
    (P, 'Esses registros podem explicar a travessia. E quem ainda está atrás de nós.'),
    (M, 'Então decida agora. A barricada está vindo.'),
)
CARRIER = (
    (P, 'Espere. Não quero os seus índices. Preciso da ordem daquela travessia.'),
    (C, 'Eu carrego referências, não as ordens. A segunda via não foi destruída.'),
    (P, 'Como encontro essa via?'),
    (C, 'N-04. Série da retaguarda. Foi separada dos papéis de cobrança.'),
    (P, 'Quem a assinou?'),
    (C, 'A assinatura não estava no índice. Não me faça inventar um nome.'),
    (C, 'Volte à carroça. Eles tinham uma ficha de entrega com o destino das caixas.'),
    (C, 'Eu ainda preciso passar. Há outros registros nesta bolsa.'),
)
AFTERMATH = {
    'protect': (
        (T, 'A roda aguentou. O homem passou antes de fecharem o portão.'),
        (P, 'Perdi a chance de perguntar.'),
        (M, 'Você deixou respostas irem embora. Eu sei o que isso pode custar.'),
        (M, 'Mas a farinha chega ao abrigo. Obrigada por ficar.'),
        (T, 'A ficha sob as sacas fala das caixas do pedágio. Talvez ainda ajude.'),
        (M, 'Leve duas poções. Eram da viagem; agora conseguimos dividir.'),
    ),
    'pursue': (
        (P, 'Ele sabia onde procurar uma referência. N-04, série da retaguarda.'),
        (T, 'Nós chegamos ao muro. Meu braço prendeu na roda quando largamos a carga.'),
        (M, 'Estamos vivos. A farinha ficou no chão.'),
        (P, 'Eu achei que conseguiria voltar antes.'),
        (M, 'Não dava para saber. Agora precisamos encontrar comida em outro lugar.'),
        (T, 'Eu não queria ficar entre a carroça e uma espada. A passagem nos salvou.'),
        (M, 'Guardei a ficha da entrega. Se o que buscou ajudar a impedir outra travessia assim, descubra.'),
    ),
}
ENDING = (
    (T, 'Esta ficha acompanhava as caixas do pedágio, não a nossa farinha.'),
    (M, '"Livro de Ordens — travessia de Namar. Segunda via: Depósito de Registros da Margem Seca. Gaveta 7."'),
    (P, 'A ordem ainda existe.'),
    (T, 'A ficha diz onde foi guardada. Não diz o que mandava fazer.'),
    (P, 'Vou procurá-la.'),
    (M, 'Nós seguimos para o abrigo. Quando souber, lembre que havia gente na fila.'),
)


class NamarGuard(Enemy):
    def __init__(self, kind, position, load, seed=0):
        super().__init__('red_soldier', position, load, seed)
        self.config = dict(self.config, name='Guarda de Requisição', max_hp=64,
                           damage=6, speed=1.8, perception=520, xp_reward=28)
        self.name = self.config['name']
        self.hp = self.max_hp = self.config['max_hp']
        self.damage, self.speed = self.config['damage'], self.config['speed']


def choice(story):
    return ('protect' if story.get('namar_choice_protect') else
            'pursue' if story.get('namar_choice_pursue') else None)


def apply_state(region, story):
    branch = choice(story)
    region['story_phase'] = 'namar_complete' if story.get('namar_completed') else branch or 'investigation'
    for actor in (region['mara'], region['teo']):
        actor.story = story
        actor.running = False
        actor.enabled = branch is None or story.get('namar_completed')
    region['mara'].x, region['mara'].y = (605, 773) if branch == 'pursue' else (820, 660)
    region['teo'].x, region['teo'].y = (682, 790) if branch == 'pursue' else (920, 700)
    region['teo'].facing = 1
    region['supplies_prop'].image = prop('lost_sacks' if story.get('namar_supplies_lost') else 'sacks')
    region['npcs'] = [region['mara'], region['teo']]
    if story.get('chapter1_final_returned'):
        region['npcs']=[]
        if region['supplies_prop'] in region['scenery']: region['scenery'].remove(region['supplies_prop'])
    if (branch == 'pursue' and not story.get('namar_dispatch_detail')):
        region['carrier'].x, region['carrier'].y = 1200, 270
        region['npcs'].append(region['carrier'])
    region['enemy_factory'] = NamarGuard
    region['enemy_spawns'] = [('namar_guard', position) for position in
        (PROTECT_SPAWNS if branch == 'protect' else PURSUE_SPAWNS)] if branch and not story.get('namar_combat_completed') else []
    # Prevent retreat from bypassing the danger, and keep the gate closed in both branches.
    region['exits'] = {} if branch and not story.get('namar_completed') else {'pursuit': pygame.Rect(0, 780, 32, 90)}
    if story.get('namar_completed'):
        region['exits']['archive']=pygame.Rect(1188,0,76,44)
    for target in region['interactables']:
        target.enabled = branch is None or story.get('namar_completed')
        if target.uid == 'namar_cache': target.enabled &= not story.get('namar_cache_found')


def spawn_pending(region, story, spawn_enemies):
    return [enemy for enemy in spawn_enemies(region)
            if not story.get(f'namar_enemy_{enemy.namar_id}_defeated')]


def complete_evidence(target, story, inventory):
    flag = {'namar_military': 'namar_military_clue', 'namar_civilian': 'namar_civilian_clue',
            'namar_cache': 'namar_cache_found'}.get(getattr(target, 'uid', ''))
    if flag is None or story.get(flag): return False
    story.set(flag)
    if flag == 'namar_cache_found': add_inventory_item(inventory, consumable('herb', 2))
    return True


def complete_combat(story, region):
    if (choice(story) and not story.get('namar_combat_completed')
            and all(story.get(f'namar_enemy_{i}_defeated') for i in range(2))):
        story.set('namar_combat_completed')
        apply_state(region, story)
        return True
    return False


def moment_at(player, region, story, dialogue, quests, inventory, load):
    if story.get('namar_completed'): return None
    branch = choice(story)
    if branch is None:
        if (story.get('namar_military_clue') and story.get('namar_civilian_clue')
                and region['choice_trigger'].colliderect(player.hitbox)):
            return NamarScene('choice' if story.get('namar_survivors_met') else 'intro',
                              player, region, story, dialogue, quests, inventory, load)
    elif story.get('namar_combat_completed'):
        if branch == 'pursue' and not story.get('namar_dispatch_detail'):
            target, kind = region['carrier'], 'carrier'
        else:
            target = region['mara']
            kind = ('aftermath' if not story.get('namar_aftermath_seen') else
                    'memory' if not story.get('namar_memory_seen') else 'ending')
        if math.dist((player.x, player.y), (target.x, target.y)) < 150:
            return NamarScene(kind, player, region, story, dialogue, quests, inventory, load)
    return None


class NamarScene:
    def __init__(self, phase, player, region, story, dialogue, quests, inventory, load):
        self.phase, self.player, self.region, self.story = phase, player, region, story
        self.dialogue, self.quests, self.inventory = dialogue, quests, inventory
        self.active, self.autosave_requested = True, False
        self.sequence, self.actor = None, None
        self.elapsed_ms = 0
        self.guards = [NPC(f'namar_guard_pose_{i}', 'Guarda', position, {},
            load(f'assets/vale_characters/red_soldier_{i}_idle.png'),
            run_sprite=load(f'assets/vale_characters/red_soldier_{i}_walk.png'), frame_size=32, draw_size=64)
            for i, position in enumerate(PROTECT_SPAWNS)]
        if phase in {'intro', 'choice'}:
            region['carrier'].x, region['carrier'].y = 1100, 490
        self.memory_actors = [NPC(f'namar_voice_{i}', 'Voz', (807+i*112, 300+i*18), {},
            load(f'assets/vale_characters/red_soldier_{i}_idle.png'), frame_size=32, draw_size=64)
            for i in range(2)]
        # Presentation-only silhouettes conceal faces and uniform details in the fragment.
        for actor in self.memory_actors:
            rows = []
            for row in actor.prepared:
                silhouettes = []
                for frame in row:
                    im = frame.copy()
                    im.fill((70, 75, 83, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    silhouettes.append(im)
                rows.append(tuple(silhouettes))
            actor.prepared = tuple(rows)
        player.attack_timer = player.attack_cooldown_timer = 0
        player.dash_timer = player.dash_iframes = player.dash_recovery_timer = 0
        player.moving = False
        player.walk_frame = 0
        player.dash_trail.clear()
        player.facing = 2 if phase in {'intro', 'choice'} else 3
        self._open(phase)

    @property
    def memory_visible(self): return self.active and self.phase == 'memory'

    @property
    def focus(self):
        if self.memory_visible: return self.region['memory_center']
        if self.phase in {'intro', 'choice', 'departure'}: return (955, 615)
        target = self.region['carrier'] if self.phase == 'carrier' else self.region['mara']
        return ((self.player.x+target.x)/2, (self.player.y+target.y)/2-10)

    @property
    def world_actors(self):
        if self.memory_visible: return tuple(self.memory_actors)
        if self.phase in {'intro', 'choice', 'departure'}:
            return tuple(self.guards) + (() if self.region['carrier'] in self.region['npcs'] else (self.region['carrier'],))
        return ()

    def _talk(self, lines):
        self.actor = ScriptedDialogue(lines)
        self.actor.x, self.actor.y = self.focus
        self.dialogue.open(self.actor)

    def _open(self, phase):
        self.phase, self.elapsed_ms, self.sequence = phase, 0, None
        if phase == 'choice':
            self.actor = ScriptedDialogue(((P, 'Não consigo alcançar os dois antes do portão fechar.'),))
            self.actor.x, self.actor.y = self.focus
            self.dialogue.open_choices(self.actor, CHOICES)
        elif phase == 'memory':
            self.sequence = NarrativeSequence((
                Beat(None, 350, 'world'), Beat('Não podemos salvar todos.', 1900, 'world'),
                Beat(None, 180, 'black'), Beat('Então escolha quem fica.', 1800, 'world'),
                Beat(None, 650, 'world'),
                Beat('Eu já conheço esse silêncio depois de escolher.', 1700, 'world')))
            self.sequence.start()
        elif phase == 'departure':
            self.sequence = NarrativeSequence((Beat(
                'A carga ou os registros. O portão não espera.', 1450, 'world'),))
            self.sequence.start()
        else:
            self._talk(INTRO if phase == 'intro' else CARRIER if phase == 'carrier'
                       else AFTERMATH[choice(self.story)] if phase == 'aftermath' else ENDING)

    def advance(self):
        if self.active and self.sequence is None and self.phase != 'choice': self.dialogue.advance()

    def choose(self, index):
        if self.phase != 'choice' or not self.active or choice(self.story): return False
        if not self.dialogue.choose(index): return False
        self.story.set('namar_choice_protect', index == 0)
        self.story.set('namar_choice_pursue', index == 1)
        self.story.set('namar_supplies_lost', index == 1)
        apply_state(self.region, self.story)
        self.region['mara'].x, self.region['mara'].y = 820, 660
        self.region['teo'].x, self.region['teo'].y = 920, 700
        self.region['carrier'].x, self.region['carrier'].y = 1100, 490
        self.autosave_requested = True
        self._open('departure')
        return True

    def _commit(self):
        if self.phase == 'intro':
            self.story.set('namar_survivors_met')
            self.autosave_requested = True
            self._open('choice')
        elif self.phase == 'departure':
            apply_state(self.region, self.story)
            self.active = False
            self.quests.notice = ('Defenda a carroça de Mara e Téo.' if choice(self.story) == 'protect'
                                  else 'Afaste os guardas e alcance o portador pelo pedágio.')
            self.quests.notice_timer = 240
        elif self.phase == 'carrier':
            self.story.set('namar_dispatch_detail')
            self.autosave_requested = True
            apply_state(self.region, self.story)
            self.active = False
        elif self.phase == 'aftermath':
            self.story.set('namar_aftermath_seen')
            if choice(self.story) == 'protect': add_inventory_item(self.inventory, consumable('potion', 2))
            self.autosave_requested = True
            self._open('memory')
        elif self.phase == 'memory':
            self.story.set('namar_memory_seen')
            self.autosave_requested = True
            self._open('ending')
        elif self.phase == 'ending':
            self.story.set('namar_record_lead_found')
            self.story.set('namar_completed')
            self.autosave_requested = True
            apply_state(self.region, self.story)
            self.quests.notice = 'Ecos da Guerra: encontre a segunda via da ordem de Namar.'
            self.quests.notice_timer = 300
            self.active = False
        if not self.active: self.sequence = None

    def update(self, delta_ms):
        if not self.active: return False
        self.elapsed_ms += delta_ms
        if self.phase == 'departure':
            t = min(1, self.elapsed_ms/1450)
            def travel(points):
                u = min(len(points)-1-.000001, t*(len(points)-1))
                a, b = points[int(u)], points[int(u)+1]
                return tuple(a[k]+(b[k]-a[k])*(u-int(u)) for k in (0, 1))
            carrier = self.region['carrier']
            carrier.running, carrier.facing = True, 3
            carrier.x, carrier.y = travel(((1100,490),(1220,430),(1220,230))
                if choice(self.story) == 'protect' else ((1100,490),(1200,430),(1200,270)))
            for i, actor in enumerate(self.guards):
                actor.running, actor.facing = True, 3 if choice(self.story) == 'pursue' else 0
                actor.x, actor.y = travel((PROTECT_SPAWNS[i], PURSUE_SPAWNS[i])) if choice(self.story) == 'pursue' else PROTECT_SPAWNS[i]
            if choice(self.story) == 'pursue':
                self.region['mara'].x, self.region['mara'].y = travel(((820,660),(655,680),(655,750),(605,773)))
                self.region['teo'].x, self.region['teo'].y = travel(((920,700),(670,690),(670,750),(682,790)))
                self.region['mara'].running = self.region['teo'].running = True
                self.region['mara'].facing = self.region['teo'].facing = 1 if t < 1/3 else 0
        if self.phase == 'choice': return False
        if self.sequence is not None:
            if not self.sequence.update(delta_ms): return False
        elif self.dialogue.active: return False
        self._commit()
        return not self.active

    def finish(self):
        """F4 skips only the current beat; a pending priority always needs an explicit choice."""
        if not self.active or self.phase == 'choice': return False
        if self.dialogue.npc is self.actor: self.dialogue.npc = None
        self._commit()
        return not self.active

    def draw_overlay(self, canvas):
        if not self.memory_visible: return
        veil = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
        veil.fill((22, 18, 24, 160)); canvas.blit(veil, (0, 0))
        pygame.draw.rect(canvas, (15, 17, 22), (0, 132, canvas.width, 8))
        pygame.draw.rect(canvas, (15, 17, 22), (0, 410, canvas.width, 5))
        if self.sequence.current and self.sequence.remaining_ms > self.sequence.current.duration_ms-90:
            veil.fill((158, 136, 104, 70)); canvas.blit(veil, (0, 0))
