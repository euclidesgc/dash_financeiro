# Veredicto — 003-comprometido, fase 2 (primeira rodada)

VEREDICTO: REPROVADO

Portões: `pytest -q` → `293 passed`; `gates_runner.sh` → limpo. Lint não executável.

Doze dos treze critérios cumpridos: a tela responde 200 com sessão e 302 sem;
55 assinaturas ordenadas por valor médio, com 35 marcadas `Sem cobrança recente`
(conferido contra o banco); as três dispensas levam a economia projetada a
`R$ 1.099,63` e a retomada devolve a `R$ 990,63`; dispensar parcelamento é
recusado com `400` e `Parcelamento contratado não para com um clique.`, sem
gravar nada; o bloco `#dispensadas` traz as três linhas e a frase que diz que a
marca não cancela nada no fornecedor; o estado vazio; nenhuma cor fora de
`tokens.css`; 80 cifras tabulares com `U+2212`; sem rolagem horizontal nas seis
medições; foco visível e movimento zerado.

  [ ] RF-32, RF-33 — `#parcelamentos tbody tr` devolve **10**, não 6.
      `#caixa-liberado` estava **dentro** de `#parcelamentos`, com tabela própria,
      então o seletor da seção misturava 6 linhas de parcelamento com 4 de mês de
      término. A sequência de `data-restante` só não acusava violação porque
      `NaN > x` é sempre falso.

Apontamento aproveitado: `tests/test_comprometido_screen.py` não pegava a quebra
porque o helper `_rows` casava só o **primeiro** `<tbody>` da seção — a régua do
teste era mais estreita que a do DOM, e por isso 293 testes passavam com o
defeito de pé.
