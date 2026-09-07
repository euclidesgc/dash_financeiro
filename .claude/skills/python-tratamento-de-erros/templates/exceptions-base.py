class DomainError(Exception):
    """Raiz da taxonomia de erros de negócio.

    Motivo: o serviço não conhece HTTP. Ele levanta um erro desta árvore e a
    fronteira traduz; sem a raiz, cada módulo inventaria a sua e a tradução
    viraria uma cadeia de `isinstance` que ninguém mantém.
    """

    code = "domain_error"
    message = "Domain rule violated."


class NotFoundError(DomainError):
    code = "not_found"
    message = "Resource not found."


class ConflictError(DomainError):
    code = "conflict"
    message = "Resource is in a conflicting state."
