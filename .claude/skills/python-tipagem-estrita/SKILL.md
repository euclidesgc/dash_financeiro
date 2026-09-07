---
name: python-tipagem-estrita
description: "Tipos verificados em modo estrito: mypy 2.x como norma do pack, o que strict liga, o plugin do Pydantic, quando pyright é o desvio justificado e a única forma legítima de ignore."
user-invocable: false
---

# Tipos verificados em modo estrito

## Quando esta skill vale

Vale ao configurar o projeto e sempre que o verificador apontar algo que a
pessoa esteja prestes a silenciar. Ela define a ferramenta, o modo e a forma
aceitável de exceção.

Não vale para escolher anotação de domínio — a forma de um schema é da skill
`python-schemas-pydantic-v2`.

## A regra

**mypy em modo estrito é a norma deste pack**, apontado para o diretório de
fontes:

```bash
uv run mypy --strict src
```

A configuração mora no `pyproject.toml`, com `strict = true`,
`warn_unreachable = true` e o plugin do Pydantic ligado.

**Toda função tem assinatura anotada.** É o que `strict` cobra em primeiro
lugar, e é de onde vem quase todo o valor: uma função sem tipo é um buraco pelo
qual `Any` se espalha para todos os chamadores, silenciosamente.

## Por quê

**A escolha por mypy é operacional, não ideológica.** O portão de CI e o
`criteria_tools` do manifesto precisam de **um** comando determinístico —
"mypy ou pyright" não é executável. Dois motivos decidiram: o Pydantic publica
um plugin de mypy, que é o que ensina o verificador a entender o modelo gerado
a partir dos campos declarados; e o mypy instala pelo próprio uv, sem trazer
Node para dentro do ambiente do projeto.

**pyright é desvio legítimo** quando o time já o usa no editor e quer uma régua
só. Nesse caso, a troca é registrada como decisão do projeto, o comando do CI
passa a ser `pyright`, e o `pyproject.toml` ganha
`[tool.pyright] typeCheckingMode = "strict"`. O que não é aceitável é ter os
dois, cada um apontando um conjunto diferente de problemas.

**`warn_unreachable` merece linha própria** porque `strict` não o liga. Ele
acusa o ramo que nunca executa — o `if` depois de um `return`, a comparação com
um `Enum` que o tipo já excluiu. É o apontamento que costuma revelar lógica
errada, não estilo.

## Exemplo

**Errado** — a exceção que apaga toda a verificação daquela linha:

```python
def publish(post_id):  # type: ignore
    post = repository.get(post_id)
    return post.publish()
```

O `type: ignore` sem código silencia qualquer erro presente e futuro ali. E a
função sem anotação faz todo chamador dela receber `Any`, então o erro real
aparece longe, num arquivo que ninguém associou a esta mudança.

**Certo** — assinatura completa, e a exceção nomeando a regra e a razão:

```python
async def publish(self, post_id: int) -> Post:
    post = await self._repository.get(post_id)
    if post is None:
        raise PostNotFoundError
    post.publish()
    return post
```

Quando a biblioteca de terceiro não tem tipos, a exceção é declarada uma vez,
por módulo, no lugar certo:

```toml
[[tool.mypy.overrides]]
module = ["factory.*", "asyncpg.*"]
ignore_missing_imports = true
```

## O `ignore` que passa e o que não passa

| Forma | Veredito |
|---|---|
| `# type: ignore` | Reprovado: silencia tudo, para sempre |
| `# type: ignore[arg-type]` | Aceito com a razão escrita ao lado |
| `ignore_missing_imports` por módulo | Aceito: é ausência de stub, não erro seu |
| `ignore_errors = true` em `src/**` | Reprovado: desliga a régua onde ela vale |
| `cast(...)` com comentário do porquê | Aceito quando você sabe algo que o verificador não pode saber |

## Erros comuns

- **Rodar `mypy` sem argumento** e concluir que passou. Sem alvo, ele pode não
  encontrar arquivo nenhum e sair zero. Aponte `src` e confira na saída quantos
  arquivos foram medidos.
- **`Any` como saída fácil.** Uma anotação `Any` propaga para tudo que a
  consome; quando o tipo é mesmo desconhecido, `object` obriga a verificar
  antes de usar, que é o comportamento desejado.
- **Anotar só o retorno.** Sem os parâmetros, `strict` continua tratando a
  função como não anotada.
- **Deixar o verificador só no CI.** Ele precisa estar no gancho de
  `pre-commit`, senão a primeira vez que alguém vê o erro é depois do push.
- **`# type: ignore` num arquivo inteiro** para migrar código legado. A forma
  correta é `[[tool.mypy.overrides]]` para aquele módulo, com a remoção
  registrada como item de roadmap.

## Ponteiros

- `templates/mypy-config.toml` — o bloco pronto para o `pyproject.toml`.
- Como as ferramentas entram no ambiente: skill `python-uv`.
- Onde o verificador roda antes do commit: skill `python-pre-commit`.
