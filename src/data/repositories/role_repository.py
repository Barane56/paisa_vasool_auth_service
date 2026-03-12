# role_repository.py — RoleRepository
import logging
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import DatabaseError
from src.data.models.postgres import Role

logger = logging.getLogger(__name__)


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, role_name: str) -> Role | None:
        try:
            result = await self.db.execute(select(Role).where(Role.role_name == role_name))
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error("get_role_by_name failed | role=%s error=%s", role_name, exc)
            raise DatabaseError("Failed to fetch role") from exc
