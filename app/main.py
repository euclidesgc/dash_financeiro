from fastapi import FastAPI

from app.migrate import run_migrations


def create_app() -> FastAPI:
    run_migrations()
    return FastAPI()
