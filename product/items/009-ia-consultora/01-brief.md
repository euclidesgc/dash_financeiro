# Brief — 009-ia-consultora

- **RF-01** — `GET /consultor` serve a tela, atrás da sessão, e o Resumo leva até
  ela.
- **RF-02** — A tela faz **uma** pergunta por vez, a do fato ausente ou vencido
  que mais move a projeção, e diz **qual número a resposta muda** e em que tela
  informá-lo.
- **RF-03** — Fato informado e dentro da validade **não é perguntado**.
- **RF-04** — Fato vencido **volta** a ser perguntado.
- **RF-05** — "Agora não" faz a pergunta sumir, e ela não volta enquanto o fato
  não vencer.
- **RF-06** — A pergunta da taxa dos cartões só existe enquanto houver dívida sem
  taxa informada.
- **RF-07** — Sem nenhum fato pendente, a tela diz que não há o que perguntar.
- **RF-08** — A instrução de sistema do modelo proíbe cálculo com todas as
  letras, e manda copiar cada número do contexto dígito a dígito.
- **RF-09** — O contexto entregue ao modelo traz posição consolidada, caixa,
  cartão, comprometido, resultado mensal, reserva alvo, tempo até o objetivo e o
  pior ponto dos 45 dias — todos do motor determinístico.
- **RF-10** — A tela **mostra o contexto** que vai para o modelo.
- **RF-11** — Nenhum número da tela passa pelo modelo: o instantâneo é calculado
  sem chamada de rede nenhuma.
- **RF-12** — Sem `GEMINI_API_KEY`, a tela diz que a leitura está indisponível e
  que os números não dependem dela — e continua mostrando os números.
- **RF-13** — Erro de rede, resposta vazia ou JSON inesperado degradam do mesmo
  jeito, com `200`, nunca com `500`.
- **RF-14** — Pergunta vazia ou acima de 500 caracteres é recusada com `400`.
- **RF-15** — A tela obedece à linguagem visual; nenhum número medido aparece
  como literal no código.
