import re
import unicodedata

# Reason: the consolidator in ingestao/ writes this same form into the
# "chave" field of data/processed/transacoes.json, and that script lives
# outside the package, so it cannot be imported (norm 15). The two
# implementations are held together by tests/test_normalize.py, which
# compares them record by record.
_DATE = re.compile(r"\d{2}/\d{2}(/\d{2,4})?")
_INSTALLMENT = re.compile(r"(?<!\d)(\d{1,2})\s*(?:/|\s+de\s+)\s*(\d{1,2})(?!\d)")
_NOT_LETTER = re.compile(r"[^a-z\s]")
_SPACES = re.compile(r"\s+")


def normalize_description(text: str | None) -> str:
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    lowered = stripped.lower()
    without_dates = _DATE.sub(" ", lowered)
    without_installments = _INSTALLMENT.sub(" ", without_dates)
    letters = _NOT_LETTER.sub(" ", without_installments)
    return _SPACES.sub(" ", letters).strip()
