# PRD 056 — spa-legacy-navigation

## Problema

O painel novo (Saldos, Gastos, Categorias, Conexões) e o painel antigo (Resumo, Objetivo, Dívidas, Simulador, Consultor, Configuração e demais) não se ligam. Quem entra pelo painel novo não chega ao plano de saída do déficit, que só existe no antigo, e quem está no antigo não encontra as telas novas.

## Requisitos

- R1 — O cabeçalho do painel novo tem "Mais telas", que abre links para Resumo, Objetivo, Dívidas, Simulador, Consultor e Configuração do painel antigo.
- R2 — O menu do painel antigo tem o grupo "Painel novo", com links para Saldos, Gastos, Categorias e Conexões.
- R3 — Em um celular de 375 px, nenhuma tela ganha rolagem horizontal, com "Mais telas" aberto ou fechado.

## Fora do escopo

Migrar qualquer tela antiga para o painel novo.
