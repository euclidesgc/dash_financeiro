# Plano — 032-o-campo-vazio-quer-dizer-a-mesma-coisa

**Trilha:** rápida · **Fonte aprovada:** `01-brief.md` · Uma fase.

## O terreno, medido em 08/09/2026

`app/cards/typed.py:25-27` — `parse` devolve `None` para toda string em branco,
antes de escolher o leitor. `app/cards/store.py` grava esse `None` como `NULL`.
Os campos afetados são os quatro do cartão: dia de fechamento, dia de vencimento,
taxa mensal e limite.

Na configuração da IA o caminho é outro e já está certo: campo vazio não toca a
chave guardada.

## Decisões

| Dúvida | Decisão |
|---|---|
| Qual dos dois significados vence | **"Não mexi".** É o que a tela da IA já faz, é o que o dono espera de um formulário que vem preenchido, e é o único cujo engano não perde dado |
| Como fica o gesto de apagar | Um botão por campo, com o nome do campo no rótulo. Não um campo de texto com uma palavra mágica |
| A tela de cartões avisa o quê | O texto passa a descrever o comportamento novo, e some o aviso de armadilha |

## Fase 1 — Vazio quer dizer "não mexi", e apagar é um gesto (api)

**Critérios de aceite**

- [ ] `comando` — RF-01, RF-05
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_cards.py -k vazio`
      sai `0` com ao menos um teste coletado. Os casos, para **cada um** dos
      quatro campos de cartão: com um valor gravado, um `POST` do mesmo campo em
      branco deixa o valor **inalterado**; e um `POST` com valor novo continua
      gravando o valor novo.
- [ ] `comando` — RF-02
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_cards.py -k apagar`
      sai `0` com ao menos um teste coletado: o gesto explícito apaga o campo que
      ele nomeia, e **não** apaga os outros três.
- [ ] `comportamental` — RF-03
      *Dado* um cartão com dia de fechamento e dia de vencimento gravados
      *Quando* o dono envia só o dia de fechamento, com valor novo
      *Então* a resposta nomeia o campo que mudou — não responde `Salvo.` sobre
      um formulário de quatro campos sem dizer qual deles se moveu
- [ ] `estrutural` — RF-04
      `rtk proxy grep -rn "em branco" app/templates` imprime as duas telas
      dizendo a mesma coisa sobre o campo vazio, e **nenhuma** delas diz que
      deixar em branco apaga.
- [ ] `comando` — RF-05
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` sai
      `0`, com **mais** testes que a base desta branch, sem `failed` nem `error`.

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — `parse` deixa de traduzir vazio para `None`**, e quem grava passa a
      receber a informação de que o campo não veio. Justificativa: hoje "veio
      vazio" e "quer apagar" chegam ao gravador como o mesmo valor, e nenhuma
      correção acima disso resolve.
- [ ] **1.2 — Gesto explícito de apagar, um por campo.** Justificativa: RF-02 —
      tirar a única forma de limpar sem pôr outra no lugar troca um defeito por
      outro.
- [ ] **1.3 — A resposta nomeia o que mudou.** Justificativa: `200 Salvo.` sobre
      um formulário de quatro campos é a resposta que escondeu este defeito.
- [ ] **1.4 — Reconciliar os textos das duas telas** (normas 7 e 8).
      Justificativa: o aviso documentava a armadilha; sem armadilha, ele mente.
