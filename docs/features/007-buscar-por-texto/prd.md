# PRD 007 — buscar por texto

## Valor

O dono do painel encontra rapidamente um gasto específico digitando parte da descrição ou de quem recebeu, sem precisar rolar a lista inteira.

## Usuários

O único usuário do painel, dono das contas, na página "Gastos", já vendo a lista paginada, ordenável e filtrável por período e conta, querendo localizar um gasto lembrando só de um trecho do nome ou da descrição.

## Requisitos

- **R1** — Na página "Gastos", o usuário vê um campo de texto "Buscar" na barra de controles, junto dos demais filtros.
- **R2** — Digitando um texto, o usuário vê a lista restrita aos gastos cuja descrição ou nome de quem recebeu contenha aquele texto.
- **R3** — A busca não diferencia maiúsculas de minúsculas nem acentos: digitar "acougue" encontra "Açougue".
- **R4** — A busca é aplicada ao pressionar Enter ou automaticamente após uma pequena pausa na digitação (300 ms), sem exigir que o usuário confirme manualmente todas as vezes.
- **R5** — Texto com menos de 2 caracteres não filtra a lista; a lista continua mostrando o resultado dos demais filtros ativos.
- **R6** — O usuário tem um botão ou atalho para limpar o texto buscado e voltar a ver a lista sem esse filtro.
- **R7** — A busca vale para a lista inteira, não só para a página atual: virando de página, o texto buscado se mantém.
- **R8** — O texto buscado fica registrado no endereço da página, de forma que o usuário possa voltar, atualizar ou compartilhar o link e ver a mesma busca.
- **R9** — Ao mudar o texto buscado (de forma que ele passe a filtrar), a lista volta a mostrar a página 1.
- **R10** — A busca convive com a ordenação (fatia 004), o filtro de período (fatia 005) e o filtro de conta (fatia 006): mudar um não reseta os outros.
- **R11** — O resumo da lista mostra a quantidade de gastos e o total em reais considerando a busca junto com os demais filtros ativos.
- **R12** — Se a combinação de filtros e busca não tiver nenhum gasto, o usuário vê a mensagem "Nenhum gasto para esse filtro."
- **R13** — Os estados de carregando e erro (com "Tentar de novo") das fatias 003, 004, 005 e 006 continuam valendo, agora respeitando a busca por texto.

## Fora de escopo

- Agrupar por categoria (fatia 008).
- Editar categoria (fatia 009).
- Buscar por outros campos além de descrição e nome de quem recebeu (por exemplo, valor ou categoria).
- Destacar o trecho encontrado no texto da lista.
- Salvar a busca preferida entre sessões (o padrão é sempre sem busca ao abrir a página sem parâmetro na URL).

## Pontos em aberto

- nenhum
