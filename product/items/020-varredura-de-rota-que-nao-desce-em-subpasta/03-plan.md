# Plano — 020-varredura-de-rota-que-nao-desce-em-subpasta

**Item:** `020-varredura-de-rota-que-nao-desce-em-subpasta` · **Trilha:** rápida ·
**Fonte aprovada:** `01-brief.md` · **Terreno:** `00-discovery.md` · Uma fase.

> **Todo fato deste plano foi medido no repositório em 07/09/2026**, não
> presumido: a listagem de `app/routers/`, a forma da varredura em
> `tests/test_route_guard.py`, o precedente de `tests/test_frozen_numbers.py`, o
> escopo dos gates em `.harness/gates.json` e o passo de teste do CI.

## Objetivo

O guarda que impede uma rota de resolver a data de tela por conta própria passa
a enxergar todo módulo sob `app/routers/`, em qualquer profundidade, e cada
módulo é medido pelo seu caminho, não pelo nome do arquivo. A varredura ganha
dente onde hoje ela é cega: testes que a exercitam sobre uma árvore com módulo
dentro de subpasta — um que chama o relógio e é acusado, outro que consome o
leitor único e é aceito — de modo que desfazer a correção deixa o teste
vermelho, em vez de deixá-lo verde e calado.

Nenhum módulo de `app/` muda. O item é a rede, não o que ela pega.

## O terreno, medido

| Sítio | Hoje | O que falta |
|---|---|---|
| `tests/test_route_guard.py:76` | `ROUTERS_DIR.glob("*.py")`, chaveado por `path.name` | descer em subpasta; chavear por caminho relativo |
| `tests/test_route_guard.py:82-85` | o teste do dente entrega um **dicionário literal** (`{"fake.py": ...}`) a `_accused` | passar pela enumeração: hoje ele prova o casamento do texto, nunca a varredura |
| `app/routers/` | 15 arquivos `.py`, todos no nível de cima; nenhum subdiretório além de `__pycache__` | nada — o item não cria subpacote de produção |
| `app/routers/__pycache__/` | só `.pyc` (inclusive `pages.cpython-312.pyc`, de um módulo que já não existe) | a enumeração recursiva precisa excluí-lo por nome, e não por extensão |

Três fatos decidem o desenho e não se re-discutem:

- **O precedente da casa já tem a forma certa.** `tests/test_frozen_numbers.py:68-75`
  define `scan(folder, base)` — raiz por parâmetro, `rglob`, chave por
  `relative_to(base)` — e prova o próprio dente plantando arquivo em `tmp_path`
  (`:99-102`, `:115-117`). A varredura de rota é o mesmo problema com outro
  padrão de busca.
- **`pytest` já é o executor.** `pyproject.toml:27-29` fixa `testpaths = ["tests"]`
  e `.github/workflows/ci-python.yml:93-101` roda `uv run pytest -q`: teste novo
  neste arquivo entra no CI sem que nenhum fluxo, portão ou manifesto mude.
- **O gate de comentário não alcança teste.** `.harness/gates.json:8-14` restringe
  G3 a `src/**` e isenta `**/tests/**`; G4 (sem pendência marcada no código)
  alcança `tests/**`.

## Decisões resolvidas por padrão, não por pergunta

| Dúvida | O que decidiu | Decisão |
|---|---|---|
| Onde mora a enumeração? | O item toca um arquivo, e a varredura só serve aos testes dele | função `_sources(root)` no próprio `tests/test_route_guard.py`; nenhum arquivo novo |
| Qual a chave do mapeamento? | RF-05: dois módulos de mesmo nome em subpacotes diferentes colapsam numa chave só | `path.relative_to(root).as_posix()` |
| Como o cache é excluído? | O risco do brief é fonte copiada dentro de diretório de cache | `"__pycache__" in relative.parts` — sobre o caminho **relativo**, porque o caminho absoluto pode carregar o nome por acidente do checkout |
| O teste do dente atual basta? | Ele entrega dicionário literal a `_accused` e nunca chama a enumeração — é exatamente o buraco medido | ele **sai** e é substituído pela versão sobre árvore temporária |
| O teste de alcance congela os 15 nomes? | Os itens `024`, `025` e `027` acrescentam rotas, e guarda que fica vermelho por motivo errado é guarda que se desliga | o teste calcula o nível de cima com `iterdir()` e afirma **inclusão**, não igualdade |
| Entra portão novo em `scripts/gates/`? | Decisão do item `016`, ainda válida: quem executa o guarda é `pytest` | não; `gates_runner.sh`, `.harness/gates.json` e `.github/workflows/` não são tocados |
| O critério de integração do `016` (`grep -R`) muda? | Não-escopo do brief: ele já desce | não |

---

## Fase 1 — A varredura que desce, e o dente que prova (api)

**Objetivo da fase:** o guarda de rota enumera `app/routers/` recursivamente,
identifica cada módulo pelo caminho relativo, e falha se a varredura voltar a
ser rasa.

**Critérios de aceite:**

- [ ] `estrutural` — RF-01, RF-05
      `tests/test_route_guard.py` define a função `_sources`, que recebe um
      diretório como parâmetro e devolve o mapeamento dos módulos daquele
      diretório. O arquivo contém a expressão `.rglob("*.py")`, contém
      `relative_to` e **não** contém a expressão `.glob("*.py")` — o ponto antes
      de `glob` é o que separa as duas, porque `.rglob("*.py")` não carrega
      `.glob("*.py")` dentro de si.
- [ ] `estrutural` — RF-02, RF-03, RF-04, RF-05
      `tests/test_route_guard.py` define as funções
      `test_no_router_resolves_the_screen_date_by_itself`,
      `test_the_sweep_reaches_every_module_of_the_routers_folder`,
      `test_the_sweep_accuses_a_router_inside_a_subpackage`,
      `test_the_sweep_accepts_a_subpackage_router_that_reads_the_reference`,
      `test_two_routers_of_the_same_name_are_two_measurements` e
      `test_a_cached_copy_is_not_a_router`; define também
      `test_every_registered_route_requires_session` e
      `test_the_login_form_is_the_open_door`, que são a guarda de sessão e
      seguem intactos; e **não** define
      `test_the_sweep_accuses_a_source_that_calls_the_clock`, cujo dicionário
      literal nunca passava pela enumeração.
- [ ] `comportamental` — RF-01, RF-02
      *Dado* um diretório temporário com dois arquivos escritos pelo próprio
      teste — `cards/screen.py` e `cards/detail/screen.py`, cada um com o texto
      `from datetime import date` numa linha e `date.today()` na seguinte
      *Quando* a enumeração do guarda é aplicada a esse diretório e o resultado
      é entregue à acusação
      *Então* a lista de acusados é exatamente
      `["cards/detail/screen.py", "cards/screen.py"]` — um módulo a um nível de
      profundidade e outro a dois. Com varredura rasa a lista vem vazia, e o
      guarda passa verde
- [ ] `comportamental` — RF-03
      *Dado* um diretório temporário com o arquivo `cards/screen.py` escrito
      pelo próprio teste, contendo `from app.routers.reference import screen_date`
      e uma função que devolve `screen_date(pedido).date`, sem nenhuma
      ocorrência de `date.today()`
      *Quando* a enumeração do guarda é aplicada a esse diretório
      *Então* a chave `cards/screen.py` está presente no mapeamento **e** a
      lista de acusados é vazia — as duas afirmações juntas, porque só a segunda
      passaria também numa varredura que não enxergou o arquivo, e o item existe
      justamente contra a aprovação por cegueira
- [ ] `comportamental` — RF-05
      *Dado* um diretório temporário com `cards/screen.py`, contendo
      `from app.routers.reference import screen_date`, e `goals/screen.py`,
      contendo `from datetime import date` e `date.today()` — dois arquivos de
      mesmo nome em subpastas diferentes
      *Quando* a enumeração do guarda é aplicada a esse diretório
      *Então* o conjunto de chaves do mapeamento é
      `{"cards/screen.py", "goals/screen.py"}` — duas entradas — e a lista de
      acusados é exatamente `["goals/screen.py"]`. Chaveado por nome de arquivo
      o mapeamento tem **uma** entrada, e qual dos dois textos sobrevive depende
      da ordem de leitura: numa das ordens o módulo que chama o relógio
      desaparece sem acusação
- [ ] `comportamental` — RF-04
      *Dado* um diretório temporário com `screen.py` no nível de cima, contendo
      `from app.routers.reference import screen_date`, e
      `__pycache__/screen.py`, contendo `from datetime import date` e
      `date.today()`
      *Quando* a enumeração do guarda é aplicada a esse diretório
      *Então* o conjunto de chaves do mapeamento é exatamente `{"screen.py"}` e
      a lista de acusados é vazia — fonte copiada para dentro de diretório de
      cache não é módulo de rota, e não reprova quem não a escreveu
- [ ] `comportamental` — RF-01, RF-04
      *Dado* o diretório `app/routers/` deste repositório
      *Quando* a enumeração do guarda é aplicada a ele
      *Então* o conjunto de chaves contém `__init__.py`, `advisor.py`,
      `auth.py`, `commitments.py`, `debts.py`, `health.py`, `navigation.py`,
      `plan.py`, `reference.py`, `render.py`, `rules.py`, `settings.py`,
      `spending.py`, `summary.py` e `whatif.py`; toda chave termina em `.py`;
      nenhuma chave contém `__pycache__`; e a lista de acusados é vazia — os 15
      módulos do nível de cima continuam varridos, e nenhum deles resolve a data
      de tela por conta própria
- [ ] `estrutural` — RF-01
      `app/routers/` não contém nenhum arquivo `.py` fora do nível de cima e
      nenhum subdiretório além de `__pycache__`: a prova da varredura recursiva
      é feita sobre árvore temporária, e não sobre subpacote de produção criado
      para satisfazer teste
- [ ] `comando` — RF-01, RF-02, RF-03, RF-04, RF-05
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_route_guard.py` sai com código `0`, e a linha de resumo traz
      pelo menos `8 passed` e nenhum `failed` ou `error` — dois testes de guarda
      de sessão e seis de varredura. O código de saída se lê **sem cano**:
      encadear `| tail` devolve o código do `tail`, e o comando reprovado
      passaria por aprovado

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Modificar `tests/test_route_guard.py`: a enumeração vira função
      com raiz, recursiva e chaveada por caminho relativo.**
      Método:
      ```python
      def _sources(root: Path) -> dict[str, str]:
          found = {}
          for path in sorted(root.rglob("*.py")):
              relative = path.relative_to(root)
              if "__pycache__" in relative.parts:
                  continue
              found[relative.as_posix()] = path.read_text(encoding="utf-8")
          return found
      ```
      `_accused` fica como está — passa a receber caminhos relativos onde recebia
      nomes. `test_no_router_resolves_the_screen_date_by_itself` deixa de montar
      o dicionário na própria linha e passa a `_accused(_sources(ROUTERS_DIR))`.
      *Considerando:* nada antes — é a primeira etapa.
      *Justificativa:* RF-01, RF-04, RF-05. A raiz entra por parâmetro porque é
      o que permite provar a varredura sobre árvore temporária sem criar
      subpacote de produção, que o brief põe no não-escopo;
      `tests/test_frozen_numbers.py:68-75` já é essa forma na casa, com `rglob`,
      raiz por parâmetro e chave por `relative_to`. A exclusão é por nome de
      diretório sobre o caminho **relativo**, e não sobre `path.parts`: o
      caminho absoluto pode conter o nome por acidente do lugar onde o
      repositório está clonado, e a varredura inteira sairia vazia — verde e
      calada, que é o defeito que o item fecha. `encoding="utf-8"` explícito
      acompanha `tests/test_frozen_numbers.py:62`, e os módulos de rota carregam
      texto acentuado.

- [ ] **1.2 — Modificar `tests/test_route_guard.py`: os quatro testes sobre
      árvore temporária.**
      Um auxiliar escreve a árvore a partir de um mapeamento de caminho para
      texto, criando as pastas intermediárias:
      ```python
      def _tree(root: Path, files: dict[str, str]) -> Path
      ```
      Sobre ele, quatro testes, todos com `tmp_path`:
      `test_the_sweep_accuses_a_router_inside_a_subpackage` — `cards/screen.py` e
      `cards/detail/screen.py`, os dois com `date.today()`, acusados os dois;
      `test_the_sweep_accepts_a_subpackage_router_that_reads_the_reference` —
      `cards/screen.py` importando `screen_date` de `app.routers.reference`,
      afirmando a **presença da chave** e a lista de acusados vazia;
      `test_two_routers_of_the_same_name_are_two_measurements` —
      `cards/screen.py` limpo e `goals/screen.py` com o relógio, afirmando as
      duas chaves e o único acusado;
      `test_a_cached_copy_is_not_a_router` — `screen.py` limpo no nível de cima e
      `__pycache__/screen.py` com o relógio, afirmando chave única e nenhum
      acusado.
      O teste `test_the_sweep_accuses_a_source_that_calls_the_clock`
      (`tests/test_route_guard.py:82-85`) **sai**: o que ele substitui já cobre a
      acusação, e por dentro da enumeração.
      *Considerando 1.1:* os quatro chamam `_sources(tmp_path)` e só depois
      `_accused`.
      *Justificativa:* RF-02, RF-03, RF-04, RF-05. O teste que sai entrega um
      dicionário literal a `_accused` e nunca toca a varredura — é por isso que a
      correção do `016` chegou a produção com a varredura rasa e o guarda verde.
      O teste de aceitação afirma a chave **antes** de afirmar a lista vazia
      porque instrumento que aceita por não ter olhado é o mesmo silêncio de
      antes, com outro nome. Os textos plantados são strings dentro do teste, e
      nunca são importados: a varredura lê arquivo, não módulo.

- [ ] **1.3 — Modificar `tests/test_route_guard.py`: o teste que fixa o alcance
      sobre `app/routers/`.**
      `test_the_sweep_reaches_every_module_of_the_routers_folder` calcula o nível
      de cima sem a busca antiga —
      `{entry.name for entry in ROUTERS_DIR.iterdir() if entry.suffix == ".py"}` —
      e afirma que esse conjunto está **contido** nas chaves de
      `_sources(ROUTERS_DIR)`, que toda chave termina em `.py` e que nenhuma
      contém `__pycache__`.
      *Considerando 1.1.*
      *Justificativa:* RF-04. A inclusão é deliberada: igualdade com uma lista
      congelada de 15 nomes faria o guarda ficar vermelho no dia em que os itens
      `024`, `025` ou `027` acrescentassem uma rota legítima, e guarda que
      reprova por motivo errado é guarda que se desliga. `iterdir()` no lugar de
      `glob("*.py")` mantém o arquivo sem a expressão rasa, que é o que o
      critério estrutural cobra e o que uma reversão distraída traria de volta.

- [ ] **1.4 — Quem executa a varredura, e o que não é tocado.**
      O executor é `pytest`: `pyproject.toml:27-29` fixa `testpaths = ["tests"]`
      e `.github/workflows/ci-python.yml:93-101` roda `uv run pytest -q` no PR
      fora de rascunho — os testes novos entram no CI sem edição de fluxo.
      **Nenhum arquivo sob `scripts/gates/`, `.harness/` ou `.github/` é
      modificado**, e nenhum arquivo sob `app/` é modificado. Antes de dar a
      fase por pronta, `bash scripts/lint.sh` e
      `bash scripts/gates/gates_runner.sh` rodam localmente.
      *Considerando 1.1 a 1.3.*
      *Justificativa:* RF-01 e a decisão do item `016` de que o guarda é teste, e
      não portão. A etapa existe porque a peça que falta em correção de
      instrumento é sempre a terceira — quem roda o instrumento —, e ela mora em
      pasta que não se parece com o assunto; medido aqui, ela já está no lugar, e
      registrar isso é o que impede o implementer de tocá-la e produzir
      divergência de escopo.

---

## Execução sugerida

Fase única, em branch própria integrada em `develop`. O item roda em worktree
paralela a outras cinco frentes e toca **um** arquivo, `tests/test_route_guard.py`,
que nenhuma delas tem motivo para editar: a interseção é vazia por construção, e
não há ordenação a respeitar com ninguém.

O único acoplamento com as outras frentes é de conteúdo, não de arquivo: uma
frente que acrescente rota sob `app/routers/` muda o conjunto que o teste de
alcance mede. Por isso o teste afirma inclusão, e não igualdade — o plano já
absorve esse encontro sem exigir sequência.

## Pendências que viram item de roadmap

- **O guarda reconhece uma única forma de chamar o relógio.** A varredura
  procura o texto `date.today()`; `datetime.now().date()`, `datetime.today()` e
  um `from datetime import date as d` seguido de `d.today()` passam por ela em
  silêncio. O brief não pede o contrário — os seis sítios medidos no `016`
  usavam a forma literal —, e ampliar o padrão aqui seria requisito nascido no
  plano. É a mesma família de defeito que este item fecha, e a que sobra depois
  dele.
- **O varredor de números congelados não exclui diretório de cache.** `scan`
  (`tests/test_frozen_numbers.py:68-75`) desce com `rglob` sobre `app/` em `.py`,
  `.sql` e `.html` sem excluir `__pycache__`. Hoje é inofensivo, porque o cache
  guarda só `.pyc`; uma fonte copiada para lá reprovaria o varredor por arquivo
  que ninguém escreveu. O arquivo está fora do escopo declarado deste item, que
  só toca `tests/test_route_guard.py`.

## Validações de campo pendentes

Nenhuma. Todo comportamento deste item se observa por leitura de arquivo em
disco — diretório temporário escrito pelo próprio teste e o `app/routers/` do
repositório —, executada por `pytest`; nada depende de aparelho físico,
permissão de plataforma ou rede real.
