# Numeração das migrações

`016` e `017` não existem — foram reservados por itens que fecharam fora de ordem e nunca viraram arquivo; a próxima migração é `019`, e `apply_migrations` recusa qualquer versão que ordene abaixo da maior já registrada em `schema_migrations`.
