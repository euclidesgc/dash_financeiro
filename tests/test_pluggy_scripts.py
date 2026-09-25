import json

import pytest

from app.db import connect
from app.migrate import run_migrations
from app.queries.pluggy_connections import list_item_ids
from app.sync.connections import add_connection
from ingestao import pluggy_consolidate, pluggy_extract
from ingestao.pluggy_consolidate import NoRawAccountsError, consolidate, local_date
from ingestao.pluggy_extract import (
    MissingCredentialsError,
    itens_salvos,
    read_credentials,
    registrar_item,
)

SECRET = "segredo-do-arquivo"
FIRST = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
SECOND = "0b8e5f3a-1c2d-4e5f-8a9b-0c1d2e3f4a5b"


@pytest.fixture()
def clean_environment(monkeypatch):
    # Reason: load_dotenv writes straight into os.environ; setting before
    # deleting makes monkeypatch restore whatever the file put there.
    for name in ("PLUGGY_CLIENT_ID", "PLUGGY_CLIENT_SECRET", "DASH_ENV_FILE"):
        monkeypatch.setenv(name, "placeholder")
        monkeypatch.delenv(name)
    return monkeypatch


def test_the_credentials_come_from_the_file_named_by_dash_env_file(tmp_path, clean_environment):
    env_file = tmp_path / "outro.env"
    env_file.write_text(
        f"PLUGGY_CLIENT_ID=id-do-arquivo\nPLUGGY_CLIENT_SECRET={SECRET}\n", encoding="utf-8"
    )
    clean_environment.setenv("DASH_ENV_FILE", str(env_file))
    clean_environment.chdir(tmp_path)

    assert read_credentials() == ("id-do-arquivo", SECRET)


def test_a_variable_already_in_the_environment_wins_over_the_file(tmp_path, clean_environment):
    env_file = tmp_path / "outro.env"
    env_file.write_text(
        f"PLUGGY_CLIENT_ID=id-do-arquivo\nPLUGGY_CLIENT_SECRET={SECRET}\n", encoding="utf-8"
    )
    clean_environment.setenv("DASH_ENV_FILE", str(env_file))
    clean_environment.setenv("PLUGGY_CLIENT_ID", "id-do-processo")

    assert read_credentials() == ("id-do-processo", SECRET)


def test_a_missing_secret_names_the_variable_and_never_shows_a_value():
    with pytest.raises(MissingCredentialsError) as failure:
        read_credentials({"PLUGGY_CLIENT_ID": "id-presente"})

    assert "PLUGGY_CLIENT_SECRET" in str(failure.value)
    assert "id-presente" not in str(failure.value)


def test_the_command_turns_missing_credentials_into_an_exit(tmp_path, clean_environment):
    clean_environment.setenv("DASH_ENV_FILE", str(tmp_path / "inexistente.env"))
    clean_environment.setattr("sys.argv", ["pluggy_extract.py", "status", "--item", "x"])

    with pytest.raises(SystemExit, match="PLUGGY_CLIENT_ID"):
        pluggy_extract.main()


def test_consolidating_without_raw_accounts_raises_and_prints_nothing(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(NoRawAccountsError):
        consolidate()

    assert capsys.readouterr().out == ""
    assert not (tmp_path / "data" / "processed").exists()


def test_consolidating_returns_the_counts_and_prints_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    (raw / "accounts_x.json").write_text(
        json.dumps({"results": [{"id": "acc-1", "name": "Conta", "type": "BANK"}]}),
        encoding="utf-8",
    )
    (raw / "v2_transactions_acc-1_p1.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "id": "tx-1",
                        "accountId": "acc-1",
                        "date": "2026-09-20T00:00:00.000Z",
                        "amount": -10.0,
                        "description": "Padaria",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    summary = consolidate()

    assert summary["transacoes"] == 1
    assert capsys.readouterr().out == ""
    assert (tmp_path / "data" / "processed" / "transacoes.json").exists()


@pytest.mark.parametrize(
    ("instant", "expected"),
    [
        ("2026-04-01T02:59:00.000Z", "2026-03-31"),
        ("2026-09-01T01:25:35.091Z", "2026-08-31"),
        ("2026-11-06T03:00:00.000Z", "2026-11-06"),
        ("2026-08-04T03:43:04.000Z", "2026-08-04"),
    ],
)
def test_the_consolidated_date_is_the_day_in_sao_paulo_not_in_utc(
    tmp_path, monkeypatch, instant, expected
):
    monkeypatch.chdir(tmp_path)
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    (raw / "accounts_x.json").write_text(
        json.dumps({"results": [{"id": "acc-1", "name": "Conta", "type": "BANK"}]}),
        encoding="utf-8",
    )
    (raw / "v2_transactions_acc-1_p1.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "id": "tx-1",
                        "accountId": "acc-1",
                        "date": instant,
                        "amount": 2928.46,
                        "description": "Salário REMUNERACAO/SALARIO",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    consolidate()

    rows = json.loads(
        (tmp_path / "data" / "processed" / "transacoes.json").read_text(encoding="utf-8")
    )
    assert [row["data"] for row in rows] == [expected]


def _snapshot(raw, day, entries):
    (raw / f"v2_transactions_acc-1_{day}_p1.json").write_text(
        json.dumps({"results": entries}), encoding="utf-8"
    )


def _entry(identifier, instant, status, **extra):
    return {
        "id": identifier,
        "accountId": "acc-1",
        "date": instant,
        "amount": 99.99,
        "description": "PB *BETTERME BRPorto AlegreBRA",
        "status": status,
        **extra,
    }


@pytest.fixture()
def card_raw(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    (raw / "accounts_x_2026-09-05.json").write_text(
        json.dumps({"results": [{"id": "acc-1", "name": "Cartão", "type": "CREDIT"}]}),
        encoding="utf-8",
    )
    return raw


def _consolidated(raw, name="transacoes.json"):
    return json.loads((raw.parent / "processed" / name).read_text(encoding="utf-8"))


def test_the_consolidation_keeps_the_latest_copy_of_each_transaction(card_raw):
    old = _entry("tx-1", "2026-08-04T03:00:00.000Z", "PENDING")
    new = _entry(
        "tx-1",
        "2026-09-04T03:00:00.000Z",
        "POSTED",
        creditCardMetadata={"installmentNumber": 2, "totalInstallments": 3},
    )
    _snapshot(card_raw, "2026-09-05", [old])
    _snapshot(card_raw, "2026-09-22", [new])

    consolidate()

    [row] = _consolidated(card_raw)
    assert (row["data"], row["parcela_atual"]) == ("2026-09-04", 2)


def test_a_pending_purchase_the_latest_snapshot_no_longer_returns_is_discarded(card_raw):
    _snapshot(
        card_raw,
        "2026-09-05",
        [
            _entry("gone", "2026-08-30T04:15:44.000Z", "PENDING"),
            _entry("kept", "2026-08-02T15:00:00.000Z", "POSTED"),
        ],
    )
    _snapshot(card_raw, "2026-09-22", [_entry("other", "2026-09-20T15:00:00.000Z", "POSTED")])

    summary = consolidate()

    assert sorted(row["id"] for row in _consolidated(card_raw)) == ["kept", "other"]
    assert _consolidated(card_raw, "descartadas.json") == ["gone"]
    assert summary["descartadas"] == 1


def test_a_pending_purchase_with_no_newer_snapshot_is_kept(card_raw):
    _snapshot(card_raw, "2026-09-22", [_entry("tx-1", "2026-09-20T15:00:00.000Z", "PENDING")])

    consolidate()

    assert [row["id"] for row in _consolidated(card_raw)] == ["tx-1"]
    assert _consolidated(card_raw, "descartadas.json") == []


FINANCING_CREDIT = "crédito de financiamento (parcelamento de fatura ou empréstimo)"


@pytest.fixture()
def bank_and_card_raw(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    accounts = [
        {"id": "bank", "name": "Conta", "type": "BANK"},
        {"id": "card", "name": "Cartão", "type": "CREDIT"},
    ]
    (raw / "accounts_x_2026-09-22.json").write_text(
        json.dumps({"results": accounts}), encoding="utf-8"
    )
    return raw


def _movement(identifier, account, amount, description, category, **extra):
    return {
        "id": identifier,
        "accountId": account,
        "date": "2026-09-10T15:00:00.000Z",
        "amount": amount,
        "description": description,
        "category": category,
        "status": "POSTED",
        **extra,
    }


def _consolidate_movements(raw, movements):
    (raw / "v2_transactions_x_2026-09-22_p1.json").write_text(
        json.dumps({"results": movements}), encoding="utf-8"
    )
    consolidate()
    return {row["id"]: row for row in _consolidated(raw)}


@pytest.mark.parametrize(
    ("description", "category"),
    [
        ("CREDITO PARCELAM. TODAS FATURAS", "Shopping"),
        ("Crédito de parcelamento", "Transfers"),
        ("CREDITO PARCELAMENTO DA FATURA", "Credit card payment"),
    ],
)
def test_an_invoice_plan_credit_is_neither_income_nor_spending_whatever_its_wording(
    bank_and_card_raw, description, category
):
    rows = _consolidate_movements(
        bank_and_card_raw, [_movement("credit", "card", -8579.27, description, category)]
    )

    credit = rows["credit"]
    assert credit["valor"] == 8579.27
    assert (credit["eh_transferencia"], credit["motivo_transferencia"]) == (
        True,
        FINANCING_CREDIT,
    )


def test_a_payroll_loan_credit_is_not_income(bank_and_card_raw):
    rows = _consolidate_movements(
        bank_and_card_raw,
        [_movement("loan", "bank", 32000.0, "Entrada CREDITO CONSIGNADO", "Loans and financing")],
    )

    loan = rows["loan"]
    assert (loan["eh_transferencia"], loan["motivo_transferencia"]) == (True, FINANCING_CREDIT)


@pytest.mark.parametrize(
    ("description", "category", "installment"),
    [
        ("PARCELAM. TODAS FA01/04", "Shopping", None),
        ("PARCELAMEN FATURA 02/04", "Credit card payment", None),
        (
            "Parcelamento de Fatura",
            "Credit card payment",
            {"installmentNumber": 1, "totalInstallments": 3},
        ),
    ],
)
def test_an_invoice_plan_installment_is_spending_whatever_its_wording(
    bank_and_card_raw, description, category, installment
):
    extra = {"creditCardMetadata": installment} if installment else {}
    rows = _consolidate_movements(
        bank_and_card_raw,
        [_movement("installment", "card", 2348.27, description, category, **extra)],
    )

    row = rows["installment"]
    assert row["valor"] == -2348.27
    assert (row["eh_transferencia"], row["motivo_transferencia"]) == (False, "")


def test_an_invoice_plan_installment_never_pairs_with_a_credit_of_the_same_value(
    bank_and_card_raw,
):
    rows = _consolidate_movements(
        bank_and_card_raw,
        [
            _movement("installment", "card", 1505.10, "Parcelamento de Fatura", "Shopping"),
            _movement("pix", "bank", 1505.10, "PIX RECEBIDO", "Transfer - PIX"),
        ],
    )

    assert rows["installment"]["eh_transferencia"] is False


def test_the_down_payment_of_an_invoice_plan_stays_a_bill_payment(bank_and_card_raw):
    rows = _consolidate_movements(
        bank_and_card_raw,
        [
            _movement("out", "bank", -341.86, "Entrada de parcelamento cartão", "Shopping"),
            _movement("in", "card", -341.86, "pagamento parcelam. todas faturas", "Shopping"),
        ],
    )

    assert [(rows[key]["eh_transferencia"], rows[key]["valor"]) for key in ("out", "in")] == [
        (True, -341.86),
        (True, 341.86),
    ]
    assert rows["out"]["motivo_transferencia"] == "pagamento de fatura"


def test_a_missing_date_stays_empty_and_a_date_without_zone_is_already_local():
    assert local_date(None) == ""
    assert local_date("") == ""
    assert local_date("2026-03-31T23:59:00") == "2026-03-31"
    assert local_date("2026-03-31") == "2026-03-31"


def test_the_consolidation_command_still_exits_without_raw_accounts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit, match="accounts_"):
        pluggy_consolidate.main()


def test_the_saved_items_are_the_registered_connections_in_registration_order(taxonomy_conn):
    add_connection(taxonomy_conn, FIRST)
    add_connection(taxonomy_conn, SECOND)

    assert itens_salvos(taxonomy_conn) == [FIRST, SECOND]


def test_registering_an_item_adds_it_once_and_tolerates_a_repeat(taxonomy_conn):
    registrar_item(taxonomy_conn, FIRST)
    registrar_item(taxonomy_conn, FIRST)

    assert list_item_ids(taxonomy_conn) == [FIRST]


@pytest.fixture()
def database(tmp_path, monkeypatch):
    path = tmp_path / "dash.sqlite"
    monkeypatch.setenv("DASH_DB_PATH", str(path))
    return path


@pytest.fixture()
def queried(monkeypatch):
    items: list[str] = []
    monkeypatch.setattr(pluggy_extract, "autenticar", lambda: "chave-falsa")
    monkeypatch.setattr(
        pluggy_extract, "status_de_um", lambda api_key, item_id: items.append(item_id)
    )
    return items


def _status(monkeypatch, *arguments: str) -> None:
    monkeypatch.setattr("sys.argv", ["pluggy_extract.py", "status", *arguments])
    pluggy_extract.main()


def test_status_without_item_queries_every_registered_connection(database, queried, monkeypatch):
    run_migrations(str(database))
    conn = connect(str(database))
    try:
        add_connection(conn, FIRST)
        add_connection(conn, SECOND)
    finally:
        conn.close()

    _status(monkeypatch)

    assert queried == [FIRST, SECOND]


def test_status_without_item_and_without_connections_points_at_the_screen(
    database, queried, monkeypatch
):
    with pytest.raises(SystemExit) as stop:
        _status(monkeypatch)

    assert str(stop.value) == "Nenhuma conexão cadastrada. Cadastre em Conexões ou passe --item."
    assert queried == []


def test_status_with_item_queries_only_it_and_leaves_the_database_alone(
    database, queried, monkeypatch
):
    _status(monkeypatch, "--item", SECOND)

    assert queried == [SECOND]
    assert not database.exists()
