-- 0024_add_roles_and_seed_admin.sql
-- Adds user_role enum, role column to users, index, and seeds the default admin.

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
    CREATE TYPE user_role AS ENUM ('admin', 'finance_associate');
  END IF;
END $$;

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS role user_role NOT NULL DEFAULT 'finance_associate';

CREATE INDEX IF NOT EXISTS ix_users_role ON users (role);

-- -- Seed admin (password hash is a placeholder — run seed_admin.py after migration)
-- INSERT INTO users (name, email, password_hash, role)
-- VALUES (
--   'Administrator',
--   'admin@admin.com',
--   '$argon2id$v=19$m=65536,t=3,p=4$placeholder$placeholder',
--   'admin'
-- )
-- ON CONFLICT (email) DO UPDATE
--   SET role = 'admin';
