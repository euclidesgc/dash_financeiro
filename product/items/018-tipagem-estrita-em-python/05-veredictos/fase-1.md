# Veredicto — 018, fase 1 (O verificador no ambiente, e `app` limpo)

**Veredicto:** APROVADO · **Validação cega** · **Data:** 08/09/2026

O validador não viu quem implementou nem o que ele relatou. Toda evidência foi
produzida por comando que ele mesmo executou. Ele registra que não usou as
capturas de tela deixadas pelo implementador como prova: refez a comparação de
totais por conta própria.

## Portões

| Portão | Resultado |
|---|---|
| `scripts/lint.sh` | OK — `All checks passed!`, `178 files already formatted`, saída `0` |
| Suíte | OK — `717 passed`, saída `0` |
| `scripts/gates/gates_runner.sh` | OK — `gates: limpos (árvore completa, 611 arquivo(s) considerados)`, saída `0` |
| `mypy` no portão de lint | **Ausente por desenho.** O plano liga o portão só na fase 2, com os três pacotes limpos — portão que nasce vermelho é portão que se desliga |

## Critérios

**`estrutural` (RF-01, RF-02).** `pyproject.toml` declara `mypy>=2.3.1` no grupo
de desenvolvimento e traz uma seção `[tool.mypy]` única, com `strict = true`,
`packages = ["app", "financas", "ingestao"]` e `python_executable =
".venv/bin/python"`. `uv.lock` trava a versão `2.3.1` com os hashes. Controle
positivo: `.venv/bin/mypy --version` imprime `mypy 2.3.1 (compiled: yes)` e sai
`0` — antes da fase o binário não existia. Não há `mypy.ini` nem `setup.cfg`
concorrendo com a configuração.

**`comando` (RF-03).** `mypy --strict app` → `Success: no issues found in 104
source files`, saída `0`. **N = 104**, e o número importa: o verificador também
sai verde quando não encontra arquivo nenhum. Controle cruzado do validador:
`mypy --strict financas ingestao` ainda acusa **91 erros** — prova que a limpeza
é do pacote `app` e não efeito de medir o vazio.

**`comando` (RF-05).** `grep -rn "type: ignore" app --include='*.py'` devolve
exatamente duas linhas, ambas em `app/routers/auth.py` (87 e 106), ambas com o
código do erro entre colchetes e a razão. O validador conferiu a honestidade do
silenciamento ao vivo: o stub do Starlette tipa `samesite` como literal
minúsculo, e `tests/test_login.py:39` exige o cabeçalho com `SameSite=Lax`,
maiúsculo. Trocar para minúsculo passaria no verificador e **mudaria o byte que
sai no `Set-Cookie`**. Conflito real entre o stub e o formato de rede, não
atalho escondendo defeito.

**`comando` (RF-06).** O validador recriou o commit-base da fase num worktree
temporário e mediu: **717 testes** antes, **717** depois, saída `0` nos dois.
Anotar não acrescentou nem removeu teste.

**`comportamental` (RF-06) — a prova mais forte da fase.** Com a base real
copiada para dois diretórios temporários — um rodando o código anterior, outro o
desta fase — e `DASH_TODAY=2026-09-05`, ele buscou `/`, `/gastos`,
`/comprometido` e `/dividas` contra a app em memória. As quatro responderam
`200` nas duas revisões, e o HTML devolvido é **byte a byte idêntico**. Nenhum
número de manchete se moveu.

## A revisão que este item exigia

O modo mais comum de anotação quebrar comportamento é converter um valor para
agradar o verificador. O validador leu o diff inteiro — 44 arquivos, 243 linhas
acrescentadas, 165 removidas — procurando exatamente isso:

- Os `cast()` recaem sobre expressões cujo tipo em execução já era o anotado.
- O `assert` de estreitamento em `app/ingest/loader.py:302` nunca dispara: os
  dois mapeadores só devolvem `(None, Rejection)` ou `(dict, None)`.
- `group_id` passou de `int` para `int | None` em `app/taxonomy/rules.py`. É
  alargamento honesto: a validação já tratava `None` corretamente em execução, e
  quem mentia era o tipo.
- Em `app/routers/render.py`, os filtros trocaram `object` mais `int(...)` por
  `int | None` **sem** a conversão. Só é seguro porque o domínio real desses
  parâmetros é sempre `int | None` vindo de `sqlite3.Row` — e a comparação byte a
  byte das quatro telas é o que prova.
- O único `float(...)` novo está em `app/design/contrast.py`, cálculo de
  contraste de cor. **Nenhuma conversão nova em caminho de centavos** (norma 22).

**Norma 24** confirmada: as quatro rotas sem cookie respondem `302` para
`/login`. A tipagem não afrouxou a autorização.

## Achados fora do escopo

1. A medição do plano registrava 126 erros em `app`; a máquina que implementou
   mediu 145, por uma versão de correção do verificador entre as duas medidas. O
   número que vale para o critério é o que o validador executou: 104 fontes
   limpas.
2. `correct_payee` pode alcançar a validação com grupo nulo, e a mensagem que o
   dono lê mostra literalmente `None` em vez de texto claro. Não move dinheiro e
   não foi corrigido em silêncio — vira item de roadmap de mensagem de erro.
