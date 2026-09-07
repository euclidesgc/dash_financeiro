# Decisões tomadas sem o humano — 008-simulador-e-base-de-fatos

| # | Estágio | Decidido | Alternativa descartada | Por quê |
|---|---|---|---|---|
| D1 | discovery | O simulador **injeta** na simulação do `007` | Um motor próprio de simulação | Dois motores discordariam, e o dia em que discordassem seria o dia em que o dono precisa acreditar em um deles. `simulate` ganhou um parâmetro; nada mais. |
| D2 | discovery | "Nunca → data" e "data → nunca" devolvem **nulo**, não um número | Devolver a diferença contra o horizonte de 360 meses | Chamar isso de N dias seria inventar uma aritmética sem primeiro termo. A tela diz o que é: a diferença entre chegar e não chegar. |
| D3 | discovery | Fato tem **validade** | Guardar só nome e valor | Saldo de quitação cotado em setembro não é o de dezembro. Sem prazo, um fato velho vira premissa silenciosa — o oposto do que a base de fatos existe para resolver. |
| D4 | fase 1 | O código foi escrito **antes** do brief e do plano | Escrever os documentos primeiro | Mesmo desvio registrado em `D6` do item `007`, pela mesma razão — pressa da corrida —, e registrado pela mesma razão: o portão que importa é o validador cego, que não vê nem plano nem brief, mas o processo diz que o plano vem antes e ele não veio. |
| D5 | fase 1 | O veredicto voltou **REPROVADO** — as capturas foram parar em `product/items/004-simulador-e-projecao/`, um item que não existe | Nada a decidir: é erro | Segunda vez na corrida que o script de captura, derivado por `sed` de outro item, escreveu no diretório errado. O critério estrutural pegou, como devia. |
| D6 | fase 1 | Valor é lido **estritamente na forma brasileira**, e o resto é recusado | Aceitar ponto como decimal também | Aceitar as duas formas obriga a adivinhar o que `5.000` significa. Recusar e dizer a forma esperada é o único caminho que não erra em silêncio — e errar em silêncio aqui multiplicava por cem, com `200` e sem aviso. |
| D7 | fase 1 | **Prazo** e **valor único** passaram a entrar na conta | Removê-los do formulário | Campo que não muda nenhum dígito da resposta é campo que mente, e o roadmap pede os dois. Custam seis linhas no motor que o `007` já tinha. |
