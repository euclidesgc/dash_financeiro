# Entrega — 027, fase 1: a configuração da IA na tela, e a chave que nunca volta inteira

## 1. O que foi implementado

O consultor de IA só funcionava se alguém editasse arquivo. A chave da API vinha
de variável de ambiente e o modelo era constante no código — trocar de modelo
exigia um commit —, e a única coisa que a tela do consultor sabia dizer sobre
configuração era que a chave faltava: ela nomeava um problema que ela mesma não
deixava resolver.

Os dois passaram para `/configuracao`, a tela única do que só o humano sabe. O
que está gravado vence o ambiente; o ambiente continua valendo quando não há nada
gravado; e sem nenhum dos dois, os números determinísticos seguem na tela e a
leitura da IA é declarada indisponível, exatamente como antes.

**A chave nunca volta inteira.** O campo chega vazio, a tela mostra no máximo os
quatro últimos caracteres, e apagar é um ato próprio e nomeado — enviar o campo
em branco troca o modelo e preserva a chave. E ela viaja para o provedor no
cabeçalho `x-goog-api-key`, não na query string: query string carrega segredo
para registro de servidor, proxy e histórico por construção, sem que ninguém
escreva uma linha para isso acontecer.

## 2. Critérios atendidos

Doze critérios, todos aprovados pelo validador cego, com evidência executada em
`05-veredictos/fase-1.md`. Ele verificou onze deles com instrumento próprio —
dublê de saída escrito por ele, banco em diretório temporário, usuário sem
relação com o do dono —, e só o de comando roda a suíte do implementador.

## 3. Como testar à mão

Abra `/configuracao`, desça até a seção da IA, cole uma chave e escolha um
modelo. A tela confirma e mostra os quatro últimos caracteres. Envie o campo
vazio: o modelo muda, a chave fica. Clique em apagar: a tela diz que voltou a
usar a do ambiente. Escolha um modelo fora da lista — a tela recusa de pé, com a
mensagem em português, e não grava nada.

## 4. Divergências

**`D-004` — a chave sai da query string e vai para o cabeçalho.** Ratificada em
modo autônomo. O brief aprovado dizia, no não-escopo, que a conversa com o
provedor não muda; a lista que ele enumera não menciona transporte de credencial,
e o `RF-07` — a chave não é escrita em log — valeria só até alguém ligar o
primeiro registro de chamadas de saída. Está reconciliado no brief como `RF-07b`.

## 5. Raio de impacto

Um módulo novo (`app/advisor/config.py`), uma migração (`015_advisor_config.sql`),
um fragmento de tela, duas rotas acrescentadas ao router que já servia a tela de
configuração, e edições pontuais em `app/advisor/gemini.py`,
`app/routers/advisor.py` e `app/templates/consultor.html`. `app/config.py` e
`app/main.py` não foram tocados. A suíte foi de 530 para 569 testes na branch.

## 6. Validações de campo pendentes

- **Os três nomes de modelo oferecidos são escolha do produto, não medição.** Só
  a primeira chamada real prova que a conta do dono tem acesso aos três. Como
  verificar: escolher cada um e fazer uma pergunta ao consultor.
- **Que o provedor aceite a chave no cabeçalho** só a primeira chamada real
  mostra. O dublê prova que enviamos assim.

## 7. Pendências que viraram roadmap

- **`docs/plano.md` diz que o modelo é `gemini-flash-latest`**, e o código usa
  `gemini-2.5-flash` desde o item `009`. Divergência anterior a este item, num
  arquivo fora do escopo dele.
- **O consultor aponta a taxa do cartão para `/dividas`** quando ela agora se
  edita também em `/configuracao`. Ambiguidade, não mentira: as duas telas
  escrevem na mesma casa.
