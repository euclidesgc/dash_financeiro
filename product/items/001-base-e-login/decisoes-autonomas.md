# Decisões tomadas sem o humano — 001-base-e-login

O humano autorizou autonomia para este item em 2026-09-05, no
`product/prompt-da-proxima-sessao.md`. Este arquivo é o que ele lê de manhã:
**uma linha por decisão**, com a alternativa descartada e o porquê. Nada aqui
foi aprovado por ele.

Se alguma decisão estiver errada, todas são reversíveis — o ponto de retorno
limpo é o commit `322478c`, anterior a qualquer trabalho autônomo.

## Decisões

| # | Estágio ou fase | Decidido | Alternativa descartada | Por quê |
|---|---|---|---|---|
| D1 | discovery | Trilha **rápida**, embora o gatilho "sem dependência nova" seja falso | Trilha completa, com spec em EARS | O dono já decidiu a trilha por item antes da corrida (rápida em `001`–`005`, `007`, `008`), pela régua do modo de falha. E "sem dependência nova" é falso por construção no primeiro item de um greenfield: o item que instala a stack sempre instala a stack. |
| D2 | discovery | `uv` + `pyproject.toml` + `.venv` no repositório | `pip` + `requirements.txt`; Poetry | `uv` já está na máquina (0.10.9), resolve e instala em segundos e trava as versões em `uv.lock`. Reversível: o `pyproject.toml` é padrão e `pip install -e .` continua funcionando. |
| D3 | discovery | SQLite em `data/dash.sqlite` | `var/` ou raiz do repositório | `data/` já está no `.gitignore` desde o commit inicial, junto com `*.sqlite`. Dado financeiro nasce fora do controle de versão por dois caminhos, não por um. |
| D4 | discovery | Schema nasce só com o que este item usa (`accounts`, `transactions`, `sync_runs`, `users`, `login_attempts`), por migração numerada em SQL | Criar de uma vez as 13 tabelas do `docs/plano.md` | Tabela sem consumidor é desenho adivinhado: `plan_facts` e `scenarios` mudam de forma quando o item que as usa for escrito. O runner de migração numerada é o que torna acrescentar barato. |
| D5 | discovery | Sessão por cookie assinado com `itsdangerous`, validade absoluta de 12 h, `HttpOnly`, `SameSite=Lax`, `Path=/` | Sessão em tabela no banco | Um usuário, um processo, sem necessidade de revogar sessão de terceiro. Cookie assinado não precisa de leitura no banco a cada requisição, e o `docs/plano.md` já pede exatamente isso. |
| D6 | discovery | Rate-limit do login em tabela SQLite (`login_attempts`), janela deslizante de 15 min por IP | Contador em memória do processo | Contador em memória zera a cada `uvicorn --reload`, e um limite que some quando o processo reinicia não é limite. A tabela também deixa o critério provável por consulta. |
| D7 | discovery | Ingestão lê `data/processed/transacoes.json` e `data/raw/accounts_*.json` — o consolidado que já rodou | Reprocessar o `data/raw/*transactions*` pelo `pluggy_consolidate.py` dentro do app | O consolidado já traz transferência, estorno e parcela marcados, e foi ele que produziu os números congelados em `docs/plano.md`. Reprocessar na ingestão significaria validar de novo 344 linhas de heurística que já passaram. O `pluggy_consolidate.py` continua sendo quem produz esse arquivo, no item `006`. |
| D8 | discovery | `GET /health` exige sessão, como toda rota | Deixar `/health` aberto, como é convenção em serviço web | A norma do projeto é explícita: "Login antes de qualquer rota que devolva dado. Sem exceção, nem `/health`" (`CLAUDE.md`, invariante 24). Convenção externa não vence norma escrita do projeto. |
| D9 | plan | Segredo do cookie em `SESSION_SECRET`; sem a variável, um segredo aleatório de 32 bytes gravado em `data/session.key` com modo 600 e reusado | Sortear segredo novo a cada subida | Segredo sorteado a cada subida derruba a sessão a cada `--reload`, e o dono reabriria o login a cada salvamento de arquivo. `data/` já está fora do controle de versão. |
| D10 | plan | A folha de estilo entra no HTML servido pela própria rota; nenhum diretório estático público é montado | Montar `/static` com isenção de autenticação | A invariante 24 não abre exceção, e um diretório público é a exceção que sempre cresce. Numa aplicação local, de um usuário, o custo de embutir a folha é zero. Reversível: montar `/static` depois é uma linha. |
| D11 | plan | O critério `comando` da suíte (`pytest -q` na raiz) fica no plano, marcado como portão local | Omitir, porque a DoD global é do CI e não se repete no plano | Este repositório não tem remote, e o `harness.yml` não mede nada sem ele. Sem esse critério, a suíte não seria cobrada por portão nenhum nesta corrida. |
| D13 | fase 3 | Logout durável por `users.session_epoch` (migração `002`), com o cookie carregando a época | Lista de cookies revogados em memória do processo, como o implementer entregou | Um logout que se desfaz no reinício é pior que nenhum: quem o usou acredita ter saído. Uma coluna e um `ALTER TABLE` custam menos que a tabela de sessões, e o `RF-39` deixa de valer só enquanto o processo vive. Não abri divergência: nenhum documento aprovado afirma que a sessão é sem estado — foi a decisão `D5` que subestimou o `RF-39`, e o conserto cabe na fase. |
| D14 | fase 3 | Corrigir os seis achados da auditoria de segurança dentro da própria fase | Registrar como pendência de roadmap e fechar a fase com eles | O achado alto anulava o rate-limit inteiro por um cabeçalho `X-Forwarded-For` — medido, com 40 tentativas sem bloqueio. Entregar a porta com a tranca contornável e prometer consertar depois é entregar a fase errada. |
| D15 | fase 3 | Cookie de sessão **sem** `Secure`, com a decisão amarrada por escrito ao bind e ao `proxy_headers` | Acrescentar `Secure` já | Em HTTP no loopback, `Secure` impede o cookie de existir e a tela de login para de funcionar. O risco só nasce quando o painel sair do `127.0.0.1`, e as três linhas mudam juntas — está escrito na entrega da fase 3. |
| D16 | fase 4 | Manter o `01-brief.md` como documento único, mesmo com o item promovido para a trilha completa | Desdobrar em `01-prd.md` e `02-spec.md`, como a skill `divergence-protocol` prevê | A promoção veio de `D-001`, uma divergência sobre a redação de um requisito, não sobre o produto. Partir 45 requisitos em dois arquivos no meio da execução não muda nenhuma decisão, e o dono ainda não leu nenhum dos dois. Reversível: o `doc-reconciler` desdobra quando ele quiser. |
| D17 | fase 4 | Direção visual: **instrumento de leitura graduado**, papel frio esverdeado, tinta violeta de carimbo, face monoespaçada como principal | Os três gabaritos que a skill `frontend-design` nomeia — creme com serifa e terracota; quase-preto com verde-ácido; jornal com fios e raio zero | A unidade do produto é tempo, e a forma que corresponde a isso é a escala graduada. O violeta fica fora do eixo vermelho–verde de propósito: neste painel essas duas cores já significam dinheiro saindo e entrando, e um acento de marca ali competiria com o dado. |
| D18 | fase 4 | Título da tela: **Painel financeiro** | Usar `dash_financeiro`, o nome do repositório | Nome de repositório na interface é vocabulário de quem construiu, não de quem usa. É uma string num template e o dono troca quando quiser. |
| D12 | plan | `RF-42`–`RF-45` acrescentados ao brief: foco visível, contraste AA, movimento reduzido e tema escuro | Deixar os cinco critérios de interface sem requisito que os origine | O `criteria-auditor` os apontou como critérios órfãos. Comportamento cobrado por critério e não escrito como requisito é escopo que ninguém aprovou; a régua da corrida já os exigia, faltava o requisito. |

## Aprovações registradas em modo autônomo

Cada linha aqui é um `state.py approve --por autonomo` ou um
`diverge-set --por autonomo` que o humano **não** deu.

| Estágio | Documento | O que foi aprovado | Quando |
|---|---|---|---|
| brief | `01-brief.md` | 45 requisitos `RF-01`–`RF-45`: base do projeto, ingestão com sinal normalizado, senha e seed, sessão e autorização, rate-limit, linguagem visual, tela de login, encerramento de sessão, segredo de assinatura e comportamento da interface | 2026-09-06 00:45 UTC |
| fase 4 | `04-divergencias/D-001.md` | `D-001` ratificada como APROVADA e reconciliada: `RF-41` passa a medir "não existe rota servindo arquivo" em vez de exigir `404` — o `404` obrigaria o servidor a contar ao anônimo quais caminhos existem | 2026-09-06 02:07 UTC |
| plan | `03-plan.md` | Quatro fases — base e schema · ingestão · senha, sessão e rate-limit · linguagem visual e tela —, 58 critérios tipados, `criteria-lint` sem erro e `criteria-auditor` sem requisito órfão | 2026-09-06 00:45 UTC |

## O que ficou para o humano

O que a corrida **não** decidiu de propósito.

- **Ratificar `D-001`** com `state.py diverge-set --item 001-base-e-login --id D-001 --status APROVADA --por humano`. Enquanto isso não acontece, a fase 4 permanece marcada `blocked-on-D-001` — é a espera funcionando, não defeito, e o item fecha com ela pendente.
- **Decidir se o `01-brief.md` vira `01-prd.md` + `02-spec.md`** (ver `D16`). O item está na trilha completa desde a aprovação de `D-001`.
- **Trocar o título "Painel financeiro"** por outro, se preferir (ver `D18`).
