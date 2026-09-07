# Discovery — 008-simulador-e-base-de-fatos

**Item do roadmap:** `008` — Um formulário curto responde **"isso me afasta ou me
aproxima, e quantos dias"**, o cenário pode ser guardado e comparado, e o mesmo
formulário captura os fatos que só o humano sabe.

**Data:** 2026-09-07

## História

Como dono deste painel, quero descrever uma decisão e ver em **dias** o que ela
muda, e registrar o que só eu sei, para decidir com número em vez de argumento.

## Regras e exemplos

### R1 — A resposta é em dias, e o motor é o mesmo do objetivo

- **E1.1** — A unidade do produto é a distância até o objetivo. Reais são a
  entrada; a saída é dia.
- **E1.2** — O simulador **não tem motor próprio**: injeta o efeito mensal na
  mesma simulação do item `007`. Dois motores discordariam, e o dia em que
  discordassem seria o dia em que o dono precisa acreditar.

### R2 — Virar "nunca" em data não é uma diferença de dias

- **E2.1** — Se antes havia data e depois não há — ou o contrário —, a resposta
  **não é um número**. É a diferença entre chegar e não chegar, e chamá-la de N
  dias seria inventar uma aritmética sem primeiro termo.
- **E2.2** — Com resultado mensal positivo mas **menor que os juros da escada**,
  também não há data. A tela diz isso com essas palavras, em vez de repetir
  "enquanto o resultado for negativo" sobre um número positivo.

### R3 — O que só o humano sabe tem nome, valor e validade

- **E3.1** — Saldo de quitação, custo de transporte, taxa de cartão: nada disso
  está em extrato. Enquanto não estiver na base de fatos, o painel declara a
  premissa na tela em vez de fingir que sabe.
- **E3.2** — Fato sobre dinheiro **vence**: um saldo de quitação cotado em
  setembro não é o de dezembro. O fato guarda até quando vale, e a tela marca o
  vencido.

### R4 — Cenário guardado é para comparar

- **E4.1** — Um cenário guardado com o mesmo nome substitui o anterior: a lista é
  de decisões, não de tentativas.

## Perguntas em aberto

Nenhuma.

## Trilha

**Trilha: rápida.** Uma fase.
