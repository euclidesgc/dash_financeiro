from app.commitments.series import installment_series, recurring_series
from app.taxonomy import classify
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, narrowed, transaction


def prepare(conn, seed, rows):
    load(conn, rows)
    seed_taxonomy(conn, narrowed(seed, []))
    classify.classify_all(conn)
    conn.commit()
    return conn


def steady(prefix, months, *, value=-50.00, day="10", description="Assinatura X"):
    return [
        transaction(f"{prefix}-{month}", f"{month}-{day}", value, descricao=description)
        for month in months
    ]


def keys(rows):
    return {row["series_key"] for row in rows}


def test_three_consecutive_months_of_a_steady_value_are_a_recurring_series(taxonomy_conn, seed):
    conn = prepare(taxonomy_conn, seed, steady("a", ["2026-01", "2026-02", "2026-03"]))
    detected = recurring_series(conn)
    assert len(detected) == 1
    assert detected[0]["series_key"] == "assinatura x"
    assert detected[0]["amount_cents"] == -5000
    assert detected[0]["months_observed"] == 3
    assert detected[0]["months_consecutive"] == 3
    assert detected[0]["last_seen_date"] == "2026-03-10"
    assert detected[0]["due_day"] == 10


def test_two_months_are_not_enough(taxonomy_conn, seed):
    conn = prepare(taxonomy_conn, seed, steady("a", ["2026-01", "2026-02"]))
    assert recurring_series(conn) == []


def test_three_months_that_are_not_consecutive_are_not_a_series(taxonomy_conn, seed):
    conn = prepare(taxonomy_conn, seed, steady("a", ["2026-01", "2026-03", "2026-05"]))
    assert recurring_series(conn) == []


def test_a_value_that_swings_beyond_the_deviation_is_not_a_series(taxonomy_conn, seed):
    rows = [
        transaction("a-1", "2026-01-10", -10.00, descricao="Errática"),
        transaction("a-2", "2026-02-10", -50.00, descricao="Errática"),
        transaction("a-3", "2026-03-10", -90.00, descricao="Errática"),
    ]
    conn = prepare(taxonomy_conn, seed, rows)
    assert recurring_series(conn) == []


def test_a_value_that_swings_inside_the_deviation_is_a_series(taxonomy_conn, seed):
    rows = [
        transaction("a-1", "2026-01-10", -80.00, descricao="Quase fixa"),
        transaction("a-2", "2026-02-10", -100.00, descricao="Quase fixa"),
        transaction("a-3", "2026-03-10", -120.00, descricao="Quase fixa"),
    ]
    conn = prepare(taxonomy_conn, seed, rows)
    assert [row["amount_cents"] for row in recurring_series(conn)] == [-10000]


def test_transfers_refunds_and_income_produce_no_series(taxonomy_conn, seed):
    rows = [
        *steady("t", ["2026-01", "2026-02", "2026-03"], description="Entre contas"),
        *steady("r", ["2026-01", "2026-02", "2026-03"], description="Estornada"),
        *steady("i", ["2026-01", "2026-02", "2026-03"], value=50.00, description="Salário"),
    ]
    for row in rows:
        if row["id"].startswith("t-"):
            row["eh_transferencia"] = True
        if row["id"].startswith("r-"):
            row["estornada_por"] = "outra"
    conn = prepare(taxonomy_conn, seed, rows)
    assert recurring_series(conn) == []
    assert installment_series(conn) == []


def test_the_series_key_drops_the_installment_marker(taxonomy_conn, seed):
    rows = [
        transaction(
            "p-1",
            "2026-07-11",
            -127.27,
            descricao="OTICA BARDASSON E 9/10",
            parcela_atual=9,
            parcela_total=10,
        ),
        transaction(
            "p-2",
            "2026-08-11",
            -127.27,
            descricao="OTICA BARDASSON E 10/10",
            parcela_atual=10,
            parcela_total=10,
        ),
    ]
    conn = prepare(taxonomy_conn, seed, rows)
    detected = installment_series(conn)
    assert keys(detected) == {"otica bardasson e"}
    assert len(detected) == 1
    assert detected[0]["last_installment"] == 10
    assert detected[0]["installments_left"] == 0
    assert detected[0]["ends_month"] == "2026-08"


def test_two_purchases_at_the_same_store_are_two_series(taxonomy_conn, seed):
    rows = [
        transaction(
            "p-1",
            "2026-08-11",
            -127.27,
            descricao="MERCADOLIVRE*MERCADOLIVRE",
            parcela_atual=2,
            parcela_total=24,
        ),
        transaction(
            "p-2",
            "2026-08-11",
            -37.77,
            descricao="MERCADOLIVRE*MERCADOLIVRE",
            parcela_atual=2,
            parcela_total=18,
        ),
    ]
    conn = prepare(taxonomy_conn, seed, rows)
    detected = installment_series(conn)
    assert len(detected) == 2
    assert keys(detected) == {"mercadolivre mercadolivre"}
    by_total = {row["installment_total"]: row for row in detected}
    assert by_total[24]["installments_left"] == 22
    assert by_total[24]["ends_month"] == "2028-06"
    assert by_total[18]["installments_left"] == 16


def test_the_marker_in_the_description_answers_when_the_columns_are_empty(taxonomy_conn, seed):
    rows = [transaction("p-1", "2026-01-26", -797.13, descricao="IPVA parcela 1 de 3 Detran")]
    conn = prepare(taxonomy_conn, seed, rows)
    detected = installment_series(conn)
    assert len(detected) == 1
    assert detected[0]["installment_total"] == 3
    assert detected[0]["last_installment"] == 1
    assert detected[0]["installments_left"] == 2
    assert detected[0]["ends_month"] == "2026-03"


def test_a_single_charge_without_a_marker_is_no_series_at_all(taxonomy_conn, seed):
    conn = prepare(taxonomy_conn, seed, [transaction("s-1", "2026-08-11", -30.00)])
    assert recurring_series(conn) == []
    assert installment_series(conn) == []


def instalments(prefix, months, values, *, total, description, day="08"):
    return [
        transaction(
            f"{prefix}-{month}",
            f"{month}-{day}",
            value,
            descricao=f"{description} {step}/{total}",
        )
        for step, (month, value) in enumerate(zip(months, values, strict=True), start=1)
    ]


SIX = ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]


def test_a_cent_of_rounding_does_not_split_one_purchase_in_two(taxonomy_conn, seed):
    values = [-136.47] + [-136.43] * 5
    conn = prepare(taxonomy_conn, seed, instalments("a", SIX, values, total=6, description="Loja"))
    detected = installment_series(conn)

    assert len(detected) == 1
    assert detected[0]["installment_total"] == 6
    assert detected[0]["last_installment"] == 6
    assert detected[0]["installments_left"] == 0
    assert detected[0]["amount_cents"] == -13643


def test_two_purchases_of_the_same_size_stay_apart_when_the_value_is_not_the_same(
    taxonomy_conn, seed
):
    months = [f"2026-{month:02d}" for month in range(1, 13)]
    cheap = instalments("c", months, [-27.07] * 12, total=12, description="Curso")
    dear = instalments("d", months, [-49.60] * 12, total=12, description="Curso")
    conn = prepare(taxonomy_conn, seed, cheap + dear)
    detected = installment_series(conn)

    assert len(detected) == 2
    assert sorted(row["amount_cents"] for row in detected) == [-4960, -2707]
