# PRD — Sincronização real com a Pluggy

**Item:** `037-sincronizacao-real-com-a-pluggy` · **Trilha:** completa

## Problema

**O painel mostra o extrato de 05/09/2026 com cara de extrato de hoje.** O botão
**Sincronizar agora** não fala com a Pluggy: relê um arquivo que dois scripts
geram à mão, fora do painel. As 14 sincronizações seguintes à primeira inseriram
zero lançamentos e contam como bem-sucedidas, então o Resumo exibe uma data
recente sobre um dado parado — o modo de falha que o item `006` existe para
impedir. Não há rotina diária. Toda vez que abre o painel, o dono decide corte,
dívida e reserva sobre o extrato de 05/09/2026.

**O gasto histórico está R$ 2.346,09 abaixo do real.** Catorze compras em dólar,
de dez/2025 a ago/2026, estão gravadas com o valor em dólar, e não com o valor em
reais que o cartão cobrou: a STRIPE Z.AI de US$ 64,80 conta como R$ 64,80 e
custou R$ 350,57.

**A carga descarta o que a Pluggy manda.** Não chegam à base o CPF ou CNPJ de
quem pagou (624 lançamentos no bruto) e de quem recebeu (516), o meio de
pagamento (720), o código de ramo do estabelecimento (978), o tipo de operação
(907), se o lançamento está pendente ou lançado, a fatura e a data da compra. Nem
o banco de cada conta: o nome de instituição gravado repete o nome do cartão — a
conta "platinum" é o cartão do Nubank —, e o banco de verdade é a conexão da
Pluggy. Os itens `038` a `041` dependem desses campos.

**O id da Pluggy não é estável.** A compra de cartão que passa de pendente a
lançada pode voltar com outro id. A base tem 139 lançamentos pendentes, todos de
cartão, 43 com data futura (parcelas). Buscar na Pluggy e só acrescentar o que é
novo transforma cada um deles em duplicata; apagar tudo o que não veio na
resposta apaga junto o que está preso ao lançamento e o histórico que a Pluggy
já não tem — ela guarda 12 meses, e a base local é o arquivo de longo prazo.

## Público
> Reconciliado em D-008.

**O dono**, único usuário, com o painel rodando local. Usa a sincronização de dois
jeitos: aperta **Sincronizar agora** no Resumo antes de decidir alguma coisa, ou
deixa o app de pé e espera que o extrato se atualize sozinho. Já sabe ler no
Resumo a data da última sincronização e quantos lançamentos ela trouxe. Tem
conexões em meu.pluggy.ai com CAIXA, Itaú, Mercado Pago e Nubank, mais o Safra,
ainda sem conta associada; é o único que sabe o id de cada conexão — copiado do
dashboard.pluggy.ai, porque a API da Pluggy não lista as conexões existentes — e
o único que consegue refazer o login de um banco quando o consentimento vence.
Nunca viu o painel dizer, banco a banco, quando a Pluggy o atualizou e qual pede
novo login.

## Escopo
> Reconciliado em D-008.

- **Sincronizar busca na Pluggy.** O botão e a rotina diária buscam os
  lançamentos direto na Pluggy, conta a conta de cada conexão registrada, desde a
  última busca bem-sucedida de cada conta e sem data final, para que as parcelas
  futuras continuem chegando. A primeira busca de uma conta é completa. Nenhum
  passo manual fica no caminho da busca; sem credencial da Pluggy, a
  sincronização recusa antes de buscar, com mensagem em português, e nada é
  gravado.
- **O valor é em reais, e o sinal diz a direção do dinheiro.** Compra em moeda
  estrangeira entra pelo valor que o cartão cobrou em reais: a STRIPE Z.AI de
  US$ 64,80 entra como −R$ 350,57. Negativo é dinheiro saindo em qualquer tipo de
  conta; no cartão, onde a Pluggy inverte o sinal, a carga o normaliza.
- **A carga guarda o que a Pluggy manda:** pendente ou lançado, moeda, meio de
  pagamento, tipo de operação, código de ramo do estabelecimento, fatura, data da
  compra, a conexão de cada conta e o registro original de cada lançamento. A
  contraparte segue o sentido do dinheiro — na saída é quem recebeu, na entrada
  quem pagou, no cartão o estabelecimento —, com o nome e o CPF ou CNPJ que a
  Pluggy mandar.
- **As marcas são do painel.** Transferência entre contas próprias, pagamento de
  fatura, estorno, saque e parcela são marcados a cada carga, sobre a base
  inteira, e dão para o mesmo lançamento a mesma marca que os scripts manuais
  davam. Crédito pago pelo CPF do dono é transferência entre contas próprias
  mesmo sem o par na base. Marca que muda de uma sincronização para outra é
  contada, e a tela mostra. Lançamento sem categoria da Pluggy fica sem
  categoria, e o grupo vem da classificação.
- **Lançamento recriado pela Pluggy é religado, não duplicado.** A compra
  pendente que volta lançada com outro id continua sendo a mesma linha, com o
  mesmo número interno, e o que está preso a ela sobrevive. Par ambíguo não
  religa: de duas compras de R$ 30,00 no mesmo dia, com a mesma descrição, que
  voltam com ids novos, as duas antigas saem com lápide e as duas novas entram.
- **Só sai da base o que sumiu sem par**, dentro do período buscado e de conta
  cuja conexão está em dia e cuja resposta veio inteira; sai com lápide que
  guarda o registro original e o que o dono anotou. Quando faltam linhas demais
  na resposta de uma conta, a remoção daquela conta é suspensa e a tela avisa:
  uma resposta vazia para uma conta com 40 lançamentos no período não apaga
  nenhum. Lançamento mais antigo que o período buscado nunca sai.
- **`pluggy_items` é o registro das conexões, e cada banco tem estado na tela.** O
  dono registra e remove uma conexão pelo id que copia do dashboard.pluggy.ai —
  a API da Pluggy não lista conexões —, por comando na fase 2 e pela seção
  "Conexões da Pluggy" de `/configuracao` na fase 3, que mostra cada conexão com
  seu estado e o `lastUpdatedAt`. A tela mostra, por banco, quando a Pluggy o
  atualizou pela última vez e qual pede novo login em meu.pluggy.ai. A conexão
  que pede login não perde lançamento e não impede as outras de sincronizar. A
  conexão que a Pluggy responde como inexistente aparece como "não existe mais":
  nenhum lançamento das contas dela sai, e a tela pede o id novo; a conta que
  volta por uma conexão nova mantém os seus lançamentos. Pedir ao banco uma
  atualização acontece no máximo uma vez por hora por conexão.
- **Uma sincronização por vez, pelo botão ou pelo relógio.** A rotina diária roda
  sozinha enquanto o app está de pé e busca cada conexão que a Pluggy atualizou
  desde a busca anterior; ela é ligada por configuração do ambiente, fica
  desligada nos testes e ligada no ambiente do dono. O botão apertado durante uma
  execução diz que já há uma em andamento, a tela acompanha o andamento, e
  recarregar a página não sincroniza de novo. Uma falha na escrita desfaz a carga
  inteira e fica registrada como falha.

## Não-escopo

- **Ler, filtrar e agrupar por banco e por conta não entra.** É o item `038`, que
  depende da conexão de cada conta gravada aqui; o nome editável de cada banco e
  o apelido de cada conta também são dele.
- **Cadastro de beneficiário, fusão e consulta de CNPJ não entram.** São o item
  `039`, que parte do CPF ou CNPJ de contraparte gravado aqui. Este item guarda a
  contraparte como a Pluggy a manda, sem transformá-la em cadastro nem buscar
  razão social na BrasilAPI.
- **Classificação em camadas e o eixo operação não entram.** São o item `040`, que
  deriva a operação do meio de pagamento e do tipo de operação gravados aqui.
  Neste item, nenhum dos dois muda classificação nem total, e o ajuste de um
  lançamento só também é do `040`.
- **A tela de lançamentos não entra.** Listar lançamento a lançamento, filtrar por
  pendente ou lançado, agrupar por fatura e por compra parcelada e editar em
  massa são o item `041`; é nela que o dono vê a contraparte, o meio de pagamento
  e a fatura que esta carga guarda.
- **A IA não entra.** A sugestão de classificação por beneficiário é o item
  `043`; a sincronização deste item não chama o modelo.
- **O que conta como gasto não muda para o lançamento pendente.** O pendente conta
  no gasto como qualquer lançamento. A única mudança deste item no gasto
  histórico é a do dólar, e ela se mede exata; mexer no pendente misturaria duas
  mudanças na mesma medida. A carga guarda o estado, e o filtro pendente ×
  lançado é do `041`.
- **Reconectar um banco com consentimento vencido não entra.** A renovação é
  interativa, com login no banco, em meu.pluggy.ai, e só o dono a faz; o painel
  diz qual banco a pede.
- **Sincronizar com o app desligado não entra.** A rotina vive no processo do
  painel, que roda local; com ele desligado nada busca, e o Resumo diz há quantos
  dias o dado está parado.
- **Apagar os scripts manuais de extração e consolidação não entra.** Eles saem do
  caminho do botão e ficam como ferramenta manual e como oráculo dos testes: é
  contra eles que se prova que as marcas do painel são as mesmas.

## Métricas de sucesso
> Reconciliado em D-008.

| Métrica | Onde se observa | Alvo |
|---|---|---|
| Lançamentos de 05/09/2026 em diante presentes na base | Validação de campo ao fim do item: a base do dono depois de uma sincronização real, conferida contra o que a Pluggy tem para as 10 contas vivas | Todos presentes, e a execução registra mais de zero inseridos — as 14 anteriores registraram zero |
| Compra presente duas vezes, uma pendente e outra lançada | Base do dono: mesma conta, mesmo valor, mesma parcela e mesma data da compra, em estados diferentes | Zero em toda sincronização real; cada uma das 139 pendentes de 05/09/2026 é uma linha só |
| Gasto de dez/2025 a ago/2026 depois da carga que lê o valor em reais | Base do dono, antes e depois da carga da fase 1 sobre o mesmo bruto de 05/09/2026, declarado no PR da fase | Sobe exatamente R$ 2.346,09 (234.609 centavos a mais de saída), todos das 14 compras em USD, sem outra origem |
| Lançamento que sai da base sem lápide | Base do dono, a cada sincronização: lançamentos antes + inseridos − lápides novas = lançamentos depois | Zero |

## Riscos

- **Números mudam, e cada mudança tem lugar e tamanho.** O gasto de dez/2025 a
  ago/2026 sobe R$ 2.346,09 na fase 1, e com ele tudo o que o painel calcula a
  partir do gasto desses meses. Os 21 lançamentos sem categoria da Pluggy
  (−R$ 233,98) podem trocar de grupo, sem mudar o total. A partir da fase 2 os
  lançamentos novos entram e os que a Pluggy cancelou saem, e todo total de
  05/09/2026 em diante se move — o efeito pretendido. Os números de referência de
  05/09/2026 são congelados e não trazem a correção do dólar: o gasto de seis
  meses de referência (R$ 103.772,33) fica abaixo do que o painel mostra para o
  mesmo período. Resposta: o PR da fase 1 declara a medida, incluindo quanto da
  correção cai nos seis meses de referência; nenhum número de referência é
  reescrito.
- **Conexão MeuPluggy com consentimento vencido.** A conexão para de sincronizar
  até o dono refazer o login. Resposta: as contas dela não perdem lançamento, as
  outras conexões sincronizam, e a tela diz qual banco reconectar em
  meu.pluggy.ai e quando a Pluggy o atualizou pela última vez. Quem age é o dono.
- **O pedido de atualização pode não chegar ao banco.** O MeuPluggy não é conexão
  regulada, e o agregador atualiza no ritmo dele; a Pluggy atualiza cada conexão
  sozinha a cada 24, 12 ou 8 horas, conforme o plano contratado na Pluggy.
  Resposta: o painel se comporta igual nos dois casos — busca o que a Pluggy tem
  e mostra a hora em que ela atualizou cada banco. Pedido recusado por ter vindo
  antes de uma hora não rebaixa a sincronização. A validação de campo ao fim do
  item registra qual dos dois casos acontece.
- **A sincronização de fundo e as telas disputam o SQLite**, que aceita um
  escritor por vez. Resposta: a rede roda fora da transação e a escrita é curta;
  há uma sincronização por vez; falha na escrita desfaz a carga inteira, fica
  registrada como falha e não derruba a tela.
- **A base guarda CPF e CNPJ de terceiros, e o painel fala com a Pluggy com
  credencial.** Resposta: a credencial mora só no ambiente, nunca no repositório,
  na página ou no log; o painel faz só uma lista fechada de chamadas à Pluggy e
  recusa qualquer outra antes de sair; nenhum teste sai para a rede, por nenhuma
  forma de chamada; a amostra de teste é anonimizada; a base fica fora do
  controle de versão e atrás do login. O `security-auditor` revisa as fases 1 e 2.
- **Decisão: o que some da Pluggy sai da base com lápide, em vez de ficar marcado
  como removido.** Alternativa descartada: a marca obrigaria as cerca de 20
  consultas que leem lançamentos a filtrar, e uma esquecida corrompe número em
  silêncio. Custo aceito: o lançamento removido some de toda tela e só se
  recupera pela lápide. Se o dono encontrar na lápide um lançamento que o banco
  ainda mostra, a regra que suspende a remoção volta a ele.
- **Decisão: religar só o par inequívoco.** Alternativa descartada: migrar o que
  está preso ao lançamento por semelhança a cada sincronização, o que duplica o
  mecanismo e erra justamente no par ambíguo. Custo aceito: nas compras iguais do
  mesmo dia, o que estava preso às linhas antigas vai para a lápide com elas e não
  segue as novas.
- **Decisão: a categoria inventada por expressão regular não é portada.**
  Alternativa descartada: portá-la, o que grava nome de grupo como categoria, por
  fora da classificação. Custo aceito: os 21 lançamentos podem cair em "Outros"
  até uma regra do dono pegá-los, ou até o `040` permitir ajustar um lançamento
  só.
