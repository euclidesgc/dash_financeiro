Você está em **dash_financeiro — painel financeiro pessoal de um usuário, rodando
local. Python 3.12 · FastAPI · Jinja2 · HTMX · SQLite. O objetivo do produto é
sair de um déficit mensal.** Sessão nova, sem histórico. Este texto é a sua única
entrada. Leia-o inteiro antes de agir.

## O estado — reescrito em 07/09/2026

**Os nove itens de produto do roadmap estão concluídos**, mais a dívida técnica
do lint. Todos passaram por validador cego, todos integrados em `develop` com
`--no-ff`.

| | |
|---|---|
| `001` a `009` | **concluídos**. Login, gastos nos três eixos, comprometido, resumo com projeção de 45 dias, escada de dívida com simulador, sincronização com idade cobrada, objetivo com três cenários, simulador de decisão em dias, e consultor de IA. |
| `010-lint-e-formatador-python` | **concluído**. `ruff` está no ambiente travado, configurado estreito, e roda por `scripts/lint.sh` e no CI. |
| `011-serie-duplicada-e-tolerancia-do-vencimento` | **concluído**. Quatro defeitos do motor de compromissos; o total caiu de −R$ 12.802,64 para −R$ 8.026,79. |
| `012-sync-pos-carga-atomica` | **concluído**. A pós-carga não deixa mais `sync_runs` afirmando sucesso com as tabelas derivadas paradas. |
| `013-objetivo-cenario-vazio-e-ponto-espurio` | **concluído**. A tela nomeia a lista vazia, e data recusada não grava ponto. |
| `014-taxa-sugerida-pelos-juros-cobrados` | **concluído**. O painel sugere a taxa do cheque especial a partir dos juros que o banco já cobrou: `itau` **6,71%** (faixa 4,58–9,84, 7 meses) e `CAIXA` **8,00%** (7,99–8,16, 3 meses). Cartão não recebe sugestão. |

**433 testes, lint limpo, gates limpos, 342 arquivos considerados. O roadmap está vazio.**

## O produto, em uma tela por vez

- `/` **Resumo** — três posições (consolidada −R$ 27.449,71, caixa −R$ 10.705,09,
  cartão −R$ 16.744,62), o mês típico por mediana, e a projeção de 45 dias com o
  **pior ponto nomeado**: −R$ 40.722,95 em 13/10/2026. A lista de dias prova o
  número do cabeçalho, linha a linha.
- `/gastos` — cinco eixos, período livre, drill-down, os dois cruzamentos.
- `/regras` — a classificação como tabela editável.
- `/comprometido` — assinaturas, parcelamentos vivos, caixa liberado e o
  calendário de 45 dias.
- `/dividas` — a escada por taxa mensal. **Dívida sem taxa não entra**, e a tela
  diz quantas ficaram de fora.
- `/objetivo` — reserva alvo R$ 41.879,58, três cenários e a linha do tempo.
  Hoje **nenhum cenário chega**, e a tela diz que faltam R$ 4.523,21 por mês para
  que exista uma data.
- `/simulador` — a decisão em dias, no mesmo motor do objetivo, mais a base de
  fatos com validade.
- `/consultor` — uma pergunta por vez, e a tabela do contexto exato que vai para
  o modelo.

## O que espera o dono

`state.py check` está com **`esperando_humano` vazio**: `D-001` foi ratificada
pelo dono em 07/09/2026, e a fase 4 do `001` saiu de `blocked-on-D-001`.

1. **Confirmar as taxas em `/dividas`.** Os dois cheques especiais chegam com
   sugestão medida — `itau` 6,71%, `CAIXA` 8,00% —, e basta salvar para elas
   entrarem na escada. **A taxa dos quatro cartões o painel não consegue
   derivar**: o saldo de um cartão é fatura, e fatura paga inteira não cobra juro
   nenhum. Enquanto não vierem da fatura, R$ 16.744,62 ficam fora da escada e o
   marco de dívidas do objetivo é calculado sem eles.
2. **Marcar as assinaturas que não usa mais** e **revisar as 77 categorias** nas
   telas de Comprometido e Regras. Os dois cenários do objetivo que dependem
   disso rendem hoje exatamente zero.
3. **Informar o saldo de quitação do CDC** em `/simulador`, para fechar a conta
   do carro.

## Validações de campo pendentes

- **`006`** — a chamada real à API da Pluggy exige credencial válida e item não
  expirado; o MFA é interativo.
- **`009`** — a qualidade da resposta do Gemini exige chave válida. Conferir que
  **todo número citado aparece na tabela "O que ela lê"**, dígito a dígito.

## O processo

Plugin **generic-harness** com o pack `python`. Leia o estado antes de tudo:

```bash
python3 "$CLAUDE_PLUGIN_ROOT/scripts/state/state.py" read
node scripts/loop/decide-next-action.mjs
```

**A régua que o dono deu em 07/09/2026:** *opção técnica com uma alternativa
claramente certa e justificada é execução, não pergunta.* Divergência `normal`
cuja recomendação você mesmo assina não se escala — decide, registra, e segue. O
que ele quer garantido: o sistema **atende o requisito, alcança o objetivo e é
seguro**. Quando os três apontam para a mesma opção, ela se faz.

**A régua desta corrida, aprendida cara:** *uma validação cega por fase*. Achado
que o próprio validador marca como "não reprova" vira correção com teste que
falha sem ela, nomeada na entrega — não uma rodada nova. Quatro rodadas na mesma
fase do `004` custaram quarenta minutos e acharam defeitos cada vez menores.

**E o plano vem antes do código.** Nos itens `007` e `008` isso foi invertido pela
pressa, e está registrado nas decisões autônomas dos dois como desvio.

**Nunca troque de branch enquanto um validador estiver rodando.** Aconteceu no
`012`: o `git diff` do despacho passou a devolver vazio e a árvore esteve em
outra branch enquanto ele media. Ele contornou exportando o ref e conferindo por
hash, mas um validador menos cuidadoso teria medido a árvore errada.

## Armadilhas medidas nesta máquina

1. **O hook de permissão nega qualquer comando que leia `.env`.** Todo comando
   precisa de `DASH_ENV_FILE=/dev/null` mais as variáveis na própria linha.
   Bancos e chaves sempre em `/tmp`.
2. **`rtk` reescreve a saída por hook global.** Para saída bruta,
   `rtk proxy <comando>`. No zsh, `grep --include=*.html` precisa de aspas.
3. **`grep -R` recursa em `__pycache__`** e casa bytes de `.pyc`. Use
   `--exclude-dir=__pycache__`.
4. **Medir exit code com `| tail` lê o exit do `tail`.** Capture em arquivo.
5. **O rate-limit fecha a porta:** um login por servidor, cookie reusado.
6. **`app.query` é somente-leitura.** Para montar estado, escreva no SQLite.
7. **Servidor:** `setsid ... &`, espere `/login` responder `200`, mate ao fim — e
   confira que não sobrou órfão segurando a porta 8000.
8. **Chromium** em `~/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome`,
   via `node` com o Playwright do cache do npx.
9. **O script de captura derivado por `sed` já escreveu no diretório errado
   quatro vezes.** Confira o `const OUT` antes de rodar.
10. **`gates_runner.sh` enumera por `git ls-files`.** Numa árvore sem `.git` ele
    imprime `0 arquivo(s) considerados` e sai com `EXIT=0` — passe falso.
    Confira o número.

## Entrega — este repositório NÃO tem remote

Uma fase é a unidade, mas **não vira PR**: trabalhe em `<nnn-slug>/fase-<n>-<slug>`
e integre em `develop` com `--no-ff`, depois do veredicto APROVADO e dos portões
verdes. O corpo do PR vira `product/items/<id>/05-entregas/fase-<n>.md`.
**Nunca `main`.** Segredo nunca no repositório.

## Antes de encerrar

`state.py check`, `bash scripts/lint.sh`, `bash scripts/gates/gates_runner.sh`,
árvore limpa. As seis propostas ao harness estão em `.harness/proposals/` — leia
antes de escrever a sétima.
