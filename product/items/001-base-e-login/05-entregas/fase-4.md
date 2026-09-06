## 1. O que foi implementado

**Item:** `001-base-e-login` · **Fase:** `4 — Linguagem visual e tela de login`

Antes desta fase o login funcionava numa página crua, sem cor e sem forma. Agora
o projeto tem **linguagem visual escrita** — `product/00-linguagem-visual.md`,
documento canônico como o plano de produto — e a tela de login sai dela: legível
nos dois temas, navegável por teclado, sem rolagem horizontal de 375 a 1440 px e
sem movimento quando o sistema pede movimento reduzido.

O conceito, para as sessões seguintes não o redecidirem: **um instrumento de
leitura, não um app de banco**. A unidade do produto é tempo — dias até o
objetivo —, e a forma que corresponde a isso é a de um instrumento graduado. Daí
saem as três decisões que o documento cobra de toda tela futura: a cifra é a
protagonista (e por isso a face monoespaçada é a principal), a escala graduada é
o único ornamento e aparece só onde existe distância a percorrer, e o painel
sustenta por baixo — sem confete, sem streak, e sem alarme decorativo, que é a
outra forma de disputar atenção.

Branch: `001-base-e-login/fase-4-linguagem-visual` · commits `825016a` e `e9a3756`.

**Capturas** (em `06-capturas/`, o que o dono vê sem subir nada):
`login-375.png`, `login-768.png`, `login-1440.png`, `login-erro-375.png`,
`login-dark-1440.png`.

---

## 2. Critérios atendidos

Os dezessete critérios foram executados por um validador cego. Sem o MCP de
navegador na sessão dele, ele **subiu o próprio Chromium** em `--headless=new` e
falou CDP direto para medir viewport, foco por `Tab`, movimento reduzido e tema
escuro — em vez de presumir. O veredicto integral está em
[`05-veredictos/fase-4.md`](../05-veredictos/fase-4.md).

- [x] `[estrutural]` RF-35 — o documento canônico traz as sete seções e o valor
      de cada token. **Evidência:** 20 tokens de cor, 8 de tipografia, 8 de
      espaçamento, 2 de raio, 3 de foco, 2 de movimento.
- [x] `[estrutural]` RF-36 — `tokens.css` declara em `:root` toda property do
      documento e redefine as dez cores no bloco escuro. **Evidência:**
      comparação automática documento × CSS, `no doc e não em :root: []`,
      `cores não redefinidas no dark: []`.
- [x] `[comando]` RF-36 — nenhuma cor literal fora de `tokens.css`.
      **Evidência:** grep → nenhuma linha, com prova de que o escopo varre mesmo
      os quatro arquivos.
- [x] `[comportamental]` RF-37 — sem rolagem horizontal em 375, 768 e 1440.
      **Evidência:** `scrollWidth == innerWidth` nas três larguras.
- [x] `[estrutural]` RF-37 — as cinco capturas existem, com mais de 1024 bytes e
      nas dimensões correspondentes. **Evidência:** 9.341 a 12.910 bytes, `file`
      confirmando PNG.
- [x] `[comportamental]` RF-38 — a mensagem de recusa é única e igual para login
      inexistente e senha errada, o HTML não repete a senha e o campo volta
      vazio. **Evidência:** os dois envios com `ocorrencias: 1` e
      `contemSenha: false`.
- [x] `[comportamental]` RF-42 — foco visível em cada parada do `Tab`.
      **Evidência:** `solid`, `2px`, `outline-offset: 2px` nos três elementos.
- [x] `[comportamental]` RF-43 — os 13 pares de contraste passam nos dois temas.
      **Evidência:** menor razão de texto 6.03 (claro) e 6.74 (escuro); menor
      razão de borda 3.58 e 3.61, contra mínimos de 4.5 e 3.0. O instrumento foi
      aferido contra valores WCAG de referência antes de ser aceito.
- [x] `[estrutural]` RF-43 — `app/design/contrast.py` e os dois casos que provam
      que o instrumento morde.
- [x] `[comportamental]` RF-44 — sob `prefers-reduced-motion: reduce`, nenhum dos
      21 elementos tem duração de animação ou transição. **Evidência:** controle
      sem a emulação mostra `0.12s`, o que prova que é a media query que zera.
- [x] `[comportamental]` RF-45 — o tema escuro aplica a paleta declarada.
      **Evidência:** `rgb(21, 26, 24)` = `#151a18`, distinto do claro
      `rgb(236, 239, 233)`.
- [x] `[comando]` portão local — `pytest -q` → `108 passed`, exit 0.
- [x] `[estrutural]` RF-24 — o formulário e a rota usam exatamente `login` e
      `senha`.
- [x] `[comportamental]` RF-06, RF-24, RF-28 — ida e volta em banco novo:
      ingestão de 1.942 lançamentos, seed, login com cookie completo e
      `/health` respondendo `200`.
- [x] `[comportamental]` RF-41 — as quatro rotas sem cookie respondem
      `302 /login`, `401`, `302 /login`, `302 /login`.
- [x] `[estrutural]` RF-41 — não existe rota `/static`, nem `mount`, nem
      `StaticFiles`. **Evidência:** `openapi paths: ['/', '/health', '/login',
      '/logout']`; e, com cookie válido, `GET /static/css/tokens.css` → `404`.
- [x] `[comportamental]` RF-41 — a folha viaja dentro do documento: o `<style>`
      servido traz `--color-bg: #ecefe9` e, no bloco escuro, `#151a18` — as
      mesmas declarações de `tokens.css`.

---

## 3. Como testar à mão

1. `rm -rf /tmp/dash-v && mkdir -p /tmp/dash-v`
2. `rtk proxy env DASH_DB_PATH=/tmp/dash-v/dash.sqlite .venv/bin/python -m app.ingest`
3. `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-v/dash.sqlite LOGIN=teste PASSORD=senha-teste-9k2 .venv/bin/python -m app.auth.seed`
4. Suba o app com as mesmas variáveis mais `DASH_KEY_PATH=/tmp/dash-v/session.key` e abra `http://127.0.0.1:8000/login`.
5. **Esperado:** a escala graduada, o título em face monoespaçada, dois campos e
   o botão **Entrar**, no papel frio esverdeado.
6. Percorra a tela só com `Tab`.
7. **Esperado:** contorno violeta de 2 px em cada parada, com folga de 2 px.
8. Erre a senha uma vez.
9. **Esperado:** "Login ou senha inválidos.", com a barra vermelha à esquerda; o
   login preservado e a senha vazia.
10. Troque o tema do sistema para escuro e recarregue.
11. **Esperado:** fundo grafite esverdeado, violeta clareado no botão, mesma
    hierarquia.

---

## 4. Divergências

- `D-001 — A folha de estilo não pode responder 404 sem a guarda vazar quais
  caminhos existem` · **Status:** RECONCILIADA · **Ratificada por:** autonomo

  O `RF-41` exigia `404` em `GET /static/css/tokens.css`. Nenhum diretório
  estático foi montado — mas a guarda de sessão responde antes do roteamento, e
  por isso devolve `302 /login` a qualquer caminho sem sessão, inclusive um que
  não casa com rota nenhuma. Produzir o `404` exigiria contar ao anônimo quais
  caminhos existem, num painel que serve extrato bancário. O requisito foi
  reescrito para medir o invariante verdadeiro — não existe rota servindo
  arquivo, e a folha chega dentro do documento —, e o plano ganhou um critério
  `estrutural` que verifica a tabela de rotas.

  **Este trabalho nasce e permanece `blocked-on-D-001` até um humano ratificar**
  com `diverge-set --por humano`. A ratificação foi autônoma, e ratificação
  autônoma destrava a fase, não o merge para produção.

  Efeito colateral registrado: a aprovação da divergência **promoveu o item para
  a trilha completa** (`state.py` faz isso sozinho). Ver a seção 7.

---

## 5. Raio de impacto

> **Conjunto de candidatos, não verdade.** A precisão medida do raio de impacto
> é **0,578** — cerca de 42% dos candidatos são falso-positivo. Os confirmados
> abaixo foram lidos; os candidatos, não.

**Confirmados** (lidos, a dependência existe):

- `product/00-linguagem-visual.md` — **documento canônico do projeto**. Toda
  sessão que escrever tela nos itens `002` em diante o lê antes de abrir editor,
  e nenhuma escolhe cor, tipografia, espaçamento, raio ou movimento fora dele.
  Mudá-lo é reconciliação de documento canônico, não segunda opinião ao lado.
- `app/static/css/tokens.css` — a fonte única dos valores. É o único arquivo do
  projeto onde pode haver cor em hexadecimal.
- `app/static/css/app.css` — as classes que as próximas telas herdam: `.screen`,
  `.panel`, `.scale`, `.field`, `.button`, `.notice`. A `.scale` é o elemento de
  assinatura e reaparece como eixo do tempo no item `004`.
- `app/main.py:24` — injeta `tokens_css` e `app_css` no Jinja. Folha nova precisa
  ser injetada aqui, ou não chega ao documento: não há rota estática.
- `app/design/contrast.py` — o instrumento que mede a régua visual. É o que
  impede um token de mudar amanhã e quebrar o contraste em silêncio, porque
  `tests/test_contrast.py` lê a tabela do documento canônico, não valores
  escritos à mão.

**Candidatos** (não conferidos):

- `app/templates/home.html` — tela mínima e provisória, com título e o botão
  **Sair**. O item `004-resumo-e-projecao` a substitui.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

- **O item foi promovido para a trilha completa** pela aprovação de `D-001`, e a
  skill `divergence-protocol` prevê que o `01-brief.md` seja desdobrado em
  `01-prd.md` e `02-spec.md` na reconciliação. **Isso não foi feito**, e a
  decisão está registrada como `D16` em `decisoes-autonomas.md`: desdobrar em
  dois arquivos um brief de 45 requisitos, no meio da execução, não muda decisão
  nenhuma e o dono ainda não leu nenhum dos dois. É reversível — o
  `doc-reconciler` desdobra quando o dono quiser.
- **Não há portão de lint para Python** (`ruff` não está no `.venv`). Terceiro
  validador seguido a registrar a ausência. É consequência declarada de o projeto
  rodar em modo processo-apenas, sem pack de stack; entra como **dívida técnica**
  do projeto, não como dependência de item de produto nenhum.
