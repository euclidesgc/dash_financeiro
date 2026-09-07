# Veredicto — item `004-resumo-e-projecao`, fase 1

**Resultado:** `APROVADO`

Branch: `004-resumo-e-projecao/fase-1-motor` · ponta `f858133` · base `05097be`
Data da verificação: 2026-09-07 · Validador cego, agente novo.

**Higiene do despacho.** Nenhum plano, brief, spec, histórico de fase ou
veredicto anterior veio no envelope. Duas ressalvas registradas pelo próprio
validador: o despacho carregou uma **justificativa do implementador** sobre a
reescrita do critério de RF-10 — raciocínio de quem implementou, que ele
recusou como evidência e substituiu por teste de mutação —, e o despacho
declarou `.harness/` fora dos limites enquanto as regras de operação dele mandam
ler `command_quirks` em `.harness/config.json` antes de confiar em exit code
zero. O conflito é do despacho, não do validador.

## Portões

| Portão | Resultado |
|---|---|
| lint/analyze | **não declarado na toolchain** — `pyproject.toml` traz só `pytest` e `httpx` em `dev`; `import ruff` e `import mypy` respondem `ModuleNotFoundError`. Não é portão que deixou de ser medido: é portão que não existe. |
| testes | **OK** — `324 passed, 2 warnings in 15.50s`, `EXIT=0`, capturado em arquivo e não por pipe. |
| gates | **OK** — `✓ gates: limpos (árvore completa, 233 arquivo(s) considerados).`, `EXIT=0`. |

Base preparada como o critério manda: `migrations applied: 4`,
`ingested transactions=1942 accounts=12`, `commitments recomputed: 115`.

## Critérios de aceite

- [x] **`comando` — RF-01 a RF-04** —
      `{'cash_cents': -1070509, 'card_cents': -1674462, 'consolidated_cents': -2744971}`,
      e `-1070509 + (-1674462) = -2744971`.
- [x] **`comando` — RF-05 a RF-08** — `months` com os seis meses completos,
      `income_cents 1222621`, `spending_cents -1767746`, `leftover_cents -545125`.
      Os quatro batem na ordem e no sinal.
- [x] **`comando` — RF-10, RF-12 a RF-15** — `len(days) = 46`; primeiro
      `2026-09-05 / -2744971`; último `2026-10-20 / -3444179`; pior
      `2026-10-13 / -4072295`, **anterior ao último dia**, logo o mínimo não é
      trivial; `delta_cents -699208`; `variable_cents -965067`.
- [x] **`comando` — RF-16** — `8 passed`, `EXIT=0`. As duas asserções nomeadas
      foram lidas no fonte: a linha reta afirma 46 dias com um único saldo
      distinto; a da soma percorre **todos** os pares consecutivos e afirma
      `saldo = saldo_anterior + entra + sai + variável`, com o dia zero ancorado
      à parte.
- [x] **`estrutural` — RF-10** — `forecast.py:5` importa `window` de
      `app.commitments.calendar`; `\b45\b` em `app/projection` não imprime linha.

## Critérios de integração

- [x] **`comando` — portão local** — `324 passed`, `EXIT=0`.
- [x] **`comando` — RF-24** — nenhum dos dez números aparece, em nenhum dos dois
      fluxos, medido com e sem `rtk proxy`.

## Julgamento do critério reescrito (RF-10)

**O critério mede o código; não o descreve.** O validador recusou tanto a
justificativa do implementador quanto o caminho barato:

1. Rodar o critério contra a árvore do commit base **não prova nada** —
   `git ls-tree -r 05097be -- app/projection` não devolve caminho nenhum. O
   pacote não existia, e qualquer critério apontando para ele reprovaria por
   ausência de alvo, não por discriminação.
2. **Teste de mutação**, em cópia isolada fora do repositório: trocou o import
   por `from app.commitments.calendar import calendar` e a janela por
   `last = first + timedelta(days=45)`. A primeira cláusula reprova (a linha
   existe mas não cita `window`); a segunda reprova (o literal aparece). O
   critério rejeita a implementação errada plausível que ele existe para barrar.
3. Nenhuma cláusula passa por vacuidade: a primeira exige fato positivo, então
   um `app/projection` vazio também reprova.

**Limite registrado, sem mudar o veredicto:** a segunda cláusula proíbe o
literal `45`, não a recontagem da janela. `40 + 5`, ou uma constante local com
outro nome, passaria. É uma cerca, não prova de origem.

## Instrumentos do implementer

Só o critério RF-16 depende da suíte do avaliado, e por construção — ele pede
que o arquivo exista, passe e contenha duas asserções nomeadas, que foram lidas
no fonte. Os demais foram verificados por execução própria contra a base
ingerida e por grep e mutação.

## Apontamentos

1. **O vocabulário de tipo de conta passou a ter duas fontes.**
   `app/projection/__init__.py` define `BANK` e `CREDIT`, enquanto a
   normalização de sinal do cartão em `app/ingest/loader.py:242` — a que sustenta
   o invariante 22 — continua comparando com o literal cru
   `raw.get("type") == "CREDIT"`. `positions()` soma por `type` e a inversão de
   sinal na ingestão precisam concordar sobre a mesma string: hoje concordam por
   coincidência textual, não por construção. Nenhum critério é afetado.
