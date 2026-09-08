# Plano — 029-o-guarda-reconhece-uma-forma-so-de-perguntar-as-horas

**Item:** `029` · **Trilha:** rápida · **Fonte aprovada:** `01-brief.md` ·
Uma fase.

## Objetivo

O guarda de rota reconhece a chamada ao relógio pela **árvore sintática** do
módulo, e não por busca de texto. Ele passa a alcançar `datetime.today()`,
`datetime.now()`, `datetime.now().date()` e qualquer uma delas sob apelido de
import — e deixa de acusar a cadeia quando ela aparece em comentário ou em
literal de texto, que é o falso positivo que a busca de texto traria junto.

## O terreno

`tests/test_route_guard.py` traz, desde o item `020`, uma enumeração recursiva
(`_sources`) chaveada por caminho relativo, e uma acusação (`_accused`) que é uma
busca pela cadeia `date.today()` no texto do módulo. A enumeração está certa e
não muda; o que muda é a acusação.

O módulo `ast` da biblioteca padrão resolve o problema inteiro: `import ast`,
`ast.parse`, e uma visita que (1) coleta o que cada nome importado de `datetime`
aponta e (2) acusa toda chamada cujo alvo resolva a `date.today`,
`datetime.today` ou `datetime.now`.

## Decisões

| Dúvida | Decisão |
|---|---|
| Texto ou árvore? | **Árvore.** É o que permite seguir apelido e o que exclui comentário e literal. |
| Módulo com sintaxe inválida? | Acusa, nomeando o erro: um módulo de rota que não compila é problema maior que o relógio. |
| `datetime.now()` sem `.date()`? | Acusa. Quem pergunta as horas ao relógio numa rota erra igual. |

---

## Fase 1 — O guarda reconhece a chamada, não a cadeia (api)

**Objetivo da fase:** a acusação do guarda de rota é feita sobre a árvore
sintática do módulo, alcança apelido de import, e ignora comentário e literal.

**Critérios de aceite**

- [ ] `estrutural` — RF-01, RF-03
      `tests/test_route_guard.py` importa `ast` e define uma função de acusação
      que recebe o mapeamento de módulos e devolve a lista de acusados. O arquivo
      **contém** `ast.parse` e `ast.walk` (ou `ast.NodeVisitor`), e **não**
      contém a expressão `"date.today()" in`, que é a busca de texto que ele
      substitui. O controle positivo vem antes da ausência: se a função de
      acusação não existisse, a primeira cláusula já reprovaria.
- [ ] `comportamental` — RF-01
      *Dado* um diretório temporário com quatro módulos escritos pelo próprio
      teste, cada um com uma das formas: `from datetime import date` e
      `date.today()`; `from datetime import datetime` e `datetime.today()`;
      `from datetime import datetime` e `datetime.now().date()`;
      `from datetime import datetime` e `datetime.now()`
      *Quando* a enumeração e a acusação do guarda são aplicadas a esse diretório
      *Então* a lista de acusados contém os quatro nomes de arquivo, e tem
      exatamente quatro entradas
- [ ] `comportamental` — RF-02
      *Dado* um diretório temporário com dois módulos: um com
      `from datetime import date as d` e uma chamada a `d.today()`, e outro com
      `import datetime as dt` e uma chamada a `dt.datetime.now()`
      *Quando* a acusação é aplicada
      *Então* os dois são acusados. Com busca de texto, nenhum dos dois é — e é
      essa diferença que o item existe para fechar
- [ ] `comportamental` — RF-03
      *Dado* um diretório temporário com um módulo que consome o leitor único da
      data de referência e traz, além disso, a cadeia `date.today()` dentro de um
      comentário e dentro de um literal de texto
      *Quando* a acusação é aplicada
      *Então* a lista de acusados é vazia, **e** a chave desse módulo está
      presente no mapeamento — as duas afirmações juntas, porque só a segunda
      distingue "não acusou" de "não enxergou"
- [ ] `comportamental` — RF-04
      *Dado* um diretório temporário com `cards/screen.py` e
      `cards/detail/screen.py`, ambos chamando o relógio, e um `__pycache__` com
      cópia de um deles
      *Quando* a enumeração e a acusação são aplicadas
      *Então* a lista de acusados é exatamente
      `["cards/detail/screen.py", "cards/screen.py"]` — profundidade, chave por
      caminho relativo e exclusão de cache continuam valendo
- [ ] `comportamental` — RF-05
      *Dado* o diretório `app/routers/` deste repositório
      *Quando* a enumeração e a acusação são aplicadas
      *Então* o mapeamento tem mais de dez chaves, todas terminando em `.py`, e a
      lista de acusados é vazia
- [ ] `comando` — RF-01, RF-02, RF-03, RF-04, RF-05
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_route_guard.py` sai com código `0` e a linha de resumo traz pelo
      menos `11 passed`, sem `failed` nem `error`. O código de saída se lê **sem
      cano**: encadear `| tail` devolve o código do `tail`.

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Trocar a acusação por leitura de árvore sintática.**
      Método: `ast.parse` do texto do módulo; uma passagem coleta o que cada
      `import`/`from ... import` de `datetime` liga a que nome local; uma segunda
      acusa toda chamada cujo alvo resolva a `date.today`, `datetime.today` ou
      `datetime.now`. Justificativa: seguir apelido e ignorar comentário e
      literal são a mesma capacidade, e nenhuma delas existe numa busca de texto.
- [ ] **1.2 — Os testes das seis situações acima**, mais o que o item `020`
      deixou: profundidade, colisão de nome e exclusão de cache continuam
      cobertos. Justificativa: a rede nova não pode custar a rede antiga.
