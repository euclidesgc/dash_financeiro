# Consultor de IA (chat)

Uma conversa dentro do painel (`/app/advisor`) em que o dono pergunta sobre as próprias contas e pede
ajustes: "liste os gastos com delivery de agosto", "passe esses para Alimentação", "quanto sai de
parcela e financiamento nos próximos seis meses", "quanto preciso guardar por mês para quitar o
Duster em um ano", "que dívida quitar primeiro para sobrar dinheiro no mês".

A regra que sustenta o desenho é a invariante 23: **o modelo interpreta e explica; quem calcula é
função testada.** O modelo não recebe a base inteira nem faz conta. Ele escolhe uma ferramenta, o
servidor roda uma função determinística e devolve o resultado pronto, em centavos inteiros, e o modelo
só redige a resposta a partir disso.

## O que já existe e fica como está

- A tela antiga `/consultor` (Jinja) e `app/advisor/gemini.py`: uma leitura de uma pergunta só, sem
  ferramentas, pelo Gemini via `httpx`, com a chave vinda da tela Configuração (`advisor_config`) ou de
  `GEMINI_API_KEY`. O chat não a reaproveita nem a remove; ela sai quando a SPA cobrir o painel antigo.
- As funções determinísticas que o chat expõe como ferramentas (tabela abaixo). Onde a conta ainda não
  existe, a fatia que precisa dela cria a função com teste antes de expor a ferramenta.

## Arquitetura

```
SPA /app/advisor ──POST /api/advisor/conversations/{id}/messages──▶ router (traduz HTTP)
                                                                     │
                                          app/advisor/chat.py ◀──────┘  laço de ferramentas
                                           │            │
                          ChatProvider (porta)        app/advisor/tools.py ── funções testadas
                          ├─ AnthropicProvider          (queries, projection, debts, taxonomy)
                          ├─ GeminiProvider
                          └─ dublês de teste (tests/advisor_fakes.py, tests/e2e_app.py)
                                           │
                                SQLite: advisor_conversations, advisor_messages,
                                        advisor_proposals, advisor_proposal_items
```

- **Porta de provedor:** `app/advisor/provider.py` define a conversa num formato neutro (mensagem com
  partes de texto, pedido de ferramenta e resultado de ferramenta) e o protocolo
  `ChatProvider.reply(system, messages, tools)`. Cada adaptador traduz esse formato para o do seu
  provedor e de volta. A mensagem do assistente guarda também os blocos crus que o provedor devolveu
  (assinatura de pensamento da Anthropic, `thoughtSignature` do Gemini), reenviados sem mudança ao
  mesmo provedor; outro provedor reconstrói a mensagem a partir das partes neutras, e uma conversa
  começada num provedor continua no outro.
- **Adaptadores:** `AnthropicProvider` usa o SDK oficial `anthropic` (declarado no `pyproject.toml`,
  norma 15), `messages.create` com `tools` e pensamento adaptativo, modelo em `DASH_ADVISOR_MODEL`
  (padrão `claude-opus-5`). `GeminiProvider` usa *function calling* do Gemini por `httpx`, do mesmo
  jeito que a tela antiga, sem SDK novo, modelo em `DASH_ADVISOR_GEMINI_MODEL` (padrão
  `gemini-3.8-flash`, porque os modelos `gemini-2.5-*` da tela antiga respondem 404 a contas novas).
- **Seleção** (`app/advisor/providers.py`): Anthropic se `ANTHROPIC_API_KEY` existe; senão Gemini se
  há chave do Gemini (tela Configuração ou `GEMINI_API_KEY`); senão a tela explica em pt-BR como
  configurar qualquer um dos dois (`.env` e `docs/setup-secrets.md`) e o resto do painel segue
  funcionando. A chave só vem do ambiente ou da configuração; nunca vai para resposta, log ou banco.
- **Laço manual:** enquanto o provedor pede ferramenta, o servidor roda cada ferramenta pedida e
  devolve todos os resultados numa única mensagem. Laço manual em vez do *tool runner* porque a
  escrita precisa parar no meio do laço para pedir confirmação, porque evita API beta e porque serve
  aos dois provedores. Teto de 8 voltas por pergunta; ao estourar, a resposta diz que a pergunta
  ficou grande demais.
- **Guarda de números:** a resposta final passa por `app/advisor/cited.py::uncited` contra o texto de
  todos os resultados de ferramenta da conversa. Valor em reais que nenhuma ferramenta devolveu troca
  a resposta por um aviso, e é o aviso que fica no histórico.
- **Rota síncrona:** as rotas são `def` e os adaptadores usam cliente síncrono (norma 31: I/O
  bloqueante fora do laço de eventos).
- **Resposta inteira, sem streaming:** o chat envia a pergunta e mostra "Consultando suas contas…" até
  a resposta pronta. Streaming com ferramentas no meio custa um protocolo de eventos na API e na tela
  por um ganho pequeno em respostas curtas; fica fora do escopo inicial.
- **Erros:** recusa do modelo, resposta cortada, chave recusada, excesso de chamadas, sobrecarga,
  modelo inexistente e falta de rede viram mensagem em pt-BR que diz o próximo passo. Falha do
  provedor não grava nada; a pergunta continua no campo.
- **Persistência:** migração `026_advisor_chat.sql` com `advisor_conversations` (id, título, criada e
  atualizada em) e `advisor_messages` (conversa, ordem, papel `user`/`assistant`/`tool`, conteúdo em
  JSON com as partes neutras e os blocos crus, provedor, modelo, tokens de entrada e saída). O
  histórico reenviado ao modelo sai dessa tabela, sempre por acréscimo, nunca reescrito; a volta
  inteira de uma pergunta é gravada numa transação só, depois da resposta.
- **Login:** todas as rotas ficam atrás da sessão (invariante 24).
- **Testes:** dublês escritos à mão implementam a porta e devolvem roteiros prontos; os adaptadores
  são testados com uma função `create` falsa (Anthropic) e `httpx.MockTransport` (Gemini). Nenhum
  teste chama a rede; a integração usa `TestClient` com banco real e o dublê injetado por
  `dependency_overrides`, e o e2e sobe o backend por `tests/e2e_app.py`, que faz o mesmo.

## Ferramentas

Toda saída de valor é em centavos inteiros, negativo = dinheiro saindo (invariante 22). Transferência
entre contas próprias e estorno ficam fora dos totais (invariante 25), porque as funções reusadas já
aplicam esse filtro.

| Ferramenta | Entrada | Saída | Função determinística | Fatia |
|---|---|---|---|---|
| `search_transactions` | período, conta, texto, categoria, visão (gastos ou entradas), limite ≤ 50 | lançamentos (id, data, descrição, recebedor, valor, categoria) e total e contagem do filtro inteiro | `app/queries/expenses.py::list_expenses` e `sum_expenses`, com filtro novo por categoria em `_where` | 070 |
| `spending_summary` | período, conta | total por categoria, entradas, gastos e saldo do período, e o total de cada mês do período | `sum_by_category`, `period_result` e função nova `monthly_totals` em `app/queries/expenses.py` | 071 |
| `propose_recategorization` | ids de lançamento, categoria de destino | proposta pendente (id, quantos mudam, soma) — **não grava a categoria** | função nova `app/advisor/proposals.py::propose`, que valida ids e categoria | 072 |
| `commitments_by_month` | meses à frente (1 a 24) | por mês: parcelas de cartão, financiamentos, assinaturas vivas, total, e o que termina naquele mês | função nova `app/projection/schedule.py::schedule_by_month`, sobre `app/commitments/live.py` e `app/financings/math.py` | 073 |
| `debt_payoff` | dívida, prazo em meses (opcional) | valor para quitar hoje e no fim do prazo, e quanto guardar por mês para chegar lá | função nova `app/debts/payoff.py::payoff_at` e `saving_plan`, sobre `present_value_cents` e a escada de `app/debts/ladder.py` | 074 |
| `debts_by_liquidity` | — | dívidas e compras parceladas ordenadas por dinheiro liberado no mês por real pago, com o valor de quitação e a parcela liberada | função nova `app/debts/payoff.py::rank_by_liquidity` | 075 |

## Regras de escrita

1. O modelo **nunca** grava. A única ferramenta de escrita, `propose_recategorization`, cria uma
   proposta pendente em `advisor_proposals`, com um item por lançamento em `advisor_proposal_items`
   guardando categoria e origem anteriores e a categoria nova.
2. A tela mostra a proposta como um cartão dentro da conversa: cada lançamento com data, descrição,
   valor, "categoria atual → nova", e os botões **Aplicar** e **Descartar**. Só o clique do dono chama
   `POST /api/advisor/proposals/{id}/apply`, que aplica tudo numa transação só pela mesma regra de
   ajuste manual de `app/taxonomy/override.py` (sobrevive à próxima atualização da Pluggy).
3. A proposta aplicada pode ser desfeita (`POST /api/advisor/proposals/{id}/undo`), que devolve a
   categoria e a origem anteriores de cada item. Se um lançamento mudou depois da aplicação, o desfazer
   pula esse item e diz quantos pulou.
4. A proposta não expira: fica pendente até o dono aplicar ou descartar, e o registro guarda quando
   foi aplicada, descartada ou desfeita.
5. Descrição de lançamento e nome de recebedor são dado, não instrução: chegam ao modelo dentro do
   `tool_result`, e o prompt de sistema diz que texto de lançamento nunca muda o que ele faz.

## Fora do escopo

Streaming da resposta; criar ou apagar categoria, criar regra de classificação ou marcar "não é gasto"
pelo chat; editar taxa, prazo ou saldo de dívida pelo chat (continuam parâmetros de tela, invariante
26); trocar o provedor da tela antiga `/consultor`; guardar a chave da IA pela tela nova; desconto de
antecipação de compra parcelada (o painel não sabe, então a quitação de parcelado é o valor nominal
restante e a resposta diz isso).
