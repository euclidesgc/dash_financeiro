VEREDICTO: APROVADO

Nenhum plano, brief, spec ou histórico foi enviado no despacho, e não abri nada em `product/items/026-evolucao-da-fatura-mes-a-mes/`.

## Portões

| Portão | Resultado |
|---|---|
| ruff check | **OK** — `All checks passed!`, EXIT=0 |
| ruff format --check | **OK** — `167 files already formatted`, EXIT=0 |
| mypy --strict src | **NÃO APLICÁVEL** — não há `src/`, `mypy` não está no ambiente nem declarado em lugar nenhum. Nada a medir, e nada omitido: não é portão inconclusivo, é portão inexistente nesta stack. |
| pytest | **OK** — `676 passed, 2 warnings in 59.56s`, EXIT=0. Não é o exit 5 de coleta vazia. |
| gates | **OK** — `✓ gates: limpos (árvore completa, 569 arquivo(s) considerados).`, EXIT=0. 569 > 0. |

## Critérios da fase

| # | Tipo | Resultado | Evidência |
|---|---|---|---|
| 1 | estrutural RF-06 | cumprido | O fragmento existe com a seção uma vez, sem manchete própria, e com a frase que nomeia o mês do pagamento. A tela o inclui; o router importa a curva e entrega a chave |
| 2 | estrutural RF-06 | cumprido | O fragmento de parcelamentos passa a ter duas aberturas e dois fechamentos, com as duas seções nomeadas presentes |
| 3 | comando RF-06 | cumprido | `20 classes conferidas`, EXIT=0 |
| 4 | comando RF-06 | cumprido | Nenhuma linha de folha de estilo no diff; e o diff imprime os cinco arquivos da fase, entre eles o fragmento novo — controle positivo satisfeito |
| 5 | comportamental RF-01/04/06 | cumprido | Harness próprio: a tela responde 200 e o recorte da fatura traz os dez literais, inclusive o mês de referência valendo zero e o total. O sinal de menos é o caractere tipográfico, confirmado por ponto de código |
| 6 | comportamental RF-03 | cumprido | Cartão sem os dois dias: premissa e as duas frases. Cartão só com fechamento: a frase do vencimento, e a do fechamento **ausente**. Cartão completo: **nenhuma** das duas. A premissa é declarada e não é declarada nos lugares certos |
| 7 | comportamental RF-05 | cumprido | Três blocos, cada um com a soma dos meses igual ao próprio restante, e o total da tela igual à soma dos três |
| 8 | comportamental RF-07 | cumprido | O cartão sem parcelamento vivo traz a frase do estado vazio e **nenhum** mês; o cartão com série traz quatro |
| 9 | estrutural RF-08 | cumprido | As cinco funções de teste preexistentes seguem definidas, com os sete literais que elas fixam |

## Critérios de integração

| # | Tipo | Resultado | Evidência |
|---|---|---|---|
| I-1 | comportamental RF-05/06/08 | cumprido | Base pelo carregador real, semeada, classificada e recomputada. Parcelamentos traz duas séries somando −289000; a fatura traz um cartão com 23 meses somando exatamente −264000 — e a diferença é o parcelamento fora de cartão, nomeado na tela |
| I-2 | comando | cumprido | `32 passed`, EXIT=0 lido do próprio pytest. O diff **não toca** nenhuma linha das fixtures preexistentes; duas novas entraram. Os dois testes nomeados afirmam a soma por bloco e o balanço de seções |

## Provas independentes

**Baseline correto.** A extração da ponta de `develop` acusou uma rota a menos no ramo, que na verdade nasceu em `develop` depois da ramificação. Refiz tudo contra o **merge-base**, que é o mesmo intervalo que o critério mede.

**Nenhum total existente mudou.** Rodei **cinco bases idênticas** nas duas árvores. Removendo a seção nova:

- assinaturas, caixa liberado, calendário e dispensadas: **byte a byte idênticas** em todos os cenários
- parcelamentos: idêntica após normalizar espaço em branco — a única diferença real é o `</section>` órfão que sumiu
- manchetes, caixa liberado e janela do calendário: todos os literais iguais
- todos os restantes de parcelamento iguais

**Soma por cartão contra soma dos meses, na mesma tela:** conferido nos dois cenários, e a diferença entre a fatura e a tabela de parcelamentos é exatamente o parcelamento fora de cartão, nomeado.

**HTML bem formado — o achado mais forte da fase.** No merge-base a página estava **desbalanceada** sempre que havia parcelamento: 4 aberturas para 5 fechamentos, e 5 para 6 na resposta de dispensar. Agora: **5/5** e **6/6**; no cenário vazio, 3/3 → 4/4. Artigo, tabela, div, principal, corpo de tabela e linha também batem. O comentário que marcava o defeito saiu junto.

**Nenhuma rota perdeu guarda.** Enumerei os routers e bati **35 rotas** sem sessão nas duas árvores: lista, status e destino **idênticos**.

## Instrumentos do implementer

Só o critério I-2, que por construção manda rodar a suíte do avaliado. Os outros dez e as seis provas independentes saíram de harness que escrevi do zero.

## Achados que não reprovam

1. **O ramo está seis commits atrás de `develop`**, incluindo dois do item 019 que trazem uma rota nova. Nenhum dos cinco arquivos tocados aqui foi tocado lá, então o merge não deve conflitar — mas a fase foi medida contra o merge-base, não contra a ponta.
2. **Comentário em português no código.** A norma 11 permite comentário de decisão, mas a 16 pede código em inglês, e o resto do arquivo comenta em inglês.
3. **Diferenças de espaço em branco no HTML gerado** fora da seção nova, deixadas pelos blocos de controle do template. Sem efeito semântico nem visual; anoto para que a comparação byte a byte não seja lida como idêntica sem ressalva.
