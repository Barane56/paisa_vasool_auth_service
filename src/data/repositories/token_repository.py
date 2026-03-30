# token_repository.py — RefreshTokenRepository
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.core.exceptions import DatabaseError
from src.data.models.postgres import RefreshToken

logger = logging.getLogger(__name__)


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_token(self, token: str) -> RefreshToken | None:
        try:
            result = await self.db.execute(
                select(RefreshToken).where(RefreshToken.refresh_token.is_(token))
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error("get_by_token failed | error=%s", exc)
            raise DatabaseError("Failed to fetch refresh token") from exc

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        try:
            result = await self.db.execute(
                select(RefreshToken).where(RefreshToken.jti == jti)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error("get_by_jti failed | jti=%s error=%s", jti, exc)
            raise DatabaseError("Failed to fetch refresh token by jti") from exc

    async def create(
        self, user_id: int, jti: str, refresh_token: str, settings: Settings
    ) -> RefreshToken:
        try:
            expires_at = datetime.now(UTC) + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )
            record = RefreshToken(
                user_id=user_id,
                jti=jti,
                refresh_token=refresh_token,
                is_revoked=False,
                expires_at=expires_at,
            )
            self.db.add(record)
            await self.db.flush()
            logger.debug("Refresh token staged | user_id=%s jti=%s", user_id, jti)
            return record
        except SQLAlchemyError as exc:
            logger.error(
                "create refresh token failed | user_id=%s error=%s", user_id, exc
            )
            raise DatabaseError("Failed to create refresh token") from exc

    async def revoke(self, token_record: RefreshToken) -> None:
        try:
            token_record.is_revoked = True  # type: ignore
            await self.db.flush()
            logger.debug(
                "Refresh token revoked | token_id=%s jti=%s",
                token_record.token_id,
                token_record.jti,
            )
        except SQLAlchemyError as exc:
            logger.error(
                "revoke token failed | token_id=%s error=%s", token_record.token_id, exc
            )
            raise DatabaseError("Failed to revoke refresh token") from exc

    async def revoke_all_for_user(self, user_id: int) -> None:
        try:
            await self.db.execute(
                update(RefreshToken)
                .where(
                    RefreshToken.user_id == user_id, RefreshToken.is_revoked.is_(False)
                )
                .values(is_revoked=True)
            )
            await self.db.flush()
            logger.warning("All refresh tokens revoked | user_id=%s", user_id)
        except SQLAlchemyError as exc:
            logger.error(
                "revoke_all_for_user failed | user_id=%s error=%s", user_id, exc
            )
            raise DatabaseError("Failed to revoke all tokens for user") from exc
