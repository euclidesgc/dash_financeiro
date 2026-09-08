# Discovery — 020-varredura-de-rota-que-nao-desce-em-subpasta

**Item do roadmap:** `020-varredura-de-rota-que-nao-desce-em-subpasta` — o guarda que
impede uma rota de resolver a data de tela por conta própria varre `app/routers/` com
`glob("*.py")`, que não desce em subpasta, enquanto o critério de integração do `016`
usa `grep -R`. Hoje os dois coincidem, porque os 15 módulos estão todos no nível de
cima. No dia em que nascer um subpacote sob `app/routers/`, o guarda fica cego, verde
e silencioso.

**Data:** 2026-09-07 · **Trilha declarada:** rápida

## Regra, exemplo e pergunta

- **Regra.** O guarda de rota enxerga todo módulo de rota, em qualquer profundidade.
- **Regra.** O guarda tem teste do próprio dente: um módulo de rota que resolve a data
  sozinha faz o guarda falhar, e o teste prova isso onde o guarda de fato olha.
- **Exemplo.** Nasce `app/routers/cards/screen.py` chamando `date.today()`. Hoje o
  guarda passa verde. Depois deste item, ele acusa.
- **Pergunta em aberto:** nenhuma.

## Os quatro gatilhos de trilha completa

| Gatilho | Resposta |
|---|---|
| Mexe em contrato público ou OpenAPI? | Não. Nenhuma rota muda. |
| Toca autenticação, autorização ou dado pessoal? | Não. |
| Tem mais de uma frente de stack? | Não: `api`, e só em teste. |
| Requisito ambíguo que exija spec formal? | Não: a mudança é uma palavra e a prova dela. |

**Trilha rápida**, uma fase.

## Decisões autônomas

| Dúvida | Decisão | Alternativa descartada e por quê |
|---|---|---|
| Trocar `glob` por `rglob`, ou reescrever o guarda sobre `grep -R`? | `rglob("*.py")` | `grep -R` põe o guarda a depender de processo externo e de opção de plataforma (`--exclude-dir=__pycache__`); o guarda é Python e a varredura é da linguagem. |
| O teste do dente basta como está? | Não: ele passa a exercer o guarda **dentro de subpasta**, que é o buraco medido | Manter o teste no nível de cima deixaria a correção sem prova: o guarda mudaria e nenhum teste falharia se a mudança fosse desfeita. |
