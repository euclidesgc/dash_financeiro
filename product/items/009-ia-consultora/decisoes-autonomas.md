# Decisões tomadas sem o humano — 009-ia-consultora

| # | Estágio | Decidido | Alternativa descartada | Por quê |
|---|---|---|---|---|
| D1 | discovery | O modelo é chamado por **HTTP direto** com `httpx`, sem SDK | `google-genai` no `pyproject.toml` | `httpx` já é dependência desde o `001`. Um SDK a mais para montar um JSON de duas chaves é dependência que não se paga, e a norma 15 diz que dependência não declarada não entra. |
| D2 | discovery | A ordem das perguntas é **fixa e declarada**, do que mais move a projeção | Ordenar por impacto calculado a cada leitura | Calcular o impacto de um fato que não se tem exigiria simular com um valor inventado — o oposto do que este item promete. A ordem está escrita, com o porquê de cada posição ao lado, e muda quando alguém decidir que muda. |
| D3 | discovery | A tela **mostra o contexto** que vai para o modelo | Mandar o contexto em silêncio | O dono precisa poder ver de onde veio cada número que ele lê. É também a defesa mais barata contra o modelo citar coisa que não está lá: o que ele pode dizer está à vista. |
| D4 | discovery | Indisponibilidade da IA é `200` com aviso, nunca `500` | Deixar o erro subir | A tela existe para mostrar número determinístico. Derrubar a página porque o modelo não respondeu seria deixar a parte confiável refém da parte que não é. |
| D5 | fase 1 | Os cinco apontamentos do veredicto viraram requisito (`RF-16` a `RF-19`) e foram corrigidos com teste, **sem rodada nova** | Uma segunda validação cega | Mesma régua do `005` e do `006`: uma validação por fase. O mais importante invertia a garantia central do item — a tela mostrava cinco das oito linhas que vão para o modelo, então um número que ele citasse legitimamente (caixa, cartão) não seria encontrado na tela e leria como invenção. |
