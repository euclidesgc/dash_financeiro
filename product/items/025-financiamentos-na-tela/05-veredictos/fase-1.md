VEREDICTO: APROVADO

## Portões

| Portão | Resultado | Saída executada |
|---|---|---|
| `ruff check` (via `scripts/lint.sh`) | OK | `All checks passed!` — exit `0` |
| `ruff format --check` (via `scripts/lint.sh`) | OK | `145 files already formatted` — exit `0` |
| `mypy --strict` | **não é portão deste projeto** | `.venv/bin/mypy` não existe e não há configuração em `pyproject.toml`, `scripts/lint.sh` nem nos workflows. Norma 35 declara isso como item de roadmap. Não medi, e não conto como aprovado nem como reprovado |
| `pytest` (suíte inteira) | OK | `556 passed, 2 warnings in 45.07s` — exit `0`. Coletou 556 testes, não é o falso passe do exit `5` |
| `gates_runner.sh` | OK | `✓ gates: limpos (árvore completa, 509 arquivo(s) considerados).` — exit `0`, **509 > 0**, portão mediu de verdade |

## Critérios de aceite

| # | Tipo | RF | Passou | Evidência executada |
|---|---|---|---|---|
| 1 | comando | RF-01 | **sim** | Comando literal do critério, exit `0`. `PRAGMA table_info(financings)` devolveu exatamente `{'kind': ('TEXT',1,1), 'monthly_rate_bp': ('INTEGER',1,0), 'term_months': ('INTEGER',1,0), 'balance_cents': ('INTEGER',0,0), 'payment_cents': ('INTEGER',0,0), 'first_due_date': ('TEXT',0,0)}`. `migrations applied: 12` |
| 2 | estrutural | RF-01 | **sim** | `ls app/migrations/sql/` devolve os doze nomes exatos do critério e só eles. `git show f73c359 --name-status` mostra `014_financings.sql` como único arquivo novo da pasta no commit. `tests/test_migrations.py:33-46` traz a mesma lista de doze; `:20` tem `"financings"` em `EXPECTED_TABLES`; `:73` afirma `(len(EXPECTED_MIGRATIONS), "001", "014")` |
| 3 | comportamental | RF-01, RF-02 | **sim** | Base nova em tmp, `accounts` vazia, `DASH_MANUAL_DIR` com os dois JSON do critério. `rebuild` duas vezes devolveu `2` e `2`; `ladder` devolveu, nesta ordem: `vehicle / CDC do veículo / -3917636 / 163 / 45 / -123533` e `mortgage / Financiamento imobiliário / -23858518 / 72 / 370 / None`. `SELECT COUNT(*) FROM financings` = `2` |
| 4 | comportamental | RF-03 | **sim** | Mesma base e mesma pasta `M`, linha `mortgage/1000/12/-10000000` inserida antes de qualquer reconstrução: `ladder` devolveu **um** degrau `mortgage / 1000 / 12 / -10000000`; `COUNT(financings)` = `1`; os dois JSON continuam no disco e nenhum entrou |
| 5 | estrutural | RF-03 | **sim** | `grep -F` em `app/debts/ladder.py`: `import json`, `MORTGAGE_FILE`, `VEHICLE_FILE`, `DASH_MANUAL_DIR`, `manual_dir` e `.json` **todos ausentes**. `app/financings/store.py:10-13` define `MANUAL_DIR = "DASH_MANUAL_DIR"`, `MORTGAGE_FILE = "financiamento_caixa.json"`, `VEHICLE_FILE = "cdc_safra_veiculo.json"` |
| 6 | comportamental | RF-04 | **sim** (com ressalva de redação, abaixo) | Pasta manual inexistente, `financings` vazia, uma conta `id='a'`, `type='BANK'`, `balance_cents=-1000`: `rebuild` = `1`, sem exceção; `ladder` = `[]`; `without_rate` = 1 linha; `COUNT(financings)` = `0` |
| 7 | comportamental | RF-06 | **sim** | Depois de `UPDATE debts SET monthly_rate_bp=352 WHERE kind='overdraft'` e `UPDATE financings SET monthly_rate_bp=500 WHERE kind='mortgage'` e segunda reconstrução: degrau `mortgage` com `monthly_rate_bp=500` e degrau `overdraft` com `monthly_rate_bp=352`. As duas metades andam juntas, como o critério exige |
| 8 | comportamental | RF-07, RF-08 | **sim** | Linha `vehicle/163/12/NULL/-100000/2026-01-31`, `today=2026-09-05`: **sem exceção**, `rebuild` = `1`, degrau com `term_months=4` e `balance_cents=-384217` (`< 0`) |
| 9 | comportamental | RF-07 | **sim** | Caso 1: `2026-09-05` → `term=45`, `balance=-3917636`; `2026-10-05` → `term=44`, `balance=-3857960` (maior que `-3917636` e ainda negativo). Caso 2 (`term=12`, `first_due=2020-01-10`): `rebuild` = `0`, `ladder` = `[]`, `COUNT(financings)` = `1` |
| 10 | comando | RF-01..07 | **sim** | `pytest -q tests/test_debts.py tests/test_financings.py tests/test_migrations.py` → `30 passed in 0.83s`, exit `0`. `tests/test_financings.py` define as sete funções que cobrem os seis cenários exigidos. `tests/test_debts.py` mantém `test_the_vehicle_step_is_built_by_the_loader_and_not_by_the_test` e as constantes `VEHICLE_BALANCE=3917636`, `PAYMENT=123533`, `RATE_BP=163`, `TERM=45` intactas |

## Minha própria comparação numérica da escada

Instrumento meu, independente da suíte do avaliado: extraí de `git show f73c359^:app/debts/ladder.py` a versão anterior do carregador — a que lia os dois JSON — para um módulo fora do repositório, e rodei as duas origens sobre bases SQLite recém-migradas, uma para cada, com a mesma data fixada.

**Com os arquivos reais do dono** (`data/manual/*.json`, copiados só para leitura):

| Data | Origem | kind | saldo (centavos) | taxa (bp) | prazo | parcela |
|---|---|---|---|---|---|---|
| 2026-09-05 | tabela | vehicle | −3.917.636 | 163 | 45 | −123.533 |
| 2026-09-05 | JSON | vehicle | −3.917.636 | 163 | 45 | −123.533 |
| 2026-09-05 | tabela | mortgage | −23.858.518 | 72 | 370 | None |
| 2026-09-05 | JSON | mortgage | −23.858.518 | 72 | 370 | None |
| 2026-10-05 | ambas | vehicle | −3.857.960 | 163 | 44 | −123.533 |
| 2027-06-11 | ambas | vehicle | −3.275.150 | 163 | 35 | −123.533 |
| 2029-01-01 | ambas | vehicle | −1.821.361 | 163 | 17 | −123.533 |

Cinco datas com os arquivos reais e seis com os arquivos do critério: **zero divergências**, degrau a degrau, nos seis campos. Os R$ 39.176,36 e R$ 238.585,18 de 05/09/2026 são os mesmos dos dois lados.

**O saldo do veículo é calculado, não copiado.** Sobre a mesma linha da tabela, variando só a data: −4.706.081 (60 meses) → −4.413.437 (54) → −3.917.636 (45) → −3.133.711 (33) → −1.234.843 (11) → sem degrau. Estritamente crescente em direção a zero, sempre negativo, e `financings.balance_cents` do veículo **continua `NULL`** depois de todas as reconstruções — nada foi congelado na tabela.

**A máquina que nunca recebeu os contratos sobe.** Base nova, `DASH_MANUAL_DIR` para pasta inexistente, `financings` vazia: `GET /login` → 200; `GET /` sem sessão → 302 para `/login`; autenticado, `GET /` → 200 e `GET /dividas` → 200; `ladder` e `without_rate` vazias; `python -m app.debts.ladder` imprime `debts rebuilt: 0 reference=2026-09-05`, rc 0. Com os contratos presentes, `/dividas` responde 200 e a página traz `CDC do veículo`, `Financiamento imobiliário`, `39.176,36`, `238.585,18`, `1,63` e `0,72` — os números chegam à tela sem mudar de valor ao mudar de lugar.

**Tentativas de quebra.** Dia 31 atravessando fevereiro: passa (prazos 4 e 52, saldos negativos). Vencimento 29/02 de ano bissexto: passa. Prazo zero, no veículo e na mortgage: passa, sem exceção e sem saldo positivo. Todas as parcelas vencidas: passa, e o código anterior emitia um degrau fantasma de saldo 0 e prazo 0 que este some. **Taxa zero no veículo: `ZeroDivisionError`** — o único que não passou; detalhe abaixo.

## Instrumentos do implementer

Nenhum critério dependeu da suíte do avaliado como prova. O critério 10 é sobre a suíte por definição, e ali eu inspecionei o oráculo de `tests/test_financings.py:31-70`: é uma reimplementação da aritmética anterior, não uma comparação da tabela contra ela mesma — conferi caractere a caractere contra o `app/debts/ladder.py` de `f73c359^` e bate. Todos os demais critérios foram provados com harness meu, em bases temporárias.

## Achados que não reprovam

1. **Taxa zero no veículo derruba a reconstrução.** `app/financings/math.py:present_value_cents` divide por `rate`; há guarda para `left <= 0`, não para `rate == 0`. Uma linha `vehicle` com `monthly_rate_bp=0` levanta `ZeroDivisionError`. **Não reprova porque é idêntico em `develop`** (provei rodando o carregador anterior com um JSON de juros 0: mesma exceção) e porque nenhum caminho de código que esta fase adiciona escreve taxa zero — só SQL à mão chega lá. O raio de dano hoje também é menor do que um 500: o único chamador de `rebuild` é `app/sync/__init__.py:104`, dentro do `try/except` que rebaixa a corrida para `failed`. Correção de uma linha, com teste, **antes da fase 2**, que é quando a tela abre o primeiro caminho para o dono digitar essa taxa.
2. **A migração 014 aceita linha de veículo que quebra o rebuild.** `payment_cents` e `first_due_date` são anuláveis para qualquer `kind`; uma linha `vehicle` com `first_due_date NULL` levanta `TypeError: fromisoformat: argument must be str`, e com `payment_cents NULL`, `TypeError: unsupported operand type(s) for *`. Sugestão: `CHECK (kind <> 'vehicle' OR (payment_cents IS NOT NULL AND first_due_date IS NOT NULL))`, ou validação no caminho de escrita da fase 2.
3. **Reconciliação de merge pendente.** A base do ramo está atrás de `develop`, que tem `013_cards.sql` e `015_advisor_config.sql`. Depois do merge, `EXPECTED_MIGRATIONS` e `EXPECTED_TABLES` de `tests/test_migrations.py` precisam receber os nomes de `develop`. Sem risco de dados: `app/migrations/runner.py` ordena por nome e pula versões já aplicadas, sem exigir ordem monotônica — aplicar 014 depois de 015 na base do dono funciona.
4. **`debts.source` mudou de valor.** Era o nome do arquivo, agora é `financings` nos dois degraus. Nenhum consumidor lê esse campo, mas relatório ou documento que cite a origem muda de texto.
5. **Redação do critério 6.** O critério descreve a linha de `accounts` por três colunas. Se `name` ficar `NULL`, `rebuild` levanta `IntegrityError`. Confirmei que **o código anterior faz exatamente o mesmo**, então não é regressão desta fase. Julguei o critério pelo caso com nome.
6. **A mensagem do commit exagera um dos defeitos.** Ela afirma que o contrato quitado "returned a balance of inverted sign". Não reproduzi inversão de sinal: o `_paid` anterior limitava as parcelas ao prazo, então `left` chegava a 0 e o saldo saía `0`, com prazo `0` — degrau fantasma, não sinal invertido. A correção continua sendo melhoria; só a descrição está acima do que os números mostram.
