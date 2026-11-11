# Capítulo 1F — A Ordem Esquecida

Implementado somente em `pygame/`, como continuação da Gaveta 7 do **Depósito de Registros da Margem Seca**. O retorno e o encerramento estão documentados no [bloco 1G](CHAPTER_1G.md).

## Percurso

A saída norte da margem seca abre após `namar_completed`. O depósito tem entrada sinalizada, pequeno desembarque com carroça, recepção de madeira com mesa de triagem e papéis queimados, pátio de separação dos registros e sala seca protegida. O pátio comporta esquivas e mantém sólidos nas bordas, sem obstáculos no centro. Os lacres, peças de uniforme e folhas arrancadas mostram buscas das duas facções.

As duas fontes iniciais devem ser lidas antes do confronto. Papéis queimados são investigação opcional. A Gaveta 7 permanece inacessível até a derrota do veterano. A saída retorna a Namar; durante o combate, o portão do pátio fecha. Depois, o jogador pode sair e retomar a investigação sem repetir o confronto.

## Fontes e revelação

- **Relatório da retaguarda:** o intendente da R-17 atribui ao fechamento a proteção da coluna de feridos em retirada para o Vale. Sua conclusão depende dos sinais da margem seca; não observou o destino da outra margem.
- **Petição dos atravessadores:** Lia descreve famílias, carregadores e soldados ainda esperando quando as grades baixaram. Ela estava fora da cadeia de mensagens militares. A lista anexa foi retirada; o registro não responde o destino de todos.
- **Segunda via:** Livro de Ordens, Gaveta 7, operação **N-04**, autoridade **R-17**. Determina baixar as grades, suspender os embarques da margem oposta e manter o fechamento até a retirada dos feridos pela encosta. Registra que a autoridade recebeu o aviso de pessoas ainda esperando e confirmou a decisão. Nome raspado; folha do resultado removida.
- **Ficha do esquecimento:** encaminhamento com as mesmas referências R-17/N-04, recibo anterior ao registro do colapso e indicação de envio ao Vale. Responsável e destinatário queimados. Confirma a conexão documental e preserva a cronologia relatada por Edrin; não explica o procedimento.

A escolha do 1E permanece intacta. Quem interceptou o portador reconhece **N-04, série da retaguarda**, no relatório; quem protegeu a carga identifica a operação na ordem. As reflexões sobre Mara respeitam a farinha preservada ou perdida. Não há contagem de mortos nem conclusão definitiva sobre a justificativa militar.

## Soren

Veterano da retaguarda e irmão de Lia, tenta preservar os registros das famílias depois de permitir uma busca que terminou em destruição. A motivação é a proteção dos nomes e a desconfiança das duas facções. Não reconhece magicamente o protagonista e não entrega a revelação principal em uma confissão.

Possui sete atlas próprios de 48×40 pixels, pivô `(24,36)`, escala inteira 2×, manto dividido, ombreira reforçada, armadura gasta, cabelo grisalho e barba. Corpo e arma compartilham coordenadas da mão. A lâmina conserva 30 pixels nativos. Máscaras seguem a lâmina de cada frame ativo; rastros curtos mostram apenas o trecho percorrido.

| Golpe | Preparação | Ativo | Recuperação | Dano |
| --- | ---: | ---: | ---: | ---: |
| Corte direto | 22 frames | 5 | 27 | 9 |
| Corte amplo | 40 frames | 8 | 42 | 13 |
| Avanço | 32 frames | 14 | 38 | 11 |

Valores no combate existente de 60 Hz. Todos travam a direção na preparação. O avanço usa três subpassos por frame para respeitar paredes. Golpes comprometidos recebem dano sem perder o aviso; a recuperação permite contra-ataque. Soren tem 210 HP, sem alterar outros inimigos. Ao chegar a 1 HP, rende-se, ajoelha e larga a espada. Não concede drops aleatórios nem ressuscita ao carregar.

A câmera do pátio permanece fixa durante a luta. Barra no alto, objetivo oculto durante o confronto e efeitos de impacto já existentes mantêm a arena legível.

## Memória e encerramento

Após ler a ordem, um flashback de 11,1 segundos reconstrói a sala militar do pedágio de Namar, antes do colapso. O protagonista usa o mesmo rosto e proporções em um uniforme vermelho. Ouve o aviso **“Ainda há pessoas lá fora!”**, faz um gesto e ordena o fechamento. O corte escuro ocorre antes dos resultados.

A ficha é examinada depois da memória. O encerramento atualiza **Ecos da Guerra** para **“Volte ao Vale com a segunda via e procure Alden.”** A segunda via é um item de missão único. A conversa e as consequências do retorno pertencem ao 1G.

## Persistência e validação

Flags: `archive_entered`, `archive_search_marks`, `archive_defense_report`, `archive_petition`, `archive_confrontation_started`, `archive_veteran_defeated`, `archive_order_obtained`, `archive_memory_seen`, `archive_forgetting_record`, `archive_completed`.

Entrada, documentos, início/derrota do confronto, memória e encerramento solicitam autosave. Saves anteriores continuam na versão 1, com flags ausentes falsas. A validação rejeita chegada sem a pista do 1E, confronto sem as duas fontes, revelações fora de ordem e ausência da segunda via obtida. Carregar retoma memória/encerramento pendentes; não duplica o item. Uma tentativa interrompida reinicia apenas o miniboss. Derrota/continuar recoloca o protagonista no pátio com recursos restaurados, mantendo documentos e a escolha anterior.

`tests.test_archive` cobre fontes, escolhas, documentos bloqueados, checkpoints, memória, rendição, item único, saves inválidos, rotas com colisão, passagem real de Namar, três preparações/esquivas, contato da lâmina, avanço contra parede, retomada após derrota e uma execução do loop real até autosave/F9 final. O piloto de teste dirige o personagem automaticamente; não substitui um playtest manual completo.

Também foram verificados `tests.test_namar`, `tests.test_edrin`, `tests.test_save_manager`, `tests.test_combat` e `tests.test_character_visuals`.

`python tools/draw_archive_veteran.py` reconstrói somente os sete atlas novos. `python tools/review_archive.py` captura o renderer do jogo, mapa, documentos, confronto, ataques completos, rendição, flashback e objetivo final em `tools/visual_checks/archive/`, sem usar o save real do jogador.
