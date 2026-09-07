from fastapi import APIRouter, status

from src.posts.dependencies import PaginationDep, PostDep, ServiceDep
from src.posts.schemas import PostCreate, PostRead

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=list[PostRead])
async def list_posts(service: ServiceDep, pagination: PaginationDep) -> object:
    limit, offset = pagination
    return await service.list(limit=limit, offset=offset)


@router.post("", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_post(payload: PostCreate, service: ServiceDep) -> object:
    return await service.create(payload)


@router.get("/{post_id}", response_model=PostRead)
async def get_post(post: PostDep) -> object:
    return post


@router.post("/{post_id}/publish", response_model=PostRead)
async def publish_post(post: PostDep, service: ServiceDep) -> object:
    return await service.publish(post.id)
