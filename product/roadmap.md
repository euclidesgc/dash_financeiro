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

- [x] `024-cartoes-como-entidade` — O cartão de crédito é uma entidade com os
  dados que só o dono sabe: **limite, taxa mensal, dia de fechamento e dia de
  vencimento**, editáveis em `/configuracao`, um bloco por cartão. Os cartões
  nascem cadastrados e vazios, derivados das contas de crédito da base, e
  sobrevivem à sincronização: uma carga nova não apaga o que o dono informou.
  **A taxa tem uma casa só**, e é dela que a escada de dívida lê — o campo de
  `/dividas` escreve no mesmo lugar. Era o defeito que o `015` já tinha pago uma
  vez, e o validador cego foi caçá-lo escrevendo pelos dois caminhos e lendo pelos
  quatro: não discordam em estado nenhum. Ele achou o defeito reentrando por
  outra porta — conta que deixava de ser cartão virava degrau de cheque especial
  carregando a taxa do cartão morto, e a tela devolvia 12,50% para quem digitava
  3,52% — e mais uma escrita forjada que transformava conta corrente em cartão.
  Os dois fechados, com teste que reprova sem a correção.
  **Com a taxa informada, os R$ 16.744,62 de cartão entram na escada** e param de
  ficar fora do marco "dívidas caras zeradas" do objetivo. Informar a taxa de cada
  cartão é a entrada que só a fatura dá — está nas validações de campo pendentes.
  **Depende de:** nada aberto. **Destrava:** `026` e `028`.

- [-] `025-financiamentos-na-tela` — O financiamento do imóvel e o do veículo se
  editam na tela, como todo o resto do que só o humano sabe. Hoje os dois moram
  em arquivo JSON escrito à mão e fora do versionamento —
  `data/manual/financiamento_caixa.json` e `cdc_safra_veiculo.json`, lidos por
  `app/debts/ladder.py:22-23` —, o que contraria a norma 26 do projeto no lugar
  em que ela mais importa: são as duas maiores dívidas do painel, e a do imóvel é
  a que a escada existe para **não** amortizar antes da reserva. Os campos que já
  existem no formato de hoje são saldo devedor, taxa mensal, prazo em meses e
  valor da parcela; a tela os expõe com a mesma gramática de digitação do `015`,
  e nenhum número muda de valor ao mudar de lugar.
  **Depende de:** nada aberto. **Destrava:** `028`.

- [-] `026-evolucao-da-fatura-mes-a-mes` — O painel responde **como fica a fatura
  do cartão mês a mês até zerar**, e não só quanto sai nos próximos 45 dias. O
  motor de compromissos já sabe o que é preciso — `commitments` guarda
  `installment_current`, `installment_total`, `installments_left` e `ends_month`
  (`app/migrations/sql/004_commitments.sql:1-18`), e `released_cash`
  (`app/commitments/live.py:62-68`) já soma o caixa que cada série libera ao
  acabar. O que **não** existe é a série mensal fechada: hoje a previsão é uma
  janela de 45 dias (`app/commitments/calendar.py:82-101`), e nenhuma consulta
  soma "quanto ainda falta pagar" de uma compra parcelada. O item entrega a
  curva por mês, com o mês em que cada parcelamento morre nomeado, para a decisão
  de antecipar ou não ser tomada olhando a curva e não a intuição.
  **Depende de:** `024-cartoes-como-entidade` — sem dia de fechamento e limite
  não há fatura a projetar, só uma soma de parcelas.

- [x] `027-configuracao-do-gemini` — A integração com o Gemini se configura na
  tela: **chave de API e escolha do modelo**, em `/configuracao`, a mesma tela do
  resto do que só o humano sabe. O que está gravado vence o ambiente; o ambiente
  vale quando não há nada gravado; e sem nenhum dos dois o painel segue como
  sempre — os números determinísticos na tela e a leitura da IA declarada
  indisponível.
  **A decisão de segurança, tomada e justificada:** a chave mora **no SQLite
  local**, sem cifragem em repouso. O banco está fora do versionamento, então a
  norma 14 continua valendo por construção; cifrar exigiria uma chave de
  derivação que teria de morar no ambiente — exatamente onde a chave de API já
  morava —, o que move o segredo um arquivo para o lado sem mudar quem o lê.
  **A chave nunca volta inteira:** o campo chega vazio, a tela mostra no máximo
  os quatro últimos caracteres, e apagar é ato próprio — campo em branco troca o
  modelo e preserva a chave. E ela viaja no cabeçalho `x-goog-api-key`, não na
  query string (`D-004`), porque query string carrega segredo para registro de
  servidor, proxy e histórico por construção. Chave que não pode ser valor de
  cabeçalho é recusada no ato de gravar, com a tela de pé.
  O validador cego varreu **37 rotas em quatro estados do provedor** — sucesso,
  chave recusada, falha de rede e resposta ilegível — procurando a chave em corpo,
  cabeçalho, cookie, URL de saída, log e tela: nenhum vazamento.

- [ ] `028-consultor-comparativo-de-divida` — O consultor responde à pergunta que
  decide dinheiro: **é melhor ficar no cheque especial ou pegar um empréstimo, e
  qual proposta quita tudo mais barato**. Hoje `/consultor` explica o número e
  pergunta o fato que falta, mas não compara caminhos de dívida — e as taxas que
  a comparação exige só existem depois do `024` e do `025`.
  **A restrição que desenha o item é a norma 23: quem calcula é função testada,
  nunca o modelo.** A comparação é código determinístico — custo total de cada
  caminho, mês a mês, até zerar — e o modelo lê o resultado e explica a escolha.
  Se ele computasse "esse empréstimo te economiza R$ 3.400" e errasse por um
  ponto percentual, o erro cairia na unidade central do produto e destruiria a
  confiança em tudo o mais.
  **Consequência prática para o dono:** nenhuma proposta de empréstimo está nos
  dados de hoje. O item precisa de uma forma de **informar propostas** — taxa,
  prazo, valor liberado, custo de contratação — para ter o que comparar contra o
  cheque especial já medido.
  **Depende de:** `024-cartoes-como-entidade` e `025-financiamentos-na-tela` — sem
  as taxas reais a comparação responde com confiança um número que não mediu.

- [x] `023-taxonomia-hierarquica-do-dono` — A classificação primária é uma
  **árvore de duas alturas que pertence ao dono**: grupo, e dentro dele categoria,
  ligados por chave estrangeira. Os doze grupos são Moradia, Transporte,
  Alimentação, Saúde, Educação, Assinaturas, Pessoal, Financeiro, Dependentes,
  Renda, **Não é gasto** — que guarda transferência entre contas próprias e
  estorno, e existe porque sem ele o painel mente em R$ 20.272,00 — e o escape
  **Outros**. As 77 categorias que a fonte manda pertencem cada uma a um deles, e
  o nome em português mora junto da categoria em vez de numa lista paralela.
  **Nenhum número se moveu.** O validador cego refez o remapeamento na mesma base
  e mediu os quatro números dos dois lados: gasto total, contagem de lançamentos
  considerados gasto, e os dois cruzamentos, idênticos dígito a dígito. A
  exclusão de gasto é pelas colunas escritas na ingestão, nunca pelo grupo — por
  isso mover um grupo de lugar não desloca um centavo.
  Ele também achou que o cruzamento que nomeia a lista de corte estava guardado
  por uma igualdade entre dois conjuntos vazios: nenhum vocabulário declara regra
  no par variável × supérfluo, porque só o dono marca supérfluo na tela. O teste
  passou a plantar o par nos dois lados e a exigir conteúdo antes de comparar.
  **Depende de:** nada aberto. **Destrava:** `019`.

- [ ] `019-reclassificacao-a-partir-do-lancamento` — A correção de classificação
  começa onde o erro aparece: no lançamento aberto em `/gastos`, o dono escolhe o
  grupo, **cria grupo novo ali mesmo** se nenhum dos dez serve, e a tela diz antes
  de gravar quantos lançamentos e quanto dinheiro a correção alcança — os do mesmo
  beneficiário e os da mesma categoria de origem. Hoje isso só existe em `/regras`,
  num vocabulário que não é o de quem olha o gasto: uma expressão regular sobre o
  beneficiário, ou o nome cru que a Pluggy mandou. Escolher grupo arrasta natureza
  e essencialidade junto, porque uma regra atribui os três de uma vez e nenhum
  deles aceita nulo — e é o par natureza × essencialidade que monta a lista de
  corte. A correção vira **regra**, nunca exceção de uma linha: `classify_all`
  recalcula a base inteira a cada sincronização, então uma marca presa a um
  lançamento é apagada na carga seguinte, em silêncio. O item também resolve a
  palavra "categoria", que hoje nomeia três coisas — o texto cru da Pluggy (o eixo
  `categoria`, 77 valores distintos), a tabela `categories` que só espelha esses
  nomes, e `category_groups`, que a tela chama de `grupo` e é o único que a
  classificação de fato usa.
  **Medido na base de 05/09/2026:** o resíduo sem regra é **zero** — a tela que
  existe para achar classificação faltando afirma que não falta nada — enquanto
  **244 lançamentos e R$ 16.556,28**, 7,6% do gasto, estão no grupo de escape
  `Outros` por regra explícita, com `mercadolivre` partido em três beneficiários
  distintos que somam R$ 1.679,53.
  **Depende de:** `023-taxonomia-hierarquica-do-dono` — escolher grupo passa a
  ser escolher grupo **e** categoria, e construir a correção sobre o vocabulário
  plano de hoje é construí-la duas vezes; `002-gastos-tres-eixos` — a correção nasce no drill-down dele e
  usa a mesma tabela de regras; `012-sync-pos-carga-atomica` — a reclassificação
  roda dentro do tratamento de erro da carga, e um segundo caminho de escrita
  entra na mesma transação ou reintroduz o sucesso mentiroso que aquele item
  fechou.

- [x] `022-mes-corrente-como-abertura-padrao` — Toda tela abre no presente. O
  período padrão de `/gastos` passa a ser **do dia 01 do mês corrente até a data
  de referência**, e `/gastos` passa a aceitar `?data=` como as outras cinco
  telas, em vez de ser a única que chama o leitor e descarta o que foi pedido.
  Escolher outro período continua sendo do dono: o padrão é a abertura, não a
  única janela.
  Hoje `/gastos` abre nos **seis últimos meses fechados** e o mês corrente nunca
  aparece na abertura — a janela termina no último dia do mês anterior. A decisão
  é deliberada e está escrita em `app/queries/period.py`: a razão dada é que o
  mês em curso abriria a tela sobre um punhado de dias. **O item derruba essa
  decisão e paga o preço dela**, medido na base de 05/09/2026: a janela de hoje
  mostra **732 lançamentos e R$ 103.772,33**; do dia 01 até 05, **7 lançamentos
  e R$ 730,59**.
  **Duas coisas que o discovery precisa resolver, porque a troca as expõe:**
  primeiro, **cortar em "hoje" esconde mês corrente que já é conhecido** — 54
  lançamentos e R$ 6.997,99 da base estão datados depois de 05/09, parcelas de
  cartão que a Pluggy já postou, e só de setembro são R$ 1.614,45 no dia 08; o
  mês inteiro é R$ 2.345,04 contra R$ 730,59 até hoje. Segundo, **a média mensal
  do painel divide por meses inteiros** (`_months` de `app/queries/crossings.py`),
  então uma janela de cinco dias imprime "média mensal" de cinco dias — e é a
  média do cruzamento fixa × essencial que dimensiona a reserva do `007`, ainda
  que `app/plan/objective.py` monte a própria janela e não consuma a de
  `/gastos`.
  **Depende de:** `016-data-de-referencia-no-caminho-de-recusa` — a abertura de
  `/gastos` passa a sair do mesmo `screen_date`, com os mesmos três estados (sem
  pedido, pedido aceito, pedido recusado), e o guarda de rota que aquele item
  deixou em pé já cobre a sexta chamada.

- [ ] `021-mascara-e-medida-dos-campos` — Todo campo de digitação declara o que
  aceita e cabe no que aceita: campo de dinheiro chega ao servidor já na forma
  que o leitor único exige, campo de texto tem teto de comprimento, e a largura
  de cada um é proporcional ao que ele guarda. Hoje não existe **nenhum**
  `maxlength`, `pattern`, `minlength` ou `required` em template nenhum, e
  `.field-input` é `width: 100%` para todos: o aporte, de no máximo 12
  algarismos, e a pergunta livre ao consultor, de 500 caracteres, têm a mesma
  medida. Os 18 campos de digitação espalhados por sete telas carregam, no
  máximo, `inputmode="decimal"` e `placeholder="0,00"` — dica de teclado, não
  máscara. O item fecha o laço que o `015` abriu: lá a **leitura** ficou estrita
  e `5000.00` deixou de virar R$ 500.000,00 em silêncio; aqui a **digitação**
  passa a produzir o que o leitor aceita, em vez de devolver uma recusa que o
  dono tem de decifrar. E acerta duas assimetrias que a varredura encontra: a
  validade do fato em `/simulador` é texto cru com `placeholder="AAAA-MM-DD"`
  enquanto `/gastos` usa `type="date"`; e o único teto de texto do projeto
  inteiro é o `MAX_QUESTION = 500` de `app/routers/advisor.py` — o apelido do
  beneficiário, o nome do cenário e a expressão regular da regra não têm nenhum,
  no cliente nem no servidor.
  **É item de varredura, e por isso vem depois do que ele varre.** Os campos de
  `024`, `025` e `027` entram na conta: varrer uma vez ao fim custa menos que
  varrer agora e de novo a cada tela nova.
  **A escolha que o discovery fecha:** máscara ao digitar exige o primeiro
  arquivo JavaScript próprio do projeto, que hoje só tem htmx e Chart.js por CDN
  e um `<script>` embutido em `gastos.html`. Formatar ao sair do campo, ou não
  formatar e apenas estreitar `inputmode`, teto e largura, são os caminhos sem
  essa dívida. A largura sai dos tokens de medida do `017`, não de número novo.
  **Depende de:** `015-configuracao-e-nome-do-beneficiario` — a máscara tem de
  concordar com a gramática de `app/settings/typed.py`, e máscara que formata
  para uma forma que o leitor recusa é pior que máscara nenhuma;
  `017-navegacao-lateral-e-largura-de-monitor` — "tamanho adequado" se escreve
  nos tokens de medida que ele criou.

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

- [x] `016-data-de-referencia-no-caminho-de-recusa` — Toda tela responde pela
  data de referência do processo, e existe **um** leitor dela
  (`app/routers/reference.py`), não seis. O defeito era mais largo do que a linha
  original dizia: `day(None, …)` levanta como data ilegível levanta, então
  **entrar na tela sem `?data=` era o caminho de recusa** — o normal, não a
  borda. Daí saíam três coisas medidas: a tela inicial imprimia
  `data inválida: data (None)` sobre uma data que ninguém digitou; `/` e
  `/comprometido` devolviam **500** (`year 0 is out of range`) para
  `?data=0001-01-01`, o mesmo defeito que `/objetivo` já tinha resolvido com
  faixa; e `/simulador`, `/consultor` e `/comprometido` recusavam em silêncio.
  O leitor distingue **três** situações — sem pedido, pedido aceito, pedido
  recusado — e `/objetivo` grava ponto na linha do tempo por `notice is None`,
  nunca por `asked`, porque a ausência de parâmetro **deve** gravar. Um guarda
  em `tests/test_route_guard.py` acusa a sétima rota que tentar resolver a data
  sozinha, e ele tem teste do próprio dente. Fechou com **526 testes**, lint e
  portões limpos.

- [x] `020-varredura-de-rota-que-nao-desce-em-subpasta` — O guarda que impede uma
  rota de resolver a data de tela por conta própria **desce em subpasta**: a
  enumeração é recursiva e chaveia cada módulo pelo caminho relativo, então dois
  módulos de mesmo nome em subpacotes diferentes são duas medições e não uma —
  chaveado por nome, o segundo apagava o primeiro, e qual deles sobrevivia
  dependia da ordem de leitura do disco. O dente que prova o guarda deixou de ser
  um dicionário escrito à mão, que nunca passava pela enumeração e por isso não
  provava a enumeração, e passou a ser quatro testes sobre árvore que o próprio
  teste escreve: subpasta acusada a um e a dois níveis, subpasta aceita quando
  consome o leitor único, colisão de nome, e cópia dentro de `__pycache__`
  ignorada. O validador cego provou por mutação que a recursão é o que sustenta o
  teste — trocando `rglob` por `glob`, a acusação esvazia e a asserção cai.
  Fechou com **530 testes**, e a mesma exclusão de cache foi aplicada ao caso
  idêntico ao lado, em `tests/test_frozen_numbers.py`.

- [ ] `029-o-guarda-reconhece-uma-forma-so-de-perguntar-as-horas` — O guarda de
  rota procura o literal `date.today()`. `datetime.now().date()`,
  `datetime.today()` e `from datetime import date as d` seguido de `d.today()`
  passam caladas — é a mesma família de silêncio que o `020` fechou por
  profundidade e que continua aberta por forma. O guarda passa a reconhecer a
  chamada pela árvore sintática, não por texto, e o dente dele cresce para as
  formas que hoje escapam. Achado pelo planejador do `020`, que não o resolveu
  porque requisito nascido no plano é requisito que ninguém aprovou.
  **Depende de:** nada aberto.

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