# Brief — 032-o-campo-vazio-quer-dizer-a-mesma-coisa

**Trilha:** rápida · **Este documento funde discovery, PRD e spec.**

## Problema

**Duas telas do mesmo painel dizem o oposto sobre o mesmo gesto.**

- `app/templates/fragments/configuracao_ia.html:23` —
  *"Deixar em branco não altera a chave guardada."*
- `app/templates/fragments/configuracao_cartoes.html:6` —
  *"Deixar um campo em branco apaga o valor guardado nele."*

O dono aprende um significado numa tela e o aplica na outra. Na de cartões, o
custo do engano é silencioso e caro: `app/cards/typed.py:26` devolve `None` para
toda string em branco antes de qualquer leitor rodar, o gravador escreve `NULL`, e
a resposta é `200 Salvo.` sem dizer **o que** foi salvo. O dia de fechamento e o
de vencimento são justamente o que decide em qual fatura cada parcela cai — apagar
um deles move dinheiro de mês na tela de comprometido.

A tela avisa, e o aviso não conserta: ele documenta uma armadilha em vez de
removê-la. E ninguém consegue distinguir "não mexi neste campo" de "quero apagar
este campo", porque os dois se escrevem igual.

## Escopo

Campo vazio quer dizer **"não mexi"** em toda tela do painel. Apagar um valor
guardado passa a ser um gesto próprio, explícito, distinto de deixar em branco.

## Requisitos

- **RF-01.** Enviar um campo em branco **não altera** o valor guardado, em toda
  tela — a de cartões passa a se comportar como a da IA.
- **RF-02.** Existe um gesto explícito para apagar um valor guardado, e ele diz o
  que vai apagar antes de apagar.
- **RF-03.** A resposta de gravação diz **quais** campos mudaram, não só `Salvo.`
- **RF-04.** As duas telas passam a dizer a mesma coisa sobre o campo vazio, e o
  texto descreve o comportamento real.
- **RF-05.** Nenhum valor hoje gravado se perde nem muda com esta entrega.

## Riscos

- **Tirar do dono a única forma que ele tem hoje de limpar um campo.** RF-02 é o
  que impede: o gesto novo entra na mesma entrega, não depois.
