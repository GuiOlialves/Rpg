# O Vale — RPG em Pygame

**Versão 0.13** · RPG 2D top-down desenvolvido em Python com Pygame CE.

O jogo reúne exploração, combate e progressão em três áreas conectadas: Vila do Vale, Floresta Mística e Deserto das Dunas. A versão inclui inimigos com animações, NPCs e diálogos, uma missão inicial com chefe, equipamentos, inventário, atributos e salvamento da recompensa dos baús do deserto durante a sessão.

## Executar

Requer Python 3.10 ou superior.

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Controles

| Tecla | Ação |
| --- | --- |
| `WASD` ou setas | Mover |
| `Espaço` | Atacar |
| `Q` | Dash (10 SP; curta esquiva na direção de movimento ou da última direção) |
| `E` | Conversar, aceitar/entregar a missão ou abrir um baú |
| `V` | Abrir atributos e equipamentos |
| `I` | Abrir inventário |
| `1`–`4` | Distribuir pontos de atributo ou usar a ação do item selecionado |
| Clique em `+` no menu `V` | Distribuir um ponto de atributo |
| `Esc` | Fechar a tela atual ou sair |
| `F5` | Salvar em `savegame.json` |
| `F9` | Carregar manualmente o save |
| `F3` | Exibir hitboxes de combate e avisos dos ataques |

Ao chegar a 0 HP, a tela de derrota permite continuar do ponto seguro da região, carregar o último save ou sair. Continuar restaura HP/SP, preserva a progressão e reinicia um encontro ainda não concluído com o Guardião. Não é possível salvar com HP zerado. Consumíveis compartilham uma recarga de 1,5 segundo.

## Estrutura

- `main.py`: janela, personagem, loop principal e interface.
- `village.py`, `forest.py` e `desert.py`: composição das regiões.
- `environment.py` e `ambient.py`: texturas, camadas, sombras e efeitos ambientais.
- `enemy.py`, `npc.py`, `quest.py`, `equipment.py` e `dialogue.py`: lógica dos sistemas do jogo.
- `attributes.py`: fórmulas dos quatro atributos, stats de combate, defesa e crítico.
- `items.py`: IDs e dados dos consumíveis.
- `save_manager.py`: validação, gravação atômica e restauração do save.
- `assets/` e `sprites_meu/`: imagens necessárias para executar o projeto.

## Assets e créditos

Os sprites são mantidos separados do código-fonte e preservam a estrutura de pastas usada pelo jogo. Os textos de licença disponíveis para os conjuntos da vila e do deserto acompanham a publicação em `licenses/`. Veja `ASSET_CREDITS.md` para os conjuntos usados. Consulte as licenças originais antes de redistribuir os assets separadamente ou utilizá-los em outro projeto.

## Estado do projeto

A versão 0.13 é um projeto em desenvolvimento. O jogo ainda não é distribuído como executável independente; execute-o pelo Python seguindo os passos acima. O carregamento é manual; o autosave acontece ao trocar de região, concluir a quest inicial e derrotar o Guardião. Saves inválidos não são sobrescritos automaticamente.

Os quatro atributos afetam HP, SP, ataque, defesa, poder mágico, velocidade, cadência e crítico. O menu `V` mostra os bônus de equipamento, os stats de combate e a prévia de cada ponto ao passar o mouse sobre `+`.

O combate foi ajustado para reduzir dano explosivo e permitir recuperação entre golpes. O Dash percorre até 99 pixels em 11 frames, custa 10 SP, tem 6 frames iniciais de esquiva e 39 frames de recarga. O SP começa a regenerar após quatro segundos sem gasto (1 ponto por segundo); Éter recupera SP imediatamente, respeitando a recarga global de consumíveis.
