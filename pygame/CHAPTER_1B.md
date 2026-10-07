# Capítulo 1B — A Antiga Estrada

O bloco ativa a saída oeste preparada no 1A. A conexão `old_road` usa o
registro existente de regiões e fades curtos nas duas direções. A estrada
tem o tamanho padrão de 2048 × 1152; bancos de pedra contêm a área útil e
o caminho faz curvas e uma volta antes do trecho militar. O retorno à
Vila coloca o jogador junto à saída oeste, sem repetir o 1A.

Os três momentos são uma aproximação tranquila do Vale, uma curva com
carroça destruída e uma abertura de combate, e um trecho com cercas,
equipamento militar e acampamento recente. O solo gasto, vegetação de
tons secos, rochedos e objetos humanos diferenciam a região da Floresta
Mística. Os novos objetos são desenhados em pixel art com escala inteira.
O protagonista e todas as suas animações permanecem os atuais.

Há quatro inimigos em três espaços: dois Slimes junto à carroça e dois
Errantes da Estrada separados. A variação do Guardião Errante usa a arte
atual, anda mais rápido e alterna dois cortes comuns com um golpe carregado
de preparação mais longa. Tem 72 HP e 6 de dano base. Não pertence a uma
facção; sua configuração é uma cópia local, sem alterar outros guerreiros.

Três desvios recompensam a exploração pelo sistema de baús existente:

- recuo arborizado: duas Ervas;
- abrigo em ruínas: um Éter, curativos usados e tecido vermelho;
- carroça lateral: uma Poção e um bilhete sobre deixar água junto ao marco.

Na estrada principal, um tecido com o símbolo vermelho permite reconhecer
sua passagem. A carroça avariada, mercadorias abertas, sangue seco e arma
partida mostram violência sem atribuir autoria. O abrigo e os curativos
sugerem cuidado com feridos. Mais tarde, um escudo azul deixa em aberto
quem passou primeiro e quem seguia quem.

A reação ao marco dura 1,96 s: uma impressão de botas andando, uma leve
alteração visual e “Continue andando.”, seguida de reconhecimento incerto.
Ela espera um momento seguro do combate e usa as botas do sprite atual.
Não mostra identidade, personagem novo ou flashback completo.

O acampamento final contém fogueira apagada, restos de comida, caixas,
tecido vermelho, curativos e pegadas recentes. Examinar seu mapa revela
“Reagrupar. Posto Norte”. Depois das pistas e da memória, o mirante mostra
o exterior do posto durante 2,45 s e atualiza **Ecos da Guerra** para
**Investigue o antigo posto de vigia.** `watchpost_future` prepara a
continuação junto à barricada. O interior não está implementado.

O save JSON continua na versão 1. Flags opcionais novas:

- `old_road_entered`;
- `road_red_clue_found`;
- `road_blue_trace_found`;
- `road_memory_seen`;
- `road_camp_found`;
- `watchpost_seen`;
- `road_enemy_0_defeated` até `road_enemy_3_defeated`.

Baús usam o conjunto já serializado de baús abertos, com IDs
`road_chest_turnout`, `road_chest_shelter` e `road_chest_caravan`.
Entrada, descobertas concluídas, recompensas e derrotas pedem autosave.
Reload restaura pistas desativadas, objetivo, baús abertos e inimigos
removidos. Saves anteriores continuam aceitos; novas flags ausentes são
falsas. A validação rejeita descobertas anteriores à entrada ou o posto
localizado sem as pistas necessárias.

Validação focada, sem suíte completa:

```powershell
python -m unittest tests.test_old_road tests.test_chapter1_return tests.test_save_manager tests.test_combat -q
python tools/review_old_road.py
```

Os dez testes novos incluem transição, spawn/respawn, navegação com a
hitbox real até todos os pontos, obstáculos, inimigos, telegraph/recovery,
interações, duração e repetição da memória, pista do posto, recompensas,
save/reload e o fluxo integrado do Game. As imagens e a memória animada
ficam em `tools/visual_checks/old_road/`. Todos os saves de teste são
temporários; a revisão visual não modifica o save real.
