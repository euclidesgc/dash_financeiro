# Revisão pré-código — 015

Quatro revisores de modelo forte leram o `03-plan.md` contra o código real, sem
escrever uma linha de implementação. Cada um recebeu uma dimensão: fase 1, fase
2, fase 3 e a transversal de segurança e invariantes. **36 problemas distintos**,
todos com evidência medida. Os que mudaram plano ou brief estão abaixo; os que
sobreviveram à minha conferência viraram correção.

## Três defeitos vivos, que não são deste item

1. **O painel pergunta para sempre o que o dono já respondeu.** `/dividas` grava
   o saldo de quitação como `quitacao` em `plan_parameters`
   (`app/routers/debts.py:48`); o consultor procura `quitacao-cdc` em
   `plan_facts` (`app/advisor/gaps.py:7`). Mesmo par para transporte. É a causa
   exata do sintoma que abriu este item.
2. **`/dividas` lê `5000.00` como R$ 500.000,00**, em silêncio, no campo do saldo
   de quitação (`app/debts/simulate.py:89`) — a falha que o item `008` corrigiu
   no outro leitor. E `inf`, `1e308` e `nan` no mesmo campo, e `nan` no campo de
   taxa, são HTTP 500.
3. **`httpx` está no grupo `dev` do `pyproject.toml`** e
   `app/advisor/gemini.py:4` o importa em produção. Instalação sem o grupo dev
   não sobe o app. Norma 15.

Os três entram no escopo: o 1 e o 2 porque a fase 1 passa exatamente por ali, o
3 porque a fase 3 seria o segundo consumidor.

## O que a revisão mudou no plano

| Achado | Correção |
|---|---|
| `ALTER TABLE ADD COLUMN NOT NULL` falha em tabela com linha — passa em todo teste e quebra só na base do dono | `DEFAULT 'fato'`, e o critério cria linha preexistente em `plan_facts` |
| Existem **três** catálogos, não dois: `PARAMETERS`, `gaps.py::WANTED` e o nome livre de `/simulador` | O catálogo é a promoção do `WANTED`, que é o mais rico; os nomes dele são os canônicos |
| `value_cents` guardaria centavos, pontos-base e meses, e `simulador.html:122` renderiza tudo com `\|brl`: `550` viraria "R$ 5,50" | A coluna passa a se chamar `value`, e a formatação segue a `unit` |
| O leitor único não tinha exceção decidida: **cinco `except` órfãos**, três rotas de 400 para 500 | Uma exceção só, `InvalidValueError`, e as cinco sedes nomeadas na etapa |
| Taxa usa ponto decimal e faixa 0–100%; o leitor estrito de dinheiro recusaria `3,52`→`3.52` e aceitaria 200% ao mês | `typed.py` tem uma gramática por unidade, não uma só |
| `tests/test_debts.py:6` importa no topo: apagar `parse_amount` some com **17 testes**. `tests/test_migrations.py:23,70` trava tabela e contagem | Ambos entram no escopo declarado da etapa |
| `RESERVE_MONTHS` também vira **texto** em `objetivo.html:12,96`: a tela diria "6 meses" acima de uma cifra de 3, e o critério aprovava em verde | A etapa nomeia `routers/plan.py:75` e as duas linhas do template; o critério mede o texto |
| `mediana-meses` entra em `survival_floor_cents`, que multiplica a reserva — não são independentes. E `seen[-N:]` trunca calado | O acoplamento é declarado, e pedir mais meses do que a base tem é recusado |
| Há **dois padrões de campo**; eu apontei o quebrado. `input.field` perde borda, raio e cai abaixo de 16px | Fixado `div.field > label.field-label > input.field-input` |
| `plan.py` não tem `_answer`; HTMX no projeto é **rota separada** para `fragments/`, não cabeçalho; e nada registrava o router em `app/main.py` | A etapa copia o `_answer` de `whatif.py`, o `_text` de `rules.py`, e registra o router |
| Sem o `_text` de `rules.py:264`, `Consórcio Coimex` chega mojibake — decisão da fase 2, prejuízo da fase 3 | `_text` entra na etapa 2.1 |
| `payee_names` com `payee` como chave primária comporta **4** níveis para uma precedência de **5**: batizar destrói o nome consultado, e apagar não devolve o anterior — RF-24 quebrada | Chave composta `(payee, source)`, como `commitments` já faz |
| `/gastos` tem cinco eixos e uma macro `cell_name` compartilhada; `row['key']` é rótulo **e** chave de drill-down | Só o eixo de beneficiário, só pelo mapa `labels`, chave intocada; `/regras` fora |
| O consolidado velho + botão Sincronizar **apaga** as quatro colunas em 1942 linhas, sem erro | A carga recusa consolidado sem as chaves novas |
| A consulta de CNPJ era a primeira saída de rede **sem opt-in**, com destino não nomeado, e a lista é ordenada por dinheiro | Opt-in explícito como o `009`, endpoint nomeado, 14 dígitos validados, e `payee_names` é o cache |
| Meus números vinham de um predicado de gasto próprio; o projeto tem `SPENDING` em `app/queries/spending.py:8` | Adotado: **720** beneficiários, **55,53%**, **72,83%**, **36,1%** |
| Sete critérios não mediam o que diziam | Reescritos — ver abaixo |
| O script de captura **não existe no repositório**, e é por isso que o erro se repetiu quatro vezes | Norma 20: o script passa a ser artefato versionado |

## Os sete critérios que passavam sem provar

1. `grep -o 'data-config="[a-z-]*"'` **some com a linha inteira** se o nome tiver dígito — e RF-08 pede taxa por dívida, cujo nome natural é `taxa-3`.
2. `grep -o 'data-gasto="[0-9]*"'` não casa valor negativo; `sort -c` aprova o vazio. A invariante 22 exige o sinal.
3. `--include=*.py` sem aspas: o zsh **aborta a linha** e o critério "não imprime nada" passa sem rodar.
4. `def parse_amount|def parse_rate|def _cents\(typed` não acha o leitor novo se ele tiver outro nome — passaria com o arquivo vazio.
5. `data-total` em `/comprometido` é o total **de um dia do calendário** (−12727), não o comprometido (−802679).
6. `grep -c "Consórcio Coimex"` imprime **3**, não 1: a série alimenta a tabela e duas ocorrências do calendário.
7. O critério de `prefers-reduced-motion` passaria **com o `tokens.css` ausente**, porque elemento sem transição já vale `0s`.

Além de: `where cnpj is not null` consultava coluna que a migração chama
`merchant_cnpj`; o cenário de RF-02 não era construível porque `apply_migrations`
não aceita versão; `app/query.py:22` imprime separado por espaço, não por `|`; e
o meu número `391` era `386`.

## Pendências que viram item de roadmap, não escopo

- `data/manual/financiamento_caixa.json` e `cdc_safra_veiculo.json` carregam saldo
  devedor, juros e prazo informados pelo humano, em arquivo com o nome do banco
  no código (`app/debts/ladder.py:22`). É invariante 26 e não cabe aqui.
- `tests/` não tem guarda global de rede; cada teste do consultor faz o seu
  `monkeypatch`. A fase 3 acrescenta a guarda porque passa a ter um segundo
  consumidor de rede, mas varrer o resto é outro item.
