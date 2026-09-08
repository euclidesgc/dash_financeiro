# Discovery — 024-cartoes-como-entidade

**Item do roadmap:** `024-cartoes-como-entidade` — o cartão de crédito é uma entidade
com os dados que só o dono sabe: limite, taxa mensal, dia de fechamento e dia de
vencimento, editáveis na tela.

**Data:** 2026-09-07 · **Trilha declarada:** rápida

## O terreno, lido no código

`accounts` (`app/migrations/sql/001_schema.sql:17-25`) guarda `id`, `name`, `type`,
`subtype`, `institution` e `balance_cents`, e mais nada. Não existe cartão no modelo:
existe conta cujo `type` é `CREDIT` (`app/accounts.py`).

A taxa vive em `debts.monthly_rate_bp` (`app/migrations/sql/005_debts.sql`), por dívida
e não por conta, e é reconstruída a cada `rebuild` — que preserva a taxa digitada pelo
dono numa releitura chaveada por `(kind, name)` (`app/debts/ladder.py:42-45`). Um cartão
vira degrau da escada com `monthly_rate_bp = None` (`app/debts/ladder.py:83`), e degrau
sem taxa não entra na escada (`app/debts/ladder.py:174-183`).

O `014` registrou por escrito que **cartão não recebe taxa sugerida**: o saldo de um
cartão é fatura, fatura paga inteira não cobra juro, e derivar dos encargos daria
0,06% ao mês — um número falso.

A consequência medida está no roadmap desde o `005`: **R$ 16.744,62 de cartão ficam
fora da escada de dívida**, e o marco "dívidas caras zeradas" do objetivo é calculado
sem eles.

## Regra, exemplo e pergunta

- **Regra.** Cada cartão da base tem limite, taxa mensal, dia de fechamento e dia de
  vencimento, informados pelo dono na tela.
- **Regra.** Os cartões nascem cadastrados e vazios. Limite e taxa não se inferem do
  que a Pluggy manda, e inventá-los é pior que deixar em branco.
- **Regra.** Informada a taxa, o cartão entra na escada de dívida na posição dela.
- **Exemplo.** O dono informa 12,5% ao mês num cartão. A escada se reordena e os
  R$ 16.744,62 param de ficar de fora.
- **Pergunta em aberto:** nenhuma de produto.

## Os quatro gatilhos de trilha completa

| Gatilho | Resposta |
|---|---|
| Mexe em contrato público ou OpenAPI? | Não. |
| Toca autenticação, autorização ou dado pessoal? | Não: dado financeiro do próprio dono, atrás do mesmo guarda de sessão. |
| Tem mais de uma frente de stack? | Não. |
| Requisito ambíguo que exija spec formal? | Não. |

**Trilha rápida.**

## Decisões autônomas

| Dúvida | Decisão | Alternativa descartada e por quê |
|---|---|---|
| Tabela nova ou colunas em `accounts`? | **Tabela `cards`**, chaveada pela conta. | `accounts` é espelho do que a fonte manda e é reescrita a cada sincronização; coluna do dono ali seria apagada pela carga seguinte, em silêncio. |
| Quais cartões nascem cadastrados? | Os que a base tiver com `type = 'CREDIT'`, derivados na migração e mantidos pela sincronização. | Fixar quatro cartões no código faria o painel de outra base nascer errado, e o número quatro é medição desta base, não regra do produto. |
| Onde a taxa do cartão mora, já que `/dividas` também a edita? | **Uma casa só: `cards.monthly_rate_bp`.** A escada passa a ler dali, e o campo de taxa de `/dividas` para um degrau de cartão escreve na mesma casa. | Duas casas é exatamente o defeito que o `015` fechou: o mesmo fato com dois nomes fez o painel perguntar para sempre o que já tinha sido respondido. |
| Em que tela se edita? | **Em `/configuracao`**, que o `015` estabeleceu como a única tela do que só o humano sabe. | Tela nova por entidade multiplica navegação e contraria a norma que o item anterior escreveu. |
| Fechamento e vencimento se validam como? | Dia do mês de 1 a 31, campo opcional. | Data completa não é o que o dono sabe: ele sabe "fecha dia 3". |
| O que este item calcula com fechamento e vencimento? | **Nada.** Ele os guarda. Quem os usa é o `026`. | Entregar a curva da fatura junto misturaria dois itens e faria o `026` deixar de existir sem que ninguém tivesse decidido isso. |
