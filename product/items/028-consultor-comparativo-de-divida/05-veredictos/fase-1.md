VEREDICTO: APROVADO

Nenhum plano, brief ou spec foi enviado no despacho, e nada dentro de `product/items/028-.../` foi aberto. Julguei só o objetivo, os nove critérios e `git log develop..HEAD`.

## Portões

| Portão | Resultado |
|---|---|
| ruff check | **OK** — `All checks passed!` |
| ruff format --check | **OK** — `174 files already formatted`; `EXIT=0` |
| mypy --strict | **NÃO APLICÁVEL, e digo em vez de omitir** — não existe no ambiente nem no `pyproject.toml`. Não é portão que falhou em medir: é portão que este projeto declara não ter (norma 35). Zero arquivos medidos — se a intenção fosse cobrá-lo, isto seria REPROVADO. |
| pytest | **OK** — `677 passed, 2 warnings in 58.52s`, `EXIT=0` |
| gates | **OK** — `✓ gates: limpos (árvore completa, 577 arquivo(s) considerados)`, `EXIT=0`. Contagem maior que zero. |

## A conta refeita à mão

Refiz **antes** de abrir o código da função, e depois confirmei com aritmética **racional exata**, não com ponto flutuante.

**Caso 1 — (100000, 1000 bp, 2, 5000):** `i = 0,10`; `1,1² = 1,21`; `1/1,21 = 0,8264462809917355`; `1 − isso = 0,1735537190082645`. Parcela `= 10000 / 0,1735537190082645 = 57619,047619…` → **57619**. `57619 × 2 = 115238`; `− 100000 = 15238` de juros; `+ 5000` = **20238**.

**Caso 2 — (100000, 2000 bp, 2, 0):** `i = 0,20`; `1,2² = 1,44`; `1 − 1/1,44 = 0,305555…`. Parcela `= 20000 / 0,305555… = 65454,5454…` → **65455**. `65455 × 2 = 130910`; `− 100000 = 30910`.

**Caso 3 — (100000, 0, 2, 5000):** taxa zero, sem fator de anuidade, custo `=` **5000**.

**O critério está certo, e a implementação também.** Os três conferem no centavo.

Fui além do pedido, porque isto é o que decide dinheiro: varri **25.800 combinações** — taxas de 1 a 3000 pontos-base mais o teto, prazos de 1 a 420 meses, valores de mil reais a dez bilhões — comparando a implementação contra o oráculo racional exato. **Zero divergências.** A escolha de ponto flutuante não custa um centavo em nenhum caso alcançável.

## Critérios de aceite

| # | Critério | Veredicto | Evidência |
|---|---|---|---|
| 1 | `comando` — colunas da tabela | cumprido | Comando do critério rodado **verbatim**: `EXIT=0`. A taxa é anulável; prazo e valor liberado não são |
| 2 | `estrutural` — a função existe e não fala com IA | cumprido | Assinatura conferida por introspecção. Busca por cliente HTTP, chamada ao modelo e nome do provedor: saída vazia, exit 1. Único import é a escala da taxa |
| 3 | `comportamental` — os três valores | cumprido | `20238 30910 5000`, confirmados pelo oráculo exato acima |
| 4 | `comportamental` — gravar e mostrar | cumprido | Gravação e leitura em `200`; o recorte da proposta traz prazo, taxa, valor e contratação nas formas do painel, e a data de captura segue a data de referência do processo — sem ela, a mesma proposta gravou o dia real |
| 5 | `comportamental` — recusa com controle positivo | cumprido | Forma estrangeira → **400** com a recusa nomeada e a tela de pé; a mesma proposta na forma correta → `200`. O banco guarda só a segunda |
| 6 | `comportamental` — proposta sem taxa | cumprido | Gravada com taxa nula; o recorte traz `Ausente` e a frase que diz que ela não entra na comparação — **fica de fora e é dita, não some** |
| 7 | `comportamental` — remoção | cumprido | A proposta removida some do HTML e do banco; a vizinha continua nos dois |
| 8 | `estrutural` — fragmento e include | cumprido | O fragmento existe, é incluído **exatamente uma vez**, e não usa o atributo que a suíte da tela de configuração casa com o catálogo |
| 9 | `comando` — quatro arquivos de teste | cumprido | `23 passed`, `EXIT=0`, exercitando taxa positiva, taxa zero e contratação zero |

## As provas que levantei por conta própria

- **Gravar duas vezes edita, não duplica.** A mesma proposta regravada com outros números manteve a contagem em 1 e o mesmo identificador.
- **Guarda de sessão nas rotas novas.** As duas sem sessão → **302** para o login, banco vazio. Cookie forjado → idem. A guarda é middleware de negação por omissão, então não depende de o autor lembrar de decorar a rota. Varri as dez telas: todas negam anônimo.
- **A tela não quebrou as que já existiam.** As sete seções de `/configuracao` continuam presentes **e continuam gravando**: fatos, metas, financiamentos, IA e propostas. Recusa na seção nova preserva as outras; recusa numa seção antiga preserva a nova. **Nos dois sentidos.**
- **Nenhum total existente mudou.** O diff sobre o código da aplicação tem **zero deleções**. Os únicos toques em arquivo existente são duas linhas de registro do router, duas de contexto e uma de include. Nenhum arquivo de consulta, projeção, plano ou dívida foi tocado.

## Achados que não reprovam

**1 — Erro de servidor com prazo além de 64 bits.** Um prazo com algarismos demais devolve **500**, não 400. Nada é gravado e o banco fica intacto, mas a tela cai. **Não reprova, e explico por quê:** não é regressão desta fase. A causa raiz é o leitor de meses, que **não tem teto de algarismos** enquanto o leitor de dinheiro tem. Provei que a mesma entrada já derruba rota entregue antes — o campo de meses de reserva também dá 500. A fase reusou a gramática existente e herdou o buraco. Pelo mesmo motivo, é a **segunda ocorrência**: vira causa raiz, não terceiro remendo, e o gêmeo se corrige junto.

Todo o resto da bateria hostil passou: forma estrangeira, ponto decimal inglês, 300 algarismos, 13 algarismos, zero, negativo, taxa acima do teto, notação científica, infinito, indefinido, taxa negativa, taxa em texto, prazo zero, fracionário, negativo e vazio, nome vazio, nome só espaço, nome longo demais, corpo sem campo, contratação inválida, corpo JSON e corpo binário — **22 casos, todos 400, todos com a recusa e a seção na resposta, todos com o banco conferido e intacto**. Injeção no nome é gravada como texto literal e a tabela continua existindo: consulta parametrizada.

**2 — A função de custo estoura com prazo zero**, e devolve custo negativo com taxa negativa. Hoje é inalcançável por HTTP, mas **a fase 2 vai chamá-la a partir do código de comparação**, onde não há rota filtrando. Vale um guarda com teste.

**3 — Bytes crus viram nome ilegível.** Não é erro de servidor nem perda de dado, mas a chave de gravação é o nome, então o dono não consegue sobrescrever essa linha redigitando — só removendo.

**4 — Lacuna na numeração de migrações.** Inofensiva hoje, e a suíte fixa a lista. Mas o executor aplica por ordem de nome pulando as já registradas: se um item futuro criar um número intermediário, ele roda depois numa base que já subiu — seguro só enquanto o esquema for independente.

**Alarme falso que verifiquei antes de levantar:** a comparação de dois pontos sugere que a branch reverte um veredicto e apaga um documento. É artefato: a branch nunca tocou esses arquivos, e a mesclagem sobre a base real dá **merge limpo**. Nenhum documento se perde.

## Instrumentos do implementer

Só o critério 9 depende da suíte do avaliado — ele **é** o comando que a roda. Os outros oito provei com sondas minhas, contra o banco e contra oráculo racional independente.

Duas divulgações: usei auxiliares de outro arquivo de teste apenas para **semear** a base nas sondas de regressão de tela, nunca como asserção; e citei a suíte de números congelados como evidência secundária para "nenhum total mudou", apoiada na primária de que nenhum arquivo de cálculo foi tocado.
