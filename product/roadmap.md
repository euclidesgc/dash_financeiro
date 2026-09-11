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

- [x] `025-financiamentos-na-tela` — O financiamento do imóvel e o do veículo se
  editam em `/configuracao`, como todo o resto do que só o humano sabe. Eles
  saíram do arquivo JSON escrito à mão e fora do versionamento para uma tabela do
  banco, importados uma vez, e **nenhum número mudou de valor ao mudar de lugar**:
  o validador cego extraiu do histórico o carregador antigo e comparou as duas
  origens em cinco datas reais e seis sintéticas — zero divergências, degrau a
  degrau, nos seis campos.
  **O saldo do CDC do veículo continua calculado**, como valor presente das
  parcelas não vencidas: ele encolhe sozinho conforme elas vencem, a tela não
  oferece campo para ele, e forçar um saldo no corpo do formulário não o congela.
  O do imóvel continua informado, porque é o que o aplicativo do banco mostra.
  Quatro defeitos latentes fecharam junto: vencimento no dia 31 atravessando
  fevereiro, taxa zero dividindo por zero, contrato quitado emitindo degrau
  fantasma, e a preservação de taxa que faria a taxa editada nunca alcançar a
  escada. Mais um que o validador achou: gravar um financiamento **trocava o
  identificador dos degraus**, e uma aba de `/dividas` aberta antes gravaria a
  taxa na dívida errada — a escrita passou a atualizar a linha no lugar (`D-005`).
  **Depende de:** nada aberto. **Destrava:** `028`.

- [x] `026-evolucao-da-fatura-mes-a-mes` — O painel responde **como fica a fatura
  do cartão mês a mês até zerar**, e não só quanto sai nos próximos 45 dias, com
  o mês em que cada parcelamento morre nomeado e o quanto a fatura cai quando ele
  morre. Para uma dívida feita de compras parceladas, 45 dias mostram uma fatura
  parecida com a do mês passado e escondem que ela cai pela metade em abril
  porque três parcelamentos acabam em março.
  **O dia de fechamento decide de qual fatura a parcela faz parte; o dia de
  vencimento decide em que mês essa fatura sai da conta**, e é esse o mês que a
  curva nomeia (`D-006`) — a mesma língua do calendário de vencimentos ao lado.
  Faltando um dos dois, a curva responde e **declara a premissa**.
  O validador cego escreveu uma **terceira via inteiramente em SQL**, sem tocar na
  aritmética julgada, e comparou o vetor mês a mês em quatro bases, inclusive
  virada de ano: todas idênticas. Depois rodou cinco bases nas duas árvores e
  provou que assinaturas, caixa liberado, calendário, dispensadas e todas as
  manchetes saem **byte a byte iguais**. E mediu o HTML: a tela abria quatro
  seções e fechava cinco sempre que havia parcelamento — agora abre e fecha o
  mesmo número.
  **Depende de:** nada aberto.

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

- [x] `028-consultor-comparativo-de-divida` — O consultor responde à pergunta que
  decide dinheiro: **é melhor ficar no cheque especial ou pegar um empréstimo, e
  qual proposta quita tudo mais barato**. A proposta é entidade — nome, taxa,
  prazo, valor liberado e custo de contratação, informados em `/configuracao` —
  e a comparação põe lado a lado, por proposta, o custo de continuar como está e
  o custo do caminho novo até zerar, com a diferença e qual dos dois é mais
  barato. Proposta sem taxa fica de fora, e a tela diz quantas ficaram.
  **A restrição que desenha o item é a norma 23: quem calcula é função testada,
  nunca o modelo.** A comparação é fórmula fechada em centavos inteiros, e o
  modelo só **lê de volta** o que a função já calculou: uma cifra que ele escreve
  e que não está no contexto enviado **descarta a leitura inteira**, e o dono vê
  os números determinísticos com o aviso de que a leitura não foi conferida. Sem
  chave de API a comparação continua de pé — ela nunca dependeu do modelo.
  A guarda compara **pelo número, não pela escrita dele**: cada cifra é reduzida
  a centavos antes de se procurar no contexto, então o modelo pode reformatar sem
  derrubar leitura correta, e não pode inventar em formato nenhum. A primeira
  versão da guarda falhava aberta — `R$987.654,32` sem o espaço e `R$ 202,4` com
  uma casa decimal não eram reconhecidos como cifra, e o que ela não reconhecia
  ela deixava passar. O validador cego provou os dois furos chamando a função
  direto, e eles fecharam com onze testes de regressão.
  Fechou com **717 testes**, lint e portões limpos.

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

- [x] `019-reclassificacao-a-partir-do-lancamento` — A correção de classificação
  começa **onde o erro aparece**: no lançamento aberto em `/gastos`, o dono
  escolhe o grupo, cria grupo novo ali mesmo, e a tela diz **antes de gravar**
  quantos lançamentos e quanto dinheiro a correção alcança — pelo beneficiário e
  pela categoria de origem. A correção vira **regra**, na mesma transação que
  reclassifica a base: marca presa a um lançamento seria apagada na carga
  seguinte, em silêncio.
  **A promessa é que a tela nunca diga um número e faça outro**, e ela se sustenta
  em duas frentes. A prévia e a gravação leem o **mesmo** gabarito de consulta,
  com casamento exato sobre o beneficiário — `mercado livre` não alcança
  `mercado livre pago`, provado por identidade de linha. E o número que aparece
  depois de gravar é o alcance, nunca o contador da camada de baixo, que se move
  também com transferência e estorno: o validador montou a base onde um conta
  quatro e o outro conta dois, e a tela imprime dois.
  Quando outra regra de precedência maior já segura o beneficiário, a gravação
  alcança zero e a tela **nomeia a regra que segura**, com link para editá-la —
  sem isso o dono clicaria em corrigir, receberia sucesso, e nada teria mudado.
  A correção escolhe **grupo**, não categoria (`D-007`): dar categoria à regra
  abriria um segundo jeito de decidir a categoria do mesmo lançamento,
  competindo com a árvore do `023`.
  **Depende de:** nada aberto.

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

- [x] `021-mascara-e-medida-dos-campos` — Todo campo de digitação declara ao
  navegador o que aceita — teto de comprimento, modo de teclado e, onde o
  servidor recusa vazio, obrigatoriedade — e **tem largura proporcional ao que
  guarda**. Eram **37** campos, não os 26 que o brief contou: cartões, propostas
  e configuração da IA nasceram durante a corrida e entraram na conta. Nenhum
  declarava nada.
  **O teto é um número só, escrito num lugar só.** `app/settings/limits.py` é a
  casa de todos eles, exposta ao template como global — antes, os três tetos que
  existiam moravam em três arquivos com três nomes, e nenhum alcançava a tela,
  porque template não importa módulo Python. Sem isso o campo e o servidor não
  tinham como ser o mesmo número, que é o risco que o brief nomeia.
  A largura **deriva** do teto em vez de repeti-lo: uma regra só na folha de
  estilo solta o `width: 100%` de quem declarou teto, e o `size` do campo faz o
  resto (D-001). O campo de aporte e a pergunta livre ao consultor deixaram de
  ter a mesma medida — o exemplo com que o brief descrevia o defeito. E três
  templates estilizavam o campo com a classe do invólucro em vez da do campo, que
  é por que a régua nunca tinha efeito ali.
  **Três frestas da gramática fecharam**, todas achadas por validadores desta
  corrida: dígito arábico-índico e de largura cheia eram aceitos no campo que
  decide a venda do carro — o número saía certo, e a surpresa era a aceitação;
  taxa de exatamente 100% ao mês passava num financiamento imobiliário, e agora
  cada tipo de dívida tem teto próprio; e nome com byte ilegível virava linha que
  o dono não conseguia sobrescrever redigitando, porque o nome é a chave de
  gravação. Quatro campos de texto que não tinham teto nenhum ganharam um.
  **O risco central não se realizou:** prazo de 420 meses e valor de doze
  algarismos continuam entrando inteiros, provado por HTTP de ponta a ponta — e o
  pior caso formatado com separador de milhar cabe no teto declarado. Autorização
  continua sendo do servidor: um `POST` que passa por cima do atributo do campo é
  recusado com mensagem em português.
  `scripts/campos-digitaveis.py` fica atrás como medidor, e foi **visto acusando**
  antes de merecer confiança. Item de varredura que não deixa medidor volta a
  zerar na próxima tela que alguém escrever — foi assim que 26 viraram 37.
  Fechou com **741 testes**, lint, tipos e portões limpos.

- [-] `037-sincronizacao-real-com-a-pluggy` — O botão **Sincronizar busca na
  Pluggy**, e a base deixa de estar parada em 05/09/2026. Hoje ele relê um
  arquivo que dois scripts de `ingestao/` geram à mão: catorze sincronizações
  seguidas trouxeram zero lançamentos, e o painel mostra dado velho com cara de
  fresco — o que o `006` existia para impedir. A busca por janela (desde a última
  busca bem-sucedida, sem data final) e as marcas que o consolidador fazia — sinal
  do cartão, transferência entre contas próprias, pagamento de fatura, estorno,
  saque, parcela — passam para dentro do app, e a carga guarda o que hoje
  descarta: CPF/CNPJ de pagador e recebedor, meio de pagamento, MCC, pendente ou
  lançado, fatura, data da compra e a conexão de cada conta.
  **O id da Pluggy não é estável**: a compra de cartão que passa de pendente a
  lançada volta com id novo, e as 139 pendentes da base virariam duplicata. O
  lançamento recriado é **religado** ao antigo, mantendo o número interno — é
  isso que faz ajuste do dono e etiqueta sobreviverem —, e só o que some sem par
  sai da base, com lápide, dentro da janela buscada e nunca de conta com resposta
  incompleta. A Pluggy guarda 12 meses; a base local é o arquivo de longo prazo.
  **Corrige um defeito de dinheiro:** 14 compras em dólar foram gravadas com o
  valor em dólar — STRIPE US$ 64,80 entrou como R$ 64,80, eram R$ 350,57 — e o
  gasto histórico está **R$ 2.346,09 abaixo** do real.
  A rotina diária roda sozinha com o app de pé, e a tela diz, por banco, quando a
  Pluggy o atualizou e qual pede novo login no MeuPluggy. Pedir atualização ao
  banco é limitado a uma vez por hora por conexão.
  Fases: 1 a carga entende o bruto; 2 o botão busca na Pluggy; 3 o botão e o
  relógio.
  **Depende de:** nada aberto. **Destrava:** `038`, `039`, `040` e `041`.

- [-] `038-conta-e-instituicao-como-eixo` — Todo lançamento diz **de que banco e
  de que conta veio**, e os gastos se leem, filtram e agrupam por instituição e
  por conta. O banco é a conexão da Pluggy, não o campo `institution`, que repete
  o nome do cartão: a conta chamada "platinum" é o cartão do Nubank, e o Passaí
  Visa Gold está na conexão do Itaú. As cinco conexões — C6, Mercado Pago,
  Nubank, CAIXA, Itaú — viram cinco instituições com nome editável, e cada uma
  das 12 contas ganha apelido editável. A sincronização nunca sobrescreve nenhum
  dos dois, pelo mesmo motivo que separou `cards` de `accounts`.
  **Depende de:** `037` — a conexão de cada conta só passa a ser gravada na fase
  1 dele.

- [-] `039-beneficiario-como-entidade` — O beneficiário é **um cadastro** — nome,
  razão social, nome fantasia, CPF ou CNPJ e ramo de atividade —, e não mais a
  descrição do extrato normalizada. Hoje "IFOOD *RESTAURANTE X" e "iFood.com" são
  dois beneficiários, e os 805 da base são 805 textos. O mesmo documento junta as
  variações sozinho; o que o documento não junta, o dono **funde**, e fundir
  nunca muda o total. A contraparte segue o sentido: na saída é quem recebeu, na
  entrada quem pagou, no cartão o estabelecimento.
  A razão social e o nome fantasia chegam **sem clique**: depois da
  sincronização, cada CNPJ novo é consultado uma vez na BrasilAPI, com cache por
  CNPJ e ritmo contido, e falha não rebaixa a sincronização. A consulta continua
  opt-in, como decidiu o `015`. CPF não tem consulta pública: fica o nome que o
  banco mandou. Os apelidos gravados pelo `015` migram para o cadastro.
  Fases: 1 o cadastro; 2 o CNPJ automático.
  **Depende de:** `037` — o CPF/CNPJ de pagador e recebedor (624 e 516
  lançamentos no bruto) só entra na base pela fase 1 dele. **Destrava:** `040`,
  `042` e `043`.

- [ ] `040-classificacao-em-camadas` — Cada campo da classificação sabe **de onde
  veio** — dono, regra, IA, sistema ou reserva —, e o dono ajusta **um lançamento
  só** sem que a próxima sincronização apague. Hoje não dá: a classificação é
  recalculada inteira a cada carga, e por isso o `019` teve de transformar toda
  correção em regra. A precedência é por campo: ajuste no lançamento, padrão do
  dono para o beneficiário, regra do dono, sugestão da IA, sistema, reserva. E a
  semente para de devolver o grupo antigo a uma regra que o dono editou.
  **Dois eixos mudam.** Entra a **operação** — compra no cartão, Pix enviado e
  recebido, TED/DOC, boleto, pagamento de fatura, transferência entre contas
  próprias, estorno, saque —, derivada dos dados e corrigível pelo dono, e é dela
  que passa a sair o que não é gasto: hoje 7 lançamentos do grupo "Não é gasto"
  contam como gasto (−R$ 2.125,65), e o dono não tem como corrigir uma
  transferência que a detecção errou. A **natureza** ganha "parcelada", e a
  parcela sai de variável e de fixa — piso e lista de corte encolhem, e a
  diferença é medida e declarada.
  Fases: 1 as camadas, sem mover número nenhum; 2 operação e parcelada, com o
  número medido.
  **Depende de:** `039` — o padrão do dono mora no cadastro do beneficiário — e
  `037`, cujo meio de pagamento e tipo de operação alimentam a derivação.
  **Destrava:** `041`, `042` e `043`.

- [ ] `041-lancamentos-e-edicao-em-massa` — Existe **uma tela com todos os
  lançamentos** de todas as contas, entradas e saídas, com o saldo de hoje de
  cada conta no topo. Ela filtra por período, banco, conta, texto (descrição,
  beneficiário, razão social), faixa de valor, sentido, cada eixo, etiqueta,
  origem da classificação, pendente ou lançado e recorrente; e agrupa por
  qualquer eixo, pela **compra parcelada** (parcela atual, quantas faltam,
  quando acaba) e pela **fatura** do cartão.
  **A edição é em massa:** o dono marca linhas, ou "todos os N do filtro", e troca
  categoria, natureza, operação, essencialidade, beneficiário, etiqueta ou
  descrição própria de uma vez, escolhendo se vale **só para estes** ou **também
  para os próximos deste beneficiário**. A tela diz antes de gravar quantos
  lançamentos e quanto dinheiro a mudança alcança, e recusa gravar se a seleção
  mudou entre a prévia e a confirmação — uma sincronização que entrou no meio,
  por exemplo. A descrição do extrato continua visível ao lado da do dono. A
  etiqueta é texto livre, várias por lançamento ("Reforma", "Férias jan/27").
  Fases: 1 leitura; 2 ação em massa; 3 etiquetas.
  **Depende de:** `040` — sem origem e sem ajuste por lançamento não há o que
  editar em massa —, e de `038` e `039` para os eixos conta e beneficiário.

- [ ] `042-tela-de-beneficiarios` — Os beneficiários têm tela própria: nome,
  razão social, nome fantasia, documento, quantidade de lançamentos, dinheiro e a
  classificação padrão de cada um, com fundir, renomear e classificar em massa.
  O "corrigir" de `/gastos` passa a gravar o padrão do beneficiário em vez de uma
  regra de texto exato, e `mercado livre` deixa de não alcançar
  `mercado livre pago`. A seção de apelidos sai de `/configuracao`.
  **Depende de:** `039` e `040`.

- [ ] `043-sugestao-da-ia-por-beneficiario` — A IA **sugere** categoria, natureza
  e essencialidade **por beneficiário**, não por lançamento, e a sugestão vale na
  hora, marcada como da IA, até o dono aceitar ou trocar. O modelo recebe nome,
  razão social, ramo de atividade, exemplos de descrição, valor típico e
  frequência, e só pode responder com o vocabulário do banco: valor fora dele é
  descartado. **Nunca recebe beneficiário pessoa física** e **nunca decide
  operação** — é a operação que decide o que é gasto, e a norma 23 tira isso do
  modelo. Pergunta uma vez por beneficiário, e a sincronização seguinte só
  pergunta pelos novos; um interruptor na tela diz se a IA pode classificar, e
  uma fila "revisar sugestões" aceita em massa.
  **Depende de:** `039` e `040` — a sugestão é uma camada da classificação presa
  ao cadastro do beneficiário. Não depende do `041` e pode correr ao lado dele.

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

- [x] `018-tipagem-estrita-em-python` — `mypy --strict` roda sobre `app`,
  `financas` e `ingestao`, e o portão de lint o cobra — junto do lint e do
  formatador, não no lugar deles. A integração contínua chama o mesmo comando,
  porque portão que só existe na máquina de quem rodou não é portão. A norma 35
  deixou de cobrar tipagem que nenhum comando verificava.
  A medição veio antes da escolha, como o item exigia: **202 erros em 36
  arquivos**, três quartos deles em duas classes mecânicas — genérico sem
  parâmetro e função sem anotação —, e a classe seguinte sumindo sozinha quando
  o que se chama ganha tipo. Por isso a decisão foi corrigir todos, em duas
  fases, e não tolerar uma baseline decrescente: número que só cai quando alguém
  lembra reproduz com nome novo a norma que nada mede. Hoje são **109 fontes
  limpas** e **dois** silenciamentos em toda a árvore, ambos no mesmo conflito
  entre o stub do Starlette e a caixa do cookie que um teste fixa.
  **Anotar não moveu dinheiro, e isso foi medido, não afirmado:** os validadores
  cegos serviram o painel contra o código de antes e o de depois, sobre a mesma
  cópia da base real, e compararam as telas **byte a byte** — quatro na fase 1,
  oito na fase 2, todas idênticas. Os dois executáveis de `financas` e o
  consolidador de `ingestao` produziram saída idêntica sobre os mesmos dados.
  O portão foi **visto vermelho antes de merecer confiança**: o validador quebrou
  um tipo de propósito e confirmou que ele reprova. Isso importa aqui porque os
  portões arquiteturais deste projeto passaram quinze itens dizendo `limpos` sobre
  a contagem do que tinham varrido, não do que tinham julgado — que era zero.
  Fechou com **732 testes**, lint, tipos e portões limpos.

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

- [x] `029-o-guarda-reconhece-uma-forma-so-de-perguntar-as-horas` — O guarda de
  rota reconhece a chamada ao relógio pela **árvore sintática**, não por busca de
  texto. Ele segue apelido de import e reatribuição simples de nome, alcança
  `date.today()`, `datetime.today()`, `datetime.now()`, `datetime.utcnow()` e
  `date.fromtimestamp(time.time())` — e deixa de ser enganado pela cadeia em
  comentário, docstring, literal, nome de variável ou chave de dicionário,
  inclusive no caso legítimo de um `date` vindo dos modelos do próprio projeto,
  que uma busca de texto acusaria em falso.
  O validador cego provou por **mutação** que o verde é sustentado pela árvore:
  revertendo a acusação para busca de texto, três testes voltam a falhar. Ele
  achou quatro formas que ainda escapavam, e as quatro fecharam com teste que
  reprova sem a correção. O limite declarado é o rastreio de nome, não análise de
  fluxo: desempacotamento de tupla, atribuição múltipla e reatribuição
  condicional ficam de fora, e nenhum deles existe hoje em `app/routers/`.

- [x] `030-numeracao-de-migracao-sem-buraco` — O aplicador de esquema **recusa
  uma migração que chega por baixo** do que a base já aplicou, e recusa antes de
  aplicar qualquer coisa da mesma execução — provado com lote misto, em que
  pendentes válidas ao lado de uma inválida também não entram. A numeração perdeu
  o vão: `016` e `017` não existem, a próxima é `019`, e isso está registrado onde
  quem escrever a próxima migração vai ler.
  **O guarda achou um caso real, na base do dono:** ela tem `001`–`011`, `013`,
  `014` e `015` e nunca aplicou a `012`, que entrou na pasta depois. Daí a segunda
  fase: as duas situações pedem conselhos **opostos** e o guarda dava um só.
  Migração nova com número baixo se renumera; versão que **esta** base pulou —
  reconhecida pelo vão, versões abaixo e acima dela — se reconcilia com
  `python -m app.migrate --reconciliar <versao>`. A reconciliação **tenta
  aplicar**: se a migração não couber no esquema, nada é gravado e o vão continua,
  porque registrar às cegas é assinar que o esquema está certo sem olhar — e foi
  assim que o vão nasceu. Ela também recusa uma versão que não seja vão, para não
  reabrir a porta que o item existe para fechar.
  **Ensaiado contra cópia da base real:** reconciliar a `012` esvazia `categories`
  (77 → 0, porque a migração derruba e recria a tabela) e a classificação a repõe
  inteira (77, `changed=0`). O validador não confiou nesse número: extraiu os
  1.942 pares de lançamento e grupo antes e depois e comparou **byte a byte** —
  idênticos. Nenhum dinheiro se move.
  E a comparação de versões é textual, então a largura importa: um arquivo `9_x.sql`
  sem zero à esquerda inverteria ordenação e guarda ao mesmo tempo. É recusado na
  porta. Fechou com **753 testes**.

- [x] `032-o-campo-vazio-quer-dizer-a-mesma-coisa` — Campo vazio quer dizer **"não
  mexi"** em toda tela do painel, e apagar um valor guardado é um gesto próprio:
  um botão por campo, com o nome do campo no rótulo, visível só quando há o que
  apagar. A resposta de gravação diz **qual** campo mudou e para quanto — o
  `200 Salvo.` genérico sobre um formulário de quatro campos era o que escondia o
  defeito.
  Duas telas do mesmo painel diziam o oposto sobre o mesmo gesto: a da IA, que
  branco não altera a chave; a de cartões, que branco apaga o valor. O dono
  aprendia um significado numa e o aplicava na outra, e na de cartões o engano era
  silencioso — nos campos que decidem em qual fatura cada parcela cai. O aviso na
  tela documentava a armadilha em vez de removê-la.
  O escritor é compartilhado com a rota de taxa de dívida, que herdou a proteção
  junto. O validador leu a tabela **direto**, campo por campo, em vez de confiar
  no código de resposta, e confirmou contra `develop` que o valor era mesmo
  gravado sem condição — perda de dado real, não suposição do plano. Fechou com
  **763 testes**.

- [x] `033-semear-taxonomia-deixa-o-banco-coerente` — Semear a taxonomia deixa o
  banco coerente **sozinha**, sem depender de um segundo comando. Ela reescrevia o
  grupo dos lançamentos que apontavam para grupo removido, mas não o do lançamento
  cujo grupo sobreviveu e cuja **regra** mudou de grupo: rodada isolada, saía com
  sucesso deixando divergência — o mesmo sucesso mentiroso que o item `012` fechou
  na sincronização.
  **A medição desmentiu a estimativa.** O número da árvore anterior era "14 de 87";
  na base real do dono são **343 de 1.942** — 18% dos lançamentos. O validador
  refez a conta com consulta própria e chegou ao mesmo: 343 com o código anterior,
  **0** com a correção.
  E o custo é o que o plano exigia que fosse: **uma** atualização com predicado
  alargado, sobre uma que já existia. Nenhuma chamada de classificação por baixo,
  então o caminho encadeado da linha de comando não passou a fazer o trabalho duas
  vezes. Os totais das quatro telas de dinheiro são idênticos com e sem a
  correção — dado derivado não move dinheiro. Fechou com **771 testes**.

- [x] `034-o-portao-de-comentario-fala-a-lingua-do-projeto` — O portão que cobra
  comentário-com-porquê reconhece a justificativa **na língua em que o projeto
  escreve código**, distingue cabeçalho de arquivo de comentário ao lado de
  código, e **julga a árvore inteira** — o recorte por diff que ele carregava
  desde que foi ligado acabou.
  A norma 16 manda escrever em inglês e o portão só reconhecia marca em
  português: comentário escrito na língua certa era reprovado, e o que passava
  violava a norma. Medido na árvore inteira, o estrago era **1.129 linhas em 103
  arquivos — 407 blocos**, e a maior parte era justificativa legítima em inglês,
  sem marca, mais cabeçalho de script, que documenta o contrato do próprio arquivo
  e não tem outro lugar onde morar.
  **Absorveu o antigo `031`**, que era a varredura retroativa: ela virou a fase 2
  deste item. Invertido, a varredura poria marca em português em 407 blocos para a
  correção seguinte mandar trocar todas — norma 20, causa raiz e não segundo
  remendo.
  A fase 1 **foi reprovada na primeira rodada**, e a reprovação é o que dá valor a
  este item: o portão tinha ficado permissivo. Uma linha de comentário vazia não
  fechava o bloco, então uma marca em qualquer ponto contaminava todos os
  parágrafos seguintes; e a marca casava em qualquer lugar da frase, então
  `# for some reason: it does` pagava o pedágio. **A contagem tinha caído de 1.129
  para 910 e parte da queda era vazamento.** Fechado o vazamento e ancorada a
  marca, ela subiu para 977 — o número honesto é maior que o bonito.
  A fase 2 julgou os **336 blocos um a um**. Três foram apagados, todos assinatura
  de função, nenhum um porquê — e o validador vasculhou as linhas removidas atrás
  de número medido, data, incidente e decisão de segurança: todas continuam lá,
  traduzidas e marcadas. Ele leu 18 blocos marcados para conferir o risco oposto,
  a marca virando enfeite sobre prosa descritiva: nenhum. E provou que o `0` é
  conserto e não permissividade injetando dois comentários e vendo o portão sair
  vermelho.
  Fechou com **771 testes**, e as quatro telas de dinheiro byte a byte idênticas.

- [x] `035-a-recusa-diz-o-que-faltou` — A recusa de correção de classificação diz,
  em português, **o que faltou** e o que fazer em seguida. Ela mostrava
  literalmente `None` no lugar do termo, quando o dono não escolhia grupo existente
  nem digitava um novo: a recusa estava certa e a explicação estava quebrada — e é
  a explicação que decide se ele corrige ou desiste.
  A correção é da **causa**, não da formatação: a validação passou a distinguir
  *termo ausente* de *termo inválido*, então o próximo caminho que chegar com valor
  nulo não imprime `None` de novo. E um teste percorre **as 20 rotas de escrita que
  podem recusar** — 20 de 20, contadas pelo validador — afirmando que nenhuma
  mensagem traz `None`, `null`, `NoneType` ou `Traceback`. Revertida a correção,
  ele falha e **nomeia a rota**. É o que impede o terceiro caso, e o que a norma 20
  pede quando o segundo aparece. Fechou com **749 testes**.

- [x] `036-a-suite-nao-depende-do-diretorio-do-dono` — A suíte passa numa árvore
  recém-clonada, **sem nenhum arquivo do dono**: 749 coletados, 749 passados, zero
  pulados — idêntico à árvore completa. Era o ambiente da integração contínua, e
  ninguém o tinha medido.
  Dois testes liam `data/processed/` e `data/raw/`, e **mais seis** liam um nível
  abaixo, pela reconstrução da escada semeando os contratos de financiamento reais
  do dono. Todos passaram a usar dado versionado. Três outros liam o corpus real e
  **se pulavam sozinhos** quando ele faltava — na integração contínua nunca
  exercitavam a função que diziam provar, e a corrida saía verde assim mesmo. Um
  teste que se pula sozinho quando o dado falta não é um teste que passou.
  O que só os 1.942 registros reais provam mudou para
  `scripts/conferir-normalizacao.py`, que **diz** o que faz em vez de pular em
  silêncio. A amostra que a suíte usa é sintética: versionar descrições de
  transação do dono para provar uma função de texto trocaria um problema por um
  pior.
  E a mensagem de erro de escrita passou a nomear a restrição violada. A anterior
  custou **duas atribuições de culpa erradas** nesta corrida, a validadores
  diferentes. Fechou com **768 testes**.

- [ ] `044-o-router-nao-monta-consulta` — O portão da norma 30 enxerga **SQL
  cru**. Hoje ele casa só as formas do SQLAlchemy — `select(` e
  `session.execute` —, que este projeto não usa, e passa verde sobre quatro
  routers que montam consulta com `conn.execute("SELECT…")`: `spending`,
  `rules`, `settings` e `summary`. É o defeito que o `018` descreveu nos portões
  arquiteturais: `limpos` sobre a contagem do que foi varrido, não do que foi
  julgado. O SQL dos quatro vai para `app/queries`, e o portão passa a pegar
  `conn.execute(`, `.executemany(` e `.commit()` em `app/routers`, provado
  reprovando de propósito antes de merecer confiança.
  Fases: 1 a varredura; 2 o portão que a cobra — nesta ordem, porque portão
  ligado antes da varredura nasce vermelho.
  Vem **por último**, depois do `043`: os itens de cima mexem nesses mesmos
  routers, e as telas novas já nascem com o SQL fora do router (norma 36).

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