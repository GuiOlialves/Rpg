# Capítulo 1D — O Homem que Deveria Estar Morto

O bloco começa na saída lateral do Posto de Vigia e termina após o encontro com Edrin. A Ponte de Namar é uma pista; seu destino não foi construído.

## Personagem e conversa

Edrin é um veterano da antiga escolta vermelha. Guardava a retaguarda e recebia ordens do protagonista. Tem respeito cauteloso, receio e uma dúvida que não resolveu: se deveria ter obedecido à última ordem em Namar. É econômico nas palavras e presta atenção aos arredores antes de responder.

Seu sprite próprio usa células 32×36, pivô (16,34), escala inteira de 2× e cinco animações: descanso, mão na arma, alerta, recuo e caminhada ferida. Cabelo grisalho, barba curta, cicatriz, manga vermelha desbotada, marcas da insígnia retirada, equipamento gasto e joelho enfaixado distinguem sua silhueta. A fonte dos atlas é `tools/edrin_pixel_art.py`.

O encontro começa com silêncio, “Não.”, outra pausa e “Não pode ser.”. Edrin recua antes de dizer “Você está morto.”. A identificação R-17 o leva a perceber a amnésia. Ele afirma ter visto o protagonista morrer, mas descreve o desaparecimento durante o colapso da Ponte de Namar, entre fumaça e rio; nenhum corpo foi encontrado.

Ele confirma “Você dava as ordens.”, reconhece a descrição do Oficial Vermelho e considera deliberada sua partida. A revelação principal é anterior ao colapso: o protagonista pedira que Edrin deixasse de usar seu nome e já procurava uma forma de esquecer. Edrin não sabe o motivo desse pedido. Sabe o que ocorreu na operação, mas não conta: não confia no homem diante dele e teme ser ouvido. Não há confirmação de massacre, traição ou responsabilidade por morte de inocentes, nem revelação do cargo completo ou do nome do protagonista.

## Percurso e encerramento

`pursuit` é uma trilha de 1280×768, percorrida em menos de oito segundos de caminhada. Pegadas irregulares, sangue recente, galhos quebrados e uma tira de uniforme mostram que alguém ferido saiu do posto. Duas observações opcionais usam a interação normal com E. Não há combate adicional.

A conversa é avançada com E; os silêncios têm duração própria. Movimento, ataque, dash e menus ficam bloqueados. Dois soldados azuis aparecem no caminho superior, com passos discretos. Antes de escapar vivo pelo arvoredo, Edrin indica **a casa de pedágio da Ponte de Namar, na margem seca**, onde o protagonista deu sua última ordem. A separação deixa o personagem disponível para encontros futuros.

O protagonista fica sozinho com R-17, pergunta “Do que eu estava fugindo?” e recebe o objetivo de **Ecos da Guerra: “Descubra o que aconteceu na Ponte de Namar.”** A saída futura apenas informa que a trilha termina no barranco. Não existe região Namar neste bloco.

## Persistência

| Flag | Estado persistido |
| --- | --- |
| `pursuit_entered` | Entrada na trilha após a pista do posto |
| `pursuit_trace_found` | Rastro ou tecido examinados; observação opcional |
| `edrin_met` | Reconhecimento inicial concluído |
| `edrin_name_known` | Identidade de Edrin apresentada |
| `edrin_death_revealed` | Testemunho de sua suposta morte ouvido |
| `namar_event_named` | Colapso da Ponte de Namar mencionado |
| `edrin_authority_revealed` | Autoridade sobre a escolta confirmada |
| `edrin_officer_recognized` | Relação com o Oficial Vermelho discutida |
| `edrin_forgetting_revealed` | Busca consciente por esquecimento revelada |
| `pursuit_patrol_heard` | Interrupção azul presenciada |
| `namar_clue_received` | Casa de pedágio e margem seca indicadas |
| `edrin_escaped` | Edrin saiu vivo |
| `edrin_encounter_completed` | Encerramento e novo objetivo concluídos |

Cada trecho completo da conversa solicita autosave. Revelações são validadas em ordem; identidade, testemunho e evento são um único checkpoint. Carregar durante a cena retoma o próximo trecho pendente. Carregar após a conclusão mantém Edrin ausente e não repete a conversa. O F4 já existente conclui a cena por uma operação idempotente. Saves anteriores continuam compatíveis; nenhuma gravação real do jogador é usada pelos testes ou previews.

## Validação e previews

- `python -m unittest tests.test_edrin -v`: oito testes focados no percurso, rastreamento, pausas/recuo, diálogo inteiro, patrulha/fuga, objetivo, checkpoints e estados inválidos. Um deles executa o loop real desde o posto, verifica bloqueio de ataque/dash/inventário, autosave e carregamento sem repetir o encontro.
- `python -m unittest tests.test_watchpost tests.test_save_manager -v`: 21 testes da conexão do posto, investigação, combate existente e compatibilidade de Save/Load.
- `python tools/review_edrin.py`: renderiza as 55 falas com o renderer do jogo. Previews em `tools/visual_checks/edrin/`: trilha, poses, oito cenas, storyboard, objetivo e GIF da conversa completa. O tempo de leitura do GIF é ilustrativo; no jogo, E controla as falas.

O próximo bloco não foi iniciado.
