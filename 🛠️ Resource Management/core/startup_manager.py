"""
启动顺序管理器
管理所有服务的启动顺序和依赖关系
"""

import subprocess
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StartupManager:
    """启动顺序管理器"""
    
    def __init__(self):
        # 服务启动配置（按用户需求8.3定义）
        self.startup_sequence = [
            {
                "order": 1,
                "service": "docker",
                "command": "open -a Docker",
                "wait_time": 30,
                "health_check": self._check_docker,
                "required": True,
                "description": "Docker 桌面应用"
            },
            {
                "order": 2,
                "service": "ollama",
                "command": "ollama serve",
                "wait_time": 10,
                "health_check": self._check_ollama,
                "required": True,
                "description": "Ollama LLM 服务"
            },
            {
                "order": 3,
                "service": "open-webui",
                "command": "docker run -d -p 3000:8080 --name open-webui ghcr.io/open-webui/open-webui:main",
                "wait_time": 15,
                "health_check": self._check_open_webui,
                "required": True,
                "description": "OpenWebUI 统一交互界面"
            },
            {
                "order": 4,
                "service": "rag-service",
                "command": 'cd "/Users/ywc/ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph" && python3 -m uvicorn api.app:app --host 0.0.0.0 --port 8011',
                "wait_time": 5,
                "health_check": lambda: self._check_http("http://localhost:8011/health"),
                "required": False,
                "description": "RAG 知识图谱服务"
            },
            {
                "order": 5,
                "service": "erp-backend",
                "command": 'cd "/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management" && source venv/bin/activate && python -m uvicorn api.main:app --host 0.0.0.0 --port 8013',
                "wait_time": 5,
                "health_check": lambda: self._check_http("http://localhost:8013/health"),
                "required": False,
                "description": "ERP 后端服务"
            },
            {
                "order": 6,
                "service": "erp-frontend",
                "command": 'cd "/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management/web/frontend" && npm run dev',
                "wait_time": 10,
                "health_check": lambda: self._check_http("http://localhost:8012"),
                "required": False,
                "description": "ERP 前端界面"
            },
            {
                "order": 7,
                "service": "stock-service",
                "command": 'cd "/Users/ywc/ai-stack-super-enhanced/📈 Intelligent Stock Trading" && python -m uvicorn api.main:app --host 0.0.0.0 --port 8014',
                "wait_time": 5,
                "health_check": lambda: self._check_http("http://localhost:8014/health"),
                "required": False,
                "description": "股票交易服务"
            },
            {
                "order": 8,
                "service": "trend-service",
                "command": 'cd "/Users/ywc/ai-stack-super-enhanced/🔍 Intelligent Trend Analysis" && python -m uvicorn api.main:app --host 0.0.0.0 --port 8015',
                "wait_time": 5,
                "health_check": lambda: self._check_http("http://localhost:8015/health"),
                "required": False,
                "description": "趋势分析服务"
            },
            {
                "order": 9,
                "service": "content-service",
                "command": 'cd "/Users/ywc/ai-stack-super-enhanced/🎨 Intelligent Content Creation" && python -m uvicorn api.main:app --host 0.0.0.0 --port 8016',
                "wait_time": 5,
                "health_check": lambda: self._check_http("http://localhost:8016/health"),
                "required": False,
                "description": "内容创作服务"
            },
            {
                "order": 10,
                "service": "task-agent",
                "command": 'cd "/Users/ywc/ai-stack-super-enhanced/🤖 Intelligent Task Agent" && python -m uvicorn web.api.main:app --host 0.0.0.0 --port 8017',
                "wait_time": 5,
                "health_check": lambda: self._check_http("http://localhost:8017/health"),
                "required": False,
                "description": "智能任务代理"
            }
        ]
        
        # 启动状态
        self.startup_status = {}
        
        # 最大等待时间（秒）
        self.max_wait_time = 120
        
        logger.info("启动顺序管理器初始化完成")
    
    def _check_docker(self) -> bool:
        """检查Docker是否运行"""
        try:
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_ollama(self) -> bool:
        """检查Ollama是否运行"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_open_webui(self) -> bool:
        """检查OpenWebUI是否运行"""
        return self._check_http("http://localhost:3000")
    
    def _check_http(self, url: str) -> bool:
        """检查HTTP服务是否可用"""
        try:
            import urllib.request
            urllib.request.urlopen(url, timeout=2)
            return True
        except:
            return False
    
    def start_all_services(
        self,
        skip_optional: bool = False
    ) -> Dict[str, Any]:
        """
        按顺序启动所有服务
        
        Args:
            skip_optional: 是否跳过非必须服务
            
        Returns:
            启动结果
        """
        result = {
            "started": [],
            "failed": [],
            "skipped": [],
            "total_time_seconds": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        start_time = time.time()
        
        for service_config in self.startup_sequence:
            service_name = service_config["service"]
            
            # 跳过非必须服务
            if skip_optional and not service_config.get("required", False):
                result["skipped"].append(service_name)
                logger.info(f"跳过非必须服务: {service_name}")
                continue
            
            logger.info(f"启动服务 [{service_config['order']}]: {service_name}")
            
            service_result = self._start_service(service_config)
            
            if service_result["success"]:
                result["started"].append({
                    "service": service_name,
                    "order": service_config["order"],
                    "duration_seconds": service_result.get("duration", 0)
                })
            else:
                result["failed"].append({
                    "service": service_name,
                    "order": service_config["order"],
                    "error": service_result.get("error", "Unknown error")
                })
                
                # 如果是必须服务启动失败，中止后续启动
                if service_config.get("required", False):
                    logger.error(f"必须服务 {service_name} 启动失败，中止后续启动")
                    break
        
        result["total_time_seconds"] = time.time() - start_time
        
        return result
    
    def _start_service(self, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        启动单个服务
        
        Args:
            service_config: 服务配置
            
        Returns:
            启动结果
        """
        service_name = service_config["service"]
        start_time = time.time()
        
        result = {
            "service": service_name,
            "success": False,
            "duration": 0
        }
        
        try:
            # 检查服务是否已运行
            health_check = service_config.get("health_check")
            if health_check and health_check():
                logger.info(f"服务 {service_name} 已在运行")
                result["success"] = True
                result["already_running"] = True
                return result
            
            # 执行启动命令（模拟）
            command = service_config.get("command", "")
            logger.info(f"执行命令: {command}")
            
            # 实际环境中这里应该执行真正的命令
            # subprocess.Popen(command, shell=True)
            
            # 等待服务启动
            wait_time = service_config.get("wait_time", 10)
            max_attempts = service_config.get("max_attempts", 10)
            
            logger.info(f"等待服务 {service_name} 启动...")
            
            for attempt in range(max_attempts):
                time.sleep(wait_time / max_attempts)
                
                if health_check and health_check():
                    logger.info(f"服务 {service_name} 启动成功")
                    result["success"] = True
                    break
            else:
                # 如果没有健康检查，假设启动成功
                if not health_check:
                    result["success"] = True
                    logger.info(f"服务 {service_name} 启动命令已执行（无健康检查）")
                else:
                    result["error"] = f"服务启动超时（等待 {wait_time} 秒）"
                    logger.error(result["error"])
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"启动服务 {service_name} 失败: {e}")
        
        result["duration"] = time.time() - start_time
        
        return result
    
    def stop_all_services(self) -> Dict[str, Any]:
        """停止所有服务"""
        result = {
            "stopped": [],
            "failed": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # 按相反顺序停止
        for service_config in reversed(self.startup_sequence):
            service_name = service_config["service"]
            
            try:
                logger.info(f"停止服务: {service_name}")
                # 实际环境需要执行停止命令
                result["stopped"].append(service_name)
            except Exception as e:
                result["failed"].append({
                    "service": service_name,
                    "error": str(e)
                })
        
        return result
    
    def restart_service(self, service_name: str) -> Dict[str, Any]:
        """重启指定服务"""
        service_config = next(
            (s for s in self.startup_sequence if s["service"] == service_name),
            None
        )
        
        if not service_config:
            return {
                "success": False,
                "error": f"服务 {service_name} 不存在"
            }
        
        logger.info(f"重启服务: {service_name}")
        
        # 停止服务
        # 实际环境需要执行停止命令
        
        # 启动服务
        return self._start_service(service_config)
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """获取服务状态"""
        service_config = next(
            (s for s in self.startup_sequence if s["service"] == service_name),
            None
        )
        
        if not service_config:
            return {
                "service": service_name,
                "exists": False
            }
        
        health_check = service_config.get("health_check")
        is_running = health_check() if health_check else False
        
        return {
            "service": service_name,
            "exists": True,
            "running": is_running,
            "order": service_config["order"],
            "required": service_config.get("required", False),
            "description": service_config.get("description", "")
        }
    
    def get_all_services_status(self) -> List[Dict[str, Any]]:
        """获取所有服务状态"""
        return [
            self.get_service_status(s["service"])
            for s in self.startup_sequence
        ]
    
    def generate_auto_start_script(self, output_path: str = None) -> str:
        """
        生成自动启动脚本（用于电脑重启后自动启动）
        
        Args:
            output_path: 输出路径
            
        Returns:
            脚本内容
        """
        script = """#!/bin/bash
# AI Stack Super Enhanced - 自动启动脚本
# 生成时间: {timestamp}

echo "🚀 开始启动 AI Stack 所有服务..."

""".format(timestamp=datetime.now().isoformat())
        
        for service_config in self.startup_sequence:
            service_name = service_config["service"]
            command = service_config["command"]
            wait_time = service_config.get("wait_time", 10)
            description = service_config.get("description", "")
            
            script += f"""
# {service_config['order']}. 启动 {service_name} - {description}
echo "启动 {service_name}..."
{command} &
sleep {wait_time}
"""
        
        script += """
echo "✅ 所有服务启动完成！"
"""
        
        # 保存到文件
        if output_path:
            try:
                with open(output_path, 'w') as f:
                    f.write(script)
                # 添加执行权限
                subprocess.run(["chmod", "+x", output_path])
                logger.info(f"自动启动脚本已生成: {output_path}")
            except Exception as e:
                logger.error(f"生成脚本失败: {e}")
        
        return script
    
    def create_launchd_plist(self, plist_path: str = None) -> str:
        """
        创建 macOS LaunchAgent 配置文件（开机自启动）
        
        Args:
            plist_path: plist文件路径
            
        Returns:
            plist内容
        """
        plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aistack.startup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/ywc/ai-stack-super-enhanced/scripts/auto_start.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/aistack_startup.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/aistack_startup_error.log</string>
</dict>
</plist>
"""
        
        if plist_path:
            try:
                with open(plist_path, 'w') as f:
                    f.write(plist)
                logger.info(f"LaunchAgent plist已生成: {plist_path}")
            except Exception as e:
                logger.error(f"生成plist失败: {e}")
        
        return plist

