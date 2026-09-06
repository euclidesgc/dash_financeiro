# Decisões tomadas sem o humano — 002-gastos-tres-eixos

O humano autorizou autonomia para este item em 2026-09-05, no
`product/prompt-da-proxima-sessao.md`. Este arquivo é o que ele lê de manhã:
**uma linha por decisão**, com a alternativa descartada e o porquê. Nada aqui
foi aprovado por ele.

Se alguma decisão estiver errada, todas são reversíveis — o ponto de retorno
limpo para este item é o commit anterior à primeira escrita dele, e o item
`001-base-e-login` continua de pé sem ele.

## Decisões

| # | Estágio ou fase | Decidido | Alternativa descartada | Por quê |
|---|---|---|---|---|
| D1 | discovery | Beneficiário derivado da descrição normalizada, gravado como coluna `payee` por migração nova e preenchido na ingestão | Derivar em tempo de consulta, ou pedir ao dono uma lista de beneficiários | Agrupar pela descrição normalizada reproduz o "top beneficiários" do relatório de origem dígito a dígito (`débito prestação habitacional` = −R$ 12.358,81, em 5 lançamentos). Coluna com índice é o que torna o agrupamento barato; o SQLite não tem regex nativo para fazer isso na consulta. |
| D2 | discovery | Seed de classificação conservador: na dúvida, `importante`, nunca `supérfluo` | Classificar por julgamento próprio o que é supérfluo | O que é supérfluo na casa de alguém não é decisão de quem escreve o código — e o item manda que a classificação seja tabela editável na tela. O seed é ponto de partida declarado; a tela é o lugar de corrigir. |
| D3 | discovery | Trilha rápida, com os quatro gatilhos verdadeiros | — | Régua mecânica e decisão do dono coincidem neste item. |
| D4 | brief | Precedência de regras: expressão sobre a descrição antes de categoria, `id` crescente dentro do tipo, primeira que casa vence | Coluna `priority` explícita, editável na tela | Determinismo é inegociável para o total ser explicável, e uma ordem implícita e simples é menos coisa para o dono entender na tela de Regras. Se a precedência virar problema real, `priority` entra por divergência. |
| D5 | brief | Período padrão da tela de Gastos: os seis meses fechados mais recentes (em 05/09/2026, de 01/03/2026 a 31/08/2026) | Mês corrente | O mês corrente abriria a tela com cinco dias de dado. Os seis meses fechados fazem a primeira carga mostrar o mesmo −R$ 103.772,33 do relatório de origem, o que a torna verificável de olho. |
| D9 | fase 2 | Corrigir a lista de `RF-17` no brief e no plano — ela omitia `Transfer - Bank Slip` (−R$ 5.239,59) e `Transfer - PIX` (−R$ 4.685,15), que por valor ocupam a 6ª e a 8ª posição | Abrir divergência `D-002` e ratificá-la | Não havia opção a decidir: o brief se contradizia sozinho — `RF-19` manda contar PIX e boleto a terceiros como gasto, e `RF-17` os omitia da lista das dez maiores. Erro material com uma única correção possível é reconciliação direta; divergência é para quando existem caminhos com impactos diferentes. |
| D8 | fase 1 | Rótulo em pt-BR por categoria entra no `seed.json` e é exibido pela tela; a chave continua sendo o nome cru da Pluggy | Traduzir na ingestão, trocando o nome da categoria | O nome da Pluggy é o que casa com a fonte a cada sincronização; trocá-lo quebraria o reencontro no item `006`. O rótulo é camada de apresentação, e é lá que a norma de interface em pt-BR se cumpre. |
| D7 | plan | `Não classificado` não ganha regra no seed: os 15 lançamentos caem no fallback e aparecem no balde de resíduo | Cobrir as 77 categorias, inclusive essa | Cobri-la esvaziaria o balde de resíduo no primeiro dia. `Não classificado` é o nome que a consolidação deu ao que ninguém classificou — escondê-lo atrás de uma regra é transformar "não sei" em "sei". |
| D6 | brief | Reclassificar lançamento isolado à mão fica fora do escopo | Permitir exceção por transação | A classificação é tabela justamente para que a correção valha para todos os casos iguais. Exceção por lançamento é a porta pela qual o total deixa de ser explicável. |

## Aprovações registradas em modo autônomo

Cada linha aqui é um `state.py approve --por autonomo` ou um
`diverge-set --por autonomo` que o humano **não** deu.

| Estágio | Documento | O que foi aprovado | Quando |
|---|---|---|---|
| plan | `03-plan.md` | Quatro fases — taxonomia e motor · agregação pelos cinco eixos · tela de Gastos · tela de Regras —, 55 critérios tipados, `criteria-lint` sem aviso e os oito achados do `criteria-auditor` corrigidos antes da aprovação | 2026-09-06 |
| brief | `01-brief.md` | 47 requisitos `RF-01`–`RF-47`: taxonomia em tabela, motor de classificação, agregação pelos cinco eixos, cruzamentos e evolução, tela de Gastos, tela de Regras e a régua de interface | 2026-09-06 |

## O que ficou para o humano

O que a corrida **não** decidiu de propósito.

- **Revisar a classificação inicial das 77 categorias** na tela de regras. O seed
  é conservador de propósito e quase certamente marca como `importante` coisas
  que o dono considera supérfluas — que é exatamente onde mora a lista de corte.
