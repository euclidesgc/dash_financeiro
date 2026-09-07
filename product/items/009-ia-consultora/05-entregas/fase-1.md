## 1. O que foi implementado

**Item:** `009-ia-consultora` · **Fase:** `1 de 1`

`GET /consultor`. Três promessas, e a mais importante é a terceira.

**A IA pergunta o que falta — uma coisa de cada vez.** O painel escolhe o fato
ausente ou vencido cuja resposta mais move a projeção, faz **uma** pergunta, diz
qual número ela muda e em que tela responder. Três perguntas de uma vez não
recebem nenhuma resposta. Fato informado nunca é perguntado de novo; fato vencido
volta. E "Agora não" faz a pergunta sumir sem insistir — insistir é como um
painel deixa de ser lido.

**A IA nunca calcula.** Todo número que ela pode dizer já está no contexto,
calculado por código testado, e a instrução de sistema manda copiar dígito a
dígito e recusar a conta que o contexto não traz pronta. Se ela computasse "isso
te afasta 11 dias" erraria, e um número errado na unidade central deste produto
destrói a confiança em todo o resto.

**E a tela mostra o contexto exato que vai para o modelo** — as mesmas linhas, na
mesma ordem, construídas num lugar só. É por isso que o dono acha na tela todo
número que ele citar. O primeiro veredicto pegou justamente isso: a tabela
mostrava cinco das oito linhas, e as três de fora incluíam caixa e cartão.

Sem chave, sem rede, com resposta vazia ou JSON inesperado, a tela diz que a
leitura está indisponível — **em português e dizendo o quê** — e mostra os
números do mesmo jeito. Eles não dependem dela.

Branch: `009-ia-consultora/fase-1` · commits `cf38c41` e `d478c15`.

---

## 2. Critérios atendidos

Doze critérios, **um validador cego**. Veredicto integral em
[`05-veredictos/fase-1.md`](../05-veredictos/fase-1.md).

O que ele fez de mais forte: subiu o servidor **com chave falsa**, deixou o
provedor recusar, e comparou os cinco números da tela com os da execução sem
chave — **idênticos**. E verificou que a chave falsa não vazou na página. Também
conferiu a fronteira exata do limite de caracteres (500 → `200`, 501 → `400`), e
matou um servidor órfão de sessão anterior antes de medir qualquer coisa.

---

## 3. Como testar à mão

1. Abra `http://127.0.0.1:8000/consultor?data=2026-09-05`.
2. **Esperado:** uma pergunta só — a taxa dos cartões — dizendo que ela decide a
   ordem da escada de dívida.
3. Clique em **Agora não**.
4. **Esperado:** a pergunta vira o saldo de quitação do CDC.
5. Faça uma pergunta livre, sem `GEMINI_API_KEY` no ambiente.
6. **Esperado:** `200`, com "a leitura da IA está indisponível" e os números
   intactos.
7. Compare a tabela **O que ela lê** com o que o código envia.
8. **Esperado:** as mesmas nove linhas, na mesma ordem.

---

## 4. Divergências

Nenhuma. Cinco apontamentos do veredicto viraram requisito (`RF-16` a `RF-19`) e
foram corrigidos com teste em `d478c15`, sem rodada nova — régua registrada em
`D5`.

---

## 5. Raio de impacto

- `app/migrations/sql/009_advisor.sql` — `advisor_questions`.
- `app/advisor/gaps.py` — a fila declarada, o adiamento e o catálogo fechado.
- `app/advisor/context.py` — **`lines()` é a fonte única**: a tela renderiza e o
  modelo recebe a mesma lista.
- `app/advisor/gemini.py` — a instrução que proíbe o cálculo e as quatro formas
  de degradar, cada uma dizendo o quê.
- `app/routers/advisor.py`, `app/templates/consultor.html` — a tela.

---

## 6. Validações de campo pendentes

- **`009-ia-consultora`** — a qualidade da resposta do Gemini só se julga lendo,
  e exige chave válida. Como verificar: fazer três perguntas sobre os próprios
  dados e conferir que **todo número citado aparece na tabela "O que ela lê"**,
  dígito a dígito.

---

## 7. Pendências que viraram roadmap

Nenhuma nova.
