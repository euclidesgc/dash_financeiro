# Discovery — 029-o-guarda-reconhece-uma-forma-so-de-perguntar-as-horas

**Item do roadmap:** o guarda de rota procura o literal `date.today()`.
`datetime.now().date()`, `datetime.today()` e `from datetime import date as d`
seguido de `d.today()` passam caladas.

**Data:** 08/09/2026 · **Trilha declarada:** rápida

## O terreno

O item `020` fechou a metade da **profundidade**: a varredura desce em subpasta e
chaveia por caminho relativo. Ficou aberta a metade da **forma**: a acusação é
uma busca de texto por uma cadeia, e há pelo menos três outras maneiras de
perguntar as horas que a busca não vê.

O guarda existe porque toda tela deste painel tem de responder pela data de
referência do processo, e não pelo relógio — sem isso, nenhum número é
comparável com os valores congelados do documento de referência.

## Regra, exemplo e pergunta

- **Regra.** O guarda reconhece a chamada ao relógio pela **árvore sintática**, e
  não por texto, então apelido de import e caminho por `datetime` não escapam.
- **Exemplo.** Uma rota escreve `from datetime import date as d` e chama
  `d.today()`. Hoje passa verde; depois deste item, é acusada.
- **Pergunta em aberto:** nenhuma.

## Os quatro gatilhos de trilha completa

Nenhum dispara: sem contrato público, sem segunda frente, sem dado pessoal, e o
requisito é uma frase. **Trilha rápida, uma fase.**

## Decisões autônomas

| Dúvida | Decisão | Alternativa descartada e por quê |
|---|---|---|
| Como reconhecer a chamada? | **Árvore sintática (`ast`)**, resolvendo o que cada nome importado aponta dentro do módulo. | Ampliar a busca de texto para mais cadeias multiplica o falso positivo (um comentário ou uma string passariam a acusar) e continua cega para apelido. |
| O guarda passa a acusar `datetime.now()` sem `.date()`? | **Sim.** Quem pergunta as horas ao relógio numa rota erra igual, com ou sem a conversão. | Distinguir os dois casos ensina a contornar o guarda pela forma que ele não vê. |
| E os testes que legitimamente usam o relógio? | Continuam fora: o guarda varre `app/routers/`, e nada mais. | — |
