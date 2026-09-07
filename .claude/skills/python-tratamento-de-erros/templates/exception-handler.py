from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.exceptions import ConflictError, DomainError, NotFoundError
from src.posts.router import router as posts_router
from src.reports.router import router as reports_router

STATUS_BY_ERROR = {NotFoundError: 404, ConflictError: 409}


async def handle_domain_error(request: Request, exc: Exception) -> JSONResponse:
    """Única fronteira entre a taxonomia de domínio e o HTTP.

    Motivo: a mensagem que vai para o corpo é a da taxonomia, nunca `str(exc)`
    — o texto de uma exceção interna carrega nome de tabela e de coluna, e isso
    é desenho do banco entregue a quem chamou.
    """
    status = next(
        (code for tipo, code in STATUS_BY_ERROR.items() if isinstance(exc, tipo)),
        400,
    )
    message = exc.message if isinstance(exc, DomainError) else DomainError.message
    code = exc.code if isinstance(exc, DomainError) else DomainError.code
    return JSONResponse(status_code=status, content={"code": code, "detail": message})


def create_app() -> FastAPI:
    app = FastAPI(title="Example API")
    app.add_exception_handler(DomainError, handle_domain_error)
    app.include_router(posts_router)
    app.include_router(reports_router)
    return app


app = create_app()
