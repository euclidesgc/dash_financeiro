# Veredicto — 033, fase 1, rodada 2 (Semear não deixa o banco pela metade)

**Veredicto:** APROVADO · **Validação cega** · **Data:** 08/09/2026

A rodada 1 **parou no portão**, antes dos critérios: o comentário que explica a
decisão de escopo do SQL não abria com marca de justificativa, e o portão de
comentário — endurecido horas antes pela fase 1 do item `034` — o acusou. Vale
registrar: **o portão pegou um comentário escrito no mesmo dia, em outro item, na
primeira chance que teve.** É portão funcionando como portão. O texto não mudou;
ele passou a dizer, na primeira linha, que é uma decisão.

## Portões

| Portão | Resultado |
|---|---|
| `scripts/lint.sh` | OK — ruff, formatador e `mypy --strict` nos três pacotes |
| `scripts/gates/gates_runner.sh` | OK — `gates: limpos (árvore completa, 672 arquivo(s) considerados)` |
| Suíte | OK — `771 passed` |

## Critérios

**`comando` (RF-01, RF-02) — o número que decide.** `-k coerente` → `2 passed`. E
o validador não parou aí: copiou a base **real**, reconciliou o vão da migração
`012`, escreveu **sua própria** consulta de divergência — lançamento cujo
`group_id` difere do grupo da regra que o classifica — e rodou a semeadura
**isolada**, sem classificação depois:

| código | divergência |
|---|---|
| `develop` | **343** |
| esta fase | **0** |

O contraste é a prova de que a correção corrige. Não é teste vazio.

**`comando` (RF-01) — a migração que derruba e repõe, com controle positivo.**
`-k migracao` → `1 passed`. O validador provou por mutação: suprimida a
reclassificação dentro do teste, ele **falha**. Desfeita, volta a passar.

**`comando` (RF-03) — o que a correção custou.** `26 passed` nos quatro arquivos.
E o validador leu o diff: `app/ingest/__main__.py` está **byte a byte igual** ao
de `develop`, e a correção inteira é o alargamento do predicado de uma atualização
que já existia — de "grupo fora dos declarados" para "grupo diferente do grupo da
regra". Não há chamada de classificação dentro da semeadura. **O caminho encadeado
não passou a fazer o trabalho duas vezes**, que era o custo que o plano recusava.

**`comportamental` (RF-04) — nenhum dinheiro se moveu.** O painel servido sobre
duas cópias da base real — uma semeada com o código de `develop`, com as 343
divergências; outra com o desta fase, com zero — devolve os mesmos totais:
posição consolidada −R$ 27.449,71, caixa −R$ 5.451,25, cartão −R$ 40.722,95,
gastos −R$ 730,59, comprometido −R$ 8.026,79, e as 15 cifras da escada de dívidas
idênticas, total −R$ 238.585,18. Dado derivado não move dinheiro.

**`comando` (RF-03) — a contagem.** `768` em `develop`, `771` aqui. O validador
extraiu os identificadores coletados dos dois lados e comparou: **zero teste
removido ou renomeado**, exatamente três novos.

## Achados fora do escopo

1. `/dividas` não tem célula com o rótulo de manchete que o critério pressupõe —
   já era assim em `develop`. O validador comparou as 15 cifras da escada em vez
   disso. Um critério futuro para essa tela deve nomear as cifras, não a manchete.
2. Dois avisos de depreciação na suíte, pré-existentes.
