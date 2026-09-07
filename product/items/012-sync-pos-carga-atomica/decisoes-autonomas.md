# Decisões tomadas sem o humano — 012-sync-pos-carga-atomica

| # | Estágio | Decidido | Alternativa descartada | Por quê |
|---|---|---|---|---|
| D1 | discovery | A linha já gravada é **rebaixada** para `failed` | Desfazer a carga inteira; gravar uma segunda linha | Desfazer perderia lançamentos que entraram corretamente, e a carga é idempotente — a próxima sincronização os reencontra. Uma segunda linha faria o histórico contar duas execuções onde houve uma. Rebaixar diz a verdade sobre a execução que aconteceu. |
| D2 | discovery | A mensagem da tela diz **o que ficou para trás**, não o nome da exceção | Repetir a mensagem técnica | Mesma régua do `006` e do `009`: o dono não pode agir sobre `RuntimeError`. Pode agir sobre "as telas mostram o estado anterior; sincronize de novo". |
| D3 | fase 1 | `IngestResult` passou a expor `run_id`, e o rebaixamento **nomeia a própria linha** | Deixar o `MAX(id)`, já que não há defeito vivo | O validador mediu que hoje não quebra e disse exatamente o que faltava para fechar: o id da linha gravada. Custou um campo e duas linhas. Deixar de fora seria manter uma suposição sem dono — "ninguém escreve em `sync_runs` entre o ingest e a falha" — dentro do item que existe para acabar com sucesso mentiroso. |
| D4 | fase 1 | **Nenhuma troca de branch enquanto um validador roda** | — | Troquei de branch no meio da validação e quebrei o ponteiro do despacho. O validador contornou exportando o ref e conferindo por hash, mas o erro foi meu, e um validador menos cuidadoso teria medido a árvore errada. |
