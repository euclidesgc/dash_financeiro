# Brief — 012-sync-pos-carga-atomica

- **RF-01** — Uma exceção em `_after` — classificação, compromissos ou escada —
  **rebaixa** a execução de `sync_runs` para `failed`, em vez de deixá-la
  afirmando sucesso.
- **RF-02** — A mensagem gravada nomeia a etapa (`pós-carga falhou`) e o tipo da
  exceção, para o log.
- **RF-03** — A mensagem que a tela mostra é **em português e acionável**: diz
  que os lançamentos entraram, que a classificação e os compromissos não foram
  recalculados, que as telas mostram o estado anterior, e manda sincronizar de
  novo.
- **RF-04** — `POST /sincronizar` devolve `200` com o aviso, nunca `500`.
- **RF-05** — A execução bem-sucedida continua gravando `ok` e continua rodando a
  pós-carga: nada do caminho feliz muda.
