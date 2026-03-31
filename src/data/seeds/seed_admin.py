"""
Idempotent seed: ensures admin@admin.com exists with role='admin'
and a correct argon2id password hash for password 'admin'.

Run after migration 0024:
    python -m src.data.seeds.seed_admin
"""

import asyncio
import logging

from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")

ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "admin"
ADMIN_NAME = "Administrator"


async def seed() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore

    hashed = _pwd_ctx.hash(ADMIN_PASSWORD)
    logger.info("Generated fresh argon2 hash for admin password")

    async with async_session() as session:
        await session.execute(
            text("""
                INSERT INTO users (name, email, password_hash, role)
                VALUES (:name, :email, :hash, 'admin')
                ON CONFLICT (email) DO UPDATE
                    SET password_hash = EXCLUDED.password_hash,
                        role          = 'admin',
                        name          = EXCLUDED.name
            """),
            {"name": ADMIN_NAME, "email": ADMIN_EMAIL, "hash": hashed},
        )
        await session.commit()

    logger.info("Admin seeded: %s (password: %s)", ADMIN_EMAIL, ADMIN_PASSWORD)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
