SLOTS = ("Arma", "Armadura", "Acessório")

EQUIPMENT = {
    "iron_blade": {"id": "iron_blade", "name": "Lâmina de Ferro", "type": "equipment", "slot": "Arma", "description": "Uma espada simples e confiável.", "bonuses": {"força": 2}, "color": (190, 190, 205)},
    "reinforced_leather": {"id": "reinforced_leather", "name": "Couro Reforçado", "type": "equipment", "slot": "Armadura", "description": "Protege sem atrapalhar os movimentos.", "bonuses": {"vitalidade": 2}, "color": (132, 83, 48)},
    "grove_charm": {"id": "grove_charm", "name": "Amuleto da Clareira", "type": "equipment", "slot": "Acessório", "description": "Ainda guarda a energia da clareira.", "bonuses": {"vitalidade": 1, "agilidade": 1}, "color": (91, 181, 126)},
}

def item(item_id):
    return dict(EQUIPMENT[item_id], bonuses=dict(EQUIPMENT[item_id]["bonuses"]))
