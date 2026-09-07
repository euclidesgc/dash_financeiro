# Discovery — 009-ia-consultora

**Item do roadmap:** `009` — A IA **pergunta o que falta**, explica o resultado,
orienta o próximo passo e responde pergunta livre sobre os próprios dados. **A IA
nunca calcula.**

**Data:** 2026-09-07

## História

Como dono deste painel, quero que ele me pergunte o que falta e me explique o
que vejo, sem nunca inventar um número, para eu confiar no que leio.

## Regras e exemplos

### R1 — Uma pergunta de cada vez, e ela diz qual número muda

- **E1.1** — O painel escolhe o fato ausente ou vencido cuja resposta mais move a
  projeção e faz **uma** pergunta. Três perguntas de uma vez não recebem nenhuma
  resposta.
- **E1.2** — Hoje a primeira é a **taxa dos cartões**: ela decide a ordem da
  escada de dívida, e com ela onde o próximo real rende mais.
- **E1.3** — A pergunta some quando o fato entra, e **não volta**. Volta só
  quando o fato vence.
- **E1.4** — "Agora não" faz a pergunta sumir sem insistir. Insistir é como um
  painel deixa de ser lido.

### R2 — A IA nunca calcula

- **E2.1** — Todo número que ela pode dizer já está no contexto, calculado por
  código testado. A instrução de sistema manda copiar dígito a dígito e recusar
  a conta que o contexto não traz pronta.
- **E2.2** — Se ela computasse "isso te afasta 11 dias", erraria — e um número
  errado na unidade central deste produto destrói a confiança em todo o resto.
- **E2.3** — A tela **mostra o contexto exato** que vai para o modelo. O dono vê
  de onde cada número que ele lê pode ter vindo.

### R3 — Sem chave, sem rede, sem resposta: o número continua

- **E3.1** — Sem `GEMINI_API_KEY`, com erro de rede, com resposta vazia ou com
  JSON inesperado, a tela diz que a leitura da IA está indisponível **e mostra
  os números do mesmo jeito**. Eles não dependem dela.

## Perguntas em aberto

Nenhuma.

## Trilha

**Trilha: rápida.** Uma fase.
