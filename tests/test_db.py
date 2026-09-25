import os
import stat

from app.db import connect, fold


def test_a_new_database_is_readable_only_by_its_owner(tmp_path):
    target = tmp_path / "dash.sqlite"

    conn = connect(str(target))
    conn.execute("CREATE TABLE t (a)")
    conn.commit()
    conn.close()

    assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_a_database_left_open_to_everyone_is_narrowed(tmp_path):
    target = tmp_path / "dash.sqlite"
    connect(str(target)).close()
    os.chmod(target, 0o644)

    connect(str(target)).close()

    assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_a_filesystem_that_refuses_chmod_still_connects(tmp_path, monkeypatch):
    def refuse(*args, **kwargs):
        raise PermissionError("read-only filesystem")

    monkeypatch.setattr(os, "chmod", refuse)

    conn = connect(str(tmp_path / "dash.sqlite"))

    assert conn.execute("SELECT 1").fetchone()[0] == 1
    conn.close()


def test_a_database_without_a_file_still_connects():
    conn = connect(":memory:")

    assert conn.execute("SELECT 1").fetchone()[0] == 1
    conn.close()


def test_fold_drops_accents_and_case_in_sql():
    conn = connect(":memory:")

    row = conn.execute("SELECT fold('Açougue São JORGE')").fetchone()

    assert row[0] == "acougue sao jorge"
    conn.close()


def test_fold_of_null_is_null():
    conn = connect(":memory:")

    row = conn.execute("SELECT fold(NULL)").fetchone()

    assert row[0] is None
    conn.close()


def test_fold_keeps_digits_and_punctuation():
    conn = connect(":memory:")

    row = conn.execute("SELECT fold('GASTO 42 10/12')").fetchone()

    assert row[0] == "gasto 42 10/12"
    conn.close()


def test_fold_is_available_on_a_second_connection_to_the_same_file(tmp_path):
    target = tmp_path / "dash.sqlite"
    connect(str(target)).close()

    conn = connect(str(target))
    row = conn.execute("SELECT fold('Ünico')").fetchone()

    assert row[0] == "unico"
    conn.close()


def test_fold_in_python_matches_the_sql_function():
    assert fold("Ação") == "acao"
    assert fold(None) is None
