# Plano — 035-a-recusa-diz-o-que-faltou

**Trilha:** rápida · **Fonte aprovada:** `01-brief.md` · Uma fase.

## O terreno

`app/taxonomy/rules.py` — `correct_payee` alcança a validação com `group_id`
podendo ser `None`, e a validação levanta nomeando o termo inválido. Como o termo
é o próprio `None`, ele entra na mensagem formatado pelo Python.

## Decisões

| Dúvida | Decisão |
|---|---|
| Corrigir só este caso ou varrer | **Varrer.** Um caso é remendo; o segundo já apareceu neste projeto sob outra forma. Um teste que proíbe `None` em mensagem de recusa é o que impede o terceiro |
| A recusa muda de código | Não. Continua `400` |

## Fase 1 — Nenhuma recusa imprime um símbolo de código (api)

**Critérios de aceite**

- [ ] `comando` — RF-01, RF-03
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_gastos_correcao_screen.py -k grupo`
      sai `0` com ao menos um teste coletado. Os casos: a correção sem grupo responde `400`, a mensagem
      **não contém** a cadeia `None`, diz em português o que faltou, e
      `transactions` fica inalterada.
- [ ] `comando` — RF-02
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q -k recusa_sem_simbolo`
      sai `0` com ao menos um teste coletado. Esse teste percorre as rotas de
      escrita do painel com entrada que cada uma recusa, e afirma que **nenhuma**
      mensagem devolvida contém `None`, `null`, `NoneType` ou `Traceback`. É a
      forma de o terceiro caso não aparecer.
- [ ] `comando` — RF-04
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` sai
      `0`, com **mais** testes que a base desta branch e **nenhum** teste
      existente mudando de veredicto — as recusas que já diziam algo útil não
      foram tocadas.

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — A validação recebe o que faltou, não o valor nulo.** Justificativa:
      formatar `None` numa mensagem é sintoma; a causa é a validação não saber
      distinguir "termo inválido" de "termo ausente".
- [ ] **1.2 — Teste de varredura das recusas.** Justificativa: norma 20 — o caso
      idêntico ao lado se corrige junto, e o que impede o terceiro é uma medida,
      não uma intenção.
