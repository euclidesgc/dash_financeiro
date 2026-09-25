# PLAN 040 — vscode-single-run-config

Branch: `feature/040-vscode-single-run-config`

Item de configuração do editor, sem tela nem regra de produto: PRD e SPEC não
se aplicam, e as decisões ficam aqui.

## Causa de "não funciona"

O arranjo anterior era um `compounds` com `stopAll: true` juntando três
entradas: a API (debugpy), o front (`node-terminal` com `pnpm dev`) e
"Abrir o painel no navegador" (`node-terminal` que esperava o Vite, chamava
`xdg-open` e terminava com `exit`). No VS Code 1.138 instalado:

- o `node-terminal` do js-debug encerra a sessão quando o terminal fecha
  (`onDidCloseTerminal` resolve o processo como `killed`);
- com `stopAll`, a primeira sessão do compound que termina dispara o
  `sessionStopped` da raiz do compound, e o VS Code para todas as outras.

No GNOME, `xdg-open` vira `gio open`, que entrega o endereço ao navegador e
volta na hora. O `exit` fecha o terminal, a sessão de abertura termina e o
`stopAll` derruba a API e o Vite logo em seguida: a aba abre sobre um
servidor que acabou de sair. A suspeita do navegador morrer junto com o
terminal só vale quando ele ainda não estava aberto; a nova forma cobre os
dois casos.

## Decisões

- **D1 — Um script, uma entrada.** `scripts/dev.sh` prepara a base (os mesmos
  `app.migrate`, `app.auth.seed` e `app.ingest` da antiga tarefa "Preparar a
  base local"), sobe a API e o Vite, espera os dois responderem, abre o
  navegador e derruba os dois quando sai. `.vscode/launch.json` tem só
  "Executar", um `node-terminal` que roda `bash scripts/dev.sh`;
  `.vscode/tasks.json` sai porque nada mais o usa.
- **D2 — Navegador fora da sessão do terminal.** `setsid -f xdg-open`: o
  navegador não herda o desligamento do terminal nem entra na limpeza.
- **D3 — Cada servidor no próprio grupo de processos** (`set -m`), para a
  limpeza alcançar o Vite que o `pnpm` cria; entrada padrão em `/dev/null`,
  senão o Vite em segundo plano lê o terminal e para por `SIGTTIN`.
- **D4 — `--strictPort` no Vite.** Com a 5173 ocupada ele iria para a 5174 e o
  navegador abriria uma página que ninguém serve; o script também recusa
  começar se a 8000 ou a 5173 já respondem.
- **D5 — Sem depurador na API.** Manter o debugpy exigiria uma segunda entrada
  de anexar, e o item pede uma só.

## Fase 1 — "Executar" sobe tudo e abre o painel

- [x] T1.1 — Script e configuração
  - Arquivos: `scripts/dev.sh`, `.vscode/launch.json`, `.vscode/tasks.json`
  - O que fazer: D1 a D4.
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `.vscode/launch.json` interpretado como JSON tem uma única configuração, de nome "Executar", tipo `node-terminal`, comando `bash scripts/dev.sh`, e nenhum `compounds`; `.vscode/tasks.json` não existe. (estrutural)
- [x] CA1.2 — Com `xdg-open` trocado por um registrador via `PATH`, `bash scripts/dev.sh` deixa `http://127.0.0.1:8000/api/me` respondendo 401, `http://localhost:5173/app/` respondendo 200 e `http://localhost:5173/api/me` respondendo 401 (proxy), e chama `xdg-open http://localhost:5173/app/` numa sessão própria. (comportamental)
- [x] CA1.3 — Depois de `SIGTERM` no script, de `SIGHUP` pelo fechamento do seu terminal, ou da morte do processo da API, as portas 8000 e 5173 deixam de responder e não sobra processo `python -m app` nem Vite do projeto. (comportamental)
- [x] CA1.4 — Com o `xdg-open` real, o script o invoca com `http://localhost:5173/app/` e ele sai com código 0. (comando)

## DoD da entrega

- [x] DoD1 — Todas as tarefas e critérios do plano marcados
- [x] DoD2 — Suíte de testes inteira passa
- [x] DoD3 — Lint do projeto inteiro sem erros nem avisos
- [x] DoD4 — Tipos de todos os `tsconfig` sem erros
- [x] DoD5 — Console dos testes sem erro nem aviso
- [x] DoD6 — `build` passa
- [x] DoD7 — Nenhum import entre features nem contra o fluxo compartilhado → features → app
- [x] DoD8 — Nenhum `console.log`, `TODO`, `// @debug`, `.only(` ou `.skip(` no diff da branch
- [x] DoD9 — Nenhuma worktree ou branch temporária sobrando
