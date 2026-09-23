# Design do app

Fonte única da aparência. Este arquivo é seu: `/br:init` cria uma vez e nunca sobrescreve. Todo agente que mexe em tela lê antes de decidir qualquer classe, e acrescenta aqui a receita de cada padrão novo. Classes são Tailwind.

## Base

- Fonte: a padrão do projeto. Texto principal `text-gray-900`; secundário `text-gray-600`.
- Espaçamento: escala do Tailwind; entre blocos de uma página, `mt-6`; entre título e texto de apoio, `mt-2`.
- Cor de ação: `blue-600` (hover `blue-700`). Erro: `red`. Sucesso: `green`. Aviso: `amber`.
- Cantos: `rounded-md`; selos `rounded-full`.

## Receitas

| Padrão | Classes |
|---|---|
| Contêiner de página | `<main className="mx-auto max-w-2xl p-8">` |
| Título de página (`h1`) | `text-2xl font-bold` |
| Subtítulo (`h2`) | `mt-8 text-lg font-semibold` |
| Texto de apoio | `mt-2 text-gray-600` |
| Lista | `<ul className="mt-6 divide-y divide-gray-200">`; item `flex items-center justify-between gap-4 py-3` |
| Selo de status | `rounded-full px-2 py-0.5 text-sm` + par de cor (`bg-green-100 text-green-800`, `bg-amber-100 text-amber-800`, `bg-gray-100 text-gray-700`) |
| Botão principal | `rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50 min-h-10` |
| Botão secundário | `rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-900 hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50 min-h-10` |
| Link de navegação | `font-medium text-blue-600 underline-offset-4 hover:underline` |
| Carregando | `<p role="status" className="mt-6 text-gray-600">` |
| Vazio | `<p className="mt-6 rounded-md border border-dashed border-gray-300 p-6 text-center text-gray-600">` |
| Erro | `<div role="alert" className="mt-6 rounded-md border border-red-200 bg-red-50 p-4">`; texto `text-red-800`; botão de erro: o principal com `red-600`/`red-700` |

## Padrões acrescentados pelas entregas

<!-- uma linha por padrão novo: | Padrão | Classes | fatia que criou | -->

| Padrão | Classes | Fatia |
|---|---|---|
| Campo de formulário | `<label className="block text-sm font-medium text-gray-900">` + `<input className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600">`; erro de campo `mt-1 text-sm text-red-700` | 001 |
| Valor monetário | `tabular-nums font-medium`; negativo `text-red-700`; positivo `text-gray-900` | 001 |
| Cabeçalho de app | `<header className="border-b border-gray-200">` com `mx-auto flex max-w-2xl items-center justify-between p-4`; nome do painel à esquerda, ação à direita | 001 |
| Painel de situação | `<section className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-md border border-gray-200 p-4">`; texto à esquerda em `min-w-0`, ação à direita | 002 |
| Selo de erro | par `bg-red-100 text-red-800` para o selo de status | 002 |
| Navegação do cabeçalho | `<nav aria-label="Principal" className="flex items-center gap-4">`; `NavLink` com `text-sm font-medium underline-offset-4 hover:underline`; ativo (`aria-current="page"`) `text-gray-900 underline`; inativo `text-gray-600` | 003 |
| Linha de lançamento | item da receita "Lista" com `items-start`; esquerda `min-w-0 flex-1` empilhando `font-medium truncate` (descrição), `text-sm text-gray-600 truncate` (recebedor, conta); direita `flex shrink-0 flex-col items-end gap-1` com `text-sm text-gray-600 tabular-nums` (data), selo, valor monetário | 003 |
| Paginação | `<nav aria-label="Paginação" className="mt-6 flex flex-wrap items-center justify-between gap-4">`; texto `text-sm text-gray-600`; dois botões secundários | 003 |
| Barra de controles de lista | `<div className="mt-6 flex flex-wrap items-end gap-3">`; cada controle em `flex flex-col gap-1`; `<select>` com as classes do `<input>` da receita "Campo de formulário" mais `min-h-10` (sem `w-full`); botão secundário alinhado pela base | 004 |
| Grupo de período | `<fieldset className="flex flex-col gap-1">` com `<legend className="text-sm font-medium text-gray-900">`; linha `flex flex-wrap items-center gap-2`; texto do mês `min-w-40 text-center text-sm text-gray-900 tabular-nums`; `<input type="date">` com as classes do `<input>` da receita "Campo de formulário" mais `min-h-10` (sem `w-full`) | 005 |
| Tabela de totais | `<table className="mt-3 w-full text-sm">`; `<thead className="sr-only">`; `<tbody className="divide-y divide-gray-200">`; `<tr>` com `<td className="min-w-0 truncate py-2 text-gray-900">` (rótulo), `<td className="whitespace-nowrap py-2 pl-4 text-right text-gray-600 tabular-nums">` (contagem) e `<td className="whitespace-nowrap py-2 pl-4 text-right tabular-nums font-medium text-gray-900">` (total); botão secundário abaixo com `mt-3` | 008 |
