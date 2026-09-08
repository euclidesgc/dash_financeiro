# Veredicto — 032, fase 1 (Vazio quer dizer "não mexi", e apagar é um gesto)

**Veredicto:** APROVADO · **Validação cega** · **Data:** 08/09/2026

O validador não confiou em código de resposta: para cada afirmação, leu a tabela
`cards` direto, campo por campo, com sua própria sonda.

## Portões

| Portão | Resultado |
|---|---|
| Merge de `develop` | Limpo, sem conflito |
| `scripts/lint.sh` | OK — `All checks passed!`, `182 files already formatted`, `Success: no issues found in 109 source files` |
| Suíte | OK — `763 passed`, saída `0` |
| `scripts/gates/gates_runner.sh` | OK — `gates: limpos (árvore completa, 664 arquivo(s) considerados)` |

## Critérios

**`comando` (RF-01, RF-05) — vazio deixou de apagar, nos quatro campos.**
`-k vazio` → `7 passed`. Prova independente: gravados limite, taxa, dia de
fechamento e dia de vencimento, o validador enviou **cada um** dos quatro em
branco, um de cada vez, e leu a tabela — os quatro valores permaneceram
idênticos, e os outros três ficaram intactos a cada rodada. Depois, um valor novo
continuou gravando.

**`comando` (RF-02) — o gesto apaga só o que nomeia.** `-k apagar` → `3 passed`.
Com os quatro campos preenchidos, o gesto sobre o dia de fechamento zerou **só**
ele; limite, taxa e vencimento seguiram intactos.

**`comportamental` (RF-03) — a resposta nomeia o que mudou.** Enviado só o dia de
fechamento entre quatro campos, a resposta traz `Dia do fechamento — valor
salvo: 20.` e **não** traz o `Salvo.` genérico. As outras duas: `em branco, valor
mantido` e `valor apagado`.

**`estrutural` (RF-04) — as duas telas concordam.** A da IA: *"Deixar em branco
não altera a chave guardada."* A de cartões: *"Deixar um campo em branco não
altera o valor guardado nele. Para apagar um valor, use o botão «Apagar» ao lado
do campo."* Nenhuma diz que branco apaga.

**`comando` (RF-05).** `763 passed`, contra `746` na base do ramo.

## O que confirma que o defeito era real

O validador comparou com `develop`: lá, o escritor gravava o valor
**incondicionalmente** — inclusive o nulo vindo de campo em branco. A fase
corrigiu perda de dado real, não uma suposição do plano.

E o escritor é **compartilhado**: `/dividas/taxa` chama o mesmo. O validador
confirmou que aquele caminho herdou a proteção — uma taxa enviada em branco por
lá também não apaga mais.

## Provas de norma

- **Norma 13.** `POST` direto com dia `99`, fora da faixa, recusado com `400` e
  mensagem em português, sem gravar. A validação não depende da tela.
- **Norma 24.** Sem cookie, `GET /configuracao` e `POST /configuracao/cartao`
  respondem `302` para `/login`, sem escrever.

## Achados fora do escopo

Nenhum defeito. O único outro chamador do escritor já está coberto.
