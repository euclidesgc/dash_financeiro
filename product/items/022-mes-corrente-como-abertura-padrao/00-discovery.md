# Discovery — 022-mes-corrente-como-abertura-padrao

**Item do roadmap:** `022-mes-corrente-como-abertura-padrao` — toda tela abre no
presente. O período padrão de `/gastos` passa a ser do dia 01 do mês corrente até a
data de referência, e `/gastos` passa a aceitar `?data=` como as outras cinco telas,
em vez de ser a única que chama o leitor e descarta o que foi pedido.

**Data:** 2026-09-07 · **Trilha declarada:** rápida

## O terreno, lido no código

`app/routers/spending.py:98` chama `default_period(screen_date(None).date)` — passa
`None` ao leitor único, isto é, **descarta o `?data=` que o dono digitou**. É a única
das seis telas que faz isso; as outras cinco consomem `screen_date(pedido)` desde o
`016`.

`app/queries/period.py:41-47` decide a janela: seis meses **fechados**, terminando no
último dia do mês anterior. A razão está escrita ali — o mês em curso abriria a tela
sobre um punhado de dias.

`app/queries/crossings.py:50-52` divide o total pelos meses de calendário que a janela
toca, com piso de um. Numa janela de cinco dias, "média mensal" imprime a soma de cinco
dias.

## Regra, exemplo e pergunta

- **Regra.** `/gastos` abre no mês corrente, do dia 01 até a data de referência.
- **Regra.** `/gastos` responde pela data pedida em `?data=`, com os mesmos três
  estados do leitor único: sem pedido, pedido aceito, pedido recusado.
- **Regra.** Escolher outro período continua sendo do dono: o padrão é a abertura, não
  a única janela.
- **Exemplo.** Com a referência em 05/09/2026, a abertura mostra 7 lançamentos e
  R$ 730,59, e não os 732 lançamentos e R$ 103.772,33 da janela de hoje.
- **Pergunta que a troca expõe:** o corte em "hoje" esconde 54 lançamentos e
  R$ 6.997,99 já postados depois da referência. Resolvida abaixo.
- **Pergunta que a troca expõe:** a média mensal passa a dividir cinco dias por um mês.
  Resolvida abaixo.

## Os quatro gatilhos de trilha completa

| Gatilho | Resposta |
|---|---|
| Mexe em contrato público ou OpenAPI? | Não. `/gastos` já aceita `inicio`, `fim` e passa a aceitar `data`, que as outras cinco telas já aceitam. |
| Toca autenticação, autorização ou dado pessoal? | Não. |
| Tem mais de uma frente de stack? | Não. |
| Requisito ambíguo que exija spec formal? | Não: as duas ambiguidades estão resolvidas abaixo, e nenhuma é de produto. |

**Trilha rápida.**

## Decisões autônomas

| Dúvida | Decisão | Alternativa descartada e por quê |
|---|---|---|
| A janela termina na data de referência ou no fim do mês? | **Na data de referência.** É o que o item pede, e é o que "abrir no presente" significa: o painel não afirma como gasto o que ainda não aconteceu. | Terminar no fim do mês somaria ao gasto do mês parcelas de cartão já postadas para datas futuras — o painel passaria a responder "quanto vai sair" onde a tela responde "quanto saiu", e o número deixaria de casar com o extrato. |
| Então o que se faz com os R$ 6.997,99 já postados depois da referência? | **Nomear.** A tela diz, em uma linha, quantos lançamentos e quanto dinheiro já estão postados no mês depois da data de referência, e não os soma. | Esconder em silêncio é o defeito que o item existe para não criar: um número que some sem que a tela diga é a mesma classe do "sucesso mentiroso" do `012`. |
| E a "média mensal" de uma janela de cinco dias? | O rótulo passa a depender da janela: **"média mensal" só quando a janela cobre meses inteiros** (começa no dia 01 de um mês e termina no último dia de um mês); fora disso, "no período", e o número é o total. | Manter o rótulo fixo imprime "média mensal R$ 730,59" sobre cinco dias, e é a média do cruzamento fixa × essencial que dimensiona a reserva do objetivo: um rótulo errado ali vira decisão errada de dinheiro. Dividir por fração de mês inventa precisão que a base não tem. |
| `app/plan/objective.py` passa a consumir a janela de `/gastos`? | **Não.** Ele monta a própria janela e continua montando. | Acoplar o objetivo à janela da tela faria a reserva alvo mudar quando o dono trocasse o período que está olhando — a projeção deixaria de ser propriedade da base e passaria a ser propriedade da navegação. |
