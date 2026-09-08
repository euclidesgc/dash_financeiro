# Plano — 036-a-suite-nao-depende-do-diretorio-do-dono

**Trilha:** rápida · **Fonte aprovada:** `01-brief.md` · Uma fase.

## O terreno

`tests/test_sync.py` — os testes usam a fixture de conexão e chamam a
sincronização direto. A carga lê o caminho de `DASH_TRANSACTIONS_PATH`, que já é
sobrescrito num dos testes do arquivo (`test_a_source_that_cannot_be_read...`),
mas não nos dois que dependem do dado real.

`app/ingest/loader.py:163` — a mensagem de falha de escrita é
`f"erro de escrita: {type(failure).__name__}"`. O texto do `sqlite3.IntegrityError`
diz qual restrição falhou e é descartado.

## Decisões

| Dúvida | Decisão |
|---|---|
| De onde vem o dado de teste | De um arquivo versionado em `tests/data/`, pequeno, escrito para o caso — não de uma cópia da base do dono |
| A mensagem passa a expor o quê | O texto da exceção, que em SQLite nomeia a restrição. Não é dado do dono: é o nome de uma coluna |
| Varrer os outros testes | Sim. O critério mede a suíte inteira sem `data/`, não só estes dois |

## Fase 1 — A suíte passa numa árvore sem os dados do dono (api)

**Critérios de aceite**

- [ ] `comportamental` — RF-01, RF-02
      *Dado* um clone da branch num diretório temporário, **sem `data/` nenhum**
      — feito por `git clone` da própria árvore, ou por `git worktree add` seguido
      de remover `data/`
      *Quando* a suíte inteira roda ali
      *Então* ela sai com código `0`, sem `failed` nem `error`, com o mesmo número
      de testes que sai na árvore completa. Este é o critério central: é
      exatamente o ambiente da integração contínua, e é o que ninguém tinha
      medido.
- [ ] `comando` — RF-01
      `rtk proxy grep -rnE '"data/|'"'"'data/|DASH_TRANSACTIONS_PATH' tests/`
      imprime apenas linhas que apontam para dentro de `tests/`, ou que
      sobrescrevem o caminho para um diretório temporário. **Nenhuma** aponta
      para o `data/` da raiz.
- [ ] `comando` — RF-03
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_sync.py -k restricao`
      sai `0` com ao menos um teste coletado: uma escrita que viola chave
      estrangeira produz mensagem que **contém o texto da restrição violada**, e
      não apenas `IntegrityError`.
- [ ] `comando` — RF-04
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_sync.py`
      sai `0` e os dois testes nomeados no brief continuam presentes e passando —
      `-k "demotes or demotion"` coleta os dois. Eles provam o mesmo de antes;
      o que mudou é de onde vem o dado.
- [ ] `comando` — RF-02
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` sai
      `0` na árvore completa também, sem `failed` nem `error`.

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Dado de teste versionado em `tests/data/`**, escrito para exercitar
      o mesmo caminho de carga. Justificativa: RF-04 — fixture que não passa pelo
      mesmo código não substitui o dado real, troca um teste por outro.
- [ ] **1.2 — Os dois testes apontam para ele.** Justificativa: é a correção.
- [ ] **1.3 — A mensagem de erro de escrita nomeia a restrição.** Justificativa:
      a mensagem atual custou duas atribuições de culpa erradas nesta corrida; é
      a informação que estava disponível e foi jogada fora.
- [ ] **1.4 — Provar num clone sem `data/`.** Justificativa: é o ambiente do CI, e
      medir na árvore completa é medir outra coisa.
