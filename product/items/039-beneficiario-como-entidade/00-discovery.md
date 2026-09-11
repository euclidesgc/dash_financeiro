# Discovery — 039-beneficiario-como-entidade

**Item do roadmap:** `039-beneficiario-como-entidade` — o beneficiário é um
cadastro, com nome, razão social, nome fantasia, CPF ou CNPJ e ramo de
atividade, e não mais a descrição do extrato normalizada.

**Data:** 2026-09-10 · **Origem:** plano "Base financeira organizada", aprovado
pelo dono em 10/09/2026. · **Trilha declarada:** rápida

## O terreno

- Hoje o beneficiário é a **descrição normalizada** (`normalize_description`,
  `app/ingest/normalize.py:15-24`: minúsculas, sem acento, sem dígitos, sem
  data nem parcela). A base tem **805** deles. "IFOOD *RESTAURANTE X" vira
  `ifood restaurante x` e "iFood.com" vira `ifood com`: dois beneficiários.
- `transactions.payee` só é preenchido quando está vazio
  (`app/taxonomy/classify.py:100-107`): se a descrição muda — 5 das 94 compras
  parceladas mudam entre parcelas —, a chave antiga fica.
- `payee_names` (migração 011) guarda apelido do dono (`source='dono'`) e nome
  consultado (`'cnpj'`), com a chave no beneficiário, não no CNPJ. Está vazia na
  base do dono. O nome exibido segue `app/payees/names.py:62-76`.
- A consulta de CNPJ (`app/payees/lookup.py`) vai à BrasilAPI, síncrona, um
  beneficiário por clique em `/configuracao/cnpj`, e é **opt-in** por
  `DASH_CNPJ_LOOKUP` (RF-25a do `015`: o produto é local por definição). Hoje
  devolve só um nome: nome fantasia ou, na falta, razão social.
- Depois do `037` fase 1, cada lançamento traz `counterparty_name`,
  `counterparty_document` e `counterparty_kind` (CPF ou CNPJ), e continua
  trazendo `merchant_cnpj` (338 linhas). São cerca de 100 CNPJs distintos.
- O eixo "beneficiário" (`app/queries/axes.json`) agrupa pela chave crua;
  `app/queries/reach.py` e a `series_key` dos compromissos também usam `payee`.
- CPF não tem consulta pública.

## INVEST

| Critério | Passa | Observação |
|---|---|---|
| Independente | sim, em ordem | Consome o documento da contraparte que a fase 1 do `037` grava; ela vem antes na fila. |
| Negociável | sim | Fixo: documento identifica; fundir não muda total. Conversável: precedência do nome exibido. |
| Valioso | sim | O iFood vira um beneficiário com razão social, não cinco textos. |
| Estimável | sim | Duas fases. |
| Pequeno | sim | Fase 1 o cadastro; fase 2 o CNPJ automático. |
| Testável | sim | Exemplos com CNPJ real e contagens. |

**Veredicto do INVEST:** segue como está.

## História

Como dono, quero que cada beneficiário seja uma coisa só — o iFood é um, mesmo
com cinco descrições diferentes —, com razão social e nome fantasia, e poder
juntar e renomear o que o sistema não juntou sozinho, para ler meus gastos por
quem recebeu o dinheiro.

## Regras e exemplos

### R1 — O beneficiário é identificado pelo documento; sem documento, pela descrição normalizada

- **E1.1** — "IFD*IFOOD.COM" e "IFOOD *RESTAURANTE" com o mesmo CNPJ
  `14380200000121` caem no mesmo `beneficiary_id`.
- **E1.2** — Dois Pix enviados ao mesmo CPF, com descrições diferentes: um
  beneficiário só, do tipo CPF, com o nome que veio do `paymentData`.
- **E1.3** — "PADARIA SAO JOSE 12/03" e "PADARIA SAO JOSE", sem documento:
  chave de descrição `padaria sao jose`, um beneficiário.

### R2 — Fundir junta, e fundir nunca muda o total

- **E2.1** — Fundir `mercado livre pago` em `mercado livre`: o eixo
  beneficiário mostra uma linha com a soma dos dois; o total do eixo é igual
  antes e depois; um lançamento novo com a chave de `mercado livre pago` cai no
  beneficiário fundido.
- **E2.2** — Renomear o beneficiário fundido para "Mercado Livre" muda o rótulo
  em toda tela e não muda número nenhum.

### R3 — A chave de descrição acompanha a descrição quando ela muda

- **E3.1** — A parcela 2/10 volta da Pluggy com a descrição trocada de
  "MERCADOLIVRE*LOJA" para "MERCADO LIVRE LOJA" e sem documento: o `payee` é
  recalculado para a descrição nova, e a linha passa ao beneficiário dessa
  chave — nunca fica presa à chave antiga.

### R4 — O nome exibido tem uma precedência só

- **E4.1** — CNPJ `14380200000121`, sem nome do dono, `merchant.name` "iFood",
  nome fantasia vazio, razão social "IFOOD.COM AGENCIA DE RESTAURANTES ONLINE
  S.A.": exibe "iFood", com a razão social ao lado.
- **E4.2** — Mesmo beneficiário depois de o dono nomeá-lo "Delivery": exibe
  "Delivery". A ordem é nome do dono, `merchant.name`, nome fantasia, razão
  social, nome vindo do banco, descrição normalizada.

### R5 — O que o `015` gravou migra para o cadastro, e a tabela antiga sai

- **E5.1** — Base com `payee_names` (`mercado do bairro`, `dono`,
  "Mercadinho"): depois da migração o beneficiário da chave `mercado do bairro`
  exibe "Mercadinho", e `payee_names` não existe mais.

### R6 — A razão social e o nome fantasia chegam sozinhos, uma consulta por CNPJ

- **E6.1** — Com `DASH_CNPJ_LOOKUP` ligado e 100 CNPJs sem consulta: a
  sincronização consulta cada um uma vez, no ritmo de uma por segundo; a
  sincronização seguinte consulta zero.
- **E6.2** — Sem o opt-in: nenhuma chamada sai, e a tela diz que a consulta
  está desligada.
- **E6.3** — 429 na terceira consulta: o lote para, a falha fica registrada, a
  sincronização termina `ok`, e a próxima retoma pelos que faltam.
- **E6.4** — CNPJ que a BrasilAPI responde 404: fica registrado como não
  encontrado e não é consultado de novo sozinho.

### R7 — O eixo beneficiário soma por cadastro, não por texto

- **E7.1** — Em `/gastos`, eixo beneficiário, agosto de 2026: "iFood" aparece
  numa linha só, somando as variações do mesmo CNPJ; o total do eixo é igual ao
  dos outros eixos.

## Perguntas em aberto

Nenhuma.

## Trilha

**Trilha: rápida**

| Gatilho | Verdadeiro | Evidência |
|---|---|---|
| Zero perguntas em aberto | sim | Nenhuma. |
| Uma stack só | sim | Só a frente `api` (`.`, Python). |
| Sem mudança de contrato | sim | Não existe OpenAPI; as rotas são de `/configuracao`. |
| Sem dependência nova | sim | `httpx` já está declarado. |

O item guarda **CPF de terceiros** e chama **serviço externo** (BrasilAPI): o
`security-auditor` entra nas duas fases.

## Decisões autônomas

| Dúvida | Decisão | Alternativa descartada e por quê |
|---|---|---|
| O que identifica o beneficiário? | **Documento primeiro**, descrição normalizada na falta dele. | Só descrição mantém o iFood partido em cinco. |
| O cache da consulta é por quê? | **Por CNPJ.** | Por beneficiário consulta duas vezes o mesmo CNPJ antes de uma fusão. |
| `transactions.payee` sai? | **Não.** Continua como chave de reserva e como `series_key` dos compromissos. | Trocar a chave dos compromissos agora mexe no `003` sem pedido. |
| A consulta vira automática para todos? | **Continua opt-in** (RF-25a do `015`); liga-se no ambiente do dono ao fim da fase 2, porque ele pediu razão social e nome fantasia. | Ligar por padrão manda CNPJ para fora em toda instalação. |
| Como se junta o que o documento não junta? | **Fusão explícita** de chaves no cadastro. | Regra por expressão regular faz o dono escrever regex para dizer que dois nomes são a mesma empresa. |
