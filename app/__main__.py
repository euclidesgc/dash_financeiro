import uvicorn

from app.main import create_app


def main() -> None:
    # Reason: Uvicorn trusts X-Forwarded-For coming from 127.0.0.1, and on a
    # loopback bind every client is 127.0.0.1 — the header would forge the
    # rate-limit key.
    uvicorn.run(create_app(), host="127.0.0.1", port=8000, proxy_headers=False)


if __name__ == "__main__":
    main()
