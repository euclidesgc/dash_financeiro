---
name: python-tratamento-de-erros
description: "Taxonomia de erro por módulo: exceptions.py com a raiz do domínio, uma fronteira só traduzindo para HTTP, o except Exception que não existe e o ValueError que vaza detalhe interno."
user-invocable: false
---

# Erros e exceções por módulo

## Quando esta skill vale

Vale sempre que algo pode dar errado por regra de negócio: recurso ausente,
estado conflitante, permissão negada, limite excedido.

Não vale para erro de forma da requisição — isso o Pydantic resolve com 422,
na skill `python-schemas-pydantic-v2`.

## A regra

**Cada módulo tem o seu `exceptions.py`**, e todas as exceções descendem de uma
raiz comum do projeto:

```python
class DomainError(Exception):
    code = "domain_error"
    message = "Domain rule violated."
```

**O serviço levanta erro de domínio, nunca `HTTPException`.**

**Uma fronteira só traduz para HTTP**, e ela é registrada na aplicação:

```python
app.add_exception_handler(DomainError, handle_domain_error)
```

**`except Exception` em volta do corpo da rota não existe.**

## Por quê

**A raiz comum é o que impede a tradução de virar uma cadeia de `isinstance`
que ninguém mantém.** Com ela, um módulo novo ganha erros novos e a fronteira
não muda; sem ela, cada módulo inventa a sua hierarquia e o tradutor cresce a
cada domínio.

**A mensagem que vai para o corpo é a da taxonomia, nunca `str(exc)`.** O texto
de uma exceção interna carrega nome de tabela, de coluna e às vezes o valor que
falhou — desenho do banco entregue a quem só sabe mandar uma requisição.

**`except Exception` transforma defeito em resposta de sucesso mal formada.**
Ele engole o erro de programação junto com o de negócio, o alerta não dispara, e
o defeito só aparece quando alguém reclama do dado errado. É anti-padrão nomeado
na fonte primária.

**`ValueError` dentro de validador do Pydantic vira erro de validação com a
mensagem inteira exposta.** Quem escreve `raise ValueError("user 42 has no
active plan")` num validador está publicando isso para qualquer cliente. Regra
de negócio se verifica no serviço.

## Exemplo

**Errado** — regra no validador, captura genérica e mensagem interna vazando:

```python
class TransferCreate(BaseModel):
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def check_balance(cls, v: Decimal) -> Decimal:
        if v > current_balance():
            raise ValueError(f"balance {current_balance()} is below {v}")
        return v


@router.post("/transfers")
async def create(payload: TransferCreate) -> dict:
    try:
        return await service.transfer(payload)
    except Exception as exc:
        return {"error": str(exc)}
```

O saldo do usuário vaza numa resposta 422. A captura genérica devolve 200 com um
corpo de erro, então nenhum monitor conta isso como falha.

**Certo** — o schema valida forma, o serviço valida regra, a fronteira traduz:

```python
class InsufficientBalanceError(DomainError):
    code = "insufficient_balance"
    message = "Insufficient balance for this transfer."
```

```python
async def transfer(self, payload: TransferCreate) -> Transfer:
    account = await self._accounts.get(payload.account_id)
    if account.balance < payload.amount:
        raise InsufficientBalanceError
    return await self._transfers.add(...)
```

```python
@router.post("/transfers", response_model=TransferRead)
async def create_transfer(payload: TransferCreate, service: ServiceDep) -> object:
    return await service.transfer(payload)
```

## O formato da resposta de erro é um só

```python
return JSONResponse(status_code=status, content={"code": code, "detail": message})
```

`code` é estável e legível por máquina — é por ele que o cliente decide o que
fazer. `detail` é para gente. Uma API que devolve três formatos de erro obriga
cada consumidor a escrever três tratamentos.

## O mapa de status vive na fronteira, não no domínio

```python
STATUS_BY_ERROR = {NotFoundError: 404, ConflictError: 409}
```

O domínio conhece "não encontrado" e "conflito"; que isso seja 404 e 409 é
decisão de transporte. Um consumidor de fila usando o mesmo serviço não quer
saber de código de status.

## Erros comuns

- **`HTTPException` no serviço.** Amarra o domínio ao framework, e a mesma
  regra deixa de servir a worker e a comando de linha.
- **Um `try/except` por rota.** A tradução se espalha e diverge.
- **`code` derivado do nome da classe.** Renomear a classe quebra o contrato do
  cliente sem que nada acuse.
- **Devolver 500 para regra de negócio.** Alerta que dispara sem defeito ensina
  o time a ignorar alerta.
- **Erro de domínio sem `code`.** O cliente passa a comparar a mensagem, e
  qualquer melhoria de texto vira quebra.

## Ponteiros

- `templates/exceptions-base.py` — a raiz da taxonomia e as duas classes gerais.
- `templates/module-exceptions.py` — a taxonomia de um domínio.
- `templates/exception-handler.py` — a fronteira única, com o mapa de status.
- Onde a regra é verificada: skill `python-service-layer`.
- Onde a forma é verificada: skill `python-schemas-pydantic-v2`.
