# Plano — 033-semear-taxonomia-deixa-o-banco-coerente

**Trilha:** rápida · **Fonte aprovada:** `01-brief.md` · Uma fase.

## O terreno

`app/taxonomy/seed.py` — `seed_taxonomy` reescreve `transactions.group_id` de quem
apontava para grupo removido, e só isso. `app/taxonomy/seed.py` também expõe o
comando de linha, e `app/ingest/__main__.py` encadeia semeadura e classificação.

Medir primeiro, decidir depois: a fase começa reproduzindo o número do validador
— quantos lançamentos ficam com grupo divergente da regra depois de uma semeadura
isolada, na árvore de hoje.

## Decisões

| Dúvida | Decisão |
|---|---|
| Completar ou recusar | **Completar**, se o custo couber; **recusar com mensagem**, se completar significar reclassificar a base inteira a cada semeadura. A medição da etapa 1.1 decide, e a decisão vai escrita no veredicto |
| A migração `012` | Fora do escopo de mudança: ela já rodou na base do dono, e reescrevê-la não desfaz o que ela fez. O que entra é o **teste** que prova que a classificação repõe o que ela derruba |

## Fase 1 — Semear não deixa o banco pela metade (api)

**Critérios de aceite**

- [ ] `comando` — RF-01, RF-02
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_taxonomy_seed.py -k coerente`
      sai `0` com ao menos um teste coletado (o arquivo é criado nesta fase se
      não existir). O caso: numa base onde a regra de um lançamento mudou de
      grupo, a semeadura rodada **sozinha** termina com uma de duas coisas — ou o
      lançamento corrigido, ou uma falha cuja mensagem nomeia o comando que
      falta. **Sair com sucesso deixando o lançamento divergente reprova.** O
      teste verifica a consulta que conta divergência: lançamento cujo
      `group_id` difere do grupo da regra que o classifica; ela devolve zero, ou
      a semeadura levantou.
- [ ] `comando` — RF-01
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_taxonomy_seed.py -k migracao`
      sai `0` com ao menos um teste coletado: depois de a migração da árvore
      hierárquica rodar sobre uma base com categorias registradas, a classificação
      seguinte **repõe** as categorias observadas. O controle positivo é que o
      teste falha se a classificação não rodar.
- [ ] `comando` — RF-03
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_classify.py tests/test_taxonomy_tree.py tests/test_taxonomy_remap.py tests/test_taxonomy_integration.py`
      sai `0`, sem `failed` nem `error` — o caminho encadeado da linha de comando
      continua como estava.
- [ ] `comportamental` — RF-04
      *Dado* o painel servido com a base real copiada para diretório temporário e
      `DASH_TODAY=2026-09-05`
      *Quando* as telas de resumo, gastos, comprometido e dívidas são buscadas
      antes e depois desta fase
      *Então* os totais de manchete são idênticos — semeadura é dado derivado, e
      dado derivado não move dinheiro
- [ ] `comando` — RF-03
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` sai
      `0`, com **mais** testes que a base desta branch.

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Medir a divergência**, reproduzindo o cenário do validador do item
      `023`, e **registrar o número** antes de escolher entre completar e recusar.
      Justificativa: a decisão depende do custo, e o custo ninguém mediu na árvore
      de hoje — o `14 de 87` é de uma árvore anterior.
- [ ] **1.2 — Fechar a aresta**, do jeito que 1.1 indicar. Justificativa: é o item.
- [ ] **1.3 — Teste da migração que derruba e repõe.** Justificativa: o
      comportamento é recuperável **por acidente do encadeamento**; sem teste, a
      próxima mudança no encadeamento o quebra sem aviso.
