# Decisão: a casa única dos tetos (RF-03). Cada dono que antes escrevia o
# próprio número passa a importar daqui, e todo campo de texto sem teto ganha
# um aqui.

# Motivo: passar de trezentos algarismos faz float() devolver inf, e round(inf)
# levanta — um 500 num campo de dinheiro. Doze algarismos já é mais dinheiro do
# que este painel jamais vai precisar somar.
MAX_DIGITS = 12

# Motivo: nome digitado à mão numa proposta de crédito; a lista de propostas na
# tela de configuração lê confortavelmente até esse tamanho.
NAME_MAX = 60

# Motivo: pergunta livre ao consultor; teto herdado do item 009, sem mudança de
# valor.
MAX_QUESTION = 500

# Motivo: apelido de beneficiário substitui o nome fantasia ou a razão social
# na tela, e a maior razão social observada nesta base tem menos de cinquenta
# caracteres — a mesma ordem de grandeza do nome de proposta cobre com folga.
PAYEE_ALIAS_MAX = 60

# Motivo: nome de cenário é rótulo curto de uma linha de tabela, não uma
# descrição — quarenta caracteres cabem uma frase como "Reduzir plano de
# saúde" com sobra.
SCENARIO_NAME_MAX = 40

# Motivo: expressão de regra é um regex escrito à mão, às vezes juntando mais
# de um nome de beneficiário por alternância — duzentos caracteres cobrem
# vários nomes escapados sem deixar a coluna sem teto nenhum.
RULE_EXPRESSION_MAX = 200

# Motivo: teto próprio por tipo de dívida, não os cem por cento ao mês do leitor
# genérico. O imóvel real desta base corre a 0,72% e o CDC do veículo a 1,63%
# (docs/plano.md, 05/09/2026); vinte por cento ao mês num financiamento
# imobiliário já é agiotagem, não erro de digitação que o leitor deva deixar
# passar.
MORTGAGE_MAX_RATE_BP = 2000

# Motivo: o CDC de veículo corre mais quente que o imobiliário num contrato de
# crédito ruim, então o teto dele fica acima — e é número próprio, não o do
# imóvel.
VEHICLE_MAX_RATE_BP = 4000

# Motivo: o teto do leitor genérico de taxa (cem por cento ao mês) — o maior
# dos três tetos de taxa do projeto. Movido de app/settings/typed.py: RF-03
# pede uma casa só, e um teto que decide uma recusa não é diferente por ter
# nascido antes do módulo que os reúne.
MAX_RATE_BP = 10_000

# Motivo: dia do mês, para o fechamento e o vencimento do cartão. Movido de
# app/cards/typed.py pela mesma razão do teto de taxa acima.
MIN_DAY = 1
MAX_DAY = 31

# Motivo: maxlength conta caracteres digitados, não algarismos. Dinheiro
# aceita separador de milhar e vírgula decimal — a forma que a tela reexibe
# um valor já guardado, por exemplo "999.999.999,99" — e o teto em
# caracteres precisa caber essa forma inteira, sem cortar o último dígito.
# No pior caso, com MAX_DIGITS algarismos divididos entre a parte inteira e
# duas casas decimais, entram três pontos de milhar e a vírgula: MAX_DIGITS
# mais quatro caracteres de pontuação.
MONEY_FIELD_MAXLENGTH = MAX_DIGITS + 4

# Motivo: taxa é escrita como "XX,YY" por cento ao mês. MAX_RATE_BP — o
# maior teto de taxa do projeto — é a forma mais longa: os algarismos
# inteiros de cem por cento, a vírgula e duas casas decimais.
RATE_FIELD_MAXLENGTH = len(str(MAX_RATE_BP // 100)) + 3

# Motivo: dia do mês vai de 1 a 31 — no máximo os algarismos de MAX_DAY, sem
# pontuação.
DAY_FIELD_MAXLENGTH = len(str(MAX_DAY))

# Motivo: validade é digitada em AAAA-MM-DD — a única forma que
# app/plan/whatif.py aceita (VALID_DATE) — sempre dez caracteres.
VALIDITY_FIELD_MAXLENGTH = 10

# Motivo: login, senha e a chave da API não têm teto no servidor — Argon2id
# aceita senha de qualquer tamanho, a tabela users não limita o login, e a
# chave da IA só é recusada por caractere ilegível, nunca por tamanho. O
# número aqui é só experiência de uso (norma 13): impede o campo de crescer
# sem fim na tela, e não é cobrado em lugar nenhum do servidor — por isso o
# teste de coerência não o cobre.
CREDENTIAL_FIELD_MAXLENGTH = 128

# Motivo: nome de grupo de categoria também não tem teto no servidor — nasce
# livre na correção de um lançamento. Mesma ordem de grandeza do nome de
# cenário, mesma nota do teto de credencial acima: é UX, não é cobrado pelo
# servidor.
CATEGORY_GROUP_MAXLENGTH = 40
