from src.exceptions import ConflictError, NotFoundError


class PostNotFoundError(NotFoundError):
    code = "post_not_found"
    message = "Post not found."


class PostAlreadyPublishedError(ConflictError):
    code = "post_already_published"
    message = "Post is already published."
