from __future__ import annotations

import json
import threading
import time
import hashlib
import hmac
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta


@dataclass
class CrawlerPolicy:
    allowed_agents: tuple[str, ...]
    blocked_agents: tuple[str, ...]
    allowed_paths: tuple[str, ...]
    blocked_paths: tuple[str, ...]
    rate_limit_per_minute: int
    require_password: bool = False  # 是否需要口令验证
    require_captcha: bool = False  # 是否需要验证码
    password_hash: Optional[str] = None  # 口令哈希（如果启用）
    captcha_secret: Optional[str] = None  # 验证码密钥（如果启用）


@dataclass
class CaptchaChallenge:
    """验证码挑战"""
    challenge_id: str
    question: str
    answer_hash: str  # 答案的哈希值
    expires_at: datetime
    attempts: int = 0
    max_attempts: int = 3


class CrawlerComplianceService:
    """
    爬虫合规检查服务（生产级实现）
    
    功能：
    1. 爬虫识别和阻止
    2. 速率限制
    3. 口令验证（5.2新增）
    4. 验证码验证（5.2新增）
    """

    def __init__(
        self,
        policy_path: Optional[Path] = None,
        default_policy: Optional[CrawlerPolicy] = None,
    ):
        self.policy_path = policy_path or Path("config/compliance/crawler_policy.json")
        self._policy = default_policy or CrawlerPolicy(
            allowed_agents=("Googlebot", "Bingbot", "Bytespider"),
            blocked_agents=("sqlmap", "nikto", "dirbuster"),
            allowed_paths=("/docs", "/sitemaps", "/robots.txt"),
            blocked_paths=("/admin", "/security", "/api/secure"),
            rate_limit_per_minute=60,
            require_password=False,
            require_captcha=False,
        )
        self._rate_cache: Dict[str, list[float]] = {}
        self._lock = threading.Lock()
        
        # 验证码挑战存储（5.2新增）
        self._captcha_challenges: Dict[str, CaptchaChallenge] = {}
        self._captcha_lock = threading.Lock()
        
        # 口令验证回调（5.2新增）
        self._password_verifier: Optional[Callable[[str], bool]] = None
        
        # 验证码生成器（5.2新增）
        self._captcha_generator: Optional[Callable[[], tuple[str, str]]] = None
        
        self._load_policy()

    def _load_policy(self) -> None:
        if not self.policy_path.exists():
            return
        try:
            data = json.loads(self.policy_path.read_text(encoding="utf-8"))
            self._policy = CrawlerPolicy(
                allowed_agents=tuple(data.get("allowed_agents", self._policy.allowed_agents)),
                blocked_agents=tuple(data.get("blocked_agents", self._policy.blocked_agents)),
                allowed_paths=tuple(data.get("allowed_paths", self._policy.allowed_paths)),
                blocked_paths=tuple(data.get("blocked_paths", self._policy.blocked_paths)),
                rate_limit_per_minute=int(data.get("rate_limit_per_minute", self._policy.rate_limit_per_minute)),
                require_password=bool(data.get("require_password", self._policy.require_password)),
                require_captcha=bool(data.get("require_captcha", self._policy.require_captcha)),
                password_hash=data.get("password_hash"),
                captcha_secret=data.get("captcha_secret"),
            )
        except Exception:
            # 默认策略
            pass
    
    def set_password_verifier(self, verifier: Callable[[str], bool]):
        """
        设置口令验证器（5.2新增）
        
        Args:
            verifier: 验证函数，接收口令字符串，返回是否验证通过
        """
        self._password_verifier = verifier
    
    def set_captcha_generator(self, generator: Callable[[], tuple[str, str]]):
        """
        设置验证码生成器（5.2新增）
        
        Args:
            generator: 生成函数，返回(问题, 答案)元组
        """
        self._captcha_generator = generator

    def evaluate(
        self,
        user_agent: str | None,
        path: str,
        client_ip: str | None,
        password: Optional[str] = None,
        captcha_challenge_id: Optional[str] = None,
        captcha_answer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        评估爬虫请求（生产级实现 - 5.2扩展）
        
        Args:
            user_agent: User Agent
            path: 请求路径
            client_ip: 客户端IP
            password: 口令（如果启用口令验证）
            captcha_challenge_id: 验证码挑战ID（如果启用验证码）
            captcha_answer: 验证码答案（如果启用验证码）
            
        Returns:
            评估结果
        """
        agent = (user_agent or "").lower()
        result = {
            "allowed": True,
            "reasons": [],
            "user_agent": user_agent,
            "path": path,
            "require_password": False,
            "require_captcha": False,
            "captcha_challenge": None,
        }

        if not agent:
            return result

        # 黑名单
        for blocked in self._policy.blocked_agents:
            if blocked.lower() in agent:
                result["allowed"] = False
                result["reasons"].append(f"blocked_agent:{blocked}")
                return result

        # 白名单路径
        for blocked_path in self._policy.blocked_paths:
            if path.startswith(blocked_path):
                result["allowed"] = False
                result["reasons"].append(f"blocked_path:{blocked_path}")
                return result

        # 速率限制
        if client_ip:
            now = time.time()
            with self._lock:
                history = self._rate_cache.setdefault(client_ip, [])
                history.append(now)
                self._rate_cache[client_ip] = [t for t in history if t > now - 60]
                if len(self._rate_cache[client_ip]) > self._policy.rate_limit_per_minute:
                    result["allowed"] = False
                    result["reasons"].append("rate_limit_exceeded")
                    return result

        # 口令验证（5.2新增）
        if self._policy.require_password:
            result["require_password"] = True
            if not password:
                result["allowed"] = False
                result["reasons"].append("password_required")
                return result
            
            # 验证口令
            if self._password_verifier:
                if not self._password_verifier(password):
                    result["allowed"] = False
                    result["reasons"].append("password_invalid")
                    return result
            elif self._policy.password_hash:
                # 使用存储的哈希值验证
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                if not hmac.compare_digest(password_hash, self._policy.password_hash):
                    result["allowed"] = False
                    result["reasons"].append("password_invalid")
                    return result

        # 验证码验证（5.2新增）
        if self._policy.require_captcha:
            result["require_captcha"] = True
            
            if not captcha_challenge_id or not captcha_answer:
                # 生成新的验证码挑战
                challenge = self._generate_captcha_challenge()
                result["captcha_challenge"] = {
                    "challenge_id": challenge.challenge_id,
                    "question": challenge.question,
                    "expires_at": challenge.expires_at.isoformat(),
                }
                result["allowed"] = False
                result["reasons"].append("captcha_required")
                return result
            
            # 验证验证码答案
            if not self._verify_captcha(captcha_challenge_id, captcha_answer):
                result["allowed"] = False
                result["reasons"].append("captcha_invalid")
                return result

        return result
    
    def _generate_captcha_challenge(self) -> CaptchaChallenge:
        """
        生成验证码挑战（5.2新增）
        
        Returns:
            验证码挑战对象
        """
        challenge_id = secrets.token_urlsafe(16)
        
        if self._captcha_generator:
            question, answer = self._captcha_generator()
        else:
            # 默认简单数学题
            import random
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            question = f"{a} + {b} = ?"
            answer = str(a + b)
        
        # 计算答案哈希
        answer_hash = hashlib.sha256(answer.encode()).hexdigest()
        
        challenge = CaptchaChallenge(
            challenge_id=challenge_id,
            question=question,
            answer_hash=answer_hash,
            expires_at=datetime.now() + timedelta(minutes=5),
        )
        
        with self._captcha_lock:
            self._captcha_challenges[challenge_id] = challenge
        
        return challenge
    
    def _verify_captcha(self, challenge_id: str, answer: str) -> bool:
        """
        验证验证码答案（5.2新增）
        
        Args:
            challenge_id: 挑战ID
            answer: 答案
            
        Returns:
            是否验证通过
        """
        with self._captcha_lock:
            challenge = self._captcha_challenges.get(challenge_id)
            
            if not challenge:
                return False
            
            # 检查是否过期
            if datetime.now() > challenge.expires_at:
                del self._captcha_challenges[challenge_id]
                return False
            
            # 检查尝试次数
            if challenge.attempts >= challenge.max_attempts:
                del self._captcha_challenges[challenge_id]
                return False
            
            # 验证答案
            answer_hash = hashlib.sha256(answer.encode()).hexdigest()
            if hmac.compare_digest(answer_hash, challenge.answer_hash):
                # 验证成功，删除挑战
                del self._captcha_challenges[challenge_id]
                return True
            else:
                # 验证失败，增加尝试次数
                challenge.attempts += 1
                return False
    
    def create_captcha_challenge(self) -> Dict[str, Any]:
        """
        创建验证码挑战（5.2新增）
        
        Returns:
            挑战信息
        """
        challenge = self._generate_captcha_challenge()
        
        return {
            "challenge_id": challenge.challenge_id,
            "question": challenge.question,
            "expires_at": challenge.expires_at.isoformat(),
        }
    
    def verify_password(self, password: str) -> bool:
        """
        验证口令（5.2新增）
        
        Args:
            password: 口令
            
        Returns:
            是否验证通过
        """
        if not self._policy.require_password:
            return True
        
        if self._password_verifier:
            return self._password_verifier(password)
        
        if self._policy.password_hash:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            return hmac.compare_digest(password_hash, self._policy.password_hash)
        
        return False


_crawler_service: Optional[CrawlerComplianceService] = None


def get_crawler_compliance_service() -> CrawlerComplianceService:
    global _crawler_service
    if _crawler_service is None:
        _crawler_service = CrawlerComplianceService()
    return _crawler_service


