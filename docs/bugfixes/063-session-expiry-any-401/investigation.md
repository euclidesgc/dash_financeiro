# Investigação: sessão que acaba no meio do uso não leva ao login

## Relato
- **Sintoma:** com o app aberto, a sessão acaba no servidor (expiração ou saída por outra aba). Na próxima chamada da API que não seja a pergunta "quem está logado" (`GET /api/auth/me`), por exemplo ao abrir "Gastos" ou ao tocar em "Atualizar agora", o servidor responde 401 e a área mostra a própria mensagem de erro ("Não foi possível carregar as contas."). O app só vai para "Entrar" quando a consulta do usuário é refeita por troca de foco da aba ou depois de 30 s parado.
- **Esperado:** o primeiro 401 de qualquer chamada leva o app a "Entrar".
- **Como reproduzir:** entrar, ver os saldos, encerrar a sessão fora do app (`POST /api/auth/logout`) e, em menos de 30 s, clicar em "Gastos".
- **Onde:** `src/lib/react-query.ts` (configuração única do cache de consultas), `src/lib/auth.tsx` (consulta do usuário e rota protegida).

## Causa raiz
Quem decide se o app mostra "Entrar" é a rota protegida, lendo só a consulta do usuário. Essa consulta fica 30 s como recente (`staleTime`) e só é refeita por troca de foco, montagem depois desse prazo ou login. Um 401 de outra chamada vira erro daquela consulta ou mutação e para ali: nada no app liga "o servidor recusou a sessão" a "o usuário guardado não vale mais". Durante esse intervalo, o app continua achando que há alguém logado.

## Evidência
- Testes de regressão (commit `2dcf6bd`), todos falham antes da correção:
  - `src/app/__tests__/login-to-balances.test.tsx`, `a 401 from another call while the app is open lands on the login page` — depois de a sessão acabar, os saldos respondem 401 e a tela fica em "Saldos de hoje" com o erro das contas, sem "Entrar";
  - `src/lib/__tests__/react-query.test.ts`, `a 401 from any query clears the signed-in user` e `a 401 from any mutation clears the signed-in user` — o usuário guardado continua `{ login: 'teste' }`;
  - `e2e/login-and-balances.spec.ts`, `a session that ends while the user moves between screens goes to the login page` — no navegador, "Gastos" abre com "Não foi possível carregar as contas." em vez de "Entrar".

## Correção proposta
- `src/lib/react-query.ts` — o cache de consultas e o de mutações ganham um tratamento de erro comum, o único ponto do app que olha 401: se a resposta é 401 **e** há um usuário guardado, a consulta do usuário é invalidada e refeita. O servidor confirma: `/api/auth/me` responde 401, `getMe` devolve `null` (047) e a rota protegida leva a "Entrar". Se o servidor ainda reconhecer a sessão, nada muda.
- A consulta do usuário nunca termina em 401 (a 047 transforma o 401 dela em `null`), então o tratamento não entra em laço; e com ninguém logado (senha errada no login) ele não pergunta de novo.
- `createQueryClient()` monta o cliente, para os testes usarem a mesma configuração do app.
- **Risco:** um 401 de uma rota que não seja de sessão faria uma pergunta a mais a `/api/auth/me`; o servidor só responde 401 por falta de sessão, fora o login com senha errada, já coberto.

## Fora da correção
- Depois de entrar de novo, o app volta aos saldos e não à tela em que a pessoa estava (não há `redirectTo` no login). Comportamento anterior a esta correção e fora do relato; não registrado como item porque o app tem quatro telas e o cabeçalho leva a todas.

## Pontos em aberto
Nenhum.
