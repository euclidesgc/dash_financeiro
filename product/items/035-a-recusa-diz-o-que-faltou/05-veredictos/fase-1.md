# Veredicto — 035, fase 1 (Nenhuma recusa imprime um símbolo de código)

**Veredicto:** APROVADO · **Validação cega** · **Data:** 08/09/2026

O validador escreveu a própria sonda — cliente em memória, banco temporário — e
conferiu as tabelas linha a linha antes e depois. Só recorreu à suíte do avaliado
onde o critério manda executá-la.

## Portões

| Portão | Resultado |
|---|---|
| `scripts/lint.sh` | OK — `All checks passed!`, `182 files already formatted`, `Success: no issues found in 109 source files` |
| Suíte | OK — `749 passed`, saída `0` |
| `scripts/gates/gates_runner.sh` | OK — `gates: limpos (árvore completa, 657 arquivo(s) considerados)` |

O merge de `develop` para dentro do ramo, feito antes de comparar contagens, veio
**limpo, sem conflito**.

## Critérios

**`comando` (RF-01, RF-03).** `-k grupo` → `1 passed`. Prova independente do
validador: `POST /gastos/correcao` com grupo vazio devolve `400`, mensagem
`Grupo ausente: escolha um grupo existente ou digite um nome para criar um novo.`,
sem a cadeia `None`, e as tabelas `transactions` e `category_rules` ficam
inalteradas.

**`comando` (RF-02) — e o teste morde.** `-k recusa_sem_simbolo` → `2 passed`. O
validador reverteu a correção e rodou de novo: `1 failed`, com
`AssertionError: /gastos/correcao devolveu 'None' na resposta` — o teste falha e
**nomeia a rota**. Restaurou em seguida, árvore limpa.

**Cobertura da varredura, contada pelo validador.** 25 rotas de escrita no painel.
Fora ficam `/login` e `/logout`, de mensagem fixa, e três que **nunca recusam** —
`/comprometido/retomar`, `/configuracao/proposta/remover` e
`/configuracao/ia/esquecer` — confirmado lendo o código de cada uma. Sobram 20
capazes de recusar, e a varredura cobre **20 de 20**. Cobertura completa, não
parcial.

**A correção é da causa, não da formatação.** A validação passou a levantar
`MissingGroupError` **antes** da checagem genérica que formatava o valor recebido.
O validador provou a distinção chamando os dois caminhos: grupo inexistente
(`999999`) devolve `grupo inválido: 999999`; grupo ausente (`None`) devolve a
mensagem nova. Dois tipos de exceção, dois textos — a validação passou a saber a
diferença entre *termo inválido* e *termo ausente*.

**`comando` (RF-04).** Base do ramo: `741`. Commit da fase isolado: `744`. Depois
do merge: `749`. Nenhuma linha de teste pré-existente removida ou alterada.

**Norma 24** confirmada sem cookie: `GET /gastos` e `GET /` respondem `302` para
`/login`.

## Achados fora do escopo

1. `/comprometido/retomar` envolve a chamada num tratamento de exceção que a
   função chamada **nunca levanta**. Código morto, inofensivo, mas engana quem lê
   o roteador achando que a rota recusa.
2. `/configuracao/proposta/remover` e `/configuracao/ia/esquecer` não validam
   nada e sempre respondem sucesso. Registrado para explicar por que ficaram fora
   da contagem de cobertura.

## Nota de protocolo

O validador registrou que o despacho o mandou ler o plano inteiro, que contém as
seções de decisão e etapas — raciocínio de implementação que a validação cega não
deveria receber. Ele usou apenas o bloco de critérios como régua e apoiou todo
veredicto em execução própria. **O despacho é que estava largo demais**, e os
próximos apontam a seção de critérios, não o arquivo inteiro.
