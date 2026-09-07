# Discovery — 007-objetivo-e-linha-do-tempo

**Item do roadmap:** `007` — Existe **um objetivo com data**: 6 meses de reserva,
com "resultado mensal ≥ 0" e "dívidas caras zeradas" como marcos no caminho. A
projeção é simulação mês a mês por código determinístico, apresentada em três
cenários, e cada recálculo grava snapshot para a linha do tempo ter passado.

**Data:** 2026-09-07

## História

Como dono deste painel, quero um objetivo com data e o caminho até ele em
marcos, para saber se o que fiz este mês me aproximou ou me afastou — e quanto.

## Regras e exemplos

### R1 — O alvo é derivado, não decretado

- **E1.1** — A reserva é de **6 meses do piso de sobrevivência**, e o piso é o
  cruzamento `fixa × essencial` que o item `002` já calcula: **R$ 6.979,93/mês**
  na base de 05/09/2026. O alvo é **R$ 41.879,58**.
- **E1.2** — O `docs/plano.md` estima ≈R$ 49.400 por outro caminho. A tela
  calcula o seu próprio e diz de onde ele vem, em vez de copiar o do relatório —
  o número muda quando o piso muda, e é isso que se quer.

### R2 — Três cenários, e nenhum é o outro vezes uma porcentagem

- **E2.1** — **conservador**: nada muda. **base**: as assinaturas marcadas "não
  uso mais" caem e a lista de corte é cortada. **otimista**: o do meio mais o
  caixa que os parcelamentos liberam ao acabar.
- **E2.2** — Cada alavanca é dinheiro que o produto **já identificou** e nomeia
  um ato que o dono tem de praticar. Um multiplicador seria palpite vestido de
  plano.
- **E2.3** — Na base de hoje: conservador e base valem **−R$ 4.523,21/mês** (as
  duas alavancas estão zeradas porque o dono ainda não marcou nada), e otimista
  vale **−R$ 4.289,45**, os R$ 233,76 que os parcelamentos liberam.

### R3 — Quando não chega, a tela diz "nunca", não uma data grande

- **E3.1** — Com resultado mensal negativo, **nenhum** cenário alcança o
  objetivo, e o campo de meses fica **nulo** — não um número enorme, que se leria
  como uma data distante.
- **E3.2** — A tela então mostra o único número acionável que sobra: **faltam
  R$ 4.523,21 por mês** para que exista uma data. É esse o número a atacar, não
  o alvo da reserva.

### R4 — O imóvel fica fora do objetivo

- **E4.1** — A 0,72% a.m. ele é a dívida mais barata da escada, e amortizá-lo
  antes de ter reserva é trocar segurança por uma taxa que não está doendo. O
  marco de dívidas mede só o que está **acima de 1% ao mês**.

### R5 — A linha do tempo precisa de passado

- **E5.1** — Cada leitura da tela grava um ponto por cenário, chaveado pela data
  de referência: ler duas vezes no mesmo dia grava um ponto, não dois.
- **E5.2** — Com um ponto só, a tela diz que precisa de duas leituras em datas
  diferentes para mostrar movimento, em vez de desenhar uma reta de um ponto.

## Perguntas em aberto

Nenhuma.

## Trilha

**Trilha: rápida.** Uma fase.
