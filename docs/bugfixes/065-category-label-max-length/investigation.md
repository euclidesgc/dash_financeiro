# Investigação: nome de categoria sem teto de tamanho

## Relato
- **Sintoma:** criar ou renomear uma categoria aceita um nome de qualquer tamanho. `POST /api/categories` com 5.000 caracteres responde 201 e grava; o `PATCH /api/categories/{key}` de renomear faz o mesmo. A partir daí, a página "Categorias", o seletor de troca de categoria em "Gastos" e cada lançamento daquela categoria carregam e mostram esse texto.
- **Esperado:** o servidor recusa com 422 e uma mensagem em português o nome acima do teto, sem gravar nada; os campos "Nome da categoria" e "Novo nome" param de aceitar caracteres no mesmo teto.
- **Como reproduzir:** entrar e chamar `POST /api/categories` com `{"label": "<5.000 letras>"}`; ou, na página "Categorias", colar um texto longo em "Nome da categoria" e tocar em "Criar categoria".
- **Onde:** `app/taxonomy/catalogue.py` (`_check_label`, a regra do nome usada por criar e renomear), `app/routers/categories.py` (tradução para HTTP), `src/features/categories/types/category-label-schema.ts` e os dois formulários da SPA.

## Causa raiz
A única regra do nome de categoria, `_check_label` em `app/taxonomy/catalogue.py`, recusa só o nome vazio e o repetido. O esquema de entrada (`CategoryInput`) declara `label: str` sem tamanho, a tabela `categories` guarda `TEXT` sem limite e o esquema da SPA (`categoryLabelSchema`) só exige um caractere. Nenhuma camada tem teto, e `app/settings/limits.py`, onde moram os tetos de texto do projeto, não tem um para esse campo.

## Evidência
- Testes de regressão (commit `e27c574`), todos falham antes da correção:
  - `tests/test_categories_api.py`: `test_post_refuses_a_label_one_over_the_ceiling_with_422_and_writes_nothing` e `test_patch_refuses_a_label_one_over_the_ceiling_with_422_and_keeps_the_old_one` recebem 201 e 200 com 41 caracteres; `test_the_spa_holds_the_category_label_to_the_server_ceiling` não acha o teto nem no servidor nem na SPA;
  - `src/features/categories/types/__tests__/category-label-schema.test.ts`, `a name one over the ceiling is refused with the server message` — o esquema aceita 41 caracteres;
  - `create-category-form.test.tsx` e `categories-list.test.tsx`, `the name field stops at the 40 characters the server accepts` e `the rename field stops at the 40 characters the server accepts` — os campos aceitam 45;
  - `e2e/categories.spec.ts` — no navegador, "Nome da categoria" fica com os 45 caracteres digitados.

## Correção proposta
- `app/settings/limits.py` — `CATEGORY_LABEL_MAX = 40`, com o motivo: o maior nome do catálogo de hoje tem 33 caracteres ("Transferência própria em dinheiro"), e 40 é o mesmo teto do nome de grupo e do nome de cenário, rótulos curtos do mesmo tipo.
- `app/taxonomy/catalogue.py` — `_check_label` recusa, depois de tirar os espaços das pontas, o nome acima do teto com `LabelTooLongError`; criar e renomear passam pela mesma regra.
- `app/routers/categories.py` — `LabelTooLongError` vira 422 com "O nome da categoria pode ter no máximo 40 caracteres.".
- `src/features/categories/types/category-label-schema.ts` — `CATEGORY_LABEL_MAX = 40` e a mesma mensagem no esquema; os campos de `create-category-form.tsx` e `rename-category-form.tsx` recebem `maxLength`. Um teste do pytest lê o número da SPA e o compara com o do servidor, para os dois não se separarem.
- `src/testing/mocks/handlers.ts` — a API simulada recusa o nome longo como o servidor.
- **Risco:** nenhum nome gravado passa de 33 caracteres; um nome maior que já existisse continuaria lido como está, e só a gravação nova seria recusada.

## Fora da correção
- Os nomes de categoria vindos da Pluggy e da semente (`app/taxonomy/seed.py`) não passam por `_check_label`; são fixos no código ou mapeados por tabela, e nenhum passa do teto.

## Pontos em aberto
Nenhum.
