# PRD 014 — sinal do mês

## Valor

O dono do painel vê, sem fazer conta de cabeça, se o total gasto no mês está dentro do teto que o plano de recuperação exige, a tempo de reagir antes de fechar o mês estourado.

## Usuários

O único usuário do painel, dono das contas, na página "Gastos", com o filtro em um mês fechado (fatia 005), olhando o resumo "N gastos · R$ X no período".

## Requisitos

- **R1** — Na página "Gastos", quando o filtro de período é exatamente um mês fechado, o usuário vê um bloco "Teto do mês" com o total gasto no mês contra o teto definido: "R$ gasto de R$ teto · NN%".
- **R2** — O bloco mostra um selo: "Dentro" (verde) quando o gasto é menor ou igual ao teto, "Atenção" (âmbar) quando está entre 80% e 100% do teto, "Acima" (vermelho) quando ultrapassa o teto.
- **R3** — O bloco mostra também, por extenso, quanto ainda cabe ou quanto já passou: "Sobram R$ X" quando dentro do teto, "Passou R$ X" quando acima.
- **R4** — O teto mensal é um valor editável pelo usuário diretamente no bloco "Teto do mês" (campo "Teto mensal"), sem navegar para outra página.
- **R5** — Salvar um novo teto atualiza o bloco (gasto, porcentagem, selo e valor restante/excedido) sem recarregar a página, e o valor salvo vale para os próximos meses fechados também, até ser trocado de novo.
- **R6** — Sem teto definido, o bloco não mostra selo nem porcentagem; em vez disso convida o usuário a definir um teto, com o campo de edição já visível.
- **R7** — Fora de um mês fechado (intervalo de datas ou todo o período), o bloco "Teto do mês" não aparece.
- **R8** — Trocar o filtro de mês atualiza o bloco (gasto, porcentagem, selo, restante/excedido) junto com o resto da tela, sem ação separada do usuário.
- **R9** — O total gasto, a porcentagem, o selo e o valor restante/excedido são calculados no servidor, nunca no cliente nem por um modelo de IA.

## Fora de escopo

- Projeção de fechamento do mês a partir do ritmo parcial de gastos.
- Alerta ou notificação fora da tela "Gastos".
- Histórico do teto ou comparação entre meses.
- Teto por eixo diferente do total do mês (grupo, categoria, natureza, essencialidade) — isso é o sinal por categoria (fatia 013).
- Proporcionalizar o teto por dias corridos ou mês parcial.

## Pontos em aberto

- nenhum

Premissas registradas: (1) `docs/plano.md` não fixa um único número de "teto mensal de gasto" — fixa déficit (R$ 4.940,72/mês), renda (R$ 9.123 a R$ 13.593) e comprometimento fixo (R$ 6.563,57, 58% da renda), mas nenhum deles é, por si, o teto de gasto total do mês; por isso o teto nasce **vazio**, e o bloco convida o usuário a defini-lo (R6), como qualquer outro fato que só o humano sabe (invariante 26); (2) "mês fechado" é o mesmo filtro de mês único da fatia 005, sem proporcionalização (mesma leitura da fatia 013); (3) o teto é um único valor global (não por mês), editável e persistente, guardado como parâmetro do plano — não como constante no código; (4) o local de edição é inline no próprio bloco "Teto do mês", por ser o caminho mais simples e por já estar no contexto onde o número importa, em vez de uma página "Plano" separada, que ainda não existe.
