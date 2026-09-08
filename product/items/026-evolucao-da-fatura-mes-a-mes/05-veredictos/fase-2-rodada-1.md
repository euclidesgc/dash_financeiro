VEREDICTO: CRITERIO_INVALIDO

Despacho limpo: recebi só objetivo, critérios tipados e ponteiro. Nenhum plano, spec, PRD ou histórico veio junto, e não abri `product/items/026-evolucao-da-fatura-mes-a-mes/`.

## Portões

| Portão | Resultado | Saída |
|---|---|---|
| ruff check | OK | `All checks passed!` (exit 0) |
| ruff format --check | OK | `167 files already formatted` (exit 0) |
| mypy --strict src | **não se aplica** | Não existe `src/` e não há seção de mypy no `pyproject.toml`. Não medi — e não conto como aprovado. |
| pytest | OK | `676 passed, 2 warnings in 54.23s`, `EXIT=0` — julgado pela linha de coleta |
| gates | OK | `✓ gates: limpos (árvore completa, 569 arquivo(s) considerados).`, `EXIT=0` — 569 > 0 |

Cada um rodou uma vez só, capturado em arquivo e lido do arquivo.

## Critérios da fase

| # | Tipo | Resultado | Evidência |
|---|---|---|---|
| 1 | estrutural RF-06 | cumprido | O fragmento novo tem a seção uma vez, sem manchete própria, e a frase que nomeia o mês do pagamento. A tela o inclui. O router importa a curva e entrega a chave |
| 2 | estrutural RF-06 | cumprido | O fragmento de parcelamentos passa a ter duas aberturas e dois fechamentos, iguais e ≥2, com as duas seções nomeadas presentes — controle positivo satisfeito |
| 3 | comando RF-06 | cumprido | 20 classes conferidas, exit 0. **Controle negativo meu**, numa cópia fora do repositório com uma classe inexistente injetada: o comando acusa e sai não-zero — ele discrimina |
| 4 | comando RF-06 | **INVÁLIDO** | `git remote -v` é **vazio**: este repositório não tem remote. Os dois comandos saem com **128** e `fatal: ambiguous argument 'origin/develop...HEAD'`. O controle positivo do próprio critério não imprime nada. Ver abaixo |
| 5 | comportamental RF-01/04/06 | cumprido | A tela sem query string responde 200, e o trecho da fatura traz o cartão, o restante, os quatro meses com seus totais, as duas séries com o mês em que morrem e o caixa que devolvem, e o total. O sinal de menos é o caractere tipográfico, confirmado por ponto de código |
| 6 | comportamental RF-03 | cumprido | Cartão sem nenhum dos dois dias: premissa declarada e as duas frases. Cartão só com fechamento: a frase do vencimento, e a do fechamento ausente. Cartão completo: nenhuma das duas, e nenhuma marca de premissa |
| 7 | comportamental RF-05 | cumprido | Três blocos, cada um com a soma dos meses igual ao próprio restante, e o total da tela igual à soma dos três |
| 8 | comportamental RF-07 | cumprido | Cartão sem parcelamento vivo traz a frase do estado vazio e **nenhum** mês; o cartão com série traz quatro — controle positivo |
| 9 | estrutural RF-08 | cumprido | As cinco funções de teste preexistentes continuam lá, e os literais que elas fixam também |

## Critérios de integração

| # | Tipo | Resultado | Evidência |
|---|---|---|---|
| I-1 | comportamental RF-05/06/08 | cumprido | Base ingerida pelo carregador real, semeada e classificada. A seção de parcelamentos traz duas séries; a de fatura traz uma, com 23 meses somando exatamente o restante do cartão. O parcelamento fora de cartão não aparece na curva e é contado à parte |
| I-2 | comando | cumprido | `32 passed`, exit 0. O diff **não remove nenhuma linha** do arquivo de teste preexistente: as duas fixtures antigas seguem intactas e duas novas entraram. Os dois testes nomeados afirmam a soma por bloco e o balanço de seções |

## Sobre o critério 4

O critério manda comparar contra `origin/develop`. Este repositório **não tem remote configurado**. O intervalo é irresolvível, os dois comandos morrem com código 128, e o controle positivo que o próprio critério instala para pegar "intervalo escrito errado" é justamente o que dispara. A implementação não tem como cumpri-lo sem fabricar uma referência falsa, o que seria fraudar a medição.

Verifiquei a **intenção** contra a base real:

- `git diff --name-only develop...HEAD -- app/static/css` → **0 linhas**, exit 0
- `git diff --name-only develop...HEAD` → os cinco arquivos da fase, incluindo o fragmento novo — controle positivo satisfeito

Nenhuma folha de estilo mudou, e o fragmento novo está no diff. O conteúdo do critério se sustenta; a redação dele não. Corrigir é trocar `origin/develop` por `develop`.

## Comparação com `develop` (prova independente, além dos critérios)

Extraí `develop` com `git archive` para um diretório temporário — sem trocar de branch — e rodei **a mesma base** nas duas árvores.

**Base rica** (3 assinaturas, 2 parcelamentos, 1 conta de crédito com cartão):

| Bloco | develop vs HEAD |
|---|---|
| assinaturas | **idêntico** |
| parcelamentos | **idêntico** |
| caixa liberado | **idêntico** |
| calendário de 45 dias | **idêntico** — 10 cifras, 20 atributos, mesma janela |
| totais de manchete | **idênticos** |
| todas as datas da página | **idênticas** |
| dispensadas | ausente nos dois — essa comparação foi vazia, e digo por honestidade; todas as outras carregam valor diferente de zero |

**Base vazia:** as duas árvores devolvem 200, as mesmas cifras e as mesmas seções — a única diferença é a seção nova com seu estado vazio. A condição que passou a envolver o caixa liberado **não** mudou comportamento: ele já não era emitido nesse caso.

**Conclusão: nenhum número que a tela já dava mudou.**

**HTML bem formado** — contei aberturas e fechamentos na página inteira renderizada:

- `develop`, base rica: `<section` = **4**, `</section>` = **5** — desbalanceado, era o defeito que estava lá
- `HEAD`, base rica: `5` e `5`; e artigo, div, tabela, corpo de tabela, parágrafo, linha, célula, cabeçalho, lista e item **todos pareados**
- `HEAD`, base vazia: tudo pareado

**Guarda de sessão** — varri 37 rotas sem sessão, excluindo a porta do login: **zero** devolveram 200.

## Achados que não reprovam

1. **`mypy --strict` não é portão medível aqui.** Reportado como não medido, não como aprovado.
2. **A comparação da seção de dispensadas entre as duas árvores foi vazia** nas bases que montei. As demais têm conteúdo não-zero.
3. **O primeiro mês é indexado no template** dentro da condição que exige série. Conferi a aritmética: a faixa sempre devolve pelo menos um mês quando há série, então não há risco de erro de índice — registro porque a leitura do template sozinha não deixa isso claro.

## Instrumentos do implementer

Apenas o critério I-2, que cobra explicitamente a existência e o resultado da suíte do avaliado. Todos os outros foram verificados com harness próprio, que sobe a aplicação, semeia banco em diretório temporário, autentica e busca a tela sem query string, sem usar nenhuma fixture do arquivo avaliado.
