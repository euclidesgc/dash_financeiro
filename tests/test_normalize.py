import json
from pathlib import Path

import pytest

from app.ingest.normalize import normalize_description

SAMPLE = Path(__file__).resolve().parent / "data" / "normalize_sample.json"


@pytest.fixture(scope="module")
def records() -> list[dict[str, str]]:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_every_sample_record_normalizes_to_the_key_the_consolidator_wrote(records):
    mismatched = [
        (record["id"], record["descricao"], record["chave"])
        for record in records
        if normalize_description(record["descricao"]) != record["chave"]
    ]
    assert mismatched == []


def test_no_sample_record_normalizes_to_nothing(records):
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
