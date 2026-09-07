---
name: python-service-layer
description: "Camada de serviço: onde a regra de negócio mora, o que ela não conhece, orquestração entre repositórios e por que o serviço não levanta HTTPException."
user-invocable: false
---

# Camada de serviço

## Quando esta skill vale

Vale sempre que existe uma decisão a tomar: uma invariante a verificar, uma
transição de estado, uma orquestração entre dois repositórios, um evento a
publicar.

Não vale para o SQL em si (skill `python-sqlalchemy-async-repository`) nem para
a tradução do erro em código de status (skill `python-tratamento-de-erros`).

## A regra

**O serviço decide, e é o único que decide.** Ele recebe dados já validados na
forma, chama repositórios, verifica invariantes de negócio e devolve objeto de
domínio.

**O serviço não conhece HTTP.** Não importa `fastapi`, não recebe `Request`,
não devolve código de status, não levanta `HTTPException`. Quando algo dá
errado, ele levanta um erro da taxonomia do domínio.

**O serviço não monta SQL.** Ele pede ao repositório.

## Por quê

**A regra separada do transporte é a regra que dá para testar em
milissegundos.** "Publicar duas vezes é conflito" vira um `assert` com um
repositório dublê, sem cliente HTTP, sem banco, sem aplicação levantada. Quando
a mesma regra mora no router, o único jeito de exercitá-la é subir tudo — e na
prática ninguém escreve o teste da borda, escreve o da rota feliz.

**A regra separada do SQL é a regra que sobrevive à troca de persistência.**
Trocar consulta, índice ou até banco não deveria tocar em nenhuma linha que
descreve negócio; quando toca, é sinal de que as duas coisas estavam no mesmo
lugar.

**O serviço que levanta `HTTPException` amarra o domínio a um framework.** A
mesma regra passa a não servir a um worker, a um comando de linha ou a um
consumidor de fila — e a duplicação que aparece nesse dia nunca volta atrás.

## Exemplo

**Errado** — o serviço sabendo de HTTP e de SQL:

```python
class PostService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def publish(self, post_id: int) -> Post:
        result = await self._session.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if post is None:
            raise HTTPException(status_code=404, detail="post not found")
        post.status = "published"
        await self._session.commit()
        return post
```

Três camadas num método: consulta, decisão e transporte. O `commit` aqui também
tira do chamador a chance de agrupar duas operações numa transação só.

**Certo** — cada dependência no seu nível:

```python
class PostService:
    def __init__(self, repository: PostRepository) -> None:
        self._repository = repository

    async def publish(self, post_id: int) -> Post:
        post = await self._repository.get(post_id)
        if post is None:
            raise PostNotFoundError
        if post.status is PostStatus.PUBLISHED:
            raise PostAlreadyPublishedError
        post.publish()
        return post
```

O serviço depende de uma interface estreita, levanta erro de domínio e não
confirma a transação — quem a delimita é o escopo da requisição.

## A regra de negócio é escrita, não herdada de padrão de coluna

```python
async def create(self, payload: PostCreate) -> Post:
    post = Post(title=payload.title, body=payload.body, status=PostStatus.DRAFT)
    return await self._repository.add(post)
```

"Nasce como rascunho" é decisão de produto. Deixá-la no `default=` da coluna a
esconde: o objeto recém-construído fica com `status=None` até o banco escrever,
e o serviço passa a decidir sobre um estado que ainda não existe.

## Onde a orquestração mora

Quando uma operação toca dois agregados, o serviço é quem os coordena — e é a
transação da requisição que garante o tudo-ou-nada. Veja a skill
`python-unit-of-work`.

## Erros comuns

- **Serviço que recebe a sessão em vez do repositório.** Volta a montar SQL,
  e o dublê no teste passa a ser um dublê de sessão.
- **Serviço que devolve schema de resposta.** Ele devolve objeto de domínio; a
  conversão para o contrato HTTP é da fronteira.
- **Serviço anêmico que só repassa para o repositório.** Se não há decisão, o
  método não precisa existir — o router chama o repositório pela dependência.
- **`commit` dentro do serviço.** Impede compor duas operações numa transação.
- **Regra de negócio dentro do modelo do ORM sem intenção.** Método no modelo é
  legítimo para transição do próprio agregado (`post.publish()`); orquestração
  entre agregados não é.

## Ponteiros

- `templates/service.py` — o serviço completo, com invariante, transição de
  estado e erro de domínio.
- O que o serviço chama: skill `python-sqlalchemy-async-repository`.
- A transação que envolve a decisão: skill `python-unit-of-work`.
- A taxonomia que ele levanta: skill `python-tratamento-de-erros`.
