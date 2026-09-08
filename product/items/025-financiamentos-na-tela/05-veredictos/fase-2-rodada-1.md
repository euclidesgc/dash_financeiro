VEREDICTO: CRITERIO_INVALIDO — nenhum portão falhou, nenhum critério verificável falhou, mas o segundo critério estrutural exige uma linha de import de símbolos que não existem e nunca existiram nesta base; satisfazê-lo ao pé da letra derruba a aplicação no boot.

Nada de plano, spec, brief ou histórico chegou até mim: o arquivo de despacho trazia só o objetivo e os dois blocos de critérios, e não abri `product/items/025-financiamentos-na-tela/`.

## Portões

| Portão | Resultado | Saída |
|---|---|---|
| ruff check | OK | `All checks passed!` |
| ruff format --check | OK | `159 files already formatted` |
| pytest (suíte inteira) | OK | `629 passed, 2 warnings in 49.26s`, exit 0 — 629 coletados, não é o exit-5 de suíte vazia |
| gates_runner | OK | `✓ gates: limpos (árvore completa, 538 arquivo(s) considerados).` — 538 > 0, mediu de verdade |
| mypy --strict src | **NÃO APLICÁVEL, declarado** | não existe diretório `src` nesta árvore e não há configuração de mypy no `pyproject.toml`. A norma 35 diz que `mypy --strict` ainda não roda. Registro como não medido, nunca como aprovado. |

## Critérios da fase

| # | Tipo | Critério | Resultado | Evidência |
|---|---|---|---|---|
| 1 | estrutural | fragmento + include único + vizinha certa + include_router + CSS intocado | **cumprido** | `configuracao_financiamentos.html:1` abre `<section id="financiamentos">`; `grep -c` do include = **1**, linha 86; a linha 87 é `<section id="beneficiarios">`; `app/main.py:70` registra o router; `git diff --name-only main -- app/static/css` devolve **0 linhas** |
| 2 | estrutural | router existe, define `router`, registra o POST, importa `_answer, _text`, e não contém `TemplateResponse` / `def _context` / `conn.execute` | **CRITÉRIO INVÁLIDO** | ver bloco abaixo |
| 3 | comportamental RF-05 | dois formulários lidos da tabela | **cumprido** | `GET /configuracao` 200; recorte da seção com exatamente 1 `</section>`. mortgage: `saldo=238.585,18`, `taxa=0,72`, `prazo=370`; vehicle: `taxa=1,63`, `parcela=1.235,33`, `prazo=60`, `vencimento=2025-06-11` |
| 4 | comportamental RF-07 | saldo do veículo calculado, sem campo | **cumprido** | o recorte do veículo traz `<p class="figure cifra">−R$ 39.176,36</p>`; os `<input` do recorte são `tipo, taxa, parcela, prazo, vencimento` — **nenhum** `name="saldo"` |
| 5 | comportamental RF-04 | tabela vazia, as duas telas de pé | **cumprido** | `financings` com 0 linhas; `/configuracao` 200 com campos vazios; `/dividas` 200, sem `data-financiamento` e sem `CDC do veículo` |
| 6 | comportamental RF-05/06 | gravar reconstrói na mesma requisição | **cumprido** | `POST` 200 + `Salvo.`; **antes de qualquer outra requisição**: `financings` = `(500, 300, -20000000)` e `debts` = `(500, -20000000)` |
| 7 | comportamental RF-06 | escada reordena e a tela seguinte mostra | **cumprido** | 1ª leitura de `/dividas`: `['163','72']`; após o POST: `['500','163']` |
| 8 | comportamental RF-08 | `saldo=abc` recusado com a tela inteira de pé | **cumprido** | 400; `id="recusa"` com a mensagem da gramática; `id="financiamentos"` e `id="beneficiarios"` presentes; banco segue `-23858518` |
| 9 | comportamental RF-08 | três recusas do veículo, nenhuma 500 | **cumprido** | 400/400/400 — data fora da forma ISO, taxa zero, tipo desconhecido; depois das três, `(163, '2025-06-11')` intacto |
| 10 | comando | os dois arquivos de teste saem 0, e o novo cobre os seis cenários | **cumprido** | `18 passed`, `EXIT=0`, com as seis funções nomeadas presentes |

### Critérios de integração

| # | Critério | Resultado | Evidência |
|---|---|---|---|
| I-1 | importa, corrige pela tela, relê a escada; só o degrau do imóvel se move | **cumprido** | 14 migrações em sequência; importados `mortgage(72, 370, -23858518)` e `vehicle(163, 60, -123533, 2025-06-11)`. Leitura 1 e leitura 2 com o degrau do veículo **byte a byte idêntico**, e só o do imóvel mudando para `-15000000` |
| I-2 | máquina sem contrato sobe; digitar chega ao mesmo número que importar | **cumprido** | Pasta vazia: `/configuracao` 200, campos em branco, tabela com 0 linhas. Depois da gravação pela tela e `rebuild(today=2026-09-05)`: degrau digitado `(-3917636, 163, 45, -123533)` **==** degrau importado `(-3917636, 163, 45, -123533)` |

## O critério 2, em detalhe

Tudo passa **menos uma cláusula**:

- `router = APIRouter()` em `app/routers/financings.py:14` — OK
- `POST /configuracao/financiamento` registrada e respondendo (provado por HTTP em seis cenários) — OK
- `TemplateResponse`, `def _context`, `conn.execute`: **nenhuma ocorrência** no arquivo — OK (norma 30 respeitada)
- `contém a linha de import from app.routers.settings import _answer, _text` — **impossível**

O arquivo tem `from app.routers.settings import answer, text` (linha 11). Os nomes `_answer`/`_text` **não existem em `app/routers/settings.py`**, e não existiam antes desta fase: em `develop` o módulo já define `def text` e `def answer`, públicos. Prova executada:

```
$ .venv/bin/python -c "from app.routers.settings import _answer, _text"
ImportError: cannot import name '_answer' from 'app.routers.settings'. Did you mean: 'answer'?
```

Qualquer implementação que satisfaça a cláusula ao pé da letra não sobe. Por isso a marco como inválida, e não como reprovação: a intenção declarada no próprio critério ("a tela tem um renderizador só, e o router não monta consulta") está verificada. `_answer`/`_text` existem sim, mas em `app/routers/summary.py` e `app/routers/rules.py` — provavelmente a origem do engano ao escrever o critério.

**Duas saídas, com o custo de cada uma.** Corrigir o texto do critério para `answer, text` custa uma linha e não toca código — é a minha recomendação. Renomear `answer`/`text` para `_answer`/`_text` custa mexer em módulo que já estava em `develop`, atualiza os chamadores e institui import de nome privado entre módulos, que é pior desenho do que o que está lá.

## Minha própria tentativa de quebrar a tela

36 corpos enviados contra `POST /configuracao/financiamento`, com banco temporário e leitura do banco **depois de cada um**. **Zero respostas 500.** Todas as recusas vieram 400, com `id="recusa"`, mensagem em pt-BR, a tela inteira de pé e banco intacto:

`5000.00` · `1,234.56` · `$1234.56` · 13 dígitos · 400 dígitos · saldo negativo · saldo zero · taxa `100,01` · taxa zero · taxa negativa · `nan` · `1e400` · `muito alta` · prazo `0` · prazo `60,5` · prazo `-12` · `dez` · prazo vazio · saldo vazio · taxa vazia · `2025-02-30` · `11/06/2025` · `ontem` · data vazia · `mil reais` · tipo `imovel` · tipo `veículo` · tipo vazio · **corpo sem campo nenhum** · `238.585,18ç` · byte nulo no meio do número · `<script>x</script>` (escapado) · **corpo JSON em vez de formulário** (400, não 422 nem 500).

Além dos critérios, os quatro contratos pedidos:

- **Nenhum número muda de valor ao mudar de lugar.** Provado para os **dois** contratos, com a data fixa. Veículo: tela `(-3917636, 163, 45, -123533)` == arquivo. Imóvel: tela `(-23858518, 72, 370, None)` == arquivo. A conversão de `8,9899% a.a.` do arquivo chega a **72 bp/mês**, o mesmo que digitar `0,72` — o arredondamento fecha.
- **O saldo do veículo continua calculado.** Só a data mudando: `2025-06-10` → 60 meses / `-4.706.081`; `2026-09-05` → 45 / `-3.917.636`; `2028-01-05` → 29 / `-2.836.734`; `2030-05-11` → 0 / `None`. E **postar `saldo=1,00` no corpo do veículo não congela nada**: `balance_cents` continua `NULL`.
- **A tela não mente depois de uma recusa.** Os campos voltam mostrando o **guardado**, não o digitado; `value="abc"` não aparece em lugar nenhum do HTML.
- **Guarda de sessão na rota nova.** Sem cookie, `POST /configuracao/financiamento` → **302 → `/login`**, e o banco não muda.
- **As telas que já existiam.** `/configuracao` segue com as seis seções, na ordem `fatos, metas, cartoes, financiamentos, beneficiarios, ia`, sem duplicata. Recusa cruzada nos dois sentidos preserva as seções vizinhas. Todas as oito rotas de tela em 200.

## Achados que não reprovam

1. **Dígitos não-ASCII passam pela gramática do dinheiro.** `saldo=١٢٣٤,٥٦` (arábico-índico) e `saldo=１２３４,５６` (largura cheia) são **aceitos e gravados** como `-123456`. A causa é `\d` do `re` casar todo dígito decimal Unicode. O número lido está certo, e o código é o `parse_money` de `app/settings/typed.py`, **pré-existente e não tocado por esta fase** — vale para todo campo de dinheiro do painel. O conserto é `re.ASCII` num lugar só.
2. **Taxa de exatamente 100% ao mês é aceita** para o imóvel. Está dentro do limite que a própria mensagem anuncia, e o teto também é de `develop`.
3. **Corpo JSON é aceito pelo endpoint** e cai na recusa de tipo em vez de 422. Sem 500 e sem escrita.
4. **Vão na numeração das migrações**: não existe `012_*.sql` nesta branch; a sequência é `001`–`011`, `013`–`015`. Pré-existente, aplica limpo.

## Instrumentos do implementer

Um critério e só um dependeu da suíte do avaliado: **o critério 10**, que por definição pede a saída de `pytest`. Todos os outros — os nove da fase e os dois de integração — foram provados por harness próprio, batendo HTTP na aplicação e lendo o SQLite direto.
