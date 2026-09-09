# Veredicto — 034, fase 2 (A árvore antiga se adapta, e o recorte sai)

**Veredicto:** APROVADO · **Validação cega** · **Data:** 08/09/2026

Última fase da entrega.

## Portões

| Portão | Resultado |
|---|---|
| `scripts/lint.sh` | OK — `All checks passed!`, `182 files already formatted`, `Success: no issues found in 109 source files` |
| Suíte | OK — `771 passed`, saída `0` |
| `scripts/gates/gates_runner.sh` | OK — `gates: limpos (árvore completa, 673 arquivo(s) considerados)` |

## Critérios

**`comando` (RF-03) — e o `0` é conserto, não permissividade.** A varredura do
portão devolve `0`. O validador então injetou num arquivo de consulta **dois**
comentários — um sem marca ao lado de código, outro repetindo a linha seguinte —
e os dois foram acusados, com `gates_runner.sh` saindo `1`. Desfeitos, voltou a
`0`. E um comentário com marca no mesmo lugar passa.

**`estrutural` (RF-04) — o recorte saiu, e só ele.** O portão de comentário não
traz mais `modo` nem `desde`. Controle positivo: os outros dois portões seguem
com toda a configuração idêntica. Tirar o recorte não foi tirar o portão.

**`comando` (RF-04).** A saída diz **árvore completa**, não um recorte.

**`comando` (RF-05).** `771 passed`, e o validador conferiu por conta própria que
`develop` também coleta 771. Comentário não executa.

**`comportamental` (RF-05).** Com base semeada do zero e `DASH_TODAY=2026-09-05`,
o HTML de `/`, `/gastos`, `/comprometido` e `/dividas` saiu **byte a byte
idêntico** entre esta branch e `develop`, nas quatro.

**Critério de integração.** Um comentário novo sem justificativa faz o portão
sair `1`, nomeando arquivo e linha. Desfeito, volta a `0`. O portão passou a
julgar a árvore inteira, e não a lembrança do recorte.

## As razões que sobreviveram

Era o risco declarado do item: **apagar a razão junto com a prosa**. O validador
isolou no diff os trechos com remoção líquida de comentário e achou **três**
blocos realmente apagados — todos assinatura de função, do tipo
`nome_da_função <arg1> <arg2>`, nunca um porquê. Em cada um, a razão de verdade
que vivia ao lado foi preservada, traduzida e marcada.

Um quarto candidato era falso positivo do próprio portão: uma linha `## Itens`
dentro de uma string de fixture de teste, varrida como se fosse comentário. Foi
corrigido no próprio portão.

E ele fez busca dirigida por **número medido, data, incidente e decisão de
segurança** nas linhas removidas. Toda ocorrência tinha linha correspondente
carregando o mesmo dado, só traduzida e marcada — as taxas reais desta base
(0,72% no imóvel, 1,63% no CDC do veículo, com a data da medição), a decisão de
não limitar senha nem chave de API no servidor por causa do algoritmo de hash, a
data de um incidente de merge medido, e a cópia temporária da base do dono na
captura. **Nenhuma razão sumiu.**

## As marcas que conferi

O outro risco era a marca virar enfeite: prosa descritiva ganhando etiqueta só
para passar. O validador amostrou **18 blocos** — três a mais do que os quinze
pedidos — em `app`, `scripts` e `tests`, e julgou cada um. Todos carregam um
porquê genuíno: por que transferência e estorno não contam como gasto; por que o
dia de fechamento decide o mês da fatura; por que a leitura da IA é descartada
inteira e não só marcada; por que o arquivo do banco é restrito a `0600` e por
que a falha ao restringi-lo não recusa a conexão; por que `/bin/sh` é chamado por
caminho absoluto. **Nenhuma marca sobre prosa meramente descritiva.**

## Achados fora do escopo

1. A lista de **diretivas de ferramenta** do portão ganhou `shellcheck` — uma
   palavra, na mesma classe das que já eram isentas, para duas ocorrências
   legítimas. A lista de **marcas de justificativa** ficou byte a byte igual: o
   portão não afrouxou.
2. Os arrays de configuração dos outros dois portões foram reformatados de
   várias linhas para uma. Conteúdo idêntico.
