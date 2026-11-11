# Capítulo II — O Preço da Memória
## Parte B — O Preço do Esquecimento

Continuação direta da Parte A, exclusivamente em `pygame/`. A entrada da **Câmara dos Testemunhos**, na Escarpa, agora permite entrar com `E` depois do encerramento da Parte A. Não há repetição da abertura do capítulo. O Capítulo III não é iniciado nem possui mapa novo.

### Instalação e circulação

Os cinco setores servem a uma mesma finalidade: receber depositantes, operar a custódia, conservar documentos separados de ordens militares, proteger o acesso e manter o lacre.

| Setor | Conteúdo e acesso |
| --- | --- |
| Vestíbulo das Inscrições | Inscrições, sinais de uso recente, guardião, eco e primeiro mecanismo. O vestígio demonstra tigela → lamparina → nome. |
| Galeria dos Ecos | Salão alongado, pilares, faixas refletoras e três vestígios da mesma operação. Passagem → acionamento → custódia abre o arquivo. |
| Arquivo Interditado | Estantes com lacunas concentradas, mesas, registros principais, compartimento sob o rodapé, caderno de Lídia e trava da escada de serviço. |
| Câmara dos Guardiões | Vigia dos Registros, instrução sobre sua proteção, marcas de confronto e descanso liberado após a vitória. |
| Núcleo do Lacre | Estrutura de contenção, documentos sobrepostos, âncoras, Iriel, confronto em duas fases e flashback central. |

Os retornos entre setores usam as portas existentes. A escada destravada no arquivo leva ao vestíbulo. Após a decisão final, a manutenção do núcleo também permite descer ao vestíbulo, sem refazer os puzzles. A saída passa pela Escarpa e retorna à Encosta. Plantas com recortes em degraus, pisos diferentes, circulação central, depósitos laterais e espaços de combate evitam depender de um labirinto. As pegadas da Parte A, a lamparina usada e os registros revistados mantêm a presença recente sem identificar um visitante adicional.

### Ressonância, mecanismos e segredos

A mecânica da Parte A foi ampliada, não substituída. Os novos pontos reutilizam `ResonancePoint`, a mesma tecla, sequência, controle de input e flags de conclusão. Silhuetas incompletas e símbolos que aparecem em etapas mostram ações antigas; os fechos são operados no presente. Não há viagem no tempo.

São seis novos vestígios: abertura do vestíbulo, três partes da operação da galeria, compartimento do arquivo e memória central. Depois de vistos, os pontos deixam de iniciar cutscenes e oferecem uma transcrição curta com a pista necessária. Os puzzles têm iluminação dos fechos assentados, aviso de erro e progresso salvo. Errar reinicia apenas a tentativa atual.

O painel do rodapé pode ser descoberto pelo desgaste e pela fita; seu vestígio é uma pista opcional. O compartimento contém duas poções e um éter. O caderno adicional liga Lídia, o pingente e a conservação de nomes, sem garantir o destino das pessoas. Recompensas, documentos e atalhos permanecem registrados.

### Defensores e Custódio

- **Guardião de custódia:** corpo de pedra articulado, abertura de registros no peito, proteção lateral e ataque frontal preparado.
- **Eco instável:** manto fragmentado, rosto cerâmico e movimento lateral alternado. A forma menos definida reduz o dano recebido, sem invulnerabilidade; o período nítido permite dano normal.
- **Vigia dos Registros:** proteção mais elaborada, ataque direto, arco amplo e descarga de guarda que cobre uma faixa frontal mais estreita. A abertura do peito fica protegida durante preparação/contato; a recuperação permite dano normal.
- **Iriel — Custódio do Lacre:** rosto grisalho, cicatriz, manto dividido e arma proporcional. Reconhece a impressão de R-17, mas não conhece todas as lembranças do protagonista. Protege nomes de pessoas vivas porque testemunhos já foram tratados como listas de alvos.

A primeira fase de Iriel alterna corte, arco frontal e investida de direção travada, conforme distância e sequência. A metade da vida interrompe o ataque por 80 ticks e desperta o núcleo. Na segunda fase, cortes deixam um setor residual visível: **34 ticks de aviso antes de oito ticks de contato**, com alcance limitado e um acerto por eco. As duas âncoras reduzem parcialmente o dano recebido por Iriel; romper cada conexão com `E` enfraquece a proteção. Nenhuma delas torna o boss invulnerável. Preparação, contato e recuperação usam poses próprias e setores de colisão orientados, em vez de acertar todo o retângulo de debug.

São **40 novas folhas de sprites**, com idle, passos, preparação, corte, arco, investida, dano, transição e derrota nas quatro direções. Elas usam células 80×64, pés na linha 46 e escala inteira 2×. Os sprites anteriores e o corte lateral do protagonista não são reconstruídos. A queda de Iriel termina antes da conversa; sua imagem caída continua no núcleo. Ele permanece vivo, sem reaparecer como adversário após carregar.

### Evidências e encerramento

Três documentos no arquivo explicam a finalidade de preservar/isolar testemunhos, as requisições militares e a admissão de R-17. A ficha traz a impressão da peça pessoal e remete à segunda via N-04 da gaveta 7, já estabelecida no Capítulo I. Todos podem ser lidos em ordem livre.

Após o confronto, o original da terceira vigília confirma que o protagonista **autorizou voluntariamente o primeiro lacre**. Uma folha da quinta vigília foi posta sobre ele, com outra abrangência e sem nova impressão de autorização: existe uma **segunda intervenção distinta**. A evidência não identifica seu autor nem prova que o protagonista foi consultado. A memória confirma a decisão sobre o primeiro pedido e termina antes do resultado; não atribui a segunda intervenção à voz presente no primeiro procedimento.

A escolha final permite preservar a cópia ou compartilhar com Inês somente as autorizações, mantendo os nomes protegidos. Ambas concedem o **Medalhão de Custódia**, acessório com **+1 Vitalidade e +1 Magia**, ícone próprio e descrição; o bônus segue as regras existentes de equipamento. A guia aponta uma única pista: **Mesa de Revisão do Mosteiro da Vigília**, onde ficaram a matriz do selo e a via integral da revisão.

No retorno, Inês reage à decisão sobre seu termo na Parte A e à escolha atual; a notícia de Mara preserva a consequência de Namar. A cópia compartilhada permanece disponível na reação de Inês. A cena solitária é acionada no banco a leste do posto, com pausas, referência à escolha e cartela de conclusão. O movimento é restaurado; o próximo objetivo aponta o Mosteiro, mas não inicia o Capítulo III.

### Persistência e recuperação

O save mantém a versão 1 e aceita a progressão anterior. Flags agrupadas validam acesso aos setores, documentos, fechos, ecos, segredos, vitória, escolhas, recompensa e conclusão. Não há coleta infinita nem repetição obrigatória de memórias. O carregamento filtra os defensores derrotados e restaura a geometria das portas.

A vitória do Vigia libera descanso e uma posição segura de recuperação no núcleo. Salvar manualmente durante o confronto principal segue o bloqueio já existente de boss ativo. A transição à segunda fase cria um autosave de **checkpoint da fase**, com 400 HP e estado das âncoras; não é um retrato de cada tick da luta. Carregar esse checkpoint retoma a segunda fase. Escolher continuar após morrer reconstrói o encontro não concluído com vida cheia, primeira fase, âncoras restauradas e sem setores residuais. Vitórias concluídas permanecem concluídas. HP/SP, câmera e input voltam ao estado válido.

O padding 80×64 comporta toda a arma nas quatro direções sem alterar o tamanho do corpo. Foram verificadas as bordas dos frames e a variação real de idle, transição e golpes.

Texturas são preparadas na entrada; arquitetura, sprites, flashes, formas translúcidas e fontes são reutilizados. Os efeitos de combate têm duração e quantidade limitadas. Não há assets sonoros adequados no pacote atual; a expansão mantém apresentação sóbria, sem sons improvisados ou trilhas externas.

### Verificação e roteiro manual

Testes específicos em `tests/test_lacre.py` cobrem pistas consultáveis, erro/retry, save parcial, registros únicos, secret/atalho, aproximação livre de todos os objetos, resistência/vulnerabilidade, hit de espada, transição, âncoras, eco atrasado, vitória, recuperação, escolhas, equipamento e conclusão. O teste integrado percorre **a Parte A e a Parte B no loop real**, com renderer, transições, duração normal dos ecos, escolhas explícitas, contato real de espada, autosave, reload e movimento restaurado. O dano do jogador é elevado apenas na fixture para encurtar encontros; isso não mede a dificuldade normal.

```powershell
python -m unittest tests.test_lacre -v
python -m unittest discover -s tests -v
python tools/draw_lacre_cast.py
python tools/review_lacre.py
```

A suíte completa passou com **163 testes**. Depois dos ajustes finais, **11 testes direcionados** passaram. O percurso integrado também força um contato fatal de eco, opera a tela de derrota e verifica que Continuar reconstrói o boss com vida cheia, primeira fase, posição segura e efeitos limpos antes de seguir até o fim. A inspeção automatizada confirma margens livres, quatro direções e poses diferentes nas folhas de animação.

Os logs ficam em `verification/`; mapas, diálogos, ecos completos, ataques completos, fase, escolha, flashback e encerramento ficam em `tools/visual_checks/lacre/`. A ferramenta utiliza o renderer de produção e saves temporários, sem substituir o save do jogador.

Roteiro manual curto: carregar a Parte A concluída → entrar pela Câmara → experimentar erro e acerto nos dois mecanismos → consultar novamente um vestígio → explorar rodapé/escada → observar e enfrentar o Vigia → descansar → enfrentar Iriel e romper âncoras → morrer/continuar ou carregar o checkpoint → cotejar as folhas e ouvir a memória → escolher a guarda da cópia → voltar por manutenção → falar com Inês → examinar a matriz no banco → salvar/carregar e confirmar movimento, recompensa e objetivo.

Pendência de validação: playtest humano prolongado de dificuldade, ritmo e percepção narrativa. A estrutura implementada encerra o Capítulo II; o próximo conteúdo é o Mosteiro da Vigília, no Capítulo III.
