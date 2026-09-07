---
name: python-testes-de-integracao-httpx
description: "Integração com httpx.AsyncClient e ASGITransport desde o primeiro teste: banco real, dependency_overrides no lugar de monkeypatch e a afirmação sobre resposta e estado."
user-invocable: false
---

# Teste de integração com httpx

## Quando esta skill vale

Vale para todo critério de aceite do tipo `comportamental`: o que atravessa
rota, dependência, serviço, repositório e banco.

Para a regra isolada existe a skill `python-testes-unitarios`.

## A regra

**O cliente é `httpx.AsyncClient` com `ASGITransport`, desde o primeiro teste:**

```python
transport = ASGITransport(app=app)
async with AsyncClient(transport=transport, base_url="http://test") as client:
    ...
```

**O banco é real.** Mockar o banco em teste de integração é anti-padrão nomeado
na fonte primária: o que sobra prova que o código chama o que chama.

**O que se troca é a dependência, por `app.dependency_overrides`** — nunca por
monkeypatch de atributo interno.

**O mock é do serviço externo**, não do que é seu.

**A afirmação cobre a resposta e o estado.**

## Por quê

**Escolher o cliente assíncrono no primeiro dia evita reescrever a suíte
inteira depois.** O cliente síncrono roda o laço de eventos por fora; quando o
primeiro teste precisar de uma fixture assíncrona, todas as anteriores param de
valer, e a migração acontece com a suíte inteira vermelha.

**`dependency_overrides` é substituição pela porta da frente.** É o mecanismo
que a própria FastAPI oferece, e ele continua funcionando quando o módulo é
reorganizado. Monkeypatch de interno amarra o teste ao caminho de import: mover
uma função de arquivo quebra o teste sem que o comportamento tenha mudado.

**Afirmar só a resposta deixa passar o defeito mais caro.** Um `201` com o corpo
certo e nada gravado é exatamente o que acontece quando a transação não confirma
— e é invisível para um teste que só olha o JSON.

## Exemplo

**Errado** — banco mockado e afirmação só na resposta:

```python
def test_create_post(monkeypatch) -> None:
    monkeypatch.setattr("src.posts.service.PostService.create", lambda *_: FAKE_POST)
    client = TestClient(app)

    response = client.post("/posts", json={"title": "First", "body": "Body"})

    assert response.status_code == 201
```

O serviço trocado é justamente o que deveria ser exercitado. Sobrou um teste de
que a rota existe.

**Certo** — banco real, sessão do teste injetada, resposta e estado afirmados:

```python
async def test_criar_um_post_devolve_201_e_grava_no_banco(
    client: AsyncClient, session: AsyncSession
) -> None:
    response = await client.post("/posts", json={"title": "First", "body": "Body"})

    assert response.status_code == 201
    assert response.json()["status"] == PostStatus.DRAFT

    rows = await session.execute(select(Post))
    assert [p.title for p in rows.scalars().all()] == ["First"]
```

## As três naturezas também valem aqui

```python
async def test_o_contrato_de_saida_nao_devolve_campo_alem_do_declarado(client) -> None:
    assert set(response.json()) == {"id", "title", "body", "status", "created_at", "published_at"}


async def test_campo_desconhecido_na_entrada_e_recusado(client) -> None:
    assert response.status_code == 422


async def test_publicar_duas_vezes_devolve_409(client) -> None:
    assert segunda.json()["code"] == "post_already_published"
```

O primeiro é contrato, e é o que pega campo interno vazando para a resposta. O
terceiro é borda, e prova que o erro de domínio chegou ao cliente como o código
de status certo — a fronteira inteira exercitada de ponta a ponta.

## Um banco por teste, e o motivo do `StaticPool`

```python
engine = create_async_engine(
    "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
```

Sem `StaticPool`, cada retirada do pool abre um banco em memória **novo e
vazio**, e a tabela criada no preparo some antes da primeira consulta. O sintoma
é `no such table` num teste cujo preparo claramente criou a tabela.

Quando o critério depende de recurso específico do Postgres — tipo próprio,
índice parcial, restrição de exclusão —, o teste roda contra Postgres de
verdade, como o fluxo de CI já provê.

## Erros comuns

- **`TestClient` síncrono numa aplicação assíncrona.** Funciona até a primeira
  fixture assíncrona.
- **`async_asgi_testclient`.** Sem manutenção; a fonte primária o lista como
  anti-padrão.
- **Não limpar `dependency_overrides` no fim.** O vazamento contamina o teste
  seguinte, e a falha aparece em outro arquivo.
- **Compartilhar um banco entre todos os testes.** A ordem passa a importar.
- **Mockar o repositório.** Vira teste unitário com custo de integração.

## Ponteiros

- `templates/conftest.py` — a sessão em banco real e o cliente assíncrono.
- `templates/test-api.py` — as três naturezas atravessando a aplicação.
- O teste isolado da regra: skill `python-testes-unitarios`.
- Onde o Postgres do fluxo é declarado: skill `python-docker-e-ci`.
