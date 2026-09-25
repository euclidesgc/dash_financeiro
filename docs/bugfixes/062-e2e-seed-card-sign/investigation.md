# Investigação: o cartão da base de teste entra como dinheiro em caixa

## Relato
- **Sintoma:** na base de teste (a que o e2e sobe), o Resumo antigo mostra a "Posição consolidada" como R$ 57,34: o saldo da conta (R$ 12,34) somado aos R$ 45,00 do cartão, como se a dívida do cartão fosse dinheiro disponível.
- **Esperado:** o cartão entra como dívida, e a posição consolidada é R$ 12,34 − R$ 45,00 = −R$ 32,66, como acontece com os dados reais da Pluggy.
- **Como reproduzir:** rodar `tests.e2e_seed.seed` num banco vazio e ler `positions()`: `card_cents` sai `4500` e `consolidated_cents` sai `5734`.
- **Onde:** `tests/data/e2e_accounts.json`, a conta `acc-fixture-2` (`CREDIT`).

## Causa raiz
A Pluggy manda o saldo de um cartão como número **positivo** (o que se deve), e a ingestão (`app/ingest/loader.py`) inverte o sinal das contas `CREDIT` uma vez, para que dívida fique negativa em qualquer tipo de conta (invariante 22). O arquivo da base de teste foi escrito já com o sinal do banco, `"balance": -45.0`; a ingestão inverte de novo e grava `+4500`. O código está certo; o dado de teste é que não segue a convenção da fonte, então toda tela que soma saldos por tipo trata o cartão como dinheiro.

O mesmo erro está na conta de cartão escrita à mão em `tests/test_typed_limits.py` (`"balance": -200.0`), que também passa pela ingestão e vira `+20000`. Os demais testes que têm cartão gravam direto no banco, já com o sinal normalizado, ou mandam saldo positivo ou zero à ingestão.

## Evidência
- Teste de regressão (commit `5441c7a`), falha antes da correção: `tests/test_e2e_seed.py`, `test_the_seed_card_enters_as_debt_and_lowers_the_consolidated_position` — `positions()` devolve `consolidated_cents = 5734` em vez de `-3266`.
- Os demais testes de `tests/test_e2e_seed.py` e `tests/test_e2e_restore.py` passam antes e depois: o seed continua classificando tudo e não registra atualização.

## Correção proposta
- `tests/data/e2e_accounts.json` — o saldo do cartão passa a `45.0`, como a Pluggy manda.
- `tests/test_typed_limits.py` — o saldo do cartão passa a `200.0`, pelo mesmo motivo.
- **Risco:** nenhum teste de tela ou e2e confere o saldo do cartão da base de teste; a lista de gastos, o filtro por conta e os totais por categoria dependem dos lançamentos, não do saldo.

## Fora da correção
Nada.

## Pontos em aberto
Nenhum.
