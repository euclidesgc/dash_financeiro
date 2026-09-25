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
OVERDUE_CARRIED = "saldo em atraso levado para a fatura seguinte"


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


def test_an_overdue_balance_carried_to_the_next_bill_is_neither_income_nor_spending(
    bank_and_card_raw,
):
    rows = _consolidate_movements(
        bank_and_card_raw,
        [
            _movement("credit", "card", -2425.59, "Crédito de atraso", "Bank fees"),
            _movement(
                "carried", "card", 2425.59, "Saldo em atraso", "Late payment and overdraft costs"
            ),
            _movement("fine", "card", 48.70, "Multa de atraso", "Late payment and overdraft costs"),
        ],
    )

    assert [rows[key]["eh_transferencia"] for key in ("credit", "carried", "fine")] == [
        True,
        True,
        False,
    ]
    assert rows["carried"]["motivo_transferencia"] == OVERDUE_CARRIED


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


OWNER = "Maria Exemplo Teste"
OWN_TRANSFER = "transferência entre contas próprias"
BILL_PAYMENT = "pagamento de fatura"


@pytest.fixture()
def own_accounts_raw(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    accounts = [
        {"id": "bank", "name": "Conta", "type": "BANK", "owner": OWNER.upper()},
        {"id": "other", "name": "Outra conta", "type": "BANK", "owner": f"{OWNER} "},
        {"id": "card", "name": "Cartão", "type": "CREDIT", "owner": OWNER},
    ]
    (raw / "accounts_x_2026-09-22.json").write_text(
        json.dumps({"results": accounts}), encoding="utf-8"
    )
    return raw


def _on(day, movement):
    return {**movement, "date": f"2026-07-{day:02d}T15:00:00.000Z"}


def _pairing(rows, *keys):
    return [(rows[key]["eh_transferencia"], rows[key]["motivo_transferencia"]) for key in keys]


def test_a_card_purchase_never_pairs_with_a_pix_received_from_a_third_party(own_accounts_raw):
    rows = _consolidate_movements(
        own_accounts_raw,
        [
            _on(
                20,
                _movement(
                    "pix", "other", 100.0, "Transferência Recebida|FULANO DE TAL", "Transfers"
                ),
            ),
            _on(
                22,
                _movement(
                    "fuel", "card", 100.0, "POSTO DE GASOLINA VIAITABORAIBRA", "Gas stations"
                ),
            ),
        ],
    )

    assert _pairing(rows, "pix", "fuel") == [(False, ""), (False, "")]


def test_a_pix_to_a_shop_never_pairs_with_a_transfer_received_from_a_third_party(
    own_accounts_raw,
):
    rows = _consolidate_movements(
        own_accounts_raw,
        [
            _on(
                23,
                _movement(
                    "shop", "bank", -110.0, "Pix enviado ANIMAL SHOP", "Pet supplies and vet"
                ),
            ),
            _on(
                25,
                _movement(
                    "gift", "other", 110.0, "Transferência Recebida|Beltrana de Souza", "Transfers"
                ),
            ),
        ],
    )

    assert _pairing(rows, "shop", "gift") == [(False, ""), (False, "")]


def test_a_card_refund_never_pairs_with_a_bank_payment_to_a_third_party(own_accounts_raw):
    rows = _consolidate_movements(
        own_accounts_raw,
        [
            _on(10, _movement("pix", "bank", -89.9, "Pix enviado LOJA DE ROUPAS", "Shopping")),
            _on(11, _movement("refund", "card", -89.9, "REEMBOLSO LOJA ONLINE", "Shopping")),
        ],
    )

    assert _pairing(rows, "pix", "refund") == [(False, ""), (False, "")]


@pytest.mark.parametrize(
    ("sent", "received"),
    [
        (
            ("Pix enviado Maria Exemplo Teste", "Same person transfer"),
            ("Transferência Recebida|MARIA EXEMPLO TESTE", "Same person transfer"),
        ),
        (
            ("TED enviada MARIA EXEMPLO TESTE", "Same person transfer"),
            ("RECEBIMENTO TED", "Same person transfer"),
        ),
        (
            ("Transferência enviada|Maria Exemplo Teste", "Transfers"),
            ("Pix recebido Maria Exemplo Teste", "Transfer - PIX"),
        ),
    ],
)
def test_a_transfer_between_own_accounts_still_pairs(own_accounts_raw, sent, received):
    rows = _consolidate_movements(
        own_accounts_raw,
        [
            _on(10, _movement("out", "bank", -1945.78, *sent)),
            _on(11, _movement("in", "other", 1945.78, *received)),
        ],
    )

    assert _pairing(rows, "out", "in") == [(True, OWN_TRANSFER), (True, OWN_TRANSFER)]


@pytest.mark.parametrize(
    ("bank", "card"),
    [
        (
            ("Pagamento de boleto ITAU UNIBANCO HOLDING S.A.", "Transfer - Bank Slip"),
            ("Pagamento recebido", "Credit card payment"),
        ),
        (
            ("Pagamento de Pix QR Code MERCADO PAGO INSTITUICAO", "Services"),
            ("Pagamento recebido", "Credit card payment"),
        ),
        (
            ("Saída PGTO MIN PASSAI MC GOLD", "Loans and financing"),
            ("PAGAMENTO DEBITO MINIMO", "Transfers"),
        ),
        (
            ("Pagamento de fatura FATURA PAGA Itau Uniclas", "Credit card payment"),
            ("PAGAMENTO COM SALDO", "Transfers"),
        ),
    ],
)
def test_a_bill_payment_still_pairs_with_the_card_credit(own_accounts_raw, bank, card):
    rows = _consolidate_movements(
        own_accounts_raw,
        [
            _on(6, _movement("out", "bank", -3704.28, *bank)),
            _on(6, _movement("in", "card", -3704.28, *card)),
        ],
    )

    assert _pairing(rows, "out", "in") == [(True, BILL_PAYMENT), (True, BILL_PAYMENT)]


def test_a_card_credit_balance_returned_to_the_bank_still_pairs(own_accounts_raw):
    rows = _consolidate_movements(
        own_accounts_raw,
        [
            _on(
                3,
                _movement(
                    "back",
                    "card",
                    156.64,
                    "DEVOLUCAO SALDO CREDOR",
                    "Late payment and overdraft costs",
                ),
            ),
            _on(
                3, _movement("in", "bank", 156.64, "Entrada CREDITO CARTAO", "Credit card payment")
            ),
        ],
    )

    assert _pairing(rows, "back", "in") == [(True, OWN_TRANSFER), (True, OWN_TRANSFER)]


def test_cash_withdrawn_and_deposited_in_another_own_account_is_neither_spending_nor_income(
    own_accounts_raw,
):
    rows = _consolidate_movements(
        own_accounts_raw,
        [
            _on(
                6,
                _movement(
                    "atm",
                    "other",
                    -2000.0,
                    "SAQUE DINHEIRO ATM BIOMET",
                    "Same person transfer - CASH",
                ),
            ),
            _on(
                6,
                _movement(
                    "deposit", "bank", 2000.0, "Depósito DEP DIN ATM ENV 000044", "Transfer - Cash"
                ),
            ),
        ],
    )

    assert _pairing(rows, "atm", "deposit") == [(True, OWN_TRANSFER), (True, OWN_TRANSFER)]
    assert rows["atm"]["eh_saque"] is True


def test_a_debit_pairs_with_the_closest_credit_of_the_same_value(own_accounts_raw):
    rows = _consolidate_movements(
        own_accounts_raw,
        [
            _on(7, _movement("early", "other", 500.0, "PIX RECEBIDO", "Same person transfer")),
            _on(
                10,
                _movement(
                    "out", "bank", -500.0, "Pix enviado MARIA EXEMPLO TESTE", "Same person transfer"
                ),
            ),
            _on(10, _movement("same_day", "other", 500.0, "PIX RECEBIDO", "Same person transfer")),
        ],
    )

    assert rows["same_day"]["motivo_transferencia"] == OWN_TRANSFER
    assert rows["early"]["motivo_transferencia"] == (
        "transferência entre contas próprias (categoria Pluggy)"
    )


def _at(day, movement):
    return {**movement, "date": f"{day}T15:00:00.000Z"}


def _refund_links(rows, *keys):
    return [(rows[key]["eh_estorno"], rows[key]["estornada_por"]) for key in keys]


def test_a_card_refund_never_cancels_a_bill_payment_in_the_bank(own_accounts_raw):
    rows = _consolidate_movements(
        own_accounts_raw,
        [
            _at(
                "2025-10-26",
                _movement(
                    "boleto",
                    "bank",
                    -16.65,
                    "Pagamento de boleto INT PASSAI ITAU",
                    "Transfer - Bank Slip",
                ),
            ),
            _at(
                "2025-10-27",
                _movement("paid", "card", -16.65, "Pagamento recebido", "Credit card payment"),
            ),
            _at(
                "2025-10-30",
                _movement(
                    "refund",
                    "card",
                    -16.65,
                    "ESTORNO ANUIDADE DIFERENCIADA M RENOV",
                    "Late payment and overdraft costs",
                ),
            ),
        ],
    )

    assert _refund_links(rows, "boleto", "paid", "refund") == [
        (False, ""),
        (False, ""),
        (True, ""),
    ]


def test_a_card_refund_cancels_the_charge_of_its_own_card_not_a_later_bank_debit(
    own_accounts_raw,
):
    rows = _consolidate_movements(
        own_accounts_raw,
        [
            _at(
                "2025-10-06",
                _movement(
                    "annuity",
                    "card",
                    16.65,
                    "ANUIDADE DIFERENCI03/12",
                    "Late payment and overdraft costs",
                ),
            ),
            _at(
                "2025-10-26",
                _movement("pix", "bank", -16.65, "Pix enviado PADARIA DO BAIRRO", "Food"),
            ),
            _at(
                "2025-10-30",
                _movement(
                    "refund",
                    "card",
                    -16.65,
                    "ESTORNO ANUIDADE DIFERENCIADA M RENOV",
                    "Late payment and overdraft costs",
                ),
            ),
        ],
    )

    assert rows["annuity"]["estornada_por"] == "refund"
    assert rows["refund"]["estornada_por"] == "annuity"
    assert rows["pix"]["estornada_por"] == ""


def test_a_refund_prefers_the_debit_of_the_same_merchant_over_a_later_one(own_accounts_raw):
    rows = _consolidate_movements(
        own_accounts_raw,
        [
            _at("2026-01-08", _movement("bakery", "bank", -13.0, "Compra débito QUICOPAO", "Food")),
            _at(
                "2026-01-09",
                _movement("kiosk", "bank", -13.0, "Compra débito BANCA CENTRAL", "Food"),
            ),
            _at(
                "2026-01-09",
                _movement("refund", "bank", 13.0, "Estorno de compra débito QUICOPAO", "Food"),
            ),
        ],
    )

    assert rows["bakery"]["estornada_por"] == "refund"
    assert rows["kiosk"]["estornada_por"] == ""


def test_a_refund_never_cancels_a_transfer_in_its_own_account(own_accounts_raw):
    rows = _consolidate_movements(
        own_accounts_raw,
        [
            _at(
                "2026-01-05",
                _movement("purchase", "bank", -250.0, "Compra débito LOJA ONLINE", "Shopping"),
            ),
            _at(
                "2026-01-06",
                _movement(
                    "out", "bank", -250.0, "Pix enviado MARIA EXEMPLO TESTE", "Same person transfer"
                ),
            ),
            _at(
                "2026-01-06",
                _movement("in", "other", 250.0, "PIX RECEBIDO", "Same person transfer"),
            ),
            _at(
                "2026-01-07",
                _movement("refund", "bank", 250.0, "Estorno de compra", "Shopping"),
            ),
        ],
    )

    assert rows["purchase"]["estornada_por"] == "refund"
    assert rows["out"]["estornada_por"] == ""


@pytest.mark.parametrize(
    ("account", "charge", "refund"),
    [
        (
            "card",
            ("2025-11-06", 16.65, "ANUIDADE DIFERENCI04/12"),
            ("2025-11-29", -16.65, "ESTORNO ANUIDADE DIFERENCIADA M RENOV"),
        ),
        (
            "card",
            ("2026-01-28", 149.9, "Selfit - Varzea"),
            ("2026-01-30", -149.9, "Estorno de compra"),
        ),
        (
            "bank",
            ("2026-01-28", -481.37, "Compra débito A P M DA SILVA PIZZARI"),
            ("2026-01-28", 481.37, "Estorno de compra débito A P M DA SIL"),
        ),
        (
            "bank",
            ("2025-10-06", -2462.56, "DEBITO PRESTACAO HAB"),
            ("2025-10-08", 2462.56, "ESTORNO PRESTACAO HAB"),
        ),
    ],
)
def test_a_refund_still_cancels_the_charge_it_returns(own_accounts_raw, account, charge, refund):
    rows = _consolidate_movements(
        own_accounts_raw,
        [
            _at(charge[0], _movement("charge", account, charge[1], charge[2], "Shopping")),
            _at(refund[0], _movement("refund", account, refund[1], refund[2], "Shopping")),
        ],
    )

    assert _refund_links(rows, "charge", "refund") == [(False, "refund"), (True, "charge")]


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
