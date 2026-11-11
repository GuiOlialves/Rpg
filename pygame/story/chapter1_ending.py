"""1G: a voluntary journey home, responsibility and the end of Ecos da Guerra."""
import pygame
import environment as env
from entities.interactable import Interactable
from entities.namar_survivor import NamarSurvivor
from story.arrival_scene import ScriptedDialogue
from story.chapter1_return import Chapter1AldenScene, settle_player
from story.sequence import Beat, NarrativeSequence
from story.fade import FadeOverlay
from systems.items import quest_item
from systems.inventory import add_inventory_item
from world.regions.archive_art import prop
from world.regions.watchpost_art import prop as furniture

ENDING_FLAGS=('chapter1_final_returned','chapter1_consequences_seen','chapter1_final_alden_talk',
              'encosta_receipt_found','encosta_destination_known','chapter1_final_memory_seen',
              'chapter1_final_reflection_seen','chapter1_completed','chapter2_started')
P='Protagonista'
DESTINATION='Posto de Convalescença da Encosta'


class ValeSurvivor(NamarSurvivor):
    def dialogue_for(self,state,manager=None):
        if self.story.get('namar_choice_protect'):
            return (('A farinha chegou ao abrigo. Hoje conseguimos dividir pão com quem veio depois de nós.',
                     'Téo descarregou devagar. Não precisamos escolher entre comer e refazer a roda.') if self.survivor_identity=='mara' else
                    ('A roda aguentou até o Vale. Agora posso cuidar desta mão sem deixar Mara na estrada.',
                     'Você ficou com a carroça. Eu me lembro.'))
        return (('Chegamos ao Vale. O abrigo dividiu o estoque conosco; também vamos ter de ajudar a repor.',
                 'Você voltou com os registros? Espero que encontre o que aconteceu com quem não atravessou.') if self.survivor_identity=='mara' else
                ('Consegui refazer a roda aqui. A mão ainda dói; vou precisar de mais alguns dias.',
                 'Aquele índice não trouxe a farinha de volta. Pode trazer uma resposta. Quero ouvir quando souber.'))


def _add(region,obj):
    if not any(o.uid==obj.uid for o in region['interactables']): region['interactables'].append(obj)


def apply_state(region,story,load):
    if not story.get('archive_completed'): return
    kind=region.get('ambient_kind')
    if kind=='archive':
        _add(region,Interactable('chapter1_return_vale',P,(246,817),prop('papers'),
            ('A segunda via está comigo. Posso seguir pela estrada de serviço e voltar ao Vale antes de escurecer.',),
            prompt='[E] Voltar ao Vale pela estrada de serviço',transition_to='village'))
    elif kind=='village':
        if not region.get('chapter1_final_village_applied'):
            for uid,name,position in (('mara','Mara',(1610,695)),('teo','Téo',(1678,708))):
                npc=ValeSurvivor(uid,name,position,load); npc.story=story
                npc.uid='vale_'+uid
                # NamarSurvivor selects its atlas using the constructor uid above.
                npc.survivor_identity=uid
                region['npcs'].append(npc); region['obstacles'].append(npc.hitbox)
            desk=env.anchored(furniture('desk'),(1780,695))
            region.setdefault('scenery',[]).append(desk)
            region['obstacles'].append(pygame.Rect(1723,665,114,30))
            region['chapter1_final_village_applied']=True
        for npc in region['npcs']:
            if npc.uid in ('vale_mara','vale_teo'): npc.story=story
        ledger=Interactable('encosta_receipt',P,(1780,655),prop('papers'),(
            'Livro de recebimento do Vale. Alden deixou aberta a página das remessas da terceira vigília.',
            'O número de controle no verso da segunda via corresponde a uma entrada: "R-17 / N-04. Encaminhamento de custódia. Destino: Posto de Convalescença da Encosta."',
            'O livro confirma o recebimento para reenvio. Não registra quem executou um procedimento, nem se ele aconteceu.',
            'A planta de entrega marca a estrada acima da encosta e o selo do posto. Tenho um destino para procurar a via que falta.'),
            prompt='[E] Conferir recibo do encaminhamento')
        ledger.enabled=story.get('chapter1_final_alden_talk') and not story.get('encosta_receipt_found')
        _add(region,ledger)
        for obj in region['interactables']:
            if obj.uid=='encosta_receipt': obj.enabled=ledger.enabled
        if story.get('chapter1_final_alden_talk'):
            alden=next(n for n in region['npcs'] if n.uid=='alden')
            alden.dialogues={'default':('O recibo não diz o que fizeram com você. Guarde a segunda via junto da identificação.',
                                       'Quando procurar a Encosta, procure também quem não pôde voltar.')}
    elif kind=='home':
        # Keep the reachable hotspot in front of the table; draw the records
        # on its surface rather than at the hero's feet.
        records=pygame.Surface((70,110),pygame.SRCALPHA)
        records.blit(pygame.transform.scale_by(prop('order'),.5),(30,8))
        records.blit(pygame.transform.scale_by(furniture('token'),.5),(8,15))
        final=Interactable('chapter1_final_records',P,(619,392),records,(),
                           prompt='[E] Examinar R-17 e a segunda via',interaction_radius=80)
        final.visual_depth=398
        final.enabled=story.get('encosta_receipt_found') and not story.get('chapter1_completed')
        _add(region,final)
        for obj in region['interactables']:
            if obj.uid=='chapter1_final_records': obj.enabled=final.enabled


def complete_evidence(target,story,inventory):
    uid=getattr(target,'uid','')
    if uid in ('vale_mara','vale_teo') and not story.get('chapter1_consequences_seen'):
        story.set('chapter1_consequences_seen'); return True
    if uid!='encosta_receipt' or not target.enabled or story.get('encosta_receipt_found'): return False
    story.set('encosta_receipt_found'); story.set('encosta_destination_known')
    add_inventory_item(inventory,quest_item('encosta_receipt'))
    return True


class FinalAldenScene(Chapter1AldenScene):
    debug_label='chapter1_final_alden'
    STEPS=(
        (('Alden','Encontrou o que procurava?'),(P,'Encontrei uma ordem. Não sei se encontrei uma resposta.')),
        Beat(None,600,'world'),
        ((P,'Mandaram fechar Namar com gente esperando do outro lado. A decisão foi minha.'),
         ('Alden','É isso que está escrito?'),(P,'Está escrito. E eu me lembro de ouvir o aviso antes de confirmar.')),
        Beat(None,1000,'world'),
        (('Alden','Você veio me perguntar que tipo de homem faria isso?'),(P,'Talvez. Uma folha diz que salvamos a retirada. Outra pede pelos que ficaram.'),
         ('Alden','Não vi aquela margem. Não vou dar uma absolvição que não tenho como sustentar.')),
        Beat(None,650,'world'),
        ((P,'Também não quero me condenar para encerrar a pergunta. Preciso saber o que aconteceu com eles.'),
         ('Alden','Então não procure só o seu nome nos papéis. Procure as pessoas.'),
         (P,'E se alguém mudou os registros?'),('Alden','Você tem duas versões. Guarde as duas. A que incomoda também.')),
        Beat(None,650,'world'),
        ((P,'O pedido de esquecer veio antes da queda da ponte. Mandaram uma via para o Vale.'),
         ('Alden','Vire essa folha. Esse número pequeno é de recebimento, não de ordem.'),
         ('Alden','Eu anotava as remessas que passavam pela vila. Não sabia o que havia dentro dos envelopes.'),
         ('Alden','Vou deixar o livro aberto na mesa. Compare o número antes de decidir para onde ir.')),
        Beat(None,700,'world'),
        ((P,'Quando eu sair de novo, não será só para descobrir quem fui.'),
         ('Alden','Coma alguma coisa antes. Você pode procurar a verdade sem desaparecer junto dela.')),
    )

    def _open_step(self,dialogue):
        step=self.STEPS[self.index]; self.sequence=None
        self.alden.face_player(self.player)
        if isinstance(step,Beat):
            self.sequence=NarrativeSequence((step,)); self.sequence.start()
        else:
            self.dialogue_actor=ScriptedDialogue(step)
            self.dialogue_actor.x,self.dialogue_actor.y=self.alden.x,self.alden.y
            dialogue.open(self.dialogue_actor)

    def finish(self,dialogue,story,quests,inventory):
        if not self.active: return False
        story.set('chapter1_final_alden_talk')
        story.apply_to_region(self.region)
        if dialogue.npc is self.dialogue_actor: dialogue.npc=None
        self.active=False; self.sequence=None
        quests.notice='Confira o recibo no livro que Alden abriu.'; quests.notice_timer=230
        return True


class Chapter1EndingScene:
    """Each finished beat is saved; the title finishes before control is returned."""
    def __init__(self,player,story,quests):
        self.player,self.story,self.quests=player,story,quests
        self.active=not story.get('chapter1_completed'); self.autosave_requested=False
        self.phase=('fade' if story.get('chapter1_final_reflection_seen') else
                    'reflection' if story.get('chapter1_final_memory_seen') else 'memory')
        self.elapsed_ms=0; self.fade=FadeOverlay()
        if self.active:
            settle_player(player); player.x,player.y=613,409; player.facing=3
        self._open()

    def _open(self):
        self.elapsed_ms=0
        if self.phase=='memory':
            self.sequence=NarrativeSequence((Beat(None,1200,'world'),
                Beat('Uma voz: "Tem certeza de que deseja fazer isso?"',2200,'black'),
                Beat(None,1600,'black'),Beat('Eu: "Tenho."',1050,'black'),Beat(None,600,'black')))
        elif self.phase=='reflection':
            self.sequence=NarrativeSequence((Beat(None,800,'world'),
                Beat('Eu pedi para esquecer. Não vou deixar que isso responda por mim.',2400,'world'),
                Beat(None,750,'world')))
        elif self.phase=='fade':
            self.sequence=NarrativeSequence((Beat(None,850,'world'),)); self.fade.start('out',850)
        elif self.phase=='restore':
            self.sequence=NarrativeSequence((Beat(None,700,'world'),)); self.fade.start('in',700)
        else:
            self.sequence=NarrativeSequence((Beat(None,700),Beat(None,2300),Beat(None,650)))
        self.sequence.start()

    def _commit(self):
        if self.phase=='memory':
            self.story.set('chapter1_final_memory_seen'); self.autosave_requested=True
            self.phase='reflection'
        elif self.phase=='reflection':
            self.story.set('chapter1_final_reflection_seen'); self.autosave_requested=True
            self.phase='fade'
        elif self.phase=='fade': self.phase='card'
        elif self.phase=='card':
            self.story.set('chapter1_completed'); self.story.set('chapter2_started',False)
            self.phase='restore'; self.autosave_requested=True
            self.quests.notice='Capítulo I concluído. A pista da Encosta foi registrada.'; self.quests.notice_timer=300
        else:
            self.active=False
            return True
        self._open(); return False

    def update(self,delta_ms):
        if not self.active: return False
        self.elapsed_ms+=delta_ms; self.fade.update(delta_ms)
        if self.sequence.update(delta_ms): return self._commit()
        return False

    def finish(self):
        if not self.active: return False
        return self._commit()

    def draw(self,canvas,render_world):
        from ui.narrative_overlay import draw_narrative
        if self.phase!='card':
            draw_narrative(canvas,self.sequence,world_renderer=render_world)
            if self.phase in ('fade','restore'): self.fade.draw(canvas)
            return
        canvas.fill((5,7,10))
        alpha=round(255*min(1,self.elapsed_ms/700,max(0,(3650-self.elapsed_ms)/650)))
        for text,size,offset,color in (('CAPÍTULO I CONCLUÍDO',26,-35,(179,163,128)),
                                       ('ECOS DA GUERRA',46,12,(229,218,191))):
            im=pygame.font.Font(None,size).render(text,True,color); im.set_alpha(alpha)
            canvas.blit(im,im.get_rect(center=(canvas.width//2,canvas.height//2+offset)))
