from typing import Literal

# Token types
ACCESS_TOKEN_TYPE: Literal["access"] = "access"
REFRESH_TOKEN_TYPE: Literal["refresh"] = "refresh"

# Auth header
BEARER_PREFIX = "Bearer"

# Password policy
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# User status
ACTIVE_STATUS = "active"
INACTIVE_STATUS = "inactive"
