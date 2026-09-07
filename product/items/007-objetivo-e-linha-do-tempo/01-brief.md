# Brief — 007-objetivo-e-linha-do-tempo

- **RF-01** — O alvo da reserva é `6 × piso de sobrevivência`, e o piso é a média
  mensal do cruzamento `fixa × essencial` nos seis meses completos anteriores.
  Na base de 05/09/2026: piso **R$ 6.979,93**, alvo **R$ 41.879,58**.
- **RF-02** — O nome do cruzamento vem da tabela `crossings`, não do template: o
  vocabulário é dado.
- **RF-03** — Existem três cenários — `conservador`, `base`, `otimista` — e cada
  um soma uma alavanca que o produto já mede: a economia das assinaturas
  marcadas, a lista de corte, e o caixa liberado pelos parcelamentos.
- **RF-04** — O resultado mensal de um cenário nunca é menor que o do cenário à
  sua esquerda.
- **RF-05** — Na base de 05/09/2026 os três valem **−R$ 4.523,21**,
  **−R$ 4.523,21** e **−R$ 4.289,45**.
- **RF-06** — A simulação é mês a mês, determinística e testada. Aplica o
  resultado positivo à escada de dívida, da mais cara para a mais barata, e só
  depois acumula reserva.
- **RF-07** — O financiamento imobiliário **não** entra na escada do objetivo, e
  o marco de dívidas mede só o que está acima de **1% ao mês**.
- **RF-08** — Resultado mensal ≤ 0 significa que **nenhum** marco é alcançado:
  os meses ficam **nulos**, e nulo é a resposta honesta — um número muito grande
  se leria como uma data distante, e isto não é distante, é nunca.
- **RF-09** — Quando não há data, a tela mostra quanto falta por mês para que uma
  data exista, e aponta as duas telas onde agir.
- **RF-10** — Os três marcos aparecem nomeados, cada um com os meses até ele ou
  com `não chega`.
- **RF-11** — Cada leitura de `GET /objetivo` grava um ponto por cenário,
  chaveado por `(data de referência, cenário)`: duas leituras no mesmo dia
  gravam um ponto só.
- **RF-12** — Com um ponto só, a tela diz que precisa de duas leituras em datas
  diferentes.
- **RF-13** — `GET /objetivo` fica atrás da sessão, e o Resumo leva até ela.
- **RF-14** — A tela obedece à linguagem visual; nenhum número medido aparece
  como literal no código.

## O que o veredicto reprovado obrigou a escrever

- **RF-15** — Data de referência fora de `2000-01-01`–`2100-12-31` cai na data de
  hoje. `0001-01-01` é ISO válido, passava a guarda e estourava doze meses antes,
  em aritmética de calendário, derrubando a rota com `500`.
- **RF-16** — O caixa que um parcelamento libera entra na simulação **no mês em
  que ele acaba**, não no primeiro. O rótulo do cenário diz "ao acabar" e o
  código passa a honrá-lo.
- **RF-17** — Só o que a escada **não** consumiu vai para a reserva. Somar o mês
  inteiro quando a sobra é exatamente zero creditava um mês que foi todo para a
  dívida, e antecipava o objetivo em um mês.
- **RF-18** — A escada do objetivo só enxerga dívida com taxa informada. A tela
  diz **quantas ficaram de fora e quanto elas somam**, porque o marco de dívidas
  estava sendo calculado sobre uma fração da dívida real, em silêncio.
- **RF-19** — Escada já limpa foi limpa no mês **zero**, não no mês um.
- **RF-20** — Quando não há data mas o resultado mensal **não** é negativo, a
  tela diz que a sobra não vence os juros da escada, em vez de afirmar "enquanto
  o resultado for negativo" com um "faltam R$ 0,00" ao lado.
- **RF-21** — A linha do tempo mostra a **reserva alvo** de cada ponto: ela se
  move quando a janela de seis meses desliza, e comparar projeções contra um alvo
  que mudou é comparar coisas diferentes.
- **RF-22** — A tela usa **meses** como unidade em todos os blocos. A tabela de
  cenários dizia "dias" e calculava `meses × 30`, que erra cerca de cinco dias
  por ano de projeção.
