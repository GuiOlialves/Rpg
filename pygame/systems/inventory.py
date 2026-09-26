"""Regras de inventário, empilhamento e ações sobre itens."""
from core.config import CONSUMABLE_COOLDOWN_FRAMES, FPS
from systems.items import CONSUMABLES

def inventory_kind(item):
    if item.get("type") == "equipment" or item.get("slot"): return "equipment"
    if item.get("id") in CONSUMABLES: return "consumable"
    return "item"

def add_inventory_item(inventory, item_data):
    existing = next((entry for entry in inventory if entry.get("id") == item_data["id"] and entry.get("type") != "equipment"), None)
    if existing: existing["amount"] += item_data["amount"]
    else: inventory.append(item_data.copy())

def apply_inventory_action(selected, inventory, player, ui_state):
    if player.hp <= 0:
        return False, "Não é possível usar itens agora."
    if selected is None or not any(entry is selected for entry in inventory):
        return False, "Selecione um item primeiro."
    kind = inventory_kind(selected)
    if kind == "equipment":
        slot = selected["slot"]
        equipped = player.equipment.get(slot)
        if equipped and equipped.get("id") == selected.get("id"):
            player.unequip(slot)
            return True, f"{selected['name']} desequipado."
        replaced = player.equip(selected)
        message = f"{selected['name']} equipado."
        if replaced and replaced.get("id") != selected.get("id"):
            message = f"{selected['name']} equipado no lugar de {replaced['name']}."
        return True, message

    if kind == "consumable":
        cooldown = ui_state.get("consumable_cooldown", 0)
        if cooldown > 0:
            return False, f"Aguarde {cooldown / FPS:.1f}s para usar outro consumível."
        name = selected.get("name")
        definition = CONSUMABLES.get(selected.get("id"), {})
        target, amount = definition.get("resource"), definition.get("restore", 0)
        if target is None: return False, "Esse item não pode ser usado agora."
        current, maximum = getattr(player, target), getattr(player, f"max_{target}")
        if current >= maximum:
            return False, "Vida já está cheia." if target == "hp" else "SP já está cheio."
        restored = min(amount, maximum - current)
        setattr(player, target, current + restored)
        ui_state["consumable_cooldown"] = CONSUMABLE_COOLDOWN_FRAMES
        selected["amount"] = selected.get("amount", 1) - 1
        if selected["amount"] <= 0:
            del inventory[next(index for index, entry in enumerate(inventory) if entry is selected)]
            ui_state["selected"] = None
        return True, f"{name}: +{restored} {'HP' if target == 'hp' else 'SP'}."
    return False, "Esse item não possui uma ação disponível."
