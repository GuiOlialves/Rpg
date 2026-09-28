"""The promise, escape and closing card for the prologue (3C)."""
import math
import random
import pygame
from entities.npc import NPC
from story.arrival_scene import ScriptedDialogue, Silhouette
from story.sequence import Beat, NarrativeSequence
from entities.player import frame

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
        image = pygame.transform.scale(frame(self.player.idle, 0, 1), (96, 96))
        image.fill((214, 135, 139, 255), special_flags=pygame.BLEND_RGBA_MULT)
        canvas.blit(image, (round(self.x - 48 - camera[0]),
                            round(self.y - 72 - camera[1])))


class _PlacedObject:
    has_embedded_shadow = True
    def __init__(self, image, x, y):
        self.image, self.x, self.y, self.depth = image, x, y, y
    def draw(self, canvas, camera, player=None):
        canvas.blit(self.image, (round(self.x-camera[0]), round(self.y-camera[1])))


class Prologue3CScene:
    """Atomic F4 skip and resumable narrative milestones before the end card."""
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
        # A visual stage in an existing clearing; the actual player never moves.
        self.memory_center = (1010, 710)
        rng = random.Random(90210)
        self.rain = [(rng.randrange(1024), rng.randrange(576)) for _ in range(44)]
        sheet = load("assets/vale_characters/red_soldier_0_idle.png")
        offsets = ((-150,-34),(-96,-42),(94,-42),(151,-34),(-160,40),(-104,48),(108,48),(164,38))
        self.memory_soldiers = []
        for i,(dx,dy) in enumerate(offsets):
            actor=NPC(f"promise_memory_soldier_{i}","Soldado Vermelho",
                      (self.memory_center[0]+dx,self.memory_center[1]+dy),{},sheet,frame_size=32,draw_size=48)
            actor.enabled=False
            actor.facing=2 if dx<0 else 1
            self.memory_soldiers.append(actor)
        old=region.get("red_officer_actor")
        if old in region.get("scenery",[]): region["scenery"].remove(old)
        factory=region.get("red_officer_factory")
        self.officer=(None if story.get("red_officer_escaped")
                      else factory() if factory else old)
        if self.officer is not None:
            if old is not None:
                self.officer.x, self.officer.y = old.x, old.y
            self.officer.state = "DEFEATED"
            self.officer.hp = 1
            self.officer.hostile = self.officer.boss_battle_active = False
            self.officer.running=False
            self.officer.facing=2
        region["boss_battle_active"] = False
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
            self.officer.standing_up=True
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
        self.sequence.start()
        if fade: self.sequence.fade.start(fade,duration)

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
                if self.index == 4:
                    self._pause(900, "memory_pause", "promise_reply")
                else:
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
    def memory_visible(self):
        return self.phase in {"memory_transition", "memory", "memory_pause", "memory_end"}

    @property
    def world_actors(self):
        if not self.active: return ()
        if self.memory_visible:
            x, y = self.memory_center
            self.silhouette.x,self.silhouette.y=x-38,y+2
            self.past_player.x,self.past_player.y=x+30,y+2
            actors=list(self.memory_soldiers)+[self.past_player,self.silhouette]
            if self.pendant_visible:
                actors.append(_PlacedObject(self.pendant,x-8,y-28))
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
            self.officer.standing_up=True
            self.officer.x=min(self.player.x+150, self.officer.x+delta_ms*.045)
            self.officer.y=max(self.player.y-24, self.officer.y-delta_ms*.008)
            self.officer.anim_tick+=max(1,round(delta_ms/(1000/60)))
        if self.phase=="after_memory" and self.officer is not None and self.officer.running:
            self.officer.x=min(self.player.x+220, self.officer.x+delta_ms*.085)
            self.officer.y=max(self.player.y-48, self.officer.y-delta_ms*.018)
            self.officer.anim_tick+=max(1,round(delta_ms/(1000/60)))
        if self.phase=="flee":
            self.elapsed_ms+=delta_ms
            if self.officer is not None:
                t = min(1, self.elapsed_ms / 2200)
                self.officer.x = self.flee_start[0] + (self.flee_target[0] - self.flee_start[0]) * t
                self.officer.y = self.flee_start[1] + (self.flee_target[1] - self.flee_start[1]) * t
                self.officer.anim_tick+=max(1,round(delta_ms/(1000/60)))
            if self.elapsed_ms>=2200:
                self.officer.running=False
                self._escape()
                self.autosave_requested=True
                self.phase="epilogue_looks"
                self.elapsed_ms=0
        elif self.phase=="epilogue_looks":
            self.elapsed_ms+=delta_ms
            self.player.facing=(1,3,2)[min(2,self.elapsed_ms//1200)]
            if self.elapsed_ms>=3600:
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
            elif action=="promise_reply":
                self._dialogue((MEMORY[self.index],), "memory")
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
                    self.officer.facing=2
                    self.flee_start = (self.officer.x, self.officer.y)
                    self.flee_target = (max(self.player.x + 620, self.officer.x + 480),
                                        min(self.officer.y, self.player.y - 48) - 60)
            elif action=="epilogue_last":
                self.index=2
                self._dialogue((EPILOGUE[2],),"epilogue")
            elif action=="complete":
                return self._complete()
        return False

    def _escape(self):
        self.story.set("red_officer_escaped")
        if self.officer in self.region.get("scenery",[]):self.region["scenery"].remove(self.officer)
        self.region.pop("red_officer_actor", None)
        self.region["boss_battle_active"] = False
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
        self.player.facing=2
        return True

    def finish(self):
        if not self.active:return False
        self._complete()
        return True

    def draw_overlay(self,canvas):
        if self.memory_visible:
            veil=pygame.Surface(canvas.get_size(),pygame.SRCALPHA)
            veil.fill((24,32,51,62))
            canvas.blit(veil,(0,0))
            w,h=canvas.get_size()
            offset=(pygame.time.get_ticks()//18)%h
            for x,y in self.rain:
                y=(y+offset)%h
                pygame.draw.line(canvas,(117,137,161),(x,y),(x-4,y+15),1)

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
