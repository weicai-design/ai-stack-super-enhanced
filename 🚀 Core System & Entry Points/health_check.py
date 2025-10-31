#!/usr/bin/env python3
"""
AI-STACK-SUPER-ENHANCED 系统健康检查与监控脚本
对应需求: 8.3/8.4/8.5/8.6/8.8 - 健康监控、性能分析、异常检测
"""

import json
import logging
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List

import psutil
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            "/Users/ywc/ai-stack-super-enhanced/🚀 Core System & Entry Points/logs/health_check.log"
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    component: str
    status: HealthStatus
    message: str
    metrics: Dict
    timestamp: str


class SystemHealthChecker:
    """系统健康检查器"""

    def __init__(self):
        self.base_dir = "/Users/ywc/ai-stack-super-enhanced"
        self.script_dir = f"{self.base_dir}/🚀 Core System & Entry Points"
        self.results: List[HealthCheckResult] = []

        # 服务端点配置
        self.endpoints = {
            "openwebui": "http://localhost:3000",
            "ollama": "http://localhost:11434/api/tags",
            "ollama_models": "http://localhost:11434/api/tags",
        }

        # 阈值配置
        self.thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "temperature": 80.0,
            "response_time": 5.0,
        }

    def check_system_resources(self) -> HealthCheckResult:
        """检查系统资源使用情况"""
        metrics = {}
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics["cpu_percent"] = cpu_percent

            # 内存使用
            memory = psutil.virtual_memory()
            metrics["memory_percent"] = memory.percent
            metrics["memory_used_gb"] = memory.used / (1024**3)
            metrics["memory_total_gb"] = memory.total / (1024**3)

            # 磁盘使用
            disk = psutil.disk_usage("/")
            metrics["disk_percent"] = disk.percent
            metrics["disk_free_gb"] = disk.free / (1024**3)
            metrics["disk_total_gb"] = disk.total / (1024**3)

            # 检查外接硬盘
            external_disks = self._check_external_disks()
            metrics["external_disks"] = external_disks

            # 判断状态
            status = HealthStatus.HEALTHY
            message = "系统资源正常"

            if cpu_percent > self.thresholds["cpu_percent"]:
                status = HealthStatus.WARNING
                message = f"CPU使用率过高: {cpu_percent}%"
            elif memory.percent > self.thresholds["memory_percent"]:
                status = HealthStatus.WARNING
                message = f"内存使用率过高: {memory.percent}%"
            elif disk.percent > self.thresholds["disk_percent"]:
                status = HealthStatus.WARNING
                message = f"磁盘使用率过高: {disk.percent}%"

            return HealthCheckResult(
                component="system_resources",
                status=status,
                message=message,
                metrics=metrics,
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            logger.error(f"系统资源检查失败: {e}")
            return HealthCheckResult(
                component="system_resources",
                status=HealthStatus.UNKNOWN,
                message=f"检查失败: {str(e)}",
                metrics={},
                timestamp=datetime.now().isoformat(),
            )

    def _check_external_disks(self) -> Dict:
        """检查外接硬盘状态"""
        external_disks = {}
        try:
            # 检查华为外接硬盘
            disk_paths = ["/Volumes/Huawei-1", "/Volumes/Huawei-2"]

            for disk_path in disk_paths:
                if os.path.exists(disk_path):
                    try:
                        disk_usage = psutil.disk_usage(disk_path)
                        external_disks[disk_path] = {
                            "total_gb": disk_usage.total / (1024**3),
                            "used_gb": disk_usage.used / (1024**3),
                            "free_gb": disk_usage.free / (1024**3),
                            "percent": disk_usage.percent,
                        }
                    except Exception as e:
                        external_disks[disk_path] = {"error": str(e)}
                else:
                    external_disks[disk_path] = {"status": "not_mounted"}

        except Exception as e:
            logger.error(f"外接硬盘检查失败: {e}")

        return external_disks

    def check_docker_services(self) -> HealthCheckResult:
        """检查 Docker 服务状态"""
        metrics = {}
        try:
            # 检查 Docker 服务是否运行
            result = subprocess.run(
                ["docker", "info"], capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                return HealthCheckResult(
                    component="docker_services",
                    status=HealthStatus.CRITICAL,
                    message="Docker 服务未运行",
                    metrics=metrics,
                    timestamp=datetime.now().isoformat(),
                )

            # 检查 AI-STACK 容器
            containers_result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    "name=ai-stack",
                    "--format",
                    "{{.Names}}|{{.Status}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            running_containers = []
            if containers_result.returncode == 0:
                for line in containers_result.stdout.strip().split("\n"):
                    if line:
                        name, status = line.split("|", 1)
                        running_containers.append({"name": name, "status": status})

            metrics["running_containers"] = running_containers
            metrics["total_containers"] = len(running_containers)

            # 检查容器资源使用
            container_stats = self._get_container_stats()
            metrics["container_stats"] = container_stats

            if len(running_containers) == 0:
                status = HealthStatus.CRITICAL
                message = "没有运行的 AI-STACK 容器"
            else:
                # 检查关键容器
                critical_containers = ["ai-stack-ollama", "ai-stack-openwebui"]
                missing_containers = []

                for container in critical_containers:
                    if not any(
                        container in running.get("name", "")
                        for running in running_containers
                    ):
                        missing_containers.append(container)

                if missing_containers:
                    status = HealthStatus.CRITICAL
                    message = f"关键容器缺失: {', '.join(missing_containers)}"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"所有 {len(running_containers)} 个容器运行正常"

            return HealthCheckResult(
                component="docker_services",
                status=status,
                message=message,
                metrics=metrics,
                timestamp=datetime.now().isoformat(),
            )

        except subprocess.TimeoutExpired:
            return HealthCheckResult(
                component="docker_services",
                status=HealthStatus.CRITICAL,
                message="Docker 检查超时",
                metrics=metrics,
                timestamp=datetime.now().isoformat(),
            )
        except Exception as e:
            logger.error(f"Docker 服务检查失败: {e}")
            return HealthCheckResult(
                component="docker_services",
                status=HealthStatus.UNKNOWN,
                message=f"检查失败: {str(e)}",
                metrics=metrics,
                timestamp=datetime.now().isoformat(),
            )

    def _get_container_stats(self) -> Dict:
        """获取容器资源统计"""
        stats = {}
        try:
            result = subprocess.run(
                [
                    "docker",
                    "stats",
                    "--no-stream",
                    "--format",
                    "{{.Name}}|{{.CPUPerc}}|{{.MemPerc}}|{{.MemUsage}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line and "ai-stack" in line:
                        parts = line.split("|")
                        if len(parts) >= 4:
                            stats[parts[0]] = {
                                "cpu_percent": parts[1],
                                "memory_percent": parts[2],
                                "memory_usage": parts[3],
                            }
        except Exception as e:
            logger.error(f"获取容器统计失败: {e}")

        return stats

    def check_service_endpoints(self) -> HealthCheckResult:
        """检查服务端点可用性"""
        metrics = {}
        failed_endpoints = []
        response_times = {}

        try:
            for service, url in self.endpoints.items():
                try:
                    start_time = time.time()
                    response = requests.get(url, timeout=10)
                    end_time = time.time()

                    response_time = round((end_time - start_time) * 1000, 2)  # 毫秒
                    response_times[service] = response_time

                    if response.status_code == 200:
                        metrics[f"{service}_status"] = "healthy"
                        if service == "ollama_models":
                            # 解析模型信息
                            try:
                                models_data = response.json()
                                metrics["ollama_models"] = len(
                                    models_data.get("models", [])
                                )
                            except:
                                metrics["ollama_models"] = 0
                    else:
                        metrics[f"{service}_status"] = (
                            f"unhealthy_{response.status_code}"
                        )
                        failed_endpoints.append(service)

                except requests.exceptions.RequestException as e:
                    metrics[f"{service}_status"] = "unreachable"
                    failed_endpoints.append(service)
                    response_times[service] = None

            metrics["response_times_ms"] = response_times

            if not failed_endpoints:
                status = HealthStatus.HEALTHY
                message = "所有服务端点正常"
            else:
                status = HealthStatus.CRITICAL
                message = f"服务端点异常: {', '.join(failed_endpoints)}"

            return HealthCheckResult(
                component="service_endpoints",
                status=status,
                message=message,
                metrics=metrics,
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            logger.error(f"服务端点检查失败: {e}")
            return HealthCheckResult(
                component="service_endpoints",
                status=HealthStatus.UNKNOWN,
                message=f"检查失败: {str(e)}",
                metrics=metrics,
                timestamp=datetime.now().isoformat(),
            )

    def check_file_system(self) -> HealthCheckResult:
        """检查文件系统状态"""
        metrics = {}
        try:
            # 检查关键目录
            critical_dirs = [
                f"{self.script_dir}/logs",
                f"{self.script_dir}/backups",
                f"{self.script_dir}/cache",
                "/Volumes/Huawei-1/ai-stack-data",
                "/Volumes/Huawei-2/ai-stack-backup",
            ]

            dir_status = {}
            for dir_path in critical_dirs:
                if os.path.exists(dir_path):
                    try:
                        # 检查目录权限
                        stat_info = os.stat(dir_path)
                        dir_status[dir_path] = {
                            "exists": True,
                            "writable": os.access(dir_path, os.W_OK),
                            "size_mb": self._get_dir_size_mb(dir_path),
                        }
                    except Exception as e:
                        dir_status[dir_path] = {"exists": True, "error": str(e)}
                else:
                    dir_status[dir_path] = {"exists": False}

            metrics["directory_status"] = dir_status

            # 检查日志文件
            log_files = self._check_log_files()
            metrics["log_files"] = log_files

            # 判断状态
            missing_dirs = [
                path
                for path, status in dir_status.items()
                if not status.get("exists", False)
            ]
            unwritable_dirs = [
                path
                for path, status in dir_status.items()
                if status.get("exists") and not status.get("writable", False)
            ]

            if missing_dirs:
                status = HealthStatus.CRITICAL
                message = f"关键目录缺失: {', '.join(missing_dirs)}"
            elif unwritable_dirs:
                status = HealthStatus.WARNING
                message = f"目录不可写: {', '.join(unwritable_dirs)}"
            else:
                status = HealthStatus.HEALTHY
                message = "文件系统状态正常"

            return HealthCheckResult(
                component="file_system",
                status=status,
                message=message,
                metrics=metrics,
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            logger.error(f"文件系统检查失败: {e}")
            return HealthCheckResult(
                component="file_system",
                status=HealthStatus.UNKNOWN,
                message=f"检查失败: {str(e)}",
                metrics=metrics,
                timestamp=datetime.now().isoformat(),
            )

    def _get_dir_size_mb(self, path: str) -> float:
        """获取目录大小（MB）"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        continue
            return round(total_size / (1024 * 1024), 2)
        except Exception:
            return 0.0

    def _check_log_files(self) -> Dict:
        """检查日志文件状态"""
        log_info = {}
        log_dir = f"{self.script_dir}/logs"

        try:
            if os.path.exists(log_dir):
                for filename in os.listdir(log_dir):
                    if filename.endswith(".log"):
                        filepath = os.path.join(log_dir, filename)
                        stat_info = os.stat(filepath)
                        file_size_mb = stat_info.st_size / (1024 * 1024)

                        log_info[filename] = {
                            "size_mb": round(file_size_mb, 2),
                            "modified": datetime.fromtimestamp(
                                stat_info.st_mtime
                            ).isoformat(),
                        }
        except Exception as e:
            logger.error(f"检查日志文件失败: {e}")

        return log_info

    def check_temperature(self) -> HealthCheckResult:
        """检查系统温度（macOS）"""
        metrics = {}
        try:
            # 尝试使用 osx-cpu-temp 获取温度
            result = subprocess.run(
                ["which", "osx-cpu-temp"], capture_output=True, text=True
            )

            if result.returncode == 0:
                temp_result = subprocess.run(
                    ["osx-cpu-temp"], capture_output=True, text=True, timeout=5
                )

                if temp_result.returncode == 0:
                    temp_str = temp_result.stdout.strip()
                    # 解析温度值（假设格式为 "XX.XX°C"）
                    try:
                        temp_value = float(temp_str.split("°")[0])
                        metrics["cpu_temperature"] = temp_value

                        if temp_value > self.thresholds["temperature"]:
                            status = HealthStatus.WARNING
                            message = f"CPU温度过高: {temp_value}°C"
                        else:
                            status = HealthStatus.HEALTHY
                            message = f"CPU温度正常: {temp_value}°C"

                    except ValueError:
                        metrics["cpu_temperature"] = temp_str
                        status = HealthStatus.UNKNOWN
                        message = f"无法解析温度值: {temp_str}"
                else:
                    status = HealthStatus.UNKNOWN
                    message = "无法获取温度信息"
            else:
                # 回退到系统调用
                try:
                    # macOS 温度检测的替代方法
                    result = subprocess.run(
                        ["sysctl", "-n", "machdep.xcpm.cpu_thermal_level"],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        thermal_level = result.stdout.strip()
                        metrics["thermal_level"] = thermal_level
                        status = HealthStatus.HEALTHY
                        message = f"CPU热管理级别: {thermal_level}"
                    else:
                        status = HealthStatus.UNKNOWN
                        message = "温度检测不可用"
                except:
                    status = HealthStatus.UNKNOWN
                    message = "温度检测不可用"

            return HealthCheckResult(
                component="temperature",
                status=status,
                message=message,
                metrics=metrics,
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            logger.error(f"温度检查失败: {e}")
            return HealthCheckResult(
                component="temperature",
                status=HealthStatus.UNKNOWN,
                message=f"检查失败: {str(e)}",
                metrics=metrics,
                timestamp=datetime.now().isoformat(),
            )

    def run_comprehensive_check(self) -> List[HealthCheckResult]:
        """运行全面健康检查"""
        logger.info("开始全面健康检查...")

        checks = [
            self.check_system_resources,
            self.check_docker_services,
            self.check_service_endpoints,
            self.check_file_system,
            self.check_temperature,
        ]

        self.results = []
        for check_func in checks:
            try:
                result = check_func()
                self.results.append(result)
                logger.info(
                    f"{result.component}: {result.status.value} - {result.message}"
                )
            except Exception as e:
                logger.error(f"健康检查 {check_func.__name__} 失败: {e}")

        return self.results

    def generate_report(self) -> Dict:
        """生成健康检查报告"""
        if not self.results:
            self.run_comprehensive_check()

        # 计算总体状态
        status_priority = {
            HealthStatus.CRITICAL: 3,
            HealthStatus.WARNING: 2,
            HealthStatus.UNKNOWN: 1,
            HealthStatus.HEALTHY: 0,
        }

        overall_status = HealthStatus.HEALTHY
        for result in self.results:
            if status_priority[result.status] > status_priority[overall_status]:
                overall_status = result.status

        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status.value,
            "system_info": {
                "hostname": socket.gethostname(),
                "platform": sys.platform,
                "python_version": sys.version,
            },
            "components": [
                {
                    "name": result.component,
                    "status": result.status.value,
                    "message": result.message,
                    "metrics": result.metrics,
                    "timestamp": result.timestamp,
                }
                for result in self.results
            ],
            "summary": {
                "total_checks": len(self.results),
                "healthy": len(
                    [r for r in self.results if r.status == HealthStatus.HEALTHY]
                ),
                "warnings": len(
                    [r for r in self.results if r.status == HealthStatus.WARNING]
                ),
                "critical": len(
                    [r for r in self.results if r.status == HealthStatus.CRITICAL]
                ),
                "unknown": len(
                    [r for r in self.results if r.status == HealthStatus.UNKNOWN]
                ),
            },
        }

        return report

    def save_report(self, report: Dict):
        """保存健康检查报告"""
        try:
            reports_dir = f"{self.script_dir}/logs/health_reports"
            os.makedirs(reports_dir, exist_ok=True)

            filename = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(reports_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info(f"健康检查报告已保存: {filepath}")

            # 同时保存为易读格式
            txt_filepath = filepath.replace(".json", ".txt")
            with open(txt_filepath, "w", encoding="utf-8") as f:
                f.write(self._format_report_text(report))

            return filepath

        except Exception as e:
            logger.error(f"保存报告失败: {e}")

    def _format_report_text(self, report: Dict) -> str:
        """格式化报告为文本"""
        lines = []
        lines.append("=" * 60)
        lines.append("AI-STACK SUPER ENHANCED 健康检查报告")
        lines.append("=" * 60)
        lines.append(f"生成时间: {report['timestamp']}")
        lines.append(f"总体状态: {report['overall_status'].upper()}")
        lines.append(f"主机名: {report['system_info']['hostname']}")
        lines.append("")

        # 摘要信息
        summary = report["summary"]
        lines.append("检查摘要:")
        lines.append(f"  总检查数: {summary['total_checks']}")
        lines.append(f"  正常: {summary['healthy']}")
        lines.append(f"  警告: {summary['warnings']}")
        lines.append(f"  严重: {summary['critical']}")
        lines.append(f"  未知: {summary['unknown']}")
        lines.append("")

        # 组件详情
        lines.append("组件详情:")
        lines.append("-" * 40)

        for component in report["components"]:
            status_icon = (
                "✅"
                if component["status"] == "healthy"
                else "⚠️" if component["status"] == "warning" else "❌"
            )
            lines.append(f"{status_icon} {component['name']}: {component['status']}")
            lines.append(f"   消息: {component['message']}")

            # 显示关键指标
            if component["metrics"]:
                lines.append("   关键指标:")
                for key, value in list(component["metrics"].items())[
                    :3
                ]:  # 显示前3个指标
                    if isinstance(value, (int, float, str)):
                        lines.append(f"     - {key}: {value}")

            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)


def main():
    """主函数"""
    try:
        checker = SystemHealthChecker()

        # 运行健康检查
        print("🚀 开始 AI-STACK 健康检查...")
        report = checker.generate_report()

        # 显示报告
        print("\n" + checker._format_report_text(report))

        # 保存报告
        report_path = checker.save_report(report)
        if report_path:
            print(f"\n📊 详细报告已保存: {report_path}")

        # 根据总体状态设置退出码
        if report["overall_status"] == "critical":
            sys.exit(1)
        elif report["overall_status"] == "warning":
            sys.exit(2)
        else:
            sys.exit(0)

    except Exception as e:
        logger.error(f"健康检查主程序失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
