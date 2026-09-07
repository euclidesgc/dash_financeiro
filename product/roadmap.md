# Roadmap — dash_financeiro

Painel financeiro pessoal de um usuário, rodando local. O objetivo do produto
não é ver gráficos: é **sair de um déficit de R$ 4.940,72/mês e passar a viver
com folga com o salário atual**. Toda tela existe para responder uma pergunta
que muda uma decisão. O documento de referência é [`docs/plano.md`](../docs/plano.md).

A lista é **ordenada por dependência**, não por prioridade nem por data: a
posição de um item diz o que precisa existir antes dele.

O ID é `nnn-slug` e é o nome da pasta em `product/items/`. Ele não se
reaproveita: número de item removido continua vivo em veredicto, divergência,
PR e commit já escritos.

## Legenda

| Marca | Significa |
|---|---|
| `[ ]` | não iniciado |
| `[-]` | em andamento |
| `[x]` | concluído |

## Itens

- [x] `001-base-e-login` — Só entra quem tem a senha, e os 1.942 lançamentos já extraídos estão no banco com o sinal normalizado (negativo = dinheiro saindo, inclusive em cartão), sem duplicata, e com transferência entre contas próprias marcada para não virar receita.

- [x] `002-gastos-tres-eixos` — Os gastos se leem por grupo, categoria, beneficiário, **natureza** (fixa · variável · eventual) e **essencialidade** (essencial · importante · supérfluo), em qualquer período, com drill-down até a transação. O cruzamento variável × supérfluo é a lista de corte; fixa × essencial é o piso de sobrevivência. As regras de classificação são tabela editável na tela, não código.

- [x] `003-comprometido` — O que já está comprometido e quando sai da conta: assinatura recorrente com valor médio, meses seguidos e ação "não uso mais"; parcelamento com data de término e quanto de caixa ele libera ao acabar; e o calendário de vencimentos.

- [x] `011-serie-duplicada-e-tolerancia-do-vencimento` — O comprometido conta cada dívida uma vez só e conta só o que ainda vai sair da conta. Quatro defeitos do motor de compromissos, corrigidos juntos: o parcelamento que acabava e ressuscitava como assinatura, a compra partida em duas por um centavo de arredondamento, o total que somava assinatura parada, e a janela de vida que marcava como morta a cobrança datada no futuro. E o calendário passou a casar lançamento com previsão por distância entre datas, não pelo mês. O total da base de 05/09/2026 foi de −R$ 12.802,64 para **−R$ 8.026,79**, e as linhas gravadas de 151 para 115.

- [x] `004-resumo-e-projecao` — A tela inicial mostra saldo, dívida total, quanto sobra este mês e a **projeção de saldo dia a dia dos próximos 45 dias**. Depende de `003` porque a projeção soma os compromissos datados: sem eles, projeta só o passado. Com cheque especial a 3,52% a.m., o real marginal se ganha não entrando no vermelho — e é esta tela que impede.

- [x] `005-dividas-e-simuladores` — As dívidas aparecem ordenadas por taxa mensal, do cheque especial (3,52%) ao imóvel (0,72%), e o simulador responde quantas parcelas e quantos juros um aporte elimina. Inclui a decisão do Duster com **saldo de quitação e custo de transporte alternativo como parâmetro editável**, não como constante.

- [x] `006-sync-pluggy` — As movimentações se atualizam **sob demanda e todo dia**, sem duplicar nenhuma transação, e a tela diz quando foi a última sincronização e se ela falhou. Sync que falha em silêncio é pior que sync nenhum: o painel passa a mostrar dado velho com cara de dado fresco.
  **Herdado do `001`:** `sync_runs.transactions_count` hoje guarda quantas linhas existem depois da carga, não quantas entraram na execução — a segunda ingestão do mesmo arquivo grava o total sem inserir nada. Este item decide a semântica antes de mostrar "última sincronização" na tela.

- [x] `012-sync-pos-carga-atomica` — A reclassificação, o recálculo de compromissos e a reconstrução da escada rodam **dentro** do mesmo tratamento de erro da carga. Hoje eles rodam depois de a linha `ok` já estar gravada e fora de handler: uma exceção ali derruba a rota deixando um `sync_runs` que afirma sucesso com as tabelas derivadas paradas — sucesso mentiroso, que é o oposto do que o `006` entregou. Achado estrutural do validador do `006`, lido no código e não provocado.

- [x] `007-objetivo-e-linha-do-tempo` — Existe **um objetivo com data**: 6 meses de reserva (≈ R$ 49.400), com "resultado mensal ≥ 0" e "dívidas caras zeradas" como marcos no caminho. A projeção é simulação mês a mês por código determinístico, apresentada em **três cenários** (conservador · base · otimista) — nunca uma data só, que saltaria de 27 para 41 meses por causa de um mês atípico e perderia a confiança na primeira semana. Cada recálculo grava snapshot, para a linha do tempo ter passado: "em março você projetava 30 meses; hoje projeta 24" é o único sinal de progresso que este produto aceita. O financiamento imobiliário fica fora do objetivo — a 0,72% a.m. ele é a dívida mais barata, e amortizá-lo antes da reserva é o erro que a escada existe para evitar.

- [x] `013-objetivo-cenario-vazio-e-ponto-espurio` — Duas coisas que o validador do `007` achou e que nenhum critério alcança. **A tela nomeia a lista vazia**: hoje o cenário `base` promete "as assinaturas marcadas caem e a lista de corte é cortada" e entrega exatamente o número do `nada muda`, porque as duas listas estão vazias — o número está certo e a prosa parece mentir. E **leitura com data recusada não grava ponto**: `?data=` fora da faixa cai em hoje e a leitura grava assim mesmo, então um erro de digitação na URL injeta um ponto na série de progresso que depois não se distingue de uma leitura legítima.

- [x] `008-simulador-e-base-de-fatos` — Um formulário curto — tipo (receita ou despesa), valor, recorrência, prazo, taxa, data de início — responde **"isso me afasta ou me aproxima, e quantos dias"**, com a linha do tempo antes e depois sobrepostas. Cenário pode ser salvo e comparado lado a lado; "vender o Duster e ficar sem carro" contra "vender e comprar um usado de R$ 25 mil" é a decisão em aberto hoje e merece ser vista, não argumentada. O mesmo formulário captura os fatos que só o humano sabe (saldo de quitação, taxa do cartão, custo de transporte) em `plan_facts`, com valor, unidade, origem, data e prazo de validade — estruturado para consulta, e a projeção se move na tela assim que o fato entra.

- [x] `009-ia-consultora` — A IA **pergunta o que falta**: escolhe o fato ausente ou vencido cuja resposta mais move a projeção e faz **uma** pergunta, dizendo qual número ela muda. Nunca repergunta o que foi respondido, e não insiste — pergunta ignorada some e volta só quando voltar a importar; enquanto isso a tela declara a premissa que está assumindo. Também explica o resultado do simulador, orienta o próximo passo, responde pergunta livre sobre os próprios dados e classifica o resíduo que as regras não pegaram. **A IA nunca calcula**: se ela computasse "isso te afasta 11 dias" erraria, e um número errado na unidade central do produto destrói a confiança em tudo o mais. Sem chave ou com erro, a tela mostra o número determinístico e diz que a leitura da IA está indisponível.

- [x] `014-taxa-sugerida-pelos-juros-cobrados` — O painel **sugere** a taxa mensal de cada conta em cheque especial, derivada dos juros que o banco já cobrou dividido pelo saldo médio dos **dias negativos**, reconstruído a partir do saldo atual. Na base de 05/09/2026: `itau` **4,22% ao mês** (faixa 2,10%–6,80%, 7 meses) e `CAIXA` **8,04%** (4 meses). Sugestão, nunca fato: o campo vem preenchido, a faixa aparece ao lado, e nada é gravado sem o dono salvar. **Cartão não recebe sugestão** — o saldo de um cartão é fatura, e fatura paga inteira não cobra juro; derivar dos encargos pequenos daria 0,06% ao mês, um número falso.

- [x] `015-configuracao-e-nome-do-beneficiario` — Existe **uma** tela para o que só o humano sabe: `/configuracao` lista o catálogo em **fatos** (o que o mundo informa) e **metas** (o que o dono decide), diz qual número cada valor move, e grava. `plan_facts` é o armazém único e `plan_parameters` deixou de existir — o mesmo fato tinha dois nomes, e por isso o painel perguntava para sempre o que já tinha sido respondido. Existe **um** leitor de valor digitado, com uma gramática por unidade: `/dividas` lia `5000.00` como R$ 500.000,00 em silêncio, no campo que decide a venda do carro. E o beneficiário ganhou nome de verdade: o que a Pluggy já manda alcança **404** lançamentos e **148** beneficiários sem o dono digitar nada, e os **30** maiores do gasto — que cobrem **55,5%** do dinheiro — ele batiza uma vez, resolvido na leitura, sem que nenhum total mude. A consulta de nome por CNPJ é **opt-in**: o produto é local por definição.

- [x] `017-navegacao-lateral-e-largura-de-monitor` — A navegação é uma barra fixa
  na lateral esquerda, presente em toda tela com dado e ausente no login, com a
  tela corrente marcada pela aresta de acento e por `aria-current`. Ela substitui
  a pilha de botões no rodapé do Resumo e o "Voltar ao resumo" das outras seis
  telas — e alcança `Gastos`, `Comprometido` e `Regras`, que não tinham saída
  nenhuma. Junto, o painel de dado passa a tomar a largura do monitor
  (`--measure-wide`, `96rem`) enquanto o texto se mantém em `--measure`: acima de
  `75rem` o calendário de 45 dias se abre em colunas e o gráfico de evolução senta
  ao lado da própria tabela. Abaixo de `60rem` a barra deita no topo e rola dentro
  de si.

## Dívida técnica

Bloco separado de propósito. Pendência de processo — portão, fluxo de CI,
veredicto, varredura — não é dependência de item de produto nenhum, e promovê-la
ao topo da fila é a régua local certa e o agregado errado.

- [x] `010-lint-e-formatador-python` — Existe portão de lint para o código Python: `ruff`
  está no ambiente travado, configurado em `pyproject.toml` com uma seleção deliberadamente
  estreita (`E`, `F`, `I`, `B`, `UP`, `C4`), roda por `scripts/lint.sh` e no job `testes` do
  fluxo de CI. Onze validadores registraram a ausência antes de ele existir. A regra escolhida
  pega o que um leitor perde — import morto, nome não usado, ordem de import, `zip` sem
  `strict`. O formatador (`ruff format --check`) entrou junto do pack `python`, no diff que
  o adotou e em nenhum outro: os 49 arquivos reescritos ficaram num commit só, separado, e
  é por isso que o diff seguinte volta a ser legível. O escopo do portão cobre os três
  pacotes — enquanto foi `app tests`, as 35 violações de `financas` e `ingestao` ficaram
  invisíveis por itens inteiros.

- [ ] `018-tipagem-estrita-em-python` — `mypy --strict` roda sobre `app`,
  `financas` e `ingestao`, e o portão de lint o inclui. Hoje `mypy` não é nem
  dependência declarada: a skill `python-tipagem-estrita` do pack e a norma 35 do
  `CLAUDE.md` cobram tipagem que nenhum comando verifica, e norma que nada mede
  não governa. O item declara `mypy` no ambiente travado, mede quantos erros os
  136 arquivos produzem e decide entre corrigir de uma vez ou tolerar uma
  baseline decrescente — a medição vem antes da escolha, não depois.

- [ ] `016-data-de-referencia-no-caminho-de-recusa` — `_reference` de
  `app/routers/whatif.py` e de `app/routers/advisor.py` cai em `date.today()`
  quando a data pedida é inválida ou está fora da faixa, em vez de
  `app.config.reference_date()`, que é quem lê `DASH_TODAY`. Efeito medido pelo
  validador da fase 1 do `015`: com `DASH_TODAY=2026-09-05` no processo,
  `/simulador` e `/consultor` renderizam a data de hoje de verdade — e é esse
  `today` que decide se um fato está **vencido**, então uma leitura sem data
  pedida pode marcar como vencido o que a data de referência ainda considera
  válido. Pré-existente desde o item `008`, fora do diff do `015`. Varrer os
  demais `date.today()` de rota entra no mesmo item.

## Validações de campo pendentes

O que só o hardware, o aparelho real ou o navegador real provam. Não vira tipo
de critério, nem fase bloqueante, nem item eternamente em `[-]`.

**Registrar é obrigação de quem fecha o item.** Fechar sem registrar transforma
uma troca consciente em esquecimento. Cada linha diz o item de origem, o que
exatamente ficou sem verificação e como verificar.

- **`006-sync-pluggy`** — a sincronização real contra a API da Pluggy só se prova
  com credencial válida e item não expirado. O item da Pluggy pede novo consentimento
  (MFA) de tempos em tempos; a reconexão é interativa e não se automatiza. Como
  verificar: rodar o sync com as credenciais reais e conferir que `sync_runs` ganha
  linha e a contagem de transações não duplica.

- **`005-dividas-e-simuladores`** — o saldo de quitação real do CDC só o banco informa, e a
  taxa dos cartões só a fatura. Como verificar: preencher os dois campos na tela e conferir que
  a escada se reordena e que o ágio ou desconto aparece com o sinal certo.

- **`009-ia-consultora`** — a qualidade da resposta do Gemini só se julga lendo, e exige
  chave válida. Como verificar: fazer três perguntas sobre os próprios dados e conferir que
  **todo número citado aparece na tabela "O que ela lê"** da própria tela, dígito a dígito.

## Entradas pendentes do humano

A partir do item `008` **isto deixa de ser uma lista aqui e vira mecanismo do
produto**: a IA pergunta, a resposta entra em `plan_facts` estruturada, e a
projeção se move. Até lá a construção não trava — o motor usa premissa
declarada na tela —, mas o plano de curto prazo fica com uma faixa em vez de um
número.

- **Saldo de quitação antecipada do CDC do Duster** (menor que o saldo devedor de
  R$ 39.176,36; está no app do banco).
- **Custo mensal de transporte sem o carro**, e se há outro carro na casa.
- **Taxa dos cartões** (R$ 16.744,62): rotativo ou parcelado muda a posição deles
  na escada.