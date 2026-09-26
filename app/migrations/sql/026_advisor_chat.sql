CREATE TABLE advisor_conversations (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- The history resent to the model is read from here, always appended to and
-- never rewritten: a provider that signs its own turns refuses an edited one.
CREATE TABLE advisor_messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES advisor_conversations (id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'tool')),
    content TEXT NOT NULL,
    provider TEXT NULL,
    model TEXT NULL,
    input_tokens INTEGER NULL,
    output_tokens INTEGER NULL,
    created_at TEXT NOT NULL,
    UNIQUE (conversation_id, position)
);
