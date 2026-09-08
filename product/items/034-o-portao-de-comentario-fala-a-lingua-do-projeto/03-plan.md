# Plano — 034-o-portao-de-comentario-fala-a-lingua-do-projeto

**Trilha:** rápida · **Fonte aprovada:** `01-brief.md` · Duas fases, em sequência.

## Por que duas fases, nesta ordem

A fase 1 conserta o portão; a fase 2 varre o que sobrar. Invertido, a varredura
acrescentaria marca em português a 407 blocos e a fase seguinte mandaria trocar
todas — o trabalho seria feito duas vezes.

## Decisões

| Dúvida | Decisão |
|---|---|
| O portão aprende inglês, ou a norma 16 abre exceção? | **O portão aprende inglês.** A norma 16 é a regra permanente do projeto, e a lista de palavras do portão é uma lacuna de implementação, não uma decisão concorrente. O projeto já vinha convertendo comentário para inglês |
| As marcas em português saem? | Não nesta entrega. Ficam reconhecidas, e a fase 2 converte o que encontrar. Tirar as duas coisas ao mesmo tempo deixaria a árvore vermelha entre um commit e outro |
| Cabeçalho de arquivo | Reconhecido pelo lugar: bloco de comentário que **abre** o arquivo, antes de qualquer código. Não precisa de marca — ele já é, por posição, a documentação do arquivo |
| Varredura automática | **Não.** Apagar prosa por expressão regular apaga razão junto. A fase 2 julga bloco a bloco |

---

## Fase 1 — O portão reconhece o que o projeto escreve (api)

**Objetivo:** o portão para de acusar justificativa legítima. O recorte **não**
sai ainda: sair antes da varredura deixaria a árvore vermelha.

**Critérios de aceite**

- [ ] `comando` — RF-01
      `rtk proxy bash scripts/gates/__tests__/gate3.test.sh` sai `0`. Se esse
      arquivo não existir, ele é criado nesta fase. Ele prova, com árvore que o
      próprio teste escreve: comentário com marca em inglês (`Reason:`,
      `Decision:`, `Why:`, `Invariant:`, `Workaround:`, `Constraint:`) **passa**;
      comentário sem marca nenhuma **é acusado**; e comentário com marca em
      português continua passando.
- [ ] `comando` — RF-02
      `rtk proxy bash scripts/gates/__tests__/gate3.test.sh` — o mesmo comando,
      cobrindo também o cabeçalho: um bloco de comentário que **abre** o arquivo,
      antes de qualquer código, passa sem marca; e o **mesmo texto**, movido para
      o meio do arquivo ao lado de uma linha de código, é acusado. É a diferença
      entre documentar o arquivo e narrar a linha seguinte, e o teste tem de
      exercitar os dois lados dela para o critério valer.
- [ ] `comando` — RF-01, RF-02
      `rtk proxy bash -c 'find app financas ingestao tests scripts -name "*.py" -o -name "*.sh" | bash scripts/gates/gate3_no_comments.sh | wc -l'`
      imprime um número **menor que 1129**, que é o que a árvore acusa hoje. O
      número que sobrar é o escopo real da fase 2, e o veredicto o registra.
- [ ] `comando` — RF-05
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` sai
      `0` com o **mesmo** número de testes da base desta branch. Comentário não
      executa: mexer no portão não pode mover teste nenhum.
- [ ] `estrutural` — RF-04
      `.harness/gates.json` **continua** com `modo: diff` para este portão ao fim
      da fase 1, e o plano registra que ele sai na fase 2. Tirar o recorte antes
      da varredura deixa a árvore vermelha, e portão vermelho é portão que alguém
      desliga.

### Etapas

- [ ] **1.1 — Acrescentar as marcas em inglês** à alternância do portão.
      Justificativa: é a causa raiz — a norma 16 manda inglês e o portão só
      entendia português.
- [ ] **1.2 — Reconhecer o cabeçalho de arquivo pela posição.** Justificativa:
      174 dos 407 blocos são cabeçalho de script, e cabeçalho não tem outro lugar
      onde morar.
- [ ] **1.3 — Teste do próprio portão**, com árvore que o teste escreve.
      Justificativa: portão sem dente próprio se conserta às cegas.
- [ ] **1.4 — Medir e registrar quanto sobrou.** Justificativa: é o escopo da
      fase 2, e sem o número ela não tem fim declarado.

---

## Fase 2 — A árvore antiga se adapta, e o recorte sai (api)

**Objetivo:** todo comentário que sobrou ganha justificativa de verdade ou some, e
o portão passa a julgar a árvore inteira.

**Critérios de aceite**

- [ ] `comando` — RF-03
      `rtk proxy bash -c 'find app financas ingestao tests scripts -name "*.py" -o -name "*.sh" | bash scripts/gates/gate3_no_comments.sh | wc -l'`
      imprime `0`.
- [ ] `estrutural` — RF-04
      `.harness/gates.json` **não** traz mais `modo` nem `desde` para este portão.
      Controle positivo: o arquivo continua trazendo a configuração dos outros
      portões, inalterada — tirar o recorte não pode ser tirar o portão.
- [ ] `comando` — RF-04
      `rtk proxy bash scripts/gates/gates_runner.sh` sai `0` e a saída diz
      **árvore completa**, não um recorte.
- [ ] `comando` — RF-05
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` sai
      `0` com o **mesmo** número de testes que a fase 1 deixou, e
      `rtk proxy env DASH_ENV_FILE=/dev/null bash scripts/lint.sh` sai `0`.
- [ ] `comportamental` — RF-05
      *Dado* o painel servido com a base real copiada para diretório temporário e
      `DASH_TODAY=2026-09-05`
      *Quando* as telas de resumo, gastos, comprometido e dívidas são buscadas
      antes e depois desta fase
      *Então* o HTML devolvido é idêntico. Apagar comentário não pode mover
      número, e a única forma de provar isso é comparar a saída

**Critérios de integração** — só se verificam com as duas fases dentro.

- [ ] `comando` — RF-01, RF-03
      Depois de as duas fases entrarem, acrescentar um comentário novo **sem
      justificativa** a qualquer arquivo dos três pacotes faz
      `rtk proxy bash scripts/gates/gates_runner.sh` sair diferente de `0`. Desfeito
      o acréscimo, ele volta a `0`. É a prova de que o portão passou a julgar a
      árvore inteira, e não só a lembrança do recorte.

### Etapas

- [ ] **2.1 — Julgar bloco a bloco.** Comentário que diz um porquê ganha a marca;
      comentário que repete a linha seguinte, narra história ou decora seção é
      apagado. Justificativa: RF-03 — e o risco declarado do item é apagar a razão
      junto com a prosa, o que uma varredura automática faria.
- [ ] **2.2 — Converter para inglês as marcas em português** que a fase 1 deixou
      reconhecidas. Justificativa: norma 16, e a lista dupla existia só para a
      árvore não ficar vermelha no meio do caminho.
- [ ] **2.3 — Tirar o recorte de `.harness/gates.json`.** Justificativa: é o fim
      do prazo que o portão carregava.
