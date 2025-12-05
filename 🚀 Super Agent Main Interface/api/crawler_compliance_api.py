#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫合规API（生产级实现）
5.2: 提供验证码挑战和口令验证接口
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Body, status
from pydantic import BaseModel

from core.security.crawler_compliance import get_crawler_compliance_service

router = APIRouter(prefix="/api/crawler", tags=["Crawler Compliance"])


class CrawlerEvaluationRequest(BaseModel):
    """爬虫评估请求"""
    user_agent: Optional[str] = None
    path: str
    client_ip: Optional[str] = None
    password: Optional[str] = None
    captcha_challenge_id: Optional[str] = None
    captcha_answer: Optional[str] = None


class PasswordVerificationRequest(BaseModel):
    """口令验证请求"""
    password: str


@router.post("/evaluate")
async def evaluate_crawler(request: CrawlerEvaluationRequest):
    """
    评估爬虫请求（5.2扩展：支持口令和验证码）
    
    如果启用口令或验证码，会在响应中返回相应的要求
    """
    crawler_service = get_crawler_compliance_service()
    
    result = crawler_service.evaluate(
        user_agent=request.user_agent,
        path=request.path,
        client_ip=request.client_ip,
        password=request.password,
        captcha_challenge_id=request.captcha_challenge_id,
        captcha_answer=request.captcha_answer,
    )
    
    return {
        "success": result["allowed"],
        "result": result,
    }


@router.post("/captcha/create")
async def create_captcha_challenge():
    """
    创建验证码挑战（5.2新增）
    
    返回验证码挑战信息，客户端需要回答验证码问题
    """
    crawler_service = get_crawler_compliance_service()
    
    challenge = crawler_service.create_captcha_challenge()
    
    return {
        "success": True,
        "challenge": challenge,
    }


@router.post("/password/verify")
async def verify_password(request: PasswordVerificationRequest):
    """
    验证口令（5.2新增）
    
    验证提供的口令是否正确
    """
    crawler_service = get_crawler_compliance_service()
    
    is_valid = crawler_service.verify_password(request.password)
    
    return {
        "success": is_valid,
        "message": "口令验证通过" if is_valid else "口令验证失败",
    }


__all__ = ["router"]

