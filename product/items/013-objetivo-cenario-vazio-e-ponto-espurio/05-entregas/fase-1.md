## 1. O que foi implementado

**Item:** `013-objetivo-cenario-vazio-e-ponto-espurio` · **Fase:** `1 de 1`

Duas coisas que o validador do `007` achou e que nenhum critério daquela fase
cobria.

**A tela nomeia a lista vazia.** O cenário `base` promete "as assinaturas
marcadas caem e a lista de corte é cortada" e entrega exatamente o número do
`nada muda`, porque nenhuma das duas listas tem uma linha. O número está certo e
a prosa parecia mentir; agora a tela diz qual lista está vazia, que não é que a
alavanca não renda — é que ainda não há o que contar — e por que isso faz `base`
igualar `conservador`.

**Erro de digitação na URL não é ponto de progresso.** Toda leitura de
`/objetivo` grava um ponto por cenário. Data fora da faixa caía em hoje e gravava
assim mesmo: um `?data=0001-01-01` injetava três linhas indistinguíveis depois de
uma leitura legítima, na única medida de progresso que este produto aceita.

Branch: `013-objetivo-lista-vazia/fase-1` · commits `2b654df` e `a007336`.

---

## 2. Critérios atendidos

Cinco critérios, **um validador cego**. Veredicto em
[`05-veredictos/fase-1.md`](../05-veredictos/fase-1.md).

**Ele achou uma regressão que esta própria fase introduziu**, fora da letra dos
critérios: `/objetivo` sem `?data=` — o caminho por onde o dono de fato entra na
tela — passou a exibir a recusa e a não gravar. A linha do tempo tinha parado de
crescer pela navegação normal. Nenhum critério pegaria: todos passam `?data=`.

---

## 3. Como testar à mão

1. Abra `/objetivo` **sem** parâmetro.
2. **Esperado:** `200`, sem aviso de recusa, e um ponto novo na série.
3. Abra `/objetivo?data=0001-01-01`.
4. **Esperado:** `200`, com "A data pedida não foi aceita… não gravou ponto".
5. Marque **uma** assinatura como "não uso mais" e volte.
6. **Esperado:** o aviso diz **Uma** alavanca, não Duas, e **não** afirma que
   base e conservador são iguais — porque não são mais.

---

## 4. Divergências

Nenhuma. Dois apontamentos corrigidos com teste depois do veredicto, um deles
regressão desta fase, nomeados no veredicto.

---

## 5. Raio de impacto

- `app/routers/plan.py` — `_reference` devolve também se a data foi aceita, e
  **ausência de parâmetro é aceita**; `empty_levers` e `base_equals_conservative`
  no contexto.
- `app/templates/objetivo.html` — o aviso da lista vazia, concordando em número,
  e o aviso da data recusada.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

Nenhuma.
