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

- [ ] `001-base-e-login` — Só entra quem tem a senha, e os 1.942 lançamentos já extraídos estão no banco com o sinal normalizado (negativo = dinheiro saindo, inclusive em cartão), sem duplicata, e com transferência entre contas próprias marcada para não virar receita.

- [ ] `002-gastos-tres-eixos` — Os gastos se leem por grupo, categoria, beneficiário, **natureza** (fixa · variável · eventual) e **essencialidade** (essencial · importante · supérfluo), em qualquer período, com drill-down até a transação. O cruzamento variável × supérfluo é a lista de corte; fixa × essencial é o piso de sobrevivência. As regras de classificação são tabela editável na tela, não código.

- [ ] `003-comprometido` — O que já está comprometido e quando sai da conta: assinatura recorrente com valor médio, meses seguidos e ação "não uso mais"; parcelamento com data de término e quanto de caixa ele libera ao acabar; e o calendário de vencimentos.

- [ ] `004-resumo-e-projecao` — A tela inicial mostra saldo, dívida total, quanto sobra este mês e a **projeção de saldo dia a dia dos próximos 45 dias**. Depende de `003` porque a projeção soma os compromissos datados: sem eles, projeta só o passado. Com cheque especial a 3,52% a.m., o real marginal se ganha não entrando no vermelho — e é esta tela que impede.

- [ ] `005-dividas-e-simuladores` — As dívidas aparecem ordenadas por taxa mensal, do cheque especial (3,52%) ao imóvel (0,72%), e o simulador responde quantas parcelas e quantos juros um aporte elimina. Inclui a decisão do Duster com **saldo de quitação e custo de transporte alternativo como parâmetro editável**, não como constante.

- [ ] `006-sync-pluggy` — As movimentações se atualizam **sob demanda e todo dia**, sem duplicar nenhuma transação, e a tela diz quando foi a última sincronização e se ela falhou. Sync que falha em silêncio é pior que sync nenhum: o painel passa a mostrar dado velho com cara de dado fresco.

- [ ] `007-plano-e-ia` — O plano de curto, médio e longo prazo se calcula por **código determinístico** (renda regular, piso essencial, sobra projetada, escada de dívida, data-alvo da reserva) e a IA explica o próximo passo com o número que o justifica, responde pergunta livre sobre os próprios dados e classifica o que as regras não pegaram. Sem chave ou com erro, a tela mostra o número e diz que a leitura da IA está indisponível — nunca quebra.

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

- **`007-plano-e-ia`** — a qualidade da resposta do Gemini só se julga lendo. Como
  verificar: fazer três perguntas sobre os próprios dados e conferir que os números
  citados batem com os do motor determinístico.

## Entradas pendentes do humano

Não bloqueiam a construção — o produto as trata como parâmetro editável —, mas
sem elas o plano de curto prazo fica com uma faixa em vez de um número.

- **Saldo de quitação antecipada do CDC do Duster** (menor que o saldo devedor de
  R$ 39.176,36; está no app do banco).
- **Custo mensal de transporte sem o carro**, e se há outro carro na casa.
- **Taxa dos cartões** (R$ 16.744,62): rotativo ou parcelado muda a posição deles
  na escada.