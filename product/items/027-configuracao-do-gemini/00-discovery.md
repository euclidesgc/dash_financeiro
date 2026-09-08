# Discovery — 027-configuracao-do-gemini

**Item do roadmap:** `027-configuracao-do-gemini` — a integração com o Gemini se
configura na tela: chave de API e escolha do modelo. Hoje a chave só vem do ambiente
(`GEMINI_API_KEY`, `app/config.py:29,68`) e o modelo é constante no código
(`MODEL = "gemini-2.5-flash"`, `app/advisor/gemini.py:6`) — trocar de modelo exige
editar fonte, e `/consultor` só sabe dizer que a chave falta.

**Data:** 2026-09-07 · **Trilha declarada:** rápida

## Regra, exemplo e pergunta

- **Regra.** O dono informa a chave na tela e o painel passa a responder com IA, sem
  editar arquivo nenhum e sem reiniciar o processo.
- **Regra.** O dono escolhe o modelo entre os que o produto declara, na tela.
- **Regra.** A chave nunca aparece inteira: nem na tela, nem em log, nem em resposta.
- **Exemplo.** Sem chave, `/consultor` diz que a leitura da IA está indisponível e
  mostra os números determinísticos — como já faz. Com a chave salva na tela, a mesma
  tela passa a responder, e o número continua vindo do código.
- **Pergunta em aberto, e é de segurança:** um campo de formulário significa segredo
  gravado no SQLite. Resolvida abaixo.

## Os quatro gatilhos de trilha completa

| Gatilho | Resposta |
|---|---|
| Mexe em contrato público ou OpenAPI? | Não. |
| Toca autenticação, autorização ou dado pessoal? | **Sim — segredo.** Por isso o item passa por auditoria de segurança antes do validador. |
| Tem mais de uma frente de stack? | Não. |
| Requisito ambíguo que exija spec formal? | Não: a única ambiguidade é a de guarda do segredo, decidida abaixo com a alternativa descartada escrita. |

**Trilha rápida**, com auditoria de segurança obrigatória na fase.

## Decisões autônomas

| Dúvida | Decisão | Alternativa descartada e por quê |
|---|---|---|
| Onde mora a chave? | **No SQLite local**, em tabela própria, com o ambiente valendo como origem alternativa quando não há nada gravado. O banco está fora do versionamento (`.gitignore` cobre `data/`, `*.db` e `*.sqlite`), então a norma 14 — segredo nunca no repositório — continua valendo por construção. | **Cifrar em repouso com chave derivada fora do banco:** a chave de derivação teria de morar no ambiente, que é exatamente onde a chave de API mora hoje. Move o segredo um arquivo para o lado, acrescenta um modo de falha novo (perdeu a derivação, perdeu a configuração) e não muda quem consegue ler: numa máquina de um usuário só, quem lê o arquivo do banco lê o arquivo do ambiente. **Só o ambiente, com o modelo na tela:** é metade do que o item pede, e deixa a chave sendo a única coisa do painel que exige editar arquivo. |
| Quem vence quando os dois existem? | **O que foi gravado na tela.** O que o dono acabou de digitar é a intenção mais recente; o ambiente é o que sobra quando ele não digitou nada. | O contrário faria a tela aceitar um valor e o painel continuar usando outro — a tela mentindo, que é a classe de defeito que o `012` fechou. |
| A chave volta para a tela? | **Nunca inteira.** A tela mostra os quatro últimos caracteres e diz que há uma chave guardada; o campo vem vazio, e vazio significa "não mudar". Apagar é um ato próprio e nomeado. | Devolver a chave preenchida no campo a põe no HTML, no histórico do navegador e em qualquer captura de tela do painel. |
| Quais modelos a tela oferece? | **Lista declarada no código**, com o atual como padrão. Nome de modelo digitado à mão vira erro só no momento da chamada, longe de onde foi digitado. | Campo livre: o dono descobriria o erro de digitação como "o provedor respondeu com erro". |
| A chamada do provedor muda? | Só o modelo e a chave passam a vir de um leitor único. O resto — instrução, tempo limite, tradução do erro para português — fica como está. | Reescrever a chamada junto misturaria duas mudanças num diff só. |
