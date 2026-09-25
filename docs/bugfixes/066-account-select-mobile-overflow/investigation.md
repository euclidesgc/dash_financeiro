# Investigação: seletor "Conta" passa da tela no celular

## Relato
- **Sintoma:** em 375 px, na tela "Gastos", o seletor "Conta" termina em 382 px e a página rola na horizontal.
- **Esperado:** o seletor cabe na largura disponível; o nome longo de conta é cortado dentro dele.
- **Onde:** `src/features/expenses/components/account-select.tsx`.

## Causa raiz
O `<select>` não tem largura máxima e toma a largura do rótulo mais longo das opções ("nome · instituição (Cartão)"). O bloco que o envolve é item de uma linha flexível dos filtros e, sem `min-width: 0` nem `max-width`, cresce junto com ele. Com as contas da base de teste, isso dá 382 px numa tela de 375.

## Evidência
- `e2e/mobile-layout.spec.ts` espera as contas carregarem na tela "Gastos" e mede a borda direita do seletor: falhava com 382 px contra o limite de 375 (commit do teste antes da correção).

## Correção
- O bloco do seletor recebe `min-w-0 max-w-full` e o `<select>` recebe `max-w-full`: ele continua do tamanho do conteúdo quando há espaço, e para na largura da linha quando não há.

## Fora da correção
Nenhum outro filtro passou da tela na mesma medição.
