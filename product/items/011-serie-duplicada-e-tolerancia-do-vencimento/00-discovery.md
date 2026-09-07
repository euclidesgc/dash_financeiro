# Discovery — 011-serie-duplicada-e-tolerancia-do-vencimento

**Item do roadmap:** `011` — Integridade das séries: nenhum compromisso contado
duas vezes, nenhuma parcela partida por centavo, e a previsão só apagada pelo
lançamento que de fato a realiza.

**Data:** 2026-09-06

## INVEST

| Critério | Passa | Observação |
|---|---|---|
| Independente | sim | Depende só do `003`, concluído. Não depende de nada que ainda não exista. |
| Negociável | sim | Fixo: os três defeitos e o total corrigido. Conversável: a tolerância que separa duas compras de uma compra com centavo diferente, e a tolerância que separa a cobrança do mês da cobrança de outro evento. |
| Valioso | sim | O `004` projeta saldo dia a dia somando estes compromissos datados. Projetar sobre R$ 368,61/mês de dívida que já acabou é errar a tela principal em toda leitura. |
| Estimável | sim | Uma fase. Três correções no mesmo pacote `app/commitments/`, medidas pela mesma base. |
| Pequeno | sim | Nenhum arquivo novo de produto, nenhuma migração, nenhuma tela nova. |
| Testável | sim | Todo número sai de consulta sobre a base de 05/09/2026, e os três defeitos têm caso nomeado nos dados reais. |

**Veredicto do INVEST:** segue como está.

## História

Como dono deste painel, quero que o comprometido conte cada dívida uma vez só e
que o calendário não esconda vencimento nem invente vencimento, para que a
projeção de saldo do `004` nasça sobre um número que eu possa acreditar.

## Regras e exemplos

### R1 — Parcelamento que acabou não vira assinatura

- **E1.1** — `jim com` fechou na parcela **6 de 6** em **08/09/2026**. Não deve
  mais nada. Mas o motor mantém **também** uma linha recorrente de −R$ 136,44,
  que é a média das mesmas seis cobranças, e o calendário prevê −R$ 136,44 em
  **06/10/2026** para uma dívida encerrada.
- **E1.2** — A causa está em `engine.recurring_after_precedence`: a precedência
  do parcelamento sobre a recorrência só vale enquanto o parcelamento tem
  `installments_left > 0`. No mês em que a última parcela cai, a série deixa de
  ser "viva", a precedência solta, e a linha recorrente ressuscita o dinheiro.
- **E1.3** — São **quatro** chaves, não uma: `cp amigao macae` (−R$ 36,55),
  `jim com` (−R$ 136,44), `mercadolivre merca` (−R$ 57,32) e
  `mercadolivre prod` (−R$ 138,30), somando **R$ 368,61/mês** de dívida
  encerrada tratada como assinatura viva.
- **E1.4** — A regra certa é a que o `001` já escreveu: parcelamento tem fim,
  recorrência não, e cada lançamento entra uma vez só. Se a chave foi cobrada
  como parcelamento dentro da janela de vida, é parcelamento — tendo ou não
  parcela a vencer. Um parcelamento cobrado há seis meses e uma assinatura viva
  hoje continuam sendo coisas diferentes, porque a janela de vida os separa.

### R2 — Uma compra é uma série, e um centavo não a parte em duas

- **E2.1** — A base tem **66** compras parceladas distintas por `(beneficiário,
  número de parcelas)`. O motor grava **96** séries, porque a chave inclui o
  valor exato da parcela e a primeira parcela quase sempre difere das demais por
  arredondamento.
- **E2.2** — `jim com`, total 6: as parcelas valem R$ 136,47 e R$ 136,43 — quatro
  centavos de diferença, **0,03%**. Viram duas séries: uma com
  `1/6, restam 5, vista em 02/03/2026`, e outra com `6/6, restam 0, vista em
  08/09/2026`. A primeira é um fantasma que "deve" cinco parcelas de uma compra
  já quitada.
- **E2.3** — Em **24 dos 66** grupos há mais de um valor. Em 23 deles o desvio
  relativo é de 0,01% a 0,14%. O único caso legítimo é
  `htm neg cursos tre`, total 12, com valores de R$ 27,07 e R$ 49,60 — desvio de
  **45,4%** e 24 ocorrências: são **duas** compras de 12 parcelas na mesma loja,
  e elas precisam continuar separadas.
- **E2.4** — Por isso a chave não pode ser o valor exato nem só o par
  `(beneficiário, parcelas)`. Ela agrupa por `(beneficiário, parcelas)` e separa
  dentro do grupo quando o valor foge de uma tolerância relativa. O que hoje
  salva a tela do fantasma é a janela de vida, que esconde a série velha — mas
  esconder o sintoma não é corrigir a causa, e é a janela que carrega o peso
  sozinha.

### R3 — A previsão é substituída pelo lançamento que a realiza, não pelo mês

- **E3.1** — `app/commitments/calendar.py` casa lançamento com previsão pela
  chave `(série, AAAA-MM)`. Qualquer cobrança futura já lançada apaga a previsão
  do mês inteiro daquela série.
- **E3.2** — Hoje o dano é zero: um único lançamento casou dentro da janela de
  45 dias, e ele está a **dois dias** do dia previsto — `jim com`, previsto dia 6
  pela mediana, lançado em 08/09/2026.
- **E3.3** — O risco é o inverso do que a chave por mês evita. Uma cobrança
  avulsa lançada no dia 5 esconderia o vencimento previsto para o dia 25 da mesma
  série, e o dono veria um mês mais leve do que ele é. A correção é uma
  tolerância em dias em torno do dia previsto — não a volta à comparação exata,
  que reabriria o dinheiro em dobro que a chave por mês existe para evitar.

### R4 — Vivo é o que ainda vai sair, e data futura não é passado

- **E4.1** — O total comprometido soma **todas** as séries recorrentes, cobradas
  recentemente ou não. Entram nele R$ 4.266,18/mês de assinaturas que pararam:
  `pagamento de pix qr code mercado pago…` visto pela última vez em 28/12/2025,
  `g orengo mot ct to` em 06/02/2026, `pg hack one hackone` em 29/05/2026. O
  invariante que o `003` escreveu para parcelamento — série morta não é
  compromisso — vale igual para assinatura, e a tela já mostra a marca de viva ou
  não em cada linha. Só o total não a usa.
- **E4.2** — A janela de vida é hoje um **conjunto de dois meses** (o corrente e
  o anterior). Isso marca como morto o que está no **futuro**: fatura de cartão
  chega com parcela lançada meses adiante, e `otica bardasson e`, com cobrança
  datada em 10/02/2027, é lida como série que parou. São **10** séries nessa
  situação.
- **E4.3** — A janela certa é um **piso de data**, não um conjunto: viva é a
  série cuja última cobrança não é anterior ao primeiro dia do mês passado. O
  passado remoto sai, o futuro entra, e a regra encolhe em vez de crescer.
- **E4.4** — Com os quatro defeitos corrigidos, o comprometido da base de
  05/09/2026 passa de **−R$ 12.802,64** para **−R$ 9.553,00**, o caixa liberado
  pelos parcelamentos passa de R$ 374,82 para **R$ 233,76/mês**, e as linhas
  gravadas caem de 151 para **125**. As três assinaturas canceláveis continuam
  devolvendo exatamente **R$ 1.099,63/mês**.

### R5 — Corrigir número congelado é reconciliar documento, não deixar cicatriz

- **E5.1** — `−R$ 12.802,64`, `R$ 374,82`, `6 parcelamentos vivos` e
  `96 séries` aparecem no `00-discovery.md`, no `01-brief.md` e no `03-plan.md`
  do `003`, e em critérios já aprovados. Todos mudam. A reconciliação é no mesmo
  PR da mudança, reescrita no presente, com âncora de uma linha para este item.
- **E5.2** — `docs/plano.md` é o documento de números congelados de 05/09/2026 e
  não muda: ele não afirma nada sobre séries de compromisso, que são construção
  deste projeto e não do relatório de origem.

## Perguntas em aberto

Nenhuma.

Três dúvidas técnicas, todas de limiar numérico, todas registradas em
`decisoes-autonomas.md`: quanto de desvio relativo ainda é a mesma compra,
quantos dias de distância ainda são a mesma cobrança, e onde fica o piso da
janela de vida. Nenhuma é pergunta para o dono — são parâmetros do modelo,
mensuráveis contra a base, e não fatos que só ele sabe.

A pergunta que **seria** dele — *"qual desses R$ 4.266,18 você ainda paga?"* —
já é mecanismo do produto: a tela lista toda assinatura, marca a que parou de
ser cobrada, e a ação "não uso mais" é dele.

## Trilha

**Trilha: rápida.**

| Gatilho | Verdadeiro | Evidência |
|---|---|---|
| Zero perguntas em aberto | sim | Nenhuma sobrou. |
| Uma stack só | sim | Python 3.12; o item não toca template nem folha de estilo. |
| Sem mudança de contrato | sim | Nenhum OpenAPI, nenhum consumidor externo, nenhuma coluna nova. |
| Sem dependência nova | sim | Nada entra no `pyproject.toml`. |
