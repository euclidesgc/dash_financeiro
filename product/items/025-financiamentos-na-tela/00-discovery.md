# Discovery — 025-financiamentos-na-tela

**Item do roadmap:** `025-financiamentos-na-tela` — o financiamento do imóvel e o do
veículo se editam na tela, como todo o resto do que só o humano sabe. Hoje os dois moram
em arquivo JSON escrito à mão e fora do versionamento, lidos por `app/debts/ladder.py`.

**Data:** 2026-09-07 · **Trilha declarada:** rápida

## O terreno, lido no código

`app/debts/ladder.py:93-101` lê dois arquivos de `data/manual/`:
`financiamento_caixa.json` e `cdc_safra_veiculo.json`. Arquivo ausente é degrau ausente,
nunca carga quebrada (`app/debts/ladder.py:104-111`) — o painel precisa subir numa
máquina que nunca recebeu os contratos.

Os dois degraus não se calculam do mesmo jeito, e isso decide o desenho do item:

- **Imóvel** (`app/debts/ladder.py:114-128`): o saldo devedor é **informado** e a taxa
  mensal é derivada da taxa efetiva anual, uma vez, na leitura.
- **Veículo** (`app/debts/ladder.py:131-145`): o saldo é **calculado** — valor presente
  das parcelas ainda não vencidas, descontadas à taxa do contrato. O comentário no
  código diz por quê: é o que a lei manda o banco oferecer na quitação antecipada, e
  copiar um número o congelaria.

## Regra, exemplo e pergunta

- **Regra.** Os dois financiamentos se editam na tela, com os campos que o formato de
  hoje já tem: saldo devedor, taxa mensal, prazo em meses e valor da parcela.
- **Regra.** Nenhum número muda de valor ao mudar de lugar.
- **Regra.** O painel continua subindo numa máquina sem contrato nenhum.
- **Exemplo.** O dono corrige o saldo devedor do imóvel na tela. A escada se reordena
  na mesma requisição, e nada precisa ser editado em arquivo.
- **Pergunta em aberto:** nenhuma de produto.

## Os quatro gatilhos de trilha completa

| Gatilho | Resposta |
|---|---|
| Mexe em contrato público ou OpenAPI? | Não. |
| Toca autenticação, autorização ou dado pessoal? | Não. |
| Tem mais de uma frente de stack? | Não. |
| Requisito ambíguo que exija spec formal? | Não. |

**Trilha rápida.**

## Decisões autônomas

| Dúvida | Decisão | Alternativa descartada e por quê |
|---|---|---|
| Onde os financiamentos passam a morar? | **Tabela própria**, e a migração importa os dois arquivos JSON se eles existirem. | Gravar direto em `debts` os perderia: `rebuild` apaga a tabela inteira e a reescreve a cada reconstrução. |
| O saldo do CDC do veículo passa a ser digitado? | **Não. Continua calculado** — valor presente das parcelas não vencidas, à taxa do contrato. O que se edita é o ingrediente: taxa, parcela, prazo e primeiro vencimento. | Digitar o saldo o congela no dia em que foi digitado, e o número volta a envelhecer em silêncio — que é o defeito que o comentário no código de hoje existe para evitar. |
| E o do imóvel? | **Continua informado**, porque é o que o aplicativo do banco mostra. A taxa se digita **mensal**, já convertida na importação. | Manter a taxa anual na tela obrigaria o dono a saber que o painel a converte, e a conversão sumiria dentro de um campo com outro nome. |
| Os arquivos JSON continuam sendo lidos? | **Não**, depois da importação. A leitura tem uma origem só. | Duas origens fazem a tela e o arquivo discordarem, e quem vence passa a ser a ordem de execução. |
| E numa máquina sem os arquivos? | Nasce sem financiamento nenhum, e o dono informa na tela. O painel sobe igual. | — |
| Em que tela se edita? | **Em `/configuracao`**, pela mesma razão do `024`. | — |
