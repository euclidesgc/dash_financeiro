---
name: python-unit-of-work
description: "Unidade de trabalho: a sessão como escopo transacional da requisição, confirmação na saída limpa, desfazimento em qualquer exceção e por que o commit não mora no serviço."
user-invocable: false
---

# Unidade de trabalho

## Quando esta skill vale

Vale ao definir onde a transação começa e termina, e sempre que uma operação
toca mais de um agregado.

Não vale para a consulta em si (skill `python-sqlalchemy-async-repository`) nem
para a decisão de negócio (skill `python-service-layer`).

## A regra

**Uma requisição, uma transação.** A sessão do SQLAlchemy é a unidade de
trabalho concreta desta stack, e o escopo é declarado num lugar só:

```python
async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session, session.begin():
        yield session
```

`session.begin()` confirma na saída limpa e desfaz em qualquer exceção.

**Nenhuma camada acima chama `commit` ou `rollback`.** Nem o serviço, nem o
repositório, nem o router.

## Por quê

**Sem escopo declarado, cada serviço decide quando confirmar** — e a requisição
que falha no meio deixa metade do trabalho gravado. O caso concreto: criar um
pedido, debitar o estoque, falhar ao cobrar. Com dois `commit` pelo caminho, o
estoque foi debitado de um pedido que não existe, e nenhum log diz isso.

**O desfazimento automático é o que torna o erro de domínio seguro.** Quando o
serviço levanta `PostAlreadyPublishedError` no meio de uma operação que já
escreveu, a exceção sobe pelo `async with` e a transação inteira volta atrás. É
por isso que o serviço pode levantar sem se preocupar em limpar o que fez.

**O padrão vem de fora do framework, e é isso que o torna testável.** A camada
de serviço não sabe se está numa requisição HTTP, num worker ou num teste — ela
recebe repositórios ligados a uma sessão, e quem abre e fecha a sessão é o
contorno. Nos testes, o contorno é a fixture; em produção, é a dependência.

## Exemplo

**Errado** — confirmação espalhada:

```python
async def transfer(self, order_id: int) -> None:
    order = await self._orders.get(order_id)
    order.confirm()
    await self._session.commit()

    await self._stock.reserve(order.items)
    await self._session.commit()

    await self._billing.charge(order.total)
    await self._session.commit()
```

Se a cobrança falhar, o pedido está confirmado e o estoque reservado. Não há
como voltar atrás, porque as duas primeiras transações já fecharam.

**Certo** — uma transação para a operação inteira:

```python
async def transfer(self, order_id: int) -> None:
    order = await self._orders.get(order_id)
    order.confirm()
    await self._stock.reserve(order.items)
    await self._billing.charge(order.total)
```

O serviço não confirma nada. Se qualquer linha levantar, o escopo desfaz tudo.

## Quando uma operação precisa mesmo de duas transações

Existe: publicar um evento externo que não pode ser desfeito, ou uma escrita
longa que não deve segurar bloqueio. Nesse caso a divisão é **decisão
registrada**, não consequência de esquecer o escopo — e o trecho que fica fora
da transação declara o que acontece se ele falhar depois de a primeira ter
confirmado.

## O que a unidade de trabalho não resolve

Ela garante atomicidade **no banco**. Chamada a serviço externo dentro da
transação não é desfeita pelo `rollback`: o e-mail já saiu, a cobrança já foi
autorizada. Efeito externo vai **depois** da confirmação, ou entra numa fila
com a garantia própria dela.

## Erros comuns

- **`expire_on_commit` no padrão.** Depois do commit, todo atributo vira uma
  nova consulta, e o objeto devolvido pela rota dispara consultas durante a
  serialização. A fábrica de sessão declara `expire_on_commit=False`.
- **Abrir sessão dentro do repositório.** Cada repositório passa a ter a sua, e
  duas escritas da mesma operação caem em transações diferentes.
- **`try/except` em volta do corpo do serviço que engole a exceção.** O escopo
  não vê erro nenhum e confirma o trabalho parcial.
- **Sessão compartilhada entre requisições.** Uma sessão é de uma requisição; a
  global vaza estado de um cliente para outro.
- **Chamar serviço externo antes do fim da transação.** O `rollback` não desfaz
  o que já saiu pela rede.

## Ponteiros

- `templates/session-scope.py` — o escopo transacional, a fábrica de sessão e a
  convenção de nomes do metadata.
- A camada que decide dentro da transação: skill `python-service-layer`.
- Quem executa as consultas: skill `python-sqlalchemy-async-repository`.
