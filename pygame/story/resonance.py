"""Configured impressions, not recordings: one reusable E-interaction sequence."""
from dataclasses import dataclass
import math
import pygame
from story.sequence import Beat, NarrativeSequence
from story.chapter1_return import settle_player


@dataclass(frozen=True)
class ResonancePoint:
    uid: str
    region: str
    position: tuple
    prerequisite: str
    flag: str
    beats: tuple
    silhouettes: tuple = ()  # (offset x, offset y, visual role)

    def available(self, story):
        return story.get(self.prerequisite) and not story.get(self.flag)


POINTS = (
    ResonancePoint('echo_meal','encosta',(650,768),'encosta_entered','echo_meal_seen',
        (Beat(None,450,'world'),Beat('“Deixa o terceiro prato. Ela ainda vem.”',2100,'world'),
         Beat(None,650,'world'),Beat('Uma colher bate duas vezes na borda. Depois, passos.',1600,'world')),
        ((-42,-12,'civilian'),(40,-8,'civilian'))),
    ResonancePoint('echo_departure','encosta',(1220,790),'encosta_entered','echo_departure_seen',
        (Beat(None,450,'world'),Beat('“Os nomes ficam comigo. Não com a escolta.”',2200,'world'),
         Beat('“Se escrever que partiram, ninguém vai procurar.”',2000,'world'),
         Beat(None,700,'world')),((-34,-12,'civilian'),(52,0,'guard'))),
    ResonancePoint('echo_orders','encosta',(1090,360),'encosta_investigated','echo_orders_seen',
        (Beat(None,500,'world'),Beat('“Nem azul nem vermelho. Esse rol não sai daqui.”',2300,'world'),
         Beat(None,500,'black'),Beat('“A autorização é R-17. A custódia não é.”',2000,'world'),
         Beat('Uma mão cobre o selo. Falta o começo da conversa.',1700,'world')),
        ((-48,-8,'red'),(46,4,'blue'))),
    ResonancePoint('echo_threshold','threshold',(1450,630),'threshold_guard_defeated','echo_threshold_seen',
        (Beat(None,700,'world'),Beat('Minha voz: “Quando a porta se fechar, não restará caminho de volta.”',2500,'world'),
         Beat(None,800,'black'),Beat('Outra voz: “Você sabe o que isso vai custar?”',2000,'black'),
         Beat(None,650,'black'),Beat('Eu estive aqui. Não sei o que deixei do outro lado.',2200,'world')),
        ((-44,-4,'red'),(42,-2,'civilian'))),
)
POINTS += (
    ResonancePoint('l_echo_vestibule','inscription_vestibule',(1024,690),'lacre_inscription_vestibule_entered','lacre_vestige_seen',
        (Beat(None,450,'world'),Beat('Uma figura pousa a tigela, acende a lamparina e registra o nome. Os três fechos cedem nessa ordem.',2600,'world'),
         Beat('No presente, as inscrições gastas ainda guardam esse rito: tigela, lamparina, nome.',2000,'world')),((-35,-5,'guard'),)),
    ResonancePoint('l_echo_door','echo_gallery',(650,735),'lacre_echo_gallery_entered','lacre_gallery_door_seen',
        (Beat(None,450,'world'),Beat('“Primeiro, deixe passar o depositante.” A figura atravessa o arco antes que o mecanismo se mova.',2500,'world'),
         Beat('O símbolo da passagem fica iluminado. É o primeiro gesto.',1600,'world')),((-22,-7,'civilian'),)),
    ResonancePoint('l_echo_hand','echo_gallery',(1024,700),'lacre_echo_gallery_entered','lacre_gallery_hand_seen',
        (Beat(None,450,'world'),Beat('“Agora, assente a mão. Ele precisa estar do outro lado.” Uma palma pressiona a placa.',2500,'world'),
         Beat('O acionamento vem depois da passagem e antes do lacre.',1700,'world')),((30,-8,'guard'),)),
    ResonancePoint('l_echo_seal','echo_gallery',(1390,735),'lacre_echo_gallery_entered','lacre_gallery_seal_seen',
        (Beat(None,450,'world'),Beat('“Só então feche a custódia.” Os três arcos se unem por um instante, depois tornam a separar-se.',2500,'world'),
         Beat('Passagem, acionamento, custódia. O padrão permite abrir a porta atual; não mudar o passado.',1900,'world')),((-20,-10,'guard'),)),
    ResonancePoint('l_echo_secret','forbidden_archive',(590,810),'lacre_forbidden_archive_entered','lacre_secret_seen',
        (Beat(None,500,'world'),Beat('Uma mão puxa a fita do rodapé antes de recolher um caderno. O painel deixa uma linha clara na pedra.',2100,'world'),),((28,0,'civilian'),)),
    ResonancePoint('l_echo_central','seal_core',(1024,730),'lacre_records_ready','lacre_memory_seen',
        (Beat(None,800,'world',400),Beat('Outra voz: “O lacre não distingue culpa de nomes. Vai guardar o que você pedir.”',2600,'world'),
         Beat('Minha voz: “O rol fica separado. Nem uma escolta nem a outra.”',2300,'world'),Beat(None,750,'world'),
         Beat('Outra voz: “Você pode não saber como voltar a ele.”',2100,'black'),Beat('Minha voz: “Eu li o limite. Faça o primeiro lacre.”',2300,'world'),
         Beat(None,900,'black'),Beat('A luz muda antes do resultado. A folha de quinta vigília não aparece neste vestígio.',2300,'world'),
         Beat(None,850,'world'),Beat('Eu autorizei uma parte. A outra folha veio depois. Não sei quem a autorizou.',2300,'world')),
        ((-75,-20,'red'),(75,-20,'civilian'))),
)
BY_ID = {point.uid:point for point in POINTS}


class ResonanceScene:
    def __init__(self, point, player, story):
        self.point,self.player,self.story=point,player,story
        self.phase='resonance'; self.focus=(player.x,player.y)
        self.active=point.available(story); self.elapsed_ms=0
        self.sequence=NarrativeSequence(point.beats); self.sequence.start()
        settle_player(player)
        # Prepared once per event; no per-frame sprite loading or silhouette allocation.
        from core.assets import load
        from ui.character_art import character_sheet, prepared_frames
        self.ghosts=[]
        for x,y,role in point.silhouettes:
            look={'civilian':'civilian_woman','guard':'civilian_worker',
                  'red':'red_soldier_0','blue':'blue_soldier_0'}[role]
            im=prepared_frames(character_sheet(load,look,'idle'),64)[0][0].copy()
            im.fill((154,150,128,255),special_flags=pygame.BLEND_RGBA_MULT)
            self.ghosts.append((x,y,im))
        self.veil=pygame.Surface((1024,576),pygame.SRCALPHA)
        self.veil.fill((43,42,38,105))
        self.marks=[]
        if point.uid.startswith('l_echo_'):
            from world.regions.lacre_art import prop
            kinds={'l_echo_vestibule':('bowl','lamp','name'),'l_echo_door':('door',),
                'l_echo_hand':('hand',),'l_echo_seal':('seal',),'l_echo_central':('record','seal')} .get(point.uid,())
            for i,kind in enumerate(kinds):
                im=pygame.transform.scale_by(prop(kind,True),.5)
                self.marks.append(((i-(len(kinds)-1)/2)*76,im))

    def finish(self):
        if not self.active: return False
        self.story.set(self.point.flag); self.active=False
        return True

    def update(self, delta_ms):
        self.elapsed_ms+=delta_ms
        return self.finish() if self.active and self.sequence.update(delta_ms) else False

    def draw_overlay(self, canvas, camera):
        canvas.blit(self.veil,(0,0))
        alpha=round(95*min(1,self.elapsed_ms/450)*(.82+.18*math.sin(self.elapsed_ms/450)))
        for x,y,im in self.ghosts:
            im.set_alpha(alpha)
            canvas.blit(im,(round(self.point.position[0]+x-32-camera[0]),
                            round(self.point.position[1]+y-56-camera[1])))
        px,py=self.point.position[0]-camera[0],self.point.position[1]-camera[1]
        for i,(offset,im) in enumerate(self.marks):
            if self.elapsed_ms>550+i*650:
                im.set_alpha(min(160,round((self.elapsed_ms-550-i*650)/3)))
                canvas.blit(im,(round(px+offset-im.width/2),round(py-im.height-16)))
        for i in range(5):
            t=self.elapsed_ms/1400+i*1.2
            x=round(px+math.sin(t)*30); y=round(py-12-(t%2)*18)
            pygame.draw.line(canvas,(177,171,139),(x,y),(x+2,y-1),1)
