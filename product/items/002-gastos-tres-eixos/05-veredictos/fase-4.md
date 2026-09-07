# Veredicto — 002-gastos-tres-eixos, fase 4

VEREDICTO: APROVADO

> Segunda rodada, por um validador novo, depois de renomeadas as três capturas
> de lista e gerada a captura do estado de recusa. O julgamento anterior está em
> `fase-4-reprovada-1.md`.

Portões
  lint/analyze: NÃO EXECUTADO — o projeto não declara linter nem type checker.
                Não presumo que passaria.
  testes:       OK — `pytest -q` → `238 passed, 2 warnings in 38.88s`, exit 0
  gates:        OK — `✓ gates: limpos (árvore completa, 170 arquivo(s) considerados).`

Critérios de aceite
  [x] RF-39 — 80 linhas na tela contra `count(*) from category_rules` = 80, e a
      linha de `Eating out` com casamento, grupo, natureza, essencialidade e o
      alcance `128`.
  [x] RF-40 (criar) — `POST /regras` com corpo UTF-8 conferido por `xxd` →
      `26 lançamentos reclassificados.`, e a consulta de alcance devolve `26`.
  [x] RF-40 (editar) — `POST /regras/20/editar` → `128 lançamentos
      reclassificados.`, e `/gastos` traz `Comer fora / Eating out −R$ 4.360,13`
      em 60 lançamentos no bloco `variável × supérfluo`.
  [x] RF-07 — `natureza inválida: fixo`, HTTP 400, nada gravado.
  [x] RF-42 — `expressão inválida: [a-`, HTTP 400, contagem de regras igual
      antes e depois (81).
  [x] RF-43 — remoção → `128 lançamentos reclassificados.`, `rule_id is null`
      para os 128, e o resíduo de `/gastos` passa a `−R$ 4.360,13 em 60
      lançamentos`.
  [x] RF-41 — `Sem regra` no offset 14894 e a lista no 21791: o bloco vem antes.
      `Eating out −R$ 8.683,82` é o maior valor absoluto dos 12 e ocupa o topo.
  [x] RF-44 (comando) — nenhuma cor fora de `tokens.css`; controle confirma que
      os 11 arquivos foram varridos.
  [x] RF-44 (comportamental) — 93 elementos `.cifra`, todos com `tabular-nums`,
      todos casando `^−?R\$ [\d.]+,\d{2}$`, nenhum com hífen ASCII.
  [x] RF-45 (comportamental) — 375, 768 e 1440 sem transbordo.
  [x] RF-45 (estrutural) — as cinco capturas existem, acima de 1024 bytes; a de
      erro foi aberta e mostra a recusa `expressão inválida: [a-`.
  [x] RF-46 — `Tab` alcança casamento, grupo e botão na ordem, cada um com
      `outline: solid 2px rgb(91, 44, 141)`.
  [x] RF-47 — 1458 elementos varridos, nenhum com duração diferente de `0s`, e a
      lista mantém as 80 linhas.

Critérios de integração
  [x] portão local — `pytest -q` → `238 passed`, exit 0.
  [x] RF-13, RF-33 — sem reiniciar processo e sem nova ingestão, a edição da
      regra move o eixo: `importante` de `−R$ 49.085,08` para `−R$ 44.724,95`, e
      `supérfluo`, que não aparecia, passa a `−R$ 4.360,13` — a mesma cifra dos
      dois lados.
  [x] RF-16, RF-20 — `−R$ 103.772,33` nos cinco eixos, antes e depois da
      mudança de regra.

Instrumentos do implementer
  Apenas o critério que nomeia `pytest` como seu próprio objeto. Os demais foram
  medidos por `curl`, SQL direto, `grep` e Chromium real.

Apontamentos
  `app/__main__.py:8` — a porta 8000 é fixa, sem variável de ambiente. Critério
  que precise de dois bancos simultâneos esbarra nisso; o validador subiu em
  8010 e 8011 com a mesma app e os bancos que os critérios nomeiam.

  `app/routers/rules.py:261-269` — `_text` reinterpreta campo de formulário como
  latin-1 → UTF-8 para desfazer o mojibake do parser de urlencoded. Os dois
  caminhos foram testados e aceitos. Fica o registro de que o contorno
  transforma silenciosamente qualquer valor cujos bytes latin-1 sejam UTF-8
  válido, o que é indistinguível do mojibake que ele conserta.
