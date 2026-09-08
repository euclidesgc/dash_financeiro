# Discovery — 018-tipagem-estrita-em-python

**Item do roadmap:** `mypy --strict` roda sobre `app`, `financas` e `ingestao`, e
o portão de lint o inclui. Hoje `mypy` não é nem dependência declarada: a skill
de tipagem do pack e a norma 35 do `CLAUDE.md` cobram tipagem que nenhum comando
verifica, e norma que nada mede não governa.

**Data:** 08/09/2026 · **Trilha declarada:** rápida

## A medição, feita antes da escolha

Rodei `mypy --strict` num ambiente à parte, apontando o interpretador do projeto
para que os tipos das bibliotecas resolvessem. **202 erros em 36 arquivos, sobre
86 fontes medidas.**

| Classe | Quantos | O que é |
|---|---|---|
| `type-arg` | 86 | genérico sem parâmetro: `dict`, `list`, `sqlite3.Row` cru |
| `no-untyped-call` | 56 | chamada a função sem anotação — some quando a função ganha tipo |
| `no-untyped-def` | 34 | função sem anotação |
| `no-any-return` | 11 | devolve o que o verificador não sabe |
| resto | 15 | argumento, sobrecarga, anotação de variável, atribuição |

Por pacote: **`app` 126, `ingestao` 79, `financas` 15**.

Sem apontar o interpretador do projeto, o número sobe para 279 — a diferença são
43 importes não resolvidos e 32 decoradores sem tipo, artefato de medir num
ambiente sem as bibliotecas. **O número que vale é 202.**

## A escolha que a medição destrava

O roadmap deixou em aberto: corrigir de uma vez ou tolerar uma baseline
decrescente. **Corrigir de uma vez**, em duas fases.

Três quartos dos erros são de duas classes mecânicas — genérico sem parâmetro e
função sem anotação —, e a terceira maior classe (`no-untyped-call`, 56) some
sozinha quando as funções chamadas ganham tipo. Não é um projeto: é uma varredura.

E baseline decrescente é promessa que ninguém cobra. Este item nasceu porque
existe norma que nada mede; trocá-la por um número que só cai quando alguém se
lembra é reproduzir o problema com outro nome.

## Os quatro gatilhos de trilha completa

Nenhum dispara: sem contrato público, sem segunda frente de stack, sem dado
pessoal, e o requisito é uma linha. **Trilha rápida, duas fases.**

## Decisões autônomas

| Dúvida | Decisão | Alternativa descartada e por quê |
|---|---|---|
| Corrigir tudo ou tolerar baseline? | **Tudo**, em duas fases. | Baseline decrescente é promessa sem cobrança, e o item existe justamente porque norma sem medição não governa. |
| Uma fase ou duas? | **Duas**: primeiro `app` (126 erros), depois `financas` e `ingestao` (94) mais o portão. | Uma fase só produz um diff de 36 arquivos que ninguém revisa de verdade. |
| O portão liga quando? | **Só no fim da fase 2**, com os três pacotes limpos. | Ligar antes deixa o portão vermelho por dívida conhecida, e portão que nasce vermelho é portão que se desliga. |
| `mypy` entra como o quê? | **Dependência de desenvolvimento declarada e travada**, como o `ruff`. | Ferramenta que só existe na máquina de quem rodou não é portão. |
| Qual verificador? | **`mypy`**, que é o que a norma 35 nomeia. | Trocar de verificador junto misturaria duas decisões num item só. |
| Ignorar linha a linha é permitido? | **Não**, exceto com o comentário que nomeia o código do erro **e** a razão, na mesma linha. Ignore mudo é dívida invisível. | — |
