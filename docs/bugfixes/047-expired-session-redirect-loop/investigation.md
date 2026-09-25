# Investigação: sessão expirada prende o app entre o login e os saldos

## Relato
- **Sintoma:** com o app aberto, a sessão expira no servidor (ou o dono sai por outra aba). Na próxima vez que o app pergunta "quem está logado", a tela pisca entre "Entrar" e "Saldos de hoje" sem parar, e não dá para entrar de novo sem fechar a aba.
- **Esperado:** com a sessão expirada, o app vai para a tela "Entrar" e fica nela; um novo login leva aos saldos.
- **Como reproduzir:** entrar, ir aos saldos, encerrar a sessão no servidor (`POST /api/auth/logout` fora do app ou esperar a expiração) e voltar o foco para a aba: a URL alterna entre `/app/login` e `/app/`.
- **Onde:** `src/lib/auth.tsx` (`getMe`, `ProtectedRoute`), `src/app/routes/login.tsx`.

## Causa raiz
A consulta de "quem está logado" (`GET /api/auth/me`) trata o 401 como erro. Quando uma consulta que já tinha dado falha, o React Query guarda o erro **e mantém o último dado bom**. Depois da expiração, a mesma consulta passa a dizer duas coisas ao mesmo tempo:

- `error` é o 401, e `ProtectedRoute` manda para `/login`;
- `data` ainda é o usuário de antes, e `LoginRoute` manda para `/`.

As duas telas leem a mesma consulta por lados diferentes e se devolvem a navegação sem fim. O 401 de `/api/auth/me` não é falha: é a resposta normal para "ninguém logado", e deveria substituir o usuário guardado.

## Evidência
- Teste de regressão (commit `c94193e`): `src/app/__tests__/login-to-balances.test.tsx`, `a session that expires while the app is open lands on the login page and stays there`. Depois do login, a sessão acaba no servidor e a consulta do usuário é refeita: o roteador registra `/login`, `/`, `/login`, `/`… (21 navegações, até o freio do próprio teste), quando o esperado é uma só, para `/login`.

## Correção proposta
- `src/lib/auth.tsx` — `getMe` devolve `User | null`: o 401 de `/api/auth/me` vira `null` (ninguém logado), qualquer outro erro continua subindo. Como a consulta termina com sucesso, o `null` substitui o usuário guardado e as duas telas passam a ler a mesma resposta.
- `ProtectedRoute` redireciona para o login quando o dado é `null`, em vez de olhar o 401 no erro; um erro que não é 401 continua indo para o limite de erro.
- `LoginRoute` não muda: com `data` nulo ela mostra o formulário.
- **Risco:** as telas que mostram o login do usuário no cabeçalho já leem `data?.login`, e continuam funcionando com `null`.

## Fora da correção
- Um 401 em qualquer outra chamada da API (saldos, gastos, categorias) não avisa o app de que a sessão acabou: a tela mostra a mensagem de erro daquela área até a consulta do usuário ser refeita (troca de foco da aba ou nova tela). Registrado no roadmap como item próprio.

## Pontos em aberto
Nenhum.
