"""
安全模块 - OAuth2认证测试
"""

import pytest
from common.security import oauth2_auth


@pytest.mark.security
@pytest.mark.unit
class TestOAuth2Authentication:
    """OAuth2认证测试"""
    
    def test_password_hashing(self):
        """测试：密码哈希"""
        password = "test_password_123"
        hashed = oauth2_auth.get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 20
    
    def test_password_verification(self):
        """测试：密码验证"""
        password = "test_password_123"
        hashed = oauth2_auth.get_password_hash(password)
        
        # 正确密码
        assert oauth2_auth.verify_password(password, hashed)
        
        # 错误密码
        assert not oauth2_auth.verify_password("wrong_password", hashed)
    
    def test_create_access_token(self):
        """测试：创建访问Token"""
        data = {"sub": "test_user"}
        token = oauth2_auth.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 20
    
    def test_create_refresh_token(self):
        """测试：创建刷新Token"""
        data = {"sub": "test_user"}
        token = oauth2_auth.create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 20
    
    def test_decode_token(self):
        """测试：解码Token"""
        data = {"sub": "test_user", "scopes": ["read", "write"]}
        token = oauth2_auth.create_access_token(data)
        
        token_data = oauth2_auth.decode_token(token)
        
        assert token_data.username == "test_user"
        assert "read" in token_data.scopes
    
    def test_token_expiration(self):
        """测试：Token过期"""
        from datetime import timedelta
        
        data = {"sub": "test_user"}
        # 创建一个立即过期的token
        token = oauth2_auth.create_access_token(
            data,
            expires_delta=timedelta(seconds=-1)
        )
        
        # 解码应该失败
        with pytest.raises(Exception):
            oauth2_auth.decode_token(token)

