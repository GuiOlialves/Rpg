# Capítulo 1A — O Retorno

O fechamento do prólogo permanece no campo de batalha, com “Quem era eu?”
e seu fade de 1,6 s. Em seguida o jogo segura o preto por 650 ms, apresenta
“CAPÍTULO I / ECOS DA GUERRA” (850 ms de entrada, 1,65 s de leitura e
700 ms de saída), espera mais 250 ms e revela a entrada leste da Vila.
O retorno leva 1,4 s, com fade de 1 s e um breve instante sem interface.
Não exige confirmação nem travessia de volta pela floresta.

O jogador reaparece em `(1850, 575)`, perto de Alden, com os mesmos HP,
SP, inventário e sprites. Mira e Tomas se reúnem perto da entrada e olham
para a estrada. Seus comentários e os do Morador refletem o ruído da
batalha e o receio de sair do Vale. Não há invasão ou destruição.

A conversa com Alden é iniciada por E, usa o diálogo existente e inclui
pausas que E não elimina. A confissão “Eu fazia parte deles.” é seguida
por 1,2 s de silêncio. Alden apenas reconhece a insígnia de homens que
passaram pela estrada antiga sem entrar no Vale. O protagonista decide
procurar o que fez antes de esquecer, sem descobrir ainda sua identidade.

O rastreador exibe **Ecos da Guerra** e muda de **Fale com Alden.** para
**Investigue a antiga estrada.** A saída oeste aproveita o caminho
existente e recebe uma placa examinável. `old_road_future` prepara a
conexão; mantém o jogador na Vila, como a conexão futura já usada pelas
ruínas. Nenhuma região da antiga estrada ou conteúdo do Capítulo 1B existe
neste bloco.

O JSON existente mantém a versão 1. As novas flags são opcionais em saves
anteriores e usam `False` quando ausentes:

- `chapter1_started`: título concluído;
- `chapter1_returned`: retorno à Vila efetivado;
- `chapter1_alden_talk`: conversa concluída;
- `old_road_unlocked`: pista entregue e saída oeste preparada.

`prologue_completed` continua sendo definido pelo encerramento original.
O retorno é salvo ao posicionar o jogador sob o preto; carregar esse ponto
já libera o jogo, sem repetir título ou cena. A conversa é salva em sua
conclusão; depois dela, Alden apenas lembra o caminho e pede que o jogador
volte. F4 aplica os mesmos marcos da reprodução normal, sem nova recompensa.

Validação restrita a este fluxo:

```powershell
python -m unittest tests.test_chapter1_return -v
python -m unittest tests.test_save_manager tests.test_prologue_audit.PrologueAuditTests.test_promise_normal_skip_and_safe_save_milestones -q
python tools/review_chapter1_return.py
```

As prévias estão em `tools/visual_checks/chapter1_return/`, incluindo a
transição animada, o título, o retorno, a admissão, a pista e a saída oeste.
Os testes usam arquivos temporários e a revisão não modifica o save real.
