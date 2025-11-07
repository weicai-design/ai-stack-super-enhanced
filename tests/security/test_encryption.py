"""
安全模块 - 数据加密测试
"""

import pytest
from common.security.data_encryption import DataEncryption, SensitiveDataMask


@pytest.mark.security
@pytest.mark.unit
class TestDataEncryption:
    """数据加密测试"""
    
    @pytest.fixture
    def encryptor(self):
        return DataEncryption("test-secret-key")
    
    def test_encrypt_decrypt(self, encryptor):
        """测试：加密和解密"""
        original_data = "敏感数据123"
        
        # 加密
        encrypted = encryptor.encrypt(original_data)
        assert encrypted != original_data
        
        # 解密
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == original_data
    
    def test_encrypt_empty_string(self, encryptor):
        """测试：加密空字符串"""
        result = encryptor.encrypt("")
        assert result == ""
    
    def test_hash_password(self):
        """测试：密码哈希"""
        password = "test_password"
        hashed, salt = DataEncryption.hash_password(password)
        
        assert hashed != password
        assert len(salt) > 0
    
    def test_verify_password(self):
        """测试：验证密码"""
        password = "test_password"
        hashed, salt = DataEncryption.hash_password(password)
        
        # 正确密码
        assert DataEncryption.verify_password(password, hashed, salt)
        
        # 错误密码
        assert not DataEncryption.verify_password("wrong", hashed, salt)
    
    def test_generate_api_key(self):
        """测试：生成API Key"""
        key1 = DataEncryption.generate_api_key()
        key2 = DataEncryption.generate_api_key()
        
        assert len(key1) > 20
        assert key1 != key2
    
    def test_hash_api_key(self):
        """测试：哈希API Key"""
        api_key = "test_api_key_12345"
        hashed = DataEncryption.hash_api_key(api_key)
        
        assert hashed != api_key
        assert len(hashed) == 64  # SHA256


@pytest.mark.security
@pytest.mark.unit
class TestSensitiveDataMask:
    """敏感数据脱敏测试"""
    
    def test_mask_phone(self):
        """测试：手机号脱敏"""
        phone = "13800138000"
        masked = SensitiveDataMask.mask_phone(phone)
        
        assert masked == "138****8000"
        assert len(masked) == len(phone)
    
    def test_mask_email(self):
        """测试：邮箱脱敏"""
        email = "user@example.com"
        masked = SensitiveDataMask.mask_email(email)
        
        assert "@example.com" in masked
        assert "user" not in masked or "*" in masked
    
    def test_mask_id_card(self):
        """测试：身份证脱敏"""
        id_card = "110101199001011234"
        masked = SensitiveDataMask.mask_id_card(id_card)
        
        assert masked == "110101********1234"
    
    def test_mask_bank_card(self):
        """测试：银行卡脱敏"""
        card = "6222021234567890"
        masked = SensitiveDataMask.mask_bank_card(card)
        
        assert "6222" in masked
        assert "7890" in masked
        assert "****" in masked
    
    def test_mask_custom(self):
        """测试：自定义脱敏"""
        data = "sensitive_data_123"
        masked = SensitiveDataMask.mask_custom(data, keep_start=3, keep_end=3)
        
        assert masked.startswith("sen")
        assert masked.endswith("123")
        assert "*" in masked

