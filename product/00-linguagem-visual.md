# Linguagem visual — dash_financeiro

Documento **canônico**, como o plano de produto. Toda sessão que escreve
interface o lê antes de abrir editor, e nenhuma escolhe cor, tipografia,
espaçamento, raio ou movimento fora dele. Mudar o que está aqui é reconciliação
de documento canônico — reescrita no presente, sem cicatriz —, nunca uma segunda
opinião ao lado.

Os valores vivem em `app/static/css/tokens.css`, que é a **fonte única**. Este
documento diz o porquê e a régua; o CSS diz o valor. Nenhum template e nenhuma
outra folha de estilo declara cor em hexadecimal, `rgb()` ou `hsl()`.

## O conceito: um instrumento de leitura, não um app de banco

Este painel não vende produto financeiro. Ele mede uma distância: onde o dono
está hoje e quantos **dias** faltam até o objetivo. A unidade do produto é
tempo, e a forma que corresponde a isso é a de um **instrumento graduado** —
régua, escala, marcação, cursor —, não a de um cartão de banco com gradiente.

Três consequências, e elas explicam quase todas as escolhas abaixo:

1. **A cifra é a protagonista**, e por isso a face de dados é a face principal
   da interface, não a de texto.
2. **A escala é o ornamento**, e é o único. Marcações graduadas aparecem onde
   existe distância a percorrer — a linha do tempo de 45 dias, a escada de
   dívidas, os três marcos. Onde não há distância, não há marcação.
3. **O painel sustenta por baixo.** Quem abre está resolvendo um problema de
   R$ 4.940,72 por mês. Sem confete, sem streak, sem parabéns, sem
   ilustração — e sem alarme decorativo, que é a outra forma de disputar
   atenção.

O elemento de assinatura é a **escala graduada**: uma faixa de traços finos,
desenhada em CSS por gradiente repetido, sem imagem e sem rede. Na tela de login
ela é a marca; nas telas de dados ela é o eixo do tempo. É a mesma forma
carregando a mesma ideia nos dois lugares.

## Paleta

O papel é **frio e levemente esverdeado** — a herança do papel de relatório
contábil, não o creme quente de revista. A tinta é grafite esverdeado. O acento
é **violeta de carimbo**, e ele está fora do eixo vermelho–verde de propósito:
neste produto vermelho e verde já têm significado obrigatório — dinheiro saindo
e dinheiro entrando — e um acento de marca nessas cores competiria com o dado.

### Tema claro (`:root`)

| Token | Valor | O que é |
|---|---|---|
| `--color-bg` | `#ECEFE9` | o papel, fundo da página |
| `--color-surface` | `#F7F9F5` | a superfície levantada: cartão, campo, painel |
| `--color-ink` | `#1B2118` | texto principal |
| `--color-ink-muted` | `#4A5347` | rótulo, legenda, texto secundário |
| `--color-rule` | `#C6CCC0` | fio de escala e separador — decoração, nunca sozinho |
| `--color-field-border` | `#767F74` | borda de campo e de controle |
| `--color-accent` | `#5B2C8D` | violeta de carimbo: ação primária, foco, marca |
| `--color-accent-ink` | `#F7F9F5` | texto sobre o acento |
| `--color-negative` | `#9E2B25` | dinheiro saindo |
| `--color-positive` | `#2E6B3E` | dinheiro entrando |

### Tema escuro (`@media (prefers-color-scheme: dark)`)

| Token | Valor | O que é |
|---|---|---|
| `--color-bg` | `#151A18` | grafite esverdeado, não preto |
| `--color-surface` | `#1E2421` | superfície levantada |
| `--color-ink` | `#E6EAE2` | texto principal |
| `--color-ink-muted` | `#A3ACA0` | rótulo, legenda, texto secundário |
| `--color-rule` | `#333B36` | fio de escala e separador |
| `--color-field-border` | `#727B74` | borda de campo e de controle |
| `--color-accent` | `#C4A6E8` | o mesmo violeta, clareado para o fundo escuro |
| `--color-accent-ink` | `#151A18` | texto sobre o acento |
| `--color-negative` | `#F0918A` | dinheiro saindo |
| `--color-positive` | `#86C79A` | dinheiro entrando |

**Cor nunca é o único sinal.** Todo valor negativo carrega o sinal `−` colado ao
número, e todo estado que a cor comunica traz também rótulo ou ícone. O painel se
lê em tela de celular, sob sol, com pressa — e por daltônico.

**E cor semântica é exceção, não regra.** Numa tela de gastos toda cifra é
negativa; pintar todas de vermelho produz uma parede vermelha onde o vermelho não
significa mais nada — é o oposto de sinalizar. `--color-negative` e
`--color-positive` marcam **o número que pede decisão**: o total que resume a
tela, o saldo que projeta o vermelho, o valor que muda de sinal. A coluna de
valores de uma tabela usa `--color-ink`, com o sinal `−` fazendo o trabalho de
dizer que é saída.

## Tipografia

Sem fonte de CDN. A tela precisa abrir sem rede, e uma requisição externa na
página de login é rede que o produto não controla. A personalidade vem do **uso**
das faces do sistema: qual face carrega qual papel, com que peso, tamanho e
espaçamento.

| Token | Valor | Papel |
|---|---|---|
| `--font-data` | `ui-monospace, "SF Mono", "DejaVu Sans Mono", "Liberation Mono", "Roboto Mono", Consolas, monospace` | **a face principal**: cifra, data, escala, contagem, e o título de tela |
| `--font-text` | `system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", "Liberation Sans", Arial, sans-serif` | texto corrido, rótulo, mensagem, botão |

A face monoespaçada ser a protagonista é a decisão tipográfica do projeto, e ela
vem do assunto: uma coluna de valores só se lê quando os algarismos não dançam
entre as linhas. Onde houver cifra, `font-variant-numeric: tabular-nums` — e isso
é requisito, não gosto.

### Escala

| Token | Valor | Onde |
|---|---|---|
| `--text-xs` | `0.75rem` (12px) | rótulo em versalete, legenda de escala |
| `--text-sm` | `0.8125rem` (13px) | texto secundário, mensagem de erro |
| `--text-base` | `1rem` (16px) | corpo e campo de formulário |
| `--text-lg` | `1.25rem` (20px) | título de seção |
| `--text-xl` | `1.625rem` (26px) | título de tela |
| `--text-2xl` | `2.125rem` (34px) | a cifra protagonista de cada tela |

Campo de formulário nunca desce de `--text-base`: abaixo de 16px o navegador de
celular dá zoom sozinho ao focar, e a tela salta na mão de quem digita.

### Rótulo em versalete

Rótulo é caixa alta, `--text-xs`, peso 600, `letter-spacing: 0.08em`, na cor
`--color-ink-muted`. É o vocabulário do instrumento: a legenda pequena e
espaçada ao lado da graduação. Vale para rótulo de campo, cabeçalho de coluna e
eyebrow de seção — e para mais nada, porque caixa alta em texto corrido não se
lê.

## Espaçamento

Base de 4px, sem valor fora da escala.

| Token | Valor |
|---|---|
| `--space-1` | `0.25rem` (4px) |
| `--space-2` | `0.5rem` (8px) |
| `--space-3` | `0.75rem` (12px) |
| `--space-4` | `1rem` (16px) |
| `--space-6` | `1.5rem` (24px) |
| `--space-8` | `2rem` (32px) |
| `--space-12` | `3rem` (48px) |
| `--space-16` | `4rem` (64px) |
| `--measure` | `34rem` |
| `--measure-wide` | `96rem` |

Duas medidas, porque são dois leitores. `--measure` é a **largura de leitura**:
nenhum bloco de texto passa dela, em monitor nenhum, e o limite mora no
parágrafo — não no painel que o contém. `--measure-wide` é a **largura de
dado**: o painel que carrega tabela, gráfico ou calendário toma a largura que o
monitor tem, porque uma coluna de cifras não é uma coluna de prosa.

Acima de `75rem` de viewport o painel largo comporta dois blocos que sozinhos
empilhariam: o calendário da projeção se abre em colunas e o gráfico senta ao
lado da própria tabela. A tabela, essa, para em duas medidas (`68rem`) — mais
larga que isso, o olho perde a linha entre o nome e o valor.

## Raio

| Token | Valor | Onde |
|---|---|---|
| `--radius-sm` | `2px` | campo, botão, marca de escala |
| `--radius-md` | `4px` | cartão, painel |

Nada acima de 4px. Instrumento tem canto usinado, não canto de bolha — e raio
zero em tudo é a outra caricatura, a do jornal.

## Foco

| Token | Valor |
|---|---|
| `--focus-width` | `2px` |
| `--focus-offset` | `2px` |
| `--focus-color` | `--color-accent` |

Todo elemento que recebe foco mostra `outline: var(--focus-width) solid
var(--focus-color)` com `outline-offset: var(--focus-offset)`. **Nenhuma regra
do projeto zera `outline`.** Percorrer a tela inteira só com `Tab` precisa
mostrar onde o foco está, em cada parada, nos dois temas.

## Movimento

| Token | Valor |
|---|---|
| `--motion-fast` | `120ms` |
| `--motion-ease` | `cubic-bezier(0.2, 0, 0, 1)` |

Movimento existe para confirmar que algo respondeu ao toque — mudança de foco, de
estado de botão, entrada de mensagem de erro. Nada se move sozinho, nada pisca,
nada desliza para chamar atenção.

Sob `@media (prefers-reduced-motion: reduce)` toda duração de animação e de
transição é `0s` e o estado final permanece. Isso mora no `tokens.css`, uma vez,
e não é lembrado componente a componente.

## Pares de contraste

A régua é WCAG 2.1 AA: **4.5** para texto, **3.0** para borda de componente e
borda de foco. A tabela é lida pelo teste automatizado — `tests/test_contrast.py`
casa cada linha com os valores declarados no `tokens.css`, nos dois temas — e por
isso o formato não muda: token de frente, token de fundo, papel, mínimo exigido.

| Frente | Fundo | Papel | Mínimo |
|---|---|---|---|
| `--color-ink` | `--color-bg` | texto | 4.5 |
| `--color-ink` | `--color-surface` | texto | 4.5 |
| `--color-ink-muted` | `--color-bg` | texto | 4.5 |
| `--color-ink-muted` | `--color-surface` | texto | 4.5 |
| `--color-accent` | `--color-bg` | texto | 4.5 |
| `--color-accent` | `--color-surface` | texto | 4.5 |
| `--color-accent-ink` | `--color-accent` | texto | 4.5 |
| `--color-negative` | `--color-surface` | texto | 4.5 |
| `--color-positive` | `--color-surface` | texto | 4.5 |
| `--color-field-border` | `--color-surface` | borda | 3.0 |
| `--color-field-border` | `--color-bg` | borda | 3.0 |
| `--color-accent` | `--color-bg` | borda | 3.0 |
| `--color-accent` | `--color-surface` | borda | 3.0 |

## O que a régua não negocia

| O quê | Como se prova |
|---|---|
| Contraste AA nos dois temas | a tabela acima, medida por `tests/test_contrast.py` |
| Foco visível em tudo que recebe foco | percorrer a tela inteira só com `Tab` |
| Responsivo de 375 a 1920 | sem rolagem horizontal do corpo em 375, 768, 1024, 1440 e 1920 |
| `prefers-reduced-motion` respeitado | a animação some, o estado final permanece |
| Nenhum valor mágico | cor e espaço vêm do token; hexadecimal só em `tokens.css` |
| Estado vazio e de erro acionáveis | dizem o que aconteceu e qual é o próximo ato |
| Algarismo tabular em toda cifra | `font-variant-numeric: tabular-nums` na classe de cifra |

## Navegação

As telas do painel são um lugar onde se está, não um passo de uma sequência: a
navegação é uma barra fixa na lateral esquerda, com o nome do painel gravado em
versalete no alto e a saída da sessão embaixo, separada por um fio. Ela é a
mesma em todas as telas com dado, e não existe na de login, onde ainda não há
para onde ir.

Onde se está é uma **aresta**: o traço de acento de `--space-1` na borda
esquerda do item, o mesmo que a mensagem usa para dizer que uma escrita
aconteceu. A aresta nunca carrega o sentido sozinha — o item atual também toma
a tinta cheia e o peso 600, e leva `aria-current="page"`.

Abaixo de `60rem` a barra deita: vira uma faixa no topo que rola dentro de si
mesma, com a aresta na borda inferior, e o corpo da página nunca herda a
rolagem lateral.

## Escrita de interface

Português do Brasil, frase em caixa baixa com maiúscula inicial, verbo no
infinitivo ou no imperativo, sem exclamação.

- O botão diz o que acontece: **Entrar**, não "Enviar".
- A ação mantém o nome do começo ao fim: quem clica em "Salvar" recebe "Salvo".
- Erro não pede desculpa e não é vago: diz o que aconteceu e qual é o próximo
  ato. "Login ou senha inválidos." é a mensagem única do login — e ela é única de
  propósito, para a tela não virar oráculo de quais logins existem.
- Tela vazia é convite: diz o que colocar ali e como.
- Nada de "Ops", "Oops", "Ei", nem de tom animado. O assunto é dinheiro que está
  faltando.
