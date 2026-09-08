# Veredicto — 018, fase 2 (Os outros dois pacotes, e o portão)

**Veredicto:** APROVADO · **Validação cega** · **Data:** 08/09/2026

O validador não viu quem implementou nem o que ele relatou. Nenhuma asserção da
suíte do avaliado foi usada como prova de comportamento: ele escreveu a própria
sonda HTTP e comparou saídas por conta própria.

## Portões

| Portão | Resultado |
|---|---|
| `scripts/lint.sh` | OK — `All checks passed!`, `180 files already formatted`, `Success: no issues found in 109 source files`, saída `0` |
| Suíte | OK — `732 passed`, saída `0` |
| `scripts/gates/gates_runner.sh` | OK — `gates: limpos (árvore completa, 615 arquivo(s) considerados)` |

## Critérios

**`comando` (RF-03).** `mypy --strict app financas ingestao` sai `0` com
`Success: no issues found in 109 source files` — 105 de `app`, 2 de `financas`,
2 de `ingestao`. **109 ≥ 86**, o piso que a medição do terreno fixou, e maior que
os 104 da fase 1 com `app` sozinho. O número importa porque o verificador também
sai verde quando não encontra arquivo nenhum.

**`estrutural` (RF-04) — o portão ganhou uma verificação, não trocou uma pela
outra.** `scripts/lint.sh` traz as três chamadas: `ruff check`,
`ruff format --check` e `mypy --strict`, todas sobre os três pacotes. Nenhuma das
duas antigas saiu.

**`comando` (RF-04).** `bash scripts/lint.sh` sai `0` e a saída traz as três
linhas — a do lint, a da formatação e a do verificador de tipos.

**`estrutural` (RF-04) — a integração contínua cobra o mesmo.** O passo `Tipos`
de `.github/workflows/ci-python.yml` roda `mypy --strict app financas ingestao`,
o mesmo comando que o portão local. Um portão que só existe na máquina de quem
rodou não é portão.

**`comando` (RF-05).** Só duas ocorrências de silenciamento em toda a árvore,
ambas herdadas da fase 1, ambas com o código do erro entre colchetes e a razão na
mesma linha. **Zero** em `financas` e `ingestao`.

**`comando` (RF-06).** `732 passed`, saída `0`. E `tests/` está byte a byte igual
a `develop` — a contagem não teve como mudar por esta fase.

**`comportamental` de integração (RF-06).** Com a base real copiada para
diretório temporário e `DASH_TODAY=2026-09-05`, o validador buscou **oito** telas
com sessão autenticada, contra o código desta branch e contra o de `develop`, sobre
a mesma cópia. Todas responderam `200`, e os oito corpos saíram **byte a byte
idênticos**.

## O portão foi visto vermelho

Um portão que nunca reprovou não foi provado. O validador injetou uma quebra
deliberada de tipo em `financas/cdc_veiculo.py` — atribuir um número fracionário
a uma variável declarada inteira — e `bash scripts/lint.sh` **saiu com código 1**,
apontando o erro. Desfeita a quebra, o portão voltou a `0`.

Isso importa nesta corrida em particular: os portões arquiteturais deste projeto
passaram quinze itens dizendo `✓ limpos (551 arquivos considerados)` quando o
número era o que eles tinham **varrido**, não o que tinham **julgado** — zero.
Um portão que nasce sem prova de reprovação repete essa história.

## A revisão que este item exigia

O diff de `financas` e `ingestao` foi lido inteiro à procura de anotação que
virasse conversão. Só entraram assinaturas e anotações de variável. Os dois
`cast()` novos em `ingestao/pluggy_extract.py` recaem sobre campos de texto do
contrato da Pluggy, cada um com a razão ao lado. **Nenhum `int(`, `str(`,
`float(` ou `or 0` novo em caminho de dinheiro** (norma 22).

O comportamento dos dois executáveis foi conferido rodando-os antes e depois
sobre os mesmos dados: `financas/cdc_veiculo.py` e
`financas/financiamento_sac.py` imprimem a mesma coisa, e
`ingestao/pluggy_consolidate.py` produz os quatro arquivos de saída byte a byte
idênticos. `ingestao/pluggy_extract.py` **não foi executado**: exige rede real e
credenciais, que o ambiente de teste bloqueia de propósito. O validador declara
isso em vez de contar como medido.

**Norma 35** reescrita no presente, sem cicatriz: o portão é `ruff check`,
`ruff format --check` e `mypy --strict` nos três pacotes, e a integração contínua
cobra o mesmo comando.

## Achados fora do escopo

1. A entrada do roadmap ainda descrevia o estado anterior — reescrita no
   fechamento do item, junto deste veredicto.
2. O validador notou uma alteração local não commitada em `product/roadmap.md`,
   de outro item entregando em paralelo. Não é desta fase.
