# Investigação: formulário do teto abre sozinho e puxa o foco

## Relato
- **Sintoma:** num mês sem teto, o bloco "Teto do mês" já carrega com o formulário "Teto mensal (R$)" aberto e o campo com o foco. Quem navega pelo teclado com "Mês anterior" e "Próximo mês" perde o lugar, e quem começa a digitar a data do período antes do carregamento perde as teclas no campo do teto. Desde a 054, "Gastos" abre no mês corrente, então isso acontece toda vez que a tela abre num mês sem teto.
- **Esperado:** o formulário só abre quando a pessoa toca em "Definir teto"; ao abrir por ela, o campo recebe o foco.
- **Como reproduzir:** sem teto definido, abrir "Gastos" e olhar onde está o foco.
- **Onde:** `src/features/expenses/components/month-ceiling.tsx` (bloco do teto), `src/features/expenses/components/ceiling-form.tsx` (formulário).

## Causa raiz
O bloco calculava "formulário aberto" como `editing || (sem teto && não dispensado)`: sem teto, o formulário nascia aberto sem ação de ninguém. O campo do formulário tem `autoFocus`, correto quando a pessoa abre o formulário, mas que, com a abertura automática, puxava o foco no carregamento da página.

## Evidência
- `src/features/expenses/components/__tests__/month-ceiling.test.tsx`:
  - `without a ceiling shows the invitation with the form closed, no stolen focus, no badge and no percentage` — antes da correção, não há botão "Definir teto do mês" e o campo "Teto mensal (R$)" está na tela;
  - `"Definir teto" opens the empty form focused and "Cancelar" closes it again` — antes da correção, falha ao procurar o botão "Definir teto do mês".

## Correção
- `month-ceiling.tsx` — o formulário abre só pelo estado `editing`, ligado por "Definir teto" ou "Alterar teto"; some o estado "dispensado", que só existia para fechar a abertura automática.
- O `autoFocus` do campo fica: ele só roda quando o formulário é aberto pela pessoa.
- `e2e/expenses.spec.ts` — as duas jornadas que esperavam o campo focado no carregamento passam a esperar o botão "Definir teto do mês" e, na do teto, abrem o formulário por ele.

## Pontos em aberto
Nenhum.
