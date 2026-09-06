# Veredicto — 002-gastos-tres-eixos, fase 4 (primeira rodada)

VEREDICTO: REPROVADO

Portões: `pytest -q` → `238 passed`, exit 0; `gates_runner.sh` → limpo.
Lint não executável — o projeto não declara linter nem typechecker.

Os treze critérios de comportamento e de comando passaram, medidos por `curl`,
SQL direto e Chromium real: listagem casando com o banco (80 regras), gravação
de regra de descrição (`26 lançamentos reclassificados`), edição de `Eating out`
para `supérfluo` (`128`), as duas recusas com a mensagem que nomeia o valor e
nada gravado, remoção devolvendo os 128 ao resíduo, o bloco `Sem regra` antes da
lista com o maior valor no topo, nenhuma cor fora de `tokens.css`, 93 cifras
todas tabulares com `U+2212`, sem rolagem horizontal nas três larguras, foco
visível e movimento zerado sob `prefers-reduced-motion`. Os dois critérios de
integração também: o total `−R$ 103.772,33` idêntico nos cinco eixos, e a
mudança de regra movendo o eixo essencialidade **sem reiniciar processo** —
`importante` caiu `−R$ 4.360,13` e `supérfluo`, que não existia, passou a valer
exatamente o mesmo.

  [ ] `estrutural` RF-45 — capturas
      Quatro dos cinco arquivos exigidos não existem:
        regras-lista-375.png   AUSENTE
        regras-lista-768.png   AUSENTE
        regras-lista-1440.png  AUSENTE
        regras-erro-1440.png   AUSENTE
        regras-dark-1440.png   EXISTE
      Havia `regras-375.png`, `regras-768.png` e `regras-1440.png` — plausivelmente
      as três capturas de lista, salvas sem o segmento `-lista-`. E não havia,
      sob nome nenhum, a captura do estado de recusa, que é a única prova visual
      do comportamento que o próprio objetivo da fase nomeia.
