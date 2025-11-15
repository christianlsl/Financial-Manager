from datetime import datetime, timedelta
from typing import Optional

import base64
from jose import jwt
from .config import settings
from pwdlib import PasswordHash

# RSA crypto for client-side password encryption
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

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


# ---- RSA helpers for encrypted credentials ----
_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_public_key_pem = (
    _private_key.public_key()
    .public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    .decode("utf-8")
)


def get_public_key_pem() -> str:
    """Return PEM-encoded public key for clients to encrypt passwords.

    Uses RSA-OAEP with SHA-256 (RSA-OAEP-256) on the client.
    """
    return _public_key_pem


def _b64_any_decode(data: str) -> bytes:
    # Try standard Base64 first
    try:
        return base64.b64decode(data, validate=True)
    except Exception:
        # Fallback to URL-safe base64 with padding fix
        s = data + "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(s)


def decrypt_password(enc_b64: str) -> str:
    """Decrypt a base64/base64url RSA-OAEP-256 ciphertext into UTF-8 password."""
    ciphertext = _b64_any_decode(enc_b64)
    plaintext = _private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return plaintext.decode("utf-8")
