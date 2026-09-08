# Entrega — 024, fase 2: a seção de cartões, e a tela que para de se contradizer

## 1. O que foi implementado

Os quatro campos que só o dono sabe — limite, taxa mensal, dia de fechamento e
dia de vencimento — passaram a se editar em `/configuracao`, um bloco por cartão,
na mesma tela em que ele já informa tudo o mais que só ele sabe. A taxa digitada
ali é a que a escada de dívida usa: uma casa só, alcançada por duas telas.

Três correções entraram junto, todas achadas pelo validador cego e nenhuma
pedida por critério. Uma escrita forjada conseguia transformar uma conta corrente
em cartão — a chave estrangeira provava que a conta **existia**, não que ela era
de crédito —, e agora a escrita e a leitura exigem as duas coisas. A mesma tela
dizia duas coisas sobre onde a taxa se edita, e passou a dizer uma. E limpar um
campo, que é o único jeito de desfazer um limite digitado por engano, passou a
estar declarado na tela e a confirmar "Apagado." em vez de "Salvo.".

## 2. Critérios atendidos

Nove critérios da fase e três de integração, todos aprovados, com evidência
executada em `05-veredictos/fase-2.md`. O validador não usou nenhum instrumento
do implementador: montou as próprias bases e mediu os treze por conta própria.

## 3. Como testar à mão

Abra `/configuracao` e desça até Cartões. Cada conta de crédito da base tem um
bloco com quatro campos vazios. Informe a taxa de um deles e abra `/dividas`: o
cartão está na escada, na posição da taxa, e saiu da lista de dívidas sem taxa.
Volte e apague o campo: a tela confirma que apagou.

## 4. Divergências

Nenhuma.

## 5. Raio de impacto

Um router novo, um fragmento de tela, uma linha de inclusão, uma chave de
contexto, e o texto de ajuda do catálogo. `app/debts/` não foi tocado nesta fase.
A suíte foi de 576 para 621 testes.

## 6. Validações de campo pendentes

- **A taxa real dos quatro cartões só a fatura informa.** É a entrada que faz os
  R$ 16.744,62 entrarem na escada de verdade. Como verificar: informar a taxa de
  cada cartão em `/configuracao` e conferir que a escada se reordena e que o
  marco de dívidas caras do objetivo passa a contá-los.

## 7. Pendências que viraram roadmap

- **Dois cartões de mesmo nome colapsam num degrau só.** `debts` tem restrição de
  unicidade por tipo e nome, então duas contas de crédito homônimas viram um
  degrau, e a taxa do segundo nunca chega a `/dividas`. Defeito anterior a este
  item, que ele torna alcançável.
- **O consultor aponta a taxa do cartão para `/dividas`** quando ela agora se
  edita nas duas telas. Ambiguidade, não mentira.
