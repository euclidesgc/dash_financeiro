## 1. O que foi implementado

**Item:** `002-gastos-tres-eixos` · **Fase:** `4 — Tela de Regras`

A classificação deixa de ser código. A rota `/regras` — que duas telas já
apontavam e respondia 404 — lista as 80 regras com o alcance e o gasto de cada
uma, e permite criar, editar e remover. Toda operação **reclassifica a base na
mesma transação** e diz quantos lançamentos mudaram. Valor fora do vocabulário e
expressão inválida são recusados com a mensagem que nomeia o valor, sem gravar
nada. Antes da lista vem o que está **sem regra**, do maior gasto para o menor,
porque é ali que mora a regra que falta escrever.

A tela fecha um defeito silencioso que um validador tinha medido na fase 1: a
expressão é casada contra a descrição normalizada — minúscula, sem acento, sem
dígito —, então quem digitasse `Uber` gravava uma regra que não fazia nada, sem
erro e sem log. Agora o formulário diz de antemão contra o que a expressão será
casada, com exemplos tirados da própria base, e uma regra que alcança zero diz
isso na hora e sugere o que verificar.

Branch: `002-gastos-tres-eixos/fase-4-tela-regras` · commits `cb4b498` e `473d98e`.
Capturas: `regras-lista-375/768/1440.png`, `regras-erro-1440.png`,
`regras-dark-1440.png`.

**Reprovou na primeira rodada** por quatro capturas — três com nome diferente do
exigido e a do estado de recusa faltando. Aprovada na segunda, por validador
novo. Os dois julgamentos estão em `05-veredictos/`.

---

## 2. Critérios atendidos

Os dezesseis critérios foram executados por validador cego, com `curl`, SQL
direto e Chromium real. O veredicto integral está em
[`05-veredictos/fase-4.md`](../05-veredictos/fase-4.md).

- [x] `[comportamental]` RF-39 — 80 linhas na tela contra 80 no banco, com a
      linha de `Eating out` completa e o alcance `128`.
- [x] `[comportamental]` RF-40 — criar regra de descrição devolve `26
      lançamentos reclassificados`; editar `Eating out` para `supérfluo` devolve
      `128`, e a lista de corte de `/gastos` passa a mostrar `−R$ 4.360,13`.
- [x] `[comportamental]` RF-07 e RF-42 — `natureza inválida: fixo` e `expressão
      inválida: [a-`, ambas HTTP 400, ambas sem gravar nada.
- [x] `[comportamental]` RF-43 — remover devolve os 128 lançamentos ao resíduo, e
      `/gastos` passa a mostrar `−R$ 4.360,13 em 60 lançamentos` em `Sem regra`.
- [x] `[comportamental]` RF-41 — o bloco do que está sem regra vem **antes** da
      lista (offset 14894 contra 21791) e traz o maior valor absoluto no topo.
- [x] `[comando]` e `[comportamental]` RF-44 — nenhuma cor fora de `tokens.css`;
      93 cifras, todas tabulares, todas com o sinal `U+2212`.
- [x] `[comportamental]` e `[estrutural]` RF-45 — sem rolagem horizontal nas três
      larguras; as cinco capturas existem, e a de erro mostra a recusa.
- [x] `[comportamental]` RF-46 e RF-47 — foco visível de 2 px em cada parada do
      `Tab`; sob `prefers-reduced-motion`, zero dos 1458 elementos se move.
- [x] `[comando]` portão local — `pytest -q` → `238 passed`.
- [x] `[comportamental]` RF-13, RF-33 — **sem reiniciar processo e sem nova
      ingestão**, editar a regra move o eixo: `importante` cai `−R$ 4.360,13` e
      `supérfluo`, que não existia, passa a valer exatamente o mesmo.
- [x] `[comportamental]` RF-16, RF-20 — `−R$ 103.772,33` nos cinco eixos, antes
      e depois da mudança de regra.

---

## 3. Como testar à mão

1. Prepare a base e o usuário, suba o app e faça login.
2. Abra `http://127.0.0.1:8000/regras`.
3. **Esperado:** as 80 regras, com alcance e gasto, e o bloco `Sem regra` acima.
4. Edite a regra de `Eating out` para essencialidade `supérfluo`.
5. **Esperado:** `128 lançamentos reclassificados.`
6. Volte a `/gastos`.
7. **Esperado:** a lista de corte deixou de estar vazia e traz `Comer fora
   −R$ 4.360,13` em 60 lançamentos.

---

## 4. Divergências

nenhuma

Dois critérios foram corrigidos antes da validação, como erro material: o
`RF-07` mandava `group_id=9999` e esperava a mensagem de natureza, mas a
validação checa grupo primeiro; e o `RF-40` media o total do grupo `Transporte`
mudando, que não muda — os lançamentos de `uber` já estavam nele pela regra de
categoria que a expressão passa a vencer. Ambos passaram a medir o alcance.

---

## 5. Raio de impacto

> **Conjunto de candidatos, não verdade.** Precisão medida: **0,578**.

**Confirmados** (lidos):

- `app/routers/rules.py` — a rota `/regras` e as três operações. `_text`
  reinterpreta campo de formulário como latin-1 → UTF-8 para desfazer o mojibake
  do parser de urlencoded; os dois caminhos foram testados.
- `app/templates/regras.html` e `fragments/regras_lista.html` — seguem o padrão
  de fragmento que a tela de Gastos estabeleceu.
- `app/taxonomy/rules.py` — consumido, não alterado: é ele que devolve quantos
  lançamentos cada operação reclassificou, e é esse número que a tela mostra.

**Candidatos** (não conferidos):

- `app/templates/home.html` — ganhou o link para `/regras`.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

- **A porta 8000 é fixa em `app/__main__.py`**, sem variável de ambiente. Um
  critério que precise de dois bancos simultâneos esbarra nisso — o validador
  precisou subir em 8010 e 8011. **Não virou item de roadmap**: é uma linha, e o
  item `006` (sync) é o primeiro que vai querer subir dois processos.
- **`_text` conserta mojibake de forma indistinguível de dado legítimo.** Ele
  transforma qualquer valor cujos bytes latin-1 sejam UTF-8 válido. Hoje é
  correto para todo caminho testado; registrado porque o dia em que estiver
  errado será difícil de ver.
