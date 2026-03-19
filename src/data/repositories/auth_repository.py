# auth_repository.py — backward-compatibility shim
# Repositories have been split into role_repository.py, user_repository.py,
# and token_repository.py. This re-exports all three so existing imports work.
from .role_repository import RoleRepository
from .token_repository import RefreshTokenRepository
from .user_repository import UserRepository

__all__ = ["RoleRepository", "UserRepository", "RefreshTokenRepository"]
