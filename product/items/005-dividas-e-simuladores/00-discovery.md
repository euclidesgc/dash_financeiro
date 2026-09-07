# Discovery — 005-dividas-e-simuladores

**Item do roadmap:** `005-dividas-e-simuladores` — As dívidas aparecem ordenadas
por taxa mensal, do cheque especial ao imóvel, e o simulador responde quantas
parcelas e quantos juros um aporte elimina. Inclui a decisão do Duster com saldo
de quitação e custo de transporte alternativo como **parâmetro editável**.

**Data:** 2026-09-07

## INVEST

| Critério | Passa | Observação |
|---|---|---|
| Independente | sim | Depende do `001` (contas e saldos) e do `004` (posição). Ambos concluídos. |
| Negociável | sim | Fixo: a escada por taxa, o simulador e a taxa como parâmetro editável. Conversável: de onde nasce cada dívida, como a taxa desconhecida é apresentada, qual matemática o simulador usa. |
| Valioso | sim | É a tela que responde *"onde eu ponho o próximo real"*. A resposta é sempre a dívida mais cara, e sem a escada o dono adivinha. |
| Estimável | sim | Uma fase: motor e tela juntos, porque a tela é a única consumidora do motor. |
| Pequeno | sim | Uma migração, um pacote, uma tela. Nenhuma dependência nova. |
| Testável | sim | O saldo do CDC se reproduz ao centavo pelo valor presente das parcelas; as duas taxas de contrato saem do arquivo; e o que ninguém sabe é declarado como não sabido. |

**Veredicto do INVEST:** segue como está.

## História

Como dono deste painel, quero ver minhas dívidas ordenadas pela taxa mensal e
simular o que um aporte elimina, para pôr o próximo real onde ele rende mais em
vez de onde dói menos.

## Regras e exemplos

### R1 — A escada ordena por taxa, e a taxa não sai do código

- **E1.1** — Quatro degraus na base de 05/09/2026: cheque especial
  **R$ 11.190,18**, cartões **R$ 16.744,62**, CDC do Duster **R$ 39.176,36** a
  1,63% a.m., e financiamento imobiliário **R$ 238.585,18** a **0,7200% a.m.**
- **E1.2** — Os dois saldos de conta vêm do banco de dados: a soma das contas
  bancárias negativas dá exatamente R$ 11.190,18 e a dos cartões R$ 16.744,62.
  As duas taxas de contrato vêm de `data/manual/*.json`, que já estão no disco e
  fora do controle de versão.
- **E1.3** — O saldo do CDC **não** é copiado de lugar nenhum: é o valor presente
  das 45 parcelas ainda não vencidas de R$ 1.235,33, descontadas a 1,63% a.m., e
  dá **R$ 39.176,36** — o número que o relatório de origem traz, reproduzido por
  cálculo. É o que a lei manda o banco oferecer na quitação antecipada.
- **E1.4** — A taxa mensal do imóvel também é derivada:
  `(1 + 8,9899%)^(1/12) − 1` = **0,7200% a.m.**

### R2 — O que ninguém sabe é dito como não sabido, e é editável na tela

- **E2.1** — A taxa do cheque especial e a dos cartões **não estão em lugar
  nenhum dos dados**. O relatório de origem traz 3,52% a.m. para o cheque
  especial e "a confirmar" para os cartões — os dois são fato do humano, não da
  base.
- **E2.2** — Dívida sem taxa **não entra na escada**: ela aparece num bloco
  próprio, dizendo que falta a taxa e que sem ela não dá para saber onde o
  próximo real rende mais. Colocá-la num degrau chutado seria o painel decidindo
  por ele.
- **E2.3** — A taxa se edita na tela e a escada se reordena na hora, sem
  reingestão e sem reiniciar o processo — como as regras do `002` e o "não uso
  mais" do `003`.
- **E2.4** — Preenchida a taxa do cheque especial com 3,52% e a dos cartões com
  qualquer valor acima de 1,63%, a escada fica cheque especial → cartões → CDC →
  imóvel, que é a ordem do relatório de origem.

### R3 — O simulador responde em parcelas e em juros, não em adjetivos

- **E3.1** — Um aporte aplicado a uma dívida com prazo e parcela devolve
  **quantas parcelas sozinham** e **quantos juros deixam de ser pagos**. Para o
  CDC, R$ 10.000 de aporte encurtam a dívida e o número de parcelas eliminadas é
  calculado, não estimado.
- **E3.2** — Aporte maior que o saldo quita a dívida e o excedente é devolvido
  como sobra, em vez de produzir parcela negativa.
- **E3.3** — Dívida sem prazo — cheque especial e cartão rotativo — não tem
  parcela a eliminar; o simulador devolve **juros mensais evitados**, que é a
  única resposta verdadeira ali.

### R4 — O Duster é uma decisão, e ela mora em parâmetro

- **E4.1** — O saldo de quitação antecipada do CDC é **menor** que o valor
  presente, e só o banco informa. O custo de transporte sem o carro também só o
  dono sabe. Os dois são campo editável, começam vazios, e a tela diz o que muda
  quando forem preenchidos.
- **E4.2** — Com os dois vazios, a tela mostra o que **já** dá para afirmar: o
  CDC custa 1,63% a.m. sobre R$ 39.176,36, e a parcela de R$ 1.235,33 é fluxo
  mensal preso.

## Perguntas em aberto

Nenhuma.

As duas perguntas que **seriam** do dono — a taxa dos cartões e o saldo de
quitação — são exatamente o que este item transforma em mecanismo: campo na
tela, não constante no código. É a mesma resposta que o `002` deu para a
classificação e o `003` para o que é cancelável.

## Trilha

**Trilha: rápida.** Zero perguntas em aberto; uma stack só; sem mudança de
contrato; sem dependência nova.
