# Brief — 020-varredura-de-rota-que-nao-desce-em-subpasta

**Item:** `020-varredura-de-rota-que-nao-desce-em-subpasta` · **Trilha:** rápida

> Este documento funde PRD e spec. O que a trilha rápida corta é documentação,
> nunca verificação: critério tipado, reviewer de stack e validador cego valem igual.

## Problema

O item `016` deixou em pé um guarda em `tests/test_route_guard.py`: ele varre os
módulos de rota e reprova aquele que resolva a data de tela por conta própria, em vez
de passar pelo leitor único (`app/routers/reference.py`). É a rede que impede o sétimo
sítio de nascer com o mesmo defeito que os seis primeiros tinham.

A varredura é `glob("*.py")` sobre `app/routers/`. `glob` não desce em subpasta. Hoje
os 15 módulos de rota estão todos no nível de cima, então o guarda e o critério de
integração do `016` — que usa `grep -R`, e desce — concordam por coincidência, não por
construção.

No dia em que um subpacote nascer sob `app/routers/`, o guarda deixa de olhar para ele
e continua verde. **Guarda que cala é pior que guarda que não existe**: quem lê o verde
conclui que a norma está cumprida, e ninguém volta a olhar. É exatamente a combinação
que a norma 20 do projeto manda tratar como causa raiz.

O risco não é hipotético: os itens `024`, `025` e `027` deste roadmap acrescentam rotas,
e a forma por domínio é a que o pack `python` sugere por padrão.

## Escopo

O guarda de rota enxerga todo módulo de rota sob `app/routers/`, em qualquer
profundidade, e existe teste que falha se a varredura voltar a ser rasa.

## Não-escopo

- **Nenhum módulo de rota muda.** O item é a rede, não o que ela pega.
- **Nenhum subpacote é criado sob `app/routers/` para provar o guarda.** A prova é
  feita em diretório temporário, com módulos escritos pelo teste: criar um subpacote de
  produção só para satisfazer um teste é código que existe para o teste.
- **O critério de integração do `016` não muda.** Ele já desce; quem estava raso era o
  guarda.

## Requisitos

- **RF-01.** O guarda de rota enumera os módulos de `app/routers/` recursivamente, e
  alcança módulo em subpasta de qualquer profundidade.
- **RF-02.** Existe teste que exercita o guarda sobre uma árvore com módulo de rota
  **dentro de subpasta** que resolve a data por conta própria, e afirma que o guarda o
  acusa.
- **RF-03.** Existe teste que exercita o guarda sobre uma árvore com módulo de rota em
  subpasta que consome o leitor único, e afirma que o guarda o aceita — para que a rede
  não seja aprovada por acusar tudo.
- **RF-04.** O conjunto de módulos que o guarda enumera hoje não muda: os 15 módulos do
  nível de cima continuam sendo varridos, e nenhum arquivo que não é rota entra.
- **RF-05.** Cada módulo varrido é identificado pelo caminho relativo a `app/routers/`,
  não pelo nome do arquivo. Hoje a chave é `path.name`; com varredura recursiva, dois
  módulos de mesmo nome em subpacotes diferentes colapsariam numa chave só e um dos
  dois deixaria de ser medido — o mesmo silêncio que o item existe para fechar.

## Riscos

- **`rglob` alcança `__pycache__`.** Um `.pyc` não casa `*.py`, mas um diretório de
  cache com fonte copiada casaria. A enumeração exclui diretório de cache por nome.
