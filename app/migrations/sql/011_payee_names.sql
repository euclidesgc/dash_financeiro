-- One column per field the Pluggy already sends and the load discarded. No
-- CNAE column: the code arrives bare (7490104) and is useless without a table
-- nobody has, and a speculative column is a pendency wearing a schema.
ALTER TABLE transactions ADD COLUMN merchant_name TEXT;

ALTER TABLE transactions ADD COLUMN merchant_legal_name TEXT;

ALTER TABLE transactions ADD COLUMN merchant_cnpj TEXT;

ALTER TABLE transactions ADD COLUMN receiver_name TEXT;

-- The key is composite because the precedence has five levels and the same
-- payee can hold two of them at once: with the key on payee alone, naming a
-- payee would destroy the name looked up by CNPJ, and deleting the nickname
-- would fall two levels instead of one.
CREATE TABLE payee_names (
    payee TEXT NOT NULL,
    source TEXT NOT NULL,
    name TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (payee, source)
);
