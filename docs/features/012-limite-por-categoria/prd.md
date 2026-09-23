# PRD 012 — limite por categoria

## Valor

O dono do painel registra, para cada categoria, quanto pretende gastar por mês — o parâmetro que só ele sabe e que o painel não pode inventar — preparando a base para o sinal de dentro/acima do limite (fatia 013).

## Usuários

O único usuário do painel, dono das contas, na página "Categorias", já com o catálogo criado (fatia 010), querendo dizer quanto pode gastar em cada categoria por mês.

## Requisitos

- **R1** — Na página "Categorias", cada linha da lista ganha um campo "Limite mensal" em reais, editável direto na linha, sem abrir outra tela.
- **R2** — O campo é opcional: vazio significa que a categoria não tem limite definido.
- **R3** — O usuário confirma o valor digitado apertando Enter ou um botão de salvar da própria linha; o valor não salva a cada tecla.
- **R4** — Enquanto o valor está sendo salvo, o usuário vê um indicador de salvando na linha.
- **R5** — Se salvar falhar, o usuário vê o erro na linha e o valor anterior permanece (na tela e no catálogo).
- **R6** — Depois de salvo, a linha passa a mostrar o limite no formato "Limite: R$ X"; sem limite definido, mostra "Sem limite".
- **R7** — Apagar o valor do campo e confirmar remove o limite da categoria, voltando a exibir "Sem limite".
- **R8** — O limite é um único valor por categoria, válido para todo mês — não existe limite específico de um mês nem limite geral que valha para várias categorias juntas.
- **R9** — Um valor negativo ou igual a zero não é aceito; o usuário vê o erro junto do campo, sem perder o que digitou.
- **R10** — Uma categoria do sistema aceita limite do mesmo jeito que uma criada pelo usuário.

## Fora de escopo

- Mostrar, na página "Gastos" ou em qualquer outro lugar, se a categoria está dentro, acima ou abaixo do limite (fatia 013).
- Teto do mês inteiro, diferente do limite por categoria (fatia 014).
- Limite que varia por mês ou por período.
- Limite agregado por grupo, natureza ou essencialidade — só por categoria.
- Alertar ou notificar quando um gasto aproxima o limite.

## Pontos em aberto

- nenhum
