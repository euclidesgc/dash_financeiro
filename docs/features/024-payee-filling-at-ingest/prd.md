# PRD 024 — payee-filling-at-ingest

## Valor

O dono do painel confia que as provas automáticas medem o mesmo comportamento que ele vê na tela: qualquer base carregada, por qualquer caminho, já nasce com o recebedor preenchido, em vez de exibir "gastos parecidos" por descrição e sem nome de recebedor até a primeira troca de categoria.

## Usuários

O único usuário do painel, dono das contas, quando confere o dashboard de gastos numa base carregada fora do fluxo normal de atualização — a base das provas automáticas de ponta a ponta, uma base de teste ou uma carga manual.

## Requisitos

- **R1** — Todo lançamento que entra na base, por qualquer caminho de carga (botão de atualizar, comando diário, carga da base de provas), sai da própria carga com o recebedor já preenchido, quando a descrição permite derivá-lo.
- **R2** — Um lançamento sem descrição continua sem recebedor após a carga.
- **R3** — Um lançamento que já tinha recebedor preenchido não é alterado por esta carga.
- **R4** — A classificação automática de grupo, natureza e essencialidade continua acontecendo só na etapa pós-atualização, não na carga em si.
- **R5** — Uma base carregada pela via de provas automáticas mostra, desde a primeira consulta, "gastos parecidos" agrupados por recebedor e o nome de quem recebeu na lista — sem depender de uma troca de categoria para preencher o recebedor.

## Fora de escopo

- Rodar a classificação automática (grupo, natureza, essencialidade) na carga da base de provas — fica para a fatia 032.
- Mudar a regra de como o recebedor é derivado da descrição.
- Mudar a precedência do nome exibido — fatia 026.
- Corrigir o recebedor de lançamentos já existentes cuja descrição mudou.

## Pontos em aberto

- nenhum
