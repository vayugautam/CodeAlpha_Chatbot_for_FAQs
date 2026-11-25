import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()
_dummy_hash = _password_hash.hash("not-a-real-user-password")


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, hashed: str | None) -> bool:
    valid = _password_hash.verify(password, hashed or _dummy_hash)
    return valid and hashed is not None


def create_access_token(subject: UUID) -> str:
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET must contain at least 32 characters")
    mins = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(subject), "iat": now, "exp": now + timedelta(minutes=mins)}, secret, algorithm="HS256")


def decode_access_token(token: str) -> UUID:
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET must contain at least 32 characters")
    return UUID(jwt.decode(token, secret, algorithms=["HS256"], options={"require": ["sub", "exp"]})["sub"])
