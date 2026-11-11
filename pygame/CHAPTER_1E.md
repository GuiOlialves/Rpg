# Capítulo 1E — O Peso das Escolhas

O bloco continua a pista de Edrin: a casa de pedágio da **Ponte de Namar, na margem seca**. Não revela o nome, a patente completa ou a responsabilidade do protagonista pelo colapso. O Depósito de Registros indicado no encerramento é o destino do 1F e ainda não foi construído.

## Região e investigação

`namar` tem 1536×960 pixels. Rio, pilares quebrados da ponte, pedágio sem teto, barricadas, carroça, padaria destruída, abrigo e uma despensa em ruínas substituem a composição de floresta. As paredes e props sólidos têm colisão correspondente. Duas entradas curtas no pedágio e passagens ao redor das barricadas permitem aproximação e flanqueamento.

Após o encerramento do 1D, uma passagem pela borda baixa da Trilha do Posto chega à margem seca. É possível voltar pela mesma conexão após concluir o encontro. Antes do conflito, a exploração é livre e sem inimigos ativos:

- O livro de travessia associa o pedágio à escolta vermelha e à marca R-17; a página da operação falta, mas há indicação de uma segunda via.
- As contas de uma padaria registram famílias e entregas interrompidas. Uma anotação diz que a travessia fechou com pessoas ainda na fila.
- Uma despensa lateral guarda duas ervas opcionais, concedidas uma única vez.

As duas pistas principais precisam ser lidas até o fim antes de acionar o conflito junto à carroça. Mara e Téo podem ser abordados antes disso; suas conversas explicam a vida e as necessidades deles, sem entregar uma missão genérica.

## Sobreviventes e prioridade

**Mara** tinha uma padaria na outra margem e leva farinha para um abrigo. Usa xale ferrugem, trança, avental e bolsa remendada. Desconfia da marca militar, mas não sabe quem deu a ordem de fechar a travessia.

**Téo** conserta rodas e tenta conduzir a carroça com uma mão enfaixada. Tem faixa curta na cabeça, colete índigo e avental de trabalho. Quer chegar vivo e conhece a passagem baixa da muralha. Os dois têm atlas próprios de idle/caminhada, construídos a partir da geometria nativa do elenco. Nenhum atlas existente foi refeito.

Um portador de índices militares tenta passar antes de o portão fechar; dois guardas de requisição avançam para recolher a carga. No próprio painel de diálogo, **1** mantém o protagonista com Mara e Téo e **2** prioriza interceptar o portador. Os custos aparecem junto às opções. E e F4 não escolhem pelo jogador. A prioridade é persistida assim que o número é pressionado.

| Prioridade | Encontro e consequência | Informação/recompensa |
| --- | --- | --- |
| Proteger Mara e Téo | Os dois guardas avançam pelo pátio, entre carroça e barricadas. A farinha é preservada; o portador passa sem ser interceptado. | Os sobreviventes compartilham duas poções e uma ficha de entrega que acompanhava as caixas do pedágio. |
| Interceptar o portador | Os mesmos guardas bloqueiam a aproximação pelas ruínas do pedágio. Mara e Téo recuam pela abertura da muralha; deixam a carga e Téo agrava o ferimento no braço. Ambos sobrevivem. | O portador informa **N-04, série da retaguarda**, e orienta o retorno à carroça. Os sobreviventes ainda têm a ficha de entrega; não oferecem poções. |

Os encontros usam a espada, dash, máscaras de golpe, hitstop, impacto e telegraph atuais. Os guardas têm 64 HP e 6 de dano base. Há somente esse par, sem ondas. Durante o conflito a saída de retorno fica indisponível; derrota/continuar conserva a escolha e reinicia apenas os guardas ainda não derrotados. Carregar um save não ressuscita um guarda já registrado como derrotado.

## Memória e indício comum

Depois de conversar com os sobreviventes sobre o resultado, uma memória de cerca de 6,6 segundos mostra duas figuras militares sem identificação, cortes escuros, bandas e flashes discretos: **“Não podemos salvar todos.” / “Então escolha quem fica.”** O protagonista reconhece o silêncio posterior à decisão; o contexto e os interlocutores continuam desconhecidos.

A ficha de entrega aponta para **“Livro de Ordens — travessia de Namar. Segunda via: Depósito de Registros da Margem Seca. Gaveta 7.”** É uma referência de arquivamento, não o conteúdo da ordem. As reações e a posição dos sobreviventes continuam diferentes depois do encerramento, mas os dois caminhos recebem o mesmo objetivo de **Ecos da Guerra**:

> Encontre a segunda via da ordem de Namar no Depósito de Registros da Margem Seca.

## Save e checkpoints

As 16 flags booleanas do bloco são `namar_entered`, `namar_military_clue`, `namar_civilian_clue`, `namar_cache_found`, `namar_survivors_met`, `namar_choice_protect`, `namar_choice_pursue`, `namar_supplies_lost`, `namar_enemy_0_defeated`, `namar_enemy_1_defeated`, `namar_combat_completed`, `namar_dispatch_detail`, `namar_aftermath_seen`, `namar_memory_seen`, `namar_record_lead_found` e `namar_completed`.

Chegada, investigação, encontro/decisão pendente, escolha, derrotas, referência do portador, consequências, memória e encerramento solicitam autosave. A validação rejeita escolhas simultâneas, progressão fora de ordem e informações ainda não obtidas. Saves anteriores mantêm as flags ausentes como falsas. O objetivo e a cena pendente são derivados das flags; carregar depois das consequências retoma a memória ou o encerramento sem repetir poções ou diálogos já concluídos.

## Validação e revisão

`python -m unittest tests.test_namar -v` cobre os dois resultados, entradas do diálogo, escolha explícita, segredo opcional, checkpoints, saves inválidos, circulação, chegada pela trilha, telegraph/dash e duas execuções do loop real com ataques, impacto, autosave e F9. Os testes dirigem o personagem automaticamente; não substituem um playtest manual completo.

Também foram verificados `tests.test_edrin`, `tests.test_save_manager`, `tests.test_combat` e `tests.test_character_visuals` para a continuidade do 1D, compatibilidade de saves e preservação do combate/arte anteriores.

`python tools/review_namar.py` renderiza mapa, escolha, encontros, memória e os dois desfechos com o renderer do jogo, sem usar o save real. PNGs, storyboard, GIF e flags dos resultados ficam em `tools/visual_checks/namar/`. `python tools/draw_namar_survivors.py` reconstrói somente os quatro novos atlas de Mara e Téo.

O 1E termina nesse indício. A continuação no depósito está documentada em [CHAPTER_1F.md](CHAPTER_1F.md).
