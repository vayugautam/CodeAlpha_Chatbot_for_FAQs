import pytest

from app.security import create_access_token, decode_access_token, hash_password, verify_password
from uuid import uuid4


def test_password_hashing_and_jwt_round_trip(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret-key-that-is-at-least-32-characters-long")
    password = "correct horse battery staple"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong password", hashed)
    user_id = uuid4()
    assert decode_access_token(create_access_token(user_id)) == user_id


def test_jwt_requires_a_strong_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "short")
    with pytest.raises(RuntimeError, match="32 characters"):
        create_access_token(uuid4())
