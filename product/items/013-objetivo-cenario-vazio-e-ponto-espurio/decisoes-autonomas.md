# Decisões tomadas sem o humano — 013-objetivo-cenario-vazio-e-ponto-espurio

| # | Estágio | Decidido | Alternativa descartada | Por quê |
|---|---|---|---|---|
| D1 | discovery | Data recusada **não grava** e a tela diz que não gravou | Gravar assim mesmo; recusar a requisição com 400 | Gravar sujava a única medida de progresso do produto com um erro de digitação, sem como distinguir depois. Recusar com 400 derrubaria a tela por causa da URL, quando a resposta pela data de hoje é útil. Responder e avisar é o meio-termo que não mente. |
| D2 | discovery | A tela **nomeia a lista vazia** em vez de mudar o rótulo do cenário | Renomear o cenário `base` para algo que não prometa | O rótulo está certo e continuará certo assim que o dono marcar a primeira assinatura. O que faltava era dizer por que o número é zero **hoje**. |
