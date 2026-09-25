# Investigação: a suíte ponta a ponta não aguenta uma segunda volta

## Relato
- **Sintoma:** `pnpm exec playwright test --repeat-each=2` falha na segunda volta de "updates the records from the balances page" (`e2e/sync.spec.ts`): `getByText('Nunca atualizado')` não aparece em 5 s, e os dois testes seguintes do arquivo nem rodam.
- **Esperado:** cada teste começa da base que o seed criou, em qualquer volta, e a suíte inteira pode ser repetida para caçar teste instável.
- **Como reproduzir:** `pnpm exec playwright test --repeat-each=2` na suíte inteira.
- **Onde:** suíte ponta a ponta, `e2e/sync.spec.ts`. A tela não tem defeito: depois de uma sincronização ela mostra "Última atualização", como deve.

## Causa raiz
Os três testes de `e2e/sync.spec.ts` apertam "Atualizar agora", que roda uma sincronização de verdade (`POST /api/sync/run`) no banco único da execução (`scripts/e2e-backend.sh` cria o SQLite temporário uma vez). A sincronização grava uma linha em `sync_runs` e carrega contas e lançamentos — e não há nada que a desfaça: nem rota da API (e não deve haver, é histórico), nem limpeza no teste. O primeiro teste parte de "Nunca atualizado", que só é verdade enquanto nenhuma sincronização rodou; na segunda volta a primeira já rodou, e o teste falha antes de apertar o botão.

## Evidência
- `pnpm exec playwright test --repeat-each=2`, em 25/09/2026: 33 passaram, 1 falhou, 2 não rodaram. A falha é `sync.spec.ts:19`, `expect(getByText('Nunca atualizado')).toBeVisible()`, na repetição 1. A ordem da execução é a suíte inteira da volta 0 e depois a da volta 1, então os outros arquivos da volta 1 já rodam sobre uma base sincronizada e passam — o único teste que depende de a base nunca ter sido sincronizada é esse.

## Correção proposta
- A base volta ao seed antes de cada teste de `e2e/sync.spec.ts`, e depois dele também, rode o teste até o fim ou não. Como não existe desfazer pela API, a volta é pelo arquivo: o `scripts/e2e-backend.sh` guarda uma cópia do banco logo depois do seed, antes de o servidor subir, e um módulo Python novo (`tests/e2e_restore.py`) copia essa cópia de volta para o banco vivo pela API de backup do SQLite, que respeita as travas das conexões abertas do servidor.
- O teste precisa saber onde está o banco: o `playwright.config.ts` cria a pasta temporária uma vez, no processo principal, e passa o caminho ao servidor e aos testes pelo ambiente (`DASH_E2E_DIR`). O `scripts/e2e-backend.sh` usa essa pasta e continua apagando-a na saída.
- **Risco:** só a infraestrutura do e2e muda; nenhuma rota nova. Cada restauração custa uma chamada ao `uv run python` (menos de 1 s), seis por volta.
- **Fora da correção:** os outros arquivos continuam desfazendo pela API o que gravam (item 038); a restauração pelo arquivo fica restrita ao que a API não desfaz.

## Pontos em aberto
Nenhum.
