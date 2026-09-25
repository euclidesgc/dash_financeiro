ALTER TABLE categories ADD COLUMN monthly_limit_cents INTEGER NULL CHECK (monthly_limit_cents IS NULL OR monthly_limit_cents > 0);
