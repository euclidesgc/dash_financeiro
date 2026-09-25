# Investigação: data do lançamento cortada em UTC

## Relato
- **Sintoma:** lançamentos feitos à noite aparecem no dia seguinte. O salário pago em 31/03/2026 às 23:59 entra em abril; a assinatura do YouTube cobrada em 31/08 às 22:02 entra em setembro. Todo total mensal (gasto, entrada, resultado) soma o lançamento no mês errado.
- **Esperado:** a data do lançamento é o dia do calendário em São Paulo, o fuso em que o dono vive e em que o banco mostra o extrato.
- **Como reproduzir:** rodar `python ingestao/pluggy_consolidate.py` sobre o bruto de 05/09/2026 e procurar o lançamento "Salário REMUNERACAO/SALARIO" de R$ 2.928,46: a Pluggy manda `2026-04-01T02:59:00.000Z`, o consolidado grava `2026-04-01`, e o painel em `http://localhost:5173/app/` o conta em abril.
- **Onde:** consolidação dos brutos da Pluggy, antes da carga no banco; afeta toda tela que agrupa por dia ou por mês. Desde a primeira versão do script.

## Causa raiz
`ingestao/pluggy_consolidate.py:198` grava `"data": (t.get("date") or "")[:10]`. A Pluggy devolve a data como instante em UTC (`...Z`), e os dez primeiros caracteres são o dia em UTC. Em São Paulo (UTC−3, sem horário de verão desde 2019), tudo o que acontece entre 21:00 e 23:59 cai no dia seguinte. No bruto atual, 261 lançamentos mudam de dia e 13 mudam de mês, entre eles 4 salários do último dia do mês às 23:59. Os lançamentos sem hora (fatura futura, parcela) vêm como `T03:00:00.000Z`, que é meia-noite em São Paulo; nenhum vem como meia-noite em UTC, então a conversão não empurra nenhum para o dia anterior.

O mesmo corte aparece no inventário da extração (`ingestao/pluggy_extract.py:321-327`, primeira e última data de cada conta), que só é impresso e gravado no `inventario_*.json`.

## Evidência
- Teste de regressão: `tests/test_pluggy_scripts.py` › `test_the_consolidated_date_is_the_day_in_sao_paulo_not_in_utc`
- Falha hoje com: `AssertionError: assert ['2026-04-01'] == ['2026-03-31']` e `assert ['2026-09-01'] == ['2026-08-31']`; os casos de meia-noite local (`T03:00:00.000Z`) e de madrugada (`T03:43:04.000Z`) passam, como devem.
- Medição sobre o bruto de 05/09/2026 (o mesmo dos números congelados), com a conta do relatório de origem reproduzida ao centavo antes da mudança: transferências (152), estornos (18), recorrências (55) e parcelamentos (100) não mudam; o fluxo mensal muda, porque os lançamentos das 21h às 23h59 do último dia do mês voltam ao mês certo.

## Correção proposta
- `ingestao/pluggy_consolidate.py` — função `local_date` que converte o instante da Pluggy para o dia em `America/Sao_Paulo` (`zoneinfo`, da biblioteca padrão); valor sem fuso é tratado como já local, e ausência continua como texto vazio.
- `ingestao/pluggy_consolidate.py` — a coluna `data` usa `local_date`; o script continua rodando sozinho, sem importar outro módulo do projeto.
- `ingestao/pluggy_extract.py` — primeira e última data do inventário usam `local_date`, importada da consolidação.
- `docs/plano.md` — reconciliação dos números de referência que mudam (norma 28): déficit real R$ 4.940,72 → R$ 5.661,30/mês; gasto total de 6 meses R$ 103.772,33 → R$ 104.197,31; renda regular de R$ 9.123 a R$ 13.593 → R$ 9.123 a R$ 13.148.
- `tests/test_frozen_numbers.py` — o novo total congelado entra na varredura que proíbe número de referência dentro de `app/`.
- **Risco:** a carga (`app/ingest/loader.py`) grava a coluna `date` de novo em todo lançamento já existente (upsert por id), então a base real passa a ter a data certa na próxima sincronização, sem migração. Quem lê `date` (gastos, teto, comprometido, calendário) passa a ver os lançamentos no dia e mês certos.
- **Fora da correção:** os números citados em documentos históricos de itens já entregues (`product/items/…`, `docs/features/…`) ficam como estavam, porque registram o que foi medido na época; o resumo do produto em `CLAUDE.md` e `product/roadmap.md` cita o déficit antigo e é configuração do dono.

## Pontos em aberto
Nenhum.
