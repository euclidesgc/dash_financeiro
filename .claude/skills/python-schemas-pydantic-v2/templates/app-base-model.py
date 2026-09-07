from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_serializer


class AppBaseModel(BaseModel):
    """Base compartilhada por todo schema da aplicação.

    Centraliza serialização e formato de data num lugar só: sem ela, cada
    módulo decide o seu, e a mesma data sai em dois formatos na mesma resposta.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    @field_serializer("*", when_used="json", check_fields=False)
    def serialize_datetimes(self, value: object) -> object:
        if isinstance(value, datetime):
            return value.astimezone(UTC).isoformat()
        return value
