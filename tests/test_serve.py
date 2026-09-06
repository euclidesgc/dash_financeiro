from app import __main__ as entrypoint


def test_the_server_does_not_trust_forwarded_headers(monkeypatch):
    captured = {}
    monkeypatch.setattr(entrypoint, "create_app", lambda: object())
    monkeypatch.setattr(entrypoint.uvicorn, "run", lambda app, **kwargs: captured.update(kwargs))

    entrypoint.main()

    assert captured["proxy_headers"] is False
    assert captured["host"] == "127.0.0.1"
