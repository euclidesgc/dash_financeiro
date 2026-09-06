CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    login TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE login_attempts (
    id INTEGER PRIMARY KEY,
    ip TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    success INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_login_attempts_ip_occurred_at ON login_attempts (ip, occurred_at);

CREATE TABLE accounts (
    id TEXT PRIMARY KEY,
    name TEXT,
    type TEXT,
    subtype TEXT,
    institution TEXT,
    balance_cents INTEGER NOT NULL,
    updated_at TEXT
);

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    pluggy_id TEXT NOT NULL UNIQUE,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    date TEXT NOT NULL,
    description TEXT,
    amount_cents INTEGER NOT NULL,
    type TEXT,
    category_pluggy TEXT,
    category TEXT,
    installment_current INTEGER,
    installment_total INTEGER,
    is_transfer INTEGER NOT NULL DEFAULT 0,
    transfer_reason TEXT NOT NULL DEFAULT '',
    is_refund INTEGER NOT NULL DEFAULT 0,
    refunded_by TEXT,
    is_cash_withdrawal INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE sync_runs (
    id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    transactions_count INTEGER,
    accounts_count INTEGER,
    message TEXT
);
