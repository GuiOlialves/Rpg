# O Vale — sprites e animações

Pacote de 18 identidades na mesma grade de pixel: protagonista, cinco civis, tropas azuis/vermelhas, comandante, oficial e quatro inimigos. Não cria personagens, quests ou encontros novos no jogo.

O protagonista usa casaco verde-petróleo com abas, lenço cobre, cabelo castanho assimétrico, correia clara, mochila e braçadeira. Os civis têm roupas de profissão, barba/bengala, trança/avental, ferramentas ou chapéu. O cavaleiro errante tem viseira fechada e escudo gasto; o batedor usa capuz e arco; o lanceiro usa elmo alongado e lança; o Guardião tem armadura musgosa, chifres e lâmina larga. O oficial tem manto assimétrico, ombreira dourada e espada de golpes pesados.

## Estados e direção

| Grupo | Animações por direção |
| --- | --- |
| Protagonista | idle 4, caminhada 8, ataque 8, preparação 2, dash 5, dano 3, derrota 4 |
| Civis | idle 4, caminhada 8 |
| Tropas azuis/comandante | idle 4, caminhada 8, caído 1/2 |
| Tropas vermelhas/oficial | idle 4, caminhada 8, preparação 2, ataque 8, dano 3, morte 4, caído 1; oficial ajoelhado 1 |
| Outros inimigos próprios | idle 4, caminhada 8, preparação 2, ataque 8, dano 3, morte 4 |

Linhas das folhas: baixo, esquerda, direita, cima. As direções são desenhadas separadamente, mantendo iluminação e acessórios físicos. O manifesto lista arquivos, contagens, paleta, tamanhos e pivôs. O slime de Mystic Woods reutiliza seus estados originais.

## Contrato visual

- Corpos: células 32×32; pivô dos pés (16,28); escala inteira 2×, nearest-neighbor. NPCs conservam pés completos.
- Armas: células transparentes 96×96, pivô (48,58). Golpes pesados: 160×160, pivô (80,90). O padding permite desenhar a arma completa na mesma resolução dos corpos.
- Mão, guarda, lâmina e máscara são exportadas a partir da mesma trajetória. A espada do protagonista mantém o comprimento nas quatro direções; as armas maiores dos inimigos usam diferença discreta de perspectiva entre norte e sul.
- Corpos com alpha binário, contorno azul escuro, luz superior esquerda, sombras em blocos e paleta comum. Slash/poeira usam alpha discreto e também pixels sem suavização.
- Sombra e ordenação pelos pés continuam no renderer do mundo. Impacto entra na profundidade do alvo, depois do corpo e antes de objetos à frente.
- As folhas públicas antigas do jogador continuam em células 64×64, com padding e seis/oito colunas, para retratos, checkpoint e Save/Load. O renderer de jogo usa os estados novos diretamente.

## Animação e combate

`core/animation.py` centraliza cadência, duração dos estados, pivôs e dimensões. Caminhada avança pela distância realmente percorrida: 48 pixels por ciclo do protagonista e 64 dos demais atores. Input bloqueado não avança as pernas. O protagonista tem apoio, passagem e levantamento distintos dos pés. No idle, cabeça e pés ficam firmes; ombros e tecido respiram, com uma piscada curta.

O ataque conserva 16 ticks e a recarga dos atributos. Os timings são 2/2/1/1/2/2/2/4 ticks: preparação curta, aceleração, contato e recuperação. A janela ativa fica nos ticks 4–9 (frames 2–5). A espada do protagonista tem ponta a 15 pixels da empunhadura, aproximadamente 12 de lâmina, em todas as poses. Mão, arma e máscara usam os mesmos pontos desenhados; o slash estreito aparece só nos dois frames de contato. `attack_box` é o limite da máscara, e `attack_hits` exclui os cantos transparentes. O alcance agora acompanha a espada menor. Continua havendo apenas um acerto por ataque/alvo. Colisões de chão, dano e stats permanecem com os valores existentes.

Dash tem carga, impulso, deslocamento e dois momentos de retorno. Seus 11 ticks de movimento, 99 pixels, custo, recarga e invulnerabilidade permanecem iguais. Os cinco ticks de recuperação são apenas visuais e permitem mover ou atacar imediatamente. O rastro usa no máximo duas cópias, duração de cinco ticks e alpha máximo 60/255; a poeira nasce na arrancada. A espada permanece na bainha presa ao quadril. Dano usa reação e flash sem esconder o corpo; derrota mantém o novo rosto/roupa e termina no chão. Impactos têm faíscas curtas, hitstop existente e sacudida de 1–2 pixels somente nos golpes relevantes. Inimigos preservam IA e avisos; batedor puxa a corda do arco, lanceiro mantém investida e chefes têm postura mais pesada, ombreiras próprias e slash contido.

`ui/character_art.py` prepara slicing, nearest scaling, máscaras, flashes e rastros antes da renderização. Nenhum slicing, scale, flip ou rotação de atores ocorre no draw normal. O cache é compartilhado entre entidades do mesmo visual.

## Reproduzir e verificar

Pillow só é necessário para reconstruir sprites e gerar previews; o jogo continua usando Pygame CE.

```powershell
python tools/build_vale_characters.py
python -m unittest tests.test_combat tests.test_architecture tests.test_character_visuals -q
python tools/review_character_overhaul.py
python tools/review_protagonist.py all
```

Previews em `tools/visual_checks/character_overhaul/`: `before.png`, `cast.png`, `hero_states.png`, `sword_directions.png`, `animations.gif`, capturas da Vila/Floresta/Deserto/Casa e `impact.png`, `boss_states.png` e `smoke.json`. A revisão compara poses, pivôs, direções e integração nos cenários reais. O smoke usa SDL dummy e não grava saves.

O segundo passe foi feito em etapas: base/rosto/idle/passos → espada/ataque → dash → demais atores. `tools/visual_checks/staged_overhaul/` guarda as folhas de cada etapa, silhuetas, assets anteriores do protagonista e `hero_in_motion.gif`, renderizado com o controlador real nas quatro direções. `final/` contém a comparação do elenco, reações/derrota, chefes, capturas de mapas e impacto confirmado pelo sistema de combate. O desenho específico do protagonista fica em `tools/hero_pixel_art.py`; `draw_vale_pack.py --look protagonist` permite reconstruí-lo sem alterar NPCs e inimigos.

O ajuste final do ataque ao sul usa um corte lateral baixo: esquerda → arco frontal → direita, com empunhadura na cintura, rotação discreta de ombros/tronco e pés apoiados. Comprimento, duração e janela ativa permanecem iguais; slash e máscara seguem o mesmo arco. A comparação, trajetória e repetição nas quatro direções ficam em `tools/visual_checks/front_sword_cut/`, geradas por `python tools/review_front_sword_cut.py`.

Limites: são as quatro direções cardinais existentes; o projétil do batedor representa o ataque instantâneo original, sem adicionar física. Não foi feito playtest manual de todo o prólogo. Os props Tiny Swords do campo de batalha continuam reutilizados. História, mapas, inventário, progressão e formato de save permanecem fora das alterações.
