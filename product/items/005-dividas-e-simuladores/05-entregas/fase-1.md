## 1. O que foi implementado

**Item:** `005-dividas-e-simuladores` · **Fase:** `1 de 1`

`GET /dividas` responde a pergunta que decide o próximo real: **onde ele rende
mais**. A resposta é sempre o degrau de cima da escada, qualquer que seja o
tamanho do saldo — e a escada ordena por taxa mensal, não por valor.

Quatro degraus nascem do que existe: um por conta bancária no vermelho, um por
cartão, e um por contrato em `data/manual/`. Na base de 05/09/2026 são
**R$ 11.190,18** de cheque especial, **R$ 16.744,62** de cartões,
**R$ 39.176,36** de CDC a 1,63% a.m. e **R$ 238.585,18** de imóvel a
**0,7200% a.m.**

Três decisões que definem o item:

- **O saldo do CDC não é copiado de lugar nenhum.** É o valor presente das 45
  parcelas ainda não vencidas de R$ 1.235,33, descontadas à taxa do contrato —
  o que a lei manda o banco oferecer na quitação antecipada. Dá exatamente o
  número do relatório de origem, reproduzido por cálculo.
- **Dívida sem taxa não entra na escada.** Fica num bloco próprio dizendo o que
  falta. Chutar seria o painel decidindo o que não sabe, e as duas dívidas mais
  caras são justamente as duas cuja taxa não está em dado nenhum. A taxa que o
  dono digita **sobrevive à recarga**.
- **O simulador responde em parcelas e em juros, nunca em adjetivo.** As parcelas
  que somem são as do fim do cronograma, por valor presente: dividir o aporte
  pela parcela daria um número que nunca está certo. R$ 10.000 no CDC eliminam
  **14 parcelas** e **R$ 7.294,62** de juros.

E os dois números que só o dono sabe — saldo de quitação e custo de transporte
sem o carro — são campo na tela, começam vazios, e a tela não finge que sabe.

Branch: `005-dividas-e-simuladores/fase-1-escada` · commits `6ef9bd1` e `0892c0f`.

**Capturas** em `06-capturas/`: `dividas-375.png`, `dividas-1440.png`,
`dividas-dark-1440.png`.

---

## 2. Critérios atendidos

Quinze critérios, executados por um **validador cego**. Veredicto integral em
[`05-veredictos/fase-1.md`](../05-veredictos/fase-1.md).

Ele não aceitou nenhuma conta pronta: **recalculou por fora** a taxa mensal do
imóvel a partir da anual, o valor presente das 45 parcelas, e a simulação de
R$ 10.000 iterando o saldo à taxa do contrato. As três bateram ao centavo.

- [x] `[comando]` RF-01 a RF-04, RF-09 — os quatro tipos, os quatro saldos, as
      duas taxas conhecidas e os seis degraus sem taxa.
- [x] `[comando]` RF-14 a RF-19 — `13 passed`, com os cinco testes exigidos lidos
      no fonte.
- [x] `[comportamental]` RF-06 a RF-08, RF-23 — a escada com 2, o bloco sem taxa
      com 6, na ordem certa.
- [x] `[comportamental]` RF-10 a RF-12 — a taxa gravada sobe o degrau ao topo, a
      inválida é recusada sem gravar, a vazia devolve o degrau ao bloco.
- [x] `[comportamental]` RF-14 a RF-16 — 14 parcelas, R$ 7.294,62.
- [x] `[comportamental]` RF-20 a RF-22 — os dois campos vazios, e o desconto de
      R$ 4.176,36 depois de gravar R$ 35.000,00.
- [x] `[comportamental]` RF-25, RF-24, RF-26, RF-05 — estado vazio, seis medições
      de responsividade e movimento, o link do Resumo, e a carga sem os
      contratos.
- [x] `[comando]` portão local, RF-13/RF-27 e cor — `352 passed`; zero linhas nos
      dois fluxos de saída dos greps.
- [x] `[comportamental]` RF-23 guarda — `302` com `location: /login`.

---

## 3. Como testar à mão

1. Prepare `/tmp/dash-d.sqlite` com `app.ingest` (`DASH_TODAY=2026-09-05`) e `app.auth.seed`.
2. Suba o app e abra `http://127.0.0.1:8000/dividas`.
3. **Esperado:** dois degraus na escada — CDC a 1,63% e imóvel a 0,72% — e seis
   dívidas no bloco "Sem taxa informada".
4. Informe `3,52` na taxa da conta `itau`.
5. **Esperado:** ela sobe ao **topo** da escada, acima do CDC.
6. Simule R$ 10.000,00 no CDC.
7. **Esperado:** 14 parcelas eliminadas e R$ 7.294,62 de juros.
8. Simule qualquer valor num cartão sem taxa.
9. **Esperado:** recusa pedindo a taxa — não `R$ 0,00`.
10. Grave R$ 45.000,00 como saldo de quitação.
11. **Esperado:** **Ágio da quitação**, em vermelho, dizendo que quitar assim
    custa mais que seguir pagando.

---

## 4. Divergências

Nenhuma.

**O código mergeado não é byte a byte o que o validador julgou.** Os oito
apontamentos dele foram corrigidos depois do veredicto, no commit `0892c0f`,
cada um com teste que falha sem a correção, e nenhum deles reprovava critério.
A régua está registrada como `D7`: uma validação por fase. Está dito aqui em vez
de escondido.

---

## 5. Raio de impacto

**Confirmados:**

- `app/migrations/sql/005_debts.sql` — `debts` e `plan_parameters`. A segunda é o
  embrião do `plan_facts` do item `008`.
- `app/debts/ladder.py` — a construção dos degraus, a ordem, e o `parse_rate`.
  **A taxa digitada pelo dono sobrevive ao `rebuild`**: é a única coisa nesta
  tela que nenhuma fonte consegue produzir de novo.
- `app/debts/simulate.py` — parcelas por valor presente e juros evitados.
- `app/routers/debts.py` — as quatro rotas e o `KIND_LABELS`, que é a casa do
  vocabulário de tipo na interface.
- `app/ingest/__main__.py` — a carga passa a reconstruir os degraus.
- `app/routers/render.py` — os filtros `taxa` e `numero`.

---

## 6. Validações de campo pendentes

- **`005-dividas-e-simuladores`** — o saldo de quitação real do CDC só o banco
  informa, e a taxa dos cartões só a fatura. Como verificar: ligar para o banco,
  preencher os campos na tela, e conferir que a escada se reordena e que o ágio
  ou desconto aparece com o sinal certo.

---

## 7. Pendências que viraram roadmap

Nenhuma nova.

- **Ainda não há portão de lint para Python.** Décimo primeiro validador a
  registrar. Segue como `010-lint-e-formatador-python`.
