---
name: python-uv
description: "Dependências e ambiente com uv: pyproject como fonte única, uv.lock commitado, grupo de desenvolvimento, uv sync --frozen no CI e uv run como única forma de executar."
user-invocable: false
---

# Dependências e ambiente com uv

## Quando esta skill vale

Vale sempre que uma dependência entra, sai ou muda de versão, e sempre que
alguém precisa rodar um comando do projeto. Ela define onde a dependência é
declarada, o que é commitado e como o ambiente é reproduzido.

Não vale para escolher a biblioteca em si, nem para configurar lint (skill
`python-ruff`) ou verificação de tipos (skill `python-tipagem-estrita`).

## A regra

**O `pyproject.toml` é a única declaração de dependência, e o `uv.lock` é
commitado.** Não existe `requirements.txt`, nem `pip install` avulso, nem
ativação manual de virtualenv.

Os quatro comandos que cobrem o dia a dia:

| Intenção | Comando |
|---|---|
| Acrescentar dependência de produção | `uv add fastapi` |
| Acrescentar dependência de desenvolvimento | `uv add --dev pytest` |
| Reproduzir o ambiente exatamente como está travado | `uv sync --frozen` |
| Executar qualquer coisa no ambiente do projeto | `uv run pytest` |

A versão do Python é declarada em `.python-version`, e o uv a respeita sem que
ninguém precise instalar nada à mão.

## Por quê

**`uv.lock` commitado é o que faz a máquina de quem escreveu e o runner
rodarem a mesma árvore.** Sem ele, `>=0.141.1` resolve para uma versão hoje e
para outra na semana que vem; o teste que passou no PR reprova no `main` sem
que uma linha de código tenha mudado, e o tempo gasto para descobrir isso é
sempre maior que o tempo de commitar o arquivo.

**`--frozen` é a diferença entre reproduzir e reresolver.** `uv sync` sozinho
atualiza o lock quando o `pyproject.toml` mudou; no CI isso significa instalar
silenciosamente uma árvore diferente da que foi revisada. Com `--frozen`, o
desencontro entre os dois arquivos falha em voz alta, no passo de instalação,
em vez de virar um erro de tipo inexplicável três passos adiante.

**`uv run` remove a classe inteira de defeito "funciona na minha máquina".**
Ele garante o ambiente sincronizado antes de executar, então não existe o caso
de rodar o teste contra uma dependência que já foi removida do projeto.

## Exemplo

**Errado** — dependência instalada fora da declaração:

```bash
pip install httpx
pytest
```

O `httpx` existe na máquina de quem rodou e em lugar nenhum mais. O CI reprova
com `ModuleNotFoundError`, e a correção parece ser "instalar no CI também" —
que é o mesmo defeito, agora em dois lugares.

**Certo** — a dependência entra pela declaração, e o lock registra:

```bash
uv add --dev httpx
uv run pytest
```

O `pyproject.toml` ganha a linha, o `uv.lock` ganha a versão exata, e os dois
entram no mesmo commit.

## O grupo de desenvolvimento não vai para a imagem

```toml
[dependency-groups]
dev = ["ruff>=0.16.6", "mypy>=2.3.1", "pytest>=9.1.1"]
```

No contêiner, `uv sync --frozen --no-dev` deixa de fora o verificador de tipos,
o formatador e o framework de teste. Não é economia de disco: é superfície de
ataque. Ferramenta de desenvolvimento dentro da imagem de produção é código
executável que ninguém revisou naquele contexto.

## Erros comuns

- **Editar `uv.lock` à mão** para resolver conflito de merge. O arquivo é
  gerado; a resolução é rodar `uv lock` de novo depois de resolver o
  `pyproject.toml`.
- **`uv pip install`** para "só testar uma coisa". Instala fora do lock, e a
  dependência fantasma sobrevive até alguém recriar o ambiente do zero.
- **Fixar versão exata em toda dependência** no `pyproject.toml`. A faixa mora
  no `pyproject`, a versão exata mora no lock — inverter os dois transforma
  toda atualização de segurança numa edição manual.
- **`.venv` commitado.** Ele é derivado do lock e carrega binário compilado
  para o sistema operacional de quem o gerou.
- **Rodar `python -m pytest`** em vez de `uv run pytest`. Usa o interpretador
  do sistema, que não é o do projeto, e o erro só aparece quando as versões
  divergirem.

## Ponteiros

- `templates/pyproject.toml` — a declaração completa do projeto de exemplo,
  com dependências, grupo de desenvolvimento e a configuração das ferramentas.
- `templates/python-version` — o conteúdo de `.python-version`; renomeie ao
  copiar, porque um arquivo iniciado por ponto não sobrevive a toda cópia.
- Como o lint e a formatação são configurados: skill `python-ruff`.
- Como o ambiente vira imagem: skill `python-docker-e-ci`.
