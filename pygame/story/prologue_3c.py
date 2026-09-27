"""The promise, escape and closing card for the prologue (3C)."""
import math
import random
import pygame
from entities.npc import NPC
from story.arrival_scene import ScriptedDialogue, Silhouette
from story.sequence import Beat, NarrativeSequence

OPENING = (
    ("Protagonista", "Quem sou eu?"),
    ("Oficial Vermelho", "Essa é mesmo a primeira coisa que quer saber?"),
    ("Protagonista", "Responda."),
    ("Oficial Vermelho", "Então conseguiram."),
    ("Protagonista", "Conseguiram o quê?"),
    ("Oficial Vermelho", "Fazer você acreditar que não existe nada antes desta manhã."),
    ("Protagonista", "As cinco letras."),
    ("Protagonista", "Quem é?"),
    ("Oficial Vermelho", "Quer saber quem era?"),
    ("Oficial Vermelho", "Comece perguntando por que homens como aqueles seguiam você."),
)
MEMORY = (
    ("Silhueta", "Quando isso acabar..."),
    ("Silhueta", "Você promete?"),
    ("Protagonista do passado", "Prometo."),
    ("Silhueta", "Mesmo se esquecer?"),
    ("Protagonista do passado", "Como eu esqueceria você?"),
)
AFTER_MEMORY = (
    ("Protagonista", "ESPERA!"),
    ("Protagonista", "Quem é ela?!"),
    ("Oficial Vermelho", "Quer respostas?"),
    ("Oficial Vermelho", "Venha nos encontrar."),
    ("Protagonista", "ONDE?!"),
    ("Protagonista", "Quem é █████?"),
    ("Oficial Vermelho", "Você realmente quer lembrar?"),
    ("Protagonista", "Sim."),
    ("Oficial Vermelho", "Então descubra primeiro..."),
    ("Oficial Vermelho", "...por que quis esquecer."),
)
EPILOGUE = (
    ("Protagonista", "Quem era você?"),
    ("Protagonista", "..."),
    ("Protagonista", "Quem era eu?"),
)


class _PastProtagonist:
    has_embedded_shadow = True
    def __init__(self, player):
        self.player = player
        self.x, self.y = player.x + 17, player.y + 3
        self.depth = self.y
    def draw(self, canvas, camera, player=None):
        layer = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
        self.player.draw(layer, camera)
        layer.fill((150, 44, 47, 255), special_flags=pygame.BLEND_RGBA_MULT)
        canvas.blit(layer, (0, 0))


class _PlacedObject:
    has_embedded_shadow = True
    def __init__(self, image, x, y):
        self.image, self.x, self.y, self.depth = image, x, y, y
    def draw(self, canvas, camera, player=None):
        canvas.blit(self.image, (round(self.x-camera[0]), round(self.y-camera[1])))


class Prologue3CScene:
    """Atomic F4 skip, then a persistent end card rather than post-story play."""
    def __init__(self, player, story, region, dialogue, load):
        self.player, self.story, self.region = player, story, region
        self.dialogue, self.load = dialogue, load
        self.active, self.phase = True, "opening"
        self.sequence = None
        self.sequence_action = None
        self.elapsed_ms = 0
        self.index = -1
        self.actor = None
        from world.regions.home import build as build_home
        pendant = next(obj.image for obj in build_home()["investigation_interactables"]
                       if obj.uid == "broken_pendant")
        self.pendant = pygame.transform.scale(pendant, (20, 28))
        self.pendant_visible = False
        self.silhouette = Silhouette(load("assets/npc/civilian_seller.png"))
        self.past_player = _PastProtagonist(player)
        sheet = load("sprites_meu/Tiny Swords (Free Pack)/Tiny Swords (Free Pack)/Units/Red Units/Warrior/Warrior_Idle.png")
        offsets = ((-150,-34),(-96,-42),(94,-42),(151,-34),(-160,40),(-104,48),(108,48),(164,38))
        self.memory_soldiers = []
        for i,(dx,dy) in enumerate(offsets):
            actor=NPC(f"promise_memory_soldier_{i}","Soldado Vermelho",
                      (player.x+dx,player.y+dy),{},sheet,frame_size=192,draw_size=72)
            actor.enabled=False
            actor.facing=2 if dx<0 else 1
            self.memory_soldiers.append(actor)
        old=region.get("red_officer_actor")
        if old in region.get("scenery",[]): region["scenery"].remove(old)
        factory=region.get("red_officer_factory")
        self.officer=(None if story.get("red_officer_escaped")
                      else factory() if factory else old)
        if self.officer is not None:
            self.officer.running=False
            self.officer.facing=2
        region["red_officer_actor"]=self.officer
        self.object_start=(self.officer.x,self.officer.y-16) if self.officer else (player.x,player.y)
        self.object_target=(player.x+24,player.y+1)
        self.object_x,self.object_y=self.object_start
        self.autosave_requested=False
        self.player.attack_timer=self.player.dash_timer=self.player.dash_iframes=0
        self.player.invulnerability_timer=0
        if story.get("prologue_completed"):
            self.active=False
        elif story.get("red_officer_escaped"):
            self.officer=None
            self.phase="epilogue_looks"
            self.elapsed_ms=0
        elif story.get("red_officer_memory_seen"):
            self.officer.x=player.x+150
            self.officer.y=player.y-4
            self.officer.running=True
            self.index=0
            self._dialogue((AFTER_MEMORY[0],),"after_memory")
        else:
            self.actor=ScriptedDialogue(OPENING)
            self.dialogue.open(self.actor)

    def _dialogue(self, lines, phase):
        self.phase=phase
        self.actor=ScriptedDialogue(lines)
        self.dialogue.open(self.actor)

    def _pause(self, duration, phase, action, text=None, fade=None):
        self.phase=phase
        self.sequence_action=action
        self.sequence=NarrativeSequence((Beat(text,duration,background="world"),))
        if fade: self.sequence.fade.start(fade,duration)
        self.sequence.start()

    def _after_line(self):
        i=self.index
        if i in (0,1):
            self.officer.running=True
            self._pause(420 if i==0 else 300,"after_pause","next_after")
        elif i==4:
            self._pause(340,"after_pause","next_after")
        elif i==5:
            self.officer.running=False
            self.officer.facing=1
            self._pause(850,"after_pause","next_after","█████")
        elif i==8:
            self._pause(430,"after_pause","next_after")
        elif i==9:
            self._pause(280,"after_pause","flee")
        else:
            self.index+=1
            self._dialogue((AFTER_MEMORY[self.index],),"after_memory")

    def advance(self):
        if not self.active or self.sequence is not None or not self.dialogue.active:
            return False
        closed=self.dialogue.advance()
        if closed is not self.actor: return False
        if self.phase=="opening":
            self.elapsed_ms=0
            self._pause(520,"throw","memory_transition",fade="out")
        elif self.phase=="memory":
            self.index+=1
            if self.index<len(MEMORY):
                if self.index==1: self.pendant_visible=True
                self._dialogue((MEMORY[self.index],),"memory")
            else:
                self._pause(520,"memory_end","after_memory","*****","out")
        elif self.phase=="after_memory":
            self._after_line()
        elif self.phase=="epilogue":
            if self.index==0:
                self.pendant_visible=True
                self.index=1
                self._pause(1050,"epilogue_pause","epilogue_last","...")
            elif self.index==2:
                self._pause(1600,"ending","complete",fade="out")
        return False

    @property
    def world_actors(self):
        if not self.active: return ()
        if self.phase=="memory":
            self.silhouette.x,self.silhouette.y=self.player.x-48,self.player.y+2
            self.past_player.x,self.past_player.y=self.player.x+20,self.player.y+2
            actors=list(self.memory_soldiers)+[self.past_player,self.silhouette]
            if self.pendant_visible:
                actors.append(_PlacedObject(self.pendant,self.player.x-8,self.player.y-28))
            return tuple(actors)
        actors=[]
        if self.officer is not None and self.phase not in {"epilogue","epilogue_looks","ending"}: actors.append(self.officer)
        if self.phase=="throw": actors.append(_PlacedObject(self.pendant,self.object_x,self.object_y))
        if self.phase=="epilogue" and self.pendant_visible:
            actors.append(_PlacedObject(self.pendant,self.player.x+8,self.player.y-28))
        return tuple(actors)

    def update(self,delta_ms):
        if not self.active:return False
        delta_ms=max(0,int(delta_ms))
        if self.phase=="throw":
            self.elapsed_ms+=delta_ms
            t=min(1,self.elapsed_ms/520)
            self.object_x=self.object_start[0]+(self.object_target[0]-self.object_start[0])*t
            self.object_y=self.object_start[1]+(self.object_target[1]-self.object_start[1])*t-36*math.sin(t*math.pi)
        if self.officer is not None and self.phase=="memory":
            self.officer.x+=delta_ms*.045
            self.officer.y-=delta_ms*.008
            self.officer.anim_tick+=max(1,round(delta_ms/(1000/60)))
        if self.phase=="after_memory" and self.officer is not None and self.officer.running:
            self.officer.x+=delta_ms*.085
            self.officer.y-=delta_ms*.018
            self.officer.anim_tick+=max(1,round(delta_ms/(1000/60)))
        if self.phase=="flee":
            self.elapsed_ms+=delta_ms
            if self.officer is not None:
                self.officer.x+=delta_ms*.14
                self.officer.y-=delta_ms*.035
                self.officer.anim_tick+=max(1,round(delta_ms/(1000/60)))
            if self.elapsed_ms>=2200:
                self.officer.running=False
                self._escape()
                self.autosave_requested=True
                self.phase="epilogue_looks"
                self.elapsed_ms=0
        elif self.phase=="epilogue_looks":
            self.elapsed_ms+=delta_ms
            self.player.facing=(1,3,2)[min(2,self.elapsed_ms//600)]
            if self.elapsed_ms>=1800:
                self.index=0
                self.pendant_visible=True
                self._dialogue((EPILOGUE[0],),"epilogue")
        if self.sequence is not None and self.sequence.update(delta_ms):
            action=self.sequence_action
            self.sequence=self.sequence_action=None
            if action=="memory_transition":
                self._pause(360,"memory_transition","start_memory",fade="in")
            elif action=="start_memory":
                self.index=0
                self._dialogue((MEMORY[0],),"memory")
                if self.officer:self.officer.running=True
            elif action=="after_memory":
                self._pause(360,"memory_return","begin_after",fade="in")
            elif action=="begin_after":
                self.index=0
                self.story.set("red_officer_memory_seen")
                self.autosave_requested=True
                self._dialogue((AFTER_MEMORY[0],),"after_memory")
            elif action=="next_after":
                self.index+=1
                if self.index==5 and self.officer:
                    self.officer.running=False
                    self.officer.facing=1
                self._dialogue((AFTER_MEMORY[self.index],),"after_memory")
            elif action=="flee":
                self.phase="flee"
                self.elapsed_ms=0
                if self.officer:
                    self.officer.running=True
                    self.officer.facing=1
            elif action=="epilogue_last":
                self.index=2
                self._dialogue((EPILOGUE[2],),"epilogue")
            elif action=="complete":
                return self._complete()
        return False

    def _escape(self):
        if self.story.get("red_officer_escaped"):return
        self.story.set("red_officer_escaped")
        if self.officer in self.region.get("scenery",[]):self.region["scenery"].remove(self.officer)
        self.officer=None

    def _complete(self):
        self.story.set("red_officer_memory_seen")
        self._escape()
        self.story.set("prologue_completed")
        self.active=False
        self.sequence=None
        self.dialogue.npc=None
        self.player.attack_timer=self.player.dash_timer=self.player.dash_iframes=0
        self.player.invulnerability_timer=0
        return True

    def finish(self):
        if not self.active:return False
        self._complete()
        return True

    def draw_overlay(self,canvas):
        if self.phase=="memory":
            veil=pygame.Surface(canvas.get_size(),pygame.SRCALPHA)
            veil.fill((29,41,72,78))
            canvas.blit(veil,(0,0))
            rng=random.Random(90210);w,h=canvas.get_size()
            offset=(pygame.time.get_ticks()//18)%h
            for _ in range(82):
                x,y=rng.randrange(w),(rng.randrange(h)+offset)%h
                pygame.draw.line(canvas,(166,184,220),(x,y),(x-9,y+28),1)
        elif self.phase=="memory_end" and self.sequence:
            elapsed=self.sequence.current.duration_ms-self.sequence.remaining_ms
            if elapsed<150:
                veil=pygame.Surface(canvas.get_size(),pygame.SRCALPHA)
                veil.fill((217,207,231,32));canvas.blit(veil,(0,0))

    def draw_card(self,canvas):
        canvas.fill((5,7,10))
        lines=(("O VALE",44,(224,207,165)),("Prólogo",30,(218,218,212)),
               ("O Nome que Falta",30,(218,218,212)),("CONCLUÍDO",36,(224,207,165)))
        y=canvas.get_height()//2-sum(size+32 for _,size,_ in lines)//2
        for text,size,color in lines:
            image=pygame.font.Font(None,size).render(text,True,color)
            canvas.blit(image,image.get_rect(center=(canvas.get_width()//2,y+image.get_height()//2)))
            y+=image.get_height()+32


def math_sin(t):
    import math
    return math.sin(t*math.pi)
