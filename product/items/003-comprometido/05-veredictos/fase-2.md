# Veredicto — 003-comprometido, fase 2

VEREDICTO: APROVADO

> Segunda rodada, validador novo, depois de `#caixa-liberado` virar seção irmã de
> `#parcelamentos` e do helper de teste passar a varrer todos os `<tbody>`.
> Ver `fase-2-reprovada-1.md`.

Portões: `pytest -q` → `293 passed`, exit 0; `gates_runner.sh` → limpo (204
arquivos). Lint não executável — o projeto não declara linter nem typechecker.

Critérios (os treze cumpridos):
  [x] RF-30 → `200`, os três blocos presentes, `−R$ 12.802,64` sob "Total
      comprometido" e `R$ 0,00` sob "Economia projetada"
  [x] RF-31/35 → 55 assinaturas, ordenação não crescente sem `NaN`, 55 botões,
      35 `Sem cobrança recente` — igual ao que o banco devolve
  [x] RF-32/33 → **6** parcelamentos, `data-restante`
      `[279994,60432,28212,12348,11920,3220]`; `−R$ 127,27` com `22` e `06/2028`;
      `−R$ 141,06` com `10/2026`; caixa liberado listando os quatro meses e
      fechando em `R$ 374,82`
  [x] RF-24/25 → as três dispensas levam a `−R$ 11.703,01` / `R$ 1.099,63`; a
      retomada devolve `−R$ 11.812,01` / `R$ 990,63`
  [x] RF-27 → `400`, `Parcelamento contratado não para com um clique.`,
      `commitment_dismissals` = 0
  [x] RF-28/29 → `#dispensadas` com três linhas, `R$ 1.099,63` e a frase exata
  [x] RF-36 → banco vazio conferido, `200`, zero `<tr>`, `Nenhum compromisso
      detectado.` seguido do caminho para Gastos
  [x] RF-37 → grep do conteúdo entregue (`git archive`) sai vazio nos dois fluxos
  [x] RF-38 → nenhuma cor fora de `tokens.css`; 80 `.cifra`, todas
      `tabular-nums`, todas no formato, 68 negativas com `U+2212` colado
  [x] RF-39 → seis medições de viewport, carregando e redimensionando; as seis
      capturas existem, todas PNG e acima de 1024 bytes
  [x] RF-40/41 → foco `solid 2px` em duas paradas distintas do `Tab`; 907
      elementos varridos, zero com duração diferente de `0s`

Apontamentos
  1. O critério `RF-37` recursa em `app/commitments/` sem excluir `__pycache__`,
     e o GNU grep imprime em stderr que o `.pyc` casa o padrão — por coincidência
     de bytes do bytecode, não por constante no código. Julgado contra o objeto
     entregue, onde os dois fluxos saem vazios. O comando é instável entre
     máquinas: falha em árvore usada, passa em checkout limpo.
     Correção barata: `--exclude-dir=__pycache__`.
  2. O despacho manda não abrir `product/items/<id>/**`, e o critério estrutural
     de `RF-39` exige verificar as capturas que vivem exatamente ali. Resolvido
     por `stat`/`file`/`git ls-files`, sem abrir documento de processo — mas a
     exceção precisa ser explícita no despacho.
  3. Cruzamento contra código velho: o validador reproduziu os marcadores num
     servidor subido por ele da árvore em `5522c91`, e os números bateram — a
     evidência não veio de processo desatualizado.
