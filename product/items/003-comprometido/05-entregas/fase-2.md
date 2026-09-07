## 1. O que foi implementado

**Item:** `003-comprometido` · **Fase:** `2 — Tela de Comprometido`

`GET /comprometido` responde a pergunta que abre o mês: **quanto já está
prometido antes de qualquer escolha**. Total comprometido de **−R$ 12.802,64/mês**,
as **55 assinaturas** do maior valor médio para o menor — com meses seguidos,
última cobrança e a ação **"não uso mais"**, reversível —, os **6 parcelamentos**
em aberto com data de término, e o cronograma de caixa liberado: **R$ 374,82/mês**
voltam quando o último acabar, sendo R$ 141,06 já em 10/2026.

Duas frases que a tela diz com todas as letras, porque são a diferença entre
informar e mentir: **o valor é a média observada, não o contratado, e o dia é
previsão tirada do histórico**; e **"não uso mais" registra a decisão neste painel
e não cancela nada no fornecedor** — quem marca ainda vai ligar para a empresa.

Marcar as três assinaturas que o relatório de origem trata como canceláveis leva
a economia projetada a exatamente **R$ 1.099,63/mês**. Quem decide isso é o dono:
o código não classifica nada como supérfluo, do mesmo jeito que no item `002`.

Branch: `003-comprometido/fase-2-tela` · commits `3231478` e `5522c91`.
Reprovou na primeira rodada.

---

## 2. Critérios atendidos

Os treze critérios, por validador cego, com Chromium real. Veredicto em
[`05-veredictos/fase-2.md`](../05-veredictos/fase-2.md); o da primeira rodada em
[`fase-2-reprovada-1.md`](../05-veredictos/fase-2-reprovada-1.md).

Destaques da evidência: 55 assinaturas com ordenação não crescente e sem `NaN`;
35 marcadas `Sem cobrança recente`, número conferido contra o banco; 6
parcelamentos com `−R$ 127,27` mostrando `22` parcelas e `06/2028`; dispensar um
parcelamento é recusado com `400`, sem gravar nada; o estado vazio diz o que
aconteceu e oferece o caminho para Gastos; 80 cifras, todas tabulares, todas com
`U+2212` colado; nenhuma rolagem horizontal nas seis medições — carregando na
largura e redimensionando; foco visível e movimento zerado sob
`prefers-reduced-motion`.

---

## 3. Como testar à mão

1. `rm -f /tmp/dash-c.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-c.sqlite DASH_TODAY=2026-09-05 .venv/bin/python -m app.ingest`
2. Suba o app com o mesmo banco e faça login; abra `http://127.0.0.1:8000/comprometido?data=2026-09-05`.
3. **Esperado:** `−R$ 12.802,64` no total, 55 assinaturas, 6 parcelamentos e
   `R$ 374,82` no caixa liberado.
4. Marque "não uso mais" em `ANTHROPIC* CLAUDE`, `MYCON` e `TotalPass`.
5. **Esperado:** economia projetada em `R$ 1.099,63` e o total caindo para
   `−R$ 11.703,01`.

---

## 4. Divergências

nenhuma

Três diferenças de forma em relação à letra do plano, nenhuma de contrato:
`#caixa-liberado` virou seção **irmã** de `#parcelamentos` (era filha, e foi o que
reprovou a primeira rodada); a assinatura marcada **sai** da lista e vai para o
bloco de dispensadas, em vez de aparecer nas duas — duplicar a linha duplicaria a
cifra; e a frase sobre não cancelar no fornecedor aparece duas vezes, antes e
depois do clique.

---

## 5. Raio de impacto

**Confirmados** (lidos):

- `app/routers/commitments.py` — as três rotas: a tela, `dispensar` e `retomar`.
- `app/templates/comprometido.html` e os três fragmentos — seguem o padrão que a
  tela de Gastos estabeleceu.
- `app/commitments/**` — consumido, não alterado.
- `tests/test_comprometido_screen.py:66` — o helper `_rows` passou a varrer
  **todos** os `<tbody>` da seção. Era ele que deixava passar o defeito que
  reprovou a fase.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

- **O critério `RF-37` é instável entre máquinas.** O grep recursa em
  `app/commitments/` sem excluir `__pycache__`, e o GNU grep acusa que o `.pyc`
  casa o padrão — por coincidência de bytes, não por constante no código. Passa em
  checkout limpo, falha em árvore usada. A correção é `--exclude-dir=__pycache__`
  na próxima redação de critério; vale para todo critério de varredura do projeto.
- **Não se sai de `/comprometido` sem o botão voltar.** A tela não tem nenhum
  `<a href>`: o primeiro `Tab` já cai no botão "não uso mais". `/gastos` oferece
  caminho para `/regras`; esta não oferece nenhum. Entra como ajuste da navegação
  quando o item `004` montar o Resumo, que é a casa natural do menu.
