# Discovery — 004-resumo-e-projecao

**Item do roadmap:** `004-resumo-e-projecao` — A tela inicial mostra saldo,
dívida total, quanto sobra este mês e a **projeção de saldo dia a dia dos
próximos 45 dias**.

**Data:** 2026-09-07

## INVEST

| Critério | Passa | Observação |
|---|---|---|
| Independente | sim | Depende do `003` e do `011`, ambos concluídos. O comprometido datado já existe e já está correto. |
| Negociável | sim | Fixo: os quatro números e a linha de 45 dias. Conversável: sobre qual posição a linha corre, de onde sai a renda esperada, como o gasto que não é compromisso entra na conta. |
| Valioso | sim | É a tela que responde *"e daí?"*. Sem ela o painel diz onde o dinheiro foi; com ela diz para onde está indo. Com cheque especial a 3,52% a.m., o real marginal se ganha não entrando no vermelho — e projeção é o que impede. |
| Estimável | sim | Duas fases: motor de projeção · tela de Resumo. |
| Pequeno | sim | Nenhuma migração, nenhuma dependência nova, nenhuma tabela nova. |
| Testável | sim | Todo número sai de consulta sobre a base de 05/09/2026, e o saldo somado bate com `docs/plano.md` ao centavo. |

**Veredicto do INVEST:** segue como está.

## História

Como dono deste painel, quero abrir a tela inicial e ver onde estou e para onde
estou indo nos próximos 45 dias, para saber se o mês que vem me afunda ou me
tira do vermelho — e quanto.

## Regras e exemplos

### R1 — Há três posições, e confundi-las é o erro que destrói a tela

- **E1.1** — A soma dos saldos das 12 contas é **−R$ 27.449,71**, exatamente o
  número congelado em `docs/plano.md`. Ele é a **posição consolidada**.
- **E1.2** — Separada por tipo: as 6 contas bancárias somam **−R$ 10.705,09** —
  o caixa, que é o que entra no cheque especial — e os 6 cartões somam
  **−R$ 16.744,62**, que é exatamente a linha "Cartões" da escada de dívida.
  As três se leem juntas e nenhuma substitui as outras.
- **E1.3** — Os três números aparecem na tela com nome próprio. Uma tela que
  mostra só "saldo: −R$ 27.449,71" esconde que R$ 16.744,62 disso é dívida de
  cartão a 51% ao ano e o resto é cheque especial.

### R2 — A projeção corre sobre a posição consolidada, não sobre o caixa

- **E2.1** — Os **54** lançamentos com data futura na base estão **todos** em
  conta de cartão: são parcelas lançadas adiante na fatura. Nenhum deles sai do
  caixa no dia em que está datado.
- **E2.2** — Projetar o caixa exigiria saber a data de vencimento de cada fatura,
  que a base não traz. Projetar a posição consolidada não exige: uma compra no
  cartão piora a posição no dia da compra, e o pagamento da fatura é
  transferência entre duas contas de dentro da posição — soma zero, e já está
  marcado `is_transfer`.
- **E2.3** — A tela declara isso em texto. Dizer "projeção de saldo" sem dizer de
  qual saldo é a forma mais rápida de o dono ler a linha errada.

### R3 — Projetar renda inteira contra gasto pela metade é mentir para cima

- **E3.1** — O calendário de 45 dias traz **R$ 17.176,05** de compromisso datado.
  A renda esperada no mesmo período traz **R$ 24.452,42**, porque a janela de 45
  dias alcança dois créditos de salário. Só com essas duas parcelas a linha
  **sobe** R$ 7.276,37 — e o painel diria que o buraco está se fechando sozinho.
- **E3.2** — O compromisso é só a parte datável do gasto. O gasto mensal mediano
  é **R$ 17.677,46**; o comprometido é **R$ 8.026,79**. A diferença,
  **R$ 9.650,67/mês**, é gasto variável, e ela precisa entrar na projeção ou a
  linha não fecha com o déficit que o produto existe para resolver.
- **E3.3** — Com as três parcelas — comprometido datado, renda esperada no dia
  mediano e gasto variável diluído por dia do mês — a posição vai de
  **−R$ 27.449,71** a **−R$ 34.441,79** em 45 dias, passando pelo pior ponto,
  **−R$ 40.722,95**, em 13/10/2026. São **−R$ 6.992,08** no período, ou cerca de
  R$ 4.661/mês, na mesma ordem do déficit de R$ 4.940,72 que `docs/plano.md`
  mede por outro caminho.

### R4 — Mediana, não média, e a tela diz que é projeção

- **E4.1** — A renda mediana dos seis meses completos é **R$ 12.226,21**. A média
  seria R$ 16.605,25, puxada por 03/2026, que teve R$ 42.210,26 — o crédito
  atípico que `docs/plano.md` exclui à mão. A mediana o neutraliza sozinha, sem
  regra especial e sem alguém decidir o que é atípico.
- **E4.2** — O dia do crédito é o **dia 14**, mediana dos dias observados de
  entrada — a mesma régua que o `003` usa para prever vencimento.
- **E4.3** — Cada número projetado é declarado como projeção, com a régua ao
  lado. Número que parece exato e não é destrói a confiança no resto.

### R5 — Quanto sobra este mês é uma subtração, e ela é negativa

- **E5.1** — Renda mediana menos gasto mediano dá **−R$ 5.451,25/mês**. É a
  resposta a "quanto sobra", e ela é negativa: o produto existe por causa disso.
- **E5.2** — A tela não suaviza, não arredonda para cima e não põe emoji. Também
  não alarma: sem vermelho piscando, sem alerta decorativo. O número basta.

### R6 — A linha do tempo é a escala graduada, que já é a assinatura do projeto

- **E6.1** — A linguagem visual diz que a escala graduada é o único ornamento e
  aparece onde existe distância a percorrer. A projeção de 45 dias é literalmente
  isso, e reusa a mesma forma da tela de login e do calendário do `003`.
- **E6.2** — A linha se lê sem gráfico: cada ponto de virada tem data e valor em
  texto, com `tabular-nums`. Sem rede, sem Chart.js, a tela continua respondendo
  a pergunta.

## Perguntas em aberto

Nenhuma.

Quatro dúvidas técnicas, todas registradas em `decisoes-autonomas.md`: sobre qual
posição a linha corre, de onde vem a renda esperada, como o gasto que não é
compromisso entra, e o que é "quanto sobra". Nenhuma é pergunta para o dono — as
quatro se medem contra a base.

A pergunta que **seria** dele — *"quanto você espera receber no mês que vem?"* —
vira parâmetro editável no item `008`, quando `plan_facts` existir. Até lá a
tela usa a mediana e **declara a premissa na própria tela**, que é o que o
prompt desta corrida manda fazer enquanto o fato não entra.

## Trilha

**Trilha: rápida.**

| Gatilho | Verdadeiro | Evidência |
|---|---|---|
| Zero perguntas em aberto | sim | Nenhuma sobrou. |
| Uma stack só | sim | Python 3.12 servindo HTML por Jinja2. |
| Sem mudança de contrato | sim | Nenhum OpenAPI, nenhum consumidor externo. |
| Sem dependência nova | sim | Nada entra no `pyproject.toml`. |
