VEREDICTO: APROVADO

Nenhum plano, spec, PRD ou histórico foi enviado no despacho — só objetivo, critérios tipados e ponteiro. Não abri nada em `product/items/019-.../`.

## Portões

| portão | resultado |
|---|---|
| pytest (suíte inteira) | **OK** — `659 passed, 2 warnings in 53.93s`, `EXIT=0`. Coleta real (659 > 0), não é o falso-sucesso do código 5 |
| ruff check + ruff format | **OK** — `All checks passed!` / `165 files already formatted`, `EXIT=0` |
| gates | **OK** — `✓ gates: limpos (árvore completa, 577 arquivo(s) considerados).`, `EXIT=0`. **577 > 0**, lido cru do arquivo com `od -c` |
| mypy `--strict` | **N/A por norma do projeto, não por omissão** — não existe `src/` e o portão de lint é só ruff; a norma 35 registra `mypy --strict` como item de roadmap. Não inventei um portão que o CI não roda |

Árvore limpa antes e depois de tudo.

## Critérios de aceite

Prova montada em bancada minha (`TestClient` + base própria em diretório temporário), não pela suíte do avaliado. Leitura de banco sempre por **segunda conexão** ao mesmo arquivo.

| # | critério | evidência |
|---|---|---|
| 1 | `estrutural` rota, importes, sem SQL de alcance, fragmento sem estilo | cumprido | A rota existe com o caminho derivado da constante da tela; os importes de alcance e de correção estão lá. Os SQL novos do router só leem alvo e vocabulário — nenhuma contagem ou soma nova. O fragmento existe e não traz `style=`, `<style` nem literal de cor; o diff não toca arquivo de estilo |
| 2 | `comportamental` abrir a correção sem mover total | cumprido | Resposta `200` com o bloco de correção, os quatro campos, o beneficiário — e **sem** campo de categoria. Alcance por beneficiário `−R$ 150,00 em 2 lançamentos, em toda a base`; por categoria de origem `−R$ 175,00 em 3 lançamentos`. Sem alvo, o bloco não aparece. O total do período segue `−R$ 175,00` nas três leituras |
| 3 | `comportamental` gravar e repartir | cumprido | `200`; resultado `2 lançamentos recolocados em Pessoal.`; uma regra por descrição; duas transações sob ela; a linha do grupo com `−R$ 150,00` e o total do período inalterado |
| 4 | `comportamental` a regra de precedência maior é nomeada | cumprido | `200`; resultado `0 dos 2 lançamentos previstos foram movidos: a regra ^mercado ainda segura mercado livre.` com link para a tela de regras. Duas regras, e zero transações no grupo pedido |
| 5 | `comportamental` grupo novo por bytes UTF-8 crus | cumprido | Corpo percent-encoded em UTF-8 → `200`; o grupo `Educação do filho` existe uma vez, com a natureza pedida, e aparece na lista de grupos |
| 6 | `comportamental` duas recusas e o controle positivo | cumprido | Grupo inexistente e alvo inexistente → **400** com a mensagem nomeada; depois das duas, zero regras por descrição (2ª conexão); a terceira chamada, válida, leva a contagem a 1 |
| 7 | `comando` subconjunto + tipos de teste + portões intocados | cumprido | `64 passed`, `EXIT=0`. O arquivo traz os quatro tipos: abre, grava, recusa e bytes crus. O diff não toca `scripts/` |

## Critérios de integração

| # | critério | evidência |
|---|---|---|
| I1 | prévia e resultado saem da mesma medida | cumprido | Nas duas execuções a prévia diz `2 lançamentos` e `−R$ 150,00` — a prévia não olha regra. Sem regra concorrente: `2 lançamentos recolocados`; com ela: `0 dos 2 ... ainda segura` |
| I2 | irmão de prefixo fica onde estava | cumprido | `mercado livre` → `['Pessoal', 'Pessoal']`; `mercado livre pago` → `['Outros']`. A expressão gravada é ancorada nos dois lados |
| I3 | a tela de regras edita o mesmo conjunto | cumprido | A linha da regra aparece lá com o grupo, a natureza, a essencialidade, a contagem e o valor alcançados |
| I4 | `comando` suíte inteira | cumprido | `659 passed`, `EXIT=0` |

## Caça ao número que vaza — não vaza

Achei o contador: um campo do resultado é o retorno da reclassificação, ou seja **toda linha cuja classificação mudou**, inclusive transferência e estorno. O outro vem do alcance, que filtra por gasto.

Montei a base que separa os dois: mesmo beneficiário com quatro linhas — duas de gasto, uma transferência e um estorno.

- prévia: `−R$ 150,00 em 2 lançamentos`
- linhas de fato sob a regra depois de gravar: **4**
- tela: `2 lançamentos recolocados em Pessoal.`

A tela imprime **2**, não 4. O contexto do resultado usa o alcance, e o campo da reclassificação não tem caminho até o HTML. A promessa "o número depois de gravar é o da prévia ou zero, nunca um terceiro" se sustenta nos três casos que testei.

## Outras provas que fiz por conta

- **Guarda de sessão na rota nova:** cliente anônimo → **302** para o login, e zero regras depois. O guarda é middleware global, então a rota nasce coberta.
- **Recusa não deixa resíduo invisível:** grupo novo com natureza inválida → **400**; pela **segunda conexão**, o grupo fantasma não existe e nenhuma regra foi escrita. O desfazimento cobre o grupo criado antes de a validação falhar.
- **Tentativas de quebra — todas recusadas com mensagem nomeada e zero resíduo** (12 grupos antes, 12 depois): grupo repetido, natureza inválida, essencialidade inválida, corpo vazio, grupo não numérico, corpo JSON em vez de formulário, alvo não numérico. Nenhum 500.
- **Beneficiário forjado no corpo é ignorado:** o alvo vem da query string, e o beneficiário irmão continuou onde estava.
- **Erro e resultado nunca convivem** na mesma resposta, nos dois sentidos.

## Achados que não reprovam

1. **400 mudo.** A rota **sem** o parâmetro de alvo responde `400` com o corpo sem mensagem nenhuma: o contexto da correção vira nulo quando não há alvo, o aviso montado é descartado, e o template pula o bloco inteiro. Não é alcançável pelo formulário, mas é uma recusa que o leitor não vê.
2. **A branch está sete commits atrás de `develop`**, e entre eles vem o item que trocou o guarda de rota por leitura de árvore sintática — o mesmo guarda que a rota nova precisa satisfazer. Os `659 passed` foram medidos sem esses commits.
3. **Risco vivo para quem editar depois:** os dois contadores ficam lado a lado no mesmo objeto, com nomes parecidos e semânticas diferentes. Hoje o router acerta; uma troca de campo quebra a promessa da tela sem quebrar nenhum teste de tipo.

## Instrumentos do implementer

Só o critério 7 e o de integração I4, que por construção nomeiam a suíte do avaliado. Todos os demais foram provados em bancada montada por mim, independente das asserções do implementer.
