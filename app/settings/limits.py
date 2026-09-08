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
