# user_repository.py — UserRepository
import logging
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import DatabaseError
from src.data.models.postgres import User, UserRole, Role
from .role_repository import RoleRepository

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        try:
            result = await self.db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error("get_by_email failed | email=%s error=%s", email, exc)
            raise DatabaseError("Failed to fetch user by email") from exc

    async def get_by_id(self, user_id: int) -> User | None:
        try:
            result = await self.db.execute(select(User).where(User.user_id == user_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error("get_by_id failed | user_id=%s error=%s", user_id, exc)
            raise DatabaseError("Failed to fetch user by id") from exc

    async def create(self, name: str, email: str, password_hash: str) -> User:
        """Creates a user with the default 'finance_associate' role."""
        return await self.create_with_role(name, email, password_hash, "finance_associate")

    async def create_with_role(self, name: str, email: str, password_hash: str, role_name: str) -> User:
        """Creates a user and assigns the given role via the user_roles table."""
        try:
            role = await RoleRepository(self.db).get_by_name(role_name)
            if not role:
                raise DatabaseError(f"Role '{role_name}' not found in roles table")
            user = User(name=name, email=email, password_hash=password_hash)
            self.db.add(user)
            await self.db.flush()
            user_role = UserRole(user_id=user.user_id, role_id=role.role_id)
            self.db.add(user_role)
            await self.db.flush()
            logger.debug("User staged with role | email=%s role=%s", email, role_name)
            return user
        except DatabaseError:
            raise
        except SQLAlchemyError as exc:
            logger.error("create_with_role failed | email=%s error=%s", email, exc)
            raise DatabaseError("Failed to create user") from exc

    async def get_all_by_role(self, role_name: str) -> list[User]:
        """Returns all users assigned to the given role."""
        try:
            result = await self.db.execute(
                select(User).join(User.user_role).join(UserRole.role).where(Role.role_name == role_name)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            logger.error("get_all_by_role failed | role=%s error=%s", role_name, exc)
            raise DatabaseError("Failed to fetch users by role") from exc
