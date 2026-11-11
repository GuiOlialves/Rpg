"""Two native creatures with locked attacks, terrain-aware approach and readable recovery."""
import math
import pygame
from core.animation import cardinal,timed_frame,IDLE_DURATIONS,WALK_STRIDE_PIXELS
from ui.character_art import prepared_frames,flash_image

SPECS={
    'reed_stalker':dict(name='Espreitador dos juncos',hp=48,damage=6,speed=2.65,radius=15,
                       windup=24,active=9,recovery=33,reach=58,xp=24),
    'slateback':dict(name='Dorso-de-ardósia',hp=105,damage=10,speed=1.05,radius=23,
                   windup=43,active=7,recovery=48,reach=78,xp=42),
    'slate_warden':dict(name='Dorso-de-ardósia — vigia do ninho',hp=145,damage=11,speed=1.25,radius=25,
                      windup=46,active=8,recovery=52,reach=85,xp=55),
}
COUNTS={'idle':4,'walk':8,'windup':3,'attack':8,'hurt':3,'death':4}


class EncostaCreature:
    def __init__(self,kind,position,load,seed=0):
        self.kind=kind; spec=SPECS[kind]; self.name=spec['name']
        self.config=dict(spec,max_hp=spec['hp'],hitbox_radius=spec['radius'],scale=2,xp_reward=spec['xp'])
        self.x,self.y=map(float,position); self.spawn_x,self.spawn_y=self.x,self.y
        self.hp=self.max_hp=spec['hp']; self.damage=spec['damage']; self.speed=spec['speed']
        self.visual_foot=36; self.visual_facing=0; self.visual_distance=0; self.visual_moving=False
        self.state='IDLE'; self.anim_tick=seed*7; self.dead_timer=0; self.hurt_timer=0
        self.hit_resistance_timer=0; self.visual_flash=0; self.attack_cooldown=30+seed*9
        self.attack_phase=None; self.attack_action=None; self.attack_zone=None; self.phase_timer=0
        self.attack_direction=(0.,1.); self.attack_hit=False; self.chapter2_id=seed; self.strikes=0
        self.frames={a:prepared_frames(load(f'assets/vale_characters/{kind}_{a}.png'),160,cell=80,height=40) for a in COUNTS}
        self.flashes={a:tuple(tuple(flash_image(im) for im in row) for row in rows) for a,rows in self.frames.items()}

    @property
    def hitbox(self):
        radius=self.config['radius']
        return pygame.Rect(round(self.x-radius),round(self.y-12),radius*2,24)
    @property
    def hurtbox(self): return self.hitbox.inflate(4,22).move(0,-11)
    @property
    def alive(self): return self.state!='DEAD' or self.dead_timer>0
    def drop(self): return None
    def attack_box(self): return self.attack_zone or pygame.Rect(0,0,0,0)

    def _move(self,dx,dy,obstacles):
        old=(self.x,self.y); self.x+=dx; self.y+=dy
        if not (30<self.x<2018 and 45<self.y<1118) or any(self.hitbox.colliderect(o) for o in obstacles):
            self.x,self.y=old; return False
        self.visual_distance=(self.visual_distance+math.hypot(dx,dy))%WALK_STRIDE_PIXELS
        self.visual_moving=True; self.visual_facing=cardinal(dx,dy)
        return True

    def _begin_attack(self,player):
        length=max(1,math.hypot(player.x-self.x,player.y-self.y))
        self.attack_direction=((player.x-self.x)/length,(player.y-self.y)/length)
        self.visual_facing=cardinal(*self.attack_direction); self.state='ATTACK'
        self.attack_action='charge' if self.kind=='reed_stalker' else ('charged' if self.kind=='slate_warden' and self.strikes%2 else 'normal')
        self.strikes+=1; self.attack_phase='windup'; self.phase_timer=self.config['windup']
        self.attack_hit=False; self.anim_tick=0
        self.windup_frames=self.config['windup']+(14 if self.attack_action=='charged' else 0)
        self.phase_timer=self.windup_frames

    def _strike(self):
        if self.attack_action=='charged':
            return pygame.Rect(round(self.x-66),round(self.y-66),132,132)
        dx,dy=self.attack_direction; reach=self.config['reach']
        center=(self.x+dx*reach*.6,self.y+dy*reach*.6)
        width=40 if self.kind=='reed_stalker' else 88
        return pygame.Rect(round(center[0]-width/2),round(center[1]-width/2),width,width)

    def receive_hit(self,damage,from_x,from_y,knockback=1):
        if self.state=='DEAD' or self.hit_resistance_timer: return False
        self.hp=max(0,self.hp-damage); self.visual_flash=8; self.hit_resistance_timer=10
        if not self.hp:
            self.state='DEAD'; self.dead_timer=36; self.attack_zone=self.attack_phase=self.attack_action=None; self.anim_tick=0
        elif self.state!='ATTACK' or self.kind=='reed_stalker':
            self.state='HURT'; self.hurt_timer=8; self.anim_tick=0; self.attack_zone=self.attack_phase=self.attack_action=None
        return True

    def update(self,player,obstacles):
        self.anim_tick+=1; self.visual_flash=max(0,self.visual_flash-1)
        self.hit_resistance_timer=max(0,self.hit_resistance_timer-1); self.visual_moving=False
        if self.state=='DEAD': self.dead_timer=max(0,self.dead_timer-1); return self.alive
        if self.hurt_timer:
            self.hurt_timer-=1
            if not self.hurt_timer: self.state='CHASE'
            return True
        if self.state=='ATTACK':
            self.phase_timer-=1
            if self.attack_phase=='windup':
                if self.phase_timer<=0:
                    self.attack_phase='active'; self.phase_timer=self.config['active']
                return True
            if self.attack_phase=='active':
                if self.kind=='reed_stalker':
                    dx,dy=self.attack_direction
                    for _ in range(3):
                        if not self._move(dx*2.3,dy*2.3,obstacles): break
                self.attack_zone=self._strike()
                hit=self.attack_zone.colliderect(player.hitbox)
                if self.attack_action=='charged':
                    closest=(max(player.hitbox.left,min(self.x,player.hitbox.right)),
                             max(player.hitbox.top,min(self.y,player.hitbox.bottom)))
                    hit=math.dist((self.x,self.y),closest)<=66
                if not self.attack_hit and hit:
                    self.attack_hit=player.take_damage(self.damage,self.x,self.y,1.15)
                if self.phase_timer<=0:
                    self.attack_zone=None; self.attack_phase='recovery'; self.phase_timer=self.config['recovery']+(12 if self.attack_action=='charged' else 0)
                return True
            if self.phase_timer<=0:
                self.state='CHASE'; self.attack_phase=self.attack_action=None; self.attack_cooldown=22
            return True
        self.attack_cooldown=max(0,self.attack_cooldown-1)
        distance=math.hypot(player.x-self.x,player.y-self.y)
        # Territorial leashes leave a restful space after a player disengages.
        if distance>300 or math.hypot(self.x-self.spawn_x,self.y-self.spawn_y)>340:
            target=(self.spawn_x,self.spawn_y); self.state='IDLE'
        else:
            target=(player.x,player.y); self.state='CHASE'
            if distance< (132 if self.kind=='reed_stalker' else 98) and not self.attack_cooldown:
                self._begin_attack(player); return True
        dx,dy=target[0]-self.x,target[1]-self.y; length=max(1,math.hypot(dx,dy))
        if length>7:
            dx,dy=dx/length*self.speed,dy/length*self.speed
            if not self._move(dx,dy,obstacles):
                # A consistent flank preference avoids jitter against a boulder.
                sign=1 if self.chapter2_id%2 else -1
                if not self._move(-dy*sign,dx*sign,obstacles):
                    if not self._move(dx,0,obstacles): self._move(0,dy,obstacles)
        return True

    def draw(self,canvas,camera):
        action,index='idle',timed_frame(self.anim_tick,IDLE_DURATIONS)
        if self.state=='DEAD': action,index='death',min(3,(36-self.dead_timer)//8)
        elif self.state=='HURT': action,index='hurt',min(2,self.anim_tick//3)
        elif self.state=='ATTACK':
            if self.attack_phase=='windup': action,index='windup',min(2,(self.windup_frames-self.phase_timer)*3//self.windup_frames)
            elif self.attack_phase=='active': action,index='attack',min(5,2+(self.config['active']-self.phase_timer)*4//self.config['active'])
            else: action,index='attack',6 if self.phase_timer>14 else 7
        elif self.visual_moving: action,index='walk',int(self.visual_distance/WALK_STRIDE_PIXELS*8)%8
        im=(self.flashes if self.visual_flash>4 else self.frames)[action][self.visual_facing][index]
        canvas.blit(im,(round(self.x-80-camera[0]),round(self.y-72-camera[1])))
        if self.state=='ATTACK' and self.attack_phase=='windup':
            dx,dy=self.attack_direction; cx,cy=round(self.x-camera[0]),round(self.y-camera[1]-8)
            color=(200,173,111)
            if self.kind=='reed_stalker':
                end=(round(cx+dx*86),round(cy+dy*86)); pygame.draw.line(canvas,color,(cx,cy),end,2)
                pygame.draw.line(canvas,color,end,(round(end[0]-dx*10-dy*6),round(end[1]-dy*10+dx*6)),2)
            elif self.attack_action=='charged':
                pygame.draw.circle(canvas,color,(cx,cy+8),66,2)
                pygame.draw.circle(canvas,(139,126,90),(cx,cy+8),56,1)
            else:
                angle=math.atan2(dy,dx)
                pts=[(round(cx+math.cos(angle+t)*82),round(cy+math.sin(angle+t)*60)) for t in (-1.2,-.8,-.4,0,.4,.8,1.2)]
                pygame.draw.lines(canvas,color,False,pts,2)
        elif self.state=='ATTACK' and self.attack_phase=='active' and self.kind!='reed_stalker':
            cx,cy=round(self.x-camera[0]),round(self.y-camera[1])
            if self.attack_action=='charged':
                radius=round(66*(1-self.phase_timer/self.config['active']))
                pygame.draw.circle(canvas,(158,146,108),(cx,cy),max(2,radius),2)
            else:
                angle=math.atan2(self.attack_direction[1],self.attack_direction[0])
                pts=[(round(cx+math.cos(angle+t)*70),round(cy+math.sin(angle+t)*53)) for t in (-1,-.6,-.2,.2,.6,1)]
                pygame.draw.lines(canvas,(172,160,121),False,pts,2)
