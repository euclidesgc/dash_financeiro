---
name: python-pre-commit
description: "Ganchos de pre-commit: ruff e verificador de tipos antes do commit, versões espelhando o CI, gancho local para o que precisa do ambiente do projeto e detecção de segredo."
user-invocable: false
---

# Ganchos de pre-commit

## Quando esta skill vale

Vale ao instalar o projeto e sempre que uma ferramenta nova entra na régua de
qualidade. Ela define o que roda antes do commit e o que fica só no CI.

Não vale para configurar as ferramentas em si — isso é das skills
`python-ruff` e `python-tipagem-estrita`.

## A regra

**Instalar é parte de entrar no projeto:**

```bash
uv run pre-commit install
```

Os ganchos são três grupos:

1. **ruff** — `ruff-check --fix` e `ruff-format`, na mesma versão que o CI usa.
2. **higiene de arquivo** — arquivo grande, marca de conflito não resolvida,
   TOML e YAML inválidos, fim de arquivo, espaço no fim da linha, chave privada.
3. **verificador de tipos** — como gancho `local`, rodando `uv run mypy`.

**A versão de cada gancho espelha a do `pyproject.toml`.** Quando divergem, o
commit passa na máquina e reprova no runner por diferença de formatação, e a
lição que a pessoa aprende é desinstalar o gancho.

## Por quê

**O gancho existe para encurtar o laço de retorno, não para substituir o CI.**
Descobrir um erro de formatação depois do push custa um ciclo inteiro de
runner; descobrir no commit custa segundos. Por isso o gancho roda o barato e
o determinístico, e o caro continua no CI.

**O verificador de tipos precisa ser gancho `local`.** O `pre-commit` cria um
ambiente isolado por repositório de gancho; um mypy que roda ali não enxerga
`fastapi`, `sqlalchemy` nem as suas próprias fontes, e reporta "módulo não
encontrado" no lugar do erro de tipo real. Com `language: system` e
`entry: uv run mypy --strict src`, ele roda no ambiente do projeto, que é o
único onde a resposta é verdadeira.

**`detect-private-key` é o gancho mais barato do arquivo.** Chave commitada é
rotação de credencial, reescrita de histórico e comunicação a quem depende dela
— e nada disso é desfeito com `git rm`.

## Exemplo

**Errado** — o verificador de tipos como gancho remoto:

```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.11.0
  hooks:
    - id: mypy
```

Ele roda num ambiente que não tem as dependências do projeto. O resultado é uma
lista de `import-not-found` que não diz nada sobre o código, e a reação natural
é desligar o gancho.

**Certo** — gancho local, no ambiente do projeto:

```yaml
- repo: local
  hooks:
    - id: mypy
      name: mypy
      entry: uv run mypy --strict src
      language: system
      types: [python]
      pass_filenames: false
```

`pass_filenames: false` está aí de propósito: verificar só os arquivos do
commit esconde o erro que a mudança causou **em outro** arquivo, que é
justamente o que a verificação de tipos existe para encontrar.

## Erros comuns

- **`git commit --no-verify` como hábito.** O gancho passa a existir só para
  quem não sabe do atalho, e a régua vira decoração.
- **Versão do gancho diferente da do projeto.** Formatação oscila entre commits
  conforme quem commitou.
- **Colocar a suíte de teste no gancho.** Commit que demora um minuto é commit
  que as pessoas param de fazer, e a granularidade do histórico piora.
- **`pre-commit autoupdate` sem atualizar o `pyproject.toml` junto.** Volta a
  divergência entre o gancho e o CI, agora na direção contrária.

## Ponteiros

- `templates/pre-commit-config.yaml` — o arquivo pronto; renomeie para
  `.pre-commit-config.yaml` ao copiar.
- Configuração das ferramentas: skills `python-ruff` e
  `python-tipagem-estrita`.
