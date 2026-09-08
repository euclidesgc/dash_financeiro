# Plano — 018-tipagem-estrita-em-python

**Item:** `018` · **Trilha:** rápida · **Fonte aprovada:** `01-brief.md` ·
Duas fases, em sequência.

## Objetivo

`mypy --strict` roda sobre `app`, `financas` e `ingestao`, sai limpo, e o portão
de lint do projeto o inclui. A norma 35 deixa de cobrar o que nenhum comando
verifica.

## O terreno, medido em 08/09/2026

`mypy --strict`, apontado para o interpretador do projeto para que os tipos das
bibliotecas resolvessem: **202 erros em 36 arquivos, sobre 86 fontes**.

| Classe | Quantos |
|---|---|
| `type-arg` — genérico sem parâmetro | 86 |
| `no-untyped-call` — chamada a função sem anotação | 56 |
| `no-untyped-def` — função sem anotação | 34 |
| `no-any-return` | 11 |
| `arg-type`, `call-overload`, `var-annotated`, `assignment` | 15 |

Por pacote: **`app` 126, `ingestao` 79, `financas` 15**.

Sem apontar o interpretador, o número sobe para 279 — a diferença são 43 importes
não resolvidos e 32 decoradores sem tipo, artefato de medir num ambiente sem as
bibliotecas. **O número que vale é 202**, e é contra ele que as fases medem.

## Decisões

| Dúvida | Decisão |
|---|---|
| Onde a configuração mora | No arquivo de projeto, numa seção só, nomeando os três pacotes |
| O portão liga quando | Só no fim da fase 2, com os três limpos — portão que nasce vermelho é portão que se desliga |
| Silenciamento | Só com o código do erro **e** a razão na mesma linha |
| Testes entram no modo estrito | Não nesta entrega: o alvo da norma são os três pacotes da aplicação |

---

## Fase 1 — O verificador no ambiente, e `app` limpo (api)

**Objetivo da fase:** `mypy` é dependência declarada e travada, a configuração do
modo estrito existe, e `mypy --strict app` sai sem erro — sem que o portão de
lint ainda o cobre.

**Critérios de aceite**

- [ ] `estrutural` — RF-01, RF-02
      O arquivo de projeto declara `mypy` no grupo de desenvolvimento e traz uma
      seção de configuração do verificador que liga o modo estrito e nomeia os
      três pacotes. O arquivo de travamento de dependências contém a entrada de
      `mypy`. Controle positivo antes da ausência: `.venv/bin/mypy --version`
      imprime uma versão e sai com código `0` — hoje esse binário não existe.
- [ ] `comando` — RF-03
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/mypy --strict app` sai com
      código `0`, e a linha final diz `Success: no issues found in N source
      files` com **N maior que zero**. O número importa: o verificador sai com
      sucesso quando não encontra arquivo nenhum, e um comando que mede zero
      arquivo dá o mesmo verde de um comando que mediu tudo.
- [ ] `comando` — RF-05
      `rtk proxy grep -rn "type: ignore" app --include=*.py` não imprime nenhuma
      linha **sem** código de erro entre colchetes seguido de um comentário com a
      razão. O controle positivo: o mesmo comando sem o filtro imprime a lista
      completa dos silenciamentos, e ela pode ser vazia — se for, o critério é
      satisfeito por não haver silenciamento nenhum, e a saída diz isso.
- [ ] `comando` — RF-06
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` sai
      com código `0` e a linha de resumo traz **exatamente o mesmo número de
      testes** que a base desta branch trazia antes da fase, sem `failed` nem
      `error`. Anotar não acrescenta nem remove teste.
- [ ] `comportamental` — RF-06
      *Dado* o painel servido com a base real copiada para diretório temporário e
      `DASH_TODAY=2026-09-05`
      *Quando* as telas de resumo, gastos, comprometido e dívidas são buscadas
      *Então* cada uma responde `200`, e os totais de manchete são idênticos aos
      que a mesma leitura produzia antes desta fase — anotar não move dinheiro

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Declarar `mypy` no grupo de desenvolvimento e travar.**
      Justificativa: ferramenta que só existe na máquina de quem rodou não é
      portão.
- [ ] **1.2 — Configurar o modo estrito no arquivo de projeto**, numa seção só,
      nomeando os três pacotes. Justificativa: configuração em dois lugares é
      configuração que diverge.
- [ ] **1.3 — Zerar os 126 erros de `app`**, na ordem das classes: primeiro os
      genéricos sem parâmetro, depois as funções sem anotação — as chamadas sem
      tipo somem sozinhas quando as chamadas ganham tipo. Justificativa: atacar a
      classe mais numerosa primeiro faz a contagem cair sozinha.
- [ ] **1.4 — Conferir que nenhum número mudou**, comparando as quatro telas
      antes e depois. Justificativa: uma conversão posta para agradar o
      verificador é a forma mais comum de anotação mudar comportamento.

---

## Fase 2 — Os outros dois pacotes, e o portão (api)

**Objetivo da fase:** `mypy --strict` sai limpo sobre os três pacotes, e o portão
de lint do projeto e o fluxo de integração contínua o cobram.

**Critérios de aceite**

- [ ] `comando` — RF-03
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/mypy --strict app financas
      ingestao` sai com código `0`, e a linha final diz `Success: no issues found
      in N source files` com **N maior ou igual a 86** — o número de fontes que a
      medição do terreno encontrou. Menos que isso significa que o comando deixou
      de medir parte da árvore.
- [ ] `estrutural` — RF-04
      `scripts/lint.sh` contém a chamada ao verificador de tipos sobre os três
      pacotes, e continua contendo as duas chamadas ao formatador e ao lint que
      já tinha. As três afirmações juntas: um portão que troca uma verificação
      por outra não é portão a mais.
- [ ] `comando` — RF-04
      `rtk proxy bash scripts/lint.sh` sai com código `0`, e a saída traz tanto a
      linha do lint quanto a do verificador de tipos — as duas, porque um portão
      que roda só metade do que anuncia é a classe de defeito que esta corrida
      encontrou nos portões arquiteturais.
- [ ] `estrutural` — RF-04
      O fluxo de integração contínua chama `scripts/lint.sh`, ou chama o mesmo
      comando de verificação de tipos que ele chama. O controle positivo: o
      arquivo do fluxo existe e nomeia os três pacotes da aplicação.
- [ ] `comando` — RF-05
      `rtk proxy grep -rn "type: ignore" app financas ingestao --include=*.py`
      imprime a lista completa dos silenciamentos dos três pacotes — e **toda**
      linha dela traz o código do erro entre colchetes seguido de um comentário
      com a razão. A lista pode ser vazia, e aí o critério é satisfeito por não
      haver silenciamento nenhum; o comando imprimindo nada é a evidência disso,
      e o controle positivo é que ele sai `0` ou `1` do `grep`, nunca `2`, que é
      caminho inexistente.
- [ ] `comando` — RF-06
      A suíte inteira sai com código `0`, com o mesmo número de testes da base
      desta branch.

**Critérios de integração** — só se verificam com as duas fases dentro.

- [ ] `comando` — RF-03, RF-04
      Sobre a árvore com as duas fases, `rtk proxy bash scripts/lint.sh` sai `0`
      **e** `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/mypy --strict app
      financas ingestao` sai `0` com `N` maior ou igual a 86. As duas medições, na
      mesma árvore: a primeira prova que o portão cobra, a segunda prova que o
      que ele cobra está limpo.
- [ ] `comportamental` — RF-06
      *Dado* a base real copiada para diretório temporário, com a data de
      referência fixada
      *Quando* as oito telas do painel são buscadas com sessão
      *Então* todas respondem `200`, e nenhum total de manchete difere do que a
      mesma leitura produz na branch de integração antes deste item

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **2.1 — Zerar os 79 erros de `ingestao` e os 15 de `financas`.**
      Justificativa: são scripts de carga e de cálculo financeiro; o segundo
      alimenta número que vai para a tela, e é onde uma conversão errada custa
      mais.
- [ ] **2.2 — Acrescentar a verificação de tipos a `scripts/lint.sh`**, sem
      remover o que já existe. Justificativa: o portão cresce, não troca.
- [ ] **2.3 — Conferir o fluxo de integração contínua**, para que ele chame o
      mesmo comando. Justificativa: portão que só existe na máquina de quem roda
      à mão não é portão.
