# Investigação: a consolidação fica com a cópia mais antiga de cada lançamento

## Relato
- **Sintoma:** o painel mostra lançamentos como estavam na primeira extração, não como a Pluggy os devolve hoje. Três compras pendentes de cartão que a Pluggy deixou de devolver (Spotify R$ 23,90, BetterMe R$ 99,99 e YouTube R$ 1,99, total R$ 125,88) continuam somando no gasto de agosto; 11 parcelas de cartão aparecem em 08/09 em vez de 06/09, e três parcelas do Mercado Livre aparecem em maio em vez de 11/09/2026.
- **Esperado:** cada lançamento vale pela cópia mais recente que a Pluggy devolveu; a compra pendente que a extração mais nova da conta não devolve mais sai do painel.
- **Como reproduzir:** com os brutos de 05/09 e de 22/09/2026 em `data/raw/`, rodar `python ingestao/pluggy_consolidate.py` e procurar a parcela "OTICA BARDASSON E 05/10" de R$ 558,00: o bruto de 22/09 diz `2026-09-06`, o consolidado grava `2026-09-08`, que é a data do bruto de 05/09.
- **Onde:** consolidação dos brutos da Pluggy (`ingestao/pluggy_consolidate.py`) e carga no banco (`app/ingest/loader.py`); afeta toda tela que soma gasto. Desde que existe mais de uma extração em disco (22/09/2026).

## Causa raiz
Cada extração grava um arquivo datado por conta (`v2_transactions_<conta>_<dia>_p<n>.json`) e os antigos ficam em `data/raw/`, então o mesmo lançamento chega uma vez por extração. A consolidação lia os arquivos em ordem de nome e `dedup` ficava com a **primeira** ocorrência de cada `id`; como o dia vem depois da conta no nome, a primeira é a mais antiga. Das 1.939 cópias repetidas, 452 diferem entre as extrações: 384 no estabelecimento, 77 nos metadados de cartão (número e data da parcela), 76 no status (pendente → lançado) e 35 na data. As contas passavam pelo mesmo `dedup`, com o mesmo defeito.

A compra pendente que o emissor cancelou só existe no bruto antigo, então nenhuma ordem de leitura a remove: é preciso descartá-la de propósito. E a carga só faz *upsert* por `pluggy_id`, nunca apaga; mesmo fora do consolidado, a linha continuaria no banco.

## Evidência
- Testes de regressão (commit `f8bca11`):
  - `tests/test_pluggy_scripts.py` › `test_the_consolidation_keeps_the_latest_copy_of_each_transaction` — falha com `assert ('2026-08-04', None) == ('2026-09-04', 2)`.
  - `tests/test_pluggy_scripts.py` › `test_a_pending_purchase_the_latest_snapshot_no_longer_returns_is_discarded` — falha com `['gone', 'kept', 'other'] == ['kept', 'other']`.
  - `tests/test_ingest.py` › `test_a_discarded_transaction_leaves_the_base_and_the_others_stay` — a carga não tem como receber a lista.
- Medição sobre os brutos atuais (05/09 + 22/09/2026): 2.073 lançamentos → 2.070; gasto de maio R$ 16.105,92 → R$ 16.037,20 (as três parcelas do Mercado Livre vão para setembro); gasto de agosto R$ 14.626,41 → R$ 14.500,53 (as três pendentes saem).
- Medição sobre o bruto de 05/09/2026 sozinho, o dos números congelados em `docs/plano.md`: nenhum `id` se repete dentro dele, e o consolidado sai idêntico antes e depois. Os números de referência não mudam.

## Correção proposta
- `ingestao/pluggy_consolidate.py` — `load_snapshots` lê cada arquivo com a série (nome sem dia e página) e o dia do nome; `newest_copies` fica com a cópia do dia mais recente de cada `id`, para contas e lançamentos; `latest_transactions` descarta o lançamento `PENDING` cuja cópia mais nova é de um dia anterior à extração mais nova da mesma série. O lançado que some continua: a extração nova pode só não alcançar aquela data. Os descartados vão para `data/processed/descartadas.json`.
- `app/ingest/source.py` — `load_discarded` lê a lista ao lado do consolidado; sem o arquivo, lista vazia.
- `app/ingest/loader.py` — `ingest` recebe `discarded` e apaga essas linhas na mesma transação da carga; `app/ingest/__main__.py` e `app/sync/__init__.py` passam a lista.
- **Risco:** apagar linha do banco. Só sai o que a consolidação nomeou; nenhuma tabela referencia `transactions`, e a categoria manual e o "não é gasto" de uma compra cancelada perdem o sentido junto com ela.
- **Fora da correção:** `docs/plano.md` não muda (medido acima).

## Pontos em aberto
Nenhum.
