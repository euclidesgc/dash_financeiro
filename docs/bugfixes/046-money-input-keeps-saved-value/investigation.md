# Investigação: campo de dinheiro apaga o valor gravado

## Relato
- **Sintoma:** no teto do mês (tela de gastos) e no limite de uma categoria (tela de categorias), digitar o valor como se escreve no Brasil, "1.500,00", e salvar apaga o valor que estava gravado, sem aviso. No mesmo formulário: limite negativo mostra "Use no máximo duas casas decimais." em vez de "Informe um valor maior que zero."; salvar o campo vazio fecha o formulário sem dizer nada (e tira o teto); e o botão continua "Definir teto" quando o teto já existe.
- **Esperado:** o campo aceita "1.500,00", "1500", "1500,5" e "1500.50"; texto que não é valor mostra um erro e nunca vira "tirar o teto"; tirar o teto ou o limite só por uma ação explícita; mensagens claras em português; com teto gravado, o botão diz "Alterar teto".
- **Como reproduzir:** tela de gastos com um mês inteiro e teto gravado → "Definir teto" → apagar o campo, digitar "1.500,00" → "Salvar": o painel volta a "Sem teto definido".
- **Onde:** `src/features/expenses/components/ceiling-form.tsx`, `src/features/categories/components/category-limit-form.tsx`, `src/utils/money-text-schema.ts`, `src/utils/cents.ts`, `src/features/expenses/components/month-ceiling.tsx`.

## Causa raiz
Os dois campos são `input type="number"`. O navegador só entrega ao formulário o que ele próprio consegue ler como número no formato inglês: para "1.500,00" o valor do campo passa a ser vazio (no jsdom, onde rodam os testes, vira "1.5"). O esquema `moneyTextSchema` trata vazio como "sem valor", e o formulário manda `null` à API, que é o pedido de tirar o teto ou o limite. Ou seja, "apagar" é o significado do campo vazio, e o campo fica vazio sempre que o texto não é número em inglês: o dono não tem como distinguir "quero tirar" de "digitei diferente".

As outras três falhas vêm do mesmo esquema e da mesma tela:
- o primeiro teste do esquema é o formato `^\d+([.,]\d{1,2})?$`, e "-5" falha nele antes de chegar ao teste de "maior que zero", por isso a mensagem de casas decimais;
- vazio é válido no esquema, então salvar vazio manda `null` e o `onDone` fecha o formulário;
- `month-ceiling.tsx` usa o mesmo rótulo "Definir teto" nos dois ramos, com e sem teto.

## Evidência
- Testes de regressão (commit `7a33940`):
  - `src/features/expenses/components/__tests__/ceiling-form.test.tsx`: `a pt-BR amount like "1.500,00" saves 150000 cents instead of removing the ceiling` (recebe 150 centavos no jsdom), `text that is not an amount shows an error and never removes the ceiling` e `saving an empty field asks for a value instead of closing silently` (mandam `null`).
  - `src/features/categories/components/__tests__/category-limit-form.test.tsx`: `a pt-BR amount like "1.500,00" saves 150000 cents instead of removing the limit` e `a negative limit asks for a value greater than zero`.
  - `src/features/expenses/components/__tests__/month-ceiling.test.tsx`: `with a ceiling already set the button says "Alterar teto"`.
- Na revisão geral de 25/09/2026, a mesma entrada num campo `type="number"` com valor inválido para o navegador deixou `input.value` vazio e o PUT saiu com `null`.

## Correção proposta
- `src/utils/money-text.ts` (novo) — `parseMoneyText` lê o texto em formato brasileiro e devolve os centavos ou o motivo da recusa (vazio, formato, casas decimais, não positivo), com aritmética de inteiros. Aceita "R$" na frente, ponto de milhar em grupos de três, vírgula decimal e, sem vírgula, ponto seguido de uma ou duas casas como decimal. `formatMoneyInput` escreve o valor gravado como "1.500,00".
- `src/utils/money-text-schema.ts` — esquema obrigatório que transforma o texto em centavos, com uma mensagem por motivo: "Informe um valor.", "Use o formato 1.500,00.", "Use no máximo duas casas decimais.", "Informe um valor maior que zero.".
- `ceiling-form.tsx` e `category-limit-form.tsx` — campo `type="text"` com `inputMode="decimal"`; salvar manda os centavos do esquema; com valor gravado, um botão "Remover teto" / "Remover limite" manda `null`, que passa a ser a única forma de tirar.
- `month-ceiling.tsx` — com teto gravado, o botão diz "Alterar teto" (nome acessível "Alterar teto do mês"); na categoria com limite, o nome acessível passa a "Alterar limite de …".
- `src/utils/cents.ts` sai: `toCents` e `fromCents` só serviam a esses dois campos.
- **Risco:** "1.999" passa a ser mil novecentos e noventa e nove reais (milhar), não um erro de casas decimais; é a leitura brasileira. Quem digitava "0" continua vendo "Informe um valor maior que zero.".

## Fora da correção
Nenhum.

## Pontos em aberto
Nenhum.
