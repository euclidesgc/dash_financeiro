# PRD — Buscar categoria na página "Categorias"

## Problema

A página "Categorias" lista cerca de 80 categorias em ordem alfabética, sem busca. Para achar a que tem gasto ou limite, o usuário rola a lista inteira, passando por dezenas que nunca usou.

## O que o usuário ganha

- Um campo "Buscar categoria" acima do catálogo filtra a lista enquanto se digita, sem distinguir acento nem maiúscula ("farmacia" acha "Farmácia").
- As categorias com algum gasto ou com limite mensal aparecem primeiro; as sem uso vêm depois. Cada grupo mantém a ordem alfabética.
- Uma linha acima da lista diz quantas estão em cada grupo.
- Sem resultado, a tela diz o termo buscado e sugere conferir a grafia ou criar a categoria.
- "Limpar" apaga a busca e volta a lista inteira.

## Fora desta fatia

O seletor de troca de categoria na tela "Gastos" (lista de 78 opções sem busca, `Esc` devolvendo o foco ao topo, etiqueta que não parece editável) fica para um item novo do roadmap.

## Critérios de aceite

- Digitar parte do nome, com ou sem acento, mostra só as categorias cujo nome contém o termo.
- Sem busca, as categorias com gasto ou limite vêm antes das demais.
- Definir um limite numa categoria sem uso não fecha nem perde a linha que está sendo editada.
