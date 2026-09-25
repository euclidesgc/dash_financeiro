from typing import Annotated

from fastapi import Path

from app.db import SQLITE_INTEGER_MAX, SQLITE_INTEGER_MIN

RowId = Annotated[int, Path(ge=SQLITE_INTEGER_MIN, le=SQLITE_INTEGER_MAX)]
