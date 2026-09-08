# dash_financeiro — painel financeiro pessoal de um usuário, rodando local. Login, dashboard das movimentações bancárias (sincronizadas da Pluggy todo dia ou sob demanda) e IA que ajuda a alcançar o plano de curto, médio e longo prazo. Stack Python 3.12 + FastAPI + Jinja2 + HTMX + SQLite. O objetivo do produto é sair de um déficit de R$ 4.940,72/mês.

Frentes: api em `.` (python).

## Processo

`/harness:start` conduz; `/harness:status` resume.

1. Sem plano aprovado (`03-plan.md`), o guard recusa escrita em código.
2. Cada agent escreve só no escopo declarado.
3. Mudança de API começa no OpenAPI.
4. Divergência de contrato para a fase. A normal segue na recomendação e se
   registra; trava merge só se a escolha for do dono.
5. Critério de aceite é tipado (`comando`, `estrutural`, `comportamental`).
   Adjetivo não é critério.
6. A DoD global é do CI e não se repete no plano.
7. Documento canônico não tem cicatriz: reescreve-se no presente.
8. Reconciliação de doc no mesmo PR da mudança.
9. Uma fase é um PR. Pilha é `gh stack`, nunca `--base` à mão.
10. "Pronto" é build verde com testes passando.

## Código

11. Zero comentário, exceto o porquê que o código não mostra: decisão,
    contorno externo, restrição de plataforma, invariante.
12. Sem TODO. Pendência vira item de roadmap, na posição de precedência
    certa, antes de a fase fechar.
13. Autorização é do servidor; no cliente é experiência de uso.
14. Segredo nunca no repositório.
15. Sem dependência não declarada.
16. Código e commits em inglês; documentos e interface em pt-BR.

## Invariantes do produto

22. **Valor em centavos inteiros**; negativo = dinheiro saindo, em qualquer tipo
    de conta. A Pluggy inverte o sinal em cartão: normaliza-se na ingestão, uma
    vez.
23. **Cálculo financeiro é código determinístico, nunca IA.** O modelo interpreta
    e explica; quem calcula é função testada.
24. **Login antes de qualquer rota que devolva dado.** Sem exceção, nem `/health`.
25. Transferência entre contas próprias e estorno **não** entram no total de
    gasto. Sem isso o painel mente em R$ 20.272,00.
26. O que só o humano sabe (saldo de quitação, custo de transporte, taxa de
    cartão) é **parâmetro editável na tela**, nunca constante no código.
27. Antes de escrever qualquer tela, carregue a skill **`frontend-design`**.
28. Os números de referência estão congelados em `docs/plano.md`, medidos em
    05/09/2026. Critério que se compara com relatório regerável passa por
    construção.

## Ferramentas

17. Grafo antes de busca crua: `semantic_search_nodes_tool`, `query_graph_tool`.
18. Saída de comando se estreita na origem, não por camada que resume.
19. Antes de dar por pronto: `bash scripts/lint.sh` e
    `bash scripts/gates/gates_runner.sh`. Portão que não conseguiu medir
    reprova, nunca aprova.
20. Erro repetido pela segunda vez vira causa raiz, não terceiro remendo.
21. `/harness:doctor` diagnostica ambiente, hooks e estado.

Detalhe nas skills do harness.

## Python · FastAPI (`.`)

29. Domínio é pasta (`plan`, `payees`, `sync`); o router dele fica em
    `app/routers/`, um por domínio — a forma por tipo do pack, que vale porque
    o serviço é pequeno e de dono único.
30. Router traduz HTTP; não monta consulta nem dá commit (G7).
31. I/O aguardável em `async def`; bloqueante em `def`; nunca bloqueante dentro
    de `async def`.
32. Dependência valida, não só injeta; forma `Annotated[T, Depends(...)]`.
33. Junção e agregação em SQL, em `app/queries`; Pydantic só valida a resposta.
34. Esquema muda por arquivo em `app/migrations`, aplicado por `app/migrate.py`.
    Não há Alembic, e SQLite é o banco em todo ambiente.
35. `scripts/lint.sh` é `ruff check`, `ruff format --check` e `mypy --strict`
    nos três pacotes. O fluxo de integração contínua cobra o mesmo comando.

Detalhe nas skills `python-*`; as de SQLAlchemy, Alembic e `BaseSettings`
descrevem ferramenta que este projeto não usa.

<!-- harness:claude-md -->
