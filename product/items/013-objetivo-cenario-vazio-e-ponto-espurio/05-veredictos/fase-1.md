# Veredicto — item `013-objetivo-cenario-vazio-e-ponto-espurio`, fase 1

**Resultado:** `APROVADO`

Branch: `013-objetivo-lista-vazia/fase-1` · base `1ef1f69` · ponta julgada `2b654df`
Data: 2026-09-07 · Validador cego, agente novo.

> Os dois apontamentos foram corrigidos depois do veredicto, com teste, em
> `a007336`. **Um deles era regressão introduzida por esta própria fase.**

## Portões

| Portão | Resultado |
|---|---|
| lint | **OK** — `All checks passed!`, `EXIT=0`. |
| testes | **OK** — `418 passed`, `EXIT=0`. |
| gates | **OK** — `✓ gates: limpos (árvore completa, 331 arquivo(s))`. |

O despacho avisou da armadilha do `gates_runner` — numa árvore sem `.git` ele
imprime `0 arquivo(s) considerados` e sai com `EXIT=0`. O validador **conferiu o
número**: 331, não zero. Portão que não mediu não aprova.

HEAD conferido no início e no fim: `2b654df`, sem mover. Foi a correção da falha
operacional registrada no veredicto do `012`.

## Critérios — os cinco cumpridos

- [x] **`comportamental` — RF-01** — o bloco `id="alavanca-vazia"` com `a lista
      de corte` e a frase do base/conservador. E os números **confirmam** a
      prosa neste estado: `conservador -452321` e `base -452321`.
- [x] **`comportamental` — RF-02, RF-03** — banco do zero, `plan_snapshots` com
      **0 linhas** antes. Quatro leituras: `0001-01-01`, `2026-09-05`,
      `2026-10-05`, `2026-09-05`. A primeira traz `id="recusa"` e `não gravou
      ponto`; a série fica com **exatamente duas** datas, e a de hoje **não**
      aparece. Ler a mesma data três vezes mantém 3 linhas, não 9.
- [x] **`comando` — RF-01, RF-02** — `12 passed`, com os dois testes localizados
      por linha e as asserções conferidas.
- [x] **portão local e de lint** — `418 passed`, `All checks passed!`.

## A caça adversarial

Dez formas de data absurda — `9999-12-31`, `0000-01-01`, `abacaxi`, vazia,
`2026-02-30`, `2026-9-5`, `2026-09-05T00:00`, `-2026-09-05`, `2101-01-01`,
`1999-12-31` — todas `200`, todas com `id="recusa"`, **nenhum 500**. Os limites
aceitos gravam. Leitura fora de ordem não corrompeu a série.

## Os dois apontamentos — corrigidos em `a007336`

1. **Regressão introduzida por esta fase.** `/objetivo` **sem** `?data=` caía no
   ramo da recusa: exibia "A data pedida não foi aceita" sobre uma requisição que
   não pediu data nenhuma, e **não gravava**. `record()` tem um chamador só, agora
   atrás da bandeira de aceitação, e os **dois links do produto** para esta tela
   não levam parâmetro. A linha do tempo — a única medida de progresso que este
   produto aceita — tinha parado de crescer pela navegação normal. Nenhum critério
   cobria isso: eles todos passam `?data=`.
2. **"Duas dessas alavancas" fixo sobre uma lista que pode ter uma.** E a frase
   "o cenário base devolve hoje o mesmo número do conservador" só é verdadeira
   quando as **duas** listas estão vazias — `base` soma as duas alavancas,
   `conservador` não soma nenhuma. O validador reproduziu com uma assinatura
   dispensada: a prosa dizia "Duas" listando uma, e afirmava igualdade sobre
   `conservador -452321` e `base -205601`.
