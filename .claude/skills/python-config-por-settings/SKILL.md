---
name: python-config-por-settings
description: "Configuração com pydantic-settings: um BaseSettings por módulo com env_prefix, o global só para o que é do processo, segredo sem valor padrão e .env.example versionado."
user-invocable: false
---

# Configuração por settings

## Quando esta skill vale

Vale sempre que uma variável de ambiente nova aparece, e ao criar um módulo que
precisa de configuração própria.

Não vale para segredo em si — onde ele mora e como é rotacionado é assunto do
cofre da plataforma, não do código.

## A regra

**Cada módulo tem o seu `BaseSettings`, com `env_prefix` próprio.**

```python
class PostsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POSTS_", env_file=".env", extra="ignore")

    page_size: int = 20
    max_page_size: int = 100
```

**O settings global existe, e é pequeno**: só o que é do processo inteiro —
ambiente, banco, origens permitidas.

**`pydantic-settings` é pacote separado desde a v2.** `from pydantic import
BaseSettings` não funciona mais.

**Segredo não tem valor padrão.** Sem padrão, a ausência derruba o processo no
boot com o nome da variável; com padrão, a aplicação sobe usando uma chave que
alguém escreveu para desenvolver.

## Por quê

**Um `BaseSettings` global para tudo é o anti-padrão nomeado na fonte
primária, e o custo aparece de duas formas.** A primeira: toda variável de todo
módulo passa a ser obrigatória em todo processo, e um worker que só manda
e-mail derruba por falta de uma variável de relatório. A segunda: a classe vira
o lugar onde qualquer coisa cabe, e ninguém consegue dizer quais variáveis um
módulo realmente usa.

**`env_prefix` é o que torna o recorte legível no ambiente.** `POSTS_PAGE_SIZE`
diz de quem é a variável sem abrir o código, e duas features com um `PAGE_SIZE`
cada deixam de colidir.

**Configuração validada no boot troca um erro tardio por um erro imediato.** A
alternativa é `os.environ["X"]` no meio de uma requisição, e a descoberta de que
a variável não existe acontece no primeiro cliente que aciona aquele caminho.

## Exemplo

**Errado** — uma classe para tudo, segredo com padrão e leitura solta:

```python
class Settings(BaseSettings):
    database_url: str = "postgresql://localhost/app"
    secret_key: str = "dev-secret-change-me"
    posts_page_size: int = 20
    billing_api_key: str = ""
    smtp_host: str = "localhost"


def send(to: str) -> None:
    host = os.environ["SMTP_HOST"]
```

O segredo com padrão sobe em produção sem ninguém notar. O `os.environ` no meio
do código ignora a validação. E o processo de relatórios agora exige a chave de
cobrança.

**Certo** — recorte por módulo, e o segredo sem saída fácil:

```python
class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    env: str = "local"
    database_url: str = "sqlite+aiosqlite:///./app.db"
    cors_origins: list[str] = []
```

```python
class BillingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BILLING_", env_file=".env", extra="ignore")

    api_key: str
```

`api_key` sem padrão: o processo que precisa dela não sobe sem ela, e o que não
precisa nem a carrega.

## `.env.example` é versionado; `.env` nunca

O arquivo de exemplo é a documentação executável das variáveis: quem clona o
repositório copia e preenche. Ele traz **todas** as variáveis, com valor de
desenvolvimento nas não-secretas e vazio nas secretas.

**Variável nova entra em três lugares no mesmo PR:** na classe de settings, no
`.env.example` e no cofre do ambiente. Faltando o terceiro, o deploy quebra; e
faltando o segundo, a próxima pessoa a clonar descobre sozinha.

## Erros comuns

- **`extra="forbid"` no settings.** O ambiente de execução tem dezenas de
  variáveis que não são suas; `ignore` é o correto aqui, ao contrário do que
  vale para schema de entrada.
- **Instanciar o settings dentro da função.** Relê o ambiente a cada chamada e
  perde o erro no boot, que era o ganho.
- **`os.environ` fora do módulo de configuração.** Escapa da validação e some
  do `.env.example`.
- **Segredo com valor padrão "para facilitar o teste".** O teste passa a
  provar que o padrão funciona.
- **Importar o settings de um módulo dentro de outro módulo.** É acoplamento
  entre domínios por um caminho que ninguém procura.

## Ponteiros

- `templates/global-config.py` — o settings do processo, pequeno de propósito.
- `templates/module-config.py` — o settings de um domínio, com `env_prefix`.
- `templates/env.example` — o arquivo de exemplo; renomeie para `.env.example`.
- De onde o teto de paginação é lido: skill
  `python-dependencies-para-validacao`.
- Como as variáveis chegam ao contêiner: skill `python-docker-e-ci`.
