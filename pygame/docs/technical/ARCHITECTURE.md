# Arquitetura técnica

## Pacotes e responsabilidades

- `main.py`: entry point pequeno e fachadas explícitas para compatibilidade com testes/consumidores antigos.
- `core/game.py`: inicialização e coordenação dos ciclos de evento, atualização, transição, save e renderização; mantém o estado mutável da sessão local à instância/execução.
- `core/input_handler.py`: converte teclado e mouse em comandos sem aplicar regras de gameplay.
- `core/config.py`, `core/assets.py` e `core/camera.py`: configuração, carregamento de imagens e enquadramento.
- `entities/`: estado/comportamento de `Player`, `Enemy`, `Drop` e `NPC`.
- `entities/interactable.py`: pontos estáticos examináveis com diálogo, alcance, condição e destino opcional; usam a mesma caixa e proximidade de NPCs.
- `systems/`: combate, ações de inventário, equipamentos, itens, progressão, quests e efeitos de diálogo sobre quests.
- `world/regions/`: composição da Vila, Floresta e Deserto; `world/world_manager.py` constrói regiões e resolve saídas/transições.
- `world/respawn.py`: escolha de posição segura e recuperação do jogador após derrota.
- `ui/`: HUD, menus, diálogo, tela de derrota, feedback de dano e composição visual de mundo/frame.
- `story/`: `StoryManager`, sequência temporizada reutilizável, fade, beats aprovados das Cenas 00 e 01 e `ArrivalScene` para a primeira saída da casa; `woke_up`, `saw_silhouette` e `slime_quest_started` persistem no save.
- `world/regions/home.py`: quarto inicial compacto com cama, espelho, espada/equipamento e porta examináveis; as paredes e móveis sólidos têm colisão.
- `environment.py` e `ambient.py`: texturas, camadas, sombras e efeitos ambientais compartilhados.
- `save_manager.py`: validação, serialização e gravação atômica do formato atual.
- `docs/`: documentação narrativa, de design e técnica.

## Dependências e fluxo

`main.py` chama `core.game.Game.run()`. Em novo jogo, `Game` inicia em `home` e bloqueia eventos de gameplay enquanto a sequência narrativa está ativa; apenas fechar a janela permanece disponível. Ao fim, grava `woke_up = true` e devolve o controle. Os examináveis da casa abrem a caixa de diálogo compartilhada; a porta usa `WorldManager` e o `FadeOverlay` existente. Na primeira saída de `home` para `village`, `ArrivalScene` bloqueia a jogabilidade, apresenta a silhueta e o morador, e inicia `forest_trouble` ao fechar o diálogo. As flags e quest são salvas juntas ao final da cena. `Game` também recebe comandos do `InputHandler`, coordena entidades e sistemas, e entrega o estado ao `GameRenderer`. Nenhum módulo de produção importa `main.py`.

## Regras para próximas mudanças

- Regiões constroem mapas e não controlam sistemas globais diretamente.
- UI apresenta estado e encaminha ações; não contém regras de gameplay.
- Dados de itens e inimigos devem ser separados do comportamento quando isso puder ser feito sem quebrar os contratos atuais.
- Evitar dependências circulares; os pacotes de domínio não importam `main.py` nem dependem da UI.

## Fachadas de compatibilidade

As fachadas pequenas na raiz mantêm imports antigos: `attributes.py`, `desert.py`, `dialogue.py`, `enemy.py`, `equipment.py`, `forest.py`, `game_over.py`, `items.py`, `npc.py`, `quest.py` e `village.py`. Os testes atuais ainda importam diretamente `attributes`, `enemy`, `equipment`, `items` e `quest`; mantê-las evita reescrever a suíte nesta etapa. As fachadas de `dialogue`, `game_over`, `npc` e das regiões podem ser removidas depois que consumidores externos migrarem e uma busca de imports confirmar que ninguém depende delas. `main.py` também conserva aliases usados pelos testes antigos. `save_manager.py` continua na raiz porque os testes o importam e substituem `SAVE_PATH` diretamente.

## Dívidas técnicas restantes

- `core/game.py` ainda coordena eventos de interação (NPCs/baús), ciclo de vida do save e alguns estados de sessão; regras específicas de combate, inventário, diálogo, renderização e região já foram extraídas. Uma classe `GameState` formal pode ser introduzida quando outro sistema precisar consumir esse estado sem ampliar os parâmetros do coordenador.
- `save_manager.py` permanece na raiz; movê-lo exigiria migrar seus imports e pontos de monkeypatch sem alterar o schema.
- `StoryManager` mantém flags booleanas simples; `save_manager.py` preenche `saw_silhouette` e `slime_quest_started` como `false` em saves antigos que ainda só guardavam `woke_up`.
- `data/` não foi criado: os dados continuam junto dos sistemas atuais até uma separação que tenha consumidores concretos.
