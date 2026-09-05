# dash_financeiro

Painel financeiro pessoal de um usuário. Roda local por enquanto.

## O que este produto é

Não é "ver gráficos". É **sair de um déficit estrutural de R$ 4.940,72/mês e
passar a viver com folga com o salário atual, sem viver como monge.**

O painel é o instrumento; o plano é o produto. Toda tela existe para responder
uma pergunta que muda uma decisão — tela que só informa não entra.

Três pilares, nesta ordem:

1. **Login** — é extrato bancário com CPF e nome de pessoas.
2. **Dashboard das movimentações**, atualizadas **todo dia ou sob demanda**.
3. **IA que ajuda a alcançar o plano** de curto, médio e longo prazo.

## Os números de referência (medidos em 05/09/2026)

Congelados nesta data de propósito: são a base dos critérios de verificação, e
o dado vai crescer. Critério que se compara com um relatório regerável passa por
construção em um mês.

| | |
|---|---|
| Renda regular | R$ 9.123 a R$ 13.593/mês, fonte única (GB Tech) |
| Déficit real | **R$ 4.940,72/mês** (5 meses, excluído o crédito atípico de março) |
| Comprometimento fixo | R$ 6.563,57/mês — **58% da renda** |
| Dívida líquida | **R$ 305.207,50** |
| Ativos líquidos | R$ 488,84 |
| Saldo em conta + cartão | −R$ 27.449,71 |
| Gasto total, 6 meses | R$ 103.772,33 |
| Transferências entre contas próprias (excluídas do gasto) | R$ 20.272,00 |
| Lançamentos extraídos | 1.942 |

**Escada de taxa** — onde cada real rende mais, do mais caro ao mais barato:

| Dívida | Taxa | Saldo |
|---|---|---|
| Cheque especial | **3,52% a.m.** (≈51% a.a.) | R$ 11.190,18 |
| Cartões | a confirmar | R$ 16.744,62 |
| CDC do Duster | 1,63% a.m. | R$ 39.176,36 |
| Financiamento imobiliário | 0,72% a.m. | o restante |

**Maiores despesas, 6 meses:** Escola R$ 12.992,18 · Financiamento imobiliário
R$ 12.358,81.

## A descoberta que reorganiza o plano: o Duster

**Renault Duster 1.6 SCe Expression CVT, ano-modelo 2020** (documento:
`DUSTER 16 E CVT`, 2019/2020, placa QXG4E69).

FIPE em set/2026: **R$ 70.818 a R$ 71.892** (código FIPE 025263-8). Contra um
saldo devedor de **R$ 39.176,36**.

| | Venda a particular (90–95%) | Venda a loja / troca (80–85%) |
|---|---|---|
| Recebe | R$ 63.900 – 67.450 | R$ 56.800 – 60.350 |
| Quita o CDC | −R$ 39.176 (menos, na quitação antecipada) | −R$ 39.176 |
| **Sobra em caixa** | **R$ 24.700 – 28.300** | **R$ 17.600 – 21.200** |

As duas dívidas caras somam **R$ 27.934,80**. A venda a particular quita as
duas. O fluxo mensal liberado tem piso de **R$ 1.629** (parcela de R$ 1.235,33 +
≈R$ 394 de juros do cheque especial), ou **33% do déficit**, antes de contar o
cartão.

**O enunciado do problema:** R$ 32.000 de patrimônio líquido estão imobilizados
num ativo que deprecia, enquanto se paga 51% ao ano de juros no cheque especial.
É a coisa mais cara acontecendo nestas finanças — mais cara que qualquer
assinatura da lista de corte.

**Duas entradas pendentes do humano** para fechar a conta: o **saldo de quitação
antecipada** do CDC (menor que o devedor) e o **custo mensal de transporte sem o
carro**. O painel trata as duas como parâmetro editável, não como constante.

## Stack, e por que cada escolha

| Peça | Escolha | Razão |
|---|---|---|
| Linguagem | Python 3.12 | A extração da Pluggy e a matemática financeira já existem, testadas contra a API real |
| Web | FastAPI + Jinja2 + HTMX | Sem etapa de build de JS; interatividade sem SPA |
| Gráficos | Chart.js por CDN | Sem bundler |
| Banco | SQLite em arquivo | Um usuário, um arquivo |
| Agendamento | APScheduler no processo | Um processo só |
| Auth | Usuário único, cookie assinado HttpOnly, hash Argon2, rate-limit no login | É extrato com CPF |
| IA | Gemini (`gemini-flash-latest`), chave só no servidor | Já disponível |
| Design de interface | skill `frontend-design` da Anthropic | Norma visual do projeto; cobre o lado da interface que o pack ausente não cobre |
| Execução | **Local** (`uvicorn` em `localhost`) | Deploy é a fase de maior incógnita; sai do caminho de hoje |

**A escolha de Python custa uma coisa, declarada:** o `generic_harness` tem
packs curados para Flutter, NestJS e React — **não para Python**. O projeto
recebe o processo inteiro (critérios tipados, validador cego, protocolo de
divergência, git-flow) e **não recebe a norma de código da stack**: sem revisor
de stack, sem gates de lint arquitetural. É **atalho deliberado**, registrado
como tal. A alternativa era reescrever 860 linhas de Python já testadas contra a
API real da Pluggy, o que mataria a entrega de hoje sem melhorar o produto.

## Modelo de dados (SQLite)

`accounts` · `transactions` · `category_groups` · `categories` ·
`category_rules` · `commitments` · `debts` · `goals` · `plan_params` ·
`ai_usage` · `sync_runs`.

Convenções herdadas do trabalho de extração, porque já provaram valer:

- **Valor em centavos inteiros**, sinal normalizado: **negativo = dinheiro
  saindo, em qualquer tipo de conta**. A Pluggy inverte o sinal em cartão de
  crédito (`type=DEBIT` com valor positivo é compra) — a normalização acontece
  na ingestão, uma vez, e nunca mais se pensa nisso.
- `transactions.pluggy_id` **único** — reimportar não duplica.
- Flags de exclusão do total de gasto: `is_transfer` (com `transfer_reason`),
  `is_refund` + `refunded_by`. Sem isso, R$ 20.272,00 de transferência entre
  contas próprias viram "receita" e o painel mente.
- `installment_current` / `installment_total`, da API ou do padrão `n/N` na
  descrição.
- `plan_params` guarda o que só o humano sabe (saldo de quitação, custo de
  transporte alternativo, taxa do cartão) como **parâmetro editável na tela**,
  nunca como constante no código.

## Taxonomia — três eixos, não um

O eixo de categoria sozinho não responde "onde cortar sem virar monge":

1. **Grupo** (10): Moradia · Educação · Transporte · Alimentação · Comer fora e
   lazer · Saúde · Serviços e assinaturas · Dívidas e juros · Transferências ·
   Outros.
2. **Natureza**: fixa · variável · eventual.
3. **Essencialidade**: essencial · importante · supérfluo.

O cruzamento **variável × supérfluo** é a lista de corte real. O cruzamento
**fixa × essencial** é o piso de sobrevivência, e é ele que dimensiona a reserva.

`category_rules` mapeia as 77 categorias da Pluggy observadas nos dados, mais
regex sobre a descrição. É **tabela, não código** — editável na tela, sem deploy.

## Telas — quatro superfícies

Cinco recortes do mesmo `GROUP BY` não são cinco telas.

**1. Resumo.** Saldo, dívida total, quanto sobra este mês, estado da última
sincronização — e a **projeção de saldo dia a dia dos próximos 45 dias**.

> A projeção é a tela mais valiosa do produto e não estava no desenho original.
> Com cheque especial a 3,52% a.m., o real marginal não se ganha entendendo o
> passado: se ganha **não entrando no vermelho**. Ranking histórico não impede
> isso; projeção impede. Os dados já estão no modelo — saldo atual,
> `commitments` datados, parcelamentos e a data do salário.

**2. Gastos.** Um `GROUP BY` com seletor de eixo (grupo · categoria ·
beneficiário · natureza · essencialidade) e de período, com evolução de 13 meses
e drill-down até a transação.

**3. Comprometido.** Assinaturas recorrentes (valor médio, meses seguidos,
última cobrança, ação "não uso mais"), parcelamentos com data de término e
caixa que cada um libera ao acabar, e o calendário de vencimentos. São a mesma
pergunta: o que já está comprometido e quando sai da conta.

**4. Dívidas e plano.** A escada por taxa, os simuladores de amortização e
quitação, e os três horizontes com progresso.

## Interface e design

**Antes de escrever qualquer tela, carregar a skill `frontend-design` da
Anthropic.** Ela é a norma visual deste projeto — direção estética, tipografia e
as escolhas que evitam que a interface saia com cara de template padrão.

Isso preenche exatamente a lacuna que a escolha de Python abriu: sem pack de
stack no `generic_harness`, não há revisor de norma de código; a `frontend-design`
cobre o lado da interface, que é o que o usuário vê todo dia.

Três restrições próprias deste produto, que valem acima de qualquer preferência
estética:

- **Algarismos tabulares são requisito, não gosto.** Coluna de valor não pode
  dançar entre linhas — `font-variant-numeric: tabular-nums` em toda cifra.
- **Cor nunca é o único sinal.** Vermelho de déficit vem acompanhado de sinal ou
  rótulo; o painel se lê em tela de celular, sob sol, com pressa.
- **O painel sustenta por baixo, não disputa atenção.** Sem confete, sem streak,
  sem parabéns. Quem abre este painel está resolvendo um problema de R$ 4.940,72
  por mês, não jogando.

Token de cor, tipografia, espaçamento e raio ficam agrupados num único lugar
(`static/css/tokens.css`), consumidos por variável — nunca valor cru espalhado
pelo template.

## Motor do plano — código determinístico, nunca IA

**Quem calcula é função; o modelo interpreta e explica.** Regra herdada de
propósito.

- Renda regular = mediana dos créditos de salário, descartando outliers.
- Piso essencial = fixa × essencial + média de 6 meses do variável × essencial.
- Sobra projetada = renda − comprometido − variável previsto.
- **Escada de dívida**: ordena por taxa mensal e diz onde cada real rende mais.
- **Reserva**: meses de piso essencial acumulados, com data-alvo por cenário.
- **Simuladores**: `financiamento_sac.py` e `cdc_veiculo.py` viram serviço.

### Os três horizontes, revistos pela descoberta do Duster

| Prazo | Meta | Alavanca |
|---|---|---|
| **Curto (0–3m)** | Resultado mensal ≥ 0 **e as duas dívidas caras zeradas** | Decidir o Duster (libera R$ 24.700–28.300 em caixa + R$ 1.235,33/mês); regularizar as 2 prestações do imóvel; cortar R$ 1.099,63/mês de assinatura |
| **Médio (3–12m)** | 1 mês de reserva (≈ R$ 8.234) e nenhuma dívida acima de 1% a.m. | A sobra mensal criada no curto prazo, agora sem os juros que a consumiam |
| **Longo (12–36m)** | 6 meses de reserva (≈ R$ 49.400) | Só depois disso faz sentido amortizar o imóvel a 0,72% a.m. |

A meta que era de médio prazo — zerar cheque especial e cartões — **passa para
o curto prazo**, porque a venda do Duster a resolve de uma vez em vez de em
nove meses de sobra mensal.

## Papel da IA

A chave (Gemini) vive só no servidor. A IA **nunca calcula** — recebe números
prontos do motor determinístico e trabalha sobre eles.

| Tarefa | O que faz |
|---|---|
| `plano_coach` | Recebe o estado do plano (horizontes, progresso, escada de dívida, sobra projetada) e responde "qual o próximo passo e por quê", com o número que justifica |
| `pergunta_livre` | "Por que estourei este mês?" — com acesso às agregações, não à opinião |
| `sugestao_de_corte` | Lê o cruzamento variável × supérfluo e propõe cortes com o valor de cada um |
| `categorizar` | Só o que as regras não pegaram; a resposta vira `category_rules` e a IA se aposenta sozinha à medida que aprende |

Toda chamada grava provedor, modelo, tokens, custo e latência em `ai_usage`.
Toda rota tem fallback: sem chave ou com erro, a tela mostra o número
determinístico e diz que a leitura da IA está indisponível — nunca quebra.

**Fora do escopo:** `alerta_diario`. Alerta não corta contrato, e o déficit é
estrutural (58% da renda comprometida em fixo), não causado por falta de aviso.

## Fases

Cada fase toca no máximo duas famílias de prova.

| Fase | Entrega | Famílias |
|---|---|---|
| **F1** | Schema SQLite + ingestão dos 1.942 lançamentos + login + app rodando em `localhost` | schema · Python |
| **F2** | Taxonomia nos três eixos + Resumo (com projeção de 45 dias) + Gastos | Python · tela |
| **F3** | Comprometido + Dívidas com a escada e os simuladores | Python · tela |
| **F4** | Sync sob demanda e diário, com o estado visível na tela | integração externa |
| **F5** | Motor do plano nos três horizontes + IA (`plano_coach`, `pergunta_livre`, `sugestao_de_corte`, `categorizar`) | IA |

## Segurança

- Login obrigatório antes de qualquer rota que devolva dado. Sem exceção.
- Hash Argon2, cookie assinado HttpOnly + SameSite=Lax, sessão expira, e
  **rate-limit no POST de login** (5 tentativas / 15 min) — sem ele, Argon2 só
  encarece o ataque, não o impede.
- `PLUGGY_CLIENT_ID`/`CLIENT_SECRET` e a chave do Gemini **só** em `.env`
  (gitignorado, modo 600). Nunca no repositório, nunca no HTML, nunca em log.
- O SQLite mora fora do controle de versão. `data/` e `*.sqlite` no
  `.gitignore` desde o commit inicial.
- Enquanto for local: escuta em `127.0.0.1`, não em `0.0.0.0`.

## Verificação

Todo critério é falsificável e se compara com número congelado em 05/09/2026.

1. `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/` → **302**
   para o login sem cookie; **200** com sessão.
2. `curl http://127.0.0.1:8000/api/resumo` sem cookie → **401**.
3. 6 tentativas de login com senha errada em 1 minuto: a 6ª devolve **429**.
4. Tela de Resumo mostra saldo somado **−R$ 27.449,71** e dívida líquida
   **R$ 305.207,50**.
5. Gastos, últimos 6 meses até 05/09/2026, eixo grupo: **Escola R$ 12.992,18**
   no topo, **Financiamento imobiliário R$ 12.358,81** em seguida; o total
   **exclui** os R$ 20.272,00 de transferência e os pagamentos de fatura, e soma
   **R$ 103.772,33**.
6. Dívidas mostra a escada na ordem 3,52% → 1,63% → 0,72%, e o simulador
   devolve, para R$ 10.000 no CDC, **14 parcelas quitadas e R$ 7.994,49 de juros
   evitados** — igual ao `financas/cdc_veiculo.py`.
7. Rodar o sync duas vezes seguidas: `sync_runs` ganha duas linhas e
   `SELECT count(*) FROM transactions` **não muda**.
8. Derrubar e subir o processo: a contagem de transações permanece igual.
9. Com `GEMIMI_API_KEY` ausente, a tela do plano ainda mostra os números
   determinísticos e informa que a leitura da IA está indisponível — sem erro
   500.

## Fora do escopo

Deploy em servidor · app mobile · notificação push · múltiplos usuários ·
importação de OFX · conciliação de fatura · investimentos · qualquer alteração
no repositório `ganza`.
