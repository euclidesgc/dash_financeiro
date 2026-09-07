---
name: python-schemas-pydantic-v2
description: "Schemas de entrada e saída no Pydantic v2: modelo base do projeto, field_serializer no lugar de json_encoders, extra proibido, e o response_model que não duplica validação."
user-invocable: false
---

# Schemas de entrada e saída

## Quando esta skill vale

Vale ao declarar o que entra e o que sai de uma rota. Ela define a separação
entre entrada e saída, o modelo base comum e as formas da v2 que substituíram
as da v1.

Não vale para a tabela do banco, que é outro arquivo e outra skill
(`python-sqlalchemy-async-repository`).

## A regra

**Entrada e saída são classes distintas.** `PostCreate` não é `PostRead`, mesmo
quando hoje têm os mesmos campos.

**Todo schema herda do modelo base do projeto**, que centraliza serialização e
configuração:

```python
class AppBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
```

**A validação usa o que o Pydantic já tem** — `Field(min_length=...)`,
`EmailStr`, `AnyUrl`, `StrEnum` — em vez de `if` escrito à mão depois.

## As formas da v2 que substituíram as da v1

| v1 | v2 | Por quê |
|---|---|---|
| `class Config:` | `model_config = ConfigDict(...)` | classe interna saiu |
| `json_encoders` | `@field_serializer` ou `PlainSerializer` | removido da v2 |
| `.dict()` / `.json()` | `.model_dump()` / `.model_dump_json()` | renomeados |
| `orm_mode = True` | `from_attributes=True` | renomeado |
| `BaseSettings` no pydantic | pacote `pydantic-settings` | separado |

## Por quê

**Entrada e saída mudam por razões diferentes.** Quando são a mesma classe, um
campo novo de escrita aparece na leitura sem ninguém decidir isso — e o caminho
inverso é pior: um campo interno da saída vira campo aceito na entrada, e o
cliente passa a poder gravá-lo.

**`extra="forbid"` transforma erro de cliente em 422 em vez de silêncio.** Sem
ele, um cliente que envia `stauts` no lugar de `status` recebe 201 e um recurso
criado sem o campo — e descobre isso em produção, olhando dado errado.

**O modelo base existe porque data é o campo que mais diverge.** Sem um lugar
único para decidir o formato, cada módulo escolhe o seu, e a mesma resposta sai
com dois formatos de instante.

**Declarar `response_model` e devolver a mesma classe faz a validação
acontecer duas vezes.** A fonte primária registra isso como anti-padrão: ou a
rota devolve o objeto do ORM e o `response_model` o converte, ou ela devolve o
schema já pronto e não declara `response_model`.

## Exemplo

**Errado** — uma classe para tudo, e a forma da v1:

```python
class Post(BaseModel):
    class Config:
        orm_mode = True
        json_encoders = {datetime: lambda v: v.isoformat()}

    id: int | None = None
    title: str = Field(min_length=1, default=None)
    status: str
```

`json_encoders` não existe mais na v2 e é ignorado em silêncio. `Field(min_length=1,
default=None)` é uma contradição: o campo é obrigatório ou é opcional, não os
dois. E o `id` opcional na entrada permite que o cliente escolha o
identificador.

**Certo** — duas classes, e a restrição dizendo uma coisa só:

```python
class PostCreate(AppBaseModel):
    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    body: str = Field(min_length=1)


class PostRead(AppBaseModel):
    id: int
    title: str
    body: str
    status: PostStatus
    created_at: datetime
    published_at: datetime | None
```

E a serialização de data mora no modelo base, uma vez:

```python
@field_serializer("*", when_used="json", check_fields=False)
def serialize_datetimes(self, value: object) -> object:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return value
```

## `ValueError` em validador vaza detalhe interno

Um `ValueError` levantado dentro de um validador do Pydantic chega ao cliente
como erro de validação **com a mensagem inteira**. Quando essa mensagem cita
nome de tabela, regra interna ou identificador de outro usuário, o vazamento é
para qualquer um que saiba mandar um corpo inválido. Regra de negócio se
verifica no serviço, com a taxonomia de domínio — veja a skill
`python-tratamento-de-erros`.

## Erros comuns

- **`response_model` e retorno da mesma classe.** Validação duplicada, e o
  custo aparece sob carga.
- **Reaproveitar o schema de saída como entrada de atualização.** Campos
  calculados viram campos graváveis.
- **`Optional[str]` em vez de `str | None`.** A versão-alvo já tem a forma
  nova, e o ruff a cobra com `UP007`.
- **Validador escrito à mão para o que `Field` já faz.** Mais código para
  manter e mensagem de erro pior.
- **Schema do domínio importando o modelo do ORM** para "reaproveitar tipos".
  Amarra o contrato HTTP ao desenho da tabela.

## Ponteiros

- `templates/app-base-model.py` — o modelo base do projeto, com a serialização
  centralizada.
- `templates/module-schemas.py` — entrada e saída de um domínio, separadas.
- A taxonomia de erro que o serviço levanta: skill `python-tratamento-de-erros`.
- Onde ficam a tabela e o mapeamento: skill
  `python-sqlalchemy-async-repository`.
