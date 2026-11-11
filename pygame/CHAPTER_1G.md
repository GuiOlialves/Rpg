# Capítulo 1G — Ecos do Passado

Encerramento do **Capítulo I — Ecos da Guerra**, somente em `pygame/`. O Capítulo II não começa nesta versão.

## Retorno e consequências

Depois de concluir o depósito, a interação perto da saída permite voltar ao Vale pela estrada de serviço. É opcional: a saída para Namar e os caminhos existentes continuam disponíveis. O retorno usa a transição de região e o autosave existentes.

Mara e Téo estão no Vale, sem duplicatas em Namar. Se o protagonista protegeu a carroça, a farinha chegou ao abrigo e Téo pode cuidar da mão. Se perseguiu o portador, o abrigo repartiu seu estoque, a roda foi refeita e a recuperação demora mais. O índice continua sendo uma pista útil; não há julgamento automático, recompensa adicional ou alteração da escolha.

## Alden e a pista verificável

A conversa com Alden intercala falas e silêncio. O protagonista reconhece que confirmou a ordem depois do aviso; Alden não oferece absolvição nem uma sentença baseada em registros incompletos. A orientação é preservar as duas versões e procurar as pessoas envolvidas.

Alden reconhece o número de recebimento no verso da segunda via e abre o livro local. A entrada **R-17 / N-04**, da terceira vigília, confirma o reenvio ao **Posto de Convalescença da Encosta**. O recibo tem destino, selo e referência de entrega; não prova quem realizou um procedimento, nem se ele ocorreu. Examinar o livro adiciona um único item de missão. Nenhuma região nova é criada.

## Cena final

Na casa, examine R-17 e a segunda via sobre a mesa. Uma lembrança breve apresenta uma voz desconhecida: “Tem certeza de que deseja fazer isso?”. Há silêncio; o protagonista responde “Tenho.” e a cena corta. A identidade da voz, o método e o motivo do esquecimento permanecem abertos.

De volta à casa: **“Eu pedi para esquecer. Não vou deixar que isso responda por mim.”** Um fade apresenta **CAPÍTULO I CONCLUÍDO / ECOS DA GUERRA**, com a tipografia da abertura, e retorna à exploração.

## Persistência e continuidade

- `chapter1_final_returned`, `chapter1_final_alden_talk`: retorno e conversa concluídos.
- `chapter1_consequences_seen`: conversa opcional com os sobreviventes.
- `encosta_receipt_found`, `encosta_destination_known`: recibo e próximo destino, registrados juntos.
- `chapter1_final_memory_seen`, `chapter1_final_reflection_seen`: etapas da cena já assistidas.
- `chapter1_completed=true`, `chapter2_started=false`: conclusão após a cartela.

As etapas narrativas solicitam autosave. Carregar retoma a próxima etapa ao examinar a mesa; um capítulo concluído não repete o encerramento. A validação exige a sequência de revelações e o recibo físico, preservando saves antigos da versão 1. Escolha de Namar, documentos anteriores, segunda via e derrota de Soren continuam registrados. Alden tem diálogo posterior, sobreviventes conservam seu estado, os caminhos reabrem normalmente e a HUD passa a mostrar a pista da Encosta.

O painel F3 reconhece as cenas 1E, 1F e 1G sem interromper o jogo. Os testes antigos de interação da casa foram atualizados para o mobiliário atual; as rotas são percorridas com a colisão real do jogador.

## Validação

`tests/test_chapter1_ending.py` cobre o retorno opcional, as duas escolhas, conversa e recibo, checkpoints da memória/reflexão/cartela, validação de saves e o loop real até a exploração após carregar. O teste do loop também mantém F3 ativo.

`tools/review_chapter1_ending.py` usa o renderer do jogo para gerar storyboard, frames, GIF da sequência completa e relatório das duas escolhas em `tools/visual_checks/chapter1_ending/`. As imagens foram revisadas, incluindo posicionamento dos objetos na mesa, pausas, cartela e retorno ao mundo.

A suíte completa passou: **138 testes em 173 segundos**, incluindo os seis testes do 1G, continuidade 1A–1F, combate, prólogo e Save/Load. Comando: `python -m unittest discover -s tests -v`. O resultado final fica em `verification/chapter1_full_tests.log` (artefato local ignorado pelo Git).

## Limite do bloco

Encosta é apenas o próximo destino documentado. Não foram implementados mapa, personagens ou acontecimentos do Capítulo II. Também permanecem desconhecidos o desfecho completo da margem oposta, a identidade civil ligada a R-17 e a razão do pedido de esquecer.
