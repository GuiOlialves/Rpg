# Capítulo II — O Preço da Memória
## Parte A — As Vozes que Restaram

Implementação jogável desde a despedida de Alden até o limiar da Câmara dos Testemunhos. A pista continua sendo o **Posto de Convalescença da Encosta**, o recibo da remessa e a autorização R-17 apresentados em 1G. Os acontecimentos anteriores e as duas escolhas de Namar são preservados.

### Percurso e regiões

Depois de concluir o Capítulo I, fale com Alden na Vila. A conversa breve entrega uma poção uma única vez; a cartela do Capítulo II faz fade antes de devolver o controle. A placa junto à saída leste passa a permitir seguir para a Encosta.

- **Rota das Pedras Afundadas:** estrada irregular, riacho com ponte e vau, árvores retorcidas, estratos de rocha e marcos militares. O caminho principal é acompanhado por dois desvios: o depósito de provisões e o vau que conduz a um registro de transferência escondido. Predadores e criaturas de couraça protegem espaços distintos, com encontros evitáveis e obstáculos que permitem reposicionamento. Um banco abrigado restaura HP/SP e registra o checkpoint local.
- **Posto de Convalescença da Encosta:** antigas casas, enfermaria aberta, arquivo comunitário, poço, mesa com refeição interrompida, carroça, ferramentas e cercas. Telhados, soleiras, mobiliário, musgo e desgaste diferenciam as construções. O arco norte tem barreira visível; a chave acompanha a planta de custódia.
- **Escarpa dos Testemunhos:** subida e arena com rochas assimétricas diante de uma Câmara monumental incrustada na pedra. Uma tomada mais aberta mantém protagonista e fachada visíveis. Fogueira recente, pegadas e luz interior sugerem outra presença, sem identificá-la.

### Pessoas, investigação e decisão

**Inês** preserva os registros e espera por Lídia. Tem trança grisalha, óculos, roupa de trabalho e um caderno junto ao corpo. **Breno**, antigo vigia desconfiado, reconhece detalhes de autorização militar; uma notícia de Mara muda sua reação conforme a escolha de Namar. Nenhum deles conhece toda a história do protagonista.

O livro comunitário, o pingente de Lídia e o símbolo de custódia podem ser examinados em qualquer ordem. As três evidências se complementam e liberam o fragmento militar. É necessário ouvir ambos os moradores e os três primeiros ecos para acessar os fechos do armário.

O registro comunitário explica o rito **tigela → lamparina → nome**. Acionar os três símbolos nessa ordem abre um compartimento. Um erro solta apenas os fechos: documentos, ecos e conversas continuam registrados; a tentativa pode ser retomada, inclusive após carregar um save parcial.

O termo assinado por Inês contém anotações que permitem suspeitar tanto de colaboração quanto de proteção. A decisão de entregar a folha ou retê-la temporariamente usa `1`/`2`, muda a resposta de Inês e persiste. O inventário conserva a referência documental nas duas opções. Depois da decisão, a planta conecta a Câmara à autorização R-17 sem explicar o procedimento de esquecimento.

### Ressonância

`E` ativa discretamente os pontos disponíveis. A configuração reutilizável de cada ponto reúne identificador, região, posição, requisito, flag final, sequência com duração e silhuetas. Cores dessaturadas, transparências, pausas e pequenas partículas apresentam impressões genuínas, porém incompletas; a mecânica não concede bônus de combate.

1. Mesa: refeição e um lugar reservado a alguém que ainda não chegou.
2. Carroça: retirada e discussão sobre quem ficará com os nomes.
3. Selo: figuras militares, autorização R-17 e recusa de entregar o rol a qualquer escolta; falta o início da conversa.
4. Limiar: a voz do protagonista fala do custo de fechar a porta. A segunda voz permanece desconhecida.

Os ecos concluídos não se repetem. Após o quarto, uma cartela encerra **somente a Parte A**, restaura movimento e atualiza o objetivo para entrar na Câmara dos Testemunhos. O interior pertence à Parte B e ainda não está implementado. `chapter2_completed` e `chapter2_part_b_started` permanecem falsos.

### Criaturas e recompensas

- **Predador dos juncos:** silhueta baixa, focinho e cauda longos; aproximação rápida, preparação curta, investida e recuperação vulnerável. Tem pouca resistência.
- **Couraça de ardósia:** corpo robusto com placas, deslocamento lento, golpe amplo e preparação longa. Resiste à interrupção durante o ataque, mas deixa uma janela para contra-atacar.
- **Vigia de ardósia:** variante territorial com coroa de placas. Alterna o golpe comum com uma batida radial preparada por mais tempo; a colisão circular exclui os cantos do retângulo de debug. É um encontro curto, sem estrutura de boss completo.

Os três possuem idle, passos, preparação, ataque, dano e derrota nas quatro direções. Os desenhos usam 22 novos PNGs; proporções, espada, corte frontal e dash do protagonista são preservados. Consumíveis do desvio: duas poções e um éter. Objetos narrativos únicos: registro de transferência, pingente, termo de custódia e planta. Derrotas concedem XP pelo combate existente e permanecem registradas.

### Integração e validação

Builders de região, NPCs e criaturas específicos se conectam ao WorldManager, combate, interações, inventário, HUD, respawn e debug atuais. O save mantém a versão 1, aceita saves anteriores e valida dependências, documentos e escolhas. Não há recompensas duplicadas nem ressurreição de criaturas derrotadas. Texturas são geradas na entrada; sprites, arquitetura, flashes e fontes de HUD são reutilizados em cache.

Foi feito um passe específico de acabamento depois do fluxo funcional: rochas estratificadas, caminhos desgastados, arquitetura e mobiliário, escala das criaturas, enquadramento da Câmara e legibilidade das cenas.

Validação: **152 testes da suíte completa passaram**, incluindo 14 testes do capítulo. Depois dos ajustes finais de barreira visível e cache de fontes, **21 testes direcionados de capítulo e arte passaram**. Três verificações finais também confirmaram a abertura visual do arco e a batida radial do vigia, com um único acerto e sem atingir cantos fora do círculo. O teste integrado usa o loop real, input, transições, diálogos, ecos com duração normal, escolha explícita, contato de espada, autosave, reload e recuperação do movimento. O dano do jogador é elevado apenas nesse teste para encurtar o encontro; isso não substitui um playtest humano de dificuldade.

```powershell
python -m unittest tests.test_chapter2 tests.test_character_visuals -v
python tools/draw_encosta_cast.py
python tools/review_chapter2.py
```

Na medição local com SDL dummy, 180 frames preparados da Escarpa tiveram média de aproximadamente 1,1 ms no renderer, sem captura de imagens; os três mapas foram construídos em aproximadamente 53–61 ms na entrada. Essa medição isolada não representa o FPS completo nem garante desempenho em outras máquinas.

Capturas dos mapas, cenas e animações completas ficam em `tools/visual_checks/chapter2/`; os logs em `verification/`. A revisão usa o renderer de produção e saves temporários. Não foi realizado playtest humano prolongado; equilíbrio fino e percepção do mistério merecem essa próxima revisão. Não há bloqueios conhecidos no caminho principal. A próxima implementação narrativa é a Parte B, a partir da porta da Câmara.


Continuação: a Parte B foi posteriormente implementada; veja `CHAPTER_2B.md` para entrada, dungeon e encerramento do Capítulo II. Os limites acima descrevem a entrega original da Parte A.
