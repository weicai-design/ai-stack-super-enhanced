#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验收录像/脚本记录器
P3-016 开发任务：阶段性录像/脚本功能
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import logging
import subprocess
import shutil

logger = logging.getLogger(__name__)


class AcceptanceRecording:
    """
    验收录像/脚本记录器
    记录验收过程的录像和脚本
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        初始化记录器
        
        Args:
            output_dir: 输出目录，默认为 artifacts/evidence/recordings/
        """
        if output_dir is None:
            self.output_dir = Path(__file__).parent.parent.parent / "artifacts" / "evidence" / "recordings"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.recordings: List[Dict[str, Any]] = []
    
    def start_recording(
        self,
        requirement_id: str,
        recording_type: str = "script",  # script, video, screenshot
        description: str = ""
    ) -> str:
        """
        开始记录验收过程
        
        Args:
            requirement_id: 需求ID
            recording_type: 记录类型（script/video/screenshot）
            description: 描述
            
        Returns:
            记录ID
        """
        recording_id = f"{requirement_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        recording = {
            "id": recording_id,
            "requirement_id": requirement_id,
            "type": recording_type,
            "description": description,
            "started_at": datetime.now().isoformat(),
            "status": "recording",
            "steps": [],
            "evidence_files": []
        }
        
        self.recordings.append(recording)
        
        # 创建记录目录
        recording_dir = self.output_dir / recording_id
        recording_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"开始记录验收过程: {recording_id}")
        
        return recording_id
    
    def add_step(
        self,
        recording_id: str,
        step_name: str,
        command: Optional[str] = None,
        output: Optional[str] = None,
        screenshot: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """
        添加验收步骤
        
        Args:
            recording_id: 记录ID
            step_name: 步骤名称
            command: 执行的命令（可选）
            output: 命令输出（可选）
            screenshot: 截图路径（可选）
            notes: 备注（可选）
        """
        recording = self._find_recording(recording_id)
        if not recording:
            logger.error(f"未找到记录: {recording_id}")
            return
        
        step = {
            "step_name": step_name,
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "output": output,
            "screenshot": screenshot,
            "notes": notes
        }
        
        recording["steps"].append(step)
        
        # 保存步骤到文件
        recording_dir = self.output_dir / recording_id
        step_file = recording_dir / f"step_{len(recording['steps'])}.json"
        with open(step_file, 'w', encoding='utf-8') as f:
            json.dump(step, f, ensure_ascii=False, indent=2)
        
        logger.info(f"添加验收步骤: {step_name} (记录: {recording_id})")
    
    def record_command(
        self,
        recording_id: str,
        command: str,
        step_name: Optional[str] = None
    ) -> str:
        """
        记录命令执行
        
        Args:
            recording_id: 记录ID
            command: 要执行的命令
            step_name: 步骤名称（可选）
            
        Returns:
            命令输出
        """
        if not step_name:
            step_name = f"执行命令: {command}"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            output = result.stdout + result.stderr if result.stderr else result.stdout
            
            self.add_step(
                recording_id=recording_id,
                step_name=step_name,
                command=command,
                output=output,
                notes=f"返回码: {result.returncode}"
            )
            
            return output
        except subprocess.TimeoutExpired:
            error_msg = "命令执行超时（300秒）"
            self.add_step(
                recording_id=recording_id,
                step_name=step_name,
                command=command,
                output=error_msg,
                notes="执行超时"
            )
            return error_msg
        except Exception as e:
            error_msg = f"命令执行失败: {str(e)}"
            self.add_step(
                recording_id=recording_id,
                step_name=step_name,
                command=command,
                output=error_msg,
                notes="执行异常"
            )
            return error_msg
    
    def add_evidence_file(
        self,
        recording_id: str,
        file_path: str,
        file_type: str = "log",  # log, screenshot, video, document
        description: str = ""
    ):
        """
        添加证据文件
        
        Args:
            recording_id: 记录ID
            file_path: 文件路径
            file_type: 文件类型
            description: 描述
        """
        recording = self._find_recording(recording_id)
        if not recording:
            logger.error(f"未找到记录: {recording_id}")
            return
        
        evidence = {
            "file_path": file_path,
            "file_type": file_type,
            "description": description,
            "added_at": datetime.now().isoformat()
        }
        
        recording["evidence_files"].append(evidence)
        
        # 复制文件到记录目录
        source_path = Path(file_path)
        if source_path.exists():
            recording_dir = self.output_dir / recording_id
            dest_path = recording_dir / source_path.name
            shutil.copy2(source_path, dest_path)
            evidence["file_path"] = str(dest_path)
        
        logger.info(f"添加证据文件: {file_path} (记录: {recording_id})")
    
    def finish_recording(
        self,
        recording_id: str,
        result: str = "pass",  # pass, fail, partial
        summary: Optional[str] = None
    ):
        """
        完成记录
        
        Args:
            recording_id: 记录ID
            result: 结果（pass/fail/partial）
            summary: 摘要（可选）
        """
        recording = self._find_recording(recording_id)
        if not recording:
            logger.error(f"未找到记录: {recording_id}")
            return
        
        recording["status"] = "completed"
        recording["finished_at"] = datetime.now().isoformat()
        recording["result"] = result
        recording["summary"] = summary
        
        # 保存完整记录
        recording_dir = self.output_dir / recording_id
        recording_file = recording_dir / "recording.json"
        with open(recording_file, 'w', encoding='utf-8') as f:
            json.dump(recording, f, ensure_ascii=False, indent=2)
        
        logger.info(f"完成记录: {recording_id}, 结果: {result}")
    
    def generate_script(
        self,
        recording_id: str,
        output_file: Optional[Path] = None
    ) -> Path:
        """
        生成可执行脚本
        
        Args:
            recording_id: 记录ID
            output_file: 输出文件路径（可选）
            
        Returns:
            生成的脚本文件路径
        """
        recording = self._find_recording(recording_id)
        if not recording:
            raise ValueError(f"未找到记录: {recording_id}")
        
        if output_file is None:
            recording_dir = self.output_dir / recording_id
            output_file = recording_dir / "replay_script.sh"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("#!/bin/bash\n")
            f.write(f"# 验收脚本: {recording.get('description', '')}\n")
            f.write(f"# 需求ID: {recording.get('requirement_id', '')}\n")
            f.write(f"# 生成时间: {datetime.now().isoformat()}\n\n")
            f.write("set -e  # 遇到错误立即退出\n\n")
            
            for step in recording.get("steps", []):
                if step.get("command"):
                    f.write(f"# {step.get('step_name', '')}\n")
                    f.write(f"echo '执行: {step.get('step_name', '')}'\n")
                    f.write(f"{step['command']}\n")
                    f.write("echo ''\n\n")
        
        # 添加执行权限
        output_file.chmod(0o755)
        
        logger.info(f"生成验收脚本: {output_file}")
        
        return output_file
    
    def get_recording(self, recording_id: str) -> Optional[Dict[str, Any]]:
        """获取记录"""
        return self._find_recording(recording_id)
    
    def list_recordings(self, requirement_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出所有记录
        
        Args:
            requirement_id: 需求ID（可选，用于过滤）
            
        Returns:
            记录列表
        """
        if requirement_id:
            return [r for r in self.recordings if r.get("requirement_id") == requirement_id]
        return self.recordings
    
    def _find_recording(self, recording_id: str) -> Optional[Dict[str, Any]]:
        """查找记录"""
        for recording in self.recordings:
            if recording.get("id") == recording_id:
                return recording
        return None


# 全局实例
acceptance_recording = AcceptanceRecording()

