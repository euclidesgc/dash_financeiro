# Investigação: datas "De" e "Até" digitadas pelo teclado não filtram os gastos

## Relato
- **Sintoma:** na tela de gastos, digitar a data nos campos "De" e "Até" pelo teclado (dd/mm/aaaa) apaga o que já estava no campo a cada tecla, o outro campo some, e o filtro termina sem o período digitado. Só escolher o dia no calendário funciona. Quando o "Até" fica antes do "De", o "De" desaparece sem nenhuma mensagem.
- **Esperado:** a data digitada filtra a lista assim que fica completa; o campo que a pessoa não mexeu continua como estava; "Até" antes de "De" mostra uma mensagem e não muda o filtro.
- **Como reproduzir:** abrir "Gastos", ir para um mês (os dois campos ficam preenchidos), clicar no dia do campo "De" e digitar `01092026`, depois o mesmo no "Até" com `02092026`. A URL termina em `?to=2026-09-02`, sem o "De".
- **Onde:** `src/features/expenses/components/period-controls.tsx` (os dois `<input type="date">` controlados pela URL) e `handleRangeChange` em `src/features/expenses/components/expenses-list.tsx`.

## Causa raiz
Os dois campos gravam na URL **cada** evento de digitação do campo de data do navegador, e o Chrome emite, no meio da digitação, valores que não são a data que a pessoa quer:

1. **Segmento pela metade vira "campo vazio".** Ao digitar o primeiro algarismo de um segmento já preenchido (o `0` de `01`), o campo fica incompleto e o navegador entrega o valor `""`. O app trata `""` como "a pessoa apagou a data", tira o limite da URL e devolve `""` ao campo controlado — e escrever `""` num campo de data zera dia, mês e ano de uma vez.
2. **Ano pela metade é data válida.** Digitar `2026` no ano passa por `0002-09-02`, `0020-09-02` e `0202-09-02`, todas datas válidas para o navegador e para `readIsoDate`. Cada uma vai para a URL (e para a API).
3. **Intervalo invertido descarta o outro campo em silêncio.** `handleRangeChange` resolve "Até antes de De" apagando o outro limite. Com o ano intermediário `0002`, o "Até" fica sempre antes do "De" durante a digitação, e o "De" some; com um "Até" completo e realmente anterior, o "De" some sem mensagem.

## Evidência
- Teste de regressão (commit `56ed6dd`): `e2e/expenses.spec.ts`, bloco `typing the dates by keyboard`. `filters the expenses by a range typed by keyboard in both fields` termina em `?to=2026-09-02`, quando o esperado é `from=2026-09-01&to=2026-09-02`; `keeps "De" and says why when "Até" is typed before it` cobre a mensagem.
- Rastro tecla a tecla no Chromium (pt-BR): no campo preenchido, o `0` do dia dispara `input` com valor `""` e a URL perde o limite; no ano, a URL passa por `to=0002-09-02`, `to=0020-09-02`, `to=0202-09-02`, e o `from` já tinha sumido no `0002`.
- O teste de componente não pega o defeito: o jsdom não tem os segmentos do campo de data, e o `userEvent.type` só entrega a data quando ela fica inteira.

## Correção proposta
- `src/features/expenses/components/period-controls.tsx` — cada campo passa a ter um rascunho local com o que está escrito nele. O campo só avisa a lista quando o intervalo está pronto: as duas datas completas ou vazias e o "Até" não antes do "De". Enquanto isso, o rascunho segue a digitação sem ser sobrescrito. Quando o período muda por fora (botões de mês, "Todo o período", URL), o rascunho volta ao período da URL.
  - Campo vazio **com** `validity.badInput` é segmento pela metade, não data apagada.
  - Data com ano abaixo de 1000 é ano pela metade (não há gasto antes disso).
  - "Até" antes de "De" mostra `"Até" não pode ser antes de "De".` abaixo dos campos, marca os dois como inválidos e não muda o filtro.
- `src/features/expenses/utils/period.ts` — `readTypedDate`, a regra de "data completa" (data válida com ano de 1000 em diante).
- `src/features/expenses/components/expenses-list.tsx` — `onRangeChange(from, to)` recebe o intervalo inteiro e grava; a regra "o campo editado vence" sai.
- **Risco:** escolher no calendário continua aplicando na hora, porque entrega a data completa. Digitar um dia completo num campo já preenchido aplica o filtro já com esse dia (ex.: `20/09` antes de terminar de trocar o mês): o filtro acompanha cada data completa, como já acontece hoje.

## Fora da correção
- Num mês sem teto, o formulário "Teto mensal (R$)" abre sozinho e puxa o foco quando carrega; quem já estava digitando a data perde as teclas seguintes, e quem troca de mês pelo teclado perde o lugar. Registrado no roadmap como item 064 (`ceiling-form-no-autofocus`); o teste e2e espera esse foco antes de digitar.

## Pontos em aberto
Nenhum.
