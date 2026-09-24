"""Identidades estáveis e dados de apresentação dos consumíveis."""

CONSUMABLES = {
    "potion": {"name": "Poção", "color": (194, 62, 68), "resource": "hp", "restore": 30},
    "ether": {"name": "Éter", "color": (62, 128, 207), "resource": "sp", "restore": 30},
    "herb": {"name": "Erva", "color": (84, 177, 113), "resource": "hp", "restore": 15},
}


def consumable(item_id, amount=1):
    definition = CONSUMABLES[item_id]
    return {"id": item_id, "name": definition["name"], "amount": amount,
            "color": definition["color"]}
