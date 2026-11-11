"""Identidades estáveis e dados de apresentação dos consumíveis."""

CONSUMABLES = {
    "potion": {"name": "Poção", "color": (194, 62, 68), "resource": "hp", "restore": 30},
    "ether": {"name": "Éter", "color": (62, 128, 207), "resource": "sp", "restore": 30},
    "herb": {"name": "Erva", "color": (84, 177, 113), "resource": "hp", "restore": 15},
}

QUEST_ITEMS = {
    'route_transfer_note': {'name':'Nota de transferência do rol','color':(171,166,125),
        'description':'Marco da Encosta, antes da quarta vigília. Separar os nomes dos acolhidos da remessa militar. Mesmo carimbo do recibo do Vale.'},
    'encosta_locket': {'name':'Pingente de Lídia','color':(182,142,88),
        'description':'Duas iniciais e uma fita cortada. A etiqueta manda devolver quando Lídia voltar da Câmara dos Testemunhos.'},
    'encosta_sealed_record': {'name':'Termo de custódia de Inês','color':(212,195,152),
        'description':'Inês entregou o rol à Câmara. Uma margem acusa retenção de identidades; outra cita proteção contra requisições de ambas as escoltas. Referência conservada mesmo se a folha foi entregue.'},
    'chamber_plan': {'name':'Planta da Câmara dos Testemunhos','color':(112,148,139),
        'description':'Escarpa acima do Posto de Convalescença da Encosta. Arco norte e selo de três arcos. R-17 autoriza a passagem; o procedimento não é descrito.'},
    'encosta_receipt': {'name':'Recibo de encaminhamento — Encosta','color':(174,165,128),
                       'description':'Livro do Vale, terceira vigília. R-17 / N-04. Reenvio ao Posto de Convalescença da Encosta; responsável não identificado.'},
    'namar_order_copy': {'name':'Segunda via — ordem de Namar','color':(183,154,101),
                        'description':'Gaveta 7. Operação N-04, autoridade R-17. Fechamento da travessia durante a retirada.'},
    "escort_token": {"name": "Identificação R-17", "color": (172,143,85),
                     "description": "Peça pessoal gasta, marcada R-17. Reconhecida no alojamento do Posto Norte."},
}


def quest_item(item_id):
    return {"id":item_id, "amount":1, "type":"quest", **QUEST_ITEMS[item_id]}


def consumable(item_id, amount=1):
    definition = CONSUMABLES[item_id]
    return {"id": item_id, "name": definition["name"], "amount": amount,
            "color": definition["color"]}


from story.lacre_content import DOCUMENTS
QUEST_ITEMS.update({uid:{"name":name,"color":(174,158,114),"description":" ".join(lines)} for uid,(name,flag,lines) in DOCUMENTS.items()})
QUEST_ITEMS["lacre_lead"]={"name":"Guia de cotejo — Mosteiro da Vigília","color":(157,173,166),"description":"A revisão da quinta vigília foi enviada à Mesa de Revisão do Mosteiro da Vigília. Procurar a matriz e a via integral. A identidade do responsável continua ausente."}
