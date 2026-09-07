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

## O que o veredicto obrigou a escrever

- **RF-04** — **Ausência de `?data=` não é data recusada.** É o caminho normal de
  entrada, pelos dois links que o próprio produto carrega. Tratá-la como recusa
  fez a linha do tempo **parar de crescer** pela navegação normal, e imprimiu "a
  data pedida não foi aceita" sobre uma requisição que não pediu data nenhuma. Foi
  regressão introduzida por `RF-02`.
- **RF-05** — O aviso da alavanca vazia concorda em número com a lista que ele
  mostra, e só afirma que `base` devolve o mesmo número do `conservador` quando as
  **duas** listas estão vazias — porque `base` soma as duas alavancas e
  `conservador` não soma nenhuma. Com uma só vazia, a frase contradizia os dois
  números diferentes na tabela ao lado.
