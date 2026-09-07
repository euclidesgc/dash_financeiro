# Veredicto — item `011-serie-duplicada-e-tolerancia-do-vencimento`, fase 1

**Resultado:** `APROVADO`

Branch: `011-serie-duplicada/fase-1-integridade` · ponta `4faaeb9` · base `8fa5375`
Data da verificação: 2026-09-07 · Validador cego, agente novo.

**Higiene do despacho — falha registrada pelo próprio validador.** O despacho
levava duas "declarações do implementador", e uma delas carregava um número de
histórico de planejamento (`−R$ 9.553,00`, a previsão inicial). Isso é vazamento
de envelope. O validador registrou o vazamento e tratou as duas declarações como
**perguntas a medir**, não como evidência: respondeu a primeira rodando a árvore
do commit base contra o mesmo dataset, e a segunda abrindo os arquivos que o
critério nomeia. Ver `.harness/proposals/2026-09-06-004.md`.

## Portões

| Portão | Resultado |
|---|---|
| lint/analyze | **não existe no projeto** — `pyproject.toml` declara só `pytest` e `httpx`; nenhum binário de lint em `.venv/bin/`. Declarado ausente, **não** aprovado por presunção. Quinto validador seguido a registrar. |
| testes | **OK** — `pytest -q` na raiz: `316 passed, 2 warnings in 15.25s`, exit `0`, medido sem pipe para não ler o exit do `tail`. |
| gates | **OK** — exit `0`, `✓ gates: limpos (árvore completa, 222 arquivo(s) considerados).` |

Banco preparado como o critério manda; servidor com `setsid`, `/login`
respondendo `200` antes de qualquer medição, **um** login, cookie reusado,
processos mortos ao fim.

## Critérios de aceite

- [x] **`comando` — RF-02, RF-07, RF-25** — `installment 74`, `recurring 41`,
      `count(*) = 115`, pares distintos `(series_key, installment_total)` = `66`,
      e `0` linhas recorrentes para as quatro chaves fantasmas.
      **Contraprova:** o validador extraiu a árvore do commit base e rodou o
      mesmo ingest sobre o mesmo dataset. O código anterior devolve
      `installment 96 / recurring 55`, `151` e `4`. **O critério reprova a
      implementação anterior** — é a prova de que ele mede em vez de descrever.
- [x] **`comportamental` — RF-03, RF-24, RF-25** — `200`, `−R$ 8.026,79` como
      total comprometido, `R$ 0,00` como economia projetada, `12.802,64` com
      **zero** ocorrências no HTML, e `R$ 233,76` em `id="caixa-liberado"`.
      **Reconciliado contra o banco pela regra que os próprios critérios
      definem:** recorrentes vivas não dispensadas `-779303` mais parcelamentos
      vivos `-23376` dá `-802679`. As três linhas de caixa liberado
      (`12/2026 -6872`, `12/2027 -3777`, `06/2028 -12727`) somam `-23376`. O
      número da tela não foi aceito pela tela.
- [x] **`comando` — RF-01, RF-04** — `6 passed`. A metade estrutural foi
      conferida no fonte: a série cobrada **dentro** da janela com
      `installments_left == 0` não deixa linha recorrente; a mesma série cobrada
      **fora** da janela deixa.
- [x] **`comando` — RF-05, RF-06, RF-08, RF-09** — `12 passed`. Seis parcelas
      `n/6` com a primeira em `-13647` e as outras em `-13643` viram **uma**
      série, com `last_installment = 6`, `installments_left = 0` e
      `amount_cents = -13643`. Dois grupos `n/12` de `-2707` e `-4960` viram
      **duas**.
- [x] **`comando` — RF-10 a RF-14** — `13 passed`. O lançamento a 20 dias do dia
      previsto **não** apaga a previsão: as duas entradas aparecem. A série do dia
      29 cobrada em `2026-10-01` aparece **uma** vez. O diff sobre o arquivo é
      aditivo: os casos anteriores continuam lá.
- [x] **`comando` — RF-22 a RF-25** — vivas `16`, parcelamentos vivos `5`,
      paradas `25` somando `-273997`, e `last_seen_date > '2026-09-30'` agrupado
      por tipo devolve uma linha só, `installment 15`.
- [x] **`comportamental` — RF-15** — DOM real, Chromium via Playwright:
      `{"dias": 28, "series": 59, "jimCount": 1, "jimDay": "2026-09-08",
      "jimCentavos": "-13643", "jimText": "jim com já lançado na conta
      −R$ 136,43", "semCobranca": true}`.
- [x] **`comportamental` — RF-18** — banco do zero, servidor próprio, **um**
      login. Leitura 1: `−R$ 8.026,79` / `R$ 0,00`; três dispensas com `200`;
      leitura 2: `−R$ 6.927,16` / `R$ 1.099,63`. Mesmo PID do início ao fim, sem
      reingestão. Conferido no banco: as três chaves somam `-109963`.
- [x] **`estrutural` — RF-05, RF-11, RF-16, RF-17, RF-22** — as quatro
      constantes existem em escopo de módulo:
      `SAME_PURCHASE_DEVIATION = 0.02`, `DUE_TOLERANCE_DAYS = 10`,
      `LIVE_MONTHS = 1` e `WINDOW_DAYS = 45`, esta última em `calendar.py` como o
      critério exige. Ver apontamento 2 sobre a redação da segunda frase.
- [x] **`comportamental` — RF-16** — `live_floor(2026-09-05) = 2026-08-01` e
      `live_floor(2026-01-15) = 2025-12-01`.
- [x] **`comportamental` — RF-17** — `#calendario` traz `05/09/2026` e
      `20/10/2026`, coerente com `WINDOW_DAYS = 45`.

## Critérios de integração

- [x] **`comando` — portão local** — `316 passed`, exit `0`.
- [x] **`comando` — RF-19** — exit `1`, **stdout 0 bytes, stderr 0 bytes**, os
      dois fluxos redirecionados para arquivo e medidos com `wc -c`. Nenhum valor
      medido está cravado no código.
- [x] **`comando` — RF-20** — `115` → recompute → `115` → recompute → `115`.
      Mesma contagem nas duas execuções.
- [x] **`estrutural` — RF-21, RF-26, RF-27** — `00-discovery.md` e `01-brief.md`
      do `003` têm **zero** ocorrências de `12.802,64`, `374,82` e `141,06`, e
      cada um cita o item `011` uma vez. `03-plan.md` continua citando
      `−R$ 12.802,64` cinco vezes, quatro delas dentro de blocos de critério, e a
      nota antes do primeiro `##` nomeia o `011`. `git diff` sobre
      `docs/plano.md` não imprimiu linha nenhuma.

## Julgamento das duas declarações

**(a) Os números foram reescritos depois de a implementação existir.**
Confirmado que aconteceu, e **medido que não os invalidou**: a árvore do commit
base sobre o mesmo dataset devolve `96 / 55`, `151` e `4`, contra os `74 / 41`,
`115` e `0` exigidos. O critério reprova a implementação anterior.

A ressalva que sobra é de força, não de validade: `−R$ 8.026,79`, `R$ 233,76` e
`R$ 1.099,63` são **âncoras de regressão** — provam estabilidade e coerência
interna, não correção financeira. O validador reduziu isso reconciliando as três
contra o banco pela regra escrita nos próprios critérios, e as três fecham.

**(b) O `03-plan.md` do `003` não foi reconciliado.** Não é cicatriz. Cicatriz é
o "antes era X, agora é Y" deixado num documento canônico. Aqui o número velho
fica onde ele é **registro** — um plano de fase executada, cujos veredictos
citam a saída daqueles comandos —, e a nota aponta para onde mora o presente.
Os dois canônicos foram reescritos no presente; o registro histórico permaneceu
íntegro.

## Instrumentos do implementer

Quatro critérios mandam, na própria redação, executar a suíte do avaliado, e não
havia outro caminho. Para os três de `comando`, a dependência é **parcial**: a
metade estrutural ("o arquivo contém um teste que…") foi conferida lendo o fonte
e checando que cada asserção afirma o valor que o critério descreve. Os oito
restantes foram medidos por instrumento próprio: SQL direto, HTTP contra o
servidor real, DOM com Chromium, importação direta de `live_floor`, varredura de
literais, e a execução do código do commit base sobre o mesmo dataset.

## Apontamentos

1. **Âncora de dígito vale menos que âncora de identidade.** Para a próxima fase:
   um critério que fixa *o total é a soma das vivas não dispensadas mais os
   parcelamentos em aberto* prova mais do que um que fixa `−R$ 8.026,79`.
2. **A segunda frase do critério estrutural é insatisfazível ao pé da letra.**
   "Nenhum desses quatro valores aparece como literal no meio de uma expressão"
   reprova qualquer código Python por causa do `1`:
   `date(reference.year, reference.month, 1)` o contém. O validador julgou pela
   leitura que o próprio critério oferece — "o alcance do piso de vida, valendo
   `1` **mês**" —, e sob ela está cumprido. Trocar por "os quatro valores só
   aparecem na linha da sua constante".
3. **Sem lint nem typecheck no projeto.** Não é portão que deixou de ser rodado,
   e também não é portão que passou. Segue como `010-lint-e-formatador-python`.
