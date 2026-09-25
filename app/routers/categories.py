from fastapi import APIRouter
from pydantic import BaseModel

from app.taxonomy.seed import pickable_categories

router = APIRouter(prefix="/api/categories")


class CategoryOut(BaseModel):
    key: str
    label: str


class CategoriesResponse(BaseModel):
    categories: list[CategoryOut]


@router.get("")
def categories() -> CategoriesResponse:
    return CategoriesResponse(
        categories=[CategoryOut(key=c.key, label=c.label) for c in pickable_categories()]
    )
