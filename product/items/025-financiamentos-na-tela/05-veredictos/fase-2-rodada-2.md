VEREDICTO: APROVADO

Recebi apenas o objetivo da fase e o arquivo de critérios. Nenhum plano, brief, spec ou histórico veio junto, e não abri `product/items/025-financiamentos-na-tela/`.

## Portões

| Portão | Resultado |
|---|---|
| ruff | **OK** — `All checks passed!`, exit `0` |
| format | **OK** — `159 files already formatted`, exit `0` |
| mypy | **NÃO EXISTE NESTA STACK** — não há diretório `src`, `mypy` não está no `.venv`. Registro como medida ausente, não como aprovada |
| pytest | **OK** — `629 passed, 2 warnings in 50.18s`, exit `0` (629 coletados, não é o exit 5 de suíte vazia) |
| gates | **OK** — `✓ gates: limpos (árvore completa, 538 arquivo(s) considerados)`, exit `0`. **538 > 0**, mediu de verdade |

Árvore limpa; o que medi é o commit `62eb7d8`, não trabalho solto.

## Critérios de aceite

| # | Tipo | Critério | Veredicto | Evidência |
|---|---|---|---|---|
| 1 | estrutural | fragmento, include único, vizinho `beneficiarios`, router no `main.py`, CSS intocado | **cumprido** | Fragmento linha 1 abre `<section id="financiamentos">`. `configuracao.html:86` tem o include, contagem = 1; a linha seguinte abre `beneficiarios`. `main.py:70` registra o router. `git diff --name-only main -- app/static/css` devolve 0 linhas |
| 2 | estrutural | `financings.py` define `router`, registra o POST, importa `answer, text`, sem `TemplateResponse`/`def _context`/`conn.execute` | **cumprido** | `router = APIRouter()` (l.14); enumeração das rotas devolve `['POST'] /configuracao/financiamento`; `from app.routers.settings import answer, text` (l.11); as três cadeias proibidas com contagem `0` |
| 3 | comportamental RF-05 | dois formulários preenchidos | **cumprido** | mortgage `saldo="238.585,18"`, `taxa="0,72"`, `prazo="370"`; vehicle `taxa="1,63"`, `parcela="1.235,33"`, `prazo="60"`, `vencimento="2025-06-11"` |
| 4 | comportamental RF-07 | saldo calculado, sem campo | **cumprido** | `<p class="figure cifra">−R$ 39.176,36</p>`; campos do recorte = `tipo, taxa, parcela, prazo, vencimento` |
| 5 | comportamental RF-04 | tabela vazia, as duas telas em 200 | **cumprido** | `/configuracao` 200 com campos vazios; `/dividas` 200 sem contrato; tabela segue com 0 linhas |
| 6 | comportamental RF-05, RF-06 | gravar responde e a escada já está reconstruída | **cumprido** | POST 200 com `Salvo.`; **antes de qualquer outra requisição**: `financings` = `(500, 300, -20000000)` e `debts` = `(500, -20000000)` |
| 7 | comportamental RF-06 | escada reordena entre as duas leituras | **cumprido** (ver achado 1) | Com a escada construída uma vez: primeira leitura `[('2','163'),('1','72')]`, segunda `[('2','500'),('1','163')]` |
| 8 | comportamental RF-08 | recusa com a tela inteira de pé | **cumprido** | 400 com a mensagem da gramática; `financiamentos` e `beneficiarios` presentes; banco intacto |
| 9 | comportamental RF-08 | três recusas do veículo, nenhuma 500 | **cumprido** | 400/400/400 com as três mensagens em pt-BR; depois das três, `(163, '2025-06-11')` |
| 10 | comando | os dois arquivos de teste saem `0` | **cumprido** | Exit `0`, `18 passed in 4.26s`, com as seis funções nomeadas presentes |

### Critérios de integração (fase 1 + fase 2 juntas)

| # | Critério | Veredicto | Evidência |
|---|---|---|---|
| I1 | importa dos JSON, corrige o imóvel pela tela, nada mais se move | **cumprido** | Com os arquivos de contrato **reais**: escada 1 = `[(163, -3917636), (72, -23858518)]`; POST `saldo=100.000,00`; escada 2 traz `(72, -10000000)`. Só `mortgage.balance_cents` mudou; `overdraft` e `vehicle` idênticos em todos os campos |
| I2 | máquina sem contrato sobe, e digitar chega no mesmo número que importar | **cumprido** | Pasta vazia: `/configuracao` 200 com os dois formulários em branco. Degrau **importado**: veículo `(-3917636, 163, 45, -123533)`, imóvel `(-23858518, 72, 370, None)`. Degrau **digitado**: idênticos nos quatro campos, nos dois contratos, com `today = 2026-09-05` |

## Minha tentativa de quebrar a tela

Trinta e dois corpos malformados, com o banco conferido depois de cada um. **Nenhuma exceção, nenhum 500, nada gravado, tela sempre de pé.**

Dinheiro em forma estrangeira; número gigante e científico; saldo negativo, zero, vazio e com aspa simples; taxa fora da faixa, `nan`, `inf`, e `0,001` que arredondaria a zero; prazo zero, negativo, fracionário e por extenso; data fora do calendário, em formato brasileiro, vazia, por extenso e com hora; tipo desconhecido, acentuado, em maiúsculas e vazio; **corpo sem campo nenhum**; **corpo JSON** (400 com a tela, nunca 422 cru nem 500); bytes UTF-8 crus.

- **Forçar o saldo do veículo**: `tipo=vehicle` + `saldo=999.999,99` → 200, e `balance_cents` continuou `None`. **O saldo não grudou.**
- **O saldo encolhe sozinho**: `2025-06-10` → `−R$ 47.060,81`; `2026-09-05` → `−R$ 39.176,36`; `2026-10-05` → `−R$ 38.579,60`; `2030-05-11` em diante → `—`, sem sinal invertido.
- **A tela não mente**: depois da recusa, o campo volta com o guardado, e o valor digitado não aparece como valor de campo.
- **Ida e volta**: o que a tela imprime, devolvido verbatim ao formulário, deixa as linhas byte a byte iguais.
- **Guarda de sessão**: enumerei as 36 rotas do `openapi` e disparei cada uma sem cookie. Todas devolveram `302 → /login` ou `401`; só `GET /login` respondeu 200.
- **As telas que já existiam**: as 13 rotas GET responderam 200 antes e depois de uma gravação. Recusa numa seção não apaga as outras, nos dois sentidos.

## Achados que não reprovam

1. **O *Dado* do critério 7 está incompleto.** Ele manda ler `/dividas` sobre uma base que só tem `financings` — `debts` está vazia e a tela nem renderiza a escada. Completei com o único passo que o torna não-vazio, `rebuild(conn, today=date(2026,9,5))`, e o *Então* bateu exato, sem afrouxar nada.
2. **O identificador do degrau troca de dono quando um financiamento é gravado.** `INSERT OR REPLACE` move a linha para o fim, e `rebuild` recicla os ids. Medido: antes `(1, mortgage)` e `(2, vehicle)`; depois, `(1, vehicle)` e `(2, mortgage)`. Uma aba de `/dividas` aberta antes carrega ids velhos, e um `POST /dividas/taxa` dali cai na dívida errada.
3. **Recusa apaga o que o dono digitou.** É o que o critério pede, mas custa retrabalho num formulário de quatro campos.
4. **Duas gramáticas numéricas no mesmo formulário.** A taxa aceita ponto decimal e o dinheiro recusa. Decisão antiga, intocada; este formulário é o primeiro lugar onde as duas ficam lado a lado.
5. **Imóvel quitado não se registra pela tela**: saldo zero é recusado. Só importa no dia da quitação — previsto para `2026-10-01` no próprio contrato.

## Instrumentos do implementer

**Nenhum.** Provei os dez critérios da fase e os dois de integração com harness próprio, lendo o HTML e o SQLite por conta. `tests/test_configuracao_financiamentos.py` só foi executado porque **ele é o objeto** do critério 10.
