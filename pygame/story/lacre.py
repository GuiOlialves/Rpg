"""Chapter II/B progression using the existing interaction, scene, inventory and save contracts."""
import pygame
from story.lacre_content import REGIONS,ENTER_FLAGS,FLAGS,DEFEATS,DOCUMENTS,ITEM_FLAGS,PUZZLES
from story.arrival_scene import ScriptedDialogue
from story.chapter1_return import settle_player
from story.sequence import Beat,NarrativeSequence
from systems.inventory import add_inventory_item
from systems.items import quest_item,consumable
from systems.equipment import item
from world.regions import lacre_art as art
import environment as env

def objective(s):
    if s.get('chapter2_completed'):return 'Investigue a Mesa de Revisão do Mosteiro da Vigília.'
    if s.get('lacre_return_seen'):return 'Examine a matriz no banco tranquilo, a leste do posto.'
    if s.get('lacre_reward_given'):return 'Volte a Inês pela passagem de manutenção.'
    if s.get('lacre_memory_seen'):return 'Decida quem poderá consultar a cópia dos registros.'
    if s.get('lacre_custodian_defeated'):return 'Coteje as duas folhas no núcleo e escute seu vestígio.'
    if s.get('lacre_custodian_talk_seen'):return 'Supere o Custódio; rompa as âncoras quando o núcleo despertar.'
    if s.get('lacre_vigia_defeated'):return 'Descanse e alcance o Núcleo do Lacre.'
    if s.get('lacre_archive_open'):return 'Atravesse a Câmara dos Guardiões e encontre o acesso ao núcleo.'
    if s.get('lacre_gallery_open'):return 'Coteje os três registros principais no Arquivo Interditado.'
    if s.get('lacre_vestibule_open'):return 'Leia os três vestígios da galeria e opere seus mecanismos.'
    return 'Observe o mecanismo do vestíbulo e reproduza o rito de abertura.'

def apply_state(r,s):
    kind=r.get('ambient_kind')
    if kind=='threshold':
        for obj in r['interactables']:
            if obj.uid=='chamber_entrance':obj.transition_to=REGIONS[0];obj.transition_on_interact=True
    if kind=='encosta' and s.get('lacre_reward_given'):
        from entities.interactable import Interactable
        if not any(o.uid=='lacre_closing_bench' for o in r['interactables']):
            r['interactables'].append(Interactable('lacre_closing_bench','Protagonista',(1650,810),art.prop('relic'),(),prompt='[E] Examinar a matriz em silêncio'))
        for npc in r['npcs']:
            if npc.uid=='ines' and s.get('lacre_return_seen'):
                npc.dialogues={'default':('A cópia está guardada. Só abrirei com você.' if s.get('lacre_choice_shared') else 'Se ainda não pode mostrar, não vou arrancar a folha da sua mão.',
                    'Lídia deixou o pingente para voltar por ele. Isso continua contando, mesmo depois dos registros.')}
    if kind not in REGIONS:return
    index=REGIONS.index(kind);r['story_phase']='chapter2_b'
    unlocked=(s.get('lacre_vestibule_open'),s.get('lacre_gallery_open'),s.get('lacre_archive_open'),s.get('lacre_vigia_defeated'),True)[index]
    r['obstacles']=[o for o in r['obstacles'] if o!=r['door_box']]
    r['scenery']=[o for o in r['scenery'] if o is not r['next_door']]
    r['next_door']=env.anchored(art.door(unlocked),(1024,316));r['scenery'].append(r['next_door'])
    if not unlocked:r['obstacles'].append(r['door_box'])
    from story.resonance import BY_ID
    for obj in r['interactables']:
        uid=obj.uid
        if uid in BY_ID:
            obj.enabled=BY_ID[uid].available(s)
            # Retain a concise note instead of forcing the player to replay a scene.
            if s.get(BY_ID[uid].flag):
                obj.enabled=True;obj.resonance=False
                obj.dialogues={'default':tuple(b.text for b in BY_ID[uid].beats if b.text)}
        elif uid=='lacre_next':obj.enabled=unlocked
        elif uid.startswith(('v_','g_')):
            puzzle_name='vestibule' if uid[0]=='v' else 'gallery'
            order,a,b,done,_=PUZZLES[puzzle_name]
            lit=s.get(done) or (uid==order[0] and s.get(a)) or (uid==order[1] and s.get(b))
            obj.image=art.prop({'v_bowl':'bowl','v_lamp':'lamp','v_name':'name','g_door':'door','g_hand':'hand','g_seal':'seal'}[uid],lit)
        elif uid in ('lacre_cache','lacre_lore'):obj.enabled=s.get('lacre_secret_open') and not s.get('lacre_cache_found' if uid=='lacre_cache' else 'lacre_lore_found')
        elif uid=='lacre_hidden':obj.enabled=not s.get('lacre_secret_open')
        elif uid=='lacre_shortcut':obj.enabled=s.get('lacre_shortcut_open')
        elif uid=='lacre_checkpoint':obj.enabled=s.get('lacre_vigia_defeated')
        elif uid in ('lacre_first','lacre_second'):obj.enabled=s.get('lacre_aftermath_seen')
        elif uid=='lacre_decision':obj.enabled=s.get('lacre_memory_seen') and not s.get('lacre_reward_given')
        elif uid=='lacre_escape':obj.enabled=s.get('lacre_reward_given')
        elif uid.startswith('anchor_'):
            side=uid.split('_')[1];broken=s.get('lacre_anchor_'+side+'_broken')
            obj.enabled=s.get('lacre_boss_wounded') and not s.get('lacre_custodian_defeated') and not broken
            obj.image=art.prop('anchor',s.get('lacre_boss_wounded') and not broken)
    falling=any(e.kind=='custodian' and e.state=='DEAD' and e.dead_timer>0 for e in r.get('live_enemies',()))
    if kind=='seal_core' and s.get('lacre_custodian_defeated') and not r.get('survivor_added') and not falling:
        from core.assets import load
        from ui.character_art import prepared_frames
        im=prepared_frames(load('assets/vale_characters/custodian_death.png'),160,cell=80,height=64)[0][-1]
        r['scenery'].append(env.Scenery(im,(1040,548),640));r['survivor_added']=True
    r['boss_battle_active']=kind=='seal_core' and s.get('lacre_custodian_talk_seen') and not s.get('lacre_custodian_defeated')
    r['dungeon_checkpoint']=(1024,900) if kind=='seal_core' else (1024,940)

def spawn_pending(r,s,spawn,actors=None):
    actors=spawn(r) if actors is None else actors
    result=[]
    for actor in actors:
        if s.get(f'c2_{r["ambient_kind"]}_enemy_{actor.chapter2_id}_defeated'):continue
        actor.story=s;actor.region=r
        if actor.kind=='custodian' and s.get('lacre_boss_wounded') and actor.phase==1:
            actor.phase=2;actor.hp=actor.max_hp//2
        result.append(actor)
    return result

def evidence(target,s,inventory,player,quests,r):
    uid=target.uid;changed=False
    if uid in DOCUMENTS:
        flag=DOCUMENTS[uid][1]
        if not s.get(flag):s.set(flag);add_inventory_item(inventory,quest_item(uid));changed=True
        if all(s.get('lacre_'+f+'_found') for f in ('purpose','military','identity')):s.set('lacre_archive_open')
        if s.get('lacre_first_found') and s.get('lacre_second_found'):s.set('lacre_records_ready')
    if uid=='lacre_cache' and not s.get('lacre_cache_found'):
        s.set('lacre_cache_found');add_inventory_item(inventory,consumable('potion',2));add_inventory_item(inventory,consumable('ether'));changed=True
    if uid=='lacre_service' and not s.get('lacre_shortcut_open'):s.set('lacre_shortcut_open');changed=True
    if uid=='lacre_checkpoint' and s.get('lacre_vigia_defeated'):
        s.set('lacre_checkpoint_found');player.hp=player.max_hp;player.sp=player.max_sp;changed=True
        quests.notice='Recuperado. O checkpoint do núcleo está preparado.';quests.notice_timer=180
    apply_state(r,s);return changed

def puzzle(uid,s,quests,r):
    name='vestibule' if uid.startswith('v_') else 'gallery';order,a,b,done,requirements=PUZZLES[name]
    if s.get(done):quests.notice='A passagem permanece aberta.'
    elif not all(s.get(f) for f in requirements):quests.notice='O encaixe não responde. Preciso ler os vestígios do mecanismo.'
    else:
        step=2 if s.get(b) else 1 if s.get(a) else 0
        if uid!=order[step]:
            s.set(a,False);s.set(b,False);quests.notice='Os fechos voltaram. Os vestígios continuam legíveis nos três marcos.'
        elif step==0:s.set(a);quests.notice='Primeiro fecho assentado.'
        elif step==1:s.set(b);quests.notice='Segundo fecho assentado.'
        else:s.set(done);quests.notice='O peso saiu do batente. A porta está aberta.'
    quests.notice_timer=210;apply_state(r,s);return True

class LacreScene:
    def __init__(self,kind,player,s,dialogue,quests,inventory,r):
        self.phase='b_'+kind;self.kind=kind;self.player=player;self.story=s;self.dialogue=dialogue;self.quests=quests;self.inventory=inventory;self.region=r
        self.active=True;self.autosave_requested=False;self.elapsed_ms=0;self.focus=(player.x,player.y);self.sequence=None
        if kind=='core_vista':self.focus=(1024,490)
        elif kind in ('custodian_talk','aftermath'):self.focus=(1024,640)
        if kind=='final':
            self.card=tuple((pygame.font.Font(None,size).render(text,True,color),y) for text,size,y,color in (
                ('CAPÍTULO II CONCLUÍDO',30,228,(176,162,129)),('O PREÇO DA MEMÓRIA',46,290,(229,218,191))))
        settle_player(player)
        lines={
         'custodian_talk':(('Iriel','Essa impressão... é a do depositante R-17.'),('Protagonista','Eu fiz o pedido?'),
             ('Iriel','O original está no núcleo. Não sei o que você lembra dele.'),('Protagonista','Então deixe que eu leia.'),
             ('Iriel','Há nomes sob esse lacre. Já vi uma escolta tomar um depoimento por uma lista de alvos.'),
             ('Protagonista','Não vou levar os nomes. Quero a autorização que leva minha marca.'),('Iriel','E eu não consigo separar uma coisa da outra por você.')),
         'aftermath':(('Iriel','A ligação cedeu. Ainda posso apontar a folha; não posso impedir sua mão.'),
             ('Protagonista','Fique. Não vim tirar mais uma pessoa daqui.'),('Iriel','Leia o papel de baixo também. Ele não estava ali quando recebi o primeiro.')),
         'return':(('Inês','Encontrou o caminho dos nomes?'),('Protagonista','Encontrei uma autorização minha. E uma revisão que veio depois.'),
             ('Inês','Isso explica quem saiu do posto?'),('Protagonista','Ainda não. Mas agora sei que não é uma folha só.'),
             ('Inês','Você me mostrou o termo. Vou guardar a cópia sem separar as margens.' if s.get('encosta_choice_shared') else 'Você guardou meu termo. Agora entende por que eu queria ver as duas margens.'),
             ('Protagonista','Esta cópia fica com você. Sem os nomes dos acolhidos.' if s.get('lacre_choice_shared') else 'Vou cotejar os selos antes de mostrar. Não quero esconder sua parte da história.'),
             ('Inês','Mara escreveu sobre a carroça. Alguém conseguiu ficar para contar.' if s.get('namar_choice_protect') else 'Breno leu a notícia da carga perdida. Um rol não carrega as pessoas que ficaram para trás.')),
        }
        if kind=='choice':
            actor=ScriptedDialogue((('Protagonista','O lacre guarda testemunhos de pessoas vivas. Posso separar a prova dos nomes.'),));actor.x,actor.y=player.x,player.y
            dialogue.open_choices(actor,(('Preservar os registros.', 'Guardar a cópia protegida até cotejar a matriz da revisão.'),('Compartilhar uma cópia com Inês.', 'Entregar apenas as autorizações; os nomes permanecem lacrados.')))
        elif kind in lines:
            actor=ScriptedDialogue(lines[kind]);actor.x,actor.y=player.x,player.y;dialogue.open(actor)
        else:
            beats=(Beat(None,850,'world'),Beat('Os fechos convergem para um único registro. O mecanismo ainda respira.',2300,'world'),Beat(None,600,'world')) if kind=='core_vista' else (
                Beat(None,1100,'world',500),Beat('Eu pedi que guardassem uma parte.',2100,'world'),Beat(None,750,'world'),
                Beat('A outra folha foi posta depois. Preciso encontrar sua matriz.',2300,'world'),Beat(None,800,'world'),
                Beat('CAPÍTULO II CONCLUÍDO',2200,'black',700),Beat('O PREÇO DA MEMÓRIA',2200,'black'),Beat(None,650,'world',500))
            if kind=='final':
                reference=('Inês tem uma cópia sem os nomes. Agora há outra pessoa que pode cotejar minha versão.' if s.get('lacre_choice_shared') else
                           'A cópia continua comigo. Guardar não pode se tornar outra maneira de sumir com alguém.')
                beats=beats[:5]+(Beat(reference,2400,'world'),)+beats[5:]
            self.sequence=NarrativeSequence(beats);self.sequence.start()
    def advance(self):
        if self.sequence is None and self.kind!='choice':self.dialogue.advance()
    def choose(self,index):
        if not self.active or self.kind!='choice' or self.story.get('lacre_reward_given') or not self.dialogue.choose(index):return False
        self.story.set('lacre_choice_preserved',index==0);self.story.set('lacre_choice_shared',index==1)
        if not self.story.get('lacre_reward_given'):
            add_inventory_item(self.inventory,item('custody_medallion'));add_inventory_item(self.inventory,quest_item('lacre_lead'))
            self.story.set('lacre_reward_given');self.story.set('lacre_lead_found')
        self.quests.notice='Medalhão de Custódia e guia de cotejo recebidos. A manutenção está aberta.';self.quests.notice_timer=240
        self.active=False;self.autosave_requested=True;apply_state(self.region,self.story);return True
    def finish(self):
        if not self.active or self.kind=='choice':return False
        flag={'core_vista':'lacre_core_vista_seen','custodian_talk':'lacre_custodian_talk_seen','aftermath':'lacre_aftermath_seen','return':'lacre_return_seen','final':'lacre_final_seen'}[self.kind]
        self.dialogue.npc=None;self.story.set(flag)
        if self.kind=='final':self.story.set('chapter2_completed')
        self.active=False;self.autosave_requested=True;apply_state(self.region,self.story);return True
    def update(self,delta_ms):
        self.elapsed_ms+=delta_ms
        return self.finish() if ((self.sequence is not None and self.sequence.update(delta_ms)) or (self.sequence is None and self.kind!='choice' and not self.dialogue.active)) else False
    def draw(self,canvas,render_world,font,title_font):
        from ui.narrative_overlay import draw_narrative,draw_letterbox
        if self.kind=='final' and self.sequence.current and self.sequence.current.background=='black':
            canvas.fill((5,7,10));elapsed=self.sequence.current.duration_ms-self.sequence.remaining_ms
            alpha=round(255*min(1,elapsed/450,self.sequence.remaining_ms/450))
            for image,y in self.card:image.set_alpha(alpha);canvas.blit(image,image.get_rect(center=(canvas.width//2,y)))
            self.sequence.fade.draw(canvas)
        elif self.sequence is not None:draw_narrative(canvas,self.sequence,world_renderer=render_world,font=font)
        else:render_world();draw_letterbox(canvas);self.dialogue.draw(canvas,font,title_font)

def interact(target,p,s,d,q,inv,r):
    uid=target.uid;kind=r.get('ambient_kind')
    if uid.startswith(('v_','g_')):return True,None,puzzle(uid,s,q,r)
    if uid=='lacre_hidden':
        s.set('lacre_secret_open');apply_state(r,s);q.notice='O painel soltou. Há um compartimento atrás da fita.';q.notice_timer=180;return True,None,True
    if uid.startswith('anchor_'):
        if target.enabled:s.set('lacre_anchor_'+uid.split('_')[1]+'_broken');apply_state(r,s);q.notice='Conexão rompida. A proteção do Custódio enfraqueceu.';q.notice_timer=120
        return True,None,True
    if uid=='lacre_decision':return True,LacreScene('choice',p,s,d,q,inv,r),False
    if uid=='ines' and s.get('lacre_reward_given') and not s.get('lacre_return_seen'):return True,LacreScene('return',p,s,d,q,inv,r),False
    if uid=='lacre_closing_bench' and s.get('lacre_return_seen') and not s.get('chapter2_completed'):return True,LacreScene('final',p,s,d,q,inv,r),False
    from story.resonance import BY_ID
    if uid in BY_ID and s.get(BY_ID[uid].flag):return False,None,False
    return None

def moment(p,s,d,q,inv,r):
    if r.get('ambient_kind')!='seal_core':return None
    if not s.get('lacre_core_vista_seen') and p.y<750:return LacreScene('core_vista',p,s,d,q,inv,r)
    if s.get('lacre_core_vista_seen') and not s.get('lacre_custodian_talk_seen') and p.y<680:return LacreScene('custodian_talk',p,s,d,q,inv,r)
    if s.get('lacre_custodian_defeated') and not s.get('lacre_aftermath_seen'):
        if any(e.kind=='custodian' and e.dead_timer>0 for e in r.get('live_enemies',())):return None
        apply_state(r,s)
        return LacreScene('aftermath',p,s,d,q,inv,r)
    return None

def record_defeats(s,defeats,r,q):
    if s.get('c2_guardian_chamber_enemy_0_defeated'):s.set('lacre_vigia_defeated')
    if s.get('c2_seal_core_enemy_0_defeated'):s.set('lacre_custodian_defeated')
    if defeats:apply_state(r,s)

def validate(s,ids,region,error):
    def require(flag,*parents):
        if s.get(flag) and not all(s.get(p) for p in parents):raise error('Save inválido: progressão do lacre fora de ordem: '+flag)
    require('chapter2_part_b_started','chapter2_part_a_completed')
    previous='chapter2_part_b_started'
    for r in REGIONS:require(ENTER_FLAGS[r],previous);previous=ENTER_FLAGS[r]
    for r,flag in zip(REGIONS[1:],('lacre_vestibule_open','lacre_gallery_open','lacre_archive_open','lacre_vigia_defeated')):
        require(ENTER_FLAGS[r],flag)
    for name,(order,a,b,done,requirements) in PUZZLES.items():
        require(a,*requirements);require(b,a);require(done,b)
    for point,regionflag in (('vestige',ENTER_FLAGS[REGIONS[0]]),('gallery_door',ENTER_FLAGS[REGIONS[1]]),('gallery_hand',ENTER_FLAGS[REGIONS[1]]),('gallery_seal',ENTER_FLAGS[REGIONS[1]])):
        require('lacre_'+point+'_seen',regionflag)
    for doc,(name,flag,lines) in DOCUMENTS.items():
        require(flag,'lacre_aftermath_seen' if doc in ('lacre_first','lacre_second') else ENTER_FLAGS['forbidden_archive'])
        if bool(s.get(flag))!=(doc in ids):raise error('Save inválido: registro do lacre inconsistente.')
    require('lacre_archive_open','lacre_purpose_found','lacre_military_found','lacre_identity_found')
    require('lacre_secret_seen',ENTER_FLAGS['forbidden_archive'])
    require('lacre_secret_open',ENTER_FLAGS['forbidden_archive'])
    require('lacre_cache_found','lacre_secret_open');require('lacre_lore_found','lacre_secret_open')
    require('lacre_shortcut_open',ENTER_FLAGS['forbidden_archive']);require('lacre_checkpoint_found','lacre_vigia_defeated')
    require('lacre_vigia_defeated','c2_guardian_chamber_enemy_0_defeated')
    require('lacre_core_vista_seen',ENTER_FLAGS['seal_core']);require('lacre_custodian_talk_seen','lacre_core_vista_seen')
    require('lacre_boss_wounded','lacre_custodian_talk_seen','lacre_boss_phase2_seen');require('lacre_boss_phase2_seen','lacre_custodian_talk_seen')
    for side in ('left','right'):require('lacre_anchor_'+side+'_broken','lacre_boss_phase2_seen')
    require('lacre_custodian_defeated','c2_seal_core_enemy_0_defeated');require('lacre_aftermath_seen','lacre_custodian_defeated')
    require('c2_seal_core_enemy_0_defeated','lacre_custodian_talk_seen','lacre_boss_phase2_seen')
    require('lacre_records_ready','lacre_first_found','lacre_second_found');require('lacre_memory_seen','lacre_records_ready')
    require('lacre_choice_preserved','lacre_memory_seen');require('lacre_choice_shared','lacre_memory_seen')
    if s.get('lacre_choice_shared') and s.get('lacre_choice_preserved'):raise error('Save inválido: duas escolhas de custódia.')
    require('lacre_reward_given','lacre_memory_seen')
    if s.get('lacre_reward_given') and not (s.get('lacre_choice_preserved') or s.get('lacre_choice_shared')):raise error('Save inválido: recompensa sem escolha.')
    if bool(s.get('lacre_reward_given'))!=('custody_medallion' in ids):raise error('Save inválido: medalhão de custódia inconsistente.')
    if bool(s.get('lacre_lead_found'))!=('lacre_lead' in ids):raise error('Save inválido: guia de cotejo inconsistente.')
    require('lacre_lead_found','lacre_reward_given');require('lacre_return_seen','lacre_reward_given');require('lacre_final_seen','lacre_return_seen');require('chapter2_completed','lacre_final_seen')
    for flag in DEFEATS:require(flag,ENTER_FLAGS[next(r for r in REGIONS if flag.startswith('c2_'+r+'_'))])
    if region in REGIONS and not s.get(ENTER_FLAGS[region]):raise error('Save inválido: setor sem acesso registrado.')
