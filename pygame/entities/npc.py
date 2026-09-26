import math
import pygame

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
        sheet = self.run_sprite if self.running and self.run_sprite else self.sprite
        frame_count = max(1, sheet.get_width() // self.frame_size)
        frame_index = (self.anim_tick // 5) % frame_count if self.running else 0
        frame = sheet.subsurface((frame_index * self.frame_size, 0,
                                  self.frame_size, self.frame_height)).copy()
        if self.facing == 1 and (self.running or self.frame_size == 32):
            frame = pygame.transform.flip(frame, True, False)
        source_foot = frame.get_bounding_rect().bottom
        scaled_height = max(1, round(self.draw_size * self.frame_height / self.frame_size))
        frame = pygame.transform.scale(frame, (self.draw_size, scaled_height))
        if self.foot_ratio is None:
            foot_offset = round(source_foot * scaled_height / self.frame_height)
        else:
            foot_offset = round(self.foot_ratio * scaled_height)
        canvas.blit(frame, (round(self.x - self.draw_size / 2 - camera[0]),
                            round(self.y - foot_offset - camera[1])))

def nearest(npcs, player, context=None):
    options = [(math.hypot(n.x-player.x, n.y-player.y), n) for n in npcs
               if n.interaction_rect.colliderect(player.hitbox)
               and getattr(n, "available", lambda _context: True)(context)]
    return min(options, key=lambda item: item[0])[1] if options else None
