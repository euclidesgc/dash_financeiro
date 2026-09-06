## 1. O que foi implementado

**Item:** `002-gastos-tres-eixos` · **Fase:** `1 — Taxonomia e motor de classificação`

Antes desta fase o banco sabia dizer quanto saiu, e nada além. Agora ele sabe
**de onde saiu, de que natureza e com que essencialidade**: a migração `003` traz
os dez grupos, as três naturezas, as três essencialidades, os dois cruzamentos e
a tabela de regras; o seed carrega tudo de `app/taxonomy/seed.json`, com regra
para 76 das 77 categorias observadas; e o classificador aplica as regras aos
1.942 lançamentos em ordem determinística, preenchendo também o beneficiário
derivado da descrição normalizada.

Duas escolhas que atravessam o item inteiro:

- **O vocabulário não existe em código.** Nenhum nome de grupo, natureza,
  essencialidade ou categoria aparece como literal em `.py`, `.sql` ou `.html` de
  `app/` — um teste varre isso a partir do próprio `seed.json`, então acrescentar
  um termo novo ao seed automaticamente amplia a varredura.
- **`Não classificado` fica sem regra, de propósito.** É o nome que a
  consolidação deu ao que ninguém classificou; cobri-lo por regra esvaziaria o
  balde de resíduo no primeiro dia e esconderia justamente o que precisa de olho.

Branch: `002-gastos-tres-eixos/fase-1-taxonomia` · commits `ba30005` e `7e9851f`.

**Esta fase foi reprovada na primeira rodada.** Um critério exigia que o
cruzamento fosse consultável logo depois da reclassificação, e a tabela
`crossings` estava semeada e inerte — nenhum código a lia. O veredicto da
primeira rodada está guardado em
[`05-veredictos/fase-1-reprovada.md`](../05-veredictos/fase-1-reprovada.md); a
correção foi `app/queries/crossings.py`, e a revalidação foi feita por um
validador novo, do zero.

---

## 2. Critérios atendidos

Os catorze critérios foram executados por um validador cego contra os 1.942
lançamentos reais. O veredicto integral está em
[`05-veredictos/fase-1.md`](../05-veredictos/fase-1.md).

- [x] `[comando]` RF-01 — as seis tabelas, as cinco colunas novas e o índice de
      beneficiário existem. **Evidência:** `6 5 1`, com `migrations applied: 3`.
- [x] `[comando]` RF-01 — as migrações `001` e `002` não foram tocadas.
      **Evidência:** `grep -Ec` → `0` nas duas.
- [x] `[comando]` RF-02, RF-03 — os dez grupos, as três naturezas e as três
      essencialidades, na ordem declarada. **Evidência:** a linha completa, igual
      caractere a caractere à esperada.
- [x] `[comando]` RF-04, RF-05 — 77 categorias na base, uma única sem regra
      (`Não classificado`), nenhuma regra nascendo `supérfluo`.
      **Evidência:** `77 1 0 1 1 0 1`.
- [x] `[comportamental]` RF-06 — o seed roda duas vezes e as contagens não mudam.
      **Evidência:** `10 3 3 2 80` antes e depois.
- [x] `[comportamental]` RF-07 — grupo, natureza e essencialidade fora do
      vocabulário são recusados, cada um nomeando o valor inválido, e nada é
      gravado.
- [x] `[comando]` RF-08 — nenhum termo do seed aparece como literal em código de
      `app/`. **Evidência:** `0 []`, exit 0.
- [x] `[comando]` RF-09 — nenhum lançamento sem os três eixos e sem beneficiário.
      **Evidência:** `0 0 1942`.
- [x] `[comando]` RF-10 — o beneficiário gravado bate, lançamento a lançamento,
      com a descrição normalizada da fonte. **Evidência:** `0 0 1942`.
- [x] `[comportamental]` RF-11 — reclassificar de novo não muda nada.
      **Evidência:** assinatura `1942 85507 13046 33394` antes e depois; `diff`
      vazio.
- [x] `[comportamental]` RF-11 — regra de expressão vence regra de categoria.
      **Evidência:** a regra `ifood` reclassificou 26, e 26 é o total de
      lançamentos cuja descrição a contém.
- [x] `[comportamental]` RF-12 — removida a regra de `Eating out`, os 128
      lançamentos caem no resíduo e o balde do período mostra `60 -436013`.
- [x] `[comportamental]` RF-13 — mudar a essencialidade para `supérfluo`
      reclassifica 128 e o cruzamento `corte`, consultado em seguida, traz
      `Eating out −R$ 4.360,13` em 60 lançamentos.
- [x] `[comando]` RF-14 — a gravação da regra e a reclassificação são a mesma
      transação: falha no meio não deixa base meio reclassificada.

**Portões:** `pytest -q` → `167 passed`, exit 0; `gates_runner.sh` →
`✓ gates: limpos`. Lint Python continua **não medido** — é a dívida técnica
`010-lint-e-formatador-python` do roadmap.

---

## 3. Como testar à mão

1. `rm -f /tmp/dash-tax.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-tax.sqlite .venv/bin/python -m app.ingest`
2. **Esperado:** três linhas de migração, `ingested transactions=1942 accounts=12`,
   `taxonomy seeded: groups=10 … rules=80` e
   `classified 1942: changed=1942 without_rule=7`.
3. `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-tax.sqlite .venv/bin/python -m app.query "select nature, essentiality, count(*) from transactions group by 1, 2 order by 3 desc"`
4. **Esperado:** os pares de natureza e essencialidade, sem nenhuma linha com
   valor vazio.
5. Repita o comando 1.
6. **Esperado:** as mesmas contagens, com `changed=0` — a classificação é
   determinística.

---

## 4. Divergências

nenhuma

---

## 5. Raio de impacto

> **Conjunto de candidatos, não verdade.** A precisão medida do raio de impacto
> é **0,578** — cerca de 42% dos candidatos são falso-positivo. Os confirmados
> abaixo foram lidos; os candidatos, não.

**Confirmados** (lidos, a dependência existe):

- `app/taxonomy/seed.json` — **a fonte do vocabulário do produto**. Grupo,
  natureza, essencialidade, cruzamento, regra e mensagem de recusa vivem aqui.
  Acrescentar termo aqui amplia sozinho a varredura que proíbe literal em código.
- `app/taxonomy/classify.py` — `classify_all` e `residue`. Toda agregação da
  fase 2 lê as colunas que ele materializa.
- `app/taxonomy/rules.py` — `create_rule`, `update_rule`, `delete_rule`, cada uma
  devolvendo quantos lançamentos reclassificou, tudo em transação única. É o que
  a tela de Regras da fase 4 consome.
- `app/queries/crossings.py` — `crossing(conn, slug, start, end)`. O par
  (natureza, essencialidade) vem da tabela, nunca de literal.
  `monthly_average_cents` nasce aqui porque é ele que dimensiona a reserva do
  item `007`.
- `app/ingest/normalize.py` — `normalize_description`, movida da taxonomia para a
  ingestão: a normalização é propriedade da fonte, e o item `006` vai precisar
  dela sem carregar a taxonomia junto.
- `app/ingest/__main__.py` — a ingestão agora termina rodando seed e
  classificação no mesmo processo. Carga que falha não classifica, e o código de
  saída continua diferente de zero.
- `app/queries/spending.py` — só o comentário mudou, para não citar nome de
  categoria.

**Candidatos** (não conferidos):

- `ingestao/pluggy_consolidate.py` — a função `normalizar` dele é a origem da
  regra que `normalize_description` reproduz. As duas precisam continuar
  concordando; o teste que compara os 1.942 registros com o campo `chave` é quem
  cobra isso.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

- **Regra de expressão pode ser gravada e casar zero lançamentos, em silêncio.**
  O validador mediu: a expressão é compilada sem `re.IGNORECASE` e casada contra
  a descrição normalizada, que vem minúscula, sem acento e **sem dígito**. Uma
  regra escrita como `Uber`, `99app` ou `saúde` é aceita e não faz nada. **Não
  virou item de roadmap**: é trabalho da fase 4 deste mesmo item, a tela de
  Regras, e está registrado como pendência dela — a tela mostra quantos
  lançamentos a regra alcançou, e uma regra que alcança zero precisa dizer isso
  na hora, não depois.
- **As categorias aparecem em inglês** (`Eating out`, `Groceries`), porque são a
  string crua da Pluggy, e a interface é pt-BR. Decisão registrada como `D8` em
  `decisoes-autonomas.md`: o rótulo em português entra no `seed.json` na fase 3,
  junto com a tela que os exibe; o nome da Pluggy continua sendo a chave, porque
  é ele que casa com a fonte a cada sincronização.
