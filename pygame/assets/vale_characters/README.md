# O Vale — conjunto próprio de personagens

Segundo passe: **14 desenhos, 50 spritesheets PNG RGBA, 444 células** contando quatro direções. O protagonista agora faz parte da mesma família visual dos 13 personagens do primeiro passe. Arte desenhada diretamente na grade final de **32×32**, sem reduzir uma imagem grande. Os mapas e a escala aparente do primeiro passe foram preservados.

O protagonista mantém cabelo escuro/arroxeado com dois tufos, rosto jovem, túnica verde simples, gola de linho, correia e pequena bolsa de couro. Usa exatamente a mesma construção de cabeça/corpo, contorno, sombra e pivô dos demais. Civis ganharam gola, bainha, bolso, punhos, mechas e detalhes de idade/profissão; tropas ganharam borda do capacete, rebites/faixas do escudo, recorte da armadura e brilho discreto da lâmina. Comandante e oficial mantêm a identidade anterior, com capa/ombreira e dourado mais legíveis; o oficial permanece sem capacete.

## Catálogo

Quantidades **por direção**. As linhas de cada folha são: baixo, esquerda, direita, cima. Esquerda é o espelhamento pixel a pixel de direita.

| Personagem | Variantes | Idle | Caminhada | Ataque | Preparação | Hurt | Caído | Ajoelhado | Total por personagem, 4 direções |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Protagonista | 1 | 1 | 6 | 8 | — | — | — | — | 60 |
| Civis: homem, mulher, idoso, comerciante, trabalhador | 5 | 1 | 4 | — | — | — | — | — | 20 |
| Soldado azul | 3 | 1 | 4 | — | — | — | 1 | — | 24 |
| Comandante azul | 1 | 1 | 4 | — | — | — | 2 | — | 28 |
| Soldado vermelho | 3 | 1 | 4 | 3 | 1 | 1 | 1 | — | 44 |
| Oficial Vermelho | 1 | 1 | 4 | 3 | 2 | 1 | 1 | 1 | 52 |

A caminhada dos NPCs tem dois passos alternados e duas posições neutras. No protagonista, seis slots de caminhada e oito de ataque preservam o contrato existente; as poses simples são repetidas em alguns slots. O ataque possui trajetórias desenhadas para as quatro direções. O segundo caído do comandante levanta a cabeça na reação já existente. A derrota do oficial continua ajoelhada, apoiada na espada. Têmpora grisalha, barba curta e marca discreta no rosto reforçam sua experiência.

## Contrato de renderização

- Frame: 32×32, sem padding entre células. Uma folha por personagem/animação.
- Pivô: **(16, 28)** em todas as poses; último pixel dos pés em y=27.
- Desenho no mundo: 48×48, ampliação **1,5× nearest-neighbor**, igual à ampliação do protagonista. O canvas inclui espaço para armas; o corpo tem aproximadamente 24–26 pixels de altura nativa.
- Líderes têm ombros/capa mais largos, não ampliação extra.
- Alpha apenas 0 ou 255; sem antialiasing ou sombra semitransparente embutida. O mundo conserva seu desenho de sombras.
- `manifest.json`: arquivos, contagens, direções, pivô, escala e paleta completa.
- O crop de cadáveres azuis usa o limite conjunto das poses, mantendo o corpo imóvel quando o comandante levanta a cabeça.

Paleta compartilhada de **18 cores**, com no máximo **13 cores opacas por frame**. Foram acrescentados apenas um tom arroxeado para mechas (`#80687e`) e uma sombra de roupa (`#58644f`). Contorno ameixa escuro `#29242e`; pele `#e0ad78` / `#b87956`; couro `#574039`; azul `#48688d` / `#34455f`; vermelho `#ad5148` / `#743944`. Civis usam sálvia, linho e ocre. Sombra mínima, áreas chapadas e detalhes de um pixel.

### Compatibilidade do protagonista

As folhas existentes do jogador continuam com células **64×64**, seis colunas de caminhada e oito de ataque, quatro linhas direcionais. Cada desenho nativo 32×32 é colado **1:1**, sem resize, em **(16,20)** dentro dessa célula transparente. O pivô nativo (16,28) passa a (32,48), exatamente o pivô que o renderer já desenha em (48,72) com escala 1,5×. Assim os pés ficam na mesma baseline dos NPCs sem editar `Player.draw`, HUD, memórias ou temporizadores. São padding e frame mapping, não arte feita em 64×64.

## Substituições

- Protagonista: novo desenho harmonizado, incluindo caminhada e ataque nas quatro direções. As mesmas folhas atualizam automaticamente o retrato existente e as aparições em memórias.
- Morador da chegada e seu retorno: `civilian_man`.
- Mira: `civilian_woman`; Alden: `civilian_elder`; Tomas: `civilian_worker`.
- `civilian_merchant` está completo no pack e nos previews. Não foi criado um novo NPC/interação no mapa.
- Silhuetas das memórias: máscara do desenho feminino próprio.
- Marcha: comandante e três soldados azuis; corpos do campo de batalha e comandante ferido usam as respectivas poses próprias.
- Encontros vermelhos: três variantes determinísticas, sem consumir o RNG de gameplay; visual consistente antes/durante/depois do combate.
- Soldados da memória final: base vermelha própria.
- Oficial: mesmo desenho em aproximação, conversa, preparação, boss, dano, derrota e fuga.
- Os dois PNGs em `assets/npc/civilian_customer.png` e `civilian_seller.png` agora são cópias compatíveis do morador/ciclo de caminhada e da mulher/idle. Isso preserva os caminhos existentes usados pelo carregamento e checkpoints.

Mapas, objetos do campo de batalha e inimigos fora desse escopo permanecem com seus assets anteriores.

## Integração herdada do primeiro passe

| Arquivo | Alteração visual |
|---|---|
| `ui/character_art.py` (novo) | Carregamento, recorte por direção e pivô compartilhado |
| `ui/civilian_art.py` | Seleção dos cinco desenhos próprios |
| `entities/npc.py` | Leitura das quatro direções das novas folhas |
| `entities/enemy.py` | Assets, escala e frame mapping dos soldados vermelhos e boss |
| `entities/red_officer.py` | Desenho de DEFEATED ajoelhado |
| `story/arrival_scene.py` | Escala do morador e da silhueta |
| `story/blue_march.py` | Desenhos, variações, escala e poses caídas azuis |
| `story/forest_battle.py` | Cadáver vermelho usa a pose própria e o mesmo pivô do combate |
| `story/forest_confrontation.py` | Oficial da cena compartilha idle/walk/preparação/derrota com o boss |
| `story/prologue_3c.py` | Asset e escala dos soldados da memória |
| `world/regions/village.py` | Escala de Alden, Mira e Tomas |
| `world/regions/forest.py` | Seleção das folhas caídas azuis |

Nenhuma mudança de diálogo, condições, temporizadores de combate/cena, flags, colisões, dano, HP, Save/Load ou progressão foi feita neste passe. Alterações locais anteriores nesses arquivos foram preservadas.

### Arquivos alterados no segundo passe

- `tools/build_vale_characters.py`: refino compartilhado, protagonista, paleta e exportação compatível com o jogador.
- `tools/preview_vale_characters.py`: protagonista novo nas comparações e smoke de seus 56 slots renderizados (6+8 por direção).
- Os **47 PNGs existentes** deste diretório foram regenerados; acrescentados `protagonist_idle.png`, `protagonist_walk.png`, `protagonist_attack.png`; atualizado `manifest.json`.
- `assets/player/f_player_sheet.png` e `assets/player/f_player_attack_sheet.png`: folhas compatíveis atualizadas (384×256 e 512×256).
- `assets/npc/civilian_customer.png` e `assets/npc/civilian_seller.png`: cópias compatíveis refinadas.
- Este README e `ASSET_CREDITS.md`: documentação do refino.

**Nenhum código de runtime ou teste de gameplay foi alterado neste segundo passe.** A integração ocorre pela atualização dos PNGs nos caminhos que os renderizadores já utilizam. Não foi alterado o layout do HUD.

## Reprodução e validação

Executar a partir de `pygame/` (Pillow é necessário apenas para gerar/validar; o jogo continua usando Pygame):

```powershell
python tools/build_vale_characters.py
python tools/preview_vale_characters.py --output tools/visual_checks/vale_refinement
python tools/preview_cinematics.py --output tools/visual_checks/vale_refinement --only march officer_met boss final_opening_-1
```

Previews deste segundo passe em `tools/visual_checks/vale_refinement/` (pasta já ignorada pelo Git):

- `catalogo.png`: protagonista harmonizado e os mesmos 13 personagens refinados, com amostras 1×/1,5×/4×; sem recatalogar outros assets do jogo.
- `01_civis_escala.png`: cinco civis e protagonista na Vila.
- `02_tropa_azul_escala.png`: comandante, três variantes azuis e protagonista.
- `03_tropa_vermelha_escala.png`: três variantes vermelhas e protagonista na floresta.
- `04_oficial_{idle,walk,windup,attack,hurt,defeated}.png`: estados do oficial ao lado do protagonista.
- `animacoes.gif`: caminhada e ataque em escala de jogo.
- `05_protagonista_frames.png`: caminhada e ataque completos em quatro direções, com linhas de baseline.
- Capturas de checkpoints/cenas: `march.png`, `officer_met.png`, `boss.png`, `final_opening_-1.png`.
- `validation.json`: smoke de carregamento das 444 células, alpha binário, paleta, dimensões e baseline; compara DEFEATED da cena/boss e os 56 slots reais do jogador com a renderização nativa compartilhada.
- `before/`: catálogo anterior e duas folhas anteriores do jogador, preservados apenas para comparação local.

Neste segundo passe foi feito somente o smoke visual descrito acima e inspeção das imagens. Nenhuma suíte de testes de gameplay foi rodada. Nenhum commit ou push.
