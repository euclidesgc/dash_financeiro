# Veredicto — 030, fase 1 (O aplicador recusa quem chega por baixo)

**Veredicto:** APROVADO · **Validação cega** · **Data:** 08/09/2026

O validador reproduziu cada garantia com árvores de migração temporárias que ele
mesmo construiu, chamando `apply_migrations` direto, **antes** de conferir que a
suíte do avaliado chega à mesma conclusão.

## Portões

| Portão | Resultado |
|---|---|
| `scripts/lint.sh` | OK — `All checks passed!`, `181 files already formatted`, `Success: no issues found in 109 source files` |
| Suíte | OK — `744 passed`, saída `0` |
| `scripts/gates/gates_runner.sh` | OK — `gates: limpos (árvore completa, 655 arquivo(s) considerados)` |

## Critérios

**`comando` (RF-01, RF-02) — e a prova que interessa foi além do critério.** O
validador montou uma base que já registrara `020` e pôs um arquivo `016` a
caminho: o aplicador levantou, `schema_migrations` ficou só com `020`, e a tabela
que a `016` criaria não existe. Depois fez o caso difícil — **lote misto**, com a
`016` inválida ao lado de duas pendentes válidas que ordenam acima do teto:
**nenhuma das três entrou**. Isso prova que a checagem varre o lote inteiro antes
de aplicar qualquer coisa, que é a diferença entre recusar e recusar pela metade.

**`comando` (RF-03).** `develop` tem 6 testes no arquivo; a branch tem 9, e o diff
só acrescenta três funções — nenhuma linha de teste existente removida ou
alterada. Suíte: 741 → 744, delta exato.

**`comportamental` (RF-03) — o risco central não se realizou.** Base nova aplica
as 16 migrações reais e imprime `migrations applied: 16`. E o validador foi além
do critério escrito, montando a **base parcialmente migrada** que o despacho
pediu: aplicadas as 5 primeiras à mão, o aplicador completou as 11 restantes sem
recusa. O falso positivo que travaria a subida do painel não existe.

**`estrutural` (RF-04).** `app/migrations/NUMBERING.md` registra que `016` e `017`
não existem, que a próxima é `019`, e o que o guarda faz.

**A mensagem.** Em português, nomeando as duas versões e a ação:
`migração 016 ordena abaixo da mais recente já aplicada (020); renumere o arquivo
para uma versão maior que 020`.

## O achado que virou correção

O validador notou que a comparação é **lexicográfica** — mesma convenção da
ordenação. Ela funciona enquanto todo nome mantiver três algarismos com zero à
esquerda; um arquivo `9_x.sql` quebraria **a ordenação e o guarda ao mesmo
tempo**, porque `"9"` ordena depois de `"015"`. Não era regressão desta fase: é o
pressuposto que a ordenação já carregava antes dela.

Corrigido junto, porque é a mesma classe de defeito que o item existe para fechar:
o aplicador passou a recusar na porta uma versão que não tenha exatamente três
algarismos, com mensagem que nomeia o arquivo e a forma esperada. Dois testes
novos — a forma estreita é recusada sem gravar nada, e a forma de três algarismos
que o projeto usa continua aplicando. Suíte de **744** para **746**.

## Achados fora do escopo

Nenhum outro.
