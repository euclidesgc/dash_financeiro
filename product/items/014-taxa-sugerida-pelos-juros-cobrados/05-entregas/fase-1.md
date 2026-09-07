## 1. O que foi implementado

**Item:** `014-taxa-sugerida-pelos-juros-cobrados` · **Fase:** `1 de 1`

**Origem: o dono perguntou se o painel não consegue descobrir as taxas sozinho.**
A resposta medida é **sim para o cheque especial, não para o cartão** — e o
porquê do "não" é a metade que interessa.

Os juros cobrados estão na base. O que não está é o saldo diário sobre o qual o
banco cobra — mas ele é **reconstruível**, andando do saldo de hoje para trás
pelos lançamentos. Dividindo o juro do mês pelo saldo médio dos **dias
negativos**, e casando cada cobrança com o mês que ela **remunera**:

| Conta | Sugestão | Faixa | Meses |
|---|---|---|---|
| `itau` | **6,71% a.m.** | 4,58% – 9,84% | 7 |
| `CAIXA` | **8,00% a.m.** | 7,99% – 8,16% | 3 |

**Cartão não recebe sugestão**, e não por falta de dado: o saldo de um cartão é
**fatura**, não dívida rotativa, e fatura paga inteira não cobra juro nenhum. Os
encargos pequenos que aparecem não são rotativo sobre o saldo — dividi-los pelo
saldo daria 0,06% ao mês, um número falso numa tela que decide onde o próximo
real vai.

**Sugestão, nunca fato.** O campo vem preenchido, a legenda diz de onde o número
veio e sobre quantos meses, a faixa fica ao lado, e nada é gravado sem o dono
salvar.

Branch: `014-taxa-sugerida/fase-1`, integrada em `develop` · commits `2500ddc`,
`ef1b928`, `729ad39` e `fd0ea0e`.

---

## 2. Critérios atendidos

Dez critérios, **três validadores cegos**. Veredicto integral, com o que cada
rodada derrubou, em [`05-veredictos/fase-1.md`](../05-veredictos/fase-1.md).

As três aprovaram — e as três acharam que o número ainda era ruído. **A sugestão
foi de 4,22% para 6,71%, e a faixa da `CAIXA` de cinco pontos percentuais para
dezessete pontos-base.** A diferença entre as duas coisas é que a segunda parece
uma taxa contratada e a primeira parecia dispersão do banco, quando era artefato
do meu alinhamento.

O terceiro validador **não aceitou o número pela saída do módulo**: refez a
atribuição com implementação independente e auditou os 17 lançamentos de juros um
a um — nenhum no mês errado, nenhum órfão.

---

## 3. Como testar à mão

1. Prepare `/tmp/dash-t.sqlite` com `app.ingest` (`DASH_TODAY=2026-09-05`).
2. Abra `/dividas` e role até **Sem taxa informada**.
3. **Esperado:** o campo do `itau` preenchido com `6,71` e a legenda "Sugestão:
   6,71%. Para cada um de 7 meses… Variou de 4,58% a 9,84%".
4. Olhe as quatro linhas de cartão.
5. **Esperado:** campo vazio, sem sugestão, e o parágrafo explicando por quê.
6. Sem salvar nada, consulte `select count(*) from debts where monthly_rate_bp is
   not null`.
7. **Esperado:** `2` — as duas dívidas de contrato. A sugestão não virou fato.

---

## 4. Divergências

Nenhuma. Três rodadas de validação, todas aprovando, e dez correções entre elas —
todas nomeadas no veredicto. Os números dos critérios mudaram depois do terceiro
veredicto por causa da última correção, e isso está dito no veredicto.

---

## 5. Raio de impacto

- `app/debts/observed.py` — **novo**. A reconstrução do saldo diário, a decisão
  de atraso **por conta**, o piso de saldo, o descarte do mês em curso e do mês
  parcial contra o calendário, e a mediana com a faixa.
- `app/routers/debts.py`, `app/templates/dividas.html` — o campo preenchido, a
  legenda que descreve a conta que o código faz, e o parágrafo do cartão.

---

## 6. Validações de campo pendentes

- **`014`** — a taxa contratada do cheque especial só o extrato confirma. A
  sugestão é estimativa declarada; confirmar é ato do dono. Como verificar:
  comparar 6,71% e 8,00% com o que o extrato do mês diz.

---

## 7. Pendências que viraram roadmap

- **`posts_in_arrears` decide uma vez por conta.** Numa conta de dias irregulares
  — `[1, 1, 28, 28]`, mediana 14 — a decisão erraria metade dos lançamentos. Não
  afeta esta base, cujas medianas são 6 e 1,5 contra o corte de 10. Fica como
  limitação conhecida da regra, registrada aqui e no veredicto, sem item próprio:
  corrigi-la exigiria um histórico que três ou quatro lançamentos não sustentam.
