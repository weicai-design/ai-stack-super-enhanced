"""
数据加密模块
提供数据加密和解密功能
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import os
import hashlib
import secrets


class DataEncryption:
    """数据加密类"""
    
    def __init__(self, secret_key: str = None):
        """初始化加密器
        
        Args:
            secret_key: 加密密钥（建议从环境变量获取）
        """
        if secret_key is None:
            secret_key = os.getenv("ENCRYPTION_SECRET_KEY", "default-secret-key")
        
        self.secret_key = secret_key
        self.cipher = self._create_cipher(secret_key)
    
    def _create_cipher(self, secret_key: str) -> Fernet:
        """创建Fernet加密器"""
        # 使用PBKDF2从密钥派生
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'ai-stack-salt',
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(
            kdf.derive(secret_key.encode())
        )
        
        return Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """加密数据
        
        Args:
            data: 明文数据
            
        Returns:
            加密后的数据（Base64编码）
        """
        if not data:
            return data
        
        encrypted = self.cipher.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据
        
        Args:
            encrypted_data: 加密数据
            
        Returns:
            解密后的明文
        """
        if not encrypted_data:
            return encrypted_data
        
        try:
            decrypted = self.cipher.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"解密失败: {e}")
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple:
        """密码哈希
        
        Args:
            password: 明文密码
            salt: 盐值（可选，自动生成）
            
        Returns:
            (哈希值, 盐值)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # 使用PBKDF2进行密码哈希
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
            backend=default_backend()
        )
        
        hashed = kdf.derive(password.encode())
        return base64.b64encode(hashed).decode(), salt
    
    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: str) -> bool:
        """验证密码
        
        Args:
            password: 明文密码
            hashed_password: 哈希密码
            salt: 盐值
            
        Returns:
            验证结果
        """
        try:
            new_hash, _ = DataEncryption.hash_password(password, salt)
            return new_hash == hashed_password
        except:
            return False
    
    @staticmethod
    def generate_api_key() -> str:
        """生成API Key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """哈希API Key（用于存储）"""
        return hashlib.sha256(api_key.encode()).hexdigest()


class SensitiveDataMask:
    """敏感数据脱敏"""
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """手机号脱敏"""
        if not phone or len(phone) < 11:
            return phone
        return f"{phone[:3]}****{phone[-4:]}"
    
    @staticmethod
    def mask_email(email: str) -> str:
        """邮箱脱敏"""
        if not email or '@' not in email:
            return email
        
        username, domain = email.split('@')
        if len(username) <= 2:
            masked_username = username[0] + '*'
        else:
            masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
        
        return f"{masked_username}@{domain}"
    
    @staticmethod
    def mask_id_card(id_card: str) -> str:
        """身份证号脱敏"""
        if not id_card or len(id_card) < 18:
            return id_card
        return f"{id_card[:6]}********{id_card[-4:]}"
    
    @staticmethod
    def mask_bank_card(card_number: str) -> str:
        """银行卡号脱敏"""
        if not card_number or len(card_number) < 16:
            return card_number
        return f"{card_number[:4]} **** **** {card_number[-4:]}"
    
    @staticmethod
    def mask_custom(data: str, keep_start: int = 2, keep_end: int = 2) -> str:
        """自定义脱敏"""
        if not data or len(data) <= keep_start + keep_end:
            return data
        
        masked_length = len(data) - keep_start - keep_end
        return f"{data[:keep_start]}{'*' * masked_length}{data[-keep_end:]}"


# ==================== 全局实例 ====================

encryptor = DataEncryption()
mask = SensitiveDataMask()


# ==================== 便捷函数 ====================

def encrypt_sensitive_data(data: str) -> str:
    """加密敏感数据"""
    return encryptor.encrypt(data)


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """解密敏感数据"""
    return encryptor.decrypt(encrypted_data)


def mask_sensitive_info(info_type: str, data: str) -> str:
    """根据类型脱敏"""
    mask_functions = {
        "phone": mask.mask_phone,
        "email": mask.mask_email,
        "id_card": mask.mask_id_card,
        "bank_card": mask.mask_bank_card,
    }
    
    mask_func = mask_functions.get(info_type, mask.mask_custom)
    return mask_func(data)

