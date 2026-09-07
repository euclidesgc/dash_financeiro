# Discovery — 015-configuracao-e-nome-do-beneficiario

**Origem:** dois pedidos do dono, no mesmo dia, que são o mesmo pedido.

> *"preciso de uma área de configuração no sistema para que eu possa informar
> esses e outros valores que podem servir de base para suas sugestões, cálculos e
> recomendações."*

> *"como eu posso descobrir o verdadeiro nome do estabelecimento que aparece no
> meu extrato. Aqueles nomes não são nada descritivos e eu fico sem saber o que é
> exatamente."*

O segundo é caso particular do primeiro: o nome do beneficiário é um valor que só
o dono sabe, alimenta leitura e recomendação, e hoje não tem onde morar.

**Data:** 2026-09-07

## INVEST

| Critério | Passa | Observação |
|---|---|---|
| Independente | sim | Depende de `002` (taxonomia e `payee`), `005` (`plan_parameters`), `008` (`plan_facts`) e `014` (taxa sugerida) — todos concluídos. |
| Negociável | sim | Fixo: um lugar só para os valores, e o nome real do beneficiário. Conversável: quais valores entram, como o apelido se aplica, de onde vem o nome quando o dado não tem. |
| Valioso | sim | Sem isto, quatro dos números que o painel exibe são premissa declarada em vez de fato, e 82% dos lançamentos não dizem ao dono o que são. |
| Estimável | sim | Três fases: unificar o armazém · a tela de configuração · o nome do beneficiário. |
| Pequeno | sim | Uma migração, uma tela nova, uma leitura a mais na carga. |
| Testável | sim | Toda cobertura se mede por consulta sobre a base de 05/09/2026. |

**Veredicto do INVEST:** segue como está.

## História

Como dono deste painel, quero um lugar só onde informo o que só eu sei — taxas,
saldos, metas, e o nome de verdade de cada beneficiário —, para que as contas
parem de usar premissa e as telas parem de me mostrar códigos de maquininha.

## Regras e exemplos

### R1 — Hoje há duas tabelas fazendo o mesmo trabalho, e eu criei as duas

- **E1.1** — `plan_parameters` (item `005`): `name`, `value_cents`,
  `updated_at`. Escrita por `POST /dividas/parametro`, lida por
  `app.debts.simulate.parameter`. Guarda `quitacao` e `transporte`.
- **E1.2** — `plan_facts` (item `008`): `name`, `label`, `value_cents`, `unit`,
  `source`, `captured_at`, `valid_until`. Escrita por `POST /simulador/fato`,
  lida por `app.plan.whatif.facts`.
- **E1.3** — As duas guardam "o que só o humano sabe, em centavos". A segunda faz
  tudo o que a primeira faz **e mais**: rótulo, unidade, origem e validade. Duas
  tabelas para um conceito é o oposto de DRY, e o dono já viu o efeito — informou
  o saldo de quitação em `/dividas` e ele não apareceu em `/simulador`.

### R2 — Os valores estão espalhados por quatro telas

- **E2.1** — Taxa de cada dívida em `/dividas`; saldo de quitação e custo de
  transporte em `/dividas`; fatos em `/simulador`; "não uso mais" em
  `/comprometido`; regras de classificação em `/regras`.
- **E2.2** — Cada um está **contextualmente certo** onde está: a taxa se informa
  olhando a escada. O que falta é o **índice**: um lugar que liste tudo o que
  alimenta cálculo, diga o que cada valor muda e leve à tela onde ele se edita.
- **E2.3** — Nem tudo o que parece configuração é. A tolerância de dez dias do
  calendário e os 2% que separam duas compras são **parâmetros do modelo**,
  medidos contra a base, e continuam no código. A régua da invariante 26 é *o que
  só o humano sabe*, não *o que é ajustável*.

### R3 — Três constantes são meta do dono, não parâmetro de modelo

- **E3.1** — `RESERVE_MONTHS = 6` em `app/plan/objective.py` decide o alvo de
  **R$ 41.879,58**. Seis meses é escolha dele, não do código.
- **E3.2** — `MONTHS = 6` em `app/projection/monthly.py` decide sobre quantos
  meses a mediana de renda e gasto é tirada.
- **E3.3** — `WINDOW_DAYS = 45` em `app/commitments/calendar.py` é diferente: o
  item `004` a consome como contrato entre duas telas, e mudá-la muda o
  significado de "os próximos 45 dias" em três lugares. Fica no código.

### R4 — Dezoito por cento do nome real já vem da Pluggy, e o painel joga fora

- **E4.1** — Dos 1.942 lançamentos crus em `data/raw/`, **338 trazem
  `merchant`** com razão social, CNPJ e CNAE, e **169 trazem
  `paymentData.receiver.name`**. Juntos, **356 lançamentos (18%)** e **209
  descrições distintas** têm nome real disponível.
- **E4.2** — Não é dado decorativo: `Pagamento de boleto MYCON` é
  **COIMEX ADMINISTRADORA DE CONSORCIOS S.A** — uma das três assinaturas que o
  dono está decidindo se corta. `AMAZON PRIME BRSAO12/12` é
  `PRIME VIDEO E COMERCIO LTDA`. `Compra no débito via NuPay|iFood` é
  `IFOOD.COM AGENCIA DE RESTAURANTES ONLINE S.A.`
- **E4.3** — **A cadeia perde o dado no meio.** `data/raw/*.json` traz os campos;
  `ingestao/pluggy_consolidate.py` produz `data/processed/transacoes.json`
  **sem** eles; e a carga do painel lê o consolidado, por decisão `D7` do item
  `001`. Quem tem de carregar o campo adiante é o consolidador, e ele está fora
  de `app/` — o `scripts/lint.sh` varre `app tests` e não o alcança.

### R5 — Os outros 82% se resolvem por beneficiário, não por lançamento

- **E5.1** — Sobram 1.586 lançamentos em 878 descrições distintas, quase todas
  ruído de maquininha: `8663 ASSAI 232 MAC01/03`, `47441778FelipeMACAEBRA`.
- **E5.2** — Mas a classificação já agrupa por **beneficiário**: são **720**
  distintos no gasto. E o dinheiro se concentra: **os 30 maiores cobrem 56% do
  gasto; os 100 cobrem 73%.**
- **E5.3** — Logo o apelido se prende ao **beneficiário**, não à descrição, e a
  lista se ordena **por quanto dinheiro cada um representa** — para o dono
  começar pelos que importam e parar quando quiser. Batizar 878 descrições seria
  trabalho que ninguém faz; batizar 30 é uma tarde.

### R6 — O CNPJ abre a porta para o nome que ele reconhece, e precisa de rede

- **E6.1** — Razão social não é o nome que se reconhece: `O BOTICARIO
  FRANCHISING LTDA` ainda é melhor que `BOTICARIO MACAEMAC05/05`, mas o **nome
  fantasia** é o que ele lê na rua.
- **E6.2** — O CNPJ está em 338 lançamentos, e uma consulta pública resolve
  razão social **e** nome fantasia. Precisa de rede, e rede é o que este painel
  não controla — degradar sem ela é a mesma régua do item `009`.

### R7 — A IA sugere o nome, nunca o afirma

- **E7.1** — Com CNAE e categoria em mãos, o consultor do item `009` pode propor
  um nome legível. A invariante 23 continua: o modelo interpreta, quem decide é o
  dono, e o nome só entra na base quando ele aceitar.

## Perguntas em aberto

Nenhuma.

Três dúvidas apareceram e as três se resolvem por padrão já escrito no projeto,
não por pergunta ao dono:

1. **Onde o campo novo entra na cadeia de carga.** A decisão `D7` do item `001`
   já respondeu: o consolidador produz, o painel lê o consolidado.
2. **Qual das duas tabelas de configuração sobrevive.** `plan_facts` faz tudo o
   que `plan_parameters` faz e mais; a migração converte e a segunda morre.
3. **Se a tela de configuração substitui os campos das outras telas.** O padrão
   do projeto é o campo no contexto — a taxa se informa olhando a escada. A
   configuração é **índice e complemento**, não substituição.

## Trilha

**Trilha: rápida.**

| Gatilho | Verdadeiro | Evidência |
|---|---|---|
| Zero perguntas em aberto | sim | As três dúvidas viraram decisão por padrão. |
| Uma stack só | sim | Python 3.12 servindo HTML por Jinja2. |
| Sem mudança de contrato | sim | Nenhum OpenAPI, nenhum consumidor externo. |
| Sem dependência nova | sim | `httpx` já está no `pyproject.toml` desde o `001`. |
