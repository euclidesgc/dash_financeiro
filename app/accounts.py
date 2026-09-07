# The account-type vocabulary of the source. It has one home because the sign
# normalisation at ingestion and every reader that groups by type have to agree
# on the same string, and agreeing by textual coincidence is how they stop
# agreeing (invariant 22).
BANK = "BANK"
CREDIT = "CREDIT"
