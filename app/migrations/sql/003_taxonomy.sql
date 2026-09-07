CREATE TABLE category_groups (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    position INTEGER NOT NULL,
    is_fallback INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE natures (
    value TEXT PRIMARY KEY,
    position INTEGER NOT NULL,
    is_fallback INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE essentialities (
    value TEXT PRIMARY KEY,
    position INTEGER NOT NULL,
    is_fallback INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE category_rules (
    id INTEGER PRIMARY KEY,
    match_kind TEXT NOT NULL,
    match_value TEXT NOT NULL,
    group_id INTEGER NOT NULL REFERENCES category_groups(id),
    nature TEXT NOT NULL REFERENCES natures(value),
    essentiality TEXT NOT NULL REFERENCES essentialities(value),
    UNIQUE (match_kind, match_value)
);

CREATE TABLE crossings (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    nature TEXT NOT NULL REFERENCES natures(value),
    essentiality TEXT NOT NULL REFERENCES essentialities(value),
    position INTEGER NOT NULL
);

ALTER TABLE transactions ADD COLUMN payee TEXT;

ALTER TABLE transactions ADD COLUMN group_id INTEGER REFERENCES category_groups(id);

ALTER TABLE transactions ADD COLUMN nature TEXT REFERENCES natures(value);

ALTER TABLE transactions ADD COLUMN essentiality TEXT REFERENCES essentialities(value);

ALTER TABLE transactions ADD COLUMN rule_id INTEGER REFERENCES category_rules(id) ON DELETE SET NULL;

CREATE INDEX idx_transactions_payee ON transactions (payee);

CREATE INDEX idx_transactions_group_id ON transactions (group_id);

CREATE INDEX idx_transactions_date ON transactions (date);
