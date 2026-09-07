# Decisões tomadas sem o humano — 012-sync-pos-carga-atomica

| # | Estágio | Decidido | Alternativa descartada | Por quê |
|---|---|---|---|---|
| D1 | discovery | A linha já gravada é **rebaixada** para `failed` | Desfazer a carga inteira; gravar uma segunda linha | Desfazer perderia lançamentos que entraram corretamente, e a carga é idempotente — a próxima sincronização os reencontra. Uma segunda linha faria o histórico contar duas execuções onde houve uma. Rebaixar diz a verdade sobre a execução que aconteceu. |
| D2 | discovery | A mensagem da tela diz **o que ficou para trás**, não o nome da exceção | Repetir a mensagem técnica | Mesma régua do `006` e do `009`: o dono não pode agir sobre `RuntimeError`. Pode agir sobre "as telas mostram o estado anterior; sincronize de novo". |
