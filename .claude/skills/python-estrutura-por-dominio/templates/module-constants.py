from enum import StrEnum

TITLE_MAX_LENGTH = 200


class PostStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
