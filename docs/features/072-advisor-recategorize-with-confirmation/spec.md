# SPEC 072 — Consultor de IA: trocar a categoria com confirmação

Desenho geral em `docs/consultor-chat.md` (seção "Regras de escrita"). Esta SPEC fixa o que a fatia 072
acrescenta às 070 e 071.

## Decisões

1. **Migração `027_advisor_proposals.sql`.** `advisor_proposals` (conversa com `ON DELETE CASCADE`,
   categoria de destino, status `pending`/`applied`/`discarded`/`undone`, criada, aplicada, descartada
   e desfeita em, `undo_skipped`) e `advisor_proposal_items` (proposta, lançamento, retrato de data,
   descrição e valor, categoria e origem anteriores). O lançamento **não** tem chave estrangeira: a
   ingestão apaga lançamentos (`app/ingest/loader.py`), e o registro de auditoria não pode sumir nem
   travar a ingestão. O retrato de data, descrição e valor mantém o cartão legível mesmo assim.
2. **Ferramenta `propose_recategorization`** em `app/advisor/tools.py`: entrada `target_category`
   (obrigatória, resolvida por `resolve_category` contra as categorias existentes) e, para escolher os
   lançamentos, `transaction_ids` (ids devolvidos por `search_transactions`) **ou** o mesmo filtro de
   `search_transactions` (período, texto, categoria atual, conta, visão). Pelo filtro, o servidor
   resolve os ids pelo mesmo `list_expenses` da busca, então "esses" é deterministicamente o que a
   busca anterior listou, inclusive além dos 50 mostrados. Id desconhecido, filtro vazio, mais de 200
   lançamentos ou todos já na categoria de destino viram erro da ferramenta com o próximo passo.
   Lançamento que já está na categoria de destino sai da proposta. A saída traz `proposal_id`,
   contagem, total em centavos e em reais, e os itens; **não grava a categoria**.
3. **Conversa na ferramenta.** `run_tool(conn, call, *, conversation_id)`: a proposta pertence à
   conversa e é inserida na mesma transação que grava a volta da pergunta (`send` dá o commit no fim);
   falha do provedor no meio não deixa proposta órfã.
4. **Categoria nova não se cria pelo chat.** A API de categorias cria categoria (`POST
   /api/categories`), mas `docs/consultor-chat.md` deixa criar categoria fora do escopo do chat, e o
   modelo não grava: a ferramenta devolve a lista existente e o prompt manda sugerir a tela Categorias.
5. **Mesmo caminho da troca manual.** `app/taxonomy/override.py` ganha `recategorize(conn, changes)`,
   que valida categoria e lançamento de cada troca, roda as mesmas instruções de `set_manual`
   (categoria e `category_source = 'manual'`) e `restore_auto`, e reclassifica uma vez, **sem commit**
   (quem chama é dono da transação). `set_manual` e `restore_auto` passam a usar as mesmas instruções.
6. **Serviço `app/advisor/proposals.py`:** `propose`, `apply`, `discard`, `undo`. Cada transição começa
   por `UPDATE … WHERE status = <anterior>`: a primeira escrita pega o lock do SQLite, e o segundo
   clique encontra o status já mudado e devolve a proposta como está (idempotente). Transição de um
   status que não permite (aplicar descartada) é `ProposalStateError`. `apply` regrava categoria e
   origem anteriores de cada item a partir do lançamento no momento de aplicar (o desfazer volta ao
   que era antes do clique), e lançamento apagado ou categoria de destino apagada é
   `StaleProposalError`, sem gravar nada. `undo` pula o item cuja categoria atual não é mais a de
   destino com origem manual, ou cuja categoria anterior manual não existe mais, e grava quantos
   pulou. SQL em `app/queries/advisor_proposals.py` (norma 33).
7. **API:** `POST /api/advisor/proposals/{id}/apply`, `/discard` e `/undo` devolvem a proposta; 404
   desconhecida, 409 estado ou proposta desatualizada, com mensagem pt-BR. A entrada do assistente
   (`Entry`) ganha `proposals`: as propostas criadas naquela volta, com status atual, itens (data,
   descrição, valor, rótulo de/para) e total.
8. **Prompt:** "passe esses para X" → `propose_recategorization` com o mesmo filtro da busca anterior
   ou os ids que o dono escolheu; nada muda até o dono clicar em Aplicar no cartão; nunca dizer que já
   mudou; categoria inexistente → sugerir a tela Categorias.
9. **Tela:** `proposal-card.tsx` dentro de `chat-message-item.tsx`. Botões desabilitados enquanto a
   ação roda (clique duplo). Ao aplicar ou desfazer, a proposta devolvida substitui a do cache da
   conversa e invalidam-se `['expenses']` (lista, totais por categoria, resultado do período, sinal do
   mês) e `categoriesQueryKey` (uso das categorias); descartar só atualiza a conversa.
10. **E2E:** o provedor falso de `tests/e2e_app.py` passa a propor quando a pergunta pede para passar
    lançamentos para outra categoria.

## Arquivos

Backend: `app/migrations/sql/027_advisor_proposals.sql`, `app/migrations/NUMBERING.md`,
`app/queries/advisor_proposals.py`, `app/advisor/proposals.py`, `app/advisor/tools.py`,
`app/advisor/chat.py`, `app/taxonomy/override.py`, `app/routers/advisor_chat.py`, `tests/e2e_app.py`.
Testes: `tests/test_advisor_proposals.py`, `tests/test_advisor_tools.py`, `tests/test_advisor_chat.py`,
`tests/test_migrations.py`. Front: `src/features/advisor/types/advisor.ts`,
`src/features/advisor/api/{apply,discard,undo}-proposal.ts`, `src/features/advisor/api/proposal-cache.ts`,
`src/features/advisor/components/proposal-card.tsx`, `chat-message-item.tsx`, `advisor-chat.tsx`,
`src/testing/mocks/handlers.ts` e testes; `e2e/advisor.spec.ts`. Docs: `docs/consultor-chat.md`,
`docs/design.md`.

## Skills

python-*, api-requests, component-robustness, component-testing, interface-design, e2e-testing.
