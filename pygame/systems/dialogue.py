"""Compatibility facade; the dialogue box presentation lives under ui/."""
from ui.dialogue_box import DialogueBox


class DialogueSystem:
    """Applies quest interactions when a dialogue reaches its final line."""

    def advance(self, dialogue_box, quest_manager, inventory):
        npc = dialogue_box.advance()
        if npc is None:
            return False
        quest_id = getattr(npc, "quest_id", None)
        if quest_id and getattr(npc, "quest_effects_enabled", True):
            quest = quest_manager.get(quest_id)
            if quest.state == "AVAILABLE":
                quest_manager.accept(quest.id)
            elif quest.state == "COMPLETED":
                quest_manager.claim(quest.id, inventory)
        return True


__all__ = ["DialogueBox", "DialogueSystem"]
