# Decision: the single home for ceilings (RF-03). Every owner that used to
# write its own number now imports from here, and every text field with no
# ceiling gets one here.

# Reason: past three hundred digits float() returns inf, and round(inf)
# raises — a 500 on a money field. Twelve digits is already more money than
# this panel will ever need to add up.
MAX_DIGITS = 12

# Reason: the largest amount parse_money reads, R$ 9.999.999.999,99. An
# amount that arrives as a number, and not as typed text, is held to the
# same ceiling.
MAX_CENTS = 10**MAX_DIGITS - 1

# Reason: a name typed by hand on a credit offer; the offers list on the
# configuration screen reads comfortably up to this length.
NAME_MAX = 60

# Reason: a free-form question to the advisor; ceiling inherited from item
# 009, with no change in value.
MAX_QUESTION = 500

# Reason: a payee nickname replaces the trade name or legal name on the
# screen, and the longest legal name observed in this base has under fifty
# characters — the same order of magnitude as the offer name covers with
# room to spare.
PAYEE_ALIAS_MAX = 60

# Reason: a scenario name is a short label on a table row, not a
# description — forty characters fit a sentence like "Reduzir plano de
# saúde" with room to spare.
SCENARIO_NAME_MAX = 40

# Reason: a category name is a short label on a list row and in the
# category picker. The longest name in the catalogue today has 33
# characters ("Transferência própria em dinheiro"); forty is the ceiling of
# the scenario name and of the category group, labels of the same kind.
CATEGORY_LABEL_MAX = 40

# Reason: a rule expression is a hand-written regex, sometimes joining more
# than one payee name by alternation — two hundred characters cover several
# escaped names without leaving the column with no ceiling at all.
RULE_EXPRESSION_MAX = 200

# Reason: its own ceiling per debt kind, not the generic reader's hundred
# per cent a month. This base's real mortgage runs at 0.72% and the
# vehicle's CDC at 1.63% (docs/plano.md, 2026-09-05); twenty per cent a
# month on a mortgage is already loan-sharking, not a typo the reader
# should let through.
MORTGAGE_MAX_RATE_BP = 2000

# Reason: a vehicle CDC runs hotter than a mortgage on a bad credit
# contract, so its ceiling sits above it — and it is its own number, not
# the mortgage's.
VEHICLE_MAX_RATE_BP = 4000

# Reason: the generic rate reader's ceiling (a hundred per cent a month) —
# the largest of the project's three rate ceilings. Moved from
# app/settings/typed.py: RF-03 asks for a single home, and a ceiling that
# decides a refusal is no different for having been born before the module
# that gathers them.
MAX_RATE_BP = 10_000

# Reason: day of the month, for the card's closing and due date. Moved from
# app/cards/typed.py for the same reason as the rate ceiling above.
MIN_DAY = 1
MAX_DAY = 31

# Reason: maxlength counts typed characters, not digits. Money accepts a
# thousands separator and a decimal comma — the form the screen redisplays
# a stored value in, for example "999.999.999,99" — and the ceiling in
# characters needs to fit that whole form, without cutting off the last
# digit. In the worst case, with MAX_DIGITS digits split between the whole
# part and two decimal places, three thousand-separator dots and the comma
# come in: MAX_DIGITS plus four punctuation characters.
MONEY_FIELD_MAXLENGTH = MAX_DIGITS + 4

# Reason: a rate is written as "XX,YY" per cent a month. MAX_RATE_BP — the
# project's largest rate ceiling — is the longest form: the whole digits of
# a hundred per cent, the comma and two decimal places.
RATE_FIELD_MAXLENGTH = len(str(MAX_RATE_BP // 100)) + 3

# Reason: day of the month runs from 1 to 31 — at most the digits of
# MAX_DAY, with no punctuation.
DAY_FIELD_MAXLENGTH = len(str(MAX_DAY))

# Reason: validity is typed as YYYY-MM-DD — the only form
# app/plan/whatif.py accepts (VALID_DATE) — always ten characters.
VALIDITY_FIELD_MAXLENGTH = 10

# Reason: login, password and the API key have no ceiling on the server —
# Argon2id accepts a password of any length, the users table does not limit
# the login, and the AI key is only refused for an illegible character,
# never for length. The number here is only user experience (norm 13): it
# keeps the field from growing without end on the screen, and is not
# charged anywhere on the server — which is why the coherence test does not
# cover it.
CREDENTIAL_FIELD_MAXLENGTH = 128

# Reason: a category group name also has no ceiling on the server — it is
# born free while correcting an entry. Same order of magnitude as the
# scenario name, same note as the credential ceiling above: it is UX, not
# charged by the server.
CATEGORY_GROUP_MAXLENGTH = 40
