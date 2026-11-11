"""Chapter II / A: receipt -> Encosta -> witnesses -> an unopened threshold."""
import pygame
from core.assets import load
from entities.interactable import Interactable
from story.arrival_scene import ScriptedDialogue
from story.chapter1_return import settle_player
from story.sequence import Beat, NarrativeSequence
from story.fade import FadeOverlay
from story.resonance import BY_ID, POINTS, ResonanceScene
from systems.inventory import add_inventory_item
from systems.items import quest_item, consumable

from story.lacre_content import REGIONS as DUNGEON_REGIONS, ENTER_FLAGS, FLAGS as LACRE_FLAGS, DEFEATS as LACRE_DEFEATS
REGIONS=('forgotten_route','encosta','threshold')+DUNGEON_REGIONS
FLAGS=('chapter2_started','chapter2_departure_seen','chapter2_title_seen','route_entered',
       'route_cache_found','route_record_found','route_rest_found','encosta_entered',
       'ines_met','breno_met','encosta_register_found','encosta_locket_found',
       'encosta_symbol_found','encosta_investigated','echo_meal_seen','echo_departure_seen',
       'echo_orders_seen','encosta_puzzle_step1','encosta_puzzle_step2','encosta_puzzle_solved',
       'encosta_sealed_record_found','encosta_choice_shared','encosta_choice_kept',
       'encosta_destination_found','threshold_entered','threshold_vista_seen',
       'threshold_activity_seen','threshold_guard_defeated','echo_threshold_seen',
       'chapter2_part_a_completed','chapter2_part_b_started','chapter2_completed')
DEFEAT_FLAGS=tuple(f'c2_{region}_enemy_{i}_defeated'
                   for region,count in (('forgotten_route',5),('threshold',2)) for i in range(count))
ALL_FLAGS=FLAGS+DEFEAT_FLAGS+LACRE_FLAGS+LACRE_DEFEATS
EVIDENCE={'encosta_register':'encosta_register_found','encosta_locket':'encosta_locket_found',
          'encosta_symbol':'encosta_symbol_found'}
P='Protagonista'


def investigated(story): return all(story.get(f) for f in EVIDENCE.values())
def puzzle_ready(story):
    return investigated(story) and all(story.get(f) for f in ('ines_met','breno_met','echo_meal_seen','echo_departure_seen','echo_orders_seen'))


def objective(story):
    if story.get("chapter2_part_b_started"):
        from story.lacre import objective as dungeon_objective
        return dungeon_objective(story)
    if story.get('chapter2_part_a_completed'): return 'Entre na Câmara dos Testemunhos e descubra a origem das memórias.'
    if story.get('threshold_guard_defeated'): return 'Toque o selo na entrada da Câmara dos Testemunhos.'
    if story.get('threshold_entered'): return 'Observe a aproximação e alcance a entrada da Câmara.'
    if story.get('encosta_destination_found'): return 'Suba pelo arco norte até a Câmara dos Testemunhos.'
    if story.get('encosta_sealed_record_found'): return 'Decida com Inês o destino do registro; compare a planta de custódia.'
    if story.get('encosta_puzzle_solved'): return 'Examine o compartimento aberto no armário de custódia.'
    if story.get('encosta_investigated') and not (story.get('ines_met') and story.get('breno_met')):
        return 'Ouça Inês e Breno sobre os nomes encaminhados à Câmara.'
    if puzzle_ready(story): return 'Abra o armário seguindo o rito indicado no registro comunitário.'
    if story.get('encosta_investigated'): return 'Escute os ecos da mesa, da carroça e do selo de custódia.'
    if story.get('encosta_entered'): return 'Converse com Inês e Breno; examine o livro, o pingente e o selo.'
    if story.get('route_entered'): return 'Atravesse as Pedras Afundadas até o Posto de Convalescença da Encosta.'
    return 'Siga a placa da Encosta junto à saída leste do Vale.'


def apply_state(region,story):
    kind=region.get('ambient_kind')
    from story.lacre import apply_state as apply_dungeon
    apply_dungeon(region,story)
    if kind in DUNGEON_REGIONS: return
    if kind=='village' and story.get('chapter1_completed'):
        if not any(o.uid=='encosta_route_marker' for o in region['interactables']):
            from world.regions.encosta_art import prop
            sign=Interactable('encosta_route_marker','Encosta',(1870,480),prop('route_sign'),
                ('A estrada sobe entre os marcos antigos. O selo do recibo aponta para a Encosta.',),
                prompt='[E] Seguir para a Encosta',transition_to='forgotten_route',transition_on_interact=True)
            region['interactables'].append(sign)
        sign=next(o for o in region['interactables'] if o.uid=='encosta_route_marker')
        sign.enabled=story.get('chapter2_departure_seen') and story.get('chapter2_title_seen')
        if story.get('chapter2_departure_seen'):
            alden=next(n for n in region['npcs'] if n.uid=='alden')
            alden.dialogues={'default':('A placa da Encosta está junto à saída leste. A estrada de pedra acompanha o riacho.',
                                       'Quando puder, traga notícias. Não precisa trazer certeza.')}
    if kind not in REGIONS: return
    region['story_phase']='chapter2_a'
    if kind=='forgotten_route': region['rest_checkpoint']=story.get('route_rest_found')
    for npc in region['npcs']: npc.story=story
    if kind=='encosta':
        gate=region['north_gate']
        barrier=region['north_barrier']
        region['scenery']=[o for o in region['scenery'] if o is not barrier]
        region['obstacles']=[o for o in region['obstacles'] if o!=gate]
        if story.get('encosta_destination_found'):
            region['exits']['threshold']=region['north_exit']
        else:
            region['exits'].pop('threshold',None); region['obstacles'].append(gate)
            region['scenery'].append(barrier)
    # The territorial encounter gates the final interaction, not an invisible wall.
    for obj in region['interactables']:
        uid=obj.uid
        if uid in BY_ID: obj.enabled=BY_ID[uid].available(story)
        elif uid.startswith('cabinet_'): obj.enabled=puzzle_ready(story) and not story.get('encosta_puzzle_solved')
        elif uid=='sealed_record': obj.enabled=story.get('encosta_puzzle_solved') and not story.get('encosta_sealed_record_found')
        elif uid=='custody_plan': obj.enabled=story.get('encosta_sealed_record_found') and (story.get('encosta_choice_shared') or story.get('encosta_choice_kept'))
        elif uid=='route_cache': obj.enabled=not story.get('route_cache_found')
        elif uid=='route_record': obj.enabled=not story.get('route_record_found')
        elif uid=='chamber_entrance': obj.enabled=story.get('chapter2_part_a_completed')
    for label in region.get('puzzle_markers',()):
        label.opened=story.get('encosta_puzzle_solved')


def spawn_pending(region,story,spawn,actors=None):
    kind=region.get('ambient_kind')
    if kind in DUNGEON_REGIONS:
        from story.lacre import spawn_pending as dungeon_spawn
        return dungeon_spawn(region,story,spawn,actors)
    actors=spawn(region) if actors is None else actors
    return [a for a in actors if not story.get(f'c2_{kind}_enemy_{a.chapter2_id}_defeated')]


def complete_evidence(target,story,inventory,player,quests,region=None):
    if region is not None and region.get("ambient_kind") in DUNGEON_REGIONS:
        from story.lacre import evidence
        return evidence(target,story,inventory,player,quests,region)
    uid=getattr(target,'uid',''); changed=False
    if uid in ('ines','breno'):
        flag=uid+'_met'
        if not story.get(flag): story.set(flag); changed=True
    if uid in EVIDENCE and not story.get(EVIDENCE[uid]):
        story.set(EVIDENCE[uid]); changed=True
        if uid=='encosta_locket': add_inventory_item(inventory,quest_item('encosta_locket'))
        if investigated(story): story.set('encosta_investigated')
    if uid in ('route_cache','route_record','sealed_record'):
        flag={'route_cache':'route_cache_found','route_record':'route_record_found','sealed_record':'encosta_sealed_record_found'}[uid]
        if target.enabled and not story.get(flag):
            story.set(flag); changed=True
            if uid=='route_cache':
                add_inventory_item(inventory,consumable('potion',2)); add_inventory_item(inventory,consumable('ether'))
            else: add_inventory_item(inventory,quest_item('route_transfer_note' if uid=='route_record' else 'encosta_sealed_record'))
    if uid=='route_rest':
        # Rest is repeatable but never manufactures inventory rewards.
        player.hp,player.sp=player.max_hp,player.max_sp
        story.set('route_rest_found'); changed=True
        quests.notice='Descanso na varanda de pedra. HP e SP recuperados.'; quests.notice_timer=200
    if uid=='custody_plan' and target.enabled and not story.get('encosta_destination_found'):
        story.set('encosta_destination_found'); add_inventory_item(inventory,quest_item('chamber_plan')); changed=True
    if uid=='recent_camp' and not story.get('threshold_activity_seen'):
        story.set('threshold_activity_seen'); changed=True
    return changed


def puzzle_input(uid,story,quests):
    if not puzzle_ready(story) or story.get('encosta_puzzle_solved'): return False
    index=('cabinet_bowl','cabinet_lamp','cabinet_name').index(uid)
    progress=2 if story.get('encosta_puzzle_step2') else 1 if story.get('encosta_puzzle_step1') else 0
    if index!=progress:
        story.set('encosta_puzzle_step1',False); story.set('encosta_puzzle_step2',False)
        quests.notice='O fecho retorna. Primeiro acolher, depois vigiar, por último guardar o nome.'
    elif index==0:
        story.set('encosta_puzzle_step1'); quests.notice='Tigela: acolher. O primeiro fecho cedeu.'
    elif index==1:
        story.set('encosta_puzzle_step2'); quests.notice='Lamparina: vigiar. Resta guardar o nome.'
    else:
        story.set('encosta_puzzle_solved'); quests.notice='O compartimento abriu. Há uma folha sob a planta.'
    quests.notice_timer=260
    return True


def record_defeats(story,defeats,region,quests):
    for region_id,index in defeats: story.set(f'c2_{region_id}_enemy_{index}_defeated')
    if story.get('c2_threshold_enemy_1_defeated') and not story.get('threshold_guard_defeated'):
        story.set('threshold_guard_defeated'); apply_state(region,story)
        quests.notice='O ninho ficou para trás. O selo da Câmara está ao alcance.'; quests.notice_timer=240
    from story.lacre import record_defeats as dungeon_defeats
    dungeon_defeats(story,defeats,region,quests)
    return bool(defeats)


class Chapter2Scene:
    """One coordinator for departure, title, choice, vista and the A/B boundary."""
    def __init__(self,kind,player,story,dialogue,quests,inventory,region):
        self.phase=kind; self.player,self.story,self.dialogue=player,story,dialogue
        self.quests,self.inventory,self.region=quests,inventory,region
        self.focus=(player.x,player.y); self.active=True; self.autosave_requested=False
        self.elapsed_ms=0; self.sequence=None; self.actor=None; self.fade=FadeOverlay()
        self.black=pygame.Surface((1024,576)); self.black.fill((5,7,10))
        settle_player(player)
        if kind=='departure':
            self.actor=ScriptedDialogue((('Alden','Vai seguir aquele recibo?'),
                (P,'Vou procurar quem recebeu a remessa. E quem saiu de Namar.'),
                ('Alden','Leve isto. A água da subida não serve para beber em todo trecho.'),
                (P,'Você acha que eu volto?'),('Alden','Acho que pode. É por isso que estou guardando pão.')))
            self.actor.x,self.actor.y=1780,560; dialogue.open(self.actor)
        elif kind=='choice':
            self.actor=ScriptedDialogue((('Inês','Essa folha leva meu nome. Posso saber o que diz?'),))
            self.actor.x,self.actor.y=region['npcs'][0].x,region['npcs'][0].y
            dialogue.open_choices(self.actor,(('Entregar a folha a Inês.', 'Manter a referência e permitir que ela responda à acusação.'),
                                             ('Guardar por enquanto.', 'Dizer que precisa comparar os registros antes de entregá-la.')))
        else: self._timed(kind)

    def _timed(self,kind):
        self.phase=kind; self.elapsed_ms=0
        if kind=='title':
            self.sequence=NarrativeSequence((Beat(None,700,'world'),Beat(None,3400,'black'),Beat(None,700,'world')))
            self.fade.start('out',700)
        elif kind=='vista':
            self.focus=(1280,390)
            self.sequence=NarrativeSequence((Beat(None,1000,'world',350),
                Beat('A Câmara dos Testemunhos. A planta não mostrava o tamanho da pedra.',2300,'world'),
                Beat('Há luz entre as colunas. Alguém chegou antes.',1900,'world'),Beat(None,650,'world')))
        else:
            self.sequence=NarrativeSequence((Beat(None,600,'world'),
                Beat('AS VOZES QUE RESTARAM',2300,'black'),Beat('PARTE A CONCLUÍDA',1600,'black'),Beat(None,700,'world')))
            self.fade.start('out',600)
        self.sequence.start()
        if kind in ('title','part_a_end'):
            rows=(('CAPÍTULO II',26,218,(179,163,128)),('O PREÇO DA MEMÓRIA',46,275,(229,218,191)),
                  ('As Vozes que Restaram',24,334,(159,168,160))) if kind=='title' else (
                  ('CAPÍTULO II — PARTE A',26,220,(179,163,128)),('AS VOZES QUE RESTARAM',44,276,(229,218,191)),
                  ('CONCLUÍDA',24,332,(159,168,160)))
            self.card_images=tuple((pygame.font.Font(None,size).render(text,True,color),y) for text,size,y,color in rows)

    def choose(self,index):
        if self.phase!='choice' or not self.dialogue.choose(index): return False
        self.story.set('encosta_choice_shared',index==0); self.story.set('encosta_choice_kept',index==1)
        self.quests.notice=('Inês recebeu a folha. A referência continua registrada.' if index==0 else
                            'Você guardou a folha para comparar. Inês espera uma resposta.')
        self.quests.notice_timer=260; self.active=False; self.autosave_requested=True
        return True

    def advance(self):
        if self.phase=='departure': self.dialogue.advance()

    def finish(self):
        if not self.active or self.phase=='choice': return False
        if self.phase=='departure':
            self.dialogue.npc=None
            self.story.set('chapter2_started'); self.story.set('chapter2_departure_seen')
            add_inventory_item(self.inventory,consumable('potion'))
            self.autosave_requested=True; self._timed('title'); return False
        flag={'title':'chapter2_title_seen','vista':'threshold_vista_seen','part_a_end':'chapter2_part_a_completed'}[self.phase]
        self.story.set(flag); self.active=False; self.autosave_requested=True
        return True

    def update(self,delta_ms):
        self.elapsed_ms+=delta_ms; self.fade.update(delta_ms)
        if self.phase=='departure':
            return self.finish() if not self.dialogue.active else False
        if self.sequence is not None and self.sequence.update(delta_ms): return self.finish()
        return False

    def draw(self,canvas,render_world,font,title_font):
        from ui.narrative_overlay import draw_narrative,draw_letterbox
        if self.phase in ('departure','choice'):
            render_world(); draw_letterbox(canvas); self.dialogue.draw(canvas,font,title_font)
        elif self.phase=='title':
            if self.elapsed_ms<700:
                render_world(); self.fade.draw(canvas)
            elif self.elapsed_ms<4100:
                canvas.fill((5,7,10)); t=self.elapsed_ms-700
                alpha=round(255*min(1,t/600,max(0,(3400-t)/600)))
                for im,y in self.card_images:
                    im.set_alpha(alpha)
                    canvas.blit(im,im.get_rect(center=(canvas.width//2,y)))
            else:
                render_world(); self.black.set_alpha(max(0,round(255*(4800-self.elapsed_ms)/700))); canvas.blit(self.black,(0,0))
        elif self.phase=='part_a_end':
            if self.elapsed_ms<600:
                render_world(); self.fade.draw(canvas)
            elif self.elapsed_ms<4500:
                canvas.fill((5,7,10)); t=self.elapsed_ms-600
                alpha=round(255*min(1,t/500,max(0,(3900-t)/600)))
                for im,y in self.card_images:
                    im.set_alpha(alpha)
                    canvas.blit(im,im.get_rect(center=(canvas.width//2,y)))
            else:
                render_world(); self.fade.alpha=max(0,round(255*(5200-self.elapsed_ms)/700)); self.fade.draw(canvas)
        else: draw_narrative(canvas,self.sequence,world_renderer=render_world)


def interact(target,player,story,dialogue,quests,inventory,region):
    """Return (handled, scene, changed); existing ordinary dialogue stays intact."""
    from story.lacre import interact as dungeon_interact
    result=dungeon_interact(target,player,story,dialogue,quests,inventory,region)
    if result is not None: return result
    uid=target.uid
    if region.get('ambient_kind')=='village' and uid=='alden' and story.get('chapter1_completed') and not story.get('chapter2_departure_seen'):
        return True,Chapter2Scene('departure',player,story,dialogue,quests,inventory,region),False
    if uid in BY_ID:
        if any(e.state!='DEAD' and (e.x-player.x)**2+(e.y-player.y)**2<230**2 for e in region.get('live_enemies',())):
            quests.notice='Preciso afastar a ameaça antes de escutar o eco.'; quests.notice_timer=150
            return True,None,False
        point=BY_ID[uid]
        return True,ResonanceScene(point,player,story) if point.available(story) else None,False
    if uid.startswith('cabinet_'): return True,None,puzzle_input(uid,story,quests)
    if uid=='ines' and story.get('encosta_sealed_record_found') and not (story.get('encosta_choice_shared') or story.get('encosta_choice_kept')):
        return True,Chapter2Scene('choice',player,story,dialogue,quests,inventory,region),False
    return False,None,False


def moment_at(player,story,dialogue,quests,inventory,region):
    from story.lacre import moment
    scene=moment(player,story,dialogue,quests,inventory,region)
    if scene is not None: return scene
    kind=region.get('ambient_kind')
    if story.get('chapter2_started') and not story.get('chapter2_title_seen'):
        return Chapter2Scene('title',player,story,dialogue,quests,inventory,region)
    if kind=='threshold':
        if not story.get('threshold_vista_seen') and player.x>1140 and player.y<700:
            return Chapter2Scene('vista',player,story,dialogue,quests,inventory,region)
        if story.get('echo_threshold_seen') and not story.get('chapter2_part_a_completed'):
            return Chapter2Scene('part_a_end',player,story,dialogue,quests,inventory,region)
    return None


def validate(story,inventory_ids,region_id,error):
    if story.get('chapter2_started') and not story.get('chapter1_completed'): raise error('Save inválido: Capítulo II antes do encerramento do I.')
    dependencies={'chapter2_departure_seen':'chapter2_started','chapter2_title_seen':'chapter2_departure_seen',
        'route_entered':'chapter2_title_seen','encosta_entered':'route_entered',
        'ines_met':'encosta_entered','breno_met':'encosta_entered',
        'encosta_investigated':'encosta_entered','encosta_puzzle_step2':'encosta_puzzle_step1',
        'encosta_puzzle_solved':'encosta_puzzle_step2','encosta_sealed_record_found':'encosta_puzzle_solved',
        'encosta_choice_shared':'encosta_sealed_record_found','encosta_choice_kept':'encosta_sealed_record_found',
        'encosta_destination_found':'encosta_sealed_record_found','threshold_entered':'encosta_destination_found',
        'threshold_vista_seen':'threshold_entered','threshold_activity_seen':'threshold_entered',
        'threshold_guard_defeated':'c2_threshold_enemy_1_defeated','echo_threshold_seen':'threshold_guard_defeated',
        'chapter2_part_a_completed':'echo_threshold_seen'}
    for uid,flag in EVIDENCE.items(): dependencies[flag]='encosta_entered'
    for uid,flag in (('route_cache','route_cache_found'),('route_record','route_record_found'),('route_rest','route_rest_found')): dependencies[flag]='route_entered'
    for point in POINTS: dependencies[point.flag]=point.prerequisite
    for flag in DEFEAT_FLAGS: dependencies[flag]='threshold_entered' if 'threshold' in flag else 'route_entered'
    for flag,prerequisite in dependencies.items():
        if story.get(flag) and not story.get(prerequisite): raise error('Save inválido: progressão da Encosta fora de ordem.')
    if bool(story.get('chapter2_started')) != bool(story.get('chapter2_departure_seen')):
        raise error('Save inválido: início do capítulo sem partida.')
    if bool(story.get('encosta_investigated')) != all(story.get(f,False) for f in EVIDENCE.values()):
        raise error('Save inválido: investigação incompleta.')
    if story.get('encosta_choice_shared') and story.get('encosta_choice_kept'): raise error('Save inválido: escolhas de custódia conflitantes.')
    if story.get('encosta_destination_found') and not (story.get('encosta_choice_shared') or story.get('encosta_choice_kept')):
        raise error('Save inválido: planta sem decisão sobre o registro.')
    if story.get('encosta_puzzle_step1') and not (story.get('encosta_investigated') and all(story.get(f) for f in ('ines_met','breno_met','echo_meal_seen','echo_departure_seen','echo_orders_seen'))):
        raise error('Save inválido: fecho antes dos ecos de custódia.')
    for flag,item in (('route_record_found','route_transfer_note'),('encosta_locket_found','encosta_locket'),
                      ('encosta_sealed_record_found','encosta_sealed_record'),('encosta_destination_found','chamber_plan')):
        if bool(story.get(flag)) != (item in inventory_ids): raise error('Save inválido: documento da Encosta inconsistente.')
    if region_id in REGIONS and not story.get({**ENTER_FLAGS,'forgotten_route':'route_entered','encosta':'encosta_entered','threshold':'threshold_entered'}[region_id]):
        raise error('Save inválido: região da Encosta sem acesso registrado.')
    from story.lacre import validate as validate_dungeon
    validate_dungeon(story,inventory_ids,region_id,error)
