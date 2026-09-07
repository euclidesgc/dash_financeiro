# Discovery — 001-base-e-login

**Item do roadmap:** `001-base-e-login` — Só entra quem tem a senha, e os 1.942
lançamentos já extraídos estão no banco com o sinal normalizado (negativo =
dinheiro saindo, inclusive em cartão), sem duplicata, e com transferência entre
contas próprias marcada para não virar receita.

**Data:** 2026-09-05

## INVEST

| Critério | Passa | Observação |
|---|---|---|
| Independente | sim | É o primeiro item da fila; não espera nada. O que ele consome já está em `data/` e no código de ingestão que rodou contra a API real. |
| Negociável | sim | Fixo: login obrigatório, centavos inteiros, sinal normalizado, sem duplicata. Conversável: nome dos módulos, forma do seed, validade do cookie, quanto do schema nasce agora. |
| Valioso | sim | Sem ele nenhuma tela existe: é o banco com os 1.942 lançamentos e a porta que protege um extrato com CPF. |
| Estimável | sim | Ordem de grandeza: um dia de trabalho, quatro fases. |
| Pequeno | sim | Quatro fases, cada uma com no máximo duas famílias de prova: base de projeto, ingestão, autenticação, primeira tela. |
| Testável | sim | Cada regra abaixo se prova por consulta ao banco, por `curl` com e sem cookie, ou por captura da tela de login. |

**Veredicto do INVEST:** segue como está.

## História

Como dono deste painel, quero que só quem tem a senha entre e que os 1.942
lançamentos já extraídos estejam no banco com o sinal certo e sem duplicata,
para que toda tela construída daqui em diante parta de um número em que eu
confio e ninguém mais leia meu extrato.

## Regras e exemplos

### R1 — Nenhuma rota devolve dado sem sessão válida, nem `/health`

- **E1.1** — Sem cookie, `GET /` responde 302 com `Location: /login`.
- **E1.2** — Sem cookie, `GET /api/resumo` responde 401 e o corpo não traz
  nenhum valor de conta.
- **E1.3** — Sem cookie, `GET /health` responde 401. Com sessão, responde 200
  com `{"status": "ok"}`.
- **E1.4** — Com cookie assinado por uma chave diferente da do servidor,
  `GET /` responde 302 para `/login` — assinatura inválida é ausência de sessão.

### R2 — A senha vive como hash Argon2, semeada do ambiente, e o seed é idempotente

- **E2.1** — Rodar o seed duas vezes seguidas deixa exatamente uma linha em
  `users`, e o `password_hash` começa com `$argon2id$`.
- **E2.2** — `SELECT * FROM users` não contém em nenhuma coluna o texto da senha
  do ambiente; o log da subida e o HTML da página de login também não.
- **E2.3** — O `.env` do dono traz `LOGIN` e `PASSWORD`, e a chave do Gemini em
  `GEMINI_API_KEY`. Nenhuma grafia com typo é lida.

### R3 — Cinco tentativas erradas em 15 minutos bloqueiam a sexta

- **E3.1** — Seis `POST /login` com a senha errada dentro de um minuto: as cinco
  primeiras respondem 401 e a sexta responde 429 com `Retry-After` em segundos.
- **E3.2** — Depois de cinco erros, a sexta tentativa **com a senha correta**
  também responde 429: o bloqueio é da janela, não da credencial.

### R4 — Valor em centavos inteiros, negativo = dinheiro saindo, inclusive em cartão

- **E4.1** — A compra `Pagamento recebido` de 05/08/2025 no cartão Itaú Black
  chega da Pluggy como `amount: -3310.23` (`type: CREDIT`) e entra no banco como
  `amount_cents = 331023` — crédito na fatura é dinheiro **entrando**, e o sinal
  é o oposto do que a Pluggy manda em cartão.
- **E4.2** — Nenhuma linha de `transactions` tem `amount_cents` fracionário:
  a coluna é `INTEGER` e a soma de todas elas é um inteiro.
- **E4.3** — A soma de `accounts.balance_cents` é exatamente `-2744971`
  (−R$ 27.449,71): saldo de cartão entra como dívida, com sinal negativo, embora
  a Pluggy devolva `balance: 8666.7` positivo.

### R5 — Reimportar não duplica

- **E5.1** — Rodar a ingestão duas vezes seguidas deixa `count(*) = 1942` em
  `transactions` e `count(*) = 12` em `accounts`, e grava duas linhas em
  `sync_runs`.
- **E5.2** — `SELECT count(*) FROM (SELECT pluggy_id FROM transactions GROUP BY
  pluggy_id HAVING count(*) > 1)` devolve 0.
- **E5.3** — Derrubar e subir o processo não muda a contagem de transações.

### R6 — Transferência entre contas próprias e estorno ficam marcados

- **E6.1** — As 152 linhas com transferência ou pagamento de fatura entram com
  `is_transfer = 1` e `transfer_reason` não vazio.
- **E6.2** — As 9 linhas de estorno entram com `is_refund = 1`; a que anula um
  débito anterior traz `refunded_by` com o `pluggy_id` do par.
- **E6.3** — A consulta de gasto — soma dos negativos com `is_transfer = 0` e
  `is_refund = 0` e `refunded_by IS NULL` — não inclui nenhuma das 152.

### R7 — A linguagem visual existe antes da primeira tela, e a tela sai dela

- **E7.1** — `product/00-linguagem-visual.md` existe e declara paleta, escala
  tipográfica, escala de espaçamento, raio, foco e movimento, com o valor de
  cada token.
- **E7.2** — `app/static/css/tokens.css` define os tokens declarados, e nenhum
  template ou folha de estilo do app traz cor em hexadecimal, `rgb()` ou `hsl()`
  fora de `tokens.css`.
- **E7.3** — A tela de login em 375, 768 e 1440 px não produz rolagem horizontal
  do corpo, e a captura de cada largura está em `06-capturas/`.

## Perguntas em aberto

Nenhuma.

As dúvidas que apareceram são de convenção, não de produto, e o modo autônomo
manda decidir pela opção mais comum e mais reversível: validade do cookie,
caminho do arquivo SQLite, gerenciador de ambiente Python, quanto do schema
nasce neste item. Cada uma está registrada em `decisoes-autonomas.md` com a
alternativa descartada. Nenhuma delas é decisão que só o dono saiba responder —
as três que são (saldo de quitação do CDC, custo de transporte, taxa dos
cartões) não tocam este item.

## Trilha

**Trilha: rápida.**

| Gatilho | Verdadeiro | Evidência |
|---|---|---|
| Zero perguntas em aberto | sim | Nenhuma pergunta sobrou; ver a seção acima. |
| Uma stack só | sim | Python 3.12 servindo HTML por Jinja2; sem etapa de build de JS, sem segundo runtime. |
| Sem mudança de contrato | sim | Não há OpenAPI versionado nem consumidor externo: as rotas servem HTML e fragmentos HTMX ao próprio app. |
| Sem dependência nova | **não** | O repositório não tem `pyproject.toml`; FastAPI, Uvicorn, Jinja2, `argon2-cffi`, `itsdangerous` e `pytest` entram todos aqui. |

O gatilho 4 é falso, e pela régua mecânica da skill `example-mapping` isso
levaria à trilha completa. **A trilha continua rápida por decisão do dono**,
tomada antes da corrida e registrada no prompt desta sessão: rápida em
`001`–`005`, `007` e `008`; completa em `006` e `009`. A régua dele não é
tamanho, é modo de falha — item interno erra alto e a prova é local e barata;
sync e IA erram em silêncio, e é ali que a spec paga o próprio custo.

Some-se que, no primeiro item de um repositório greenfield, "sem dependência
nova" é falso por construção: o item que instala a stack sempre instala a
stack. Um gatilho que nunca discrimina não decide nada — decidiu o dono.

O que a trilha rápida corta é documentação, nunca verificação: critério tipado,
validador cego e portões valem igual nas duas.
