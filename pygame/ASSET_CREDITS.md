# Créditos dos assets

O projeto inclui somente os arquivos de imagem necessários para executar a versão Pygame. Spritesheets e materiais-fonte completos não necessários ao jogo não fazem parte desta publicação.

| Conjunto usado | Utilização | Licença / referência |
| --- | --- | --- |
| O Vale — personagens próprios | Protagonista, cinco civis, tropas, líderes, Guardião Errante, Guardião da Clareira, Batedor e Lanceiro; armas e efeitos | Desenhos de pixels deste projeto, construídos em `tools/draw_vale_pack.py` e poses próprias do protagonista em `tools/hero_pixel_art.py`; entry point `tools/build_vale_characters.py`. Corpo 32×32 e camadas de arma com padding na mesma grade. Contrato em `assets/vale_characters/README.md`. Não derivados dos sprites Tiny Swords/Craftpix. |
| O Vale — Encosta e Câmara | Inês, Breno, predador dos juncos, couraça e vigia de ardósia; arquitetura, rochas, árvores e mobiliário das três regiões | Desenhos próprios em `tools/draw_encosta_cast.py` e `world/regions/encosta_art.py`. NPCs 32×32; criaturas 80×40 com padding para investida. Escala inteira 2×; sem novos assets externos. |
| O Vale — Câmara dos Testemunhos | Guardião de custódia, eco instável, Vigia dos Registros e Iriel; cinco setores, inscrições, mobiliário e núcleo | Desenhos próprios em `tools/draw_lacre_cast.py`, geometria em `core/lacre_motion.py` e arquitetura em `world/regions/lacre_art.py`. 40 folhas 80×64, escala 2×. Sem novos assets externos. |
| vila_tile-set | Tiles da vila, casas, caixas, grama e decoração | Consulte `licenses/craftpix-vila.txt`; [Craftpix file licenses](https://craftpix.net/file-licenses/) |
| Mystic Woods Free 2.2 | Slimes, baús e recortes individuais gratuitos de vegetação | Os sprites usados estão em `assets/forest/` e `assets/shared/`; os previews “Premium Version” não acompanham esta publicação. Consulte a distribuição original do pacote. |
| Tiny Swords (Free Pack) | Recortes de espada, escudo e insígnia no campo de batalha; folhas legadas preservadas no diretório de fontes | Consulte os termos da distribuição original do pacote antes de redistribuir os sprites. |
| Craftpix Desert Tileset | Terreno, caminhos, lago, ruínas, pedras e vegetação do deserto | Consulte `licenses/craftpix-deserto.txt`; [Craftpix file licenses](https://craftpix.net/file-licenses/) |
| BLANK GAME sprite sheets | Referência anterior de identidade e escala do protagonista | No segundo passe do pack próprio, as duas folhas em `assets/player/` foram substituídas por desenhos originais de O Vale. A pasta original do GameMaker não acompanha esta publicação. |

Os assets pertencem aos respectivos autores e estão sujeitos aos termos dos pacotes de origem. Este repositório não concede uma licença independente para redistribuir esses arquivos gráficos.
