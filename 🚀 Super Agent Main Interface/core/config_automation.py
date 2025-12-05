#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1-005/P1-201 日常配置与部署自动化（扩展版）

提供统一的环境配置管理与部署流水线编排能力：
- 环境配置：读取 config/environments/*.yaml，生成 `.env.runtime`
- 部署自动化：根据 config/deploy_pipeline.yaml 执行或模拟部署步骤
- 扩展支持：npm、模型、外部 API、Sidecar、Docker、Service Register
- 历史记录：写入 artifacts/config 与 artifacts/deployments 便于闭环审计
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = PROJECT_ROOT.parent / "config"
ENV_DIR = CONFIG_ROOT / "environments"
PIPELINE_FILE = CONFIG_ROOT / "deploy_pipeline.yaml"
ARTIFACTS_ROOT = PROJECT_ROOT.parent / "artifacts"
ARTIFACTS_ROOT.mkdir(exist_ok=True)


def _utc_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


class EnvironmentConfigManager:
    """管理环境配置与生成运行所需 env 文件（扩展版：支持 npm、模型、外部 API）"""

    def __init__(
        self,
        profiles_dir: Path | None = None,
        output_env_path: Path | None = None,
        history_path: Path | None = None,
    ):
        self.profiles_dir = profiles_dir or ENV_DIR
        self.output_env_path = (
            output_env_path or CONFIG_ROOT / ".env.runtime"
        )
        history_dir = ARTIFACTS_ROOT / "config"
        history_dir.mkdir(parents=True, exist_ok=True)
        self.history_path = history_path or history_dir / "apply_history.jsonl"

    def list_profiles(self) -> List[Dict[str, Any]]:
        profiles = []
        for file in sorted(self.profiles_dir.glob("*.yaml")):
            with file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            profiles.append(
                {
                    "name": data.get("name") or file.stem,
                    "description": data.get("description"),
                    "services": data.get("services", {}),
                    "env": list((data.get("env") or {}).keys()),
                    "npm": data.get("npm", {}),
                    "models": data.get("models", {}),
                    "external_apis": data.get("external_apis", {}),
                    "deploy": data.get("deploy", {}),
                    "file": str(file),
                }
            )
        return profiles

    def load_profile(self, name: str) -> Dict[str, Any]:
        for file in self.profiles_dir.glob("*.yaml"):
            with file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            if data.get("name") == name or file.stem == name:
                return data
        raise FileNotFoundError(f"未找到配置 profile: {name}")

    def apply_profile(
        self,
        name: str,
        overrides: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        profile = self.load_profile(name)
        env_data = dict(profile.get("env") or {})
        if overrides:
            env_data.update({k: str(v) for k, v in overrides.items()})

        # 扩展：添加 npm、模型、外部 API 配置到环境变量
        npm_config = profile.get("npm", {})
        if npm_config:
            env_data["NPM_REGISTRY"] = npm_config.get("registry", "https://registry.npmjs.org/")
            env_data["NPM_TOKEN"] = npm_config.get("token", "")
            env_data["NPM_SCOPE"] = npm_config.get("scope", "")

        models_config = profile.get("models", {})
        if models_config:
            for key, value in models_config.items():
                env_data[f"MODEL_{key.upper()}"] = str(value)

        external_apis_config = profile.get("external_apis", {})
        if external_apis_config:
            for api_name, api_config in external_apis_config.items():
                for key, value in api_config.items():
                    env_data[f"{api_name.upper()}_{key.upper()}"] = str(value)

        lines = [f"# Generated at {_utc_now()} for profile {name}"]
        lines += [f"{key}={value}" for key, value in env_data.items()]
        self.output_env_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        record = {
            "timestamp": _utc_now(),
            "profile": name,
            "output": str(self.output_env_path),
            "overrides": overrides or {},
            "npm": npm_config,
            "models": models_config,
            "external_apis": external_apis_config,
        }
        with self.history_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(record, ensure_ascii=False) + "\n")
        return {"profile": profile, "output_file": str(self.output_env_path)}

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.history_path.exists():
            return []
        lines = self.history_path.read_text(encoding="utf-8").strip().splitlines()
        records = [json.loads(line) for line in lines if line.strip()]
        return list(reversed(records[-limit:]))


@dataclass
class PipelineStepResult:
    name: str
    status: str
    command: str
    detail: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


class DeploymentAutomation:
    """读取 YAML 流水线并执行或模拟部署步骤（扩展版：支持 Sidecar、Docker、Service Register）"""

    def __init__(
        self,
        pipeline_path: Path | None = None,
        history_dir: Path | None = None,
        config_manager: Optional[EnvironmentConfigManager] = None,
    ):
        self.pipeline_path = pipeline_path or PIPELINE_FILE
        if not self.pipeline_path.exists():
            raise FileNotFoundError(f"缺少部署流水线配置: {self.pipeline_path}")
        self.pipeline = yaml.safe_load(self.pipeline_path.read_text(encoding="utf-8")) or {}
        self.config_manager = config_manager or EnvironmentConfigManager()

        self.history_dir = history_dir or (ARTIFACTS_ROOT / "deployments")
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.history_dir / "deployment_history.jsonl"

    def list_steps(self) -> List[Dict[str, Any]]:
        return self.pipeline.get("steps", [])

    async def run_pipeline(
        self,
        profile: str,
        dry_run: bool = True,
        selected_steps: Optional[List[str]] = None,
        env_overrides: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """运行部署流水线（增强版：支持CI/CD集成和部署验证）"""
        profile_data = self.config_manager.load_profile(profile)
        selected = set(selected_steps or [])
        results: List[PipelineStepResult] = []

        # 先确保 env 已生成
        self.config_manager.apply_profile(profile, overrides=env_overrides)

        # 记录部署开始时间
        deployment_start_time = time.time()
        
        for step in self.pipeline.get("steps", []):
            if selected and step.get("name") not in selected:
                continue
            result = await self._execute_step(step, dry_run=dry_run, profile_data=profile_data)
            results.append(result)
            if result.status == "failed":
                break

        # 部署后验证
        if not dry_run and results and all(r.status == "success" for r in results):
            verification_result = await self._verify_deployment(profile_data)
            results.append(verification_result)

        summary = {
            "profile": profile,
            "dry_run": dry_run,
            "timestamp": _utc_now(),
            "steps": [result.__dict__ for result in results],
            "completed": results[-1].status != "failed" if results else True,
            "deployment_duration": time.time() - deployment_start_time,
            "success_rate": len([r for r in results if r.status == "success"]) / len(results) if results else 0,
        }
        self._write_history(summary)
        
        # 发送部署通知
        if not dry_run:
            await self._send_deployment_notification(summary)
            
        return summary

    async def _verify_deployment(self, profile_data: Dict[str, Any]) -> PipelineStepResult:
        """部署后验证"""
        start_time = time.time()
        
        try:
            # 验证服务健康状态
            health_checks = profile_data.get("health_checks", [])
            for check in health_checks:
                if not await self._check_service_health(check):
                    return PipelineStepResult(
                        name="deployment_verification",
                        status="failed",
                        command="health_check",
                        detail=f"服务健康检查失败: {check}",
                        started_at=_utc_now(),
                        finished_at=_utc_now()
                    )
            
            # 验证功能完整性
            functional_tests = profile_data.get("functional_tests", [])
            for test in functional_tests:
                if not await self._run_functional_test(test):
                    return PipelineStepResult(
                        name="deployment_verification",
                        status="failed",
                        command="functional_test",
                        detail=f"功能测试失败: {test}",
                        started_at=_utc_now(),
                        finished_at=_utc_now()
                    )
            
            return PipelineStepResult(
                name="deployment_verification",
                status="success",
                command="verify_deployment",
                detail="部署验证通过",
                started_at=_utc_now(),
                finished_at=_utc_now()
            )
            
        except Exception as e:
            return PipelineStepResult(
                name="deployment_verification",
                status="failed",
                command="verify_deployment",
                detail=f"部署验证异常: {str(e)}",
                started_at=_utc_now(),
                finished_at=_utc_now()
            )

    async def _check_service_health(self, health_check: Dict[str, Any]) -> bool:
        """检查服务健康状态"""
        try:
            url = health_check.get("url")
            timeout = health_check.get("timeout", 30)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    return response.status == 200
        except Exception:
            return False

    async def _run_functional_test(self, test_config: Dict[str, Any]) -> bool:
        """运行功能测试"""
        try:
            # 执行功能测试脚本
            test_script = test_config.get("script")
            if test_script:
                result = subprocess.run(
                    test_script, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=300
                )
                return result.returncode == 0
            return True
        except Exception:
            return False

    async def _send_deployment_notification(self, summary: Dict[str, Any]) -> None:
        """发送部署通知"""
        try:
            # 构建通知消息
            message = {
                "title": f"部署完成 - {summary['profile']}",
                "content": {
                    "状态": "成功" if summary["completed"] else "失败",
                    "耗时": f"{summary['deployment_duration']:.2f}秒",
                    "成功率": f"{summary['success_rate']:.1%}",
                    "步骤数": len(summary["steps"])
                },
                "timestamp": summary["timestamp"]
            }
            
            # 发送到配置的通知渠道
            # 这里可以集成邮件、钉钉、微信等通知渠道
            logger.info(f"部署通知: {message}")
            
        except Exception as e:
            logger.error(f"发送部署通知失败: {e}")

    async def _execute_step(
        self,
        step: Dict[str, Any],
        dry_run: bool,
        profile_data: Optional[Dict[str, Any]] = None,
    ) -> PipelineStepResult:
        name = step.get("name") or "unnamed"
        step_type = step.get("type", "command")
        command = step.get("command") or ""
        result = PipelineStepResult(
            name=name,
            status="skipped" if dry_run else "pending",
            command=command,
            started_at=_utc_now(),
        )

        # 扩展：处理特殊步骤类型
        if step_type == "npm_install":
            command = self._build_npm_command(step, profile_data)
        elif step_type == "docker_build":
            command = self._build_docker_command(step, profile_data)
        elif step_type == "sidecar_deploy":
            command = self._build_sidecar_command(step, profile_data)
        elif step_type == "service_register":
            command = self._build_service_register_command(step, profile_data)

        result.command = command

        if dry_run or not command:
            result.status = "skipped"
            result.detail = "dry_run 模式" if dry_run else "未提供 command"
            result.finished_at = _utc_now()
            return result

        try:
            proc = await asyncio.to_thread(
                subprocess.run,
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT.parent,
                check=False,
                env={**os.environ},
            )
            result.finished_at = _utc_now()
            if proc.returncode == 0:
                result.status = "success"
                result.detail = (proc.stdout or "").strip()[:2000]
            else:
                result.status = "failed"
                stderr = proc.stderr or proc.stdout
                result.detail = f"退出码 {proc.returncode}: {(stderr or '').strip()[:2000]}"
        except Exception as exc:  # pragma: no cover - 防御性
            result.status = "failed"
            result.finished_at = _utc_now()
            result.detail = str(exc)
        return result

    def _build_npm_command(self, step: Dict[str, Any], profile_data: Optional[Dict[str, Any]]) -> str:
        """构建 npm 安装命令"""
        npm_config = profile_data.get("npm", {}) if profile_data else {}
        registry = npm_config.get("registry", "https://registry.npmjs.org/")
        token = npm_config.get("token", "")
        scope = npm_config.get("scope", "")
        
        cmd_parts = ["npm install"]
        if registry:
            cmd_parts.append(f"--registry={registry}")
        if token:
            cmd_parts.append(f"--//{registry.replace('https://', '').replace('http://', '')}/:_authToken={token}")
        if scope:
            cmd_parts.append(f"--scope={scope}")
        
        working_dir = step.get("working_dir", ".")
        if working_dir != ".":
            cmd_parts.append(f"--prefix {working_dir}")
        
        return " ".join(cmd_parts)

    def _build_docker_command(self, step: Dict[str, Any], profile_data: Optional[Dict[str, Any]]) -> str:
        """构建 Docker 构建/运行命令"""
        action = step.get("action", "build")
        image_name = step.get("image", "ai-stack")
        tag = step.get("tag", "latest")
        dockerfile = step.get("dockerfile", "Dockerfile")
        
        if action == "build":
            return f"docker build -t {image_name}:{tag} -f {dockerfile} ."
        elif action == "run":
            ports = step.get("ports", {})
            env_file = step.get("env_file", ".env.runtime")
            port_args = " ".join([f"-p {k}:{v}" for k, v in ports.items()])
            return f"docker run -d --name {image_name} --env-file {env_file} {port_args} {image_name}:{tag}"
        elif action == "compose":
            compose_file = step.get("compose_file", "docker-compose.yml")
            return f"docker-compose -f {compose_file} up -d"
        return ""

    def _build_sidecar_command(self, step: Dict[str, Any], profile_data: Optional[Dict[str, Any]]) -> str:
        """构建 Sidecar 部署命令"""
        sidecar_name = step.get("sidecar", "rag_sidecar")
        sidecar_path = step.get("path", f"services/{sidecar_name}.py")
        port = step.get("port", 8001)
        
        # 使用 uvicorn 运行 sidecar
        return f"python3 -m uvicorn {sidecar_path.replace('.py', '').replace('/', '.')}:app --host 0.0.0.0 --port {port} --reload"

    def _build_service_register_command(self, step: Dict[str, Any], profile_data: Optional[Dict[str, Any]]) -> str:
        """构建服务注册命令"""
        service_name = step.get("service", "rag_hub")
        endpoint = step.get("endpoint", "http://localhost:8001")
        version = step.get("version", "v1")
        
        # 调用服务注册 API
        register_url = f"http://localhost:8000/api/architecture/services/register"
        payload = {
            "service": service_name,
            "endpoint": endpoint,
            "version": version,
            "protocol": "http",
            "deployment_target": "sidecar"
        }
        
        import json as json_lib
        payload_json = json_lib.dumps(payload)
        return f'curl -X POST "{register_url}" -H "Content-Type: application/json" -d \'{payload_json}\''

    def _write_history(self, record: Dict[str, Any]) -> None:
        with self.history_file.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(record, ensure_ascii=False) + "\n")

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.history_file.exists():
            return []
        lines = self.history_file.read_text(encoding="utf-8").strip().splitlines()
        records = [json.loads(line) for line in lines if line.strip()]
        return list(reversed(records[-limit:]))


# 便于 API/脚本复用
_env_manager: Optional[EnvironmentConfigManager] = None
_deployment_manager: Optional[DeploymentAutomation] = None


def get_env_manager() -> EnvironmentConfigManager:
    global _env_manager
    if _env_manager is None:
        _env_manager = EnvironmentConfigManager()
    return _env_manager


def get_deployment_manager() -> DeploymentAutomation:
    global _deployment_manager
    if _deployment_manager is None:
        _deployment_manager = DeploymentAutomation(config_manager=get_env_manager())
    return _deployment_manager
