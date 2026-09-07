---
name: python-ruff
description: "Lint e formatação com ruff: um só executável no lugar de black, isort, autoflake e flake8; as regras selecionadas, as que sustentam a norma do pack e o que nunca se silencia."
user-invocable: false
---

# Lint e formatação com ruff

## Quando esta skill vale

Vale ao configurar o projeto e sempre que alguém for silenciar um apontamento.
Ela define quais famílias de regra estão ligadas, por que cada uma está ali e
qual é a forma legítima de exceção.

Não vale para verificação de tipos, que é de outra ferramenta e de outra skill
(`python-tipagem-estrita`).

## A regra

**Dois comandos, e nenhum outro formatador no projeto:**

```bash
uv run ruff check --fix .
uv run ruff format .
```

No CI eles viram `ruff check .` e `ruff format --check .` — sem `--fix`,
porque um runner que conserta e segue esconde o defeito de quem o escreveu.

A configuração mora no `pyproject.toml`, e as famílias selecionadas são:

| Família | O que ela impede |
|---|---|
| `E`, `F` | erro de sintaxe e nome não usado |
| `I` | bloco de import fora de ordem |
| `N` | nome fora da convenção da linguagem |
| `UP` | forma antiga onde a versão-alvo já tem a nova |
| `B` | armadilha de comportamento, incluindo `B008` |
| `C4`, `SIM` | compreensão e condicional escritas de forma tortuosa |
| `ASYNC` | chamada bloqueante dentro de função assíncrona |
| `S` | padrão inseguro: `assert` em produção, chave fixa, subprocesso com `shell` |
| `T20` | `print` que sobreviveu à depuração |
| `RUF` | regras próprias do ruff, incluindo mutável como padrão |

## Por quê

**`B008` e `ASYNC` não estão na lista por gosto: elas são a norma do pack
cobrada por máquina.** `B008` reprova chamada de função como argumento padrão,
que é exatamente `def rota(x = Depends(...))` — a forma que a fonte primária
marca como anti-padrão e que a skill `python-dependencies-para-validacao`
substitui por `Annotated`. `ASYNC` reprova chamada bloqueante dentro de `async
def`, que é a violação descrita na skill `python-rota-async-io-nao-bloqueante`.
Sem essas duas famílias, as duas regras dependeriam de alguém lembrar delas na
revisão.

**Um só executável elimina a briga entre ferramentas.** black, isort e
autoflake discordam sobre a mesma linha, e o projeto passa a ter uma ordem
obrigatória de execução que ninguém documenta. Com ruff, formatar é idempotente.

**`S` fora da lista é o caminho mais curto para um segredo commitado.** É ela
que acusa chave fixa no código e `subprocess` com `shell=True`.

## Exemplo

**Errado** — o apontamento silenciado sem razão e no arquivo inteiro:

```python
# ruff: noqa
def build(command: str) -> None:
    subprocess.run(command, shell=True)
```

Um `noqa` de arquivo desliga tudo, inclusive o que ainda nem foi escrito ali.
E o `S602` que ele engoliu é execução de comando montado a partir de texto.

**Certo** — ou se corrige, ou se silencia a regra exata com a razão ao lado:

```python
def build(command: list[str]) -> None:
    subprocess.run(command, check=True)
```

Quando a exceção é legítima, ela nomeia o código e a razão:

```python
hashlib.md5(payload, usedforsecurity=False)  # noqa: S324 - motivo: soma de verificação de cache, não credencial
```

## `per-file-ignores` é para diferença de contexto, não para dívida

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]
"migrations/**" = ["N999"]
```

`S101` proíbe `assert` — em teste, `assert` é a ferramenta. `N999` cobra nome
de módulo em `snake_case`, e o arquivo de migração é nomeado pelo Alembic com
data e descrição. Nos dois casos a regra continua certa e o contexto é que
muda. Acrescentar um caminho aqui para calar apontamento que dá trabalho
consertar é dívida escondida num arquivo de configuração.

## Erros comuns

- **Deixar `--fix` no CI.** O runner corrige, o job passa, e a correção não
  está no commit de ninguém.
- **Manter black no `pre-commit` junto do ruff.** Os dois reformatam, e cada
  commit fica com um trecho no estilo de cada um.
- **`noqa` sem o código da regra.** Silencia tudo naquela linha, inclusive o
  defeito que aparecer ali no ano que vem.
- **Baixar `select` para `["E", "F"]`** quando o projeto herda muito
  apontamento. A saída é `per-file-ignores` no legado com data de remoção
  registrada, não desligar a régua para o código novo.

## Ponteiros

- `templates/ruff-config.toml` — o bloco pronto para o `pyproject.toml`.
- Onde a configuração mora e como as ferramentas são instaladas: skill
  `python-uv`.
- A regra que `B008` sustenta: skill `python-dependencies-para-validacao`.
- A regra que `ASYNC` sustenta: skill `python-rota-async-io-nao-bloqueante`.
