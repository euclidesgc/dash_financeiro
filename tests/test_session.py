import time

from itsdangerous import TimestampSigner

from app.auth.session import MAX_AGE_SECONDS, issue_cookie, read_cookie

SECRET = "chave-do-servidor"


def test_round_trip_returns_the_login():
    assert read_cookie(issue_cookie("teste", secret=SECRET), secret=SECRET) == "teste"


def test_cookie_signed_with_another_key_is_refused():
    stranger = TimestampSigner("outra-chave").sign(b"teste").decode()

    assert read_cookie(stranger, secret=SECRET) is None


def test_tampered_cookie_is_refused():
    assert read_cookie("teste.nao-e-assinatura", secret=SECRET) is None


def test_cookie_inside_the_twelve_hour_window_is_accepted():
    now = time.time()
    raw = issue_cookie("teste", secret=SECRET, now=now - MAX_AGE_SECONDS + 60)

    assert read_cookie(raw, secret=SECRET, now=now) == "teste"


def test_cookie_past_the_twelve_hour_window_is_refused():
    now = time.time()
    raw = issue_cookie("teste", secret=SECRET, now=now - MAX_AGE_SECONDS - 60)

    assert read_cookie(raw, secret=SECRET, now=now) is None


def test_the_cookie_carries_the_epoch_it_was_issued_with():
    raw = issue_cookie("teste", secret=SECRET, epoch=3)

    assert read_cookie(raw, secret=SECRET, epoch=3) == "teste"


def test_a_cookie_from_an_older_epoch_is_refused():
    raw = issue_cookie("teste", secret=SECRET, epoch=3)

    assert read_cookie(raw, secret=SECRET, epoch=4) is None


def test_a_cookie_without_an_epoch_is_refused():
    legacy = TimestampSigner(SECRET).sign(b"teste").decode()

    assert read_cookie(legacy, secret=SECRET) is None
