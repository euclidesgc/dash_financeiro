# Veredicto — item `008-simulador-e-base-de-fatos`, fase 1

**Resultado:** `APROVADO` (segunda rodada). A primeira devolveu `REPROVADO`.

Branch: `008-simulador/fase-1` · base `1c303ae` · ponta julgada `1a680e4`
Data: 2026-09-07 · Dois validadores cegos, agentes novos.

> Os três apontamentos da segunda rodada foram corrigidos depois do veredicto,
> com teste. Estão nomeados abaixo.

## A reprovação, e o que ela achou

O critério que reprovou foi estrutural: as capturas foram parar em
`product/items/004-simulador-e-projecao/`, um item que **não existe** — segunda
vez na corrida que o script de captura, derivado por `sed`, escreveu no
diretório errado. Mas a caça em volta achou seis defeitos, e dois deles são dos
piores que uma tela de dinheiro pode ter:

- **Multiplicação por cem, em silêncio.** Todo ponto era tratado como separador
  de milhar, então `5000.00` virava **R$ 500.000,00** — aceito, exibido e
  gravado como cenário, com `200` e sem uma palavra.
- **`500` com `inf`, `nan` e `1e3`.** O arredondamento estava fora do `try`, nos
  três campos numéricos.
- `0,004` passava pelo "maior que zero" e gravava o cenário de efeito zero.
- A validade de um fato ia crua para o banco, e o vencimento era decidido
  comparando strings: `"banana" < "2026-09-07"` é falso, então validade digitada
  errada deixava o fato **para sempre parecendo fresco**.
- **`prazo` e `valor único` eram parseados, validados, gravados e nunca usados.**
- Guardar um fato repunha a data de referência da tela para hoje.

## Portões (segunda rodada)

| Portão | Resultado |
|---|---|
| lint | **OK** — `All checks passed!`, `EXIT=0`. |
| testes | **OK** — `393 passed`, `EXIT=0`. |
| gates | **OK** — `✓ gates: limpos (302 arquivo(s)).` |

Os três foram **reexecutados ao fim**, depois de toda a manipulação, e
`git status --short` saiu vazio.

## Critérios — os treze cumpridos

- [x] **RF-01, RF-02** — o `form` certo com os cinco campos, distinguido do
      formulário de fatos.
- [x] **RF-03, RF-07, RF-09** — `data-mensal="500000"`, `data-dias=""`, a frase
      dos juros da escada, **zero** ocorrências de `negativo`, e o cenário
      guardado. O validador conferiu a aritmética à mão: `−4.523,21 + 5.000,00 =
      476,79`. E conferiu a afirmação de paridade que a própria tela faz: a tela
      de Objetivo exibe o mesmo `−R$ 4.523,21`.
- [x] **RF-08** — as três recusas com `400`, e `scenarios` com `1` antes e `1`
      depois.
- [x] **RF-03 a RF-06, RF-10, RF-12** — `16 passed`, com os sete testes lidos e
      localizados por linha.
- [x] **RF-11, RF-12** — o fato com `R$ 35.000,00` e a marca `vencido`,
      conferido inclusive quanto ao tipo de espaço no número.
- [x] **RF-14, RF-15, RF-16** — `5000.00`, `inf`, `nan`, `1e3` e `0,004`: as
      cinco em `400`, **nenhuma** em `500`.
- [x] **RF-17, RF-19** — `validade=banana` em `400`, e o `data` preservado nos
      dois formulários devolvidos.
- [x] **RF-18** — o teste do prazo e do valor único, localizado por linha.
- [x] **RF-13** — seis medições, e o validador **repetiu com as tabelas
      populadas e um nome de cenário de 5.000 caracteres**: as seis continuam
      passando. As três capturas, abertas.
- [x] **portão local, lint, um motor só, guarda** — `393 passed`, uma única
      `def simulate` em `app/plan`, `302` sem sessão.

## Instrumentos do implementer

**Nenhum critério ficou apoiado apenas na suíte do avaliado.** Os dois critérios
`comando` têm o arquivo de teste como objeto declarado, mas o validador leu o
arquivo inteiro e **corroborou por fora, no banco real e sem a fixture**, todas
as afirmações comportamentais: receita aproximando de 240 → 19 meses conforme
cresce, despesa afastando, o prazo levando a `None`, o efeito zero devolvendo o
idêntico. E varreu a conversão para centavos de `0,00` a `99.999,98` em passos de
sete centavos — 1,4 milhão de valores, **zero divergências** contra `Decimal`.

## Os três apontamentos — corrigidos depois do veredicto, com teste

1. **`500` para valores de 307 algarismos ou mais.** `float()` devolve `inf` e
   `round(inf)` levanta. O limiar foi medido com precisão: 306 aceito, 307
   estoura, nos três campos de dinheiro. **É a mesma classe que o critério
   RF-15 existia para fechar** — ele enumerava cinco literais em vez de exigir a
   propriedade, e passou por construção. Corrigido com um teto de 12 algarismos
   **e** com a conversão para centavos passando a ser de inteiro para inteiro,
   sem `float` — que era também a raiz da perda de precisão acima de 17 dígitos,
   contra o invariante 22 do projeto.
2. **O campo "Valor único" era inerte no estado real do painel.** O `injected`
   só entrava depois do `break`, e o `break` acontece sempre que o resultado do
   mês 1 é `≤ 0` — que é exatamente esta base. Medido: R$ 10 milhões de entrada
   única não mudavam nada. Corrigido somando o único **antes** da verificação.
3. **O "depois" ignorava o prazo.** Com `prazo=2` a tela dizia `R$ 476,79` sem
   dizer que valia por dois meses. Agora diz.
