from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import Response

from .render import TEMPLATES

router = APIRouter()


@router.get("/")
def home(request: Request) -> Response:
    return TEMPLATES.TemplateResponse(request, "home.html", {"login": request.state.login})
