# Veredicto — item `009-ia-consultora`, fase 1

**Resultado:** `APROVADO`

Branch: `009-ia-consultora/fase-1` · base `26abe8a` · ponta julgada `cf38c41`
Data: 2026-09-07 · Validador cego, agente novo.

> Os cinco apontamentos foram corrigidos depois do veredicto, com teste, em
> `d478c15`. Régua registrada em `D5`, a mesma do `005` e do `006`.

## Portões

| Portão | Resultado |
|---|---|
| lint | **OK** — `All checks passed!`, `EXIT=0`. |
| testes | **OK** — `408 passed`, `EXIT=0`. |
| gates | **OK** — `✓ gates: limpos (319 arquivo(s)).` |

**Nota de método do validador:** a primeira sonda em `/login` respondeu `200` de
um servidor órfão de sessão anterior, que ainda segurava a porta 8000 e um
descritor do banco recriado. Ele matou o órfão e **refez toda a medição** num
servidor próprio, com PID confirmado. Nenhuma evidência veio daquele processo.

## Critérios — os doze cumpridos

- [x] **RF-01, RF-02, RF-10** — `200`; **exatamente um** `data-pergunta`,
      valendo `taxa-cartao`; o texto com `Qual é` e o link para `/dividas`,
      conferido como tela real; e os `data-numero` no bloco de números.
- [x] **RF-05** — adiar `taxa-cartao` faz a pergunta virar `quitacao-cdc`, e o
      adiamento persiste no `GET` seguinte.
- [x] **RF-12, RF-13** — servidor **sem chave**, verificado em
      `/proc/<pid>/environ` nas **duas grafias** que o `config` aceita.
      `POST /consultor` → `200`, não `500`, com `GEMINI_API_KEY` e `não dependem
      dela` na mensagem, e os números intactos.
- [x] **RF-14** — vazia → `400`; 600 caracteres → `400`. **A fronteira foi
      conferida à parte: 500 → 200, 501 → 400.**
- [x] **RF-03 a RF-08, RF-11, RF-13** — `12 passed`, com os sete testes
      localizados por linha, incluindo o que substitui `httpx.post` por algo que
      falha se for chamado — a prova de que o instantâneo não passa pelo modelo.
- [x] **RF-08, RF-09** — `NUNCA CALCULA` presente uma vez; `httpx` aparece
      **apenas** em `gemini.py`, em nenhuma linha de `context.py` ou `gaps.py`.
- [x] **RF-15** — seis medições, `filhos_pergunta=10` (a asserção não é vazia) e
      `violacoes_movimento=[]` em todas. As três capturas, PNG reais nas
      dimensões declaradas.
- [x] **portão local, lint, cor, guarda** — `408 passed`, zero cor literal,
      `302` sem sessão nas **três** rotas (o validador estendeu por conta
      própria a `POST /consultor` e `POST /consultor/adiar`).

## A caça dirigida

- **Rede cortada de verdade:** com chave falsa, o provedor recusou e a tela
  respondeu `200` com os cinco números **idênticos** aos da execução sem chave.
  Nenhum número exibido depende de rede. E a chave falsa **não vazou** na
  página: o código usa `type(failure).__name__` e não `str(failure)`, que
  carregaria a URL com a chave nos parâmetros.
- **Entradas hostis:** aspas, `<script>`, injeção de template, SQL, path
  traversal, bytes crus com surrogates, 5.000 caracteres, datas malformadas —
  **nenhum `500`**, nas três rotas, e a pergunta ecoada volta escapada.
- **Prosa:** sem `None`, `null`, `True/False`, `{{`, `Traceback` ou
  `object at 0x` no texto visível.

## Os cinco apontamentos — corrigidos em `d478c15`

1. **A tela mostrava cinco das oito linhas que vão para o modelo.** Ficavam de
   fora caixa, cartão, tempo até o objetivo e a data do pior ponto. **Isso
   inverte a garantia central do item**: se o modelo citasse o caixa — e a
   instrução o autoriza, porque o valor está no contexto —, o dono não acharia o
   número na tela e leria como invenção. A tela que existe para provar que a IA
   não inventa era a que produzia a suspeita. Tela e contexto passaram a ser
   **uma lista só**, construída num lugar só.
2. `context_text` era calculado e nunca renderizado — resquício da intenção
   acima.
3. **Nome de classe Python na prosa em pt-BR.** "A leitura da IA está
   indisponível (HTTPStatusError)." Chave recusada, timeout e erro do provedor
   chegavam com a mesma frase e um identificador que o dono não pode agir sobre.
4. **O estado vazio mentia quando tudo tinha sido adiado.** Afirmava que a
   projeção usa fato e não premissa mesmo com `plan_facts` vazia — e o estado era
   **terminal**, porque adiamento sem fato nunca expira.
5. **O adiamento aceitava qualquer string** como chave primária, sem teto, num
   POST autenticado.
6. `GEMIMI_API_KEY` era aceita sem uma linha dizendo que a grafia errada é a que
   já existe no ambiente do dono — exatamente o "contorno externo" que a regra 11
   manda comentar.
