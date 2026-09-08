# Brief — 036-a-suite-nao-depende-do-diretorio-do-dono

**Trilha:** rápida · **Este documento funde discovery, PRD e spec.**

## Problema

`tests/test_sync.py` chama a sincronização **sem substituir a etapa de carga**.
Dois testes acabam lendo `data/processed/` e `data/raw/` — diretórios do dono, que
o `.gitignore` exclui de propósito.

O efeito é que o resultado desses testes depende de arquivos que o git não
versiona. **Numa worktree onde `data/raw/` não foi copiado, os dois falham com
violação de chave estrangeira** — e a mensagem que sobra,
`erro de escrita: IntegrityError`, não diz qual restrição nem qual linha, então o
defeito parece ser do código que está sendo julgado.

Isso aconteceu de verdade nesta corrida, e **dois julgadores diferentes** — um
validador cego e eu — atribuíram a falha a mudanças de código que não tinham nada
a ver. O primeiro acertou o diagnóstico por sorte de ter causado o acidente; o
segundo o descartou cedo demais.

E há o lado que ninguém olhou: a integração contínua roda **sem `data/` nenhum**.
Ou esses dois testes passam lá por outro caminho, ou eles nunca mediram o que
prometem. Um teste que só passa na máquina onde os dados do dono estão completos
não é portão, é coincidência.

## Escopo

A suíte passa numa árvore recém-clonada, sem nenhum arquivo do dono. E a mensagem
de erro de escrita da carga nomeia a restrição violada.

## Requisitos

- **RF-01.** Nenhum teste lê `data/` do dono. O que a carga precisa ler vem de
  dado de teste **versionado**, em `tests/`.
- **RF-02.** A suíte inteira passa com `data/` ausente por completo.
- **RF-03.** A mensagem de erro de escrita da carga nomeia a restrição violada,
  em vez de só o nome da classe da exceção.
- **RF-04.** Os dois testes continuam provando o que provavam — que uma falha
  depois da carga rebaixa a corrida em vez de declarar sucesso, e que o
  rebaixamento nomeia a própria linha.

## Riscos

- **Trocar o dado real por uma fixture que não exercita o mesmo caminho.** RF-04
  é o que mede: o veredicto dos dois testes não muda.
