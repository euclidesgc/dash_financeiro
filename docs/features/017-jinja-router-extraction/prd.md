# PRD 017 — jinja-router-extraction

## Valor

As telas antigas do painel (resumo, gastos por grupo, regras, configuração e comprometido) fazem as próprias contas dentro do código que só deveria atender a página. Quando uma dessas telas passa para a interface nova, a pergunta que ela responde ("quanto sobrou sem regra", "quais grupos existem", "esse recebedor já apareceu") precisa ser escrita de novo, e duas versões da mesma conta divergem sem ninguém ver. Com as consultas num lugar só, a tela nova reaproveita a mesma resposta que a antiga já dá, e o número do painel não muda de uma tela para outra.

## Usuários

O único usuário do painel, dono das contas. Ele não vê diferença nas telas; ganha a garantia de que a migração de cada tela antiga para a nova interface mostra os mesmos números.

## Requisitos

- **R1** — As cinco telas antigas mostram exatamente o que mostram hoje: mesmos números, mesmas listas, mesmas mensagens, mesmos códigos de resposta.
- **R2** — Cada pergunta que essas telas fazem à base existe uma vez só, num lugar que a interface nova também pode usar; a lista de grupos, naturezas e essencialidades, repetida hoje em duas telas, passa a ser uma.
- **R3** — "O que ficou sem regra" é a mesma conta na tela de regras (a base inteira) e na de gastos por grupo (o período escolhido).
- **R4** — Dispensar e retomar uma assinatura na tela de comprometido continua gravando na hora e sobrevivendo ao recarregar a página.
- **R5** — Se alguém voltar a escrever uma consulta ou uma gravação direto no código de uma tela, a verificação automática do projeto recusa a mudança.

## Fora de escopo

- Migrar qualquer tela antiga para a nova interface.
- Mudar texto, layout ou comportamento de qualquer tela.
- Rótulos de categoria lidos do banco nas telas antigas (item próprio do roadmap).

## Pontos em aberto

- nenhum
