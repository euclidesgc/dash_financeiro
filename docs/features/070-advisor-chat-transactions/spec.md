# SPEC 070 — Consultor de IA: conversa e lista de lançamentos

Desenho geral em `docs/consultor-chat.md`. Esta SPEC fixa o que a fatia 070 cria.

## Decisões

1. **Porta de provedor com dois adaptadores.** `app/advisor/provider.py` define o formato neutro da
   conversa (`Message` com partes `TextPart`, `ToolCall`, `ToolResult`), `ToolSpec`, `Reply` e o
   protocolo `ChatProvider.reply(system, messages, tools) -> Reply`. Adaptadores:
   `app/advisor/anthropic_provider.py` (SDK oficial `anthropic`, `messages.create` com `tools` e
   pensamento adaptativo, modelo em `DASH_ADVISOR_MODEL`, padrão `claude-opus-5`) e
   `app/advisor/gemini_provider.py` (function calling do Gemini por `httpx`, como a tela antiga, modelo
   da tela Configuração). Cada mensagem do assistente guarda também os blocos crus do provedor que a
   gerou (`raw`), reenviados sem mudança ao mesmo provedor (assinatura de pensamento); outro provedor
   reconstrói a partir das partes neutras.
2. **Seleção.** `app/advisor/providers.py::select_provider`: Anthropic se `ANTHROPIC_API_KEY` existe;
   senão Gemini se há chave (tela Configuração ou `GEMINI_API_KEY`); senão nenhum. A chave nunca vai
   para resposta de API, log nem banco.
3. **Laço manual** em `app/advisor/chat.py::send`: até 8 voltas; cada volta roda todas as chamadas de
   ferramenta pedidas e devolve todos os resultados numa só mensagem. Ao estourar, a resposta diz que a
   pergunta ficou grande demais. A volta inteira (pergunta, pedidos, resultados, resposta) é gravada
   numa transação só, depois da resposta; falha do provedor não grava nada.
4. **Guarda de números.** A resposta final passa por `app/advisor/cited.py::uncited` contra o texto de
   todos os resultados de ferramenta da conversa; valor em reais não citado troca a resposta por um
   aviso (invariante 23).
5. **Ferramenta `search_transactions`** em `app/advisor/tools.py`: resolve categoria (chave ou rótulo,
   sem acento nem maiúscula) e conta (nome ou instituição) por funções determinísticas, chama
   `list_expenses` com filtro novo `category` em `_where` de `app/queries/expenses.py`, e devolve
   contagem, total em centavos e já formatado por `app/formatting.py::brl` (extraído de
   `app/routers/render.py`), e até 50 lançamentos. Entrada inválida vira `is_error` com a lista do que
   existe.
6. **Rotas síncronas** (`def`, norma 31) em `app/routers/advisor_chat.py`, prefixo `/api/advisor`, atrás
   do guarda de sessão: `GET /status`, `GET /conversations`, `POST /conversations`,
   `GET /conversations/{id}`, `POST /conversations/{id}/messages`. Dependência `get_provider`
   (resolve) e `require_provider` (valida: 503 com texto de configuração). O router só traduz HTTP.
7. **Persistência:** migração `026_advisor_chat.sql` com `advisor_conversations` e `advisor_messages`
   (papel `user`/`assistant`/`tool`, conteúdo JSON, provedor, modelo, tokens). SQL em
   `app/queries/advisor_chat.py`.
8. **Tela** `src/features/advisor/` (tipos, api, componentes) e rota `src/app/routes/advisor.tsx` em
   `paths.advisor = '/advisor'`, link "Consultor" no `AppHeader`. Estado da conversa atual pela
   URL (`?c=<id>`), senão a mais recente.
9. **e2e** sobe o backend por `tests/e2e_app.py`, que troca `get_provider` por um provedor roteirizado
   (chama a ferramenta e responde com os números dela). Nenhum teste usa rede.

## Arquivos

Backend: `app/advisor/{provider,anthropic_provider,gemini_provider,providers,tools,chat}.py`,
`app/formatting.py`, `app/queries/advisor_chat.py`, `app/queries/expenses.py`,
`app/routers/advisor_chat.py`, `app/routers/render.py`, `app/config.py`, `app/main.py`,
`app/migrations/sql/026_advisor_chat.sql`, `pyproject.toml`, `uv.lock`, `.env.example`.
Testes: `tests/test_advisor_chat*.py`, `tests/e2e_app.py`. Front: `src/features/advisor/**`,
`src/app/routes/advisor.tsx`, `src/app/router.tsx`, `src/config/paths.ts`,
`src/components/layouts/app-header.tsx`, `src/testing/mocks/handlers.ts`, `e2e/advisor.spec.ts`,
`scripts/e2e-backend.sh`.

## Skills

python-*, api-requests, forms, interface-design, frontend-design, component-testing,
integration-testing, e2e-testing.
