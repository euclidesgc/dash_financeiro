---
name: python-testes-unitarios
description: "Teste unitário do serviço com dublê: as três naturezas contrato, caminho feliz e bordas; nome de caso em prosa; e o teste que prova a spec em vez de espelhar a implementação."
user-invocable: false
---

# Teste unitário

## Quando esta skill vale

Vale para a camada de serviço e para funções puras. É o teste que roda em
milissegundos, sem banco, sem cliente HTTP e sem aplicação levantada.

Para o teste que atravessa a aplicação inteira existe a skill
`python-testes-de-integracao-httpx`.

## A regra

**O alvo é o serviço, e o repositório é dublê.**

**Todo conjunto de teste tem as três naturezas**, e faltando uma o conjunto está
incompleto ainda que a cobertura esteja alta:

| Natureza | O que ela prova |
|---|---|
| **Contrato e propriedades** | a forma do que entra e sai, e o que é sempre verdade |
| **Caminho feliz** | o fluxo principal faz o que o produto promete |
| **Bordas** | vazio, limite, duplicado, ausente, conflito |

**O nome do caso é uma frase em prosa** que diz a regra:

```python
async def test_publicar_duas_vezes_e_conflito_e_nao_repeticao_silenciosa() -> None:
```

**O dublê mora no arquivo de teste** ou num módulo de dublês, com a mesma forma
do colaborador real.

## Por quê

**Cobertura mede execução, não verificação.** Um teste que chama o método e não
afirma nada cobre cem por cento e prova zero. As três naturezas existem porque a
que falta é quase sempre a mesma: bordas. E é nela que mora o defeito que chega
ao cliente.

**Dublê de repositório é o que torna a borda barata.** "Publicar um post que não
existe" com banco real custa preparar estado, subir contêiner e limpar depois;
com um dublê em memória, custa uma lista vazia.

**Teste que espelha a implementação trava a refatoração.** Afirmar que
`session.execute` foi chamado uma vez prova que o código chama o que chama —
não que o comportamento está certo. Quando a consulta muda, o teste quebra sem
que nada tenha ficado errado, e o time aprende a apagar teste.

## Exemplo

**Errado** — espelha a implementação e não afirma comportamento:

```python
async def test_publish() -> None:
    repo = Mock()
    service = PostService(repo)
    await service.publish(1)
    repo.get.assert_called_once_with(1)
```

Prova que o serviço chama `get`. Não prova que publicar muda o estado, nem que
publicar duas vezes é conflito. E quebra no dia em que o método passar a se
chamar `find`.

**Certo** — afirma a regra, e a borda tem caso próprio:

```python
async def test_publicar_marca_o_instante_da_publicacao() -> None:
    post = PostFactory(id=1)
    service = make_service([post])

    published = await service.publish(1)

    assert published.status is PostStatus.PUBLISHED
    assert published.published_at is not None


async def test_publicar_duas_vezes_e_conflito_e_nao_repeticao_silenciosa() -> None:
    post = PostFactory(id=1, status=PostStatus.PUBLISHED)
    service = make_service([post])

    with pytest.raises(PostAlreadyPublishedError):
        await service.publish(1)
```

## O dublê tem a forma do real

```python
class FakePostRepository:
    def __init__(self, posts: list[Post] | None = None) -> None:
        self.posts = posts or []

    async def get(self, post_id: int) -> Post | None:
        return next((p for p in self.posts if p.id == post_id), None)
```

Um dublê escrito à mão falha na compilação quando a assinatura do real muda. Um
`Mock()` aceita qualquer chamada, inclusive as que deixaram de existir — e o
teste continua verde depois de o código real ter quebrado.

## Arranjo, ação e afirmação, separados por linha em branco

O corpo do teste tem três blocos visíveis. Quando eles se misturam, ninguém
consegue dizer o que estava sendo exercitado — e um teste ilegível é um teste
que será apagado em vez de consertado.

## Erros comuns

- **`Mock()` em tudo.** Aceita chamada que não existe mais e esconde a quebra.
- **Um teste por método.** A unidade é o comportamento, não o método; um método
  com três regras precisa de três casos.
- **Nome como `test_publish_2`.** Quando quebra, ninguém sabe o que se perdeu.
- **Afirmar a mensagem da exceção.** O tipo é o contrato; o texto é para gente
  e muda.
- **Estado compartilhado entre casos.** A ordem passa a importar, e a falha
  aparece só quando a suíte roda inteira.

## Ponteiros

- `templates/test-service.py` — as três naturezas num arquivo, com dublê
  escrito à mão.
- Os objetos que os casos usam: skill `python-fixtures-e-factories`.
- O teste que atravessa a aplicação: skill
  `python-testes-de-integracao-httpx`.
- A camada que este teste exercita: skill `python-service-layer`.
