# PRD 009 — ajustar categoria

## Valor

O dono do painel corrige, na hora, a categoria que a Pluggy errou ou não soube dar, sem perder a correção na próxima atualização.

## Usuários

O único usuário do painel, dono das contas, na página "Gastos", olhando a lista ou o bloco "Por categoria" e percebendo que um gasto está na categoria errada.

## Requisitos

- **R1** — Em cada linha da lista de gastos, o selo de categoria é clicável e abre um seletor com todas as categorias existentes, rótulos em pt-BR, incluindo a opção "Sem categoria".
- **R2** — Escolher uma categoria no seletor salva imediatamente, sem botão de confirmação.
- **R3** — Enquanto a troca salva, o usuário vê um indicador de salvando na linha; ao concluir, o selo mostra a nova categoria.
- **R4** — Se a troca falhar, o usuário vê o erro na linha com a opção "Tentar de novo", e a categoria exibida volta a ser a anterior até a nova tentativa ter sucesso.
- **R5** — Depois da troca, a lista de gastos e o bloco "Por categoria" refletem a nova categoria, sem exigir recarregar a página.
- **R6** — Uma categoria trocada manualmente sobrevive à próxima atualização dos registros: reingerir os lançamentos da Pluggy não substitui uma categoria ajustada pelo usuário.
- **R7** — Um gasto com categoria ajustada manualmente mostra uma indicação visual discreta disso (por exemplo, um ponto ou a palavra "manual" junto do selo), diferenciando-o dos gastos com categoria automática.
- **R8** — No seletor de um gasto com categoria manual, o usuário vê a opção "Voltar para a automática", que desfaz o ajuste e volta a exibir a categoria que a Pluggy atribuiu.
- **R9** — Depois de "Voltar para a automática", o gasto volta a receber a categoria da Pluggy nas próximas atualizações, e a indicação de ajuste manual desaparece.

## Fora de escopo

- Criar, renomear ou apagar categorias (fatia 010).
- Aplicar a mesma troca a todos os gastos parecidos de uma vez (fatia 011).
- Limite mensal por categoria (fatia 012).
- Editar a categoria em lote (mais de um gasto por vez).

## Pontos em aberto

- nenhum
