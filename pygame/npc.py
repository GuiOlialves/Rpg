import math
import pygame

class NPC:
    def __init__(self, uid, name, position, dialogues, sprite):
        self.uid, self.name = uid, name
        self.x, self.y = map(float, position)
        self.dialogues, self.sprite = dialogues, sprite
        self.quest_id = None
        self.facing, self.anim_tick = 0, 0

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

    def face_player(self, player):
        dx, dy = player.x - self.x, player.y - self.y
        if abs(dx) > abs(dy): self.facing = 2 if dx > 0 else 1
        else: self.facing = 0 if dy > 0 else 3

    def draw(self, canvas, camera):
        frame = self.sprite.subsurface((0, 0, 192, 192)).copy()
        frame = pygame.transform.scale(frame, (104, 104))
        canvas.blit(frame, (round(self.x - 52 - camera[0]), round(self.y - 137 * 104 / 192 - camera[1])))

def nearest(npcs, player):
    options = [(math.hypot(n.x-player.x, n.y-player.y), n) for n in npcs if n.interaction_rect.colliderect(player.hitbox)]
    return min(options, key=lambda item: item[0])[1] if options else None
