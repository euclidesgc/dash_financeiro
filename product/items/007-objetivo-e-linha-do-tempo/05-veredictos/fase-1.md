# Veredicto — item `007-objetivo-e-linha-do-tempo`, fase 1

**Resultado:** `APROVADO` (terceira rodada). As duas primeiras devolveram
`REPROVADO`, e a fase **escalou** — o diagnóstico está registrado em `D8`.

Branch: `007-objetivo/fase-1-linha-do-tempo` · base `475c944` · ponta julgada `1295a5c`
Data: 2026-09-07 · Três validadores cegos, agentes novos.

> Um defeito latente encontrado nesta terceira rodada foi corrigido depois do
> veredicto, com teste. Está nomeado abaixo.

## As duas reprovações, e o que elas acharam

**Primeira.** Um critério não cumprido — o teste do mês negativo afirmava dois
dos três marcos. Pequeno. Mas a caça em volta achou **onze** coisas, das quais
quatro mexiam na data que esta tela existe para dar:

- `?data=0001-01-01` é ISO válido, passava a guarda e estourava doze meses antes
  em aritmética de calendário: **HTTP 500**.
- Um mês cuja sobra dava exatamente zero alimentava a reserva com o mês inteiro,
  creditando um mês que foi todo para a dívida.
- Escada já limpa era reportada como limpa no mês **1**, não no mês 0.
- O cenário otimista aplicava o caixa liberado desde o mês 1, enquanto o próprio
  rótulo diz "ao acabar".

Mais três em que a tela dizia algo falso: *"enquanto o resultado for negativo"*
impresso sobre um resultado positivo com *"faltam R$ 0,00"* ao lado; a escada do
objetivo ignorando em silêncio as **seis** dívidas sem taxa, R$ 27.934,80 de
dívida real; e a linha do tempo comparando projeções contra uma reserva alvo que
se move com a janela de seis meses, sem mostrá-la.

**Segunda.** A correção de um requisito quebrou o outro. `RF-05` cobrava o
otimista em `−R$ 4.289,45`; `RF-16`, escrito depois da primeira reprovação,
mandava o caixa liberado chegar só no mês de término. Com o resultado partindo
negativo, o laço quebrava no mês 1 e o dinheiro nunca chegava.

**Diagnóstico da escalada: `criterio`.** Os dois requisitos estão certos e falam
de coisas diferentes. O **número de cabeçalho** é o estado estacionário que o
cenário promete, todas as alavancas puxadas; a **simulação** é o caminho até ele,
escalonado por mês. Separados, os dois passam — e o laço só desiste quando não há
mais alavanca agendada à frente, o que antes fazia a tela dizer "nunca" para um
caso em que a data existe.

## Portões (terceira rodada)

| Portão | Resultado |
|---|---|
| lint | **OK** — `All checks passed!`, `EXIT=0`. |
| testes | **OK** — `376 passed`, `EXIT=0`. |
| gates | **OK** — `✓ gates: limpos (288 arquivo(s)).` |

## Critérios — os catorze cumpridos

- [x] **RF-01, RF-02, RF-05, RF-13** — `data-alvo="4187958"`, `R$ 41.879,58`,
      piso `R$ 6.979,93`, e o rótulo do cruzamento vindo da tabela. O validador
      conferiu à mão: `697993 × 6 = 4187958`.
- [x] **RF-03, RF-04, RF-05** — três cenários, extraídos com **parser HTML e não
      regex**, na ordem certa, com `-452321`, `-452321`, `-428945`, monotônicos.
- [x] **RF-08, RF-09, RF-10** — os três `data-meses` vazios, `Nenhum cenário
      chega ao objetivo.`, `R$ 4.523,21`, e os três marcos com `não chega`.
- [x] **RF-11, RF-12** — quatro leituras, dois pontos.
- [x] **RF-06, RF-07** — `9 passed`. O validador leu os sete testes e checou que
      **não são vacuosos** — em particular que o imóvel do teste entra a 200 bp,
      acima do corte de 100, para que o que o exclua seja a guarda de tipo e não
      a comparação de taxa.
- [x] **RF-15, RF-20, RF-18** — `?data=0001-01-01` → `200`, e mais oito datas
      absurdas, todas `200`, com zero `Traceback` no log. O bloco
      `id="sem-taxa-aviso"` traz `6 dívida(s)` e `−R$ 27.934,80`, conferidos
      contra o banco.
- [x] **RF-16, RF-17, RF-19, RF-22** — nenhum `* 30` nos templates;
      `released_by_month` citado duas vezes.
- [x] **RF-21** — dois `data-alvo` na linha do tempo, `4187958` e `3530196`,
      **diferentes entre si**.
- [x] **RF-14** — seis medições, `scrollWidth <= innerWidth` em todas, e os 37
      elementos de `#cenarios *` com duração zero. As três capturas, abertas e
      conferidas.
- [x] **portão local, lint, RF-14 grep, guarda** — `376 passed`,
      `All checks passed!`, zero linhas nos dois fluxos, `302` sem sessão.

## Apontamentos da terceira rodada

1. **Mina do mês 0 — corrigida depois do veredicto, com teste.**
   `released_by_month` usava `max(ahead, 0)`, então uma parcela terminando **no
   mês da leitura** virava `when == 0`; `base_result` a subtraía do ponto de
   partida, mas o laço começa no mês 1 e nunca a devolvia. Medido pelo
   validador: cabeçalho anunciando `R$ 500,00/mês` de sobra e, ao lado, "não
   chega". Não disparava nos dados de hoje — o caixa liberado cai nos meses 3,
   15 e 21 — mas era uma mina armada para a primeira parcela a terminar no mês
   da leitura. É exatamente a inconsistência entre cabeçalho e caminho que esta
   fase existe para resolver.
2. **O cenário `base` promete dois atos e entrega o número do `nada muda`**,
   porque hoje não há assinatura marcada nem lista de corte. O número está
   certo; a tela não diz que as duas listas estão vazias.
3. **Data recusada grava ponto.** `_reference` cai em `date.today()` e a leitura
   grava: um erro de digitação na URL injeta um ponto na série de progresso, sem
   como distingui-lo depois de uma leitura legítima.

Os dois últimos vão para o roadmap.
