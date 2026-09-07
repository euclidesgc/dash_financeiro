# Veredicto — item `005-dividas-e-simuladores`, fase 1

**Resultado:** `APROVADO`

Branch: `005-dividas-e-simuladores/fase-1-escada` · ponta julgada `6ef9bd1` · base `076806c`
Data: 2026-09-07 · Validador cego, agente novo.

> **O código mergeado não é byte a byte o que este validador julgou.** Os oito
> apontamentos abaixo foram corrigidos depois do veredicto, no commit `0892c0f`,
> cada um com teste que falha sem a correção. Nenhum deles reprovava critério.
> A decisão está registrada como `D7`: uma validação por fase, e achado que não
> reprova vira correção com teste, nomeada aqui e na entrega — não uma rodada
> nova.

## Portões

| Portão | Resultado |
|---|---|
| lint/analyze | **não existe** — nenhum linter ou typechecker em `pyproject.toml` nem job no CI. Declarado, não presumido. |
| testes | **OK** — `352 passed`, `EXIT=0`, capturado em arquivo. |
| gates | **OK** — `✓ gates: limpos (árvore completa, 260 arquivo(s)).` O validador rodou também `bloqueio.test.sh`, `atalho.test.sh`, `medir.test.sh` e `merge-se-liberado.test.sh`, todos `EXIT=0`. |

## Critérios — todos cumpridos

- [x] **`comando` — RF-01 a RF-04, RF-09** — `card 4 -1674462`, `mortgage 1
      -23858518`, `overdraft 2 -1119018`, `vehicle 1 -3917636`; duas taxas
      conhecidas (`mortgage 72`, `vehicle 163`); seis sem taxa. **O validador
      recalculou as duas taxas derivadas por conta própria**, sem chamar o
      código: 8,9899% a.a. efetivos dão 0,719955% ao mês → 72 bp.
- [x] **`comando` — RF-14 a RF-19** — `13 passed`. Os cinco testes exigidos
      existem e foram lidos no fonte, linha a linha.
- [x] **`comportamental` — RF-06, RF-07, RF-08, RF-23** — HTML parseado com
      `html.parser`, atribuindo cada `data-degrau` à sua `<section>`: escada com
      2 (`163`, `72`, nessa ordem), sem-taxa com 6.
- [x] **`comportamental` — RF-10, RF-11, RF-12** — `3,52` sobe o degrau ao
      **topo** da escada; `-1` devolve `400` com a string `-1` na recusa e **não
      muda** a taxa; taxa vazia devolve o degrau ao bloco sem taxa.
- [x] **`comportamental` — RF-14 a RF-16** — `data-parcelas="14"` (0 < 14 < 45),
      `data-juros="729462"`. **Recalculado à mão pelo validador**, iterando o
      saldo à taxa do contrato: 31 meses restantes, 45 − 31 = 14 parcelas, e
      14 × 123533 − 1000000 = 729462. Bate ao centavo.
- [x] **`comportamental` — RF-20 a RF-22** — `−R$ 39.176,36` e `−R$ 1.235,33` na
      primeira leitura; depois de gravar R$ 35.000,00, `data-desconto="417636"`.
- [x] **`comportamental` — RF-25** — base só com migração e seed: `200`,
      `Nenhuma dívida na base.`, e o destino do link responde `200`.
- [x] **`comportamental` — RF-24** — seis medições, `cabe=true` em todas, e
      `naoZerados=0` nos 23 elementos de `#escada *`.
- [x] **`estrutural` — RF-24** — as três capturas, PNG, nas dimensões certas.
- [x] **`comportamental` — RF-26** — `href="/dividas">Ver as dívidas<`.
- [x] **`comportamental` — RF-05** — com `DASH_MANUAL_DIR` vazio: `EXIT=0`,
      `debts rebuilt: 6`, e zero degraus de contrato.
- [x] **`comando` — portão local** — `352 passed`.
- [x] **`comando` — RF-13, RF-27** — `STDOUT_LINHAS=0`, `STDERR_LINHAS=0`, os
      dois fluxos redirecionados para arquivos separados e contados.
- [x] **`comando` — RF-24 cor** — zero linhas.
- [x] **`comportamental` — RF-23 guarda** — `302` com `location: /login`.

## Caça extra

Nenhum dos três POST devolveu 500 sob id inexistente, id não numérico, valor
ilegível, negativo, zero, vazio ou gigante. Nenhuma parcela ou juro negativo
apareceu. A ordem da escada muda de fato quando a taxa é gravada e desfaz quando
é apagada.

## Os oito apontamentos — todos corrigidos em `0892c0f`

Nenhum reprovava critério. Os dois primeiros são os que o próprio validador
mandaria para o PR antes dos outros.

1. **Quitação acima do valor presente chamada de "desconto", na cor de ganho.**
   `discount_cents` não tinha piso e o template fixava `class="positive"`.
   Medido: `valor=45000,00` devolvia `−R$ 5.823,64` sob o rótulo "Desconto".
   Banco costuma cotar quitação acima do valor presente estrito — a tela mentia
   a favor de uma decisão de R$ 39 mil. Agora é **ágio**, na cor de saída, com a
   frase que diz que quitar assim custa mais que seguir pagando.
2. **O simulador respondendo `R$ 0,00` para dívida sem taxa.** Zero não é
   abstenção: é a afirmação de que o dinheiro não economiza nada, e contradiz o
   que a tela declara duas seções acima. Agora recusa e pede a taxa.
3. **Mensagem do CPython, em inglês, na tela.** `int(degrau)` estourava e o
   `except ValueError` empacotava `invalid literal for int()` como aviso ao dono.
4. **`repr` de Python na prosa** — `Taxa inválida: 'abc'.` com as aspas do repr.
5. **A recusa nomeava o campo errado.** Os dois parâmetros do carro eram
   validados com mensagens que falavam de "aporte".
6. **Gravação silenciosa em degrau inexistente.** `set_rate` não conferia
   `rowcount`: a tela recarregava como se tivesse salvo.
7. **As capturas estavam vencidas**, mostrando `vehicle`, `mortgage` e
   `overdraft` — as chaves cruas do schema, em inglês, já traduzidas na tela viva.
8. **O teste do valor presente reimplementava a fórmula** em vez de chamar o
   carregador: uma regressão em `_vehicle` ou `_paid` passaria verde.

## Instrumentos do implementer

Só o critério RF-14 a RF-19 depende da suíte do avaliado, por construção — ele
nomeia o arquivo e o conteúdo. O validador refez por fora as duas contas
centrais (o valor presente das 45 parcelas e a simulação de R$ 10.000) com
aritmética própria, e confrontou com o que o banco e a tela devolveram.
