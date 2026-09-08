# Entrega — 023, fase 2: a árvore, e o rótulo numa casa só

## 1. O que foi implementado

Cada uma das 77 categorias que a fonte manda passou a pertencer a um dos doze
grupos do dono **por chave estrangeira**, e o nome em português passou a morar
junto da categoria em vez de numa lista paralela. Grupo e categoria deixaram de
ser dois campos lado a lado e viraram pai e filho — que é o que faz "onde eu
corto?" ter resposta.

A regra continua atribuindo grupo, natureza e essencialidade de uma vez, e um
teste cobra que toda regra que casa por categoria aponte para o grupo a que
aquela categoria pertence na árvore: se as duas verdades discordarem, o portão
acusa e nomeia cada divergência.

## 2. Critérios atendidos

Oito critérios da fase e três de integração, todos aprovados, com evidência
executada em `05-veredictos/fase-2-rodada-2.md`.

**A primeira rodada devolveu `CRITERIO_INVALIDO`**, e o registro dela está em
`05-veredictos/fase-2-rodada-1.md`. Nada tinha falhado: um critério meu afirmava
que uma busca de texto não devolve nada, e ele tinha sido escrito contra uma
árvore que já não existia quando a fase começou. O validador foi ao histórico do
git provar isso, e mostrou que o arquivo que ainda casava era a cópia congelada
de que os próprios critérios de integração desta fase dependem — apagar a chave
de lá para o critério passar teria adulterado a evidência. O critério foi
reescrito, o plano reaprovado, e a segunda rodada é de um validador novo, do
zero.

## 3. Como testar à mão

```bash
DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_taxonomy_tree.py tests/test_taxonomy_integration.py
```

Na tela, `/gastos` com o eixo de categoria mostra o nome em português com a chave
crua ao lado — `Financiamento imobiliário` e `Real estate financing` na mesma
linha.

## 4. Divergências

Nenhuma.

## 5. Raio de impacto

Uma migração, a semente, o classificador, a linha de rótulos dos dois routers que
a consomem, e os testes. A suíte foi de 557 para 566 testes na branch.

## 6. Validações de campo pendentes

- **A distribuição das 77 categorias pelos doze grupos é vocabulário do dono, e
  vale a leitura dele.** Cinco escolhas são julgamento e não fato: as duas regras
  por beneficiário que foram para `Pessoal`, as categorias genéricas de
  transferência que foram para `Financeiro` e não para `Não é gasto`, `Pet e
  veterinário` em `Saúde`, `Dependentes` com uma categoria só, e `Investimentos`
  em `Financeiro`. Nenhuma delas move um centavo. Como verificar: abrir `/regras`
  e ler a lista.

## 7. Pendências que viraram roadmap

- **A migração descarta o conteúdo anterior da tabela de categorias na subida**,
  em vez de migrá-lo. É dado derivado e a classificação seguinte o repõe, mas
  quem só rodar as migrações e abrir o painel vê a tabela vazia até classificar.
- **`seed_taxonomy` sozinha não deixa o banco coerente**: rodá-la isolada exige a
  classificação na sequência. Hoje a linha de comando sempre encadeia as duas.
- **`ingestao/pluggy_consolidate.py` tem a própria lista de categorias em
  português**, independente do vocabulário da semente, e fora do alcance da
  varredura de literais.
