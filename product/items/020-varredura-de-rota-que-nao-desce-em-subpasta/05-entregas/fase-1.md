# Entrega — 020, fase 1: a varredura que desce, e o dente que prova

## 1. O que foi implementado

O guarda que impede uma rota de resolver a data de tela por conta própria passou
a enxergar módulo de rota em subpasta de qualquer profundidade.

Antes ele varria `app/routers/` com `glob("*.py")`, que não desce, e guardava
cada módulo pelo **nome do arquivo**. Duas coisas saíam disso: um subpacote
nascido sob `app/routers/` ficava invisível ao guarda, que continuava verde; e,
no dia em que a varredura descesse, dois módulos de mesmo nome em subpacotes
diferentes colapsariam numa chave só — e qual dos dois sobreviveria dependeria
da ordem de leitura do disco.

Agora a enumeração é função com raiz (`_sources(root)`), recursiva, que exclui
diretório de cache por caminho relativo e chaveia cada módulo pelo caminho
relativo à raiz. O teste que provava o dente do guarda deixou de ser um
dicionário escrito à mão — que nunca passava pela enumeração e por isso não
provava a enumeração — e passou a ser quatro testes sobre árvore que o próprio
teste escreve em diretório temporário: subpasta acusada a um e a dois níveis,
subpasta aceita quando consome o leitor único, colisão de nome tratada como duas
medições, e cópia dentro de `__pycache__` ignorada.

**Correção do caso idêntico ao lado, autorizada no despacho:** `scan()` de
`tests/test_frozen_numbers.py` descia com `rglob` sobre `app/` sem excluir
`__pycache__`. Ganhou a mesma exclusão. É inofensiva hoje — o cache guarda
`.pyc` e a varredura procura `.py`, `.sql` e `.html` —, e é guarda defensiva
contra o mesmo silêncio.

## 2. Critérios atendidos

Nove critérios, todos aprovados pelo validador cego, com evidência executada em
`05-veredictos/fase-1.md`. Três estruturais (a expressão `.rglob("*.py")`
presente, `.glob("*.py")` ausente, `relative_to` presente; o conjunto exato de
funções de teste; nenhum subpacote de produção sob `app/routers/`), cinco
comportamentais sobre árvore temporária e sobre a árvore real, e um de comando.

O validador não julgou os comportamentais pelas asserções do implementer:
escreveu as próprias árvores e chamou a enumeração diretamente. E provou por
mutação que a recursão é o que sustenta o teste — trocando `.rglob` por `.glob`
numa cópia, a acusação esvazia e a asserção cai.

## 3. Como testar à mão

```bash
DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_route_guard.py
```

Oito testes: dois de guarda de sessão, seis de varredura. Para ver o guarda
morder, crie `app/routers/cartoes/tela.py` com `date.today()` dentro e rode de
novo: o teste falha nomeando `cartoes/tela.py`. Antes desta fase, passava.

## 4. Divergências

Nenhuma. Todos os critérios bateram com o medido.

## 5. Raio de impacto

Dois arquivos, ambos de teste: `tests/test_route_guard.py` (78 linhas mexidas) e
`tests/test_frozen_numbers.py` (2 linhas). **Nenhum arquivo de `app/`, de
`scripts/`, de `.harness/` ou de `.github/` mudou.** A suíte foi de 526 para 530
testes: seis novos de varredura entraram, dois saíram — o dente antigo, que não
passava pela enumeração, e o teste do dicionário literal.

## 6. Validações de campo pendentes

Nenhuma. A fase inteira é verificável por execução.

## 7. Pendências que viraram roadmap

- **O guarda reconhece uma só forma de perguntar as horas.** A varredura procura
  o literal `date.today()`. `datetime.now().date()`, `datetime.today()` e
  `from datetime import date as d` seguido de `d.today()` passam caladas. É a
  mesma família de silêncio que este item fecha, o brief não pede, e resolver
  aqui seria requisito nascido no plano. Vira item de dívida técnica no roadmap,
  logo depois deste.
