"""Custody defenders: timed vulnerability, exact sectors, delayed echoes and two-phase duel."""
import math
import pygame
from core.animation import cardinal
from core.lacre_motion import COUNTS
from ui.character_art import prepared_frames,flash_image

SPECS={
 'lacre_guard':('Guardião de custódia',72,7,1.25,28),
 'unstable_echo':('Eco instável',62,6,1.7,32),
 'record_warden':('O Vigia dos Registros',180,10,1.2,95),
 'custodian':('Iriel — Custódio do Lacre',800,12,1.65,180),
}
class LacreActor:
    def __init__(self,kind,position,load,seed=0):
        self.kind=kind;self.name,hp,self.damage,self.speed,xp=SPECS[kind]
        self.hp=self.max_hp=hp;self.x,self.y=map(float,position);self.origin=position
        self.spawn_x,self.spawn_y=position
        self.chapter2_id=seed;self.config=dict(scale=2,xp_reward=xp,hitbox_radius=19)
        self.visual_foot=46;self.frames={a:prepared_frames(load(f'assets/vale_characters/{kind}_{a}.png'),160,cell=80,height=64) for a in COUNTS}
        self.flashes={a:tuple(tuple(flash_image(im) for im in row) for row in rows) for a,rows in self.frames.items()}
        if kind=='unstable_echo':
            self.faded={a:tuple(tuple(im.copy() for im in row) for row in rows) for a,rows in self.frames.items()}
            for rows in self.faded.values():
                for row in rows:
                    for im in row:im.set_alpha(155)
        self.state='IDLE';self.tick=seed*17;self.dead_timer=0;self.visual_facing=0;self.visual_flash=0
        self.attack_action=self.attack_phase=None;self.attack_direction=(0,1);self.timer=0;self.attack_hit=False
        self.attack_cooldown=24;self.serial=0;self.phase=1;self.phase_change=False;self.residuals=[]
        self.region=None;self.story=None;self.hurt_timer=0;self.last_hit_timer=0;self.talk_timer=0
    @property
    def hitbox(self):return pygame.Rect(round(self.x-19),round(self.y-11),38,22)
    @property
    def hurtbox(self):return self.hitbox.inflate(6,30).move(0,-15)
    @property
    def alive(self):return self.state!='DEAD' or self.dead_timer>0
    def drop(self):return None
    @property
    def coherent(self):return self.kind!='unstable_echo' or self.tick%150>=65
    @property
    def guarded(self):return self.kind=='record_warden' and self.attack_phase in ('windup','active')
    def receive_hit(self,damage,from_x,from_y,knockback=1):
        if self.state in ('DEAD','TRANSITION') or self.last_hit_timer:return False
        if self.kind=='custodian' and (not self.story or not self.story.get('lacre_custodian_talk_seen')):return False
        if not self.coherent or self.guarded:damage=max(1,damage//3)
        if self.kind=='custodian' and self.phase==2 and self.story:
            anchors=sum(not self.story.get('lacre_anchor_'+side+'_broken') for side in ('left','right'))
            damage=max(1,round(damage*(1-.18*anchors)))
        self.hp=max(0,self.hp-damage);self.visual_flash=8;self.last_hit_timer=8
        if self.kind=='custodian' and self.phase==1 and self.hp<=self.max_hp//2:
            self.hp=self.max_hp//2;self.phase_change=True
        elif not self.hp:
            self.state='DEAD';self.dead_timer=36;self.attack_phase=self.attack_action=None;self.residuals.clear();self.timer=0
        elif self.kind in ('lacre_guard','unstable_echo') or self.attack_phase=='recovery':
            self.hurt_timer=6
        return True
    def _move(self,dx,dy,obstacles):
        old=self.x,self.y;self.x+=dx;self.y+=dy
        if any(self.hitbox.colliderect(o) for o in obstacles):self.x,self.y=old;return False
        self.visual_facing=cardinal(dx,dy);return True
    def begin_attack(self,player,action=None):
        dx,dy=player.x-self.x,player.y-self.y;length=max(1,math.hypot(dx,dy));self.attack_direction=(dx/length,dy/length)
        self.visual_facing=cardinal(dx,dy);self.serial+=1
        if action is None:
            if self.kind=='custodian':action='charge' if length>130 else ('sweep' if self.serial%3==0 else 'cut')
            elif self.kind=='record_warden':action=('cut','sweep','ward')[(self.serial-1)%3]
            else:action='cut'
        self.attack_action=action;self.state='ATTACK';self.attack_phase='windup';self.attack_hit=False
        self.prep={'cut':26,'sweep':40,'charge':42,'ward':48}[action];self.timer=self.prep
        self.active_frames=14 if action=='charge' else 9;self.recovery=52 if action=='ward' else 44 if action!='cut' else 32
        self.attack_origin=(self.x,self.y)
    def _sector(self):
        return dict(origin=(self.x,self.y),direction=self.attack_direction,
                    radius=110 if self.attack_action=='ward' else 88 if self.attack_action=='sweep' else 70,
                    half=.38 if self.attack_action=='ward' else 1.45 if self.attack_action=='sweep' else .58)
    @staticmethod
    def sector_hit(sector,box):
        ox,oy=sector['origin'];dx,dy=sector['direction']
        for px,py in (box.center,box.topleft,box.topright,box.bottomleft,box.bottomright):
            vx,vy=px-ox,py-oy;dist=math.hypot(vx,vy)
            if dist<=sector['radius'] and (dist<1 or (vx*dx+vy*dy)/dist>=math.cos(sector['half'])):return True
        return False
    def attack_box(self):
        if self.attack_phase!='active':return pygame.Rect(0,0,0,0)
        radius=self._sector()['radius'];return pygame.Rect(round(self.x-radius),round(self.y-radius),radius*2,radius*2)
    def update(self,player,obstacles):
        self.tick+=1;self.visual_flash=max(0,self.visual_flash-1);self.last_hit_timer=max(0,self.last_hit_timer-1)
        if self.state=='DEAD':self.dead_timer=max(0,self.dead_timer-1);return self.alive
        if self.kind=='custodian' and self.story and not self.story.get('lacre_custodian_talk_seen'):return True
        if self.phase_change:
            self.phase_change=False;self.phase=2;self.state='TRANSITION';self.timer=80;self.attack_phase=self.attack_action=None;self.residuals.clear()
            if self.story:self.story.set('lacre_boss_wounded');self.story.set('lacre_boss_phase2_seen')
            return True
        if self.state=='TRANSITION':
            self.timer-=1
            if self.timer<=0:self.state='CHASE';self.attack_cooldown=30
            return True
        for echo in self.residuals[:]:
            echo['time']-=1
            if 0>=echo['time']>-8 and not echo['hit'] and self.sector_hit(echo,player.hitbox):
                echo['hit']=player.take_damage(max(1,self.damage-3),self.x,self.y,1)
            if echo['time']<=-8:self.residuals.remove(echo)
        if self.hurt_timer:self.hurt_timer-=1;return True
        if self.state=='ATTACK':
            self.timer-=1
            if self.attack_phase=='windup':
                if self.timer<=0:self.attack_phase='active';self.timer=self.active_frames
            elif self.attack_phase=='active':
                if self.attack_action=='charge':
                    for _ in range(3):self._move(self.attack_direction[0]*2.4,self.attack_direction[1]*2.4,obstacles)
                sector=self._sector()
                if not self.attack_hit and self.sector_hit(sector,player.hitbox):self.attack_hit=player.take_damage(self.damage,self.x,self.y,1.15)
                if self.timer<=0:
                    if self.kind=='custodian' and self.phase==2 and self.attack_action in ('cut','sweep'):
                        self.residuals.append(dict(sector,time=34,hit=False))
                    self.attack_phase='recovery';self.timer=self.recovery
            elif self.timer<=0:self.state='CHASE';self.attack_phase=self.attack_action=None;self.attack_cooldown=20
            return True
        self.attack_cooldown=max(0,self.attack_cooldown-1)
        dx,dy=player.x-self.x,player.y-self.y;dist=math.hypot(dx,dy)
        if dist>370:self.state='IDLE';return True
        if not self.attack_cooldown and dist<(220 if self.kind=='custodian' else 102):self.begin_attack(player);return True
        self.state='CHASE' if dist>65 else 'IDLE'
        if dist>65:
            dx/=max(1,dist);dy/=max(1,dist)
            if self.kind=='unstable_echo':
                side=.65 if self.tick%90<45 else -.65;dx,dy=dx-dy*side,dy+dx*side
            if not self._move(dx*self.speed,dy*self.speed,obstacles):
                self._move(-dy*self.speed,dx*self.speed,obstacles)
        return True
    @staticmethod
    def draw_sector(canvas,camera,sector,color,width=2):
        ox,oy=sector['origin'];base=math.atan2(sector['direction'][1],sector['direction'][0]);r=sector['radius']
        points=[(round(ox-camera[0]+math.cos(base-sector['half']+i*sector['half']/12)*r),round(oy-camera[1]+math.sin(base-sector['half']+i*sector['half']/12)*r)) for i in range(25)]
        pygame.draw.lines(canvas,color,False,points,width)
        for end in (points[0],points[-1]):pygame.draw.line(canvas,color,(round(ox-camera[0]),round(oy-camera[1])),end,1)
    def draw(self,canvas,camera):
        action='idle';index=(self.tick//18)%4
        if self.state=='DEAD':action='death';index=min(5,(36-self.dead_timer)//6)
        elif self.state=='TRANSITION':action='transition';index=min(5,(80-self.timer)//14)
        elif self.hurt_timer:action='hurt';index=min(2,(6-self.hurt_timer)//2)
        elif self.state=='CHASE':action='walk';index=(self.tick//6)%8
        elif self.state=='ATTACK':
            if self.attack_phase=='windup':action='windup';index=min(3,(self.prep-self.timer)*4//self.prep)
            else:
                action=self.attack_action if self.attack_action in COUNTS else 'sweep'
                index=2+min(3,(self.active_frames-self.timer)*4//self.active_frames) if self.attack_phase=='active' else 6+min(1,(self.recovery-self.timer)*2//self.recovery)
                index=max(0,index)
        image=self.frames[action][self.visual_facing][index]
        if self.visual_flash:image=self.flashes[action][self.visual_facing][index]
        if self.kind=='unstable_echo' and not self.coherent:
            # Alpha variants prepared once, not reconstructed in the frame loop.
            if not self.visual_flash:image=self.faded[action][self.visual_facing][index]
        canvas.blit(image,(round(self.x-80-camera[0]),round(self.y-92-camera[1])))
        if self.attack_phase=='windup':self.draw_sector(canvas,camera,self._sector(),(181,152,98))
        elif self.attack_phase=='active':self.draw_sector(canvas,camera,self._sector(),(206,192,148),3)
        for echo in self.residuals:self.draw_sector(canvas,camera,echo,(128,162,162) if echo['time']>0 else (214,205,159),2 if echo['time']>0 else 4)
        if self.state=='TRANSITION':
            pygame.draw.circle(canvas,(169,153,109),(round(self.x-camera[0]),round(self.y-camera[1])),30+(80-self.timer)%42,2)
        if self.kind=='custodian' and self.state=='TRANSITION':
            # A single short line, with no attack-specific dialogue spam.
            if not hasattr(self,'phase_line'):self.phase_line=pygame.font.Font(None,19).render('Não vou entregar os nomes a outra escolta.',True,(221,210,177))
            canvas.blit(self.phase_line,(round(self.x-self.phase_line.width/2-camera[0]),round(self.y-108-camera[1])))
