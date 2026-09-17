# -*- coding: utf-8 -*-
"""
极简鉴权与安全会话管理模块 (Auth & Session Manager)
原则：KISS 极简至上，避免复杂外部依赖，内置安全加盐 SHA-256 与 Token 会话
"""

import os
import time
import secrets
import hashlib
from typing import Optional, Dict, Tuple
from core.db import DatabaseManager
from config.settings import logger

TOKEN_EXPIRE_SECONDS = 7 * 24 * 3600  # 会话有效期 7 天

class AuthManager:
    """认证与会话管理器"""

    @staticmethod
    def _hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """对密码进行加盐哈希"""
        if not salt:
            salt = secrets.token_hex(16)
        salted_str = f"{salt}:{password}".encode("utf-8")
        pwd_hash = hashlib.sha256(salted_str).hexdigest()
        return pwd_hash, salt

    @classmethod
    def get_or_init_credentials(cls) -> Tuple[str, str]:
        """获取或初始化系统账号与密码哈希"""
        db = DatabaseManager()
        stored_hash = db.get_config("auth_admin_password_hash", "")
        stored_salt = db.get_config("auth_admin_salt", "")

        if not stored_hash or not stored_salt:
            # 首次初始化：优先读取环境变量，默认 admin888
            initial_password = os.environ.get("AUTH_PASSWORD", "admin888")
            pwd_hash, salt = cls._hash_password(initial_password)
            db.set_config("auth_admin_password_hash", pwd_hash)
            db.set_config("auth_admin_salt", salt)
            db.set_config("auth_admin_username", "admin")
            logger.info(f"[AuthManager]: 系统管理员账号初始完成: admin (口令已安全加盐加密)")
            return pwd_hash, salt

        return stored_hash, stored_salt

    @classmethod
    def verify_password(cls, password: str) -> bool:
        """校验输入的密码是否正确"""
        if not password:
            return False
        stored_hash, stored_salt = cls.get_or_init_credentials()
        input_hash, _ = cls._hash_password(password, stored_salt)
        return secrets.compare_digest(stored_hash, input_hash)

    @classmethod
    def change_password(cls, old_pwd: str, new_pwd: str) -> Tuple[bool, str]:
        """修改管理员密码"""
        if not cls.verify_password(old_pwd):
            return False, "旧密码不正确，请重新输入"
        if not new_pwd or len(new_pwd.strip()) < 4:
            return False, "新密码长度不能少于 4 位"
        
        pwd_hash, salt = cls._hash_password(new_pwd.strip())
        db = DatabaseManager()
        db.set_config("auth_admin_password_hash", pwd_hash)
        db.set_config("auth_admin_salt", salt)
        logger.info("[AuthManager]: 系统管理员密码已成功更新")
        return True, "密码修改成功，请重新登录"

    @classmethod
    def create_session(cls) -> str:
        """为通过校验的用户创建 7 天长效安全 Token"""
        token = secrets.token_hex(32)
        expire_at = int(time.time()) + TOKEN_EXPIRE_SECONDS
        session_val = f"{expire_at}"
        db = DatabaseManager()
        db.set_config(f"session:{token}", session_val)
        return token

    @classmethod
    def validate_token(cls, token: Optional[str]) -> bool:
        """验证 Token 有效性与是否过期"""
        if not token:
            return False
        token = token.strip()
        db = DatabaseManager()
        session_val = db.get_config(f"session:{token}", "")
        if not session_val:
            return False
        
        try:
            expire_at = int(session_val)
            if time.time() > expire_at:
                db.set_config(f"session:{token}", "")  # 过期清理
                return False
            return True
        except Exception:
            return False

    @classmethod
    def revoke_token(cls, token: Optional[str]) -> bool:
        """注销 Token"""
        if not token:
            return True
        token = token.strip()
        db = DatabaseManager()
        db.set_config(f"session:{token}", "")
        return True
