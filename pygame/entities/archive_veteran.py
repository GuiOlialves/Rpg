"""Soren: three locked, readable attacks and a nonlethal defeat."""
import math
import pygame
from core.animation import cardinal, timed_frame, IDLE_DURATIONS, WALK_STRIDE_PIXELS
from core.archive_motion import COUNTS, pose
from entities.enemy import Enemy
from ui.character_art import prepared_frames, flash_image


class ArchiveVeteran(Enemy):
    WINDUP = {'normal': 22, 'charged': 40, 'charge': 32}
    ACTIVE = {'normal': 5, 'charged': 8, 'charge': 14}
    RECOVERY = {'normal': 27, 'charged': 42, 'charge': 38}
    ACTION = {'normal': 'quick', 'charged': 'wide', 'charge': 'advance'}

    def __init__(self, position, load):
        super().__init__('red_soldier', position, load, seed=617)
        self.kind = 'archive_veteran'
        self.config = dict(self.config, max_hp=210, damage=9, speed=2.2, xp_reward=0)
        self.name = 'SOREN — VETERANO DA RETAGUARDA'
        self.hp = self.max_hp = 210
        self.damage, self.speed = 9, 2.2
        self.visual_foot = 36
        self.hostile = False
        self.attack_cooldown = 38
        self.actions_taken = 0
        self.frames = {a: prepared_frames(load(f'assets/vale_characters/archive_veteran_{a}.png'),
                                          96, cell=48, height=40) for a in COUNTS}
        self.flashes = {a: tuple(tuple(flash_image(im) for im in row) for row in rows)
                        for a,rows in self.frames.items()}
        self.blades, self.masks, self.trails, self.ready_blades = {}, {}, {}, {}
        for facing,angle in enumerate((45,135,45,-45)):
            im=pygame.Surface((96,96),pygame.SRCALPHA)
            g=(55,49)
            dx,dy=math.cos(math.radians(angle)),math.sin(math.radians(angle))
            t=(round(g[0]+dx*30),round(g[1]+dy*30))
            pygame.draw.line(im,(37,43,60),g,t,4)
            pygame.draw.line(im,(183,207,202),g,t,2)
            pygame.draw.line(im,(237,240,209),(g[0]-1,g[1]),(t[0]-1,t[1]),1)
            pygame.draw.line(im,(212,171,101),(round(g[0]+dy*3),round(g[1]-dx*3)),
                             (round(g[0]-dy*3),round(g[1]+dx*3)),2)
            self.ready_blades[facing]=pygame.transform.scale_by(im,2)
        for action in self.ACTION.values():
            for facing in range(4):
                for i in range(8):
                    im = pygame.Surface((96,96),pygame.SRCALPHA)
                    mask = pygame.Surface((96,96),pygame.SRCALPHA)
                    _center, grip, tip = pose(action,i,facing)
                    grip = (grip[0]+24,grip[1]+22)
                    tip = (tip[0]+24,tip[1]+22)
                    direction = ((tip[0]-grip[0])/30,(tip[1]-grip[1])/30)
                    g = tuple(round(v) for v in grip); t = tuple(round(v) for v in tip)
                    pygame.draw.line(im,(37,43,60),g,t,4)
                    pygame.draw.line(im,(183,207,202),g,t,2)
                    pygame.draw.line(im,(237,240,209),(g[0]-1,g[1]),(t[0]-1,t[1]),1)
                    cross = (direction[1]*3,-direction[0]*3)
                    pygame.draw.line(im,(212,171,101),
                        (round(g[0]+cross[0]),round(g[1]+cross[1])),
                        (round(g[0]-cross[0]),round(g[1]-cross[1])),2)
                    pygame.draw.line(im,(97,70,63),g,
                        (round(g[0]-direction[0]*4),round(g[1]-direction[1]*4)),2)
                    pygame.draw.line(mask,(255,255,255),g,t,5)
                    key=(action,facing,i)
                    self.blades[key]=pygame.transform.scale_by(im,2)
                    self.masks[key]=pygame.mask.from_surface(pygame.transform.scale_by(mask,2))
                    trail=pygame.Surface((96,96),pygame.SRCALPHA)
                    if 2 <= i <= 5 and action != 'advance':
                        old_tip=pose(action,max(1,i-1),facing)[2]
                        points=[(round(old_tip[0]+24),round(old_tip[1]+22)),t]
                        pygame.draw.line(trail,(232,215,164,155),*points,2)
                    self.trails[key]=pygame.transform.scale_by(trail,2)

    def drop(self): return None

    @property
    def frame_index(self):
        if self.attack_phase == 'windup':
            return 0 if self.phase_timer > self.WINDUP[self.attack_action]//2 else 1
        if self.attack_phase == 'active':
            return min(5,2+(self.ACTIVE[self.attack_action]-self.phase_timer)*4//self.ACTIVE[self.attack_action])
        return 6 if self.phase_timer > 10 else 7

    def blade_origin(self): return (round(self.x-96),round(self.y-116))

    def _blade_hits(self, box):
        key=(self.ACTION[self.attack_action],self.visual_facing,self.frame_index)
        origin=self.blade_origin()
        target=pygame.mask.Mask(box.size,fill=True)
        return self.masks[key].overlap(target,(box.x-origin[0],box.y-origin[1])) is not None

    def _begin_attack(self, action, player):
        self.state, self.attack_action, self.attack_phase = 'ATTACK', action, 'windup'
        self.attack_direction=self._direction_to(player)
        self.visual_facing=cardinal(*self.attack_direction)
        self.phase_timer=self.WINDUP[action]
        self.attack_hit=False
        self.attack_zone=None
        self.anim_tick=0

    def receive_hit(self, damage, from_x, from_y, knockback=1):
        if self.state == 'DEFEATED' or not self.hostile or self.hit_resistance_timer: return False
        self.hp=max(1,self.hp-damage)
        self.visual_flash=8
        self.hit_resistance_timer=9
        if self.hp == 1:
            self.state='DEFEATED'; self.hostile=False; self.anim_tick=0
            self.attack_zone=self.attack_action=self.attack_phase=None
        elif self.state != 'ATTACK':
            self.hurt_timer=7; self.state='HURT'; self.anim_tick=0
        return True

    def update(self, player, obstacles):
        self.anim_tick+=1
        self.visual_flash=max(0,self.visual_flash-1)
        self.hit_resistance_timer=max(0,self.hit_resistance_timer-1)
        self.visual_moving=False
        if not self.hostile: return True
        if self.hurt_timer:
            self.hurt_timer-=1
            if not self.hurt_timer: self.state='CHASE'
            return True
        if self.state == 'ATTACK':
            self.phase_timer-=1
            if self.attack_phase == 'windup':
                if self.phase_timer <= 0:
                    self.attack_phase='active'; self.phase_timer=self.ACTIVE[self.attack_action]
                return True
            if self.attack_phase == 'active':
                if self.attack_action == 'charge':
                    dx,dy=self.attack_direction
                    for _ in range(3):
                        if not self._move(dx*3.8,dy*3.8,obstacles):
                            self.phase_timer=0; break
                origin=self.blade_origin()
                key=(self.ACTION[self.attack_action],self.visual_facing,self.frame_index)
                self.attack_zone=self.masks[key].get_bounding_rects()[0].move(origin)
                if not self.attack_hit and self._blade_hits(player.hitbox):
                    power={'normal':1,'charged':1.45,'charge':1.2}[self.attack_action]
                    self.attack_hit=player.take_damage(round(self.damage*power),self.x,self.y,power)
                if self.phase_timer <= 0:
                    self.attack_phase='recovery'; self.phase_timer=self.RECOVERY[self.attack_action]
                    self.attack_zone=None
                return True
            if self.phase_timer <= 0:
                self.state='CHASE'; self.attack_phase=self.attack_action=None; self.attack_cooldown=22
            return True
        self.state='CHASE'
        self.attack_cooldown=max(0,self.attack_cooldown-1)
        distance=math.hypot(player.x-self.x,player.y-self.y)
        if not self.attack_cooldown and distance < 230:
            action='charge' if distance > 105 else 'charged' if self.actions_taken%2 else 'normal'
            self.actions_taken+=1; self._begin_attack(action,player)
        elif distance > 55:
            dx,dy=self._direction_to(player)
            if not self._move(dx*self.speed,dy*self.speed,obstacles):
                if not self._move(dx*self.speed,0,obstacles): self._move(0,dy*self.speed,obstacles)
        return True

    @property
    def depth(self): return self.y

    def draw(self, canvas, camera, player=None):
        action,index='idle',timed_frame(self.anim_tick,IDLE_DURATIONS)
        if self.state == 'DEFEATED': action,index='defeated',min(3,self.anim_tick//8)
        elif self.state == 'HURT': action,index='hurt',min(2,self.anim_tick//3)
        elif self.state == 'ATTACK': action,index=self.ACTION[self.attack_action],self.frame_index
        elif self.visual_moving: action,index='walk',int(self.visual_distance/WALK_STRIDE_PIXELS*8)%8
        image=(self.flashes if self.visual_flash > 4 else self.frames)[action][self.visual_facing][index]
        canvas.blit(image,(round(self.x-48-camera[0]),round(self.y-72-camera[1])))
        if self.state == 'DEFEATED':
            a=(round(self.x+24-camera[0]),round(self.y+5-camera[1]))
            b=(a[0]+54,a[1]-8)
            pygame.draw.line(canvas,(37,43,60),a,b,6)
            pygame.draw.line(canvas,(183,207,202),a,b,3)
            pygame.draw.line(canvas,(212,171,101),(a[0],a[1]-6),(a[0]+2,a[1]+6),3)
        elif self.state != 'ATTACK':
            canvas.blit(self.ready_blades[self.visual_facing],
                        (round(self.x-96-camera[0]),round(self.y-116-camera[1])))
        if self.state == 'ATTACK':
            origin=tuple(v-camera[k] for k,v in enumerate(self.blade_origin()))
            key=(action,self.visual_facing,index)
            canvas.blit(self.trails[key],origin); canvas.blit(self.blades[key],origin)
            if self.attack_phase == 'windup':
                dx,dy=((0,1),(-1,0),(1,0),(0,-1))[self.visual_facing]
                center=(round(self.x-camera[0]),round(self.y-camera[1]-18))
                if self.attack_action == 'charge':
                    dx,dy=self.attack_direction
                    end=(round(center[0]+dx*160),round(center[1]+dy*160))
                    pygame.draw.line(canvas,(219,175,101),center,end,2)
                    pygame.draw.circle(canvas,(219,175,101),end,5,1)
                elif self.attack_action == 'charged':
                    a=math.atan2(dy,dx)
                    points=[(round(center[0]+math.cos(a+t)*78),round(center[1]+math.sin(a+t)*78))
                            for t in (-1.5,-1,-.5,0,.5,1,1.5)]
                    pygame.draw.lines(canvas,(224,140,99),False,points,2)
                else:
                    pygame.draw.line(canvas,(214,186,115),center,(center[0]+dx*72,center[1]+dy*72),2)
