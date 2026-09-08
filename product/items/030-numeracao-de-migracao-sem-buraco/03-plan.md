# Plano — 030-numeracao-de-migracao-sem-buraco

**Trilha:** rápida · **Fonte aprovada:** `01-brief.md` · Uma fase.

## O terreno, medido em 08/09/2026

`ls app/migrations/*.sql` → `001`…`015`, `018`. Faltam `016` e `017`.
`apply_migrations` ordena por `sorted(folder.glob("*.sql"))` e pula o que já está
em `schema_migrations`. Não há nenhuma comparação entre a versão que vai entrar e
a maior já aplicada.

## Decisões

| Dúvida | Decisão |
|---|---|
| Recusar ou avisar | **Recusar.** Aviso em subida de painel local ninguém lê |
| Como fechar os buracos | Renomeando `018_offers.sql` para `016_offers.sql` **não** é opção: ele já está aplicado na base do dono, e o nome é a chave. Os buracos se fecham **para frente**: a próxima migração é `019`, e o guarda impede que alguém use `016` |
| Onde o guarda mora | Em `apply_migrations`, antes de aplicar qualquer coisa |

## Fase 1 — O aplicador recusa quem chega por baixo (api)

**Critérios de aceite**

- [ ] `comando` — RF-01, RF-02
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_migrations.py -k ordem`
      sai `0` com ao menos um teste coletado — a linha de resumo não diz
      `no tests ran`. Os casos: numa base que já registrou `018`, uma migração
      `016` levanta erro cujo texto traz **as duas versões**; e nenhuma migração
      da mesma execução é aplicada, provado por `schema_migrations` estar
      inalterada depois da recusa.
- [ ] `comando` — RF-03
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_migrations.py`
      sai `0` e traz **mais** testes do que a base desta branch trazia. Nenhum
      teste existente muda de veredicto: a árvore real não tem migração fora de
      ordem, então o guarda não pode acusá-la.
- [ ] `comportamental` — RF-03
      *Dado* um diretório temporário vazio como base
      *Quando* `python -m app.migrate` roda contra a árvore real de migrações
      *Então* ele aplica as 16 e imprime `migrations applied: 16` — a subida de
      máquina nova é o caminho que o guarda não pode quebrar
- [ ] `estrutural` — RF-04
      `docs/` ou o próprio `app/migrations/` registra, numa linha, que `016` e
      `017` não existem e que a numeração segue de `019`. Um buraco sem nota é um
      buraco que alguém preenche.
- [ ] `comando` — RF-03
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` sai
      `0`, sem `failed` nem `error`.

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Comparar a versão que vai entrar com a maior já registrada**, antes
      do laço de aplicação. Justificativa: recusar depois de aplicar metade é o
      defeito que RF-02 nomeia.
- [ ] **1.2 — Mensagem que nomeia as duas versões e o que fazer.** Justificativa:
      quem topa com isso está subindo o painel e precisa saber renumerar, não
      descobrir sozinho.
- [ ] **1.3 — Testes de ordem**, incluindo o controle positivo da base nova.
      Justificativa: guarda que nunca foi visto recusando não foi provado, e o
      risco deste item é travar a subida por falso positivo.
- [ ] **1.4 — Registrar que a numeração segue de `019`.** Justificativa: norma 12,
      a pendência vira nota antes de a fase fechar.
