# Decisões tomadas sem o humano — 003-comprometido

O humano autorizou autonomia para este item em 2026-09-05, no
`product/prompt-da-proxima-sessao.md`, e em 06/09/2026 mandou "começa e termina
isso de uma vez". Este arquivo é o que ele lê depois: **uma linha por decisão**,
com a alternativa descartada e o porquê.

Ponto de retorno limpo: o commit anterior à primeira escrita deste item. Os itens
`001` e `002` continuam de pé sem ele.

## Decisões

| # | Estágio ou fase | Decidido | Alternativa descartada | Por quê |
|---|---|---|---|---|
| D1 | discovery | **Janela de vida** de um mês: um parcelamento só é compromisso se a última parcela vista caiu no mês corrente ou no anterior | Confiar em `total − maior parcela vista`, como o consolidador calcula | Medido: a conta ingênua dá 32 parcelamentos com parcelas a vencer; com a janela sobram **6**. Os outros 26 são séries mortas — `IPVA parcela 1 de 3` visto em 26/01/2026 ainda "deve" duas parcelas. Compromisso que não existe mais inflando o total é pior que não ter a tela. |
| D2 | discovery | Dia de cobrança previsto pela **mediana** dos dias observados, com a tela declarando que é previsão | Usar o dia da última ocorrência, ou o modo | Medido: `debito prestacao hab` caiu nos dias 6, 16, 17, 18, 19, 28 e 31 em nove meses. A mediana resiste a um mês atípico; o dia da última ocorrência herda o atípico inteiro. |
| D3 | discovery | Lançamento recorrente **e** parcelado conta como parcelamento | Contar nos dois, ou preferir recorrente | Parcelamento tem fim e recorrência não; contar nos dois soma o mesmo dinheiro duas vezes no comprometido. |
| D4 | discovery | "Cancelável" é marca do dono na tela, não categoria no código | Derivar dos grupos `Serviços e assinaturas` e `Digital services` | Medido: as categorias de serviço somam R$ 2.245,69/mês, e as três que o relatório de origem trata como canceláveis somam R$ 1.099,63. A diferença é julgamento — Mycon é boleto, escola é recorrente e nenhuma se corta com um clique. Mesmo padrão do `002`: o que só o humano sabe é marca na tela. |
| D5 | discovery | O motor detecta recorrência e parcelamento **do banco**, não dos JSONs de `data/processed/` | Ler `recorrentes.json` e `parcelamentos.json` na ingestão | O item `006` vai atualizar o banco por sync, e compromisso derivado de arquivo congelado envelheceria em silêncio. Os JSONs continuam sendo a referência de conferência dos números. |

## Aprovações registradas em modo autônomo

| Estágio | Documento | O que foi aprovado | Quando |
|---|---|---|---|
| — | — | — | — |

## O que ficou para o humano

- **Marcar as assinaturas que não usa mais.** O produto não decide isso; a tela
  existe para ele decidir. As três do relatório de origem somam R$ 1.099,63/mês.
