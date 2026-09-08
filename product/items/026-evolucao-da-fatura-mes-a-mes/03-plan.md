# Plano — 026-evolucao-da-fatura-mes-a-mes

**Item:** `026-evolucao-da-fatura-mes-a-mes` · **Trilha:** rápida ·
**Fonte aprovada:** `01-brief.md` · **Terreno:** `00-discovery.md` · Duas fases,
em sequência.

> **Nenhum número deste plano foi escrito de cabeça.** Todo valor que aparece num
> critério é ou produzido pela base que o próprio critério manda montar — linhas
> de `INSERT` com os centavos escritos ali — ou um literal que já existe no
> repositório, com o arquivo e a linha nomeados. Não há número herdado de medição
> anterior nem número presumido do banco do dono.

## Objetivo

Ao fim das duas fases `/comprometido` responde **como a fatura de cada cartão
soma mês a mês até zerar**, e a curva não pode discordar do total: a soma dos
meses de um cartão é, à vírgula, o que ainda falta pagar naquele cartão. O mês
em que cada parcela cai sai do **dia de fechamento** que o item `024` passou a
guardar; cartão sem fechamento informado tem a premissa escrita na tela em vez de
um dia adivinhado.

A quebra é por **contrato, não por tela**. A fase 1 fixa a forma do dado —
consulta e aritmética, sem rota e sem template —, porque a premissa que decide o
item é o mês de cada parcela, e ela errada se espalha para cada número da tela de
uma vez. A fase 2 leva a leitura para dentro de `/comprometido`, onde ela passa a
ser conferível contra a tabela de parcelamentos que já está ao lado.

## O terreno, lido no código

| Sítio | O que já existe | O que falta |
|---|---|---|
| `app/migrations/sql/004_commitments.sql:13-15` | `installment_total`, `installments_left`, `ends_month` | nada: é daqui que a curva sai |
| `app/commitments/series.py:19` | a série guarda `a.name AS account` — o **nome** da conta, não o id | a ligação com `cards`, que é por `account_id` |
| `app/commitments/series.py:118` | `ends_month = end_month(last["date"][:7], left)` — mês do último **lançamento** | o mês da **fatura**, que o fechamento decide |
| `app/commitments/live.py:16-22` | `live_floor`: primeiro dia do mês anterior à referência | nada |
| `app/commitments/live.py:37-47` | `installments`: série de parcelamento com parcela em aberto e cobrança recente | nada; é o mesmo recorte que a curva usa |
| `app/commitments/live.py:62-68` | `released_cash`, chaveado por `ends_month` | nada, e não muda (RF-08) |
| `app/commitments/schedule.py:22-24` | `end_month(mês, n)` desloca rótulo de mês | nada; a curva reusa |
| `app/commitments/calendar.py:13` | `WINDOW_DAYS = 45` | nada, e não muda (RF-08) |
| `app/commitments/calendar.py:126-142` | `_charges` (`último < mês <= fim`) e `_months` (lista de meses por deslocamento) | nada; são a forma que a curva repete |
| `app/migrations/sql/013_cards.sql:4-12` | `cards(account_id, limit_cents, monthly_rate_bp, closing_day, due_day)` | nada: `closing_day` é o campo que faltava |
| `app/templates/fragments/comprometido_parcelamentos.html:20-32` | "Falta pagar" (`data-restante`) e "Termina em" (`ends_month`) por série | a distribuição desse saldo pelos meses |
| `app/routers/commitments.py:100-127` | `_context` monta assinaturas, parcelamentos, caixa liberado e calendário | a curva |

Três fatos decidem o desenho e não se re-discutem:

1. **A soma fecha por construção, se a distribuição for exata.** O que falta
   pagar de uma série é `amount_cents * installments_left`, que é o que
   `app/templates/fragments/comprometido_parcelamentos.html:27` já imprime em
   `data-restante`. Distribuir exatamente `installments_left` parcelas em meses
   distintos faz a soma da curva ser esse mesmo número. RF-05 não é um cálculo
   paralelo a conferir: é a propriedade que a distribuição tem ou não tem.
2. **A ligação série → cartão é por nome.** `commitments.account` guarda o nome
   da conta (`app/commitments/series.py:19`) e `cards` é chaveada por
   `account_id` (`app/migrations/sql/013_cards.sql:5`). A junção casa
   `commitments.account = accounts.name` com `accounts.type = 'CREDIT'`.
3. **Nada disso pede coluna nova.** `commitments` já traz a última cobrança e
   quantas parcelas faltam; `cards` já traz o dia de fechamento. **Este item não
   cria migração.**

## Decisões resolvidas por padrão, não por pergunta

| Dúvida | O que decidiu | Decisão |
|---|---|---|
| O mês da curva é o do fechamento ou o do vencimento? | A discovery nomeia só o fechamento, e o brief põe campo novo de cartão no não-escopo | **fechamento**: o rótulo do mês é o da fatura que **fecha**; `cards.due_day` não entra |
| Onde mora a junção? | Norma 33 — junção e agregação em SQL, em `app/queries` | `app/queries/invoices.py` |
| Onde mora a aritmética do mês? | Norma 23 — cálculo é função determinística testada | `app/commitments/invoice.py` |
| O nome `forecast`? | `app/projection/forecast.py:17` já exporta `forecast`, consumido por `app/routers/summary.py:11` | o módulo novo chama-se `invoice`, e a função `invoice_curve` |
| Duas contas de crédito com o mesmo nome | Um `LEFT JOIN` por nome duplicaria a série e a soma dobraria — que é exatamente o painel mentindo | a consulta agrupa por nome (`GROUP BY a.name`) antes de casar a série: nome duplicado vira **um** grupo, com `MAX(closing_day)`, como `app/migrations/sql/013_cards.sql:14-16` já resolve o caso irmão |
| Parcelamento vivo que **não** está em conta de crédito | O brief diz "por cartão", e a tabela de parcelamentos continua listando todos | fica fora da curva, e a tela **conta quantos ficaram de fora** — a mesma forma que `app/routers/commitments.py:114-117` usa para as assinaturas sem cobrança recente. Lacuna da spec, registrada no retorno |
| A curva começa em que mês? | RF-01: "do mês corrente" | mês de calendário da data de referência, com zero nos meses sem parcela — e zero aqui é informação: nada do que se deve vence naquele mês |
| A tabela "Termina em" passa a usar o mês da fatura? | `released_cash` (`app/commitments/live.py:62-68`) é chaveado por `ends_month`, e mexer nele move o "Caixa liberado" | **não**: a tabela existente segue no mês do lançamento; a curva nomeia o mês da **última fatura** com rótulo próprio. Divergem em no máximo um mês, e só quando há fechamento informado. Registrado em pendências |
| CSS novo? | O escopo do item não inclui `app/static/css/` | **nenhum**: a seção se monta com classes já declaradas, e um critério de comando cobra isso |
| Migração nova? | `commitments` e `cards` já trazem tudo | **nenhuma**: nenhum arquivo entra em `app/migrations/sql/` |

---

## Fase 1 — A série mensal por cartão (api)

**Objetivo da fase:** existe uma leitura que devolve, por cartão, quanto a fatura
soma em cada mês até zerar, e a soma dessa série é o que falta pagar naquele
cartão — sem que nenhuma tela ainda a mostre.

**Critérios de aceite:**

- [ ] `estrutural` — RF-01, RF-02, RF-03
      Existe `app/queries/invoices.py` exportando `card_series`, e existe
      `app/commitments/invoice.py` exportando `invoice_month` e `invoice_curve`.
      `app/queries/invoices.py` **contém** as palavras `SELECT`, `GROUP BY` e
      `LEFT JOIN`, e `app/commitments/invoice.py` **não** contém a palavra
      `SELECT` — a primeira metade é o controle positivo da segunda, sem o qual
      "não tem SQL" passaria igual num arquivo vazio ou inexistente. Nenhum
      arquivo novo aparece em `app/migrations/sql/`: a pasta segue sem nenhum
      arquivo cujo nome comece por `016`, e segue contendo `013_cards.sql` e
      `004_commitments.sql`
- [ ] `comportamental` — RF-02
      *Dado* um banco SQLite em diretório temporário com as migrações aplicadas
      e as linhas
      `INSERT INTO accounts (id, name, type, balance_cents) VALUES ('acc-azul', 'Cartão Azul', 'CREDIT', -100000)`,
      `INSERT INTO cards (account_id, closing_day) VALUES ('acc-azul', 5)` e
      `INSERT INTO commitments (kind, series_key, description, account, amount_cents, last_seen_date, installment_total, installments_left, ends_month) VALUES ('installment', 'loja azul', 'Loja Azul', 'Cartão Azul', -12000, '2026-08-11', 24, 3, '2026-11')`
      *Quando* `app.commitments.invoice.invoice_curve(conn, today=date(2026, 9, 5))`
      é chamada, e depois de novo com `cards.closing_day` alterado para `20`
      *Então* na primeira chamada o cartão `Cartão Azul` traz `months` com os
      meses `['2026-09', '2026-10', '2026-11', '2026-12']` e os
      `total_cents` `[0, -12000, -12000, -12000]`; e na segunda traz os meses
      `['2026-09', '2026-10', '2026-11']` com os `total_cents`
      `[-12000, -12000, -12000]`. O par é a medida: a compra do dia 11 cai na
      fatura seguinte quando o fechamento é dia 5 e na fatura do próprio mês
      quando é dia 20, e o mês de cada parcela anda junto
- [ ] `comportamental` — RF-03
      *Dado* o mesmo banco temporário e as mesmas três linhas do critério
      anterior, porém **sem** nenhuma linha em `cards` para `acc-azul`
      *Quando* `invoice_curve(conn, today=date(2026, 9, 5))` é chamada
      *Então* o cartão `Cartão Azul` traz `closing_day` igual a `None`, `assumed`
      igual a `True`, os meses `['2026-09', '2026-10', '2026-11']` e o
      `last_invoice` igual a `2026-11` — que é o mesmo valor da coluna
      `ends_month` da linha inserida em `commitments`, porque sem fechamento a
      curva é construída pelo mês do lançamento e não inventa deslocamento
      nenhum. E com `INSERT INTO cards (account_id, closing_day) VALUES ('acc-azul', 5)`
      aplicado, a mesma chamada devolve `assumed` igual a `False` e
      `last_invoice` igual a `2026-12`
- [ ] `comportamental` — RF-05
      *Dado* um banco SQLite em diretório temporário com as migrações aplicadas
      e as linhas
      `INSERT INTO accounts (id, name, type, balance_cents) VALUES ('acc-azul', 'Cartão Azul', 'CREDIT', -100000), ('acc-roxo', 'Cartão Roxo', 'CREDIT', -50000)`,
      `INSERT INTO cards (account_id, closing_day) VALUES ('acc-azul', 5)` e
      `INSERT INTO commitments (kind, series_key, description, account, amount_cents, last_seen_date, installment_total, installments_left, ends_month) VALUES ('installment', 'loja azul', 'Loja Azul', 'Cartão Azul', -12000, '2026-08-11', 24, 3, '2026-11'), ('installment', 'posto azul', 'Posto Azul', 'Cartão Azul', -5000, '2026-09-02', 6, 2, '2026-11'), ('installment', 'loja roxa', 'Loja Roxa', 'Cartão Roxo', -20000, '2026-08-20', 10, 1, '2026-09')`
      *Quando* `invoice_curve(conn, today=date(2026, 9, 5))` é chamada
      *Então*, para **cada** cartão devolvido,
      `sum(mes['total_cents'] for mes in cartao['months'])` é igual a
      `cartao['remaining_cents']`, e esse mesmo `remaining_cents` é igual ao que
      a consulta independente
      `SELECT sum(amount_cents * installments_left) FROM commitments WHERE kind = 'installment' AND installments_left > 0 AND account = ?`
      devolve para o nome daquele cartão — `-46000` para `Cartão Azul` e
      `-20000` para `Cartão Roxo`, que são os produtos das linhas inseridas
      acima. Os dois valores são **diferentes de zero**, e é esse o controle
      positivo: numa base sem série alguma as três somas seriam zero e a
      igualdade passaria sem medir nada
- [ ] `comportamental` — RF-04
      *Dado* a mesma base de três séries e dois cartões do critério anterior
      *Quando* `invoice_curve(conn, today=date(2026, 9, 5))` é chamada
      *Então* a série `loja azul` traz `last_invoice` igual a `2026-12` e
      `frees_cents` igual a `12000`, e a série `posto azul` traz `last_invoice`
      igual a `2026-11` e `frees_cents` igual a `5000` — positivo, porque
      dinheiro que para de sair volta ao caixa; e, nos meses do `Cartão Azul`,
      `total_cents` de `2026-11` menos `total_cents` de `2026-12` é igual a
      `5000`, que é exatamente o `frees_cents` da série que morre em `2026-11`:
      a queda da fatura no mês seguinte à morte é medida na própria curva, e não
      afirmada ao lado dela
- [ ] `comportamental` — RF-07
      *Dado* a base de três séries e dois cartões, acrescida de
      `INSERT INTO accounts (id, name, type, balance_cents) VALUES ('acc-verde', 'Cartão Verde', 'CREDIT', 0)`
      e `INSERT INTO cards (account_id, closing_day) VALUES ('acc-verde', 10)`,
      sem nenhuma linha em `commitments` cujo `account` seja `Cartão Verde`
      *Quando* `invoice_curve(conn, today=date(2026, 9, 5))` é chamada
      *Então* `Cartão Verde` **está** na lista de cartões, com `months` igual à
      lista vazia, `series` igual à lista vazia e `remaining_cents` igual a `0` —
      e, na mesma resposta, `Cartão Azul` traz `months` com quatro entradas, que
      é o controle positivo sem o qual uma resposta vazia satisfaria as três
      primeiras afirmações
- [ ] `comportamental` — RF-05
      *Dado* um banco temporário com as migrações aplicadas e **duas** contas de
      crédito de mesmo nome,
      `INSERT INTO accounts (id, name, type, balance_cents) VALUES ('acc-azul-1', 'Cartão Azul', 'CREDIT', -100000), ('acc-azul-2', 'Cartão Azul', 'CREDIT', -20000)`,
      com `INSERT INTO cards (account_id, closing_day) VALUES ('acc-azul-1', 5)`
      e uma única linha
      `INSERT INTO commitments (kind, series_key, description, account, amount_cents, last_seen_date, installment_total, installments_left, ends_month) VALUES ('installment', 'loja azul', 'Loja Azul', 'Cartão Azul', -12000, '2026-08-11', 24, 3, '2026-11')`
      *Quando* `invoice_curve(conn, today=date(2026, 9, 5))` é chamada
      *Então* a lista de cartões tem **um** elemento chamado `Cartão Azul`, e a
      soma de `remaining_cents` de todos os cartões é `-36000` — o produto da
      única linha inserida —, e não `-72000`. O valor é diferente de zero, e é
      esse o controle positivo da contagem
- [ ] `comportamental` — RF-01
      *Dado* um banco temporário com as migrações aplicadas, uma conta de crédito
      inserida por SQL
      (`INSERT INTO accounts (id, name, type, balance_cents) VALUES ('acc-cartao', 'Cartão Azul', 'CREDIT', -100000)`),
      `INSERT INTO cards (account_id, closing_day) VALUES ('acc-cartao', 5)`, e
      duas transações **ingeridas pelo carregador** com
      `tests.conftest.load` — uma com `conta_id='acc-cartao'`,
      `data='2026-08-11'`, `valor=-120.00`, `descricao='Loja Azul'`,
      `parcela_atual=2`, `parcela_total=24`, e outra na conta corrente de teste
      (`conta_id='acc-1'`), `data='2026-08-20'`, `valor=-50.00`,
      `descricao='Carne Loja'`, `parcela_atual=1`, `parcela_total=6` —, seguidas
      de `seed_taxonomy`, `classify_all` e
      `app.commitments.engine.recompute(conn, today=date(2026, 9, 5))`
      *Quando* `invoice_curve(conn, today=date(2026, 9, 5))` é chamada
      *Então* a lista de cartões tem exatamente um elemento, com `name` igual a
      `Cartão Azul` e `remaining_cents` igual a `-264000` — vinte e duas parcelas
      de doze mil centavos, que é o que o motor gravou a partir da transação
      acima —, `off_card` é igual a `1`, e
      `len(app.commitments.live.installments(conn, today=date(2026, 9, 5)))` é
      igual a `2`: as duas séries estão vivas, uma entrou na curva e a outra foi
      contada de fora. Este é o único critério da fase que passa pelo motor de
      verdade, e é ele que prova que a coluna que liga série e cartão é o
      **nome** da conta e não outro campo — uma base forjada à mão passaria com
      qualquer suposição
- [ ] `comando` — RF-01, RF-02, RF-03, RF-04, RF-05, RF-07
      `rtk proxy env DASH_ENV_FILE=/dev/null DASH_TODAY=2026-09-05 .venv/bin/python -m pytest -q tests/test_commitments_invoice.py`
      sai com código `0`, e o arquivo exercita: o cartão com fechamento e o
      mesmo cartão sem fechamento, a igualdade entre a soma dos meses e o
      restante do cartão, o mês da última fatura de cada série, o cartão sem
      série viva e o nome de cartão repetido. O código de saída é lido do próprio
      `pytest` — encadear `| tail` leria o código do `tail`

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Criar `app/queries/invoices.py`: a junção cartão × série, em SQL.**
      Uma consulta só, exportada por
      `card_series(conn: sqlite3.Connection, *, kind: str, floor: str) -> list[dict]`:
      ```sql
      SELECT g.card_name, g.closing_day, c.series_key, c.description,
             c.amount_cents, c.installments_left, c.last_seen_date, c.ends_month
        FROM (SELECT a.name AS card_name, MAX(k.closing_day) AS closing_day
                FROM accounts a LEFT JOIN cards k ON k.account_id = a.id
               WHERE a.type = ?
               GROUP BY a.name) g
        LEFT JOIN commitments c
          ON c.account = g.card_name AND c.kind = ?
         AND c.installments_left > 0 AND c.last_seen_date >= ?
       ORDER BY g.card_name, c.amount_cents * c.installments_left, c.series_key
      ```
      `CREDIT` vem de `app.accounts`; `kind` e `floor` chegam do chamador, para
      que `app/queries/` não passe a depender de `app/commitments/`.
      *Considerando:* nada antes — é a primeira etapa.
      *Justificativa:* RF-01, RF-02, RF-05, RF-07. Norma 33: a junção e a
      agregação são de SQL e moram em `app/queries`. O `GROUP BY a.name`
      **antes** do casamento com a série é o que impede o nome de cartão
      repetido de contar a mesma dívida duas vezes — com o `LEFT JOIN` direto
      sobre `accounts`, duas contas de mesmo nome dobrariam a curva enquanto o
      total ao lado ficaria certo, que é a discordância que o item existe para
      não ter. O `MAX(closing_day)` repete a solução que
      `app/migrations/sql/013_cards.sql:14-16` já usa pelo mesmo motivo: sem ele,
      qual das duas linhas responde depende da ordem física. O `LEFT JOIN` sobre
      a série (e não `JOIN`) é o que faz o cartão sem parcelamento vivo aparecer
      na lista em vez de sumir dela (RF-07). O recorte
      `installments_left > 0 AND last_seen_date >= ?` é literalmente o de
      `app/commitments/live.py:43-47`, para que a curva e a tabela de
      parcelamentos leiam o mesmo conjunto.

- [ ] **1.2 — Criar `app/commitments/invoice.py`: o mês da fatura e a curva.**
      Duas funções públicas:
      ```python
      def invoice_month(when: str, closing_day: int | None) -> str
      def invoice_curve(conn: sqlite3.Connection, *, today: date | None = None) -> dict
      ```
      `invoice_month` devolve `when[:7]` quando `closing_day is None` ou
      `int(when[8:10]) <= closing_day`, e `end_month(when[:7], 1)` no resto —
      `end_month` vem de `app/commitments/schedule.py:22-24`.
      `invoice_curve` chama `live_floor(today)`, passa `INSTALLMENT` e o piso a
      `card_series`, agrupa as linhas por `card_name` e devolve
      ```python
      {"cards": [...], "off_card": int, "remaining_cents": int}
      ```
      com cada cartão em
      ```python
      {"name": str, "closing_day": int | None, "assumed": bool,
       "months": [{"month": "AAAA-MM", "total_cents": int}],
       "series": [{"series_key": str, "description": str, "amount_cents": int,
                   "installments_left": int, "remaining_cents": int,
                   "last_invoice": "AAAA-MM", "frees_cents": int}],
       "remaining_cents": int, "last_invoice": str | None}
      ```
      Por série: `anchor = invoice_month(last_seen_date, closing_day)`,
      `last_invoice = end_month(anchor, installments_left)`,
      `remaining_cents = amount_cents * installments_left`,
      `frees_cents = -amount_cents`. Os meses do cartão vão do mês de calendário
      da referência até o maior `last_invoice`, um por mês, e cada série soma
      `amount_cents` nos meses em que `anchor < mês <= last_invoice`. `assumed` é
      `closing_day is None`. `off_card` é
      `len(installments(conn, today=today))` menos o número de linhas de
      `card_series` que trouxeram série.
      *Considerando 1.1:* as linhas chegam já casadas com o cartão e já com o dia
      de fechamento resolvido.
      *Justificativa:* RF-01 a RF-05 e RF-07. A separação é a norma 23: o que
      calcula é função determinística e testável, sem SQL dentro. O intervalo
      `anchor < mês <= last_invoice` é o mesmo de
      `app/commitments/calendar.py:134`, e a lista de meses é a mesma forma de
      `app/commitments/calendar.py:137-142` — rótulo `AAAA-MM` compara
      lexicograficamente na ordem do tempo, então a varredura não precisa de
      índice. Distribuir exatamente `installments_left` parcelas é o que faz
      RF-05 ser propriedade da construção e não conferência posterior. O nome
      `last_invoice`, e não `ends_month`, existe porque `commitments.ends_month`
      (`app/commitments/series.py:118`) é o mês da última **parcela lançada**:
      dois nomes iguais para dois fatos diferentes na mesma tela é como a
      próxima sessão passa a acreditar que são o mesmo. O módulo não se chama
      `forecast` porque `app/projection/forecast.py:17` já ocupa esse nome e
      `app/routers/summary.py:11` já o importa.

- [ ] **1.3 — Criar `tests/test_commitments_invoice.py`.**
      Os casos: fechamento 5 contra fechamento 20 sobre a mesma série; cartão sem
      linha em `cards`, com `last_invoice` coincidindo com o `ends_month` da
      linha inserida; a base de dois cartões e três séries, com a igualdade entre
      a soma dos meses, o `remaining_cents` do cartão e a soma lida por SQL
      direto; a queda entre `2026-11` e `2026-12`; o cartão sem série viva ao
      lado de um com série; o nome de cartão repetido; e a passagem pelo motor,
      com `load`, `seed_taxonomy`, `classify_all` e `recompute`, conferindo
      `off_card`. O banco é o da fixture `taxonomy_conn`
      (`tests/conftest.py:95-101`), que já roda as migrações em diretório
      temporário. Quem executa é o `pytest` que o CI já roda; **nenhum portão
      novo entra em `scripts/gates/`** e `gates_runner.sh` não é tocado.
      *Considerando 1.1 e 1.2.*
      *Justificativa:* RF-01 a RF-05 e RF-07. Montar `commitments` por `INSERT`
      é o que torna os casos de fechamento discrimináveis: pelo motor, o dia da
      transação e o dia da parcela andam juntos e não dá para variar só o
      fechamento. O caso do motor existe pelo motivo oposto — é o único que prova
      que `commitments.account` guarda o **nome** da conta; sem ele, uma base
      forjada validaria qualquer suposição sobre essa coluna.

---

## Fase 2 — A curva em `/comprometido` (api)

**Objetivo da fase:** `/comprometido` mostra, por cartão, quanto a fatura soma em
cada mês até zerar, com a premissa declarada quando o fechamento não é conhecido
— e nenhum número que a tela já dava muda.

**Linguagem visual:** a seção segue `product/00-linguagem-visual.md`, que é
canônico, com as medidas do `app/static/css/tokens.css` que o item `017`
consolidou. Ela não escolhe nada novo: painel largo (`panel panel-wide`), título
de seção, `lede` para o texto, tabela de dados compacta com `col-month` e
`col-num`, cifra em `cifra` com algarismo tabular, estado vazio em
`empty`/`empty-title`. O único ornamento é a **escala graduada** (`scale`), que o
documento reserva a onde existe distância a percorrer — e uma fatura contada mês
a mês até zerar é literalmente isso. Sinal `−` colado ao número faz o trabalho
que a cor não faz sozinha; a coluna de valores fica em tinta normal, porque
pintar uma coluna inteira de vermelho é o oposto de sinalizar.

**Critérios de aceite:**

- [ ] `estrutural` — RF-06
      Existe `app/templates/fragments/comprometido_fatura.html`, e ele contém
      `id="fatura"` e **não** contém a palavra `<section` mais de uma vez nem a
      sequência `class="headline `. `app/templates/comprometido.html` contém
      `{% include "fragments/comprometido_fatura.html" %}`.
      `app/routers/commitments.py` contém `from app.commitments.invoice import invoice_curve`
      e a chave de contexto `"invoice"`. Nenhum arquivo de `app/static/css/`
      é criado: a pasta segue com exatamente os arquivos `app.css` e
      `tokens.css`
- [ ] `comando` — RF-06
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -c "import re, pathlib; frag = pathlib.Path('app/templates/fragments/comprometido_fatura.html').read_text(encoding='utf-8'); css = pathlib.Path('app/static/css/app.css').read_text(encoding='utf-8') + pathlib.Path('app/static/css/tokens.css').read_text(encoding='utf-8'); names = {n for v in re.findall(r'class=\"([^\"{}]*)\"', frag) for n in v.split()}; assert names, 'nenhuma classe lida'; missing = sorted(n for n in names if '.' + n not in css); assert not missing, missing; print(len(names), 'classes conferidas')"`
      sai com código `0` e imprime um número **maior que zero** antes de
      `classes conferidas`. O número impresso é o controle positivo: sem ele,
      um fragmento sem nenhum atributo `class` estático sairia com código `0`
      tendo conferido nada. O comando reprova com código `1` e imprime a lista
      de classes que nenhuma das duas folhas declara
- [ ] `comportamental` — RF-01, RF-04, RF-06
      *Dado* o painel servido a partir deste repositório com
      `DASH_TODAY=2026-09-05` no ambiente do processo, banco em diretório
      temporário com as migrações aplicadas, usuário semeado, sessão autenticada,
      e a base
      `INSERT INTO accounts (id, name, type, balance_cents) VALUES ('acc-azul', 'Cartão Azul', 'CREDIT', -100000), ('acc-roxo', 'Cartão Roxo', 'CREDIT', -50000)`,
      `INSERT INTO cards (account_id, closing_day) VALUES ('acc-azul', 5)`,
      `INSERT INTO commitments (kind, series_key, description, account, amount_cents, last_seen_date, installment_total, installments_left, ends_month) VALUES ('installment', 'loja azul', 'Loja Azul', 'Cartão Azul', -12000, '2026-08-11', 24, 3, '2026-11'), ('installment', 'posto azul', 'Posto Azul', 'Cartão Azul', -5000, '2026-09-02', 6, 2, '2026-11'), ('installment', 'loja roxa', 'Loja Roxa', 'Cartão Roxo', -20000, '2026-08-20', 10, 1, '2026-09')`
      *Quando* `GET /comprometido` é buscada sem query string
      *Então* a resposta é `200` e o trecho do HTML que vai de `id="fatura"` até
      o primeiro `</section>` seguinte contém, nesta forma:
      `data-cartao="Cartão Azul"`, `data-restante="-46000"`,
      `data-mes="2026-09" data-total="0"`,
      `data-mes="2026-10" data-total="-17000"`,
      `data-mes="2026-11" data-total="-17000"`,
      `data-mes="2026-12" data-total="-12000"`,
      `data-serie="loja azul" data-termina="2026-12" data-devolve="12000"` e
      `data-serie="posto azul" data-termina="2026-11" data-devolve="5000"`; e
      contém também `12/2026` e `−R$ 170,00`, com o sinal `−` sendo o U+2212 que
      `app/routers/render.py:14` declara — o mês e a cifra escritos para o dono,
      além dos atributos escritos para a máquina
- [ ] `comportamental` — RF-03
      *Dado* o painel servido com `DASH_TODAY=2026-09-05` e a mesma base de dois
      cartões e três séries do critério anterior, com sessão autenticada
      *Quando* `GET /comprometido` é buscada sem query string
      *Então*, no recorte que vai de `data-cartao="Cartão Roxo"` até o primeiro
      `</article>` depois dele, aparecem `data-premissa="1"` e a frase
      `Sem dia de fechamento informado, a curva usa o mês do lançamento.`; e no
      recorte equivalente de `data-cartao="Cartão Azul"` — de
      `data-cartao="Cartão Azul"` até o primeiro `</article>` depois dele —
      aparece `data-fechamento="5"` e a frase **não** aparece. O par é o controle
      positivo: sem o cartão que declara a premissa, a ausência dela no outro
      passaria numa seção vazia
- [ ] `comportamental` — RF-05
      *Dado* o painel servido com `DASH_TODAY=2026-09-05` e a mesma base de dois
      cartões e três séries, com sessão autenticada
      *Quando* `GET /comprometido` é buscada sem query string
      *Então*, para **cada** bloco `<article ...>` do trecho `id="fatura"`, a
      soma dos valores de `data-total` daquele bloco é igual ao `data-restante`
      do próprio bloco — `-46000` no bloco de `Cartão Azul` e `-20000` no de
      `Cartão Roxo` —, e o `data-total-cartoes` da seção é igual a `-66000`, a
      soma dos dois. Nenhum dos três valores é zero, e é esse o controle
      positivo: numa tela sem cartão nenhum as igualdades seriam `0 == 0`
- [ ] `comportamental` — RF-07
      *Dado* o painel servido com `DASH_TODAY=2026-09-05`, sessão autenticada, e
      a base de dois cartões e três séries acrescida de
      `INSERT INTO accounts (id, name, type, balance_cents) VALUES ('acc-verde', 'Cartão Verde', 'CREDIT', 0)`
      e `INSERT INTO cards (account_id, closing_day) VALUES ('acc-verde', 10)`,
      sem nenhuma linha de `commitments` com `account = 'Cartão Verde'`
      *Quando* `GET /comprometido` é buscada sem query string
      *Então*, no recorte que vai de `data-cartao="Cartão Verde"` até o primeiro
      `</article>` depois dele, aparece a frase
      `Nenhum parcelamento em aberto neste cartão.` e **não** aparece nenhum
      `data-mes=`; e no recorte de `data-cartao="Cartão Azul"` aparecem quatro
      ocorrências de `data-mes=`, que é o controle positivo da ausência anterior
- [ ] `estrutural` — RF-08
      `tests/test_comprometido_screen.py` define as funções
      `test_the_screen_answers_with_a_session_and_carries_its_three_blocks`,
      `test_the_mark_moves_the_money_in_the_answer_of_the_same_request`,
      `test_the_released_cash_names_the_month_each_series_frees`,
      `test_every_figure_of_the_screen_is_written_as_a_figure` e
      `test_the_calendar_names_its_window_and_calls_the_date_a_forecast`, e
      contém os literais `−R$ 580,00`, `−R$ 280,00`, `R$ 300,00`, `R$ 180,00`,
      `10/2026`, `05/09/2026` e `20/10/2026` — com o `−` sendo o U+2212 de
      `app/routers/render.py:14`. São os totais que a tela já dava antes da
      curva, e eles seguem cobrados pelo mesmo arquivo

> A DoD global é do CI e não se repete aqui.

**Critérios de integração**

- [ ] `comportamental` — RF-05, RF-06, RF-08
      *Dado* o painel servido a partir deste repositório com
      `DASH_TODAY=2026-09-05` no ambiente do processo, banco em diretório
      temporário com as migrações aplicadas, usuário semeado, sessão autenticada,
      uma conta de crédito inserida por SQL
      (`INSERT INTO accounts (id, name, type, balance_cents) VALUES ('acc-cartao', 'Cartão Azul', 'CREDIT', -100000)`),
      `INSERT INTO cards (account_id, closing_day) VALUES ('acc-cartao', 5)`, e
      duas transações **ingeridas pelo carregador** — uma com
      `conta_id='acc-cartao'`, `data='2026-08-11'`, `valor=-120.00`,
      `descricao='Loja Azul'`, `parcela_atual=2`, `parcela_total=24`, e outra na
      conta corrente de teste (`conta_id='acc-1'`), `data='2026-08-20'`,
      `valor=-50.00`, `descricao='Carne Loja'`, `parcela_atual=1`,
      `parcela_total=6` —, seguidas de `seed_taxonomy`, `classify_all` e
      `app.commitments.engine.recompute(conn, today=date(2026, 9, 5))`
      *Quando* `GET /comprometido` é buscada sem query string
      *Então* a resposta é `200`; o trecho `id="parcelamentos"` traz **duas**
      linhas com `data-restante`, valendo `-264000` e `-25000`, que somam
      `-289000`; o trecho `id="fatura"` traz **um** bloco `data-cartao`, com
      `data-restante="-264000"`, cujos `data-total` somam o mesmo `-264000`; a
      chave `loja azul` aparece em `id="fatura"` e a chave `carne loja` **não**
      aparece; e o trecho `id="fatura"` traz `data-fora="1"` e a expressão
      `fora de cartão`. As duas leituras da mesma base saem de caminhos
      diferentes — a curva pela consulta nova, a tabela pelo produto que
      `app/templates/fragments/comprometido_parcelamentos.html:27` já imprimia —
      e a diferença entre elas é exatamente o parcelamento que não está em
      cartão, contado e nomeado na tela em vez de sumir. Os dois totais são
      diferentes de zero, e é esse o controle positivo
- [ ] `comando` — RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-07, RF-08
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_commitments_invoice.py tests/test_comprometido_screen.py`
      sai com código `0`, e `tests/test_comprometido_screen.py` define uma
      fixture nova para a base de cartões, sem alterar a fixture `client` nem a
      `empty_client` que o arquivo já traz, e um teste que afirma a igualdade
      entre a soma dos `data-total` e o `data-restante` de cada bloco de cartão.
      O código de saída é lido do próprio `pytest` — encadear `| tail` leria o
      código do `tail`

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **2.1 — Modificar `app/routers/commitments.py`: a curva entra no
      contexto.**
      Import `from app.commitments.invoice import invoice_curve` e, em `_context`
      (linhas 100-127), uma chave a mais: `"invoice": invoice_curve(conn, today=today)`.
      Nada mais muda na rota.
      *Considerando 1.2:* a leitura chega pronta, com os meses já somados.
      *Justificativa:* RF-06. Norma 30: a rota traduz HTTP e não monta consulta —
      chamar uma função de domínio é o que `_context` já faz com
      `released_cash` e `calendar` (linhas 109-110). Os nomes de leitura das
      séries já estão no contexto: `_labels` (linha 121) é montado sobre
      `recurring + live`, e as séries da curva são subconjunto de `live`, então a
      seção nova usa o mesmo mapa `labels` e nenhuma consulta a mais.

- [ ] **2.2 — Criar `app/templates/fragments/comprometido_fatura.html`.**
      Uma `<section id="fatura" class="panel panel-wide">` com título, duas
      linhas de `lede` — a curva distribui o que já está lançado e não prevê
      compra nova; o mês é o da fatura que fecha —, a `scale`, e um
      `<article class="released" data-cartao="{{ card['name'] }}" data-restante="{{ card['remaining_cents'] }}">`
      por cartão, nesta ordem de atributos. Dentro de cada bloco: o nome do
      cartão em `eyebrow`; a linha do fechamento, que é
      `data-fechamento="{{ card['closing_day'] }}"` quando ele é conhecido e
      `data-premissa="1"` com a frase
      `Sem dia de fechamento informado, a curva usa o mês do lançamento.` quando
      não é; uma tabela `data-table data-table-compact` de meses, com
      `<tr data-mes="{{ step['month'] }}" data-total="{{ step['total_cents'] }}">`
      nesta ordem, mês em `col-month` pelo filtro `mes` e valor em `col-num`
      dentro de `<span class="cifra">` pelo filtro `brl`; e uma segunda tabela
      com as séries, `<tr data-serie="..." data-termina="..." data-devolve="...">`
      nesta ordem, usando o macro `cell_name` de `fragments/celula.html`. Cartão
      sem série vira bloco `empty` com o título
      `Nenhum parcelamento em aberto neste cartão.`. No pé da seção, o total em
      `headline-small` com `data-total-cartoes="{{ invoice['remaining_cents'] }}"`
      e, quando `invoice['off_card']` não é zero, uma `lede` com
      `data-fora="{{ invoice['off_card'] }}"` dizendo quantos parcelamentos em
      aberto ficaram **fora de cartão** e por quê. Seção sem cartão nenhum mostra
      o estado vazio dizendo que não há conta de crédito carregada e onde
      informar o fechamento. Todos os atributos `class` são estáticos.
      *Considerando 2.1:* `invoice` está no contexto e `labels` já resolve os
      nomes.
      *Justificativa:* RF-01, RF-03, RF-04, RF-06, RF-07. Três restrições de
      forma não são estilo e sim condição de a fase não quebrar o que já existe.
      A seção é **uma** `<section>` sem seção aninhada, porque
      `tests/test_comprometido_screen.py:65-68` recorta do `id=` até o primeiro
      `</section>`. Nenhum elemento usa a classe `headline`, porque
      `tests/test_comprometido_screen.py:25-26` acha o total comprometido pela
      primeira ocorrência de `class="headline cifra"` e a economia projetada pela
      **última**: um `headline` novo nesta seção mudaria o número que aqueles
      testes leem sem que nenhum número tivesse mudado. E toda cifra sai pelo
      filtro `brl`, porque `tests/test_comprometido_screen.py:184-189` exige que
      **todo** conteúdo de elemento com classe `cifra` case com
      `^−?R\$ [\d.]+,\d{2}$` — um dia de fechamento impresso dentro de um `cifra`
      reprovaria ali. A classe `released` é reusada por papel e não por assunto:
      `app/static/css/app.css:592-600` a define como sub-bloco preso ao painel
      por um fio, que é o que cada cartão é dentro desta seção, e o escopo do
      item não inclui `app/static/css/`. A `scale` é o único ornamento, e
      `product/00-linguagem-visual.md` a reserva a onde há distância a percorrer.

- [ ] **2.3 — Modificar `app/templates/comprometido.html`: o include.**
      `{% include "fragments/comprometido_fatura.html" %}` entre a linha 32
      (parcelamentos) e a linha 33 (calendário).
      *Considerando 2.2.*
      *Justificativa:* RF-06. A ordem de leitura é a do assunto: o que falta
      pagar, depois como isso se distribui pelos meses, e por último o que sai
      nos próximos 45 dias. Pôr a curva depois do calendário separaria dois
      blocos que respondem à mesma pergunta com um terceiro no meio.

- [ ] **2.4 — Modificar `tests/test_comprometido_screen.py`: a fixture de
      cartões e os testes da curva.**
      Uma fixture nova, com base própria montada por `INSERT` sobre `_base`
      (linhas 103-111), com os três cartões e as três séries; e uma segunda base,
      ingerida por `load` + `seed_taxonomy` + `classify_all` + `recompute`, para
      o critério de integração. As fixtures `client` (linhas 114-155) e
      `empty_client` (linhas 157-164) **não** são tocadas, e nenhum teste
      existente é reescrito. Testes novos: os atributos da curva; o par premissa
      declarada / fechamento conhecido; a igualdade entre a soma dos meses e o
      restante de cada cartão; o cartão sem parcelamento; e, na base ingerida, a
      conferência entre `id="fatura"` e `id="parcelamentos"` com o parcelamento
      fora de cartão contado. Quem executa é o `pytest` que o CI já roda;
      **nenhum portão novo entra em `scripts/gates/`** e `gates_runner.sh` não é
      tocado.
      *Considerando 2.1, 2.2 e 2.3.*
      *Justificativa:* RF-01, RF-03, RF-04, RF-05, RF-06, RF-07, RF-08. A base
      de `client` não ganha cartão porque os números que ela fixa —
      `−R$ 580,00`, `R$ 300,00`, `R$ 180,00`, a janela `05/09/2026`–`20/10/2026`
      e as contagens de linhas — são justamente a prova de RF-08: mexer nela para
      caber a curva apagaria a medição que diz que nada mudou. A base ingerida do
      critério de integração existe porque só ela liga a curva ao motor: com
      `commitments` montado à mão, uma suposição errada sobre a coluna que liga
      série e cartão passaria nos dois lados.

---

## Execução sugerida

1. **Fase 1, bloqueante.** Toca `app/queries/invoices.py`,
   `app/commitments/invoice.py` e `tests/test_commitments_invoice.py` — três
   arquivos novos, nenhum arquivo existente.
2. **Fase 2 depois da 1.** Toca `app/routers/commitments.py`,
   `app/templates/comprometido.html`,
   `app/templates/fragments/comprometido_fatura.html` e
   `tests/test_comprometido_screen.py`.

As duas **não** correm em paralelo, e a interseção vazia de arquivos não muda
isso. A fase 2 consome a forma do dado que a fase 1 fixa: o nome dos campos, o
significado de `last_invoice` e a regra do mês da fatura viram atributo de HTML e
asserção de tela. Num par de `git worktree`, a fase 2 escreveria contra um
contrato ainda não decidido e o primeiro veredicto chegaria depois de o template
já estar feito — que é o momento em que refazer custa caro.

## Pendências que viram item de roadmap

- **Dois meses de término na mesma tela.** A coluna "Termina em" da tabela de
  parcelamentos (`app/templates/fragments/comprometido_parcelamentos.html:32`)
  segue nomeando o mês da última **parcela lançada**, que é o `ends_month` que o
  motor grava (`app/commitments/series.py:118`), enquanto a curva nomeia o mês da
  última **fatura**. Com dia de fechamento informado e compra depois dele, os
  dois divergem em um mês. Unificar exige mudar `ends_month` no motor, e
  `released_cash` (`app/commitments/live.py:62-68`) é chaveado por ele — o
  "Caixa liberado" mudaria de mês, que é o que RF-08 proíbe. Fica para um item
  que trate o motor e o caixa liberado juntos.
- **Parcelamento fora de cartão não tem curva.** Uma compra parcelada que não
  está em conta de crédito continua só na tabela de parcelamentos, com o total e
  o mês de término, sem distribuição mensal. A tela conta quantos são; dar a eles
  a mesma leitura mensal é outro item, e ele precisa decidir o que substitui o
  dia de fechamento.
- **A curva não separa a fatura já fechada.** O mês corrente pode aparecer com
  zero quando todas as parcelas daquele mês já foram lançadas: a curva responde
  "o que falta pagar", e o que já está na fatura deste mês não falta mais. Um
  item que queira mostrar a fatura corrente inteira — lançado mais a lançar —
  precisa do valor já lançado no ciclo, que hoje ninguém soma.

## Validações de campo pendentes

- **A curva contra a fatura real do banco.** Nenhum critério deste plano observa
  se o mês em que a curva põe uma parcela é o mês em que o banco a cobra: o que
  se prova é que a regra do dia de fechamento é aplicada como decidida, sobre
  base montada. Conferir uma parcela real contra a fatura que o banco emitiu é
  leitura de documento externo, e o item de origem é
  `026-evolucao-da-fatura-mes-a-mes`.
- **O dia de fechamento de cada cartão do dono.** A curva usa o que estiver em
  `cards.closing_day`, e esse campo só é preenchido à mão em `/configuracao`.
  Enquanto ele estiver vazio, a tela declara a premissa — mas ninguém além do
  dono sabe se o dia informado é o certo. Item de origem:
  `026-evolucao-da-fatura-mes-a-mes`.
