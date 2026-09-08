-- Chave-valor, e não uma linha com duas colunas: apagar a chave é um DELETE de
-- uma linha e não pode encostar no modelo (RF-04).
CREATE TABLE advisor_config (
    name TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
