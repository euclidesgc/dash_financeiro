DROP TABLE categories;

CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    group_id INTEGER NOT NULL REFERENCES category_groups(id)
);
