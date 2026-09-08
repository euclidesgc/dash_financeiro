VEREDICTO: APROVADO

Nenhum plano, spec ou histórico veio no despacho — só objetivo, critérios e ponteiro. Não abri `product/items/026-evolucao-da-fatura-mes-a-mes/`.

## Portões

| portão | resultado |
|---|---|
| ruff check | **OK** — `All checks passed!` |
| ruff format --check | **OK** — `167 files already formatted`, exit 0 |
| mypy --strict | **N/A neste projeto** — não há `src/`, `mypy` não está no `.venv` nem no `pyproject.toml`; a norma 35 o coloca como item de roadmap. Declarado, não omitido |
| pytest | **OK** — `660 passed, 2 warnings in 60.77s`, exit **0** lido do próprio pytest |
| gates | **OK** — `✓ gates: limpos (árvore completa, 565 arquivo(s) considerados)`, exit 0 |

Conferi que os portões arquiteturais **mediram de verdade**, gate a gate, em vez de aceitar o total global:

```
universo (git ls-files) = 565 arquivos; diff develop...HEAD = 3 arquivos
  [G3] modo=diff   alvos MEDIDOS = 2    violacoes = 0
  [G4] modo=arvore alvos MEDIDOS = 219  violacoes = 0
  [G7] modo=arvore alvos MEDIDOS = 150  violacoes = 0
```

E confirmei que o G3 está vivo, não só calado: alimentado com um comentário que descreve mecânica, ele acusa.

## Critérios de aceite

| # | tipo / RF | veredicto | evidência |
|---|---|---|---|
| 1 | estrutural RF-01/02/03 | cumprido | As quatro funções importadas e chamáveis. A consulta tem `SELECT`, `GROUP BY` e `LEFT JOIN`; o módulo de aritmética não tem `SELECT` (rc=1). A pasta de migrações para em `015` — nenhum `016` |
| 2 | comportamental RF-02 | cumprido | Fechamento `5` → quatro meses; fechamento `20` → três meses, com vencimento fixo |
| 3 | comportamental RF-01/02 | cumprido | Vencimento `25` → três meses; vencimento `5` → quatro meses; `remaining_cents = -36000` **nas duas** |
| 4 | comportamental RF-03 | cumprido | Os quatro estados de dia conhecido/ausente: premissa declarada nos três incompletos, e não declarada no completo — controle positivo fecha |
| 5 | comportamental RF-05 | cumprido | `Cartão Azul`: soma dos meses `-46000` = restante `-46000` = SQL independente `-46000`. `Cartão Roxo`: `-20000` nos três. Ambos ≠ 0 |
| 6 | comportamental RF-04 | cumprido | As duas séries com o mês de morte e o caixa que liberam; e `-12000 − (-17000) = 5000` na própria curva |
| 7 | comportamental RF-07 | cumprido | O cartão sem série viva devolve lista vazia, ao lado de um com quatro meses na mesma resposta |
| 8 | comportamental RF-05 | cumprido | Nome de cartão repetido conta uma vez: `-36000`, não `-72000` |
| 9 | comportamental RF-01 | cumprido | Pelo motor real: a ligação série↔cartão é o nome da conta; o parcelamento fora de cartão é contado à parte |
| 10 | comando | cumprido | `8 passed in 0.54s`, exit `0` lido do pytest, sem cano |

## Minha própria conferência da soma

**Terceira via, independente das duas.** Escrevi uma expansão mês a mês inteiramente em SQL, sem tocar no módulo de aritmética. Comparei o **vetor mês a mês**, não só o total, em quatro bases:

| base | curva (não-zero) | 3ª via SQL | soma / remaining |
|---|---|---|---|
| 3 séries, 2 cartões | `{10:-17000, 11:-17000, 12:-12000}` | idêntico | `-46000` **BATE** |
| vencimento antes do fechamento | `{10:-12000, 11:-17000, 12:-17000}` | idêntico | `-46000` **BATE** |
| sem linha de cartão | `{09:-12000, 10:-17000, 11:-17000}` | idêntico | `-46000` **BATE** |
| virada de ano, 9 parcelas | `2026-11 … 2027-07`, `-7777` cada | idêntico | `-69993` **BATE** |

**Os dois papéis do dia.** Mexer só no **fechamento** muda o mês em que a parcela cai e encurta a curva; mexer só no **vencimento** alonga a curva e deixa o restante intacto. O vencimento move mês, nunca dinheiro.

**Cartão sem parcelamento vivo não vira curva de zeros:** lista vazia, não fileira de zeros.

**Nenhum total existente mudou.** Extraí `develop` com `git archive`, copiei o mesmo arquivo de banco para os dois lados e rodei caixa liberado, totais, calendário de 45 dias, parcelamentos e assinaturas em cada árvore. `diff` das duas saídas JSON de 184 linhas: **vazio**. E os commits próprios tocam só 3 arquivos, todos novos. Nenhuma tela consome a leitura, coerente com o objetivo.

## Achados que não reprovam

1. **A branch está um commit atrás de `develop`, e esse commit afrouxa o G3** para julgar só linhas acrescentadas. Rodei a versão mais estrita; ao integrar, o portão passa a ser o outro. Não é defeito da fase, é aviso de que o portão que aprovou aqui não é o que rodará depois do merge.
2. **"O que falta pagar" é definido pela janela viva, e a consulta de controle do critério 5 não é.** Com a data de referência um mês à frente, o cartão some da resposta enquanto a consulta de controle continua somando. As duas leituras do painel seguem concordando entre si; quem reaproveitar aquela consulta noutra data verá divergência que não é defeito.
3. **A agregação decide em silêncio entre cartões homônimos preenchidos.** Ela agrupa por nome de conta e pega o maior dia; o critério só exercita o caso em que a conta homônima não tem cartão configurado. Com dois cartões de mesmo nome e dias diferentes, ganha o dia maior, sem sinal.
4. **Mês de referência sem cobrança entra na curva valendo zero.** É o que os critérios exigem, mas uma tela que renderize isso mostrará "R$ 0,00" no mês corrente e alguém vai ler como defeito.

## Instrumentos do implementer

Apenas o critério 10, que por construção nomeia o arquivo de teste. Os nove restantes foram verificados com bancos montados por mim, mais a terceira via em SQL e a comparação com `develop`.
