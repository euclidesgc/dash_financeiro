## 1. O que foi implementado

**Item:** `008-simulador-e-base-de-fatos` · **Fase:** `1 de 1`

`GET /simulador`: um formulário curto descreve uma decisão e a resposta volta em
**dias** — reais são a entrada, distância é a saída.

Três coisas definem o item:

- **O simulador não tem motor próprio.** Ele injeta o efeito mensal na mesma
  simulação do item `007`. Dois motores discordariam, e o dia em que
  discordassem seria o dia em que o dono precisa acreditar em um deles. O
  critério de integração mede isso: existe **uma** `def simulate` em `app/plan`.
- **Virar "nunca" em data não é uma diferença de dias.** Chamar isso de N dias
  seria inventar uma aritmética sem primeiro termo. A tela diz o que é. E quando
  o resultado vira positivo mas fica **abaixo dos juros da escada**, ela diz
  exatamente isso — R$ 476,79 de sobra contra R$ 638,57 de juros —, em vez de
  repetir "enquanto o resultado for negativo" sobre um número positivo.
- **`plan_facts` guarda o que extrato nenhum tem**, com **validade**: um saldo de
  quitação cotado em setembro não é o de dezembro, e fato vencido é premissa
  silenciosa.

Branch: `008-simulador/fase-1` · commits `d96f17b`, `1a680e4`, `2f8b0c1`.

---

## 2. Critérios atendidos

Treze critérios, **dois validadores cegos**. Veredicto integral em
[`05-veredictos/fase-1.md`](../05-veredictos/fase-1.md).

A primeira rodada reprovou — as capturas foram para o diretório de um item que
não existe — e a caça em volta achou que a tela **multiplicava valores por cem em
silêncio**: `5000.00` virava R$ 500.000,00, aceito, exibido e gravado, com `200`
e sem uma palavra. Numa tela que decide dinheiro, é o pior defeito possível.

O segundo validador varreu a conversão para centavos de `0,00` a `99.999,98` em
passos de sete centavos — 1,4 milhão de valores — contra `Decimal`: **zero
divergências**.

---

## 3. Como testar à mão

1. Abra `http://127.0.0.1:8000/simulador?data=2026-09-05`.
2. Simule uma receita de `5.000,00` com o nome "Vender o carro".
3. **Esperado:** "O resultado mensal passa a ser R$ 476,79, positivo — mas menor
   do que os juros que a escada cobra por mês".
4. Tente `5000.00`.
5. **Esperado:** recusa, dizendo a forma esperada — `1.234,56`.
6. Guarde um fato com validade `2026-08-01`.
7. **Esperado:** ele aparece marcado **vencido**.

---

## 4. Divergências

Nenhuma. Uma reprovação, seis defeitos corrigidos entre as rodadas e três
apontamentos corrigidos depois do segundo veredicto, com teste — todos nomeados
no veredicto.

---

## 5. Raio de impacto

- `app/migrations/sql/008_facts.sql` — `plan_facts` e `scenarios`.
- `app/plan/whatif.py` — a leitura estrita de dinheiro (forma brasileira, teto de
  12 algarismos, centavos de inteiro para inteiro) e o cálculo do impacto.
- `app/plan/timeline.py` — `simulate` ganhou `extra_monthly_cents`,
  `extra_months` e `extra_once_cents`. **É o mesmo motor do `007`.**
- `app/routers/whatif.py`, `app/templates/simulador.html` — a tela.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

Nenhuma nova.
