# Schema do save

O formato atual permanece em `save_manager.py`, com `save_version: 1`. Esta refatoração não altera nomes de campos, validação ou gravação.

## Campos de topo

- `save_version`: versão inteira do formato (atualmente `1`).
- `region`: `home`, `village`, `forest` ou `desert`.
- `player`: nível, XP atual/necessária, pontos, atributos, HP, SP e posição `[x, y]`.
- `inventory`: lista de `{id, amount}`.
- `equipment`: IDs ou `null`, indexados pelos espaços de equipamento.
- `quests`: estado, progresso e indicação de recompensa por missão.
- `world`: flags do evento do Guardião, abertura da passagem norte e IDs dos baús abertos.
- `drops`: itens no chão com posição e tempo de vida restante.
- `story`: objeto narrativo com a flag booleana `woke_up`.

## Integridade

O carregamento valida versão, regiões, atributos, referências de itens/equipamentos, progresso de quests e consistência do mundo. HP deve ser maior que zero; saves inválidos com HP zero são rejeitados. A gravação escreve em arquivo temporário no mesmo diretório e substitui atomicamente o save.

## Evolução futura

`story` é uma extensão opcional do schema v1 para manter compatibilidade. Saves antigos sem esse objeto são carregados com `woke_up: true`, evitando repetir a abertura em partidas existentes. Novo jogo inicia com `woke_up: false`; a conclusão grava `true` e cria autosave somente se ainda não houver um save anterior, para não sobrescrever uma aventura existente. Nenhuma outra flag narrativa é aceita nesta etapa.
