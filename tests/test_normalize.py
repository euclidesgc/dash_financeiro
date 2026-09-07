import json
from pathlib import Path

import pytest

from app.ingest.normalize import normalize_description

SOURCE = Path(__file__).resolve().parents[1] / "data" / "processed" / "transacoes.json"
RECORDS = 1942

# data/ is not versioned, so the record by record comparison with the
# consolidator only runs where the source of 05/09/2026 is on disk.
requires_source = pytest.mark.skipif(not SOURCE.exists(), reason=f"missing {SOURCE}")


@pytest.fixture(scope="module")
def records():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


@requires_source
def test_the_source_still_holds_every_measured_record(records):
    assert len(records) == RECORDS


@requires_source
def test_every_source_record_normalizes_to_the_key_the_consolidator_wrote(records):
    mismatched = [
        (record["id"], record["descricao"], record["chave"])
        for record in records
        if normalize_description(record["descricao"]) != record["chave"]
    ]
    assert mismatched == []


@requires_source
def test_no_source_record_normalizes_to_nothing(records):
    assert [
        record["id"] for record in records if not normalize_description(record["descricao"])
    ] == []


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, ""),
        ("", ""),
        ("   ", ""),
        ("PIX Cristina", "pix cristina"),
        ("Transferência enviada|JOÃO", "transferencia enviada joao"),
        ("MERCADO 12/03/2026", "mercado"),
        ("MERCADO 12/03", "mercado"),
        ("LOJA 3/10", "loja"),
        ("LOJA 3 de 10", "loja"),
        ("R$ 1.234,56 TARIFA", "r tarifa"),
        ("  duplo   espaco  ", "duplo espaco"),
    ],
)
def test_the_normalization_strips_accent_date_installment_and_punctuation(raw, expected):
    assert normalize_description(raw) == expected
