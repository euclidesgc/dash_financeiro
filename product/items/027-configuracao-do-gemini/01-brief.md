# Brief — 027-configuracao-do-gemini

**Item:** `027-configuracao-do-gemini` · **Trilha:** rápida

> Este documento funde PRD e spec. O que a trilha rápida corta é documentação,
> nunca verificação: critério tipado, reviewer de stack e validador cego valem igual.

## Problema

O consultor de IA do painel só funciona se alguém editar arquivo. A chave da API vem
de uma variável de ambiente (`GEMINI_API_KEY`, lida em `app/config.py:68`) e o modelo é
constante de código (`MODEL = "gemini-2.5-flash"`, `app/advisor/gemini.py:6`).

Duas consequências. **Trocar de modelo exige editar fonte** — quando o provedor
aposenta uma versão, o painel para e a correção é um commit, não um clique. E a única
coisa que `/consultor` sabe dizer sobre configuração é que a chave falta
(`app/templates/consultor.html:61`): não há onde informá-la, então a tela nomeia um
problema que ela mesma não deixa resolver.

Todo o resto do que só o humano sabe já tem tela desde o item `015`. A configuração da
IA é a última coisa do painel que ainda mora fora dela.

## Escopo

A chave da API e o modelo do Gemini se informam em `/configuracao`, na mesma tela em
que já se informa tudo o que só o humano sabe. O que for gravado vale sobre o ambiente;
o ambiente continua funcionando quando nada foi gravado. A chave nunca é exibida
inteira, nem registrada em log.

## Não-escopo

- **A conversa com o provedor não muda.** Instrução, tempo limite, tradução de erro
  para português e a regra de que a IA nunca calcula ficam como estão.
- **Nenhuma outra credencial migra para a tela.** As da Pluggy e o segredo de sessão
  continuam no ambiente: são credencial de processo, não escolha de uso.
- **Não há cifragem em repouso.** A decisão e a alternativa descartada estão em
  `00-discovery.md`.

## Requisitos

- **RF-01.** Existe um leitor único da configuração da IA, e ele devolve a chave e o
  modelo em vigor. Nenhum outro módulo lê `GEMINI_API_KEY` nem a constante de modelo.
- **RF-02.** O que está gravado no banco vence o ambiente. Quando não há nada gravado,
  vale o ambiente. Quando não há nem um nem outro, o painel segue como hoje: os números
  determinísticos aparecem e a tela diz que a leitura da IA está indisponível.
- **RF-03.** `/configuracao` tem uma seção da IA com o campo da chave e a escolha do
  modelo, e grava os dois.
- **RF-04.** O campo da chave chega vazio à tela. Enviar vazio **não** altera a chave
  guardada; existe um ato próprio e nomeado para apagá-la.
- **RF-05.** A tela informa se há chave guardada e mostra no máximo os quatro últimos
  caracteres dela. A chave inteira não aparece em nenhuma resposta HTTP.
- **RF-06.** O modelo é escolhido entre os que o produto declara. Um valor fora da lista
  é recusado no ato da gravação, com mensagem em português dizendo o que fazer.
- **RF-07.** A chave não é escrita em log, em mensagem de erro nem no texto de nenhuma
  tela — inclusive quando o provedor a recusa.
- **RF-08.** Trocar chave ou modelo passa a valer na chamada seguinte, sem reiniciar o
  processo.

## Riscos

- **Segredo em banco local.** É a decisão do item, e ela vale porque o banco está fora
  do versionamento e já guarda a vida financeira inteira do dono. O que não pode
  acontecer é a chave vazar para onde ela não estava: resposta HTTP, log e captura de
  tela. RF-05 e RF-07 são o que se verifica.
- **A chave gravada silenciar o ambiente.** Se o dono gravar e depois esquecer, o
  ambiente deixa de valer sem aviso. Por isso RF-05 exige que a tela diga qual origem
  está em vigor.
