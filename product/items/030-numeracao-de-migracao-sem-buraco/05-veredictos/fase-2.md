# Veredicto — 030, fase 2 (Reconciliar a base que pulou uma versão)

**Veredicto:** APROVADO · **Validação cega** · **Data:** 08/09/2026

O validador verificou as sete afirmações por execução própria, contra árvores
temporárias que ele escreveu e contra **cópia** da base real. A suíte do avaliado
foi lida só para contexto, nunca usada como evidência.

## Por que esta fase existe

O guarda da fase 1 encontrou um caso **real**: a base do dono tem `001`–`011`,
`013`, `014` e `015` aplicadas e nunca aplicou a `012`, que entrou na pasta depois.
O guarda passou a recusar migrar aquela base — e a mensagem mandava **renumerar o
arquivo**, que é o conselho errado: a `012` não é nova, e renumerá-la faria toda
outra base reaplicá-la.

## Portões

| Portão | Resultado |
|---|---|
| `scripts/lint.sh` | OK — `All checks passed!`, `182 files already formatted`, `Success: no issues found in 109 source files` |
| Suíte | OK — `753 passed` |
| `scripts/gates/gates_runner.sh` | OK — `gates: limpos (árvore completa, 658 arquivo(s) considerados)` |

## As sete afirmações

**1. Conselhos diferentes para situações diferentes.** Base com `005` e `020`
aplicadas recebendo `010` — vão real, tem versão abaixo e acima — recebe *"esta
base pulou a migração 010… reconcilie com `--reconciliar 010`"*. Base só com `020`
recebendo `010` — nada abaixo, é nova — recebe *"renumere o arquivo para uma
versão maior que 020"*.

**2. A reconciliação tenta aplicar, e não registra às cegas.** Com uma migração
que colide com o esquema, ela devolve *"não se aplica ao esquema atual desta
base: table conflito already exists. Nada foi gravado — o vão continua"*, e
`schema_migrations` fica intacta.

**3. Desbloqueia o resto.** Reconciliada a `010`, uma `025` seguinte aplica
normalmente.

**4. Contra a base real, em cópia.** Migrar recusa com a mensagem de
base-que-pulou; reconciliar a `012` responde *"aplicada e registrada; o vão desta
base fechou"*; migrar de novo aplica `018_offers.sql`.

**5. O que a reconciliação faz com os dados — a prova que decide.** Na mesma
cópia: `categories` 77 → **0** logo após reconciliar, porque a `012` derruba e
recria a tabela; e **77 de novo** depois da classificação, com
`classified 1942: changed=0 without_rule=7`. `category_groups`, `category_rules` e
`transactions` intactos o tempo todo.
E o validador **não confiou no `changed=0`**: extraiu `id, group_id` das 1.942
linhas antes e depois e comparou os dois arquivos — **idênticos, byte a byte**.
Nenhum lançamento muda de grupo; nenhum total de dinheiro se move.

**6. A recusa original continua valendo.** Migração genuinamente nova com número
baixo continua sendo mandada renumerar.

**7. A porta dos três algarismos continua fechada.** `9_sem_zero.sql` e
`abc_qualquer.sql` recusados, com `schema_migrations` vazia depois.

## O achado que virou correção

`reconcile_skipped` **não conferia** se a versão pedida era mesmo um vão: ela
aplicava e registrava qualquer versão fora de ordem, inclusive a que
`apply_migrations` classifica como *migração nova, deveria ser renumerada*. O
validador reproduziu. Isso deixava aberta a porta para recriar exatamente o vão
que esta correção existe para fechar.

Fechada: a reconciliação recusa uma versão sem nada registrado abaixo dela, e diz
para renumerar. Um teste novo prova, e a suíte de migração foi de 15 para 16.

## Achados fora do escopo

Nenhum outro.
