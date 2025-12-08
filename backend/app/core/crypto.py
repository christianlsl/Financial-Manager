import os
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

# 密钥文件路径
KEYS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "keys"))
PRIVATE_KEY_PATH = os.path.join(KEYS_DIR, "private_key.pem")
PUBLIC_KEY_PATH = os.path.join(KEYS_DIR, "public_key.pem")

# 确保密钥目录存在
os.makedirs(KEYS_DIR, exist_ok=True)

def _load_or_generate_keys():
    """加载现有密钥或生成新密钥对"""
    # 如果密钥文件已存在，则加载它们
    if os.path.exists(PRIVATE_KEY_PATH) and os.path.exists(PUBLIC_KEY_PATH):
        try:
            with open(PRIVATE_KEY_PATH, "rb") as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                )
            
            with open(PUBLIC_KEY_PATH, "rb") as f:
                public_key_pem = f.read().decode("utf-8")
                
            return private_key, public_key_pem
        except Exception:
            # 如果加载失败，继续生成新密钥
            pass
    
    # 生成新的密钥对
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )
    
    # 保存密钥到文件
    try:
        with open(PRIVATE_KEY_PATH, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
        with open(PUBLIC_KEY_PATH, "w") as f:
            f.write(public_key_pem)
    except Exception:
        # 如果保存失败，至少返回内存中的密钥
        pass
    
    return private_key, public_key_pem

# 加载或生成密钥对
_private_key, _public_key_pem = _load_or_generate_keys()

def get_public_key_pem() -> str:
    """Return PEM-encoded public key for clients to encrypt passwords.

    Uses RSA-PKCS1v15 padding for compatibility with jsencrypt library.
    This works in both HTTP and HTTPS environments.
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
    """Decrypt a base64/base64url RSA-PKCS1v15 ciphertext into UTF-8 password.
    
    Supports jsencrypt library which uses RSA-PKCS1v15 padding.
    """
    ciphertext = _b64_any_decode(enc_b64)
    plaintext = _private_key.decrypt(
        ciphertext,
        padding.PKCS1v15(),
    )
    return plaintext.decode("utf-8")