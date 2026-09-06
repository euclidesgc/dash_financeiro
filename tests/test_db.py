import os
import stat

from app.db import connect


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
