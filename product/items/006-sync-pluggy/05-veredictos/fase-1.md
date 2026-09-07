# Veredicto — item `006-sync-pluggy`, fase 1

**Resultado:** `APROVADO` (segunda rodada). A primeira devolveu
`CRITERIO_INVALIDO`.

Branch: `006-sync-pluggy/fase-1-sync` · base `5077611` · ponta julgada `dab902b`
Data: 2026-09-07 · Dois validadores cegos, agentes novos.

> **O código mergeado não é byte a byte o que o segundo validador julgou.** Os
> quatro apontamentos dele foram corrigidos em `f5575cf`, cada um com teste.
> Régua registrada como `D8`, a mesma do `005`: uma validação por fase.

## Primeira rodada — `CRITERIO_INVALIDO`, e com razão

O critério de RF-12 mandava montar o estado de falha com
`python -m app.query "insert into sync_runs ..."`. `app.query` é **somente
leitura** desde o item `001` e recusa tudo que não seja `select` ou `pragma`:
`refused: only select and pragma are allowed`. O critério pedia uma escrita por
uma ferramenta que nunca escreveu. O validador montou o estado por escrita
direta no SQLite, mediu o *Então*, e ele **passou** — o defeito era do
enunciado.

Ele também achou três defeitos que nenhum critério cobria, e os três viraram
requisito (`RF-17`, `RF-18`, `RF-19`) antes da segunda rodada.

## Portões (segunda rodada)

| Portão | Resultado |
|---|---|
| lint | **OK** — `All checks passed!`, `EXIT=0`. O portão existe desde o item `010`. |
| testes | **OK** — `366 passed`, `EXIT=0`. |
| gates | **OK** — `✓ gates: limpos (272 arquivo(s)).` |

## Critérios — os dezesseis cumpridos

- [x] **RF-01, RF-02, RF-04, RF-05** — segunda carga: `transactions=1942`, e
      `sync_runs` com exatamente `1942 1942 ok` e `0 1942 ok`.
- [x] **RF-03** — banco criado só com `001`, linha com `transactions_count=500`,
      migrações até o fim: `transactions_present = 500`, `transactions_count = None`.
- [x] **RF-07, RF-10** — `sync ok: inserted=0 accounts=0 reference=2026-09-05`,
      `EXIT=0`.
- [x] **RF-09** — recusa nomeando as duas variáveis, `EXIT=1`, e `sync_runs` com
      `3` antes e `3` depois.
- [x] **RF-08, RF-11** — `POST /sincronizar` → `200`, com data `07/09/2026`, hora
      e contagem de inseridos.
- [x] **RF-12** — falha recente e último sucesso no mesmo bloco.
- [x] **RF-13, RF-14** — base nova: `Nunca sincronizado.` e `python -m app.sync`.
- [x] **RF-13 idade** — `O dado está parado há 109 dias.`
- [x] **RF-15** — o formulário e o botão `Sincronizar agora`.
- [x] **RF-16** — o número congelado não aparece no código.
- [x] **RF-17** — chave estrangeira órfã: `POST /sincronizar` → **200**, não 500;
      `a escrita no banco foi recusada (IntegrityError); nada foi gravado.`;
      `1942` transações antes e depois; última linha de `sync_runs` com `failed`.
- [x] **RF-18** — o bloco traz `a fonte trouxe 1 lançamento(s) que o painel não
      conseguiu ler.` e **zero** ocorrências de `rejected=`, `accepted=` ou
      `present=`.
- [x] **RF-19** — os dois testes de fuso passam, e o validador **verificou o
      mesmo pela tela**: uma execução gravada em `2026-09-08T01:00:00+00:00`
      aparece como `07/09/2026 22:00`, atravessando a meia-noite local.
- [x] **portão local, portão de lint, guarda de rota** — `366 passed`,
      `All checks passed!`, `302` sem sessão (e também com cookie forjado).

## Verificações extras que passaram

Dez cargas seguidas: `transactions=1942`, `accounts=12`, cargas 2 a 10 todas com
`inserted=0`. Coluna legada nula renderiza `—`, não `None`. Falha com `message`
nula não quebra. Idade negativa não é impressa. Varredura da prosa não achou
`None`, `null`, `ok`, `failed`, `inserted`, `status` nem `Traceback` vazando.

## Os quatro apontamentos — corrigidos em `f5575cf`

1. **O arquivo de origem ausente derrubava a rota em 500 sem gravar nada.**
   `load_transactions` rodava fora de qualquer handler. Medido:
   `POST /sincronizar` → 500, `sync_runs` `8` antes e `8` depois, e a tela
   seguindo em `Última sincronização bem-sucedida`. É o modo de falha do item
   inteiro, alcançado pelo acidente operacional mais provável de todos.
2. **O aviso do topo imprimia a mensagem crua do carregador** enquanto o bloco
   logo abaixo já dizia a mesma falha em português.
3. **`_after` roda fora de handler** — observação estrutural, lida no código e
   declarada como não provocada. Coberta pelo mesmo `try` da correção 1 não
   está; segue como risco conhecido.
4. **O fuso de um teste vazava para os seguintes** no mesmo worker: invisível
   nesta máquina, que já é −03:00, e trocaria o fuso por baixo dos testes num
   runner em UTC.
