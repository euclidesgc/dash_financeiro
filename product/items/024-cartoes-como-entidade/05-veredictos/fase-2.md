VEREDICTO: APROVADO

Nenhum plano, brief, spec ou histórico foi enviado no despacho — o arquivo de critérios trazia só o objetivo e a lista tipada, e não abri `product/items/024-cartoes-como-entidade/`.

## Portões

| Portão | Resultado |
|---|---|
| `pytest` (árvore inteira) | **OK** — `584 passed, 2 warnings in 45.60s`, exit `0`. Coletou 584 testes (não é o exit 5 de "nada coletado") |
| `scripts/lint.sh` (`ruff check` + `ruff format --check`) | **OK** — `All checks passed!` / `148 files already formatted`, exit `0` |
| `scripts/gates/gates_runner.sh` | **OK** — `✓ gates: limpos (árvore completa, 517 arquivo(s) considerados).` — **517 > 0**, mediu de verdade |
| `mypy --strict` | **N/A por norma do projeto**, não pulado em silêncio: `.venv/bin/mypy` não existe e `mypy` não está declarado em `pyproject.toml`. A norma 35 do `CLAUDE.md` diz que `mypy --strict` ainda não roda e é item de roadmap; `scripts/lint.sh` é só ruff |

## Critérios da fase

| # | Tipo | Critério | Evidência |
|---|---|---|---|
| 1 | estrutural | router/catalog/main/include | `app/routers/cards.py:13` `router = APIRouter()`, `:16` `@router.post(ACTION)`; `app/cards/catalog.py:3` `ACTION = "/configuracao/cartao"`; `app/main.py:60` `app.include_router(cards.router)`; `app/templates/configuracao.html:86` o include, `grep -c` = **1**, entre o `</section>` de `metas` (linha 85, aberta em 76) e `<section id="beneficiarios"` (linha 87) | passou |
| 2 | comportamental | listagem + seção vazia | `GET /configuracao` → `200`; `id="cartoes"` ×1; `data-cartao="acc-cartao-1"` ×1, `acc-cartao-2` ×1, `acc-corrente` **×0**; 8 `data-campo` dentro da seção, todos `data-valor=""`; `fatos`/`metas`/`beneficiarios` ×1 cada. Base só com `BANK` → `200`, `id="cartoes"` presente com `class="empty"` e `Nenhum cartão na base.` | passou |
| 3 | comportamental | escrita dos quatro campos | 4 `POST` → `200` cada, `Salvo.` em todas; `SELECT limit_cents, monthly_rate_bp, closing_day, due_day` → **`(1200000, 1250, 3, 10)`**; 4ª resposta traz os quatro `data-campo=… data-valor=…` exatos, `R$ 12.000,00` e `12,50%` | passou |
| 4 | comportamental | recusa de gramática | `limite=5000.00` → `400`, `id="recusa"`, notice `Limite inválido: "5000.00". Escreva na forma 1.234,56, com no máximo 12 algarismos.`; `fechamento=32` → `400`, `Dia do fechamento inválido: "32". Use um dia do mês, de 1 a 31.`; as duas com `id="metas"` e `id="beneficiarios"`; banco → `(None, None)` | passou |
| 5 | comportamental | recusa de nome desconhecido | `acc-inexistente` → `400`, `Cartão não encontrado: "acc-inexistente".`; `campo=bandeira` → `400`, `Campo desconhecido: "bandeira".`; `SELECT COUNT(*) … limit_cents IS NOT NULL` → **`0`** | passou |
| 6 | comportamental | taxa nas duas telas | `POST` taxa `12,5` → `/dividas` traz `data-taxa="1250"` dentro de `id="escada"…</section>` (única ocorrência na fatia); `POST /dividas/taxa degrau=1 taxa=9` → `/configuracao` traz `data-campo="taxa" data-valor="900"`. Banco: `cards.monthly_rate_bp=900`, `debts.monthly_rate_bp=None` | passou |
| 7 | estrutural | fragmento sem estilo próprio | `<style` ×0, `style=` ×0, `#` ×0 no arquivo inteiro. 25 classes usadas, **todas** presentes como seletor em `app.css`/`tokens.css`; as 24 nominadas no critério estão todas usadas e todas casadas. `git diff develop...HEAD -- app/static/css/` **vazio** | passou |
| 8 | comando | os três arquivos de teste | exit `0`, `25 passed in 4.57s`. `tests/test_cartoes_screen.py` adicionado em `640a119` com 8 testes cobrindo listagem, seção vazia, quatro campos, duas recusas de gramática, duas de nome, ida e volta da taxa. `test_the_screen_lists_the_catalogue_in_two_blocks` vive em `test_configuracao_screen.py:59` e compara `set(data-config)` com `CATALOG`; `test_every_registered_route_requires_session` vive em `test_route_guard.py:37` | passou |
| 9 | estrutural | help do `taxa-cartao` | Frase antiga sumiu (`"e não uma linha aqui"` → `False`); nova nomeia as duas telas e o `mesmo lugar`. `len(CATALOG)` 5→5, mesmos nomes na mesma ordem, `CARD_RATE == 'taxa-cartao'`; único diff campo a campo: `('taxa-cartao', 'help')` | passou |

## Critérios de integração

| # | Tipo | Critério | Evidência |
|---|---|---|---|
| I1 | comportamental | costura fase 1 ↔ fase 2 | 12 migrações aplicadas em sequência, `DASH_MANUAL_DIR` inexistente. 1ª leitura: `without_rate` = **1** (`card/Cartão Azul`), `ladder` = **1** (`overdraft/Conta corrente`, 352). Após `POST /configuracao/cartao taxa=12,5`: `without_rate` = **0**, `ladder` = **2**, com o cartão **à frente** (`1250` > `352`) | passou |
| I2 | comportamental | pergunta do consultor | Antes: `pending = ['taxa-cartao', 'quitacao-cdc', 'transporte-sem-carro']`, `next_question = taxa-cartao` — a pergunta **existe**. Depois da escrita: `pending = ['quitacao-cdc', 'transporte-sem-carro']` — `taxa-cartao` some e **nada mais some** | passou |
| I3 | estrutural | `gaps.py` intocado | `git diff 2153d72^ HEAD -- app/advisor/gaps.py` **vazio** (byte-idêntico desde antes do item). Último commit a tocá-lo: `fbce551` (item 015). Símbolos públicos preservados: `wanted`, `pending`, `next_question`, `postponed`, `dismiss`, `UnknownQuestionError` | passou |

## Minha própria tentativa de quebrar a tela

**37 casos adversariais, todos `400`. Nenhum `500`, nenhuma exceção, nenhuma escrita.** Comparei o dump completo de `cards` antes e depois de cada um contra uma linha de base cheia (`999999, 725, 5, 15`) — voltou idêntica no fim.

- Dinheiro estrangeiro: `5000.00`, `1,234.56`, `$5,000.00`, `5 000.00`
- Número gigante: 21 dígitos, 400 dígitos (em limite, taxa e dia); `inf`, `nan`, `1e400`, negativo, `200%`
- Dia: `0`, `32`, `3,5`, `3.5`, `-3`, 400 dígitos
- Texto puro e acentuado nos três tipos: `abc`, `não é número`, `três vírgula cinco`, `terça`
- Campo inexistente: `bandeira`, `limíte`, `LIMITE`, `" limite "`, `""`, `limit_cents` (nome de coluna)
- Conta inexistente: `acc-inexistente`, `cartão-que-não-há`, `""`, injeção SQL com aspas e `--` (a tabela `cards` continuou de pé)
- Corpo malformado: sem campo nenhum, só `cartao`, só `campo`, só chaves inventadas

Em todos, `id="recusa"` presente e a tela **de pé** (`id="metas"`, `id="beneficiarios"`, `id="cartoes"` na resposta).

**A tela não mente sobre o que guarda.** Com `9.999,99` gravado, recusei `5000.00`: o banco continuou `999999`, o `data-valor` renderizou `999999`, o `value` do input renderizou `9.999,99`, a cifra mostrou `R$ 9.999,99` e a string recusada aparece **uma única vez** na página — no aviso, que é onde ela deve estar. O bloco do campo não ecoa o digitado.

**Guarda de sessão (norma 24).** Varri as **41 rotas registradas**: nenhuma sem guarda, exceto a porta do login. `POST /configuracao/cartao` anônimo → `302 → /login`, sem vazar `Cartão Azul` nem `data-cartao` no corpo, e sem tocar o banco.

**A tela não quebrou as que já existiam.** As quatro seções renderizam uma vez cada; o conjunto de `data-config` continua igual ao `CATALOG`. Fatos/Metas gravam por `POST /configuracao` e recusam com `400`+`id="recusa"` valor ruim, nome fora do catálogo e janela maior que a base. Beneficiários gravam por `POST /configuracao/beneficiario` (`Padaria do Zé` com acento intacto no banco e na tela), recusam beneficiário desconhecido e apagam com campo vazio; `POST /configuracao/cnpj` responde `200` com o aviso de consulta desligada.

**A taxa tem uma casa só.** Escrevi alternando os dois caminhos (`12,5` → `9` → `3,75` → `0,01`) e li pelos dois a cada passo: as duas telas mostraram o mesmo número em **todos** os estados. Um segundo cartão não contamina o primeiro; escrita recusada em qualquer dos caminhos não move o que o outro lê; e um `ladder.rebuild` (o que uma sincronização faz) preserva os valores. `debts.monthly_rate_bp` permanece `NULL` para todo degrau de cartão. O estado "sem taxa" também é coerente: `Ausente` e `data-valor=""` numa tela, degrau no bloco sem-taxa na outra.

## Achados que não reprovam

1. **Conta `BANK` vira cartão por escrita forjada.** `app/cards/store.py:53-66` — `write()` confia na FK para `accounts(id)`, que prova que a conta **existe**, não que ela é `CREDIT`. E `_READ` (`store.py:9-13`) junta `cards` a `accounts` **sem filtro de tipo**. Mandei `cartao=acc-corrente&campo=limite&valor=1.000,00`: respondeu `200 Salvo.`, criou a linha, e a conta corrente passou a aparecer como bloco de cartão em `/configuracao` com limite e taxa de 99%. `reconcile` é `INSERT OR IGNORE` e nunca apaga, então um `ladder.rebuild` não limpa. A escada **não** corrompe (o join de `_STEPS` é guardado por `d.kind = 'card'`). Só se alcança forjando o `cartao` escondido num POST autenticado, e nenhum critério cobre. Correção de uma linha: filtrar por `accounts.type = 'CREDIT'` em `write` e em `_READ`.

2. **A mesma tela diz duas coisas sobre onde a taxa se edita.** O `help` mudou como o critério 9 pediu ("se edita tanto aqui, na seção Cartões desta tela, quanto em /dividas"), mas três linhas abaixo, dentro do mesmo `<article>`, a prosa fixa de `app/templates/configuracao.html:44-46` continua: "Não é uma linha aqui... O campo está em /dividas". E a recusa de `app/settings/store.py:65-67` ainda responde `"Taxa mensal dos cartões" não é uma linha de valor: informe em /dividas.` Nenhuma das duas menciona a seção Cartões que agora está na mesma página.

3. **Valor vazio limpa o campo com `200 Salvo.`.** `app/cards/typed.py:26-27` devolve `None` para string em branco antes de qualquer leitor rodar, então `valor=""` grava NULL. Na metade Fatos/Metas da **mesma tela**, campo de dinheiro vazio é recusado. Dois comportamentos para campo vazio numa tela só — provavelmente é o único jeito de desfazer um limite, mas não está declarado em lugar nenhum.

4. **Numeração de migração pula o 012** (e `develop` pula o 014). Veio com a fase 1, não com esta; `run_migrations` aplica em ordem lexical e nada quebra.

## Instrumentos do implementer

**Nenhum.** Os treze critérios foram medidos por harness próprio, sobre bases em diretório temporário criadas do zero. A suíte do avaliado entrou apenas onde o próprio critério 8 a nomeia como o comando a executar — e mesmo lá, cada comportamento que ela afirma eu provei separadamente antes.
