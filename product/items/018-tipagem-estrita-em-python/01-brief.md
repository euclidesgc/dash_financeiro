# Brief — 018-tipagem-estrita-em-python

**Item:** `018-tipagem-estrita-em-python` · **Trilha:** rápida

> Este documento funde PRD e spec.

## Problema

A norma 35 deste projeto e a skill de tipagem do pack cobram tipos verificados em
modo estrito. **Nenhum comando verifica isso.** `mypy` não é sequer dependência
declarada: não está no ambiente travado, não está no portão de lint, não está no
fluxo de integração contínua.

Norma que nada mede não governa. Ao longo desta corrida, **todo validador cego
teve de escrever a mesma frase** — que o verificador de tipos não existe neste
projeto e por isso não foi medido. Doze veredictos carregam essa ressalva.

**A medição está feita, e vem antes da escolha:** `mypy --strict`, apontado para o
interpretador do projeto, acusa **202 erros em 36 arquivos**, sobre 86 fontes.
Três quartos são de duas classes mecânicas — genérico sem parâmetro (86) e função
sem anotação (34) —, e a maior classe restante (56 chamadas a função sem tipo)
desaparece sozinha quando as funções chamadas ganham anotação. Por pacote:
`app` 126, `ingestao` 79, `financas` 15.

## Escopo

`mypy --strict` roda sobre os três pacotes da aplicação, sai limpo, é dependência
de desenvolvimento declarada e travada, e o portão de lint o inclui.

## Não-escopo

- **Nenhuma baseline decrescente.** A decisão e o porquê estão em
  `00-discovery.md`.
- **Nenhuma mudança de comportamento.** O item acrescenta anotação; se um total
  mudar, é defeito.
- **Nenhum verificador alternativo.** A norma 35 nomeia `mypy`.
- **Os testes ficam de fora do modo estrito** nesta entrega: o alvo declarado
  pela norma são os três pacotes da aplicação.

## Requisitos

- **RF-01.** `mypy` é dependência de desenvolvimento declarada e travada no
  ambiente, como o `ruff` já é.
- **RF-02.** A configuração do modo estrito vive no arquivo de projeto, num lugar
  só, e nomeia os três pacotes.
- **RF-03.** `mypy --strict` sobre os três pacotes sai **sem nenhum erro**, e a
  saída diz quantos arquivos mediu — número maior que zero, porque o verificador
  sai com sucesso quando não encontra arquivo nenhum.
- **RF-04.** O portão de lint do projeto passa a incluir a verificação de tipos, e
  o fluxo de integração contínua roda o mesmo comando.
- **RF-05.** Nenhum silenciamento mudo: todo `ignore` traz o código do erro **e**
  a razão, na mesma linha.
- **RF-06.** Nenhum comportamento muda: a suíte inteira continua passando, com o
  mesmo número de testes, e os números congelados do documento de referência
  continuam iguais.

## Riscos

- **Anotar mudando comportamento.** É o risco central — uma conversão colocada
  para agradar o verificador altera um número. RF-06 é o que mede, e a suíte é a
  rede.
- **Silenciar em vez de resolver.** RF-05 é o que impede, e a verificação é
  estrutural: `ignore` sem código e sem razão reprova.
