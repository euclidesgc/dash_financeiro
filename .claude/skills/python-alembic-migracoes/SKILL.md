---
name: python-alembic-migracoes
description: "Migrações com Alembic: template assíncrono, migração estática e reversível, nome de arquivo com data e slug, e por que o downgrade é medido no CI e não presumido."
user-invocable: false
---

# Migrações com Alembic

## Quando esta skill vale

Vale sempre que o esquema do banco muda: coluna, tabela, índice, restrição,
tipo, ou dado que precisa acompanhar a mudança de estrutura.

Não vale para o mapeamento em si (skill
`python-sqlalchemy-async-repository`).

## A regra

**O projeto usa o template assíncrono:**

```bash
uv run alembic init -t async migrations
```

**Toda mudança de esquema é uma migração versionada.** Comando solto no banco
não existe: o ambiente seguinte não o tem, e a partir daí os dois divergem sem
que nada acuse.

**A migração é estática.** Ela não importa código da aplicação — nem modelo,
nem serviço, nem enumeração.

**Toda migração tem `downgrade` que desfaz de verdade.**

**O nome do arquivo carrega data e descrição**, pelo `file_template` do
`alembic.ini`:

```
2026_09_05_2140-create_post.py
```

## Por quê

**Migração que importa código da aplicação quebra no futuro, e o defeito é
retroativo.** A migração de março importa `PostStatus`; em agosto alguém remove
um membro dessa enumeração; a migração de março passa a falhar, e com ela toda
reconstrução do banco do zero — incluindo a de qualquer ambiente novo. Por isso
o valor é escrito literalmente dentro da migração, ainda que pareça duplicação.

**`downgrade` só existe se for executado.** `alembic check` compara modelo e
esquema e aprova um `downgrade` que nunca rodou; a primeira execução real
acontece no dia do rollback, que é o pior dia possível para descobrir que ele
está errado. Por isso o portão do CI sobe, confere **e desce**.

**O nome com data é o que torna a pasta legível.** Com o padrão só de hash, a
ordem das migrações só se descobre abrindo cada arquivo e seguindo o
`down_revision`.

## Exemplo

**Errado** — migração que depende do código de hoje:

```python
from src.posts.constants import PostStatus


def upgrade() -> None:
    op.execute(f"UPDATE post SET status = '{PostStatus.DRAFT}' WHERE status IS NULL")


def downgrade() -> None:
    pass
```

O import amarra a migração ao código vivo, e o `downgrade` vazio mente: a
migração diz que é reversível e não é.

**Certo** — literal na migração, e a volta escrita:

```python
def upgrade() -> None:
    op.add_column("post", sa.Column("status", sa.String(16), nullable=True))
    op.execute("UPDATE post SET status = 'draft' WHERE status IS NULL")
    op.alter_column("post", "status", nullable=False)


def downgrade() -> None:
    op.drop_column("post", "status")
```

## O ciclo de uma mudança de esquema

```bash
uv run alembic revision --autogenerate -m "add post status"
uv run ruff format migrations/versions
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
```

**O `--autogenerate` propõe, não decide.** Ele não enxerga renomeação — vê uma
coluna removida e outra criada, e aplicar isso apaga os dados. Toda migração
gerada é lida antes de ser commitada.

A formatação entra no ciclo porque o arquivo nasce do template do Alembic e o
`ruff format` é a régua do projeto.

## Quando a migração mexe em dados

Migração de dados grande trava a tabela pelo tempo que durar. Em tabela grande,
a forma é: acrescentar a coluna aceitando nulo, preencher em lotes fora da
migração de esquema, e só então torná-la obrigatória — três migrações, não uma.

## Erros comuns

- **`alembic upgrade head` como parte do arranque da aplicação.** Duas
  instâncias subindo ao mesmo tempo executam a mesma migração em paralelo.
- **Editar uma migração já aplicada em outro ambiente.** O `alembic_version`
  já registrou aquele identificador, e a correção nunca roda.
- **Duas cabeças depois de um merge.** Resolve-se com `alembic merge`, nunca
  editando `down_revision` à mão.
- **`downgrade` com `pass`.** Diz reversível e não é.
- **Confiar no `--autogenerate` para renomear.** Ele descarta e recria a
  coluna, e os dados vão junto.

## Ponteiros

- `templates/alembic-env.py` — o `env.py` assíncrono já apontado para o
  metadata do projeto e para a URL do settings.
- `templates/script.py.mako` — o template de migração já na forma que o ruff
  aceita, com anotação moderna e import ordenado.
- O metadata e a convenção de nomes que o autogenerate lê: skill
  `python-sqlalchemy-async-repository`.
- Onde o portão sobe, confere e desce: skill `python-docker-e-ci`.
