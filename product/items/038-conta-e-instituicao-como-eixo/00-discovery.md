# Discovery — 038-conta-e-instituicao-como-eixo

**Item do roadmap:** `038-conta-e-instituicao-como-eixo` — todo lançamento diz
de que banco e de que conta veio, e os gastos se leem, filtram e agrupam por
instituição e por conta.

**Data:** 2026-09-10 · **Origem:** plano "Base financeira organizada", aprovado
pelo dono em 10/09/2026; o dono pediu a conta como eixo no mesmo dia. ·
**Trilha declarada:** rápida

## O terreno

- `accounts` (migração 001) guarda `id` (da Pluggy), `name`, `type`, `subtype`,
  `institution`, `balance_cents`. São 12 contas; C6 BANK e o cartão Bandeirado
  têm zero lançamentos.
- **`institution` não é o banco**: para cartão, a Pluggy repete ali o nome do
  cartão — "platinum", "Itau Uniclass Mastercard Black", "Passai Visa Gold".
- **O banco é a conexão (item) da Pluggy.** São 5, todas pelo conector
  MeuPluggy (o nome do conector é "MeuPluggy", não o do banco):
  - `71349dd7` — C6 BANK (conta) + Bandeirado (cartão)
  - `838a2507` — Mercado Pago (conta) + Mercado Pago (cartão)
  - `af3c4101` — Nu Pagamentos (conta) + **platinum (cartão do Nubank)**
  - `d2dabe75` — CAIXA corrente + CAIXA poupança
  - `f7d463e2` — itau (corrente) + cartões Black, Múltiplo e **Passaí Visa Gold**
- O `037` fase 1 cria `pluggy_items` e grava `accounts.item_id` (migração 019).
  Este item consome as duas coisas e não existe antes delas.
- Eixos de leitura em `app/queries/axes.json` (cinco hoje), somados por
  `aggregate` em `app/queries/axes.py`; o teste
  `test_the_five_axes_repartition_the_same_total` prova que todos repartem o
  mesmo total.
- Precedente: `cards` foi separada de `accounts` (migração 013) justamente para a
  sincronização não apagar o que o dono informou. `/configuracao` é a tela do
  que só o humano sabe (item `015`), e campo vazio quer dizer "não mexi" (`032`).

## INVEST

| Critério | Passa | Observação |
|---|---|---|
| Independente | sim, em ordem | Consome só o que a fase 1 do `037` grava, e ela vem antes na fila. A dependência é de ordem, não de escopo: quebrar não a remove. |
| Negociável | sim | Fixo: banco = conexão; nomes do dono intocados pela sync. Conversável: onde se edita. |
| Valioso | sim | "Quanto o cartão do Nubank pesa" deixa de exigir saber que "platinum" é o Nubank. |
| Estimável | sim | Uma fase. |
| Pequeno | sim | Uma fase. |
| Testável | sim | Exemplos abaixo com as contas reais. |

**Veredicto do INVEST:** segue como está.

## História

Como dono, quero ver em cada lançamento de que banco e de que conta ele veio,
com nomes que eu reconheço, e somar e filtrar os gastos por banco e por conta,
para saber quanto cada cartão e cada banco pesam.

## Regras e exemplos

### R1 — A instituição é a conexão da Pluggy; o nome inicial vem da conta corrente dela

- **E1.1** — Conexão `af3c4101`, com "Nu Pagamentos S.A. - Instituição de
  Pagamento" (BANK) e "platinum" (CREDIT), sem nome dado pelo dono: a
  instituição se chama "Nu Pagamentos S.A. - Instituição de Pagamento", e o
  cartão "platinum" aparece sob ela.
- **E1.2** — Conexão cujas contas são todas de crédito: o nome inicial é o da
  primeira conta da conexão por ordem de nome.

### R2 — O dono nomeia a instituição e dá apelido à conta; a sincronização nunca os toca

- **E2.1** — O dono renomeia a instituição `af3c4101` para "Nubank" e a conta
  "platinum" para "Cartão Nubank"; uma nova carga do mesmo bruto mantém os dois
  nomes.
- **E2.2** — Campo vazio não mexe no nome guardado; apagar o apelido é o botão
  próprio do campo, e a conta volta a mostrar o nome vindo da Pluggy.

### R3 — Instituição e conta são eixos de leitura, e os eixos continuam repartindo o mesmo total

- **E3.1** — Em `/gastos`, eixo "instituição", agosto de 2026: uma linha por
  banco; a soma das linhas é igual ao total de gasto do período e igual à soma
  do eixo "grupo".
- **E3.2** — Eixo "conta": o cartão Itaú Black e o cartão Itaú Múltiplo
  aparecem em linhas separadas, cada um com o apelido do dono quando houver.

### R4 — Conta sem lançamento continua nomeável

- **E4.1** — C6 BANK (zero lançamentos) aparece em `/configuracao` para receber
  apelido; no eixo de gastos não aparece, porque não há o que somar.

## Perguntas em aberto

Nenhuma.

## Trilha

**Trilha: rápida**

| Gatilho | Verdadeiro | Evidência |
|---|---|---|
| Zero perguntas em aberto | sim | Nenhuma. |
| Uma stack só | sim | Só a frente `api` (`.`, Python). |
| Sem mudança de contrato | sim | Não existe OpenAPI; as rotas novas são POST de formulário em `/configuracao`. |
| Sem dependência nova | sim | Nenhum pacote novo. |

## Decisões autônomas

| Dúvida | Decisão | Alternativa descartada e por quê |
|---|---|---|
| Onde mora o nome dado pelo dono? | Em **tabelas próprias** (`institution_names`, `account_nicknames`). | Coluna em `accounts` fica ao alcance do upsert da carga — o defeito que a `013` separou em `cards`. |
| De onde vem o nome inicial da instituição? | Da **conta BANK da conexão**. | `accounts.institution` repete o nome do cartão, e o conector se chama "MeuPluggy". |
| Onde se edita? | Em **`/configuracao`**, junto do resto do que só o humano sabe. | Tela nova para dois campos por conta espalha o que o `015` juntou. |
| Os eixos novos entram em `axes.json`? | **Sim**, `instituicao` e `conta`; o teste de repartição passa a cobrar sete eixos. | Filtro sem eixo impede somar por banco, que é o que o dono pediu. |
