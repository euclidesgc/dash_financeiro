-- The default is not decoration: ALTER TABLE ADD COLUMN NOT NULL without one
-- succeeds on an empty table and fails on a table with a row, so it would pass
-- every test and break only the owner's base, which has facts since item 008.
ALTER TABLE plan_facts ADD COLUMN kind TEXT NOT NULL DEFAULT 'fato';

-- The column stores cents, basis points and months. A name that claims cents
-- over a row that holds months is how "6 meses" is rendered "R$ 0,06".
ALTER TABLE plan_facts RENAME COLUMN value_cents TO value;

-- The same fact had two names: /dividas wrote 'quitacao' and the advisor looked
-- for 'quitacao-cdc', so the panel asked forever what the owner had answered.
-- Where the canonical name already exists in plan_facts, that row wins: it
-- carries a label and a validity that plan_parameters never had.
INSERT INTO plan_facts (name, label, value, unit, kind, source, captured_at)
SELECT canonical.name,
       canonical.label,
       canonical.value,
       'centavos',
       'fato',
       'plan_parameters',
       canonical.captured_at
FROM (
    SELECT CASE name
               WHEN 'quitacao' THEN 'quitacao-cdc'
               WHEN 'transporte' THEN 'transporte-sem-carro'
               ELSE name
           END AS name,
           CASE name
               WHEN 'quitacao' THEN 'Saldo de quitação do CDC do carro'
               WHEN 'transporte' THEN 'Custo de transporte sem o carro'
               ELSE name
           END AS label,
           value_cents AS value,
           updated_at AS captured_at
    FROM plan_parameters
) AS canonical
WHERE canonical.name NOT IN (SELECT name FROM plan_facts);

DROP TABLE plan_parameters;
