ALTER TABLE transactions ADD COLUMN category_auto TEXT;
ALTER TABLE transactions ADD COLUMN category_source TEXT NOT NULL DEFAULT 'auto' CHECK (category_source IN ('auto', 'manual'));
UPDATE transactions SET category_auto = category;
