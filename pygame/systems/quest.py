from dataclasses import dataclass
from .items import consumable

AVAILABLE, ACTIVE, COMPLETED, REWARDED = "AVAILABLE", "ACTIVE", "COMPLETED", "REWARDED"

@dataclass
class Quest:
    id: str
    name: str
    description: str
    target: str
    required: int
    reward: dict
    giver: str
    state: str = AVAILABLE
    progress: int = 0

    def enemy_defeated(self, kind):
        if self.state == ACTIVE and kind == self.target:
            self.progress = min(self.required, self.progress + 1)
            if self.progress >= self.required: self.state = COMPLETED
            return True
        return False

class QuestManager:
    def __init__(self):
        self.quests = {"forest_trouble": Quest("forest_trouble", "Problemas na Floresta", "Derrote os slimes que ameaçam a vila.", "slime", 5, consumable("herb", 3), "alden")}
        self.notice = ""
        self.notice_timer = 0
        self.forest_event_started = False
        self.forest_boss_defeated = False
        self.boss_loot_given = False

    def get(self, quest_id): return self.quests[quest_id]
    def accept(self, quest_id): self.get(quest_id).state = ACTIVE
    def enemy_defeated(self, kind):
        for quest in self.quests.values():
            if quest.enemy_defeated(kind):
                self.notice = "Objetivo concluído" if quest.state == COMPLETED else f"Slimes derrotados: {quest.progress}/{quest.required}"
                self.notice_timer = 150
    def claim(self, quest_id, inventory):
        quest = self.get(quest_id)
        if quest.state != COMPLETED: return False
        item = next((i for i in inventory if i["id"] == quest.reward["id"]), None)
        if item: item["amount"] += quest.reward["amount"]
        else: inventory.append(quest.reward.copy())
        quest.state = REWARDED
        self.notice, self.notice_timer = "Recompensa recebida: 3 Ervas", 180
        return True
    def update(self):
        if self.notice_timer: self.notice_timer -= 1

    def active_text(self):
        for q in self.quests.values():
            if q.state == ACTIVE: return f"{q.name}  |  Slimes: {q.progress}/{q.required}"
            if q.state == COMPLETED: return f"Slimes: {q.progress}/{q.required}  |  Volte à Vila e fale com Alden."
        return ""

    def forest_ready(self):
        return self.get("forest_trouble").state == REWARDED
