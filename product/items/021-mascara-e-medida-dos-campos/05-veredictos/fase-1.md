# Veredicto — 021, fase 1 (A casa única dos tetos, e as três frestas fechadas)

**Veredicto:** APROVADO · **Validação cega** · **Data:** 08/09/2026

O validador não viu quem implementou nem o que ele relatou. Ele reproduziu cada
comportamento por conta própria — chamada direta às funções e requisições HTTP
que ele mesmo escreveu — sem reaproveitar uma linha do arquivo de teste do
avaliado.

## Portões

| Portão | Resultado |
|---|---|
| `scripts/lint.sh` | OK — `All checks passed!`, `180 files already formatted` |
| Suíte | OK — `732 passed`, saída `0` (717 na base, `+15` do arquivo novo) |
| `scripts/gates/gates_runner.sh` | OK — `gates: limpos (árvore completa, 597 arquivo(s) considerados)` |
| `mypy --strict` | Fora do portão no momento desta validação. Passa a valer com a fase 2 do item `018` |

## Critérios

**`estrutural` (RF-03) — a casa única.** O grep prescrito casa em
`app/settings/limits.py` e **não** casa em `app/offers/typed.py`,
`app/routers/advisor.py` nem `app/settings/typed.py`. O validador confirmou pelo
histórico que antes da fase os três escreviam o literal, e hoje importam. Os dois
tetos de texto novos também só existem em `limits.py`.

**`comando` (RF-05) — dígito não-ASCII.** `-k digito` → `3 passed`, saída `0`. O
validador reproduziu fora da suíte: `١٢٣` e `１２３` levantam recusa **tanto em
dinheiro quanto em prazo** — o teste do plano só cobria dinheiro, e ele fez o de
prazo por conta própria. Controle positivo: `parse_money("123")` continua `12300`
e `parse_months("123")` continua `123`.

**`comando` (RF-06) — teto de taxa por tipo de dívida.** `-k financiamento` →
`3 passed`. Reproduzido direto e por HTTP real: 100% ao mês é recusado num
financiamento imobiliário e continua aceito pelo leitor genérico; 30% é recusado
no imóvel e aceito no veículo; 45% é recusado no veículo. `POST` com 100% em
imóvel responde `400`.

**`comando` (RF-07) — nome ilegível.** `-k nome` → `5 passed`. O caractere de
substituição e o de controle são recusados com mensagem em português;
`Consignação Itaú` **continua aceito** e volta intacto. O filtro alcança
especificamente `U+FFFD` e a categoria de controle — nunca dispara para acento
nem cedilha.

**`comando` (RF-02) — os quatro campos de texto.** `-k teto` → `4 passed`. O
validador exercitou os quatro por HTTP com cookie: apelido de 61 caracteres →
`400`, de 60 → `200`; nome de cenário de 41 → `400`, de 40 → `200`; expressão de
regra de 201 → `400`, de 200 → `200`.

**`comando` (RF-08) — a suíte.** `732 passed`, saída `0`. A base medida na mesma
máquina: `717`. A diferença são exatamente os 15 testes do arquivo novo, e nenhum
teste pré-existente mudou de arquivo.

**`comportamental` (RF-08) — o controle positivo que importa.** Prazo de `420`
meses e valor de doze algarismos continuam aceitos, medido pela chamada direta e
repetido por HTTP real. O risco central deste item era passar a recusar o que era
legítimo, e ele não se realizou.

## O achado que virou correção

`MORTGAGE_MAX_RATE_BP` e `VEHICLE_MAX_RATE_BP` nasceram como literais **fora** de
`app/settings/limits.py`, apesar de o objetivo da fase dizer que todo teto do
projeto está escrito num lugar só. O critério passou como redigido, porque o grep
que ele prescreve só cobre os três tetos que já existiam — e é exatamente essa a
forma de fresta que RF-03 existe para fechar. Os dois foram para a casa única, e
o leitor de financiamento passou a importar de lá.

Sobre os números: o validador confirmou que **não** foram calibrados para caber
em teste antigo. As taxas reais congeladas são 0,72% ao mês no imóvel e 1,63% no
veículo (`docs/plano.md`, 05/09/2026), e o valor de 5% que a suíte já exercitava
fica a quatro vezes do teto mais apertado.

## Achados fora do escopo

1. **A suíte lê o diretório `data/` do dono, que o git não versiona.**
   `tests/test_sync.py` chama a sincronização sem substituir a etapa de carga,
   então dois testes dependem do conteúdo real e atual de arquivos fora do
   controle de versão. O validador descobriu isso porque removeu a worktree por
   engano e, ao reconstruí-la, restaurou `data/processed/` e `data/manual/` mas
   não `data/raw/` — e os dois testes passaram a falhar com violação de chave
   estrangeira. Restaurado `data/raw/`, a suíte volta a `732 passed`. É fraqueza
   pré-existente de desenho de teste, não desta fase, e vira item de roadmap: um
   teste que só passa na máquina onde os dados do dono estão completos não é
   portão, é coincidência.
2. **`PAYEE_ALIAS_MAX = 60` se justifica por uma medição que ninguém conferiu.**
   O comentário afirma que a maior razão social desta base tem menos de cinquenta
   caracteres; abrir a base do dono é vedado à validação. A ordem de grandeza é
   coerente com o teto de nome de proposta, mesmo domínio e mesmo valor.
3. **O plano chama `999.999.999,99` de "doze algarismos"; são onze.** O teto de
   doze aceita com folga, então o comportamento exigido está certo — a etiqueta
   do plano é que está imprecisa.
4. **Incidente operacional.** O validador removeu por engano a worktree que
   estava validando, e a reconstruiu. Branch e commit continuaram íntegros — o
   comando não apaga referência nem objeto. Toda a evidência de mérito havia sido
   colhida antes, e a suíte foi remedida depois da restauração completa.
