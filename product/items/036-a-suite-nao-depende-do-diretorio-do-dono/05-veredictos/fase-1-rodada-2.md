# Veredicto — 036, fase 1, rodada 2 (A suíte passa numa árvore sem os dados do dono)

**Veredicto:** APROVADO · **Validação cega** · **Data:** 08/09/2026

A rodada 1 foi **reprovada**. A razão dela é o que dá valor a este veredicto.

## Por que a rodada 1 caiu

Três testes em `tests/test_normalize.py` liam `data/processed/transacoes.json` do
dono e **se pulavam sozinhos** quando o arquivo faltava. No ambiente que este item
existe para cobrir — a integração contínua, sem `data/` nenhum — eles nunca
exercitavam a função que dizem provar, e a corrida saía verde assim mesmo. **Um
teste que se pula sozinho quando o dado falta não é um teste que passou.** O
implementador os deixara de fora de propósito, argumentando que eles se anunciam
como condicionais; o critério mede a suíte inteira, não os arquivos que a fase
tocou.

## Portões

| Portão | Resultado |
|---|---|
| Merge de `develop` | Limpo, sem conflito |
| `scripts/lint.sh` | OK — `All checks passed!`, `182 files already formatted`, `Success: no issues found in 109 source files` |
| Suíte | OK — `749 passed`, **zero pulados** |
| `scripts/gates/gates_runner.sh` | OK — `gates: limpos (árvore completa, 665 arquivo(s) considerados)` |

## Critérios

**`comportamental` (RF-01, RF-02) — o clone sem `data/`, que é o critério
central.** O validador clonou a worktree para um diretório temporário: `data/` nem
chega a existir num clone, porque é ignorado. Resultado: **749 coletados, 749
passados, zero pulados**, saída `0` — **idêntico à árvore completa**. E ele buscou
`pytest.mark.skipif` em `tests/`: **zero ocorrências**. O padrão que derrubou a
rodada anterior não existe mais.

**`comando` (RF-01).** O grep prescrito devolve três linhas: uma comparação de
string que não abre arquivo, e duas que apontam para `tests/data/` ou para um
temporário. Nenhuma alcança o `data/` da raiz.

**`comando` (RF-03) — a mensagem nomeia a restrição, e não vaza.** O validador
provocou a violação fora do pytest, com descrição e valor reconhecíveis:
`erro de escrita: IntegrityError: FOREIGN KEY constraint failed`. Nomeia a
restrição, e **não** carrega descrição, valor, identificador de conta nem caminho
de arquivo.

**`comando` (RF-04) — e a prova por mutação.** Os dois testes de rebaixamento
passam pela mesma função de carga de produção. O validador neutralizou o
rebaixamento para sempre devolver sucesso: **os dois falharam**
(`assert 'ok' == 'failed'`). Desfeita a mutação, árvore limpa.

## A prova que saiu da suíte não se perdeu

O teste que afirmava que o arquivo do dono tem 1.942 registros foi removido — é
fato sobre o dado, não sobre o código, e vivia atrás de um pulo silencioso. O que
ele provava mudou para `scripts/conferir-normalizacao.py`, que o validador rodou
contra o corpus real: **1.942 registros, zero divergências, zero normalizando
para nada**.

E a amostra que a suíte passou a usar é **sintética**, não extraída do corpus:
versionar descrições de transação do dono para provar uma função de texto trocaria
um problema por um pior.

## O achado que virou correção

O validador rodou `strace` e pegou o que a varredura tinha deixado passar: um
teste em `tests/test_cards.py` chamava a reconstrução da escada **sem** isolar o
diretório de contratos, e por isso abria os **financiamentos reais do dono** como
efeito colateral. Não quebrava critério nenhum — o teste só examina a tabela de
cartões, e a contagem não muda — mas é exatamente a classe que o item fecha.
Isolado como as outras quinze chamadas do mesmo arquivo já faziam.

O validador varreu as demais seis chamadas em cinco arquivos: todas já cobertas.

## Achados fora do escopo

Nenhum outro.
