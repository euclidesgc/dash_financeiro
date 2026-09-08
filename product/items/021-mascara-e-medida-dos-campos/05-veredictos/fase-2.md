# Veredicto — 021, fase 2 (Os campos declaram, e cabem no que declaram)

**Veredicto:** APROVADO · **Validação cega** · **Data:** 08/09/2026

Última fase do item e da corrida.

## Portões

| Portão | Resultado |
|---|---|
| `scripts/lint.sh` | OK — `All checks passed!`, `180 files already formatted`, `Success: no issues found in 109 source files` |
| Suíte | OK — `740 passed`, saída `0` |
| `scripts/gates/gates_runner.sh` | OK — `gates: limpos (árvore completa, 641 arquivo(s) considerados)`, sem `nao_mediu` |

## Critérios

**`comando` (RF-01, RF-02) — e o medidor foi visto acusando.**
`python3 scripts/campos-digitaveis.py` → `campos digitáveis: 37; sem declaração
completa: 0`, saída `0`. O validador então **quebrou de propósito**: tirou o
`maxlength` do campo de login e rodou de novo → `sem declaração completa: 1`,
apontando o arquivo e a linha, saída `1`. Restaurou, e voltou a `0`. Um medidor
que nunca foi visto acusando não foi provado.

**`estrutural` (RF-03) — nenhum teto escrito duas vezes.**
`grep -rn 'maxlength="[0-9]' app/templates` não imprime linha nenhuma;
`grep -rn 'maxlength="{{' app/templates` imprime 33. `app/main.py` expõe
`app/settings/limits.py` como global do Jinja — o teto do campo e o do servidor
são literalmente o mesmo número.

**`estrutural` (RF-04) — uma regra, e o que ela trouxe além.**
`git diff develop -- app/static/css/` mostra **um** seletor acrescentado,
`.field-input[maxlength]`. Ele traz `width: auto; max-width: 100%` — o texto de
D-001 — mais `min-width: 0` e `justify-self: start`. O validador registra o
acréscimo e explica por que não reprova: nenhum dos dois introduz medida de
largura própria, e sem eles o item de grade ignora o `size` do campo, porque
`.field` é `display: grid`. A largura continua **derivando** do teto declarado,
que é o que a divergência autorizou.

**`comportamental` (RF-04, RF-08) — as seis telas, de uma subida só.**
O validador rodou ele mesmo a captura em lote: uma subida, um login, 24
capturas. As seis rotas devolvem `200`. Em 375, 768 e 1440, claro e escuro: o
campo de aporte fica visivelmente estreito e a pergunta livre ao consultor ocupa
quase a coluna inteira — **as duas larguras deixaram de ser iguais**, que é o
exemplo com que o brief descrevia o defeito. Nenhum campo transborda a coluna
nem quebra a grade, inclusive o pior caso, a expressão de regra com `size="200"`.

**`comportamental` (RF-01, RF-08) — o risco central não se realizou.**
`aporte=9.999.999.999,99` — doze algarismos, dezesseis caracteres, exatamente o
teto declarado — entra inteiro e o simulador responde `45 parcelas eliminadas`,
`R$ 16.413,49` de juros. `prazo=420` no financiamento entra e volta como `420` na
tela seguinte. **Nada que era legítimo passou a ser recusado.**

**`comando` de integração (RF-03) — a coerência.** `-k coerencia` → `7 passed`.
E o validador não se apoiou só no teste do avaliado: rastreou à mão os importes
dos **oito** módulos de validação até `app/settings/limits.py`, confirmando que a
constante é usada na checagem real, não só declarada no template.

## Provas de norma

- **Norma 13 — autorização é do servidor.** `POST` com prazo de treze algarismos,
  passando por cima do `maxlength="12"` do campo, responde `400` com mensagem em
  português, e o valor gravado antes fica intacto. O atributo é experiência de
  uso; quem recusa é o servidor.
- **Norma 24 — login antes de dado.** Sem cookie, `/dividas`, `/configuracao` e
  `/gastos` respondem `302` para `/login`, com corpo vazio.

## Achados fora do escopo

1. **Editar o financiamento do imóvel faz o CDC do veículo sumir da escada.**
   `app/financings/store.py`, em `seed_from_manual`: o guarda desiste quando a
   tabela tem **qualquer** linha, não quando tem a linha que falta. O validador
   reproduziu numa cópia da base real — que depende inteiramente dessa semeadura:
   o primeiro `POST` de financiamento imobiliário grava a linha do imóvel, e a
   reconstrução seguinte encontra uma linha e **nunca mais semeia o veículo**. O
   degrau desaparece da tela de dívidas, em silêncio. É anterior a este item e
   fora do seu diff, mas é perda de dado real na tela que decide dinheiro:
   corrigido junto, com teste que reprova sem a correção.
2. Três capturas ficaram com bytes diferentes por variação de renderização entre
   execuções, sem mudança visual. Restauradas as versionadas.
