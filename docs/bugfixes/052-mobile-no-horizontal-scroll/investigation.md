# Investigação: telas da SPA rolam na horizontal no celular

## Relato
- **Sintoma:** numa tela de 375 px de largura, "Saldos", "Gastos", "Categorias" e "Conexões" ficam com 410 px de largura: a página rola para o lado e o link "Conexões" do cabeçalho fica cortado na borda direita.
- **Esperado:** toda tela da SPA cabe em 375 px sem rolagem horizontal, com os quatro links do cabeçalho inteiros e visíveis.
- **Como reproduzir:** entrar na SPA com a janela em 375 × 812 e abrir qualquer tela logada; `document.documentElement.scrollWidth` vale 410.
- **Onde:** `src/components/layouts/app-header.tsx`, o cabeçalho comum às telas logadas.

## Causa raiz
O cabeçalho põe o nome do painel e a navegação num grupo `flex` sem quebra de linha (`flex items-center gap-4`), e a própria navegação também não quebra. O grupo exige a soma das larguras de "dash_financeiro" e dos quatro links mais os espaços, cerca de 380 px, que com o `p-4` do cabeçalho passa dos 375 px da tela. O `flex-wrap` do contêiner de fora só consegue mandar o login e o "Sair" para a linha de baixo; o grupo da esquerda, indivisível, estoura a largura e empurra a página para 410 px. A tela de login e a de página não encontrada, que não têm o cabeçalho, já cabiam — o que confirma o cabeçalho como a única origem.

## Evidência
- Teste de regressão (commit `f4a5084`), falha antes da correção: `e2e/mobile-layout.spec.ts`, `every screen fits a 375 px phone without horizontal scroll` — a tela de login passa e a de saldos recebe `scrollWidth` 410 contra 375 de largura.
- Com o cabeçalho corrigido e as verificações da página ainda frouxas (`expect.soft`), nenhuma outra tela nem outro elemento passou da borda direita: o cabeçalho é a causa inteira.

## Correção proposta
- `src/components/layouts/app-header.tsx` — nome do painel, navegação e bloco do usuário passam a ser filhos diretos da linha do cabeçalho. No celular, a navegação ocupa uma segunda linha inteira (`order-last w-full`) e pode quebrar (`flex-wrap`); a partir de `sm` (640 px) volta para a mesma linha, logo depois do nome do painel, empurrando o usuário para a direita (`sm:order-none sm:mr-auto sm:w-auto`). O login ganha `truncate` num bloco `min-w-0`, para um login longo não estourar a linha.
- `docs/design.md` — as receitas "Cabeçalho de app" e "Navegação do cabeçalho" passam a descrever essa forma.
- **Risco:** no celular a navegação aparece abaixo do "Sair" enquanto vem antes dele na ordem do teclado; a ordem de leitura continua a do desktop (nome, navegação, usuário), que é a mesma para leitor de tela.

## Fora da correção
- O teste cobre as telas como elas abrem; estados abertos por interação (formulário de teto, seletor de categoria, confirmação em linha) não são medidos em 375 px, e na revisão nenhum deles estourou a largura.

## Pontos em aberto
Nenhum.
