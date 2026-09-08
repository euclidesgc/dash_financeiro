# Veredicto — 028, fase 2 (A comparação na tela, e a leitura que só copia)

**Veredicto:** APROVADO · **Validação cega** · **Data:** 08/09/2026

O validador não viu o plano de implementação nem o relato de quem implementou.
Toda evidência abaixo foi produzida por instrumento próprio dele — chamadas
diretas às funções, um cliente em memória e um dublê do provedor que ele mesmo
escreveu. A suíte do avaliado só rodou onde o critério manda rodá-la.

## Portões

| Portão | Resultado |
|---|---|
| `scripts/lint.sh` | OK — `All checks passed!`, `177 files already formatted`, saída `0` |
| Suíte | OK — `700 passed` no momento da validação, saída `0` |
| `scripts/gates/gates_runner.sh` | OK — `gates: limpos (árvore completa, 586 arquivo(s) considerados)`, saída `0` |
| `mypy --strict` | **Não é portão deste projeto** (norma 35). Não executado, não contado como passe nem como falha |

## Critérios

**`estrutural` (RF-03, RF-05).** `app/offers/cost.py` exporta `compare` (linha 33)
e `comparison` (linha 75); `app/advisor/cited.py` exporta `figures` e `uncited`;
`app/advisor/context.py:5` importa `comparison`; `app/routers/advisor.py:10`
importa `uncited`. Lido nos quatro arquivos.

**`comportamental` (RF-02, RF-03) — a aritmética conferida à mão.** Com degrau a
20,00% ao mês e proposta de 10,00% ao mês, 2 meses, R$ 1.000,00 liberados e
R$ 50,00 de contratação, `compare` devolveu `stay_cents=30910`,
`offer_cents=20238`, `difference_cents=10672`. Conta refeita à mão: `1,1² = 1,21`,
parcela `10000 / 0,1735537… = 57619`, custo `57619 × 2 − 100000 + 5000 = 20238`;
`1,2² = 1,44`, parcela `20000 / 0,3055555… = 65455`, custo
`65455 × 2 − 100000 = 30910`; diferença `10672`. Bate dígito a dígito com o
código e com o plano.

**`comportamental` (RF-03, RF-04) — a comparação na tela.** Com o degrau gravado
e as duas propostas enviadas por `POST /configuracao/proposta`, `GET /consultor`
respondeu `200` e a seção `id="comparativo"` trouxe `R$ 309,10`, `R$ 202,38`,
`R$ 106,72`, o nome do degrau, e a frase `1 proposta ficou de fora` para a
proposta sem taxa.

**`comportamental` (RF-05) — a leitura que só copia aparece.** Com o provedor
substituído por um dublê que devolve só cifras do contexto, `POST /consultor`
respondeu `200` com `id="leitura"` presente, e cada cifra da resposta ocorre
literalmente no corpo que foi enviado ao provedor.

**`comportamental` (RF-05) — a leitura que inventa é descartada.** Dublê
devolvendo `R$ 987.654,32`: `id="leitura"` ausente, a cifra ausente da tela, e
`id="nao-conferido"` presente. A leitura inteira é descartada, e o número
inventado não é repetido de volta ao dono.

**`comportamental` (RF-06) — sem chave, a tela ainda serve.** Sem chave gravada,
`GET /consultor` responde `200`, o comparativo traz as três cifras, e a página
diz que a leitura não roda e aponta para `/configuracao`. A comparação é código
determinístico e não depende de modelo nenhum (norma 23).

**`comportamental` de integração (RF-08) — nada mais se moveu.** Com escada de um
degrau (−R$ 5.000,00) e comprometido diferente de zero (−R$ 50,00), os totais de
`/dividas`, `/objetivo` e `/comprometido` voltaram idênticos antes e depois de
gravar as duas propostas.

**`comando` de integração (RF-01…RF-08).** Os nove arquivos de teste do critério:
`98 passed`, saída `0`.

## Verificações de norma

- **Norma 23 — cálculo é código, nunca IA.** `grep` por `httpx`, `ask(` e
  `gemini` em `app/offers/cost.py`, `app/advisor/cited.py` e
  `app/advisor/context.py`: nenhuma ocorrência. Nenhum dos três toca rede ou
  modelo.
- **Norma 24 — login antes de qualquer dado.** Sem cookie de sessão,
  `GET /consultor` e `POST /consultor` respondem `302` para `/login`. Nenhum dado
  devolvido.
- **Segredo nunca em tela nem em erro.** Com uma chave reconhecível gravada, ela
  não aparece em nenhuma resposta HTML — nem na leitura aceita, nem na
  descartada, nem na página de erro forçada por uma falha de conexão. A chave só
  viaja no cabeçalho `x-goog-api-key` (`app/advisor/gemini.py:67`), e não há
  chamada a `print` nem a `logging` em `app/advisor/`.

## O achado que virou correção com teste

A guarda de citação **falhava aberta** em duas formas que um modelo varia
sozinho, e o validador as provou chamando `figures()` e `uncited()` diretamente:

- `R$987.654,32`, sem o espaço depois do cifrão, não era reconhecido como cifra
  **nenhuma** — e o que a gramática não reconhece, ela deixa passar. Um número
  inventado nessa forma chegaria à tela como se tivesse sido conferido.
- `R$ 202,4`, com uma casa decimal em vez de duas, escapava pela mesma porta.

Nenhum critério escrito falhou, porque os dois casos que os critérios exercitam
usam a forma canônica. Mas a promessa da fase — e a norma 23 inteira — vale
exatamente para o caso em que o modelo desobedece, e um modelo real varia
formatação com frequência. Por isso o achado virou correção nesta fase, não item
de roadmap.

**A correção.** A gramática passou a aceitar espaço opcional e uma ou duas casas
decimais, e a comparação deixou de ser literal para ser **pelo número**: cada
cifra é reduzida a centavos inteiros antes de se procurar no contexto. Assim uma
cifra reescrita — sem espaço, sem ponto de milhar, com uma casa em vez de duas —
é reconhecida como a mesma cifra e não derruba leitura correta; e uma cifra que o
contexto não contém continua acusada, seja qual for a forma. `R$ 3.400` onde o
contexto traz `R$ 3.400,57` continua sendo acusação, porque o número é outro.

Onze testes de regressão em `tests/test_cited.py`, incluindo os dois formatos que
furavam. A suíte passou de **700** para **711** testes, verde.

## Achados fora do escopo

1. **A comparação usa um degrau só** — o mais caro, `ladder(conn)[0]`. Já é
   pendência nomeada no próprio plano; reconfirmada depois desta fase.
2. **O comentário de justificativa que os portões exigem está em português**, e a
   norma 16 pede código em inglês. O portão que cobra justificativa reconhece
   palavras em português e não em inglês, então hoje as duas regras se
   contradizem. Vira item de roadmap.
