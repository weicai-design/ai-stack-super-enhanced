#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CI 证据上传流程
P3-016 开发任务：CI 证据上传流程
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import logging
import shutil
import os

logger = logging.getLogger(__name__)


class CIEvidenceUploader:
    """
    CI 证据上传器
    处理CI/CD流程中的证据上传
    """
    
    def __init__(self, evidence_dir: Optional[Path] = None):
        """
        初始化证据上传器
        
        Args:
            evidence_dir: 证据目录，默认为 artifacts/evidence/ci/
        """
        if evidence_dir is None:
            self.evidence_dir = Path(__file__).parent.parent.parent / "artifacts" / "evidence" / "ci"
        else:
            self.evidence_dir = Path(evidence_dir)
        
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # CI环境变量
        self.ci_env = self._detect_ci_environment()
    
    def _detect_ci_environment(self) -> Dict[str, Any]:
        """检测CI环境"""
        env = {
            "is_ci": False,
            "provider": None,
            "build_id": None,
            "commit_sha": None,
            "branch": None,
            "workflow": None
        }
        
        # GitHub Actions
        if os.getenv("GITHUB_ACTIONS") == "true":
            env["is_ci"] = True
            env["provider"] = "github_actions"
            env["build_id"] = os.getenv("GITHUB_RUN_ID")
            env["commit_sha"] = os.getenv("GITHUB_SHA")
            env["branch"] = os.getenv("GITHUB_REF_NAME")
            env["workflow"] = os.getenv("GITHUB_WORKFLOW")
        
        # GitLab CI
        elif os.getenv("CI") == "true" and os.getenv("GITLAB_CI") == "true":
            env["is_ci"] = True
            env["provider"] = "gitlab_ci"
            env["build_id"] = os.getenv("CI_PIPELINE_ID")
            env["commit_sha"] = os.getenv("CI_COMMIT_SHA")
            env["branch"] = os.getenv("CI_COMMIT_REF_NAME")
            env["workflow"] = os.getenv("CI_PIPELINE_NAME")
        
        # Jenkins
        elif os.getenv("JENKINS_URL"):
            env["is_ci"] = True
            env["provider"] = "jenkins"
            env["build_id"] = os.getenv("BUILD_NUMBER")
            env["commit_sha"] = os.getenv("GIT_COMMIT")
            env["branch"] = os.getenv("GIT_BRANCH")
            env["workflow"] = os.getenv("JOB_NAME")
        
        return env
    
    def upload_evidence(
        self,
        requirement_id: str,
        evidence_type: str,  # test_result, screenshot, log, document, video
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        上传证据文件
        
        Args:
            requirement_id: 需求ID
            evidence_type: 证据类型
            file_path: 文件路径
            metadata: 元数据（可选）
            
        Returns:
            上传结果
        """
        source_path = Path(file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 创建需求目录
        requirement_dir = self.evidence_dir / requirement_id
        requirement_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成目标文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = source_path.suffix
        target_filename = f"{evidence_type}_{timestamp}{file_ext}"
        target_path = requirement_dir / target_filename
        
        # 复制文件
        shutil.copy2(source_path, target_path)
        
        # 创建证据元数据
        evidence_metadata = {
            "requirement_id": requirement_id,
            "evidence_type": evidence_type,
            "original_path": str(source_path),
            "stored_path": str(target_path),
            "filename": target_filename,
            "file_size": source_path.stat().st_size,
            "uploaded_at": datetime.now().isoformat(),
            "ci_environment": self.ci_env,
            "metadata": metadata or {}
        }
        
        # 保存元数据
        metadata_file = requirement_dir / f"{target_filename}.meta.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(evidence_metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"证据已上传: {target_path} (需求: {requirement_id})")
        
        return {
            "success": True,
            "evidence_id": f"{requirement_id}_{timestamp}",
            "stored_path": str(target_path),
            "metadata": evidence_metadata
        }
    
    def upload_test_results(
        self,
        requirement_id: str,
        test_results: Dict[str, Any],
        test_report_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        上传测试结果
        
        Args:
            requirement_id: 需求ID
            test_results: 测试结果
            test_report_file: 测试报告文件路径（可选）
            
        Returns:
            上传结果
        """
        # 保存测试结果JSON
        requirement_dir = self.evidence_dir / requirement_id
        requirement_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_results_file = requirement_dir / f"test_results_{timestamp}.json"
        
        with open(test_results_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        # 上传测试报告文件（如果提供）
        evidence_files = []
        if test_report_file and Path(test_report_file).exists():
            evidence = self.upload_evidence(
                requirement_id=requirement_id,
                evidence_type="test_report",
                file_path=test_report_file,
                metadata={"test_results": test_results}
            )
            evidence_files.append(evidence["stored_path"])
        
        return {
            "success": True,
            "test_results_file": str(test_results_file),
            "evidence_files": evidence_files,
            "test_results": test_results
        }
    
    def upload_screenshot(
        self,
        requirement_id: str,
        screenshot_path: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        上传截图
        
        Args:
            requirement_id: 需求ID
            screenshot_path: 截图路径
            description: 描述（可选）
            
        Returns:
            上传结果
        """
        return self.upload_evidence(
            requirement_id=requirement_id,
            evidence_type="screenshot",
            file_path=screenshot_path,
            metadata={"description": description or ""}
        )
    
    def upload_log(
        self,
        requirement_id: str,
        log_path: str,
        log_type: str = "execution"  # execution, error, debug
    ) -> Dict[str, Any]:
        """
        上传日志文件
        
        Args:
            requirement_id: 需求ID
            log_path: 日志文件路径
            log_type: 日志类型
            
        Returns:
            上传结果
        """
        return self.upload_evidence(
            requirement_id=requirement_id,
            evidence_type="log",
            file_path=log_path,
            metadata={"log_type": log_type}
        )
    
    def generate_evidence_report(
        self,
        requirement_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成证据报告
        
        Args:
            requirement_id: 需求ID（可选，用于过滤）
            
        Returns:
            证据报告
        """
        if requirement_id:
            requirement_dir = self.evidence_dir / requirement_id
            if not requirement_dir.exists():
                return {
                    "requirement_id": requirement_id,
                    "total_evidence": 0,
                    "evidence_list": []
                }
            
            evidence_list = []
            for file in requirement_dir.glob("*.meta.json"):
                with open(file, 'r', encoding='utf-8') as f:
                    evidence_list.append(json.load(f))
            
            return {
                "requirement_id": requirement_id,
                "total_evidence": len(evidence_list),
                "evidence_list": sorted(evidence_list, key=lambda x: x["uploaded_at"], reverse=True)
            }
        else:
            # 所有需求的证据
            all_evidence = {}
            for req_dir in self.evidence_dir.iterdir():
                if req_dir.is_dir():
                    req_id = req_dir.name
                    all_evidence[req_id] = self.generate_evidence_report(req_id)
            
            return {
                "total_requirements": len(all_evidence),
                "requirements": all_evidence
            }
    
    def get_ci_environment(self) -> Dict[str, Any]:
        """获取CI环境信息"""
        return self.ci_env


# 全局实例
ci_evidence_uploader = CIEvidenceUploader()

