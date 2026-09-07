# Decisões tomadas sem o humano — 013-objetivo-cenario-vazio-e-ponto-espurio

| # | Estágio | Decidido | Alternativa descartada | Por quê |
|---|---|---|---|---|
| D1 | discovery | Data recusada **não grava** e a tela diz que não gravou | Gravar assim mesmo; recusar a requisição com 400 | Gravar sujava a única medida de progresso do produto com um erro de digitação, sem como distinguir depois. Recusar com 400 derrubaria a tela por causa da URL, quando a resposta pela data de hoje é útil. Responder e avisar é o meio-termo que não mente. |
| D2 | discovery | A tela **nomeia a lista vazia** em vez de mudar o rótulo do cenário | Renomear o cenário `base` para algo que não prometa | O rótulo está certo e continuará certo assim que o dono marcar a primeira assinatura. O que faltava era dizer por que o número é zero **hoje**. |
| D3 | fase 1 | Ausência de `?data=` é **aceita**, não recusada | Deixar como estava | Foi regressão minha: `RF-02` mandava não gravar em data recusada, e `_reference(None)` caía no mesmo ramo. Os dois links do produto para a tela não levam parâmetro, então a linha do tempo — a única medida de progresso que este produto aceita — parou de crescer pela navegação normal. Achado pelo validador, fora da letra dos critérios. |
| D4 | fase 1 | O aviso **concorda em número** com a lista e só afirma a igualdade quando as duas listas estão vazias | Manter o texto fixo | `base` soma as duas alavancas e `conservador` não soma nenhuma: com uma só vazia, a frase "devolve o mesmo número" contradizia os dois números diferentes na tabela ao lado. |
