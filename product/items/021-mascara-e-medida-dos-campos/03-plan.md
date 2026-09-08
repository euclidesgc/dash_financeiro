# Plano — 021-mascara-e-medida-dos-campos

**Item:** `021` · **Trilha:** rápida · **Fonte aprovada:** `01-brief.md` ·
Duas fases, em sequência.

## Objetivo

Todo campo de digitação declara o que aceita, o servidor cobra o mesmo teto, e a
largura do campo é proporcional ao que ele guarda. As três frestas que os
validadores desta corrida encontraram na gramática fecham.

## O terreno, medido em 08/09/2026

**37 campos de digitação** vivem nos templates — não 26. O brief contou antes de
os itens `024`, `027` e `028` entregarem cartões, propostas e configuração da IA,
e esses campos nasceram durante a corrida. **Nenhum dos 37** declara `maxlength`,
`pattern`, `minlength` ou `required`: a contagem continua zero.

Os tetos que o projeto já tem estão espalhados por três arquivos, cada um com um
nome diferente:

| Teto | Onde mora hoje | Quanto |
|---|---|---|
| Algarismos de dinheiro e de prazo | `app/settings/typed.py` · `MAX_DIGITS` | 12 |
| Nome de proposta | `app/offers/typed.py` · `NAME_MAX` | 60 |
| Pergunta ao consultor | `app/routers/advisor.py` · `MAX_QUESTION` | 500 |

Apelido de beneficiário, nome de cenário e expressão de regra não têm teto
nenhum. E os três tetos que existem estão escritos onde a tela não os alcança: o
template não importa módulo Python, então hoje não há como o atributo do campo e
a regra do servidor serem o mesmo número.

## Decisões

| Dúvida | Decisão |
|---|---|
| Onde o teto passa a morar | Num módulo só, `app/settings/limits.py`, exposto aos templates como global do Jinja. Os três donos atuais passam a importar de lá |
| Máscara ao digitar | Nenhuma, conforme o discovery. Sem arquivo JavaScript próprio |
| `required` em todo campo | Não. Só onde o servidor já recusa vazio — campo de filtro e taxa opcional não são obrigatórios, e marcar todos transformaria a declaração em ruído |
| Largura proporcional | Sai do próprio teto declarado, por `size` no campo mais **uma** regra de estilo que solta o `width: 100%` de quem declara teto. Ver D-001 |
| Teto de taxa do financiamento | Próprio, por tipo de dívida; o leitor genérico mantém os 100% ao mês |

### D-001 — a largura exige uma regra de estilo, e o brief a proibia

O brief põe "nenhuma regra nova de folha de estilo" no não-escopo e manda a
largura sair dos tokens de medida do item `017`. A medição mostra que **não
existe token de largura de campo**: `017` entregou tokens de cor, texto, espaço e
uma medida de linha de leitura, e `.field-input` é `width: 100%`. Com essa regra
em pé, `size` no campo não tem efeito nenhum — a largura continua a da coluna.

Divergência **normal**, não de contrato: a escolha é técnica e segue na
recomendação. **Uma** regra nova, que solta a largura de quem declarou teto:

```css
.field-input[maxlength] { width: auto; max-width: 100%; }
```

Ela é a melhor forma disponível porque faz a largura **derivar do teto** em vez de
repetir o teto: quem declara quantos caracteres aceita já disse quão largo é. Não
há número novo na folha de estilo, e a alternativa — uma escala de classes de
largura — criaria a quarta escala de medida do projeto, exatamente o que o
discovery recusou.

---

## Fase 1 — A casa única dos tetos, e as três frestas fechadas (api)

**Objetivo da fase:** o servidor passa a cobrar teto onde não cobrava, recusa o
que hoje aceita por engano, e todo teto do projeto está escrito num lugar só.
Nenhuma tela muda nesta fase.

**Critérios de aceite**

- [ ] `estrutural` — RF-03
      Existe `app/settings/limits.py`, e ele é o único lugar da árvore onde cada
      teto está escrito como número. Controle positivo:
      `rtk proxy grep -rn "= 500\|= 60\|= 12" app --include='*.py'` casa dentro
      de `app/settings/limits.py` e **não** casa em `app/offers/typed.py`,
      `app/routers/advisor.py` nem `app/settings/typed.py` — esses três passam a
      importar. Antes desta fase o mesmo comando casa nos três.
- [ ] `comando` — RF-05
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_typed_limits.py -k digito`
      sai com código `0` e coleta ao menos um teste — a linha de resumo não diz
      `no tests ran`. Os casos: `parse_money` recusa `١٢٣` (dígito
      arábico-índico) e `１２３` (dígito de largura cheia), levantando
      `InvalidValueError`; e o controle positivo, `parse_money("123")` continua
      devolvendo `12300`. Hoje os dois primeiros passam e gravam o número certo —
      o defeito é a aceitação, não a conta.

- [ ] `comando` — RF-06
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_typed_limits.py -k financiamento`
      sai `0` com ao menos um teste coletado — a linha de resumo não diz
      `no tests ran`. Os casos: taxa de 100% ao mês é **recusada** num
      financiamento imobiliário, a mesma taxa continua **aceita** pelo leitor
      genérico, e o teto do financiamento de veículo é o do seu próprio tipo.
- [ ] `comando` — RF-07
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_typed_limits.py -k nome`
      sai `0` com ao menos um teste coletado. Os casos: nome com byte de
      substituição (`�`) ou caractere de controle é recusado com mensagem em
      português; nome com acento e cedilha — `Consignação Itaú` — continua aceito,
      porque o filtro é contra byte ilegível, não contra português.
- [ ] `comando` — RF-02
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_typed_limits.py -k teto`
      sai `0` com ao menos um teste coletado, cobrindo os quatro campos de texto:
      apelido de beneficiário, nome de cenário, expressão de regra e nome de
      proposta. Cada um recusa uma entrada de um caractere acima do seu teto e
      aceita uma exatamente no teto.
- [ ] `comando` — RF-08
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` sai
      com código `0` e traz **mais** testes que a base desta branch trazia antes
      da fase, sem `failed` nem `error`. Nenhum teste existente muda de veredicto:
      esta fase acrescenta recusa onde não havia, e o que já passava continua
      passando.
- [ ] `comportamental` — RF-08
      *Dado* os leitores desta fase em pé
      *Quando* um prazo de `420` meses e um valor de doze algarismos
      (`999.999.999,99`) são lidos
      *Então* ambos são aceitos e devolvem o mesmo inteiro de antes — o risco
      central deste item é passar a recusar o que era legítimo, e são estes os
      dois valores reais do dono que a medição nomeou

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Criar `app/settings/limits.py`** com os tetos nomeados, e fazer
      `app/settings/typed.py`, `app/offers/typed.py` e `app/routers/advisor.py`
      importarem de lá. Justificativa: RF-03 é a única forma de o campo e o
      servidor não divergirem, e ele começa por haver um número só.
- [ ] **1.2 — Trocar a classe de dígito da gramática por dígito ASCII
      explícito.** `\d` na expressão regular do Python casa todo decimal Unicode;
      `[0-9]`, ou `re.ASCII`, não. Justificativa: o dígito arábico-índico entra
      hoje no campo que decide venda de carro, e sai como número certo — o
      defeito é a aceitação, não a conta.
- [ ] **1.3 — Dar teto de taxa próprio ao financiamento**, por tipo de dívida,
      mantendo os 100% ao mês do leitor genérico. Justificativa: um teto só para
      cheque especial e imóvel deixa passar absurdo em um dos dois.
- [ ] **1.4 — Recusar nome com byte ilegível** onde o nome é chave de gravação.
      `app/offers/store.py` grava com `ON CONFLICT (name) DO UPDATE`: um nome que
      o dono não consegue redigitar é uma linha que ele não consegue
      sobrescrever. Justificativa: o defeito não é estético, é uma linha presa.
- [ ] **1.5 — Dar teto aos quatro campos de texto** que hoje não têm, com o
      número vindo de 1.1. Justificativa: texto sem teto é o caminho mais curto
      para um `INSERT` que não cabe.
- [ ] **1.6 — Escrever `tests/test_typed_limits.py`** cobrindo os casos dos
      critérios, incluindo os dois controles positivos de RF-08. Justificativa:
      recusa nova sem teste do que continua aceito é como se quebra o que
      funcionava.

---

## Fase 2 — Os campos declaram, e cabem no que declaram (api)

**Objetivo da fase:** os 37 campos declaram teto e modo de teclado, os
obrigatórios se declaram obrigatórios, a largura é proporcional, e um script
mede isso sem depender de alguém contar à mão.

**Antes de tocar em template, carregue a skill de desenho de tela:**
`/home/euclidesgc/.claude/skills/frontend-design/SKILL.md` (norma 27).

**Critérios de aceite**

- [ ] `comando` — RF-01, RF-02
      `rtk proxy python3 scripts/campos-digitaveis.py` sai com código `0` e a
      última linha diz `campos digitáveis: N; sem declaração completa: 0`, com
      **N maior ou igual a 37**. O script varre `app/templates/**/*.html`, ignora
      `type="submit"` e `type="hidden"`, e acusa todo campo restante que não
      declare `maxlength`; campo de dinheiro, taxa ou prazo tem de declarar
      também `inputmode`. Hoje o mesmo comando sai diferente de `0` e acusa 37.
- [ ] `estrutural` — RF-03
      Nenhum template escreve um teto como número literal: os valores de
      `maxlength` vêm da global do Jinja que expõe `app/settings/limits.py`.
      Controle positivo: `rtk proxy grep -rn 'maxlength="[0-9]' app/templates`
      não imprime linha nenhuma, e
      `rtk proxy grep -rn 'maxlength="{{' app/templates` imprime uma linha por
      campo declarado.
- [ ] `estrutural` — RF-04
      A folha de estilo ganha exatamente **uma** regra nova, a de D-001, e ela
      não traz número de largura próprio. Controle positivo:
      `rtk proxy git diff develop -- app/static/css/` mostra um único seletor
      acrescentado, e ele casa `.field-input[maxlength]`.
- [ ] `comando` — RF-08
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` sai
      com código `0`, sem `failed` nem `error`.
- [ ] `comportamental` — RF-04, RF-08
      *Dado* o painel servido com a base real copiada para diretório temporário e
      `DASH_TODAY=2026-09-05`
      *Quando* as telas de configuração, dívidas, simulador, gastos, regras e
      consultor são capturadas em claro e escuro
      *Então* cada uma responde `200`; o campo de aporte e a pergunta livre ao
      consultor **não** têm mais a mesma largura; e nenhum campo transborda a
      coluna nem quebra o alinhamento da grade em 375, 768 e 1440
- [ ] `comportamental` — RF-01, RF-08
      *Dado* o mesmo painel servido
      *Quando* um valor de doze algarismos é enviado ao campo de aporte e um
      prazo de `420` meses ao campo de prazo do financiamento
      *Então* os dois são aceitos e gravados — o teto declarado no campo não é
      mais apertado que o do servidor

**Critérios de integração** — só se verificam com as duas fases dentro.

- [ ] `comando` — RF-03
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_typed_limits.py -k coerencia`
      sai `0` com ao menos um teste coletado. O teste lê os `maxlength` dos
      templates renderizados e afirma que cada um é **igual** ao teto que o leitor
      do servidor cobra para aquele campo. É o que RF-03 pede e o que o risco do
      brief nomeia: teto do cliente e do servidor divergirem.

### Etapas

- [ ] **2.1 — Expor os tetos aos templates** como global do Jinja em
      `app/main.py`. Justificativa: sem isso o template só pode repetir o número,
      e repetir é como ele diverge.
- [ ] **2.2 — Declarar teto, modo de teclado e obrigatoriedade nos 37 campos.**
      Justificativa: é o item.
- [ ] **2.3 — Acrescentar a regra de D-001 e o `size` proporcional** ao teto.
      Justificativa: a largura passa a derivar do teto em vez de repeti-lo.
- [ ] **2.4 — Escrever `scripts/campos-digitaveis.py`.** Justificativa: um item
      de varredura que não deixa um medidor atrás de si volta a zerar na próxima
      tela que alguém escrever — foi assim que os 37 apareceram depois dos 26.
- [ ] **2.5 — Capturar as seis telas de uma vez** com
      `bash scripts/capturas-em-lote.sh`, em claro e escuro. Justificativa: uma
      subida e um login; o limitador de tentativas fecha a porta antes da sexta
      captura se cada uma subir o seu próprio servidor.
