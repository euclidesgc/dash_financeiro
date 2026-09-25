# Investigação: uma falha no meio de um teste da tela de gastos deixa a base suja e derruba todas as repetições seguintes

## Relato
- **Sintoma:** em 25/09/2026, numa de 40 execuções de "shows the month against its ceiling, edits the ceiling inline and leaves the base as it found it" (`e2e/expenses.spec.ts`), a região "Teto do mês" não apareceu em 5 s depois do `page.reload()`. O teste só devolve o teto a "sem teto" nos últimos passos; como parou antes, o teto de R$ 200,00 ficou gravado e todas as repetições seguintes falharam logo no começo, esperando "Sem teto definido.".
- **Esperado:** uma falha derruba só o teste em que aconteceu; o seguinte começa da base semeada.
- **Como reproduzir:** fazer o teste do teto falhar em qualquer passo depois do primeiro "Salvar" (abaixo, com uma asserção forçada) e rodá-lo com `--repeat-each=2`.
- **Onde:** suíte ponta a ponta, `e2e/expenses.spec.ts`. A tela não tem defeito.

## Causa raiz
`e2e/expenses.spec.ts` — os quatro testes do arquivo que gravam na base (teto do mês, limite de Supermercado, marca de não-gasto em AÇOUGUE SÃO JORGE, marca de não-entrada em SALARIO) desfazem o que gravaram **como últimos passos do próprio corpo**. O Playwright interrompe o corpo na primeira asserção que falha, então a limpeza só roda quando o teste passa. O banco do e2e é um só por execução (`scripts/e2e-backend.sh` cria o SQLite temporário uma vez e o `playwright.config.ts` roda com um worker), e o arquivo é `serial`: o que um teste deixa gravado é o ponto de partida do próximo e de cada repetição. Uma falha qualquer — a do reload inclusive — vira falha de todos os testes que vêm depois.

## Evidência
- Falha forçada: uma asserção que falha logo depois do primeiro "Salvar" do teto (`expect(process.env.FORCE_CEILING_FAILURE).toBeUndefined()`), com `FORCE_CEILING_FAILURE=1 pnpm exec playwright test e2e/expenses.spec.ts -g "ceiling" --repeat-each=2`:
  - **sem a correção**, a primeira volta falha na asserção forçada e a segunda falha antes dela, em `expect(block).toContainText('Sem teto definido.')`, com `Received string: "Teto do mêsR$ 105,00 de R$ 100,00 · 105%AcimaPassou R$ 5,00Definir teto"` — o teto da volta anterior;
  - **com a correção**, as duas voltas chegam à asserção forçada: a segunda começou da base limpa.
- A mesma prova no teste da marca de não-gasto (falha forçada depois de marcar AÇOUGUE SÃO JORGE, `--repeat-each=2`): com a correção, a segunda volta passa por "2 gastos · R$ 105,00" e chega de novo à asserção forçada.
- A falha original de 5 s depois do reload **não se reproduziu**: 220 de 220 em `e2e/expenses.spec.ts --repeat-each=20`, 100 de 100 no teste do teto isolado, e 300 recargas medidas da tela com o teto recém-gravado (150 com a máquina ociosa, 150 com 16 processos ocupando a CPU) levaram no máximo 1,6 s até a região aparecer, sem nenhuma resposta de erro nem requisição falhada. Foram descartados: espera por trava do SQLite (nenhuma rota lida na tela escreve na base), corrida de conexão reaproveitada entre o proxy do Vite e o uvicorn (40 rajadas com intervalo perto de 5 s, nenhuma resposta fora de 401) e reotimização de dependências do Vite (nenhuma no log do servidor).

## Correção proposta
- `e2e/expenses.spec.ts` — um `test.afterEach` põe a base de volta pela API, com sessão própria (`request`), rode o teste até o fim ou não: teto do mês sem valor, Supermercado sem limite e as marcas de AÇOUGUE SÃO JORGE e SALARIO desfeitas, só se existirem. Cada chamada confere a resposta, para uma limpeza que não conseguiu gravar aparecer como falha do teste e não como falha misteriosa do seguinte. Os testes seguem desfazendo pela tela no fim, porque isso faz parte da jornada que verificam.
- **Risco:** só a suíte e2e muda; a limpeza é idempotente e roda em todo teste do arquivo, mesmo nos que não gravam nada (quatro chamadas a mais por teste, dezenas de milissegundos).
- **Fora da correção:** a causa da única espera acima de 5 s não foi achada; com a limpeza garantida, se voltar a acontecer derruba um teste só, e o rastro dele (`--trace=retain-on-failure`) mostra qual requisição demorou. `e2e/sync.spec.ts` não aguentar segunda volta (item 037) tem outra causa — a tela espera "Nunca atualizado" e não há como desfazer uma sincronização pela API — e fica para o 037.

## Pontos em aberto
Nenhum.
