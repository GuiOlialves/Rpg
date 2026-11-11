"""Chapter 1F: documentary perspectives, a guarded order and an incomplete act of memory."""
import pygame
from entities.npc import NPC
from story.arrival_scene import ScriptedDialogue
from story.sequence import Beat, NarrativeSequence
from systems.items import quest_item
from systems.inventory import add_inventory_item
from ui.character_art import prepared_frames
from world.regions.archive import prepare_memory

ARCHIVE_FLAGS=('archive_entered','archive_search_marks','archive_defense_report','archive_petition',
               'archive_confrontation_started','archive_veteran_defeated','archive_order_obtained',
               'archive_memory_seen','archive_forgetting_record','archive_completed')
EVIDENCE={'archive_search':'archive_search_marks','archive_defense':'archive_defense_report',
          'archive_petition':'archive_petition','archive_order':'archive_order_obtained',
          'archive_forgetting':'archive_forgetting_record'}
P='Protagonista'


def document_lines(uid,story):
    if uid == 'archive_search': return (
        'Etiquetas vermelhas arrancadas dos armários. Um lacre azul mais recente prende um maço vazio.',
        'Duas buscas diferentes. Alguém separou os nomes e tentou queimar as folhas. As bordas ainda têm cinza.',
        'A placa da sala seca não foi retirada: Livro de Ordens. Gavetas de 1 a 9.')
    if uid == 'archive_defense': return (
        ('N-04, série da retaguarda. A referência do portador confere.' if story.get('namar_dispatch_detail') else
         'Relatório da retaguarda. A série do cabeçalho queimou, mas o título ainda diz: retirada de Namar.'),
        'O intendente da escolta R-17 registra: "O fechamento da travessia reteve a vanguarda azul e conservou a estrada de evacuação para o Vale."',
        '"Sem a contenção, a coluna de feridos seria alcançada antes da encosta." É uma avaliação militar, não uma contagem de sobreviventes.',
        'A última linha limita o relato: "Conclusão baseada nos sinais da margem seca. Sem observação da outra margem após o fechamento."')
    if uid == 'archive_petition': return (
        'Petição entregue por Lia, representante dos atravessadores: "As grades baixaram enquanto famílias, carregadores e soldados ainda aguardavam embarque."',
        '"O oficial com autoridade R-17 manteve a passagem fechada. Pedimos os nomes dos retirados e dos que ficaram."',
        'Lia escreveu do lado de fora. Não tinha acesso aos sinais da retaguarda; a lista anexa foi arrancada.',
        ('Mara preservou a farinha hoje. Esta petição fala de gente a quem nem essa chance foi dada.' if story.get('namar_choice_protect') else
         'Deixei a carga de Mara para alcançar um índice. Aqui, famílias pediam algo tão concreto quanto aquela farinha.'),
        'O pedido foi recebido. Não há resposta nem prova do destino de todos os citados.')
    if uid == 'archive_order': return (
        'Gaveta 7. Livro de Ordens — travessia de Namar. A segunda via está presa sob uma chapa de ferro.',
        'Operação N-04. Unidade de escolta R-17. Campo de autoridade: comando da retirada. O nome foi raspado; a marca pessoal é a mesma da minha identificação.',
        '"Baixar as grades da travessia. Suspender os embarques da margem oposta. Manter a passagem fechada até a retirada da coluna de feridos pela encosta."',
        'No rodapé: "Aviso recebido: ainda há pessoas aguardando na outra margem. Fechamento confirmado pela autoridade R-17."',
        'Não é apenas alguém dizendo que eu dava ordens. Alguém registrou a decisão que eu confirmei. A folha com o resultado foi removida.')
    return (
        'Uma ficha chamuscada foi grampeada à ordem: "Encaminhamento — ESQUECIMENTO. Requerente: autoridade R-17. Referência obrigatória: operação N-04."',
        'Recibo do pedido: terceira vigília. A folha de ocorrências anexa registra o colapso de Namar na quarta. O pedido veio antes, como Edrin disse.',
        '"Via do requerente: remeter ao Vale." O destinatário e o campo do responsável foram queimados.',
        'A referência de operação e a marca R-17 aparecem nas duas folhas. Existe uma ligação verificável com o pedido de esquecer; ainda não sei quem o recebeu ou o que fizeram.')


def apply_state(region,story):
    started,defeated=story.get('archive_confrontation_started'),story.get('archive_veteran_defeated')
    active=started and not defeated
    region['boss_battle_active']=active
    region['obstacles']=list(region['base_obstacles'])
    if not defeated: region['obstacles'].append(region['vault_lock'])
    if active: region['obstacles'].append(region['yard_lock'])
    region['yard_gate'].image.set_alpha(255 if active else 60)
    region['vault_gate'].image.set_alpha(255 if not defeated else 60)
    region['exits']={} if active else {'namar':pygame.Rect(178,930,132,30)}
    veteran=region['veteran']
    veteran.hostile=active
    if defeated:
        veteran.state='DEFEATED'; veteran.hp=1
        veteran.anim_tick=24; veteran.visual_flash=0
        veteran.attack_zone=veteran.attack_action=veteran.attack_phase=None
    if active:
        if veteran in region['scenery']: region['scenery'].remove(veteran)
    elif veteran not in region['scenery']: region['scenery'].append(veteran)
    for obj in region['interactables']:
        if obj.uid not in EVIDENCE: continue
        obj.dialogues['default']=document_lines(obj.uid,story)
        obj.enabled=not active
        if obj.uid == 'archive_order': obj.enabled &= defeated
        if obj.uid == 'archive_forgetting': obj.enabled &= story.get('archive_memory_seen')
    region['story_phase']='archive_complete' if story.get('archive_completed') else 'archive_battle' if active else 'archive_investigation'


def spawn_pending(region,story):
    return [region['veteran']] if story.get('archive_confrontation_started') and not story.get('archive_veteran_defeated') else []


def complete_evidence(target,story,inventory):
    flag=EVIDENCE.get(getattr(target,'uid',''))
    if flag is None or story.get(flag) or not target.enabled: return False
    story.set(flag)
    if flag == 'archive_order_obtained': add_inventory_item(inventory,quest_item('namar_order_copy'))
    return True


def complete_combat(region,story,enemies):
    if (story.get('archive_confrontation_started') and not story.get('archive_veteran_defeated')
            and region['veteran'] in enemies and region['veteran'].state == 'DEFEATED'):
        story.set('archive_veteran_defeated')
        apply_state(region,story)
        enemies.remove(region['veteran'])
        return True
    return False


def moment_at(player,region,story,dialogue,quests,load):
    if story.get('archive_completed'): return None
    if story.get('archive_forgetting_record'):
        return ArchiveScene('ending',player,region,story,dialogue,quests,load)
    if story.get('archive_order_obtained') and not story.get('archive_memory_seen'):
        return ArchiveScene('memory',player,region,story,dialogue,quests,load)
    if (not story.get('archive_confrontation_started')
            and all(story.get(f) for f in ('archive_defense_report','archive_petition'))
            and region['arena_trigger'].colliderect(player.hitbox)):
        return ArchiveScene('challenge',player,region,story,dialogue,quests,load)
    return None


class PastCommander:
    def __init__(self,load):
        self.x,self.y=867,302
        self.order_given=False
        self.frames={}
        for action in ('idle','attack'):
            sheet=load(f'assets/vale_characters/protagonist_{action}.png').copy()
            # Uniform of the same protagonist; faces and body proportions are preserved.
            for old,new in (((63,122,120),(184,92,87)),((46,80,92),(113,61,80)),((108,164,154),(225,138,103))):
                pixels=pygame.PixelArray(sheet)
                pixels.replace(old,new); del pixels
            self.frames[action]=prepared_frames(sheet,64,cell=32,height=36)
    def draw(self,canvas,camera):
        action,index=('attack',3) if self.order_given else ('idle',0)
        image=self.frames[action][0][index]
        canvas.blit(image,(round(self.x-32-camera[0]),round(self.y-68-camera[1])))


class ArchiveScene:
    def __init__(self,phase,player,region,story,dialogue,quests,load):
        self.phase,self.player,self.region,self.story=phase,player,region,story
        self.dialogue,self.quests=dialogue,quests
        self.active,self.autosave_requested=True,False
        self.sequence=None
        self.actor=None
        self.elapsed_ms=0
        self.commander=None
        self.memory_actors=()
        player.attack_timer=player.attack_cooldown_timer=0
        player.dash_timer=player.dash_iframes=player.dash_recovery_timer=0
        player.moving=False; player.dash_trail.clear()
        if phase == 'memory':
            prepare_memory(region,load)
            self.commander=PastCommander(load)
            soldiers=[NPC(f'archive_memory_{i}','Voz',(755+i*230,324),{},
                load(f'assets/vale_characters/red_soldier_{i}_idle.png'),frame_size=32,draw_size=64)
                for i in range(2)]
            soldiers[0].facing=2; soldiers[1].facing=1
            self.memory_actors=(self.commander,*soldiers)
            self.sequence=NarrativeSequence((
                Beat('Pedágio de Namar. Antes do colapso.',1300,'world'),
                Beat('Voz da retaguarda: "A vanguarda alcança a coluna na encosta!"',2200,'world'),
                Beat('Outra voz: "Ainda há pessoas lá fora!"',2200,'world'),
                Beat('Eu: "Baixem as grades. Ninguém mais atravessa. Mantenham fechado até a coluna passar."',3200,'world'),
                Beat(None,400,'black'),
                Beat('Eu ouvi o aviso. E dei a ordem.',1800,'world')))
            self.sequence.start()
        else:
            lines=(( 'Soren','Não toque naquela gaveta. Meu nome é Soren. Minha irmã assinou a petição que você leu.'),
                   ( 'Soren','Os vermelhos querem apagar os nomes. Os azuis querem levá-los para achar as famílias. Já vi os dois lacres aqui.'),
                   ( P,'Quero a ordem da travessia. Não a lista das famílias.'),
                   ( 'Soren','Foi assim que a primeira patrulha pediu acesso. Deixei-os entrar e encontrei a lista nas cinzas.'),
                   ( P,'O relatório diz que fechar a passagem protegeu a retirada.'),
                   ( 'Soren','E Lia esperava do outro lado. Não vou confiar os registros a outra espada.')) if phase == 'challenge' else (
                   ( P,'Soren largou a arma. A decisão está na segunda via, não numa confissão arrancada dele.'),
                   ( P,'A retaguarda fala dos feridos que conseguiu retirar. Lia fala de quem não pôde atravessar. Nenhuma folha acompanha todos os que ficaram.'),
                   ( P,'Eu tinha autoridade, recebi o aviso e confirmei o fechamento. Isso agora é parte do que sei.'),
                   ( P,'O encaminhamento liga R-17, N-04 e meu pedido de esquecer. A parte sobre o responsável foi destruída.'),
                   ( P,'Vou levar a segunda via ao Vale e procurar Alden. Preciso descobrir quem recebeu o encaminhamento e o que minha decisão deixou para trás.'))
            self.actor=ScriptedDialogue(lines)
            self.actor.x,self.actor.y=self.focus
            dialogue.open(self.actor)

    @property
    def memory_visible(self): return self.active and self.phase == 'memory'
    @property
    def focus(self): return self.region['memory_center'] if self.memory_visible else (875,558) if self.phase == 'challenge' else (920,290)
    @property
    def world_actors(self): return self.memory_actors if self.memory_visible else ()
    def advance(self):
        if self.active and self.sequence is None: self.dialogue.advance()

    def _commit(self):
        self.story.set({'challenge':'archive_confrontation_started','memory':'archive_memory_seen','ending':'archive_completed'}[self.phase])
        self.autosave_requested=True
        self.active=False; self.sequence=None
        if self.dialogue.npc is self.actor: self.dialogue.npc=None
        apply_state(self.region,self.story)
        self.quests.notice={'challenge':'Esquive. Ataque na recuperação.',
                            'memory':'O pedido de esquecer está anexado à ordem. Examine a ficha chamuscada.',
                            'ending':'Ecos da Guerra: volte ao Vale com a segunda via.'}[self.phase]
        self.quests.notice_timer=300

    def update(self,delta_ms):
        if not self.active: return False
        self.elapsed_ms+=delta_ms
        if self.commander: self.commander.order_given=self.elapsed_ms>=5700
        if self.sequence is not None:
            if not self.sequence.update(delta_ms): return False
        elif self.dialogue.active: return False
        self._commit(); return True

    def finish(self):
        if not self.active: return False
        self._commit(); return True

    def draw_overlay(self,canvas):
        if self.memory_visible:
            veil=pygame.Surface(canvas.get_size(),pygame.SRCALPHA)
            veil.fill((40,24,18,58)); canvas.blit(veil,(0,0))
