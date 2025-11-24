from datetime import datetime, timedelta
from typing import Optional

import base64
from jose import jwt
from .config import settings
from pwdlib import PasswordHash

# Import crypto functions
from .crypto import get_public_key_pem, decrypt_password

password_hash = PasswordHash.recommended()

# # Use PBKDF2-SHA256 to avoid external bcrypt backend issues
# pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = settings.ACCESS_TOKEN_EXPIRE_DELTA
    expire = datetime.utcnow() + expires_delta
    to_encode = {"exp": expire, "sub": subject}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)
