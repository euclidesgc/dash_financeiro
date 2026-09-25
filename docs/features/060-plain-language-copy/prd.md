# PRD 060 — plain-language-copy

## Valor

Alguns textos do painel falam a língua de quem construiu o sistema, não a do dono. O Resumo antigo, sem nenhuma sincronização, manda rodar um comando de terminal. A Configuração e o Consultor usam o endereço da tela (`/simulador`, `/app/expenses`, `/configuracao`) como texto do link. Os gastos avisam "Sinal só por mês" sem dizer que sinal é esse. A tela de saldos cita a Pluggy sem dizer o que ela é, e mostra "Pedida na tela", "Concluída" e "Nunca atualizado" enquanto cada conta diz "Atualizado em 05/09" — duas datas que parecem se contradizer. Com os textos reescritos, o dono entende cada frase sem saber como o sistema é feito.

## Usuários

O dono do painel, lendo o Resumo, a Configuração, o Consultor, os Gastos, os Saldos e as Conexões.

## Requisitos

- **R1** — O Resumo sem nenhuma sincronização diz para usar o botão da própria tela, sem citar comando de terminal.
- **R2** — Todo link da Configuração e do Consultor que leva a outra tela mostra o nome da tela ("Simulador", "Dívidas", "Configuração", "Gastos do painel novo"), nunca o endereço. O mesmo vale para o texto de ajuda da taxa do cartão, para a recusa da IA sem chave e para o link "Ver em Regras" da correção de categoria.
- **R3** — Nos gastos, fora de um mês inteiro, o aviso diz em frase completa que os avisos de limite por categoria só aparecem com o período de um mês inteiro.
- **R4** — Saldos e Conexões dizem o que é a Pluggy na primeira vez que a citam.
- **R5** — O painel de atualização diz quem pediu a última atualização em linguagem comum ("Você pediu pelo botão “Atualizar agora”", "Feita pela rotina diária"), como ela terminou ("Terminou sem erro") e, sem nenhuma, "Nenhuma atualização feita por este painel ainda".
- **R6** — A data de cada conta diz que é a data informada pelo banco ("Saldo informado pelo banco em 05/09/2026 …"), para não parecer contradizer a data da última atualização do painel.

## Fora de escopo

- Menções a arquivos e variáveis de ambiente fora de link (`data/manual/` em Dívidas, `DASH_CNPJ_LOOKUP` em Beneficiários).
- O identificador de conexão da Pluggy no formulário de Conexões.
- Mudança de layout; o cartão novo da tela de saldos é de outra fatia.

## Pontos em aberto

- nenhum
