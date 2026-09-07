---
name: python-estrutura-por-tipo
description: "Agrupamento por tipo de arquivo em serviço pequeno: quando a fonte primária autoriza a forma plana, o que ela custa e o sinal de que chegou a hora de migrar para domínio."
user-invocable: false
---

# Agrupamento por tipo de arquivo

## Quando esta skill vale

Vale para **serviço pequeno de responsabilidade única**: um microserviço, um
worker com uma API de saúde, uma função de borda com três rotas. É a segunda
forma de organizar a árvore, e existe porque a fonte primária do pack a
autoriza nesse recorte — ela registra que agrupar por tipo de arquivo funciona
bem em microserviço e em projeto pequeno, e que o problema apareceu no monólito
com muitos domínios.

Não vale para aplicação com mais de um assunto. Nesse caso a forma é a da skill
`python-estrutura-por-dominio`, e as duas não convivem no mesmo repositório.

## A regra

**Um arquivo por tipo, na raiz de `src/`, sem subpasta por assunto.** Os nomes
são os mesmos do módulo por domínio, no singular, e as responsabilidades também:
`router.py` traduz HTTP, `service.py` decide, `repository.py` fala SQL.

**As camadas não mudam.** O que muda é só onde os arquivos ficam. Todas as
regras de fronteira continuam valendo: o router não monta consulta nem controla
transação (portão G7), o serviço não conhece HTTP, o repositório é o único a
montar SQL.

## Por quê

**Em serviço de um assunto só, a pasta por domínio é cerimônia sem contrapartida.**
`src/posts/router.py` num serviço que só tem posts acrescenta um nível de
diretório que não separa nada — e a pessoa que abre o repositório precisa
descer duas pastas para achar a primeira linha de código.

**O custo é conhecido e chega de uma vez.** No dia em que o segundo assunto
aparece, a migração para a estrutura por domínio é reescrita de import em todo
arquivo, e ela nunca acontece em hora boa. Por isso a escolha por esta forma é
uma decisão registrada, com o gatilho de migração escrito junto.

## Exemplo

**Errado** — a forma plana com um assunto escondido dentro dela:

```
src/
├── router.py
├── service.py
└── repository.py
```

com `service.py` contendo `create_post`, `publish_post`, `create_invoice` e
`charge_invoice`. São dois assuntos num arquivo; a forma plana deixou de valer
no dia em que o segundo entrou, e ninguém percebeu porque nenhum arquivo mudou
de lugar.

**Certo** — a forma plana num assunto só:

```python
router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_post(payload: PostCreate, service: ServiceDep) -> object:
    return await service.create(payload)
```

E o import interno é sempre absoluto, como no outro formato:

```python
from src.dependencies import ServiceDep
from src.schemas import PostCreate, PostRead
```

## O gatilho de migração

Migre para a estrutura por domínio quando **qualquer um** destes aparecer:

1. **O segundo assunto de negócio entra no serviço.** É o gatilho principal e o
   mais fácil de ignorar, porque nenhum arquivo se mexe quando ele acontece.
2. **Um dos arquivos passa de algumas centenas de linhas.** `service.py` grande
   é o sintoma de duas regras diferentes disputando o mesmo arquivo.
3. **Duas pessoas passam a editar o mesmo arquivo por razões não relacionadas.**
   O conflito de merge recorrente é a árvore avisando.

A migração é registrada como divergência e reflete no documento aprovado — não
é arrumação avulsa no meio de outra fase.

## Erros comuns

- **Escolher esta forma "porque é mais simples" num produto que já tem três
  assuntos no PRD.** A simplicidade dura até a segunda fase.
- **Criar `services/` no plural com um arquivo por assunto** e chamar isso de
  forma plana. Isso já é agrupamento por domínio, só que com o nome trocado e
  sem as fronteiras que ele oferece.
- **Relaxar o portão G7 porque "é um serviço pequeno".** A camada é a mesma; a
  única coisa que mudou foi o caminho do arquivo.
- **Misturar as duas formas** — `src/posts/` ao lado de `src/router.py`. A
  árvore deixa de responder onde uma coisa mora, que é a única pergunta que ela
  existe para responder.

## Ponteiros

- `templates/arvore.txt` — a árvore completa, com a responsabilidade de cada
  arquivo e o gatilho de migração.
- A outra forma, e a norma para monólito: skill `python-estrutura-por-dominio`.
- A fronteira que vale nas duas formas: skill `python-service-layer`.
