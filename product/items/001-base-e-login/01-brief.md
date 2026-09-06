# Brief — Base e login

**Item:** `001-base-e-login` · **Trilha:** rápida

> Este documento funde PRD e spec. O que a trilha rápida corta é documentação,
> nunca verificação: critério tipado e validador cego valem igual. Se uma
> divergência for aprovada durante a execução, o item é promovido para a trilha
> completa e o `doc-reconciler` desdobra este arquivo em `01-prd.md` e
> `02-spec.md`.

## Problema

O dono deste painel tem um déficit de R$ 4.940,72/mês e 1.942 lançamentos já
extraídos que não moram em lugar nenhum consultável — estão em arquivo JSON, e
nenhuma tela pode ser construída sobre eles. Pior: um número lido cru desses
arquivos mente por construção, porque a Pluggy inverte o sinal em cartão de
crédito e porque R$ 20.272,00 de transferência entre contas próprias apareceriam
como receita.

E o que esses arquivos contêm é extrato bancário com CPF e nome de pessoas.
Enquanto não houver porta, qualquer processo que suba na máquina serve o extrato
inteiro para quem pedir.

## Escopo

Depois deste item existe um banco em que o dono confia e uma porta que o
protege: os 1.942 lançamentos e as 12 contas estão gravados em centavos
inteiros, com o sinal normalizado, com transferência e estorno marcados para não
virarem receita, e reimportar não duplica nada. Só entra quem tem a senha, e
errar cinco vezes fecha a porta por quinze minutos. A linguagem visual do
produto está escrita antes da primeira tela, e a tela de login sai dela.

O que este item instala é a base sobre a qual os itens `002` em diante
constroem: projeto Python com dependências travadas, schema SQLite por migração
numerada, ingestão, autenticação e a primeira superfície.

## Não-escopo

- **Taxonomia dos três eixos (grupo · natureza · essencialidade) e
  `category_rules`.** É o item `002-gastos-tres-eixos`. As regras de
  classificação são tabela editável na tela, e tabela sem consumidor é desenho
  adivinhado: ela muda de forma quando o item que a usa for escrito.
- **Telas de Gastos, Resumo, Comprometido e Dívidas.** São os itens `002` a
  `005`, cada um com sua pergunta. A única tela deste item é o login.
- **Sincronização com a API da Pluggy.** É o item `006-sync-pluggy`. A ingestão
  aqui lê arquivo em disco já consolidado; credencial, paginação e reconsentimento
  MFA não entram, e é justamente por serem modo de falha silencioso que `006`
  corre em trilha completa.
- **IA.** É o item `009-ia-consultora`. Deste item só sai o reconhecimento das
  duas grafias da chave no carregamento do ambiente; nenhuma chamada de modelo
  acontece.
- **Motor de projeção, objetivo com data e linha do tempo.** São os itens `007`
  e `008`. Sem eles a base não fica incompleta — ela fica pronta para recebê-los.
- **Cadastro, recuperação de senha e múltiplos usuários.** O produto tem um
  usuário e a senha vem do ambiente; redefinir é editar o `.env` e rodar o seed.
- **Deploy em servidor.** `docs/plano.md` o põe fora do escopo do produto: é a
  fase de maior incógnita e sai do caminho de hoje.

## Requisitos

### Base do projeto e execução local

- **RF-01** — O sistema deve declarar todas as suas dependências em
  `pyproject.toml` e travar as versões em `uv.lock`, de modo que `uv sync` num
  clone limpo instale o ambiente completo. *(ubíquo)*
- **RF-02** — O sistema deve escutar em `127.0.0.1:8000`, nunca em `0.0.0.0`.
  *(ubíquo)*
- **RF-03** — O sistema deve manter o banco em `data/dash.sqlite`, com `data/` e
  `*.sqlite` no `.gitignore`, de modo que o arquivo nunca apareça em
  `git status`. *(ubíquo)*
- **RF-04** — Quando o app sobe, o sistema deve aplicar em ordem crescente as
  migrações numeradas ainda não registradas e registrar cada uma como aplicada;
  a segunda subida não reaplica nenhuma. *(dirigido a evento)*
- **RF-05** — O sistema deve criar exatamente as tabelas `users`,
  `login_attempts`, `accounts`, `transactions` e `sync_runs`, mais a tabela de
  controle de migração. *(ubíquo)*

### Ingestão dos 1.942 lançamentos

- **RF-06** — Quando a ingestão roda contra `data/processed/transacoes.json` e
  `data/raw/accounts_*.json`, o sistema deve gravar 1.942 linhas em
  `transactions` e 12 linhas em `accounts`. *(dirigido a evento)*
- **RF-07** — O sistema deve armazenar valor em centavos inteiros:
  `transactions.amount_cents` e `accounts.balance_cents` são `INTEGER`, e nenhuma
  linha tem valor fracionário. *(ubíquo)*
- **RF-08** — O sistema deve gravar o valor com sinal normalizado — negativo é
  dinheiro saindo, em qualquer tipo de conta. *(ubíquo)*
- **RF-09** — Quando a ingestão lê um lançamento de cartão de crédito, o sistema
  deve inverter o sinal entregue pela Pluggy: o lançamento
  `Pagamento recebido` de 01/08/2025 no cartão Itaú Black
  (`pluggy_id = c5120b3b-cb76-4e35-b2ec-2b6784e80cd9`) chega como
  `amount: -3310.23` com
  `type: CREDIT` e entra no banco como `amount_cents = 331023`, porque crédito na
  fatura é dinheiro entrando. *(dirigido a evento)*
- **RF-10** — O sistema deve gravar saldo de cartão como dívida com sinal
  negativo, ainda que a Pluggy devolva `balance: 8666.7` positivo, de modo que a
  soma de `accounts.balance_cents` seja exatamente `-2744971` (−R$ 27.449,71).
  *(ubíquo)*
- **RF-11** — O sistema deve manter `transactions.pluggy_id` único: a consulta
  `SELECT count(*) FROM (SELECT pluggy_id FROM transactions GROUP BY pluggy_id
  HAVING count(*) > 1)` devolve 0. *(ubíquo)*
- **RF-12** — Quando a ingestão roda uma segunda vez sobre a mesma fonte, o
  sistema deve manter `count(*) = 1942` em `transactions` e `count(*) = 12` em
  `accounts`, e gravar uma segunda linha em `sync_runs`. *(dirigido a evento)*
- **RF-13** — Quando o processo é derrubado e sobe de novo, o sistema deve
  manter a contagem de `transactions` em 1.942. *(dirigido a evento)*
- **RF-14** — O sistema deve gravar as 152 linhas de transferência entre contas
  próprias ou pagamento de fatura com `is_transfer = 1` e `transfer_reason` não
  vazio. *(ubíquo)*
- **RF-15** — O sistema deve gravar as 9 linhas de estorno com `is_refund = 1`,
  e a que anula um débito anterior traz `refunded_by` com o `pluggy_id` do par.
  *(ubíquo)*
- **RF-16** — O sistema deve calcular gasto como a soma dos valores negativos com
  `is_transfer = 0`, `is_refund = 0` e `refunded_by IS NULL`, de modo que nenhuma
  das 152 linhas marcadas entre no total. *(ubíquo)*
- **RF-17** — Se um lançamento da fonte não tem `pluggy_id` ou tem valor que não
  converte para centavos inteiros, então o sistema deve recusar a linha,
  registrar a rejeição com o identificador da fonte e terminar com código de
  saída diferente de zero. *(comportamento indesejado)*
- **RF-18** — Se ao fim da ingestão a contagem gravada difere da contagem de
  registros aceitos da fonte, então o sistema deve desfazer a gravação, registrar
  a falha em `sync_runs` e terminar com código de saída diferente de zero, sem
  deixar o banco parcialmente preenchido. A comparação é fonte contra banco:
  1.942 e 12 são o que a fonte de 05/09/2026 tem, não constante no código — a
  base cresce, e um número congelado dentro da ingestão faria a ingestão do mês
  seguinte falhar por estar certa. *(comportamento indesejado)*

### Senha e seed

- **RF-19** — O sistema deve armazenar a senha como hash Argon2id, com
  `users.password_hash` começando por `$argon2id$`. *(ubíquo)*
- **RF-20** — Quando o seed roda, o sistema deve deixar exatamente uma linha em
  `users`; rodar o seed duas vezes seguidas mantém `count(*) = 1`. *(dirigido a
  evento)*
- **RF-21** — O sistema deve ler o login de `LOGIN`, a senha de `PASSORD` ou
  `PASSWORD`, e a chave do Gemini de `GEMIMI_API_KEY` ou `GEMINI_API_KEY`, sem
  exigir correção do arquivo `.env` do dono. *(ubíquo)*
- **RF-22** — O sistema deve manter o texto da senha do ambiente fora de toda
  coluna de `users`, de toda linha de log da subida e do HTML da página de login.
  *(ubíquo)*
- **RF-23** — Se o login ou a senha estão ausentes do ambiente quando o seed
  roda, então o sistema deve recusar criar usuário, escrever uma mensagem
  nomeando a variável ausente sem imprimir valor, e terminar com código de saída
  diferente de zero. *(comportamento indesejado)*

### Sessão e autorização

- **RF-24** — Quando `POST /login` recebe a credencial correta, o sistema deve
  emitir um cookie de sessão assinado, com `HttpOnly`, `SameSite=Lax`, `Path=/` e
  validade absoluta de 12 horas, e responder 302 para `/`. *(dirigido a evento)*
- **RF-25** — O sistema deve exigir sessão válida em toda rota registrada, sem
  exceção, inclusive `/health`. *(ubíquo)*
- **RF-26** — Quando `GET /` chega sem sessão válida, o sistema deve responder
  302 com `Location: /login`. *(dirigido a evento)*
- **RF-27** — Quando uma rota que responde JSON — `/api/*` e `/health` — recebe
  requisição sem sessão válida, o sistema deve responder 401 com um corpo que não
  traz nenhum valor de conta. *(dirigido a evento)*
- **RF-28** — Quando `GET /health` chega com sessão válida, o sistema deve
  responder 200 com `{"status": "ok"}`. *(dirigido a evento)*
- **RF-29** — Se o cookie chega assinado por chave diferente da do servidor,
  então o sistema deve tratar a requisição como sem sessão, aplicando RF-26 e
  RF-27. *(comportamento indesejado)*
- **RF-30** — Se o cookie chega além das 12 horas de validade absoluta, então o
  sistema deve tratar a requisição como sem sessão. *(comportamento indesejado)*
- **RF-31** — Se `POST /login` chega com a senha errada, então o sistema deve
  responder 401 e gravar a tentativa em `login_attempts` com o IP de origem e o
  instante. *(comportamento indesejado)*

### Rate-limit do login

- **RF-32** — Se cinco tentativas de login do mesmo IP falham dentro de uma
  janela deslizante de 15 minutos, então o sistema deve responder 429 à sexta,
  com `Retry-After` em segundos. *(comportamento indesejado)*
- **RF-33** — Enquanto o IP está dentro da janela de bloqueio, o sistema deve
  responder 429 também à tentativa com a senha correta: o bloqueio é da janela,
  não da credencial. *(dirigido a estado)*
- **RF-34** — O sistema deve manter o registro de tentativas em `login_attempts`
  no SQLite, de modo que reiniciar o processo não zere a janela de 15 minutos.
  *(ubíquo)*

### Linguagem visual e tela de login

- **RF-35** — O sistema deve ter em `product/00-linguagem-visual.md` a
  declaração de paleta, escala tipográfica, escala de espaçamento, raio, foco e
  movimento, com o valor de cada token. *(ubíquo)*
- **RF-36** — O sistema deve definir os tokens declarados em
  `app/static/css/tokens.css`, e nenhum template ou folha de estilo do app traz
  cor em hexadecimal, `rgb()` ou `hsl()` fora de `tokens.css`. *(ubíquo)*
- **RF-37** — O sistema deve renderizar a tela de login em 375, 768 e 1440 px
  sem rolagem horizontal do corpo, com a captura de cada largura em
  `06-capturas/`. *(ubíquo)*
- **RF-38** — Se a tentativa de login é recusada, então a tela deve reexibir o
  formulário com uma mensagem única, que não distingue login inexistente de senha
  errada e não repete a senha digitada no HTML. *(comportamento indesejado)*

### Encerrar sessão, segredo de assinatura e entrega da folha de estilo

- **RF-39** — Quando `POST /logout` chega com sessão válida, o sistema deve
  expirar o cookie de sessão e responder 302 para `/login`; a requisição seguinte
  a `/` com o cookie antigo responde 302 para `/login`. *(dirigido a evento)*
- **RF-40** — O sistema deve assinar o cookie com o segredo lido de
  `SESSION_SECRET`; na ausência da variável, deve gerar um segredo aleatório de
  32 bytes na primeira subida, gravá-lo em `data/session.key` com modo 600 e
  reusá-lo nas subidas seguintes, de modo que reiniciar o processo não derrube a
  sessão aberta. O segredo nunca aparece em log nem em HTML. *(ubíquo)*
### Comportamento da interface

- **RF-42** — Enquanto um elemento interativo da tela de login tem o foco do
  teclado, o sistema deve desenhar um contorno visível de ao menos 2 px em volta
  dele. *(dirigido a estado)*
- **RF-43** — O sistema deve manter razão de contraste de ao menos 4,5:1 entre
  texto e fundo e de ao menos 3:1 entre borda de foco e fundo, nos dois temas.
  *(ubíquo)*
- **RF-44** — Enquanto o navegador declara `prefers-reduced-motion: reduce`, o
  sistema deve entregar a tela sem animação e sem transição, com o estado final
  preservado. *(dirigido a estado)*
- **RF-45** — Enquanto o navegador declara `prefers-color-scheme: dark`, o
  sistema deve aplicar a paleta escura declarada em
  `product/00-linguagem-visual.md`, distinta da paleta clara. *(dirigido a
  estado)*

- **RF-41** — O sistema deve entregar a folha de estilo dentro do HTML servido
  pela própria rota, sem montar diretório estático público: nenhuma rota
  registrada serve arquivo, `GET /static/css/tokens.css` recebe a mesma resposta
  que qualquer caminho sem sessão — `302` para `/login` —, e a tela de login
  renderizada traz os tokens no documento. `app/static/css/tokens.css` continua
  sendo o arquivo-fonte único dos tokens, lido em tempo de renderização.
  *(ubíquo)* — ver `04-divergencias/D-001.md`

## Métrica de sucesso

| Métrica | Onde se observa | Alvo |
|---|---|---|
| Os números do banco batem com os congelados em 05/09/2026 | consulta ao `data/dash.sqlite` | `count(*) transactions` = 1942, `count(*) accounts` = 12, `sum(balance_cents)` = −2744971 |
| Nenhuma rota devolve dado sem sessão | `curl` sem cookie contra cada rota registrada no app | 100% respondem 302 ou 401; zero exceções, `/health` incluído |

## Restrições herdadas

Da norma do projeto (`CLAUDE.md`) e de `docs/plano.md`:

- **Valor em centavos inteiros, negativo = dinheiro saindo** (invariante 22). A
  inversão de sinal do cartão acontece na ingestão, uma vez, e nunca mais se
  pensa nisso.
- **Login antes de qualquer rota que devolva dado, nem `/health`** (invariante
  24). Convenção externa não vence norma escrita do projeto.
- **Transferência entre contas próprias e estorno não entram no total de gasto**
  (invariante 25). Sem isso o painel mente em R$ 20.272,00.
- **Antes de escrever a tela de login, carregar a skill `frontend-design`**
  (invariante 27). Ela é a norma visual do projeto e preenche a lacuna que a
  ausência de pack de stack Python abriu.
- **Números congelados em 05/09/2026** (invariante 28). Critério que se compara
  com relatório regerável passa por construção.
- **Algarismos tabulares, cor nunca como sinal único, painel que sustenta por
  baixo** (`docs/plano.md`, seção Interface). Valem acima de qualquer preferência
  estética, e os tokens nascem já os atendendo.
- **Segredo nunca no repositório** (invariante 14). `.env` gitignorado, modo 600;
  nenhum segredo em HTML ou log.
- **Sem dependência não declarada** (invariante 15), **zero comentário exceto o
  porquê que o código não mostra** (11), **sem TODO** (12), **código e commits em
  inglês, documentos e interface em pt-BR** (16).

Das decisões autônomas D1–D8 (`decisoes-autonomas.md`), que este brief assume e
não reabre: trilha rápida; `uv` + `pyproject.toml`; SQLite em `data/dash.sqlite`;
schema só com as cinco tabelas deste item; sessão por cookie assinado com
`itsdangerous`, 12 h absolutas; rate-limit em tabela SQLite por IP; ingestão a
partir do consolidado em `data/processed/`; `/health` autenticado.

Uma restrição de ambiente desta corrida: **nenhum comando pode ler o `.env`** —
um hook de permissão nega. A prova de que `LOGIN` e a senha existem é
comportamental: o seed roda, o app sobe, o login funciona.

## Riscos

- **O consolidado pode divergir dos números congelados.** A ingestão lê
  `data/processed/transacoes.json`, produzido por `pluggy_consolidate.py`, em vez
  de recalcular as heurísticas de transferência e estorno. Resposta: RF-18 para a
  ingestão e desfaz a gravação em vez de deixar o banco com número diferente do
  congelado; a divergência vira registro para o humano, não silêncio.
- **Cookie assinado não permite revogar sessão antes das 12 horas.** Não há
  tabela de sessão. Resposta: é um usuário e um processo, e revogar é trocar a
  chave de assinatura, o que invalida tudo de uma vez. Revogação seletiva, se
  algum dia importar, entra por divergência.
- **Em `localhost` o rate-limit por IP enxerga sempre `127.0.0.1`.** A janela é
  efetivamente global enquanto a execução é local. Resposta: aceito, porque o
  usuário é um só; a forma do requisito não muda quando a chave passar a ser um
  IP real.
- **O `.env` não pode ser lido por nenhum comando desta corrida.** Se faltar
  variável, a falha aparece só na execução. Resposta: RF-23 nomeia a variável
  ausente na mensagem, sem imprimir valor, o que transforma o erro mudo em erro
  legível em um ciclo.
- **O schema nasce parcial.** As tabelas dos itens `002` em diante não existem
  ainda. Resposta: migração numerada torna acrescentar barato, e mudar coluna
  deste schema depois é nova migração, nunca edição da existente.
- **Não há revisor de norma de código para Python.** O `generic_harness` não tem
  pack para a stack. Resposta: é atalho declarado em `docs/plano.md`; a
  compensação é `frontend-design` no lado da tela e critério tipado com validador
  cego no lado do código.
