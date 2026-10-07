import math
import pygame
from ui.character_art import FRAME, DRAW_SIZE, PIVOT, prepared_frames
from core.animation import IDLE_DURATIONS, WALK_STRIDE_PIXELS, timed_frame

class NPC:
    def __init__(self, uid, name, position, dialogues, sprite, run_sprite=None,
                 frame_size=192, draw_size=104, foot_ratio=None, frame_height=None):
        self.uid, self.name = uid, name
        self.x, self.y = map(float, position)
        self.dialogues, self.sprite = dialogues, sprite
        self.run_sprite = run_sprite
        self.frame_size = frame_size
        self.frame_height = frame_height or frame_size
        self.draw_size = draw_size
        self.foot_ratio = foot_ratio
        self.running = False
        self.enabled = True
        self.quest_id = None
        self.quest_effects_enabled = True
        self.facing, self.anim_tick = 0, 0
        self.own_art = frame_size == FRAME and sprite.get_height() == FRAME*4
        if self.own_art:
            self.draw_size = DRAW_SIZE
        self.visual_distance = 0.0
        self.last_visual_position = (self.x,self.y)
        self.idle_offset = sum(map(ord,uid))*7
        self.prepared = prepared_frames(sprite,self.draw_size,cell=frame_size,height=self.frame_height)
        self.prepared_run = (prepared_frames(run_sprite,self.draw_size,cell=frame_size,height=self.frame_height)
                             if run_sprite is not None else self.prepared)
        self.prepared_left = self.prepared_run_left = None
        if not self.own_art:
            self.prepared_left = tuple(tuple(pygame.transform.flip(im,True,False) for im in row)
                                       for row in self.prepared)
            self.prepared_run_left = tuple(tuple(pygame.transform.flip(im,True,False) for im in row)
                                           for row in self.prepared_run)
        # Legacy one-row NPCs retain their original whole-body foot contract.
        self.source_foot = sprite.subsurface((0,0,frame_size,self.frame_height)).get_bounding_rect().bottom

    def available(self, context=None):
        return self.enabled

    @property
    def hitbox(self):
        return pygame.Rect(round(self.x - 18), round(self.y - 12), 36, 24)

    @property
    def interaction_rect(self):
        return self.hitbox.inflate(70, 70)

    def dialogue_for(self, state, quest_manager=None):
        if self.quest_id and quest_manager:
            quest = quest_manager.get(self.quest_id)
            if quest.state == "REWARDED" and quest_manager.forest_boss_defeated and "BOSS_DONE" in self.dialogues:
                return self.dialogues["BOSS_DONE"]
            return self.dialogues.get(quest.state, self.dialogues["default"])
        return self.dialogues.get(state, self.dialogues["default"])

    def begin_interaction(self, dialogue, player, manager=None):
        self.face_player(player)
        dialogue.open(self, manager)

    def face_player(self, player):
        dx, dy = player.x - self.x, player.y - self.y
        if abs(dx) > abs(dy): self.facing = 2 if dx > 0 else 1
        else: self.facing = 0 if dy > 0 else 3

    def draw(self, canvas, camera):
        distance = math.dist(self.last_visual_position,(self.x,self.y))
        self.last_visual_position = (self.x,self.y)
        moving = self.running and .01 < distance < 32
        if moving:
            self.visual_distance = (self.visual_distance+distance) % WALK_STRIDE_PIXELS
        frames = self.prepared_run if moving else self.prepared
        if not self.own_art and self.facing == 1:
            frames = self.prepared_run_left if moving else self.prepared_left
        frame_index = (int(self.visual_distance/WALK_STRIDE_PIXELS*len(frames[0]))
                       if moving else timed_frame(pygame.time.get_ticks()*60//1000+self.idle_offset,IDLE_DURATIONS))
        frame = frames[self.facing if self.own_art else 0][frame_index%len(frames[0])]
        scaled_height = frame.get_height()
        foot_offset = (PIVOT[1]*self.draw_size/FRAME if self.own_art
                       else math.ceil(self.source_foot*scaled_height/self.frame_height)
                       if self.foot_ratio is None else round(self.foot_ratio*scaled_height))
        canvas.blit(frame, (round(self.x - self.draw_size / 2 - camera[0]),
                            round(self.y - foot_offset - camera[1])))

def nearest(npcs, player, context=None):
    options = [(math.hypot(n.x-player.x, n.y-player.y), n) for n in npcs
               if n.interaction_rect.colliderect(player.hitbox)
               and getattr(n, "available", lambda _context: True)(context)]
    return min(options, key=lambda item: item[0])[1] if options else None
