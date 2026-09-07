# Entrega — 015-configuracao-e-nome-do-beneficiario

Três fases implementadas, validadas às cegas e commitadas. A integração é
`develop`, e o merge está **travado** até o dono ratificar `D-002`.

## A pilha, uma fase por branch

| Branch | Fase | Rodadas | Veredicto |
|---|---|---|---|
| `015-.../fase-1-armazem` | Um armazém só para o que só o humano sabe | 1 | `APROVADO` |
| `015-.../fase-2-tela-de-configuracao` | A tela de configuração | 2 | `APROVADO` |
| `015-.../fase-3-nome-do-beneficiario` | O nome real do beneficiário | 1 | `APROVADO` |

Cada branch nasce da anterior. Não há remoto neste repositório, então "uma fase
é um PR" se realiza como uma branch por fase, e o merge na branch de integração
é ato do dono.

## O que passou a valer

**Fase 1.** `plan_facts` é a única tabela do que só o humano sabe, e
`plan_parameters` deixou de existir. O mesmo fato tinha dois nomes — `/dividas`
gravava `quitacao` e o consultor procurava `quitacao-cdc` —, e por isso o painel
perguntava para sempre o que o dono já tinha respondido. A coluna do valor deixou
de se chamar `value_cents`, porque agora guarda centavos, pontos-base e meses.
Existe **um** leitor de valor digitado, com uma gramática por unidade e uma
exceção: `/dividas` lia `5000.00` como R$ 500.000,00, em silêncio, no campo que
decide a venda do carro, e `inf`, `nan` e `1e308` ali — e `nan` no campo de
taxa — eram HTTP 500.

**Fase 2.** `/configuracao` lista o catálogo em dois blocos, diz qual número cada
valor move e grava. Valor ausente aparece como ausente e declara a premissa que o
painel usa no lugar. Meta informada substitui a constante **e o texto que a
nomeia**: a reserva alvo e o "6 meses de reserva" acima dela vinham de dois
lugares. Janela de mediana que a base não comporta é recusada, não truncada em
silêncio.

**Fase 3.** O consolidador carrega adiante o nome fantasia, a razão social, o
CNPJ e o recebedor que a Pluggy já mandava e a carga descartava. `payee_names`
prende o nome ao beneficiário, com chave `(payee, source)`, e a precedência tem
cinco níveis. A consulta de CNPJ é opt-in, nomeia o endpoint, valida 14 dígitos
antes de montar a URL e degrada com `200` em português. O nome resolvido é
**camada de leitura**: `row['key']` não muda, o drill-down continua abrindo, e
`/regras` segue mostrando o texto cru contra o qual o dono escreve regra.

## Correções que vieram dos validadores, com a prova de cada uma

Achado que o veredicto marcou como "não reprova" virou correção, nunca rodada
nova.

| Achado | Correção | Prova que falha sem ela |
|---|---|---|
| `gaps.py::WANTED` não derivava do catálogo: pergunta acrescentada ou renomeada não chegava ao consultor | `wanted()` lê o catálogo a cada chamada | `test_a_question_added_to_the_catalogue_reaches_the_advisor` — verificado: falha com a tupla congelada, passa com a leitura |
| A medição de largura rodava com a barra de rolagem escondida, com folga zero | `06-evidencias/viewport.mjs` perdeu o `--hide-scrollbars` | Remedido: `360` contra `375`, `753` contra `768`, `1425` contra `1440` |
| Comentário afirmando o contrário da linha que anotava | Reescrito, separando decisão de produto de medição da base | Nenhuma: é prosa, e um `grep` pelo texto testaria a redação |

E uma correção que eu mesmo achei enquanto media, com o mesmo tratamento: o
contexto do painel de `/gastos` **sobrescrevia** o mapa de rótulos que a tabela
tinha acabado de resolver, então o eixo de beneficiário mostrava a descrição
crua. Corrigido, com
`test_the_payee_axis_shows_the_resolved_name_and_keeps_the_key` — verificado:
falha com a ordem antiga do merge.

## Divergência

**`D-002`, tipo `normal`, RECONCILIADA e pendente de ratificação.** O critério de
guarda da fase 2 nomeava `POST /configuracao/cnpj`, rota que só a fase 3 cria, e
passava por construção: a guarda é middleware e devolve `302` para qualquer
caminho. Agora cada rota é cobrada na fase que a cria, e o critério exige as duas
metades — com sessão a rota responde diferente de `404`, sem sessão responde
`302`. **Trava o merge até a ratificação**, como manda a norma 4.

## Raio de impacto

Fora do item, mudaram: `app/debts/`, `app/plan/whatif.py`,
`app/projection/monthly.py`, `app/routers/{debts,whatif,plan,summary,spending,commitments}.py`,
`app/advisor/gaps.py`, `app/ingest/loader.py`, `ingestao/pluggy_consolidate.py`,
`app/queries/axes.py` e cinco templates. Nenhum total financeiro muda por causa
disso, e o critério de integração RF-28 prova que motor nenhum lê nome de
beneficiário.

## O que o dono precisa fazer

1. **Ratificar ou rejeitar `D-002`.** Enquanto não ratificar, o merge está
   travado.
2. **Copiar o arquivo da base antes do primeiro boot depois do merge.** A
   migração `010` funde `plan_parameters` em `plan_facts` e derruba a tabela, e a
   `011` acrescenta quatro colunas em `transactions`. Rodaram limpas em toda base
   de validação, inclusive sobre base com linha preexistente, mas são
   irreversíveis.
3. **Rodar o consolidador antes de sincronizar.** A carga **recusa** um
   consolidado gerado antes desta mudança, dizendo isso — sem a recusa, apertar
   Sincronizar zeraria as quatro colunas novas em 1942 linhas e o `sync_runs`
   registraria `ok`.

## Validação de campo pendente

A consulta de CNPJ só se prova com rede. Como verificar: pôr `DASH_CNPJ_LOOKUP=1`
no ambiente, consultar `pagamento de boleto mycon` — cujo CNPJ na base é
`27268770000176` — e conferir que o nome devolvido é reconhecível ao lado da
razão social que a própria base já traz para o beneficiário vizinho,
`COIMEX ADMINISTRADORA DE CONSORCIOS S.A`.

## Pendências que viraram roadmap

- `016-data-de-referencia-no-caminho-de-recusa` — `_reference` de
  `app/routers/whatif.py` e de `app/routers/advisor.py` cai em `date.today()` em
  vez de `reference_date()` quando a data pedida é inválida, e é esse `today` que
  decide se um fato está vencido. Pré-existente desde o `008`, achado pelo
  validador da fase 1.
- `data/manual/*.json` carregam saldo devedor, juros e prazo informados pelo
  humano em arquivo cujo nome está no código. É invariante 26 e não cabia aqui.
