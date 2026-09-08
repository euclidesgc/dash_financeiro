# Veredicto — 034, fase 1, rodada 2 (O portão reconhece o que o projeto escreve)

**Veredicto:** APROVADO · **Validação cega** · **Data:** 08/09/2026

A rodada 1 foi **reprovada**, e com razão. O registro dela está abaixo, porque a
razão da reprovação é o que dá valor a este veredicto.

## Por que a rodada 1 caiu

O portão tinha ficado **permissivo demais** — o risco central declarado da fase,
realizando-se. Uma linha de comentário vazia não fechava o bloco justificado,
então **uma marca em qualquer ponto contaminava todos os parágrafos seguintes**:
cabeçalho decorativo de seção, nota de histórico e prosa sem marca nenhuma
passavam por herdar justificativa alheia. E a marca casava em qualquer lugar da
linha, então `# I have no idea why this works but for some reason: it does`
pagava o pedágio que a marca existe para cobrar.

O validador achou os dois construindo árvores que o teste do implementador não
cobria. **A contagem tinha caído de 1.129 para 910 — e parte da queda era
vazamento, não conserto.** Fechado o vazamento e ancorada a marca, ela subiu
para **979**, que é o número honesto.

## Portões

| Portão | Resultado |
|---|---|
| `scripts/lint.sh` | OK — `All checks passed!`, `182 files already formatted`, `Success: no issues found in 109 source files` |
| Suíte | OK — `749 passed`, saída `0` |
| `scripts/gates/gates_runner.sh` | OK — `gates: limpos (árvore completa, 659 arquivo(s) considerados)` |

## Critérios

**`comando` (RF-01).** `scripts/gates/__tests__/gate3.test.sh` → **9 de 9**,
saída `0`. O validador reproduziu cada afirmação com árvores próprias.

**`comando` (RF-02) — a janela do cabeçalho, nas bordas.** Um bloco que abre o
arquivo passa sem marca; o mesmo texto depois da primeira linha de código é
acusado. Testadas as bordas: shebang antes, licença antes, linha de comentário
vazia no meio do cabeçalho, linha só com `#` logo após o shebang, e arquivo que
começa com código — todas corretas.

**`comando` (RF-01, RF-02) — a contagem, com o efeito isolado.** **979**, contra
o teto de 1.129. E o validador separou o efeito da mudança do da deriva da
árvore: rodando o portão de `develop` sobre **esta mesma árvore**, 1.146. A
mudança derruba 1.146 → 979; os 17 de diferença entre 1.146 e os 1.129 do brief
são merges alheios a esta fase.

**`comando` (RF-05).** `749 passed`, mesmo número da base. Comentário não executa.

**`estrutural` (RF-04).** O recorte por diff **continua** em pé, como a fase 1
exige. Ele sai na fase 2.

## O portão foi visto vermelho, de duas formas

O validador quebrou o portão **duas vezes**, separadamente: tirando a âncora da
marca (o teste falhou em *marca no meio da frase não paga o pedágio*), e fazendo
a linha de comentário vazia não fechar o parágrafo (falhou em dois casos de
herança). Desfeitas as duas, árvore limpa e 9 de 9. Um teste que passa com o
portão quebrado não é teste.

## Achados fora do escopo — o escopo da fase 2

**979 linhas, 336 blocos**, em: `app` 550 linhas e 186 blocos; `scripts` 311 e
103; `tests` 118 e 47. `financas` e `ingestao`: **zero**.
