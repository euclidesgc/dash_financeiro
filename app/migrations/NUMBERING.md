# Numeração das migrações

`016` e `017` não existem — foram reservados por itens que fecharam fora de ordem e nunca viraram arquivo; a próxima migração é `019`, e `apply_migrations` recusa qualquer versão que ordene abaixo da maior já registrada em `schema_migrations`.

## Base que pulou uma versão

Uma base pode ter versões acima de uma que ela nunca aplicou — foi o que
aconteceu com a base do dono, que tem `015` e não tem `012`, porque a `012`
entrou na pasta depois de ela já ter migrado.

O aplicador distingue os dois casos e dá conselhos diferentes:

- **Migração nova com número baixo**, numa base sem vão: renumere o arquivo.
- **Versão que esta base pulou**, reconhecida pelo vão — a base tem versões
  abaixo e acima dela: reconcilie com

  ```
  python -m app.migrate --reconciliar <versao>
  ```

  A reconciliação **tenta aplicar** a migração. Se ela não couber no esquema
  atual, nada é gravado e o vão continua: registrar às cegas seria assinar que o
  esquema está certo sem olhar, e foi assim que o vão nasceu.

**A `012` derruba e recria `categories`.** Reconciliá-la esvazia a tabela, e a
classificação seguinte a repõe — medido na base do dono: 77 categorias antes,
0 depois da reconciliação, 77 de novo depois de `python -m app.taxonomy.classify`,
com `changed=0`. Nenhum lançamento muda de grupo.
