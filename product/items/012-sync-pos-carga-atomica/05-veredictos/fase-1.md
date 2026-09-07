# Veredicto — item `012-sync-pos-carga-atomica`, fase 1

**Resultado:** `APROVADO`

Branch: `012-sync-pos-carga/fase-1` · base `2f266cb` · ponta julgada `e73a1af`
Data: 2026-09-07 · Validador cego, agente novo.

> Os dois apontamentos foram corrigidos depois do veredicto, com teste, em
> `a4d1e2f`. Estão nomeados abaixo.

## Falha operacional minha, registrada pelo validador

**Troquei de branch durante a validação dele.** O `git diff` do despacho passou a
devolver vazio, e a árvore de trabalho esteve em `013-objetivo-lista-vazia/fase-1`
com quatro arquivos não commitados enquanto ele media. Ele não engoliu: exportou
o ref `012-sync-pos-carga/fase-1` para uma árvore isolada e **conferiu a
identidade por hash** antes de medir qualquer coisa —
`app/sync/__init__.py 7be163c2… IDENTICO`, `tests/test_sync.py 0b5dbfb8… IDENTICO`.

Ele também pegou um **passe falso do portão**: na árvore exportada,
`gates_runner.sh` imprimiu `limpos (árvore completa, 0 arquivo(s) considerados)`,
porque enumera por `git ls-files` e a exportação não tinha `.git`. Deu um git
local à árvore, `git ls-files` devolveu 327, e reexecutou. **Portão que não
conseguiu medir não aprova** — e ele foi quem aplicou a régua, não eu.

A lição fica: **nenhuma troca de branch enquanto um validador estiver rodando.**

## Portões

| Portão | Resultado |
|---|---|
| lint | **OK** — `All checks passed!`, `EXIT=0`. |
| testes | **OK** — `414 passed`, `EXIT=0`. |
| gates | **OK** — `✓ gates: limpos (árvore completa, 327 arquivo(s))`, na execução que de fato mediu. |

## Critérios — os cinco cumpridos

- [x] **`comando` — RF-01, RF-02, RF-03** — `12 passed`. O validador conferiu as
      **seis subcláusulas** do teste linha a linha, inclusive que `runs()` ordena
      por `id` e que `[-1][2]` é mesmo a coluna `status`.
- [x] **`estrutural` — RF-01** — `_after` dentro do `try` em `:66-73`, e o
      `except` chamando `_demote`, que executa
      `UPDATE sync_runs SET status = 'failed'`.
- [x] **`comportamental` — RF-05** — o caminho feliz intacto: `sync ok:
      inserted=0`, `EXIT=0`, e a última linha de `sync_runs` em `ok`. O binário
      `sqlite3` não existe nesta máquina; ele rodou a mesma query pelo módulo do
      venv e disse que fez isso.
- [x] **portão local e de lint** — `414 passed`, `All checks passed!`.

## A verificação independente

Ele **não se contentou** em trocar `_after` inteiro, como o teste faz. Quebrou os
**três passos reais**, um a um, e leu o banco direto:

```
QUEBRANDO rebuild      → id=2 status='failed' 'pós-carga falhou: ZeroDivisionError'
QUEBRANDO recompute    → id=3 status='failed' 'pós-carga falhou: ValueError'
QUEBRANDO classify_all → id=4 status='failed' 'pós-carga falhou: KeyError'
```

E dirigiu a rota HTTP real: `POST /sincronizar` com a pós-carga quebrada devolve
**200** com o aviso em português, e o caminho feliz devolve 200 com
`Sincronizado. Nenhum lançamento novo.`

**Ponto residual entre o `ok` e o fim da função: nenhum.** Ele confirmou que
`reference_date()` está dentro do `try`, quebrando-a de propósito, e que o que
sobra depois é construção de dataclass.

## Os dois apontamentos — corrigidos em `a4d1e2f`

1. **A mensagem prometia mais do que o código entrega.** "As telas mostram o
   estado anterior" só é verdade se `classify_all` falhar **primeiro**: os três
   passos commitam por dentro, então uma falha no segundo ou no terceiro deixa a
   base **parcialmente** atualizada. Ele mediu — `TRABALHO_PARCIAL_PERSISTIU:
   sim`, lido por conexão nova. A frase agora diz *"Parte das telas pode estar
   desatualizada"*.
2. **`_demote` mirava `MAX(id)`**, acoplando o rebaixamento a "ninguém mais
   escreve em `sync_runs` entre o ingest e a falha". Ele mediu os dois limites —
   nenhum passo de `_after` toca a tabela, e dois syncs simultâneos são barrados
   pelo lock do SQLite — e só expôs o erro com uma inserção artificial. Registrou
   que fechar isso exigia `IngestResult` expor o id da linha gravada. **Foi o que
   foi feito:** `IngestResult.run_id` existe, e o `UPDATE` nomeia a própria linha.
