# Brief — 013-objetivo-cenario-vazio-e-ponto-espurio

- **RF-01** — Quando uma alavanca de cenário vale zero **porque a lista dela está
  vazia**, a tela nomeia a lista, diz que não é que ela não renda — é que ainda
  não há o que contar — e explica que por isso o cenário `base` devolve o mesmo
  número do `conservador`.
- **RF-02** — Leitura de `/objetivo` com data **recusada** não grava ponto na
  linha do tempo, e a tela diz que respondeu pela data de hoje e que **não
  gravou**.
- **RF-03** — Leitura com data aceita continua gravando, um ponto por cenário,
  chaveado por `(data, cenário)`.
