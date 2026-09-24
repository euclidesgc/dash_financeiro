ALTER TABLE transactions ADD COLUMN not_expense_reason TEXT NULL CHECK (not_expense_reason IS NULL OR not_expense_reason IN ('own_transfer', 'refund', 'other'));
