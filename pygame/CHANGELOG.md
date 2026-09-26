# Histórico de atualizações — O Vale (Pygame)

Resumo breve das mudanças por versão. O histórico reflete os marcos do projeto; versões sem tag Git foram registradas como marcos, não como releases formais.

## 0.1 — Base do projeto

- Versão Pygame separada do material do GameMaker e identificada como 0.1; a indicação antiga de 0.5 foi corrigida.
- Base jogável com exploração, combate, regiões, NPCs, missão inicial, inventário e equipamentos.

## 0.11

- Dash direcional e ajustes de combate e recuperação de SP.
- Atributos principais e estatísticas derivadas passaram a influenciar o personagem e o combate.
- Save/Load estruturado, com validação e restauração do progresso.

## 0.12

- Rebalanceamento do combate, recuperação entre golpes e melhorias nos padrões dos inimigos.
- Tela de derrota com opções para continuar, carregar o save ou sair.
- Ajustes de fluxo e testes para combate e derrota.

## 0.13

- Feedback visual para Dash indisponível por falta de SP ou recarga.
- Avisos da interface reorganizados para melhorar a leitura.
- Save inválido com HP zero passou a ser rejeitado, evitando carregar uma partida derrotada ou substituir um save válido.

## 0.2

- Refatoração incremental da estrutura em `core/`, `entities/`, `systems/`, `story/`, `world/` e `ui/`, preservando `python main.py` e os saves existentes.
- Prólogo 1: abertura, despertar, exploração da casa, silhueta, chegada do morador e ativação da missão dos Slimes.
- Polimento visual da casa e da Vila, catálogo e reutilização de assets existentes.
- Reentrada funcional na casa, colisões das construções mais precisas, correção do alinhamento dos sprites civis e regressões de Save/Load, skip e progressão da primeira Floresta.
