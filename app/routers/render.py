from pathlib import Path

from fastapi.templating import Jinja2Templates

TEMPLATES_FOLDER = Path(__file__).resolve().parents[1] / "templates"

TEMPLATES = Jinja2Templates(directory=str(TEMPLATES_FOLDER))
