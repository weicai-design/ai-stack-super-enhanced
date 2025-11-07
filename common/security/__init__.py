"""
安全模块
"""

from .oauth2_auth import (
    oauth2_scheme,
    get_current_user,
    get_current_active_user,
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    check_permission,
    require_permission,
    rbac
)

from .data_encryption import (
    encryptor,
    mask,
    encrypt_sensitive_data,
    decrypt_sensitive_data,
    mask_sensitive_info,
    DataEncryption,
    SensitiveDataMask
)

__all__ = [
    # OAuth2
    'oauth2_scheme',
    'get_current_user',
    'get_current_active_user',
    'create_access_token',
    'create_refresh_token',
    'verify_password',
    'get_password_hash',
    'check_permission',
    'require_permission',
    'rbac',
    
    # Encryption
    'encryptor',
    'mask',
    'encrypt_sensitive_data',
    'decrypt_sensitive_data',
    'mask_sensitive_info',
    'DataEncryption',
    'SensitiveDataMask',
]

