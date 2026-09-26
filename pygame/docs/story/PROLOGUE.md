# Prólogo

O roteiro-base canônico foi fornecido pelo usuário. A implementação atual cobre a CENA 00 — Escuridão, a abertura da CENA 01 — O Despertar, a exploração inicial da casa e a chegada à Vila com a CENA 02 — A Silhueta e a CENA 03 — O Primeiro Pedido.

Na casa, somente espelho, espada/equipamento e porta estão ativos. A primeira saída inicia automaticamente a silhueta, o grito “AVENTUREIRO!”, a corrida de um morador e o diálogo canônico do primeiro pedido. Ao fim, ativa a quest já existente `forest_trouble` (“Problemas na Floresta”) e devolve o controle na Vila. O combate da missão e a conversa com Alden continuam fora do escopo destas cenas. Consulte `story/prologue.py` para os fragmentos temporizados do Bloco 1A e `story/arrival_scene.py` para as fases, falas e animação da chegada.
