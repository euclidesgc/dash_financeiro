---
name: python-estrutura-por-dominio
description: "Módulo por domínio em src/: o septeto router, schemas, models, dependencies, service, exceptions e config; import explícito entre domínios e o que nunca atravessa a fronteira."
user-invocable: false
---

# Módulo por domínio

## Quando esta skill vale

Vale sempre que um domínio nasce, ganha um endpoint ou é dividido. É a norma
estrutural deste pack para monólito — a aplicação com mais de um assunto.

Para serviço pequeno de responsabilidade única existe a outra forma, na skill
`python-estrutura-por-tipo`. A escolha entre as duas é registrada uma vez, no
início do projeto, e não se mistura no mesmo repositório.

## A regra

**Um domínio é uma pasta em `src/`, e dentro dela os arquivos têm nome fixo.**

```
src/
├── config.py          configuração global
├── database.py        engine, sessão e Base
├── exceptions.py      raiz da taxonomia
├── schemas.py         modelo base de todo schema
├── main.py            montagem da aplicação
└── posts/
    ├── router.py        as rotas do domínio, e nada além disso
    ├── schemas.py       entrada e saída HTTP
    ├── models.py        as tabelas
    ├── dependencies.py  validação e injeção
    ├── service.py       a decisão de negócio
    ├── repository.py    o SQL
    ├── exceptions.py    a taxonomia do domínio
    ├── config.py        as variáveis deste domínio
    └── constants.py     enumeração e limite
```

Cada arquivo tem uma frase, e só ela:

- **`router.py` traduz HTTP.** Lê caminho, corpo e dependência; chama o
  serviço; devolve. Sem `if` de negócio, sem `select`, sem `commit`.
- **`service.py` decide.** É onde a regra mora. Ele não conhece `Request`,
  `Response`, código de status nem `HTTPException`.
- **`repository.py` fala SQL.** É o único lugar do domínio que monta consulta.
- **`dependencies.py` valida antes de o corpo da rota começar.**
- **`schemas.py` é o contrato HTTP**, separado do `models.py`, que é o banco.
- **`exceptions.py` nomeia o que pode dar errado** naquele domínio.
- **`config.py` declara as variáveis daquele domínio**, e só delas.

## Por quê

**O router que monta consulta é o portão G7, e o gate reprova o arquivo.** A
razão é testabilidade: regra de negócio que mora junto de código de status só
pode ser exercitada levantando a aplicação inteira, então ninguém escreve o
teste de borda — escreve o teste da rota feliz, e a borda vai para produção sem
verificação. Com a regra no serviço, "publicar duas vezes" é um teste de
milissegundos com um repositório dublê.

**Agrupar por domínio em vez de por tipo é o que permite o quinto domínio
nascer sem tocar nos outros quatro.** Numa árvore por tipo, acrescentar um
domínio significa editar `routers/`, `schemas/`, `models/` e `services/` — e
toda revisão de qualquer domínio passa a listar os mesmos quatro diretórios.

**A fronteira entre domínios tem custo próprio.** Quando `orders` importa
`posts/repository.py`, o domínio `posts` perde a liberdade de mudar como
persiste, porque a mudança quebra um arquivo que ele não sabia que existia.

## Exemplo

**Errado** — o router decidindo e falando com o banco:

```python
@router.post("/{post_id}/publish")
async def publish(post_id: int, db: AsyncSession = Depends(get_session)) -> PostRead:
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404)
    if post.status == "published":
        raise HTTPException(status_code=409, detail="already published")
    post.status = "published"
    post.published_at = datetime.now(UTC)
    await db.commit()
    return PostRead.model_validate(post)
```

**Certo** — cada arquivo no seu papel:

```python
@router.post("/{post_id}/publish", response_model=PostRead)
async def publish_post(post: PostDep, service: ServiceDep) -> object:
    return await service.publish(post.id)
```

```python
async def publish(self, post_id: int) -> Post:
    post = await self._repository.get(post_id)
    if post is None:
        raise PostNotFoundError
    if post.status is PostStatus.PUBLISHED:
        raise PostAlreadyPublishedError
    post.publish()
    return post
```

O router ficou com uma linha e nenhuma decisão. O serviço levanta erro de
domínio, não `HTTPException`; quem traduz para 404 e 409 é a fronteira.

## A fronteira entre domínios

**O import é sempre explícito e por módulo:**

```python
from src.auth import service as auth_service
from src.auth import constants as auth_constants
```

**Errado**: `from src.auth import *` — ninguém consegue dizer de onde veio um
nome, e o verificador de tipos perde a origem junto.

**Errado**: `from src.posts.repository import PostRepository` a partir de outro
domínio — atravessa a fronteira e amarra o consumidor à persistência alheia.

**Certo**: um domínio consome o `service` do outro, nunca o `repository`.

Quando dois domínios precisam um do outro em ciclo, o ciclo é o sintoma: ou há
um terceiro conceito escondido que merece módulo próprio, ou um dos dois
deveria reagir a um evento em vez de chamar o outro.

## Erros comuns

- **Serviço importando `fastapi` para levantar `HTTPException`.** É tradução
  para HTTP dentro da camada que não deveria conhecer HTTP.
- **Schema de entrada devolvido como resposta.** Entrada e saída mudam por
  razões diferentes; quando são a mesma classe, um campo novo de escrita vaza
  para a leitura sem ninguém decidir isso.
- **Um `utils.py` na raiz que cresce virando depósito.** Utilitário sem dono
  vira código que ninguém revisa; prefira o domínio que mais o usa.
- **`models.py` importado pelo router** para montar a resposta. O router
  conhece schema, não tabela.

## Ponteiros

- `templates/module-router.py` — o router que só traduz HTTP.
- `templates/module-service.py` — o serviço, onde a decisão mora.
- `templates/module-dependencies.py` — a validação antes do corpo da rota.
- `templates/module-exceptions.py` — a taxonomia do domínio.
- `templates/module-constants.py` — enumeração e limite do domínio.
- A outra forma de organizar a árvore: skill `python-estrutura-por-tipo`.
- O que vive em `schemas.py`: skill `python-schemas-pydantic-v2`.
- O que vive em `repository.py`: skill `python-sqlalchemy-async-repository`.
- O que vive em `config.py`: skill `python-config-por-settings`.
