#!/usr/bin/env python3
"""
初始化RSA密钥对的脚本
用于生成加密用户密码所需的公钥和私钥
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径，以便导入项目模块
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes

# 密钥文件路径
KEYS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "keys"))
PRIVATE_KEY_PATH = os.path.join(KEYS_DIR, "private_key.pem")
PUBLIC_KEY_PATH = os.path.join(KEYS_DIR, "public_key.pem")

def generate_keys():
    """生成RSA密钥对并保存到文件"""
    # 确保密钥目录存在
    os.makedirs(KEYS_DIR, exist_ok=True)
    
    # 检查密钥文件是否已存在
    if os.path.exists(PRIVATE_KEY_PATH) and os.path.exists(PUBLIC_KEY_PATH):
        print("密钥文件已存在，跳过生成。")
        return
    
    # 生成新的密钥对
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # 获取公钥
    public_key = private_key.public_key()
    
    # 保存私钥（PKCS8格式）
    with open(PRIVATE_KEY_PATH, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # 保存公钥（SubjectPublicKeyInfo格式）
    with open(PUBLIC_KEY_PATH, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    
    print(f"RSA密钥对已生成:")
    print(f"私钥: {PRIVATE_KEY_PATH}")
    print(f"公钥: {PUBLIC_KEY_PATH}")

if __name__ == "__main__":
    generate_keys()