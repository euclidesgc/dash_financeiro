O despacho trouxe só o objetivo e os critérios; nenhum plano, spec ou histórico veio junto, e `product/items/022-.../` não foi aberto.

```
VEREDICTO: APROVADO
```

## Portões

| Portão | Resultado | Saída |
|---|---|---|
| `bash scripts/lint.sh` (ruff check + format --check nos 3 pacotes) | **OK** | `All checks passed!` / `140 files already formatted` — exit `0` |
| `env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` | **OK** | `540 passed, 2 warnings in 37.97s` — exit `0` lido em arquivo, não por cano |
| `bash scripts/gates/gates_runner.sh` | **OK e mediu** | `✓ gates: limpos (árvore completa, 495 arquivo(s) considerados).` — 495 > 0, sem passe falso |
| `mypy --strict src` | **não existe nesta stack** | não instalado no venv, ausente do `pyproject.toml`; a norma 35 do repositório diz que `mypy --strict` ainda não roda e é item de roadmap. Não é portão que falhou em medir — é portão que este projeto não tem. |

## Critérios

Base de trabalho montada por mim, do zero: SQLite temporário fora do repositório, 11 migrações, semente da taxonomia, usuário sem relação com o `.env` do dono, e os seis lançamentos carregados pelo `app.ingest.loader.ingest` na categoria `Housing` — que a semente classifica em `fixa × essencial`, o cruzamento de slug `piso`. Servidor **real** (`uvicorn --factory app.main:create_app`, porta 8877) com `DASH_ENV_FILE=/dev/null` e `DASH_TODAY=2026-09-05` no ambiente do processo; sessão obtida por `POST /login` (302 + cookie `dash_session`); páginas buscadas por `curl`. Nada disso passa pela suíte do avaliado.

| # | Tipo | RF | Passou | Evidência executada |
|---|---|---|---|---|
| 1 | estrutural | 01, 02, 06 | **sim** | `app/queries/period.py:46` `def month_end`, `:50` `def covers_whole_months`; `CLOSED_MONTHS` não ocorre em lugar nenhum da árvore (grep). `app/queries/ahead.py:12-20`: `@dataclass(frozen=True) class Ahead` com `entries: int` e `amount_cents: int`, e `def posted_ahead(...) -> Ahead`. `app/routers/spending.py:22` `from app.routers.reference import DATE_FIELD, Reference, screen_date`; grep de `screen_date(None)` no arquivo: sem ocorrência (o uso real é `:106` `screen_date(params.get(DATE_FIELD))`). `meses fechados` não ocorre em `gastos_tabela.html`. |
| 2 | comportamental | 01, 04 | **sim** | `GET /gastos` → `HTTP=200`; `name="inicio" type="date" value="2026-09-01"`, `name="fim" type="date" value="2026-09-05"`; `2 lançamentos de 01/09/2026 a 05/09/2026.` com `−R$ 230,00`; nenhum `id="recusa"`. |
| 3 | comportamental | 02 | **sim** | `GET /gastos?data=2026-08-20` → `200`; `value="2026-08-01"` e `value="2026-08-20"`; `1 lançamento de 01/08/2026 a 20/08/2026.` com `−R$ 111,00`; `<input type="hidden" name="data" value="2026-08-20">` presente na forma exata; sem `id="recusa"`. |
| 4 | comportamental | 03 | **sim** | `GET /gastos?data=banana` → `200`; `<p class="notice" id="recusa" role="alert">data inválida: data (banana)</p>`; campos em `value="2026-09-01"` / `value="2026-09-05"`. |
| 5 | comportamental | 05 | **sim** | `?inicio=2026-08-01&fim=2026-08-31` → `200`, `1 lançamento de 01/08/2026 a 31/08/2026.` com `−R$ 111,00`. `?inicio=ontem&fim=2026-08-31` → `200`, campos em `value="2026-09-01"` / `value="2026-09-05"` (cai no padrão, não derruba). |
| 6 | comportamental | 06 | **sim** | Recorte de `id="posterior"` ao primeiro `</p>`: `2 lançamentos do mês já estão postados depois de 05/09/2026, somando <span class="cifra">−R$ 102,00</span>, fora deste total.` — contém `2 lançamento`, `−R$ 102,00`, `05/09/2026`, e não contém `77,00` (o controle negativo de outubro fica fora). Frase do total segue `2 lançamentos de 01/09/2026 a 05/09/2026.` com `−R$ 230,00`. |
| 7 | comportamental | 06 | **sim** | `?inicio=2026-09-01&fim=2026-09-30` → `200`; `id="posterior"` ausente; `4 lançamentos de 01/09/2026 a 30/09/2026.` com `−R$ 332,00`. |
| 8 | comportamental | 07 | **sim** | `?inicio=2026-08-20&fim=2026-09-05` → `200`; recorte `id="cruzamentos"`→`id="residuo"`: `<p class="lede">No período, <span class="cifra">−R$ 341,00</span>.</p>`; sem `Média mensal` e sem `−R$ 170,50`. |
| 9 | comportamental | 07, 08 | **sim** | `?inicio=2026-03-01&fim=2026-08-31` → `200`; mesmo recorte: `<p class="lede">Média mensal de <span class="cifra">−R$ 18,50</span>.</p>` (total −R$ 111,00 ÷ 6). |
| 10 | comando | 01, 06, 07, 08 | **sim** | `pytest -q tests/test_period.py tests/test_ahead.py tests/test_crossings.py tests/test_gastos_screen.py` → `53 passed`, exit `0` gravado em arquivo. `tests/test_period.py:15,19,44,52,56,60` trazem as seis afirmações exigidas. `tests/test_ahead.py:30-43` afirma transferência e estorno fora da contagem e da soma. `tests/test_crossings.py:96-98` segue afirmando `monthly_average_cents == round(total/6)` para `2026-03-01`→`2026-08-31`. |

## A tela mente sobre dinheiro?

Testei ativamente, além dos critérios.

**Invariante 25 vale no bloco novo, provado sem a suíte do avaliado.** Injetei na base uma transferência entre contas próprias de −R$ 500,00 em `2026-09-10` e um par estornado de −R$ 900,00/+R$ 900,00 em `2026-09-11` — todos depois da data de referência e dentro do mês. O bloco `id="posterior"` continuou dizendo `2 lançamentos` e `−R$ 102,00`, e a barra de setembro da série continuou `−R$ 332,00`. Nada de transferência ou estorno entrou na contagem, na soma nem na série.

**Nenhum total soma o que a tela declara fora.** O guarda em `app/routers/spending.py:142` (`if end > reference_iso: return Ahead(0, 0)`) mais o intervalo `date > ? AND date <= ?` tornam impossível o bloco "fora deste total" nomear um lançamento que já está no total: os lançamentos do bloco são sempre posteriores à referência, e a referência é sempre ≥ o fim da janela quando o bloco aparece. Não há dupla contagem em nenhuma janela.

## Achados que não reprovam

1. **O bloco "posterior" aparece em janela que não tem relação com o mês de referência.** Em `?inicio=2026-08-01&fim=2026-08-31` e em `?inicio=2026-03-01&fim=2026-08-31` a tela imprime, logo abaixo do total, `2 lançamentos do mês já estão postados depois de 05/09/2026, somando −R$ 102,00, fora deste total.` Cada oração é verdadeira sobre o número, e por isso não reprovo — mas "do mês", sem dizer qual, colado num total de agosto ou do semestre de referência, convida a ler R$ 102,00 como gasto daquela janela que faltou somar. A janela `2026-03-01`→`2026-08-31` é justamente a dos números congelados de `docs/plano.md`, o pior lugar para pendurar um número de outro período. A causa é o guarda comparar só `end > referência`, sem exigir que a janela termine na data de referência (ou pertença ao mês dela). Correção com teste, não rodada nova.

2. **A série de treze meses passou a terminar num mês em curso, por padrão.** `monthly_series` soma o mês de calendário inteiro, ignorando o fim da janela: na abertura padrão a última barra é `2026-09 = −R$ 332,00` (mês cheio, inclusive o lançamento de 30/09), ao lado de doze meses fechados, e o painel diz apenas "Treze meses até 2026-09". Os rótulos estão corretos e a mesma página mostra `−R$ 230,00` para `01/09` a `05/09` — dois números de setembro, cada um com seu rótulo certo. Antes desta fase a janela padrão terminava em mês fechado e a comparação era homogênea; agora a última barra não é comparável às outras e nada na tela diz isso.

3. **Redundância no painel quando a janela não cobre meses inteiros.** O cruzamento imprime o total em `crossing-total` e repete o mesmo número na linha seguinte como `No período, <total>.` (`app/templates/fragments/gastos_painel.html:44-48`).

4. **O ramo está 6 commits atrás de `develop`, e isso envenena o artefato de revisão.** `git diff develop` mostra como remoção a varredura recursiva do guarda de rota do item 020 (`tests/test_route_guard.py`), a limpeza de `__pycache__` em `tests/test_frozen_numbers.py` e quatro documentos de produto — nada disso é obra da fase. `git log develop..HEAD` traz um único commit, `c7426dc`, que toca nove arquivos e nenhum desses. O merge não reverte 020; o diff só mente porque a base é antiga. Confirmei que o código da fase sobrevive ao guarda mais estrito de `develop`: `grep -rn "date.today()" app/routers/` não acusa nada.

5. **Regra 24 confirmada:** `GET /gastos` sem cookie responde `302` para `/login`.

## Instrumentos do implementer

Só o critério 10 depende da suíte do avaliado, por definição — e mesmo nele li os três arquivos para confirmar que as afirmações nomeadas existem, em vez de aceitar o verde. Os critérios 2 a 9 e a checagem de invariante 25 foram medidos contra servidor real com base e cliente meus.
