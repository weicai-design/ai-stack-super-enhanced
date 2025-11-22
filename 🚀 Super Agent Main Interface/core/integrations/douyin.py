"""
抖音集成（最小可用版）

功能：
- 授权流程（state校验 + token模拟）
- 发布任务管理（风险评分 / 失败重试 / 状态同步）
- 回调记录（Webhook占位）
"""
from __future__ import annotations

import logging
import os
import random
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse

import httpx

from .api_monitor import APIMonitor

logger = logging.getLogger(__name__)


@dataclass
class DouyinAuthState:
    access_token: Optional[str]
    expires_at: Optional[datetime]
    refresh_token: Optional[str]
    scope: Optional[str]
    state: Optional[str] = None


@dataclass
class DouyinPublishJob:
    job_id: str
    title: str
    content: str
    tags: List[str]
    media_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    status: str = "queued"  # queued/publishing/success/failed/blocked
    attempts: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None
    compliance: Optional[Dict[str, Any]] = None
    risk: Optional[Dict[str, Any]] = None
    published_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class DouyinIntegration:
    def __init__(self, api_monitor: Optional[APIMonitor] = None):
        self._auth = DouyinAuthState(
            access_token=None,
            expires_at=None,
            refresh_token=None,
            scope=None,
            state=None
        )
        self._jobs: Dict[str, DouyinPublishJob] = {}
        self._callbacks: List[Dict[str, Any]] = []
        self.api_monitor = api_monitor or APIMonitor()

    # -------- 授权 & 状态 --------
    def get_status(self) -> Dict[str, Any]:
        authorized = self._auth.access_token is not None and (self._auth.expires_at or datetime.min) > datetime.now()
        return {
            "authorized": authorized,
            "expires_at": self._auth.expires_at.isoformat() if self._auth.expires_at else None,
            "scope": self._auth.scope,
            "pending_state": self._auth.state,
            "active_jobs": len([j for j in self._jobs.values() if j.status in {"queued", "publishing"}]),
            "failed_jobs": len([j for j in self._jobs.values() if j.status in {"failed", "blocked"}])
        }

    def begin_auth(self) -> Dict[str, Any]:
        """
        启动 OAuth：生成 state 供前端引导用户跳转抖音授权
        真实实现：支持抖音开放平台 OAuth 2.0 授权流程
        """
        import os
        state = uuid.uuid4().hex
        
        # 从环境变量获取配置（真实环境）
        client_id = os.getenv("DOUYIN_CLIENT_ID", "your_client_id")
        redirect_uri = os.getenv("DOUYIN_REDIRECT_URI", "http://localhost:8000/api/super-agent/douyin/callback")
        scope = os.getenv("DOUYIN_SCOPE", "video.create,video.data")
        
        # 构建抖音 OAuth 授权 URL
        # 真实抖音开放平台 OAuth URL 格式
        auth_url = (
            f"https://open.douyin.com/platform/oauth/connect?"
            f"client_key={client_id}&"
            f"response_type=code&"
            f"scope={scope}&"
            f"redirect_uri={redirect_uri}&"
            f"state={state}"
        )
        
        self._auth.state = state
        return {
            "success": True,
            "auth_url": auth_url,
            "state": state,
            "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat(),
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope
        }

    def complete_auth(self, code: str, state: str) -> Dict[str, Any]:
        """
        完成 OAuth 授权
        真实实现：调用抖音开放平台 API 交换 access_token
        """
        if not self._auth.state or state != self._auth.state:
            return {"success": False, "error": "state 不匹配或已过期"}
        if not code:
            return {"success": False, "error": "缺少授权code"}
        
        import os
        
        # 真实实现：调用抖音开放平台 token 接口
        client_id = os.getenv("DOUYIN_CLIENT_ID", "your_client_id")
        client_secret = os.getenv("DOUYIN_CLIENT_SECRET", "your_client_secret")
        redirect_uri = os.getenv("DOUYIN_REDIRECT_URI", "http://localhost:8000/api/super-agent/douyin/callback")
        
        try:
            # 真实抖音 API 调用
            token_url = "https://open.douyin.com/oauth/access_token/"
            token_data = {
                "client_key": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code"
            }
            
            # 如果配置了真实密钥，尝试真实调用；否则使用模拟
            if client_id != "your_client_id" and client_secret != "your_client_secret":
                resp_json, error = self._call_api(
                    method="POST",
                    url=token_url,
                    system="douyin",
                    payload=token_data,
                )
                if resp_json and resp_json.get("data"):
                    data = resp_json["data"]
                    self._auth.access_token = data.get("access_token")
                    self._auth.refresh_token = data.get("refresh_token")
                    expires_in = data.get("expires_in", 7200)
                    self._auth.expires_at = datetime.now() + timedelta(seconds=expires_in)
                    self._auth.scope = data.get("scope", "video.create,video.data")
                    self._auth.state = None
                    return {
                        "success": True,
                        "authorized": True,
                        "expires_at": self._auth.expires_at.isoformat(),
                        "scope": self._auth.scope,
                        "mode": "real",
                    }
                if error:
                    logger.warning("抖音真实API调用失败，使用模拟: %s", error)
            
            # 模拟模式（开发/测试环境）
            self._auth.access_token = f"mock_douyin_access_{uuid.uuid4().hex[:8]}"
            self._auth.refresh_token = f"mock_refresh_{uuid.uuid4().hex[:8]}"
            self._auth.scope = "video.create,video.data"
            self._auth.expires_at = datetime.now() + timedelta(hours=2)
            self._auth.state = None
            return {
                "success": True,
                "authorized": True,
                "expires_at": self._auth.expires_at.isoformat(),
                "scope": self._auth.scope,
                "mode": "mock"  # 标识为模拟模式
            }
        except Exception as e:
            return {"success": False, "error": f"授权完成失败: {str(e)}"}

    def revoke(self) -> Dict[str, Any]:
        self._auth = DouyinAuthState(access_token=None, expires_at=None, refresh_token=None, scope=None, state=None)
        return {"success": True}

    # -------- 风控 & 发布任务 --------
    def evaluate_risk(self, title: str, content: str, tags: List[str]) -> Dict[str, Any]:
        flags = []
        score = 0.15
        sensitive_keywords = ["违规", "封号", "低俗", "赌博", "博彩", "代购"]
        for kw in sensitive_keywords:
            if kw in title or kw in content:
                flags.append(f"命中敏感词：{kw}")
                score += 0.25
        if len(content) > 800:
            flags.append("内容超长（>800字）")
            score += 0.1
        if any(tag.lower().startswith("ad") for tag in tags):
            flags.append("命中广告标签")
            score += 0.1
        score = min(score, 0.95)
        if score >= 0.7:
            level = "high"
        elif score >= 0.4:
            level = "medium"
        else:
            level = "low"
        return {
            "score": round(score, 2),
            "level": level,
            "flags": flags,
            "suggestions": self._risk_suggestions(level, flags)
        }

    def submit_publication(
        self,
        title: str,
        content: str,
        tags: List[str],
        media_url: Optional[str],
        compliance: Optional[Dict[str, Any]],
        risk: Dict[str, Any]
    ) -> Dict[str, Any]:
        job_id = f"dy_job_{int(datetime.now().timestamp()*1000)}"
        job = DouyinPublishJob(
            job_id=job_id,
            title=title,
            content=content,
            tags=tags,
            media_url=media_url,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            compliance=compliance,
            risk=risk
        )
        job.attempts = 1
        self._jobs[job_id] = job
        self._process_job(job)
        return self._serialize_job(job)

    def retry_job(self, job_id: str) -> Dict[str, Any]:
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError("job_not_found")
        if job.attempts >= job.max_retries:
            raise ValueError("max_retries_reached")
        if job.status not in {"failed", "blocked"}:
            raise ValueError("job_not_in_retryable_state")
        job.status = "queued"
        job.last_error = None
        job.next_retry_at = None
        job.attempts += 1
        job.updated_at = datetime.now()
        self._process_job(job)
        return self._serialize_job(job)

    def list_jobs(self) -> List[Dict[str, Any]]:
        jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
        return [self._serialize_job(job) for job in jobs]

    def _process_job(self, job: DouyinPublishJob):
        status = self.get_status()
        if not status["authorized"]:
            job.status = "failed"
            job.last_error = "未授权"
            job.next_retry_at = datetime.now() + timedelta(minutes=5)
            job.updated_at = datetime.now()
            return
        if job.risk and job.risk.get("level") == "high":
            job.status = "blocked"
            job.last_error = "风控拦截：风险级别过高"
            job.next_retry_at = None
            job.updated_at = datetime.now()
            return
        job.status = "publishing"
        job.updated_at = datetime.now()

        used_real_api, error = self._try_real_publish(job)
        if used_real_api and not error:
            job.status = "success"
            job.published_at = datetime.now()
            job.last_error = None
            job.next_retry_at = None
            self._emit_callback(job, event="video.publish")
            job.updated_at = datetime.now()
            return

        if error:
            job.status = "failed"
            job.last_error = error
            job.next_retry_at = datetime.now() + timedelta(minutes=5)
            job.updated_at = datetime.now()
            return

        # 模拟模式：按照风险和关键字决定是否成功
        fail_keywords = ["fail", "失败", "违规"]
        hit_fail_kw = any(kw.lower() in job.title.lower() or kw.lower() in job.content.lower() for kw in fail_keywords)
        random_fail = random.random() < 0.2 and job.attempts == 1
        if hit_fail_kw or random_fail:
            job.status = "failed"
            job.last_error = "抖音API：内容审核未通过" if hit_fail_kw else "抖音API：网络波动"
            job.next_retry_at = datetime.now() + timedelta(minutes=5)
        else:
            job.status = "success"
            job.published_at = datetime.now()
            job.last_error = None
            job.next_retry_at = None
            self._emit_callback(job, event="video.publish")
        job.updated_at = datetime.now()

    def _risk_suggestions(self, level: str, flags: List[str]) -> List[str]:
        if level == "high":
            return ["⚠️ 风险过高：请修改文案/标签后再试"] + flags
        if level == "medium":
            return ["⚠️ 中等风险：建议复核敏感词"] + flags
        return ["✅ 风险较低，可继续发布"]

    def _serialize_job(self, job: DouyinPublishJob) -> Dict[str, Any]:
        data = asdict(job)
        data["created_at"] = job.created_at.isoformat()
        data["updated_at"] = job.updated_at.isoformat()
        if job.published_at:
            data["published_at"] = job.published_at.isoformat()
        if job.next_retry_at:
            data["next_retry_at"] = job.next_retry_at.isoformat()
        return data

    # -------- 回调 & Webhook --------
    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(payload or {})
        payload["received_at"] = datetime.now().isoformat()
        self._callbacks.append(payload)
        self._callbacks = self._callbacks[-50:]
        job_id = payload.get("job_id")
        new_status = payload.get("status")
        if job_id and new_status and job_id in self._jobs:
            job = self._jobs[job_id]
            job.status = new_status
            job.updated_at = datetime.now()
            if new_status == "success":
                job.published_at = datetime.now()
            if payload.get("error"):
                job.last_error = payload["error"]
        return payload

    def list_callbacks(self) -> List[Dict[str, Any]]:
        return list(reversed(self._callbacks))

    def _emit_callback(self, job: DouyinPublishJob, event: str):
        payload = {
            "event": event,
            "job_id": job.job_id,
            "status": job.status,
            "published_at": job.published_at.isoformat() if job.published_at else None,
            "timestamp": datetime.now().isoformat()
        }
        self._callbacks.append(payload)
        self._callbacks = self._callbacks[-50:]

    async def create_draft(self, title: str, content: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        兼容旧版草稿创建接口，仍可用于快速测试。
        """
        if not self.get_status()["authorized"]:
            return {"success": False, "error": "未授权或Token已过期"}
        draft_id = f"dy_draft_{int(datetime.now().timestamp())}"
        draft = {
            "success": True,
            "draft_id": draft_id,
            "title": title,
            "tags": tags or [],
            "created_at": datetime.now().isoformat()
        }
        # 将草稿视作一个未发布任务记录
        self._callbacks.append({
            "event": "draft.created",
            "draft_id": draft_id,
            "timestamp": datetime.now().isoformat()
        })
        self._callbacks = self._callbacks[-50:]
        return draft

    # -------- 内部：真实调用 & 监控 --------
    def _call_api(
        self,
        *,
        method: str,
        url: str,
        system: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        start = time.perf_counter()
        status_code = None
        success = False
        error = None
        response_json: Optional[Dict[str, Any]] = None
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.request(method.upper(), url, json=payload, headers=headers)
                status_code = resp.status_code
                resp.raise_for_status()
                response_json = resp.json()
                success = True
                return response_json, None
        except Exception as exc:  # pragma: no cover
            error = str(exc)
            return None, error
        finally:
            duration = (time.perf_counter() - start) * 1000
            endpoint = urlparse(url).path
            self.api_monitor.record_call(
                system=system,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                success=success,
                duration_ms=duration,
                error=error,
                metadata={"payload_keys": list((payload or {}).keys())},
            )

    def _try_real_publish(self, job: DouyinPublishJob) -> Tuple[bool, Optional[str]]:
        """
        如果环境变量开启真实模式，则调用 Douyin API 发布文本/图文内容。
        返回 (是否尝试真实调用, 错误信息)
        """
        real_mode = os.getenv("DOUYIN_REAL_MODE", "0") == "1"
        if not real_mode or not self._auth.access_token:
            return False, None

        publish_url = os.getenv(
            "DOUYIN_PUBLISH_URL",
            "https://open.douyin.com/api/douyin/v1/video/text/create/",
        )
        headers = {"access-token": self._auth.access_token}
        payload = {
            "text": job.content,
            "title": job.title,
            "tags": job.tags,
            "risk_level": job.risk.get("level") if job.risk else "low",
        }
        resp_json, error = self._call_api(
            method="POST",
            url=publish_url,
            system="douyin",
            payload=payload,
            headers=headers,
        )
        if error:
            return True, error
        data = resp_json.get("data") if resp_json else {}
        if data and data.get("publish_id"):
            job.metadata = {"publish_id": data["publish_id"]} if hasattr(job, "metadata") else None
            return True, None
        return True, "抖音API：未返回 publish_id"

