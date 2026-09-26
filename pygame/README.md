# O Vale — RPG em Pygame

**Versão 0.2** · RPG 2D top-down desenvolvido em Python com Pygame CE.

Veja o [histórico de atualizações](CHANGELOG.md) para um resumo breve de cada versão.

O jogo reúne exploração, combate e progressão em três áreas conectadas: Vila do Vale, Floresta Mística e Deserto das Dunas. O prólogo acompanha o protagonista da missão dos Slimes até o encontro com o Oficial Vermelho, passando pela investigação da casa e pelas primeiras memórias. A versão também inclui equipamentos, inventário, atributos e salvamento da recompensa dos baús do deserto durante a sessão. O encontro antigo com o Guardião permanece no código, mas não é ativado pela conclusão da missão inicial.

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
| `F4` | Durante uma cutscene, concluí-la imediatamente (atalho de desenvolvimento; aplica seus efeitos finais) |

Ao chegar a 0 HP, a tela de derrota permite continuar do ponto seguro da região, carregar o último save ou sair. Continuar restaura HP/SP, preserva a progressão e reinicia um encontro ainda não concluído com o Guardião. Não é possível salvar com HP zerado. Consumíveis compartilham uma recarga de 1,5 segundo.

## Estrutura

- `main.py`: ponto de entrada e fachada de compatibilidade.
- `core/`: loop/coordenador do jogo, roteamento de input, configuração, assets e câmera.
- `entities/`: jogador, inimigos, drops e NPCs.
- `systems/`: combate, diálogo/quests, ações de inventário, itens, equipamentos e progressão.
- `ui/`: HUD, inventário, menu de personagem, diálogo, derrota e renderização.
- `world/regions/`: construção da vila, floresta e deserto; `world/world_manager.py` registra builders e resolve transições.
- `story/`: sequências do prólogo e flags narrativas integradas ao Save/Load.
- `environment.py` e `ambient.py`: texturas, camadas, sombras e efeitos ambientais.
- `save_manager.py`: validação, gravação atômica e restauração do save.
- `docs/`: design, estrutura narrativa e documentação técnica.
- `assets/` e `sprites_meu/`: imagens necessárias para executar o projeto.

Os módulos legados na raiz, como `enemy.py` e `forest.py`, permanecem como fachadas para compatibilidade. Consulte `docs/technical/ARCHITECTURE.md` para as responsabilidades e as fachadas que ainda podem ser removidas futuramente.

## Assets e créditos

Os sprites são mantidos separados do código-fonte e preservam a estrutura de pastas usada pelo jogo. Os textos de licença disponíveis para os conjuntos da vila e do deserto acompanham a publicação em `licenses/`. Veja `ASSET_CREDITS.md` para os conjuntos usados. Consulte as licenças originais antes de redistribuir os assets separadamente ou utilizá-los em outro projeto.

## Estado do projeto

A versão 0.2 é um projeto em desenvolvimento. O jogo ainda não é distribuído como executável independente; execute-o pelo Python seguindo os passos acima. O carregamento é manual; o autosave acontece ao trocar de região, concluir a quest inicial e derrotar o Guardião. Saves inválidos não são sobrescritos automaticamente.

Os quatro atributos afetam HP, SP, ataque, defesa, poder mágico, velocidade, cadência e crítico. O menu `V` mostra os bônus de equipamento, os stats de combate e a prévia de cada ponto ao passar o mouse sobre `+`.

O combate foi ajustado para reduzir dano explosivo e permitir recuperação entre golpes. O Dash percorre até 99 pixels em 11 frames, custa 10 SP, tem 6 frames iniciais de esquiva e 39 frames de recarga. O SP começa a regenerar após quatro segundos sem gasto (1 ponto por segundo); Éter recupera SP imediatamente, respeitando a recarga global de consumíveis.
