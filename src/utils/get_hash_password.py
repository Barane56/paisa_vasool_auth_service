"""
Utility to generate an argon2 password hash for manual DB seeding.

Usage:
    python -m src.utils.get_hash_password <password>

Example:
    python -m src.utils.get_hash_password changeme123

It will print:
  - The hash (copy this into your INSERT statement)
  - The exact SQL INSERT commands to seed the admin user

Then run those SQL commands in your DB container:
    docker exec -it <db_container> psql -U <user> -d <db> -c "<sql>"
"""

import sys

from passlib.context import CryptContext

_pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.get_hash_password <password>")
        sys.exit(1)

    password = sys.argv[1]
    hashed = _pwd_ctx.hash(password)
    admin_name = "Administrator"
    admin_email = "admin@admin.com"

    print("\n" + "=" * 60)
    print("  PASSWORD HASH GENERATED")
    print("=" * 60)
    print(f"\nPassword : {password}")
    print(f"Hash     : {hashed}")
    print("\n" + "-" * 60)
    print("  COPY-PASTE SQL (run inside your DB container)")
    print("-" * 60)
    print(f"""
-- Step 1: Insert the admin user (no role column on users table)
INSERT INTO users (name, email, password_hash)
VALUES ('{admin_name}', '{admin_email}', '{hashed}')
ON CONFLICT (email) DO UPDATE
    SET password_hash = EXCLUDED.password_hash,
        name          = EXCLUDED.name;

-- Step 2: Assign the admin role via user_roles table
INSERT INTO user_roles (user_id, role_id)
SELECT u.user_id, r.role_id
FROM   users u, roles r
WHERE  u.email     = '{admin_email}'
AND    r.role_name = 'admin'
ON CONFLICT (user_id) DO UPDATE
    SET role_id = EXCLUDED.role_id;
""")
    print("=" * 60)
    print("\nDocker one-liner (replace <container> and <dbname>/<user>):")
    print(f"""
docker exec -it <db_container> psql -U <db_user> -d <db_name> -c \\
  "INSERT INTO users (name, email, password_hash) \\
   VALUES ('{admin_name}', '{admin_email}', '{hashed}') \\
   ON CONFLICT (email) DO UPDATE SET password_hash=EXCLUDED.password_hash, name=EXCLUDED.name; \\
   INSERT INTO user_roles (user_id, role_id) \\
   SELECT u.user_id, r.role_id FROM users u, roles r \\
   WHERE u.email='{admin_email}' AND r.role_name='admin' \\
   ON CONFLICT (user_id) DO UPDATE SET role_id=EXCLUDED.role_id;"
""")


if __name__ == "__main__":
    main()
