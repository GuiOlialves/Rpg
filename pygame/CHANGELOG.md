# Histórico de atualizações — O Vale (Pygame)

Resumo breve das mudanças por versão. O histórico reflete os marcos do projeto; versões sem tag Git foram registradas como marcos, não como releases formais.

## 0.3

- Prólogo 3A: continuação do confronto entre o protagonista, o Oficial Vermelho e o comandante azul, com a revelação do nome de cinco letras ainda encoberto.
- Prólogo 3B: combate de boss contra o Oficial Vermelho, com barra própria, fases de pressão crescente e derrota não letal ao chegar a 1 HP.
- Prólogo 3C: promessa e memória da silhueta, fuga do Oficial, epílogo e cartão de conclusão do prólogo.
- Save/Load, tentativas após derrota e F4 preservam estados seguros da progressão narrativa.

## 0.23

- Versão exibida ao abrir o jogo atualizada para 0.23.
- Overlay F3 ampliado com diagnóstico de região, progresso narrativo, quests, cenas, jogador e entidades; hitboxes e gatilhos ficam visíveis para depuração.
- Tropa azul da marcha, soldados caídos e comandante passaram a compartilhar sprites militares coerentes, com escala e variações visuais ajustadas.
- Soldados vermelhos ficam visíveis antes do contato e mantêm os mesmos personagens ao passar da apresentação para o combate.
- Corpo do comandante azul aparece no cenário pós-marcha; a cena final continua condicionada aos confrontos concluídos e à insígnia.

## 0.22

- Menu F2 de checkpoints narrativos para iniciar testes nos marcos 2A–2E.
- Checkpoints configuram dependências de quests e história sem alterar o save normal; autosave, F5 e carregamento ficam protegidos durante a sessão de debug.
- Opção para resetar o estado de teste sem afetar a campanha.

## 0.21

- HUD, barras de recursos e objetivo atual receberam molduras, espaçamento e hierarquia visual mais consistentes.
- Menus de personagem e inventário foram reorganizados visualmente, com retratos ampliados e ícones compactos para os itens disponíveis.
- Diálogos, prompts de interação, overlays narrativos e tela de derrota usam apresentação mais legível e alinhada à paleta da interface.
- Mantida a composição atual da casa e da Vila, com as correções de props e camadas já presentes na versão 0.2.

## 0.2

- Refatoração incremental da estrutura em `core/`, `entities/`, `systems/`, `story/`, `world/` e `ui/`, preservando `python main.py` e os saves existentes.
- Prólogo 1: abertura, despertar, exploração da casa, silhueta, chegada do morador e ativação da missão dos Slimes.
- Continuação do prólogo (2A–2E): retorno após os Slimes, conversa com Alden, investigação da casa e primeira memória do pingente; marcha azul, campo de batalha na Floresta, insígnia vermelha e encontro com o Oficial Vermelho.
- Flags narrativas e progresso do prólogo preservados no Save/Load; F4 conclui as sequências roteirizadas em estado consistente.
- Polimento visual da casa e da Vila, catálogo e reutilização de assets existentes.
- Ajuste local de props, footprints e camadas na casa e na praça da Vila.
- Reentrada funcional na casa, colisões das construções mais precisas, correção do alinhamento dos sprites civis e regressões de Save/Load, skip e progressão da primeira Floresta.

## 0.13

- Feedback visual para Dash indisponível por falta de SP ou recarga.
- Avisos da interface reorganizados para melhorar a leitura.
- Save inválido com HP zero passou a ser rejeitado, evitando carregar uma partida derrotada ou substituir um save válido.

## 0.12

- Rebalanceamento do combate, recuperação entre golpes e melhorias nos padrões dos inimigos.
- Tela de derrota com opções para continuar, carregar o save ou sair.
- Ajustes de fluxo e testes para combate e derrota.

## 0.11

- Dash direcional e ajustes de combate e recuperação de SP.
- Atributos principais e estatísticas derivadas passaram a influenciar o personagem e o combate.
- Save/Load estruturado, com validação e restauração do progresso.

## 0.1 — Base do projeto

- Versão Pygame separada do material do GameMaker e identificada como 0.1; a indicação antiga de 0.5 foi corrigida.
- Base jogável com exploração, combate, regiões, NPCs, missão inicial, inventário e equipamentos.
