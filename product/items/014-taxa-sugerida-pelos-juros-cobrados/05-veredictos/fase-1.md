# Veredicto — item `014-taxa-sugerida-pelos-juros-cobrados`, fase 1

**Resultado:** `APROVADO`

Branch: `develop` · ponta julgada `729ad39`
Data: 2026-09-07 · **Três** validadores cegos, agentes novos, em sequência.

> As três rodadas aprovaram. Cada uma delas, porém, atacou a pergunta que este
> item existe para responder — *o número é defensável ou é ruído com cara de
> precisão?* — e cada uma achou que ainda era ruído. As correções entre as
> rodadas mudaram a sugestão de **4,22% → 6,71%** e a faixa da `CAIXA` de
> **cinco pontos percentuais para dezessete pontos-base**.

## O que cada rodada derrubou

**Primeira.** O `</td>` perdido no diff — 18 `<td>` para 12 `</td>` no bloco
servido. E: **o banco cobra em atraso.** Os oito `COBRANCA DE JUROS` da `CAIXA`
caem entre os dias 01 e 03: o lançamento de 01/09 é o preço de **agosto**.
Casado com o mês do lançamento, as taxas saíam `383, 741, 867, 1153`; casado com
o mês que remunera, quase constantes. E o extremo de 11,53% vinha do **mês em
curso**, cinco dias de saldo sob um mês inteiro de juros.

**Segunda.** A correção estava calibrada para uma conta e **não alcançava a
outra**. O `itau` posta no dia 6 e o corte era em 5: nenhum lançamento dele era
deslocado. A prova foi abril — a conta ficou positiva **todos os 30 dias** e
ainda assim o banco cobrou R$ 1.138,07 em 07/04. O código atribuía a abril, abril
não tinha dia negativo, e a cobrança era **descartada**: 31% de todo o juro da
conta, a maior cobrança da série, sumia. A sugestão foi de 4,22% para **6,71%**.

**Terceira.** O filtro de mês parcial se media contra **os dias que a
reconstrução tem**, não contra o calendário. O mês mais antigo é truncado por
construção — a caminhada para no primeiro lançamento —, então comparava-se
consigo mesmo e passava: 14 de 26 dias reconstruídos é mais da metade, 14 de 31
dias reais não é. Era esse mês que formava o piso de **3,13%** da `CAIXA`, cujos
outros meses ficam em 7,99, 8,00 e 8,16. Mais: `abs(charged)` leria um **estorno**
como taxa, e a base tem cinco lançamentos `CREDITO JUROS` positivos.

## Portões (terceira rodada)

| Portão | Resultado |
|---|---|
| lint | **OK** — `All checks passed!`, `EXIT=0`. |
| testes | **OK** — `431 passed`, `EXIT=0`. |
| gates | **OK** — `✓ gates: limpos (árvore completa, 342 arquivo(s))`, com o número conferido contra o passe falso. |

## Critérios — os dez cumpridos

- [x] **`comando` — RF-01, RF-03, RF-07, RF-08** — as duas contas com os seis
      valores exigidos. **O validador não aceitou o número pela saída do
      módulo:** refez a atribuição com implementação independente (SQL cru mais
      `statistics.median`) e reproduziu **mês a mês**. E auditou lançamento a
      lançamento: os 9 do `itau` e os 8 da `CAIXA` são todos alcançados, nenhum
      vai para o mês errado, nenhum fica órfão.
- [x] **`comando` — RF-13, RF-14** — os cinco testes localizados por linha,
      inclusive o do **dia 6** — o dia em que a conta real posta e o que o corte
      fixo não alcançava. O validador reverificou a fronteira com bases próprias.
- [x] **`comando` — RF-15** — `<td>=18 </td>=18`, e a página inteira passa por
      `html.parser` sem erro de aninhamento.
- [x] **`comportamental` — RF-09, RF-10** — as duas sugestões, o campo do `itau`
      com `value="6,71"`, e as **quatro** linhas de cartão sem sugestão. A
      exclusão de cartão é estrutural, não amostral — ele confirmou por fora.
- [x] **`comportamental` — RF-11** — depois de **quatro** leituras da tela, todas
      com resposta byte a byte idêntica, o banco continua com `2` taxas gravadas,
      as duas de contrato.
- [x] **`comando` — RF-02, RF-04, RF-05, RF-06** — os seis testes conferidos
      asserção a asserção.
- [x] **portão local, lint, RF-12 e as capturas** — `431 passed`, nenhum número
      cravado no código, os três PNG válidos.

## Os três apontamentos da terceira rodada — corrigidos em `fd0ea0e`

Os dois primeiros estão descritos acima. O terceiro: **`posts_in_arrears` decide
uma vez por conta**, e numa conta de dias irregulares — `[1, 1, 28, 28]`, mediana
14 — erraria metade dos lançamentos. Não afeta esta base, cujas medianas são 6 e
1,5 contra o corte de 10. Fica como limitação conhecida da regra, registrada.

**Os números dos critérios mudaram depois deste veredicto**, porque a correção do
mês truncado altera a `CAIXA` de `months=4, faixa 313-816` para `months=3, faixa
799-816`. Está dito aqui em vez de escondido.
