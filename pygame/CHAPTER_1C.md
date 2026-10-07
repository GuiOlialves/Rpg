# Capítulo 1C — O Posto de Vigia

O exterior apresentado no 1B agora leva ao Posto de Vigia. A conexão troca
apenas a saída preparada na Antiga Estrada; seu mapa, encontros e pistas
permanecem os mesmos. O posto tem 1536 × 1024, com a área construída
concentrada em um recinto pequeno, e usa as animações atuais.

O portão principal está travado por dentro. Examinar o portão indica uma
abertura no muro leste; afastar duas tábuas abre a passagem lateral. O
recinto contém torre de observação, pátio, alojamento, depósito e sala de
comando. As paredes têm colisão correspondente e portas legíveis. Há
duas ocupações pontuais: um Guardião Errante no pátio e um Slime no
depósito, com percepção local de 110 px e sem ondas ou facção vermelha.

Três documentos curtos continuam disponíveis para releitura:

- **Livro do Posto:** antiga troca de escoltas e caravanas; o alojamento
  recebeu feridos dos dois lados durante a guerra.
- **Despacho Azul:** uma escolta vermelha saiu antes do amanhecer e
  batedores azuis vieram depois, sem destino registrado. Uma ordem antiga
  anexada exige reter desertores e acompanhantes e interrogá-los sem água,
  sem esperar autorização local. A evidência é específica, sem concluir
  quem tem razão na guerra.
- **Registro de Guarnição:** guarnição vermelha, identificação R-17,
  responsabilidade pela escolta e acesso ao comando para receber ordens.
  O protagonista reconhece a assinatura; seu nome completo não aparece.

Uma peça pessoal R-17, encontrada no armário do alojamento, corresponde
ao registro. O protagonista reconhece o desgaste deixado pelo seu
polegar: “Isso era meu.” O inventário existente recebe a identificação
como item importante, sem uso ou consumo. Registro e objeto, encontrados
em qualquer ordem, confirmam sua ligação à estrutura vermelha.

A memória dura **6,95 segundos**, incluindo preparação e retorno. Três
imagens do mesmo posto, com soldados vermelhos e o protagonista usando
os sprites atuais, são separadas por cortes escuros. Vozes sem identidade:
“Você recebeu suas ordens.” / “Se eles chegarem antes de nós...” /
“Não hesite desta vez.” O último fragmento mostra a espada empunhada.
No retorno, papéis remexidos, cadeira caída e marcas de gavetas permitem
perceber que alguém revistou o posto. Não se revela a missão nem quem
fala. Interações e cenas esperam condições seguras, respeitando as paredes.

Depois das evidências principais, passos abafados e uma sombra passageira
na porta lateral indicam uma saída recente. A porta abre; examinar as
pegadas atualiza **Ecos da Guerra** para **Encontre quem estava no posto.**
A trilha exterior usa `pursuit_future`, preparando a continuação. Não há
personagem, confronto ou encontro do 1D.

Flags opcionais na versão 1 do save:

- `watchpost_entered`, `watchpost_entry_open`;
- `watchpost_archive_read`, `watchpost_dispatch_read`, `watchpost_roster_read`;
- `watchpost_personal_item_found`, `watchpost_identity_confirmed`;
- `watchpost_blue_order_found`, `watchpost_flashback_seen`;
- `watchpost_search_noticed`, `watchpost_presence_seen`, `watchpost_trail_found`;
- `watchpost_enemy_0_defeated`, `watchpost_enemy_1_defeated`.

O item persistido é `escort_token`, quantidade única. Save/load valida os
pré-requisitos narrativos e a correspondência entre flag e inventário.
Entrada, abertura, documentos, coleta, cenas, derrotas e objetivo pedem
autosave. Se o jogador sair após coletar o item, antes de concluir a
memória, reload permite concluir esse fragmento; depois de visto ele não
repete. Documentos podem ser relidos sem duplicar flags ou recompensas.
Saves do 1B continuam aceitos.

Validação focada:

```powershell
python -m unittest tests.test_watchpost tests.test_save_manager tests.test_combat tests.test_old_road.OldRoadTests.test_connection_round_trip_and_safe_spawns tests.test_old_road.OldRoadTests.test_camp_and_lookout_update_objective_and_unlock_watchpost_connection -q
python tools/review_watchpost.py
```

Os dez testes novos cobrem entrada/retorno/respawn, navegação com a hitbox
real, portão e aberturas, documentos, identificação, ambas as ordens de
investigação, retomada do flashback, combate por golpes reais de espada,
ausência de repetição, validação de saves e o fluxo integrado do Game
com F3, autosave e reload. A revisão usa o GameRenderer real e gera mapa,
documentos, item, sequência animada e imagens em
`tools/visual_checks/watchpost/`. Os saves usados nos testes são temporários;
a ferramenta de revisão não escreve no save real.
