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

- [-] `011-serie-duplicada-e-tolerancia-do-vencimento` — O calendário de vencimentos para de contar o mesmo dinheiro duas vezes, e a previsão só é substituída pelo lançamento que de fato a realiza. Dois defeitos medidos pelo validador da fase 3 do `003`, ambos em `app/commitments/`:
  1. **Série que é recorrente e parcelada ao mesmo tempo sobrevive ao fim das parcelas.** `jim com` fechou na parcela 06/06 em 08/09/2026 e não deve mais nada, mas o motor mantém também uma linha `recurring` com a média das mesmas cinco cobranças, e ela é considerada viva. O calendário prevê −R$ 136,44 em 06/10/2026 para uma dívida que acabou. O invariante do `001` — parcelamento tem fim, recorrência não, e cada lançamento entra uma vez só — já diz qual das duas linhas manda.
  2. **A previsão é apagada pelo mês inteiro, não pelo vencimento.** `app/commitments/calendar.py` casa lançamento com previsão por `(série, AAAA-MM)`. Uma cobrança avulsa no dia 5 esconde o vencimento do dia 25 da mesma série. Hoje o dano é zero — um único lançamento casou na janela, a dois dias do dia previsto —, e a chave por mês existe porque a mediana erra o dia. A correção é uma tolerância em dias, não a volta à comparação exata.
  **Precede o `004`** porque a projeção de 45 dias soma exatamente estes compromissos datados: um vencimento fantasma vira saldo projetado errado, e a unidade do produto é dia.

- [ ] `004-resumo-e-projecao` — A tela inicial mostra saldo, dívida total, quanto sobra este mês e a **projeção de saldo dia a dia dos próximos 45 dias**. Depende de `003` porque a projeção soma os compromissos datados: sem eles, projeta só o passado. Com cheque especial a 3,52% a.m., o real marginal se ganha não entrando no vermelho — e é esta tela que impede.

- [ ] `005-dividas-e-simuladores` — As dívidas aparecem ordenadas por taxa mensal, do cheque especial (3,52%) ao imóvel (0,72%), e o simulador responde quantas parcelas e quantos juros um aporte elimina. Inclui a decisão do Duster com **saldo de quitação e custo de transporte alternativo como parâmetro editável**, não como constante.

- [ ] `006-sync-pluggy` — As movimentações se atualizam **sob demanda e todo dia**, sem duplicar nenhuma transação, e a tela diz quando foi a última sincronização e se ela falhou. Sync que falha em silêncio é pior que sync nenhum: o painel passa a mostrar dado velho com cara de dado fresco.
  **Herdado do `001`:** `sync_runs.transactions_count` hoje guarda quantas linhas existem depois da carga, não quantas entraram na execução — a segunda ingestão do mesmo arquivo grava o total sem inserir nada. Este item decide a semântica antes de mostrar "última sincronização" na tela.

- [ ] `007-objetivo-e-linha-do-tempo` — Existe **um objetivo com data**: 6 meses de reserva (≈ R$ 49.400), com "resultado mensal ≥ 0" e "dívidas caras zeradas" como marcos no caminho. A projeção é simulação mês a mês por código determinístico, apresentada em **três cenários** (conservador · base · otimista) — nunca uma data só, que saltaria de 27 para 41 meses por causa de um mês atípico e perderia a confiança na primeira semana. Cada recálculo grava snapshot, para a linha do tempo ter passado: "em março você projetava 30 meses; hoje projeta 24" é o único sinal de progresso que este produto aceita. O financiamento imobiliário fica fora do objetivo — a 0,72% a.m. ele é a dívida mais barata, e amortizá-lo antes da reserva é o erro que a escada existe para evitar.

- [ ] `008-simulador-e-base-de-fatos` — Um formulário curto — tipo (receita ou despesa), valor, recorrência, prazo, taxa, data de início — responde **"isso me afasta ou me aproxima, e quantos dias"**, com a linha do tempo antes e depois sobrepostas. Cenário pode ser salvo e comparado lado a lado; "vender o Duster e ficar sem carro" contra "vender e comprar um usado de R$ 25 mil" é a decisão em aberto hoje e merece ser vista, não argumentada. O mesmo formulário captura os fatos que só o humano sabe (saldo de quitação, taxa do cartão, custo de transporte) em `plan_facts`, com valor, unidade, origem, data e prazo de validade — estruturado para consulta, e a projeção se move na tela assim que o fato entra.

- [ ] `009-ia-consultora` — A IA **pergunta o que falta**: escolhe o fato ausente ou vencido cuja resposta mais move a projeção e faz **uma** pergunta, dizendo qual número ela muda. Nunca repergunta o que foi respondido, e não insiste — pergunta ignorada some e volta só quando voltar a importar; enquanto isso a tela declara a premissa que está assumindo. Também explica o resultado do simulador, orienta o próximo passo, responde pergunta livre sobre os próprios dados e classifica o resíduo que as regras não pegaram. **A IA nunca calcula**: se ela computasse "isso te afasta 11 dias" erraria, e um número errado na unidade central do produto destrói a confiança em tudo o mais. Sem chave ou com erro, a tela mostra o número determinístico e diz que a leitura da IA está indisponível.

## Dívida técnica

Bloco separado de propósito. Pendência de processo — portão, fluxo de CI,
veredicto, varredura — não é dependência de item de produto nenhum, e promovê-la
ao topo da fila é a régua local certa e o agregado errado.

- [ ] `010-lint-e-formatador-python` — Existe portão de lint e formatação para o
  código Python, rodando no `gates_runner.sh` e no fluxo de CI. Quatro validadores
  seguidos registraram a ausência: hoje `ruff` não está no ambiente e nenhum
  portão mede estilo, import morto ou variável não usada. É consequência
  declarada de o projeto rodar em modo processo-apenas, sem pack de stack — e
  por isso a compensação precisa ser explícita, não presumida.

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

- **`009-ia-consultora`** — a qualidade da resposta do Gemini só se julga lendo. Como
  verificar: fazer três perguntas sobre os próprios dados e conferir que os números
  citados batem, dígito a dígito, com os do motor determinístico.

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