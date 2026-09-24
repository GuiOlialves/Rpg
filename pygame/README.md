# O Vale — RPG em Pygame

**Versão 0.5** · RPG 2D top-down desenvolvido em Python com Pygame CE.

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
| `E` | Conversar, aceitar/entregar a missão ou abrir um baú |
| `V` | Abrir atributos e equipamentos |
| `I` | Abrir inventário |
| `1`–`4` | Distribuir pontos de atributo ou usar a ação do item selecionado |
| `Esc` | Fechar a tela atual ou sair |

## Estrutura

- `main.py`: janela, personagem, loop principal e interface.
- `village.py`, `forest.py` e `desert.py`: composição das regiões.
- `environment.py` e `ambient.py`: texturas, camadas, sombras e efeitos ambientais.
- `enemy.py`, `npc.py`, `quest.py`, `equipment.py` e `dialogue.py`: lógica dos sistemas do jogo.
- `assets/` e `sprites_meu/`: imagens necessárias para executar o projeto.

## Assets e créditos

Os sprites são mantidos separados do código-fonte e preservam a estrutura de pastas usada pelo jogo. Os textos de licença disponíveis para os conjuntos da vila e do deserto acompanham a publicação em `licenses/`. Veja `ASSET_CREDITS.md` para os conjuntos usados. Consulte as licenças originais antes de redistribuir os assets separadamente ou utilizá-los em outro projeto.

## Estado do projeto

A versão 0.5 é um projeto em desenvolvimento. O jogo ainda não é distribuído como executável independente; execute-o pelo Python seguindo os passos acima.
