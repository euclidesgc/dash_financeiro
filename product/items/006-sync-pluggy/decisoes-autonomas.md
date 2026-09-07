# Decisões tomadas sem o humano — 006-sync-pluggy

| # | Estágio | Decidido | Alternativa descartada | Por quê |
|---|---|---|---|---|
| D1 | discovery | "Todo dia" é **comando agendável mais idade cobrada na tela**, não daemon | Um agendador dentro do processo | O painel roda em `127.0.0.1` e morre com a máquina. Um agendador interno prometeria o que o processo não controla, e falharia exatamente quando o computador ficou desligado — o caso em que o dado envelhece. Cobrar a idade na tela funciona qualquer que seja o motivo de o agendamento não ter rodado. |
| D2 | discovery | A coluna antiga vira **integridade**, e a de inserção nasce nula para o passado | Recalcular o histórico; zerar; apagar as linhas antigas | O número de inserções de uma execução passada não existe em lugar nenhum — inventá-lo seria pior que não tê-lo. Nulo é a resposta honesta, e a tela sabe ler nulo. |
| D3 | discovery | Sem credencial, a sincronização **não grava linha de falha** | Gravar `status='failed'` | Não houve execução para registrar. Uma linha de falha ali encheria o histórico de falhas que nunca aconteceram e faria a tela gritar por um problema de configuração, não de sincronização. |
| D4 | plan | O botão e o comando chamam **a mesma função** | Duplicar a lógica na rota | Sync que se comporta diferente pelo botão e pelo cron é o defeito que só aparece no dia em que importa. |
