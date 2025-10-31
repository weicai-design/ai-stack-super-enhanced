#!/usr/bin/env python3
"""
智能存储优化器
功能：监控和优化系统存储资源，支持外接硬盘管理
对应需求：8.1/8.2/8.5 - 资源动态调配、冲突解决、自适应调整
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List

import psutil

logger = logging.getLogger(__name__)


class StorageType(Enum):
    """存储类型枚举"""

    SSD = "ssd"
    HDD = "hdd"
    NETWORK = "network"
    EXTERNAL = "external"


@dataclass
class StorageDevice:
    """存储设备信息"""

    device: str
    mountpoint: str
    fstype: str
    total_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float
    storage_type: StorageType
    read_speed_mbps: float = 0.0
    write_speed_mbps: float = 0.0
    health_status: str = "healthy"


class StorageOptimizer:
    """
    智能存储优化器
    负责监控、分析和优化系统存储资源使用
    """

    def __init__(self, core_services: Dict = None):
        self.core_services = core_services or {}
        self.resource_manager = core_services.get("resource_manager")
        self.event_bus = core_services.get("event_bus")
        self.health_monitor = core_services.get("health_monitor")

        # 存储配置
        self.config = {
            "optimization_threshold": 0.85,  # 使用率超过85%触发优化
            "cleanup_threshold": 0.90,  # 使用率超过90%触发清理
            "cache_cleanup_size_gb": 5.0,  # 缓存清理大小
            "monitor_interval": 300,  # 监控间隔(秒)
            "external_drives": ["Huawei-1", "Huawei-2"],  # 外接硬盘
        }

        # 存储设备缓存
        self.storage_devices: Dict[str, StorageDevice] = {}
        self.optimization_history: List[Dict] = []

        # 性能指标
        self.performance_metrics = {
            "total_optimizations": 0,
            "space_recovered_gb": 0.0,
            "last_optimization_time": None,
        }

        logger.info("存储优化器初始化完成")

    async def initialize(self, config: Dict = None, core_services: Dict = None):
        """初始化存储优化器"""
        if config:
            self.config.update(config)

        if core_services:
            self.core_services = core_services
            self.resource_manager = core_services.get("resource_manager")
            self.event_bus = core_services.get("event_bus")
            self.health_monitor = core_services.get("health_monitor")

        # 初始扫描存储设备
        await self._scan_storage_devices()

        # 注册事件监听
        if self.event_bus:
            await self.event_bus.subscribe(
                "system.storage.low_space", self._handle_low_space
            )
            await self.event_bus.subscribe(
                "system.storage.optimize", self._handle_optimize_request
            )

        logger.info("存储优化器初始化完成")

    async def start(self):
        """启动存储监控"""
        asyncio.create_task(self._monitor_storage_loop())
        logger.info("存储监控已启动")

    async def stop(self):
        """停止存储优化器"""
        logger.info("存储优化器已停止")

    async def get_health_status(self) -> Dict:
        """获取健康状态"""
        device_status = {}
        for device_name, device in self.storage_devices.items():
            device_status[device_name] = {
                "usage_percent": device.usage_percent,
                "health_status": device.health_status,
                "free_space_gb": device.free_gb,
            }

        overall_health = "healthy"
        for device in self.storage_devices.values():
            if device.usage_percent > 0.95:
                overall_health = "critical"
            elif device.usage_percent > 0.85 and overall_health != "critical":
                overall_health = "warning"

        return {
            "status": overall_health,
            "details": device_status,
            "performance_metrics": self.performance_metrics,
            "timestamp": time.time(),
        }

    async def _scan_storage_devices(self):
        """扫描所有存储设备"""
        self.storage_devices.clear()

        # 扫描系统分区
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                device_name = os.path.basename(partition.mountpoint)

                # 判断存储类型
                storage_type = self._detect_storage_type(partition, device_name)

                device = StorageDevice(
                    device=partition.device,
                    mountpoint=partition.mountpoint,
                    fstype=partition.fstype,
                    total_gb=usage.total / (1024**3),
                    used_gb=usage.used / (1024**3),
                    free_gb=usage.free / (1024**3),
                    usage_percent=usage.percent / 100,
                    storage_type=storage_type,
                )

                # 检测性能指标
                await self._measure_storage_performance(device)

                self.storage_devices[device_name] = device

            except PermissionError:
                logger.warning(f"无法访问分区: {partition.mountpoint}")
            except Exception as e:
                logger.error(f"扫描分区失败 {partition.mountpoint}: {e}")

        logger.info(f"扫描到 {len(self.storage_devices)} 个存储设备")

    def _detect_storage_type(self, partition, device_name: str) -> StorageType:
        """检测存储类型"""
        mountpoint = partition.mountpoint.lower()
        device = partition.device.lower()

        # 检测外接硬盘
        if any(
            ext_drive.lower() in mountpoint
            for ext_drive in self.config["external_drives"]
        ):
            return StorageType.EXTERNAL

        # 检测SSD (简化检测，实际应使用更精确的方法)
        if "/volumes/" in mountpoint or device_name in self.config["external_drives"]:
            return StorageType.EXTERNAL
        elif "ssd" in device or "nvme" in device:
            return StorageType.SSD
        else:
            return StorageType.HDD

    async def _measure_storage_performance(self, device: StorageDevice):
        """测量存储设备性能"""
        try:
            # 简单的性能测试 - 写入和读取小文件
            test_file = Path(device.mountpoint) / ".storage_test.tmp"
            test_data = b"x" * (1024 * 1024)  # 1MB数据

            # 写入测试
            start_time = time.time()
            with open(test_file, "wb") as f:
                f.write(test_data)
            write_time = time.time() - start_time

            # 读取测试
            start_time = time.time()
            with open(test_file, "rb") as f:
                f.read()
            read_time = time.time() - start_time

            # 清理测试文件
            test_file.unlink(missing_ok=True)

            device.write_speed_mbps = 1.0 / write_time if write_time > 0 else 0
            device.read_speed_mbps = 1.0 / read_time if read_time > 0 else 0

        except Exception as e:
            logger.warning(f"性能测试失败 {device.mountpoint}: {e}")
            device.write_speed_mbps = 0
            device.read_speed_mbps = 0

    async def _monitor_storage_loop(self):
        """存储监控循环"""
        while True:
            try:
                # 重新扫描设备
                await self._scan_storage_devices()

                # 检查存储状态并优化
                await self._check_and_optimize_storage()

                # 发布存储状态事件
                if self.event_bus:
                    await self.event_bus.publish(
                        "storage.status_update",
                        {
                            "devices": self._get_devices_summary(),
                            "timestamp": time.time(),
                        },
                    )

                await asyncio.sleep(self.config["monitor_interval"])

            except Exception as e:
                logger.error(f"存储监控循环异常: {e}")
                await asyncio.sleep(60)  # 出错时等待1分钟

    async def _check_and_optimize_storage(self):
        """检查并优化存储"""
        for device_name, device in self.storage_devices.items():
            # 检查使用率
            if device.usage_percent > self.config["optimization_threshold"]:
                logger.warning(
                    f"存储设备 {device_name} 使用率过高: {device.usage_percent:.1%}"
                )

                # 执行优化
                recovered_space = await self._optimize_storage(device)

                if recovered_space > 0:
                    self.performance_metrics["total_optimizations"] += 1
                    self.performance_metrics["space_recovered_gb"] += recovered_space
                    self.performance_metrics["last_optimization_time"] = time.time()

                    logger.info(f"存储优化完成，回收空间: {recovered_space:.2f} GB")

                # 发布优化事件
                if self.event_bus:
                    await self.event_bus.publish(
                        "storage.optimized",
                        {
                            "device": device_name,
                            "recovered_space_gb": recovered_space,
                            "previous_usage": device.usage_percent,
                            "timestamp": time.time(),
                        },
                    )

    async def _optimize_storage(self, device: StorageDevice) -> float:
        """优化指定存储设备"""
        recovered_space = 0.0

        try:
            # 1. 清理临时文件
            temp_space = await self._clean_temp_files(device.mountpoint)
            recovered_space += temp_space

            # 2. 清理缓存文件
            cache_space = await self._clean_cache_files(device.mountpoint)
            recovered_space += cache_space

            # 3. 清理日志文件 (保留最近7天)
            log_space = await self._clean_old_logs(device.mountpoint)
            recovered_space += log_space

            # 记录优化历史
            optimization_record = {
                "device": device.mountpoint,
                "timestamp": time.time(),
                "recovered_space_gb": recovered_space,
                "optimization_type": "automatic",
            }
            self.optimization_history.append(optimization_record)

            # 限制历史记录数量
            if len(self.optimization_history) > 100:
                self.optimization_history = self.optimization_history[-100:]

        except Exception as e:
            logger.error(f"存储优化失败 {device.mountpoint}: {e}")

        return recovered_space

    async def _clean_temp_files(self, mountpoint: str) -> float:
        """清理临时文件"""
        recovered_space = 0.0
        temp_dirs = [
            os.path.join(mountpoint, "tmp"),
            os.path.join(mountpoint, "temp"),
            "/tmp",
            "/var/tmp",
        ]

        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if file.endswith(".tmp") or file.startswith("temp_"):
                                file_path = os.path.join(root, file)
                                try:
                                    file_size = os.path.getsize(file_path) / (
                                        1024**3
                                    )  # GB
                                    # 只删除超过1小时的文件
                                    if time.time() - os.path.getctime(file_path) > 3600:
                                        os.remove(file_path)
                                        recovered_space += file_size
                                except Exception as e:
                                    continue  # 忽略无法删除的文件
                except Exception as e:
                    logger.warning(f"清理临时文件失败 {temp_dir}: {e}")

        return recovered_space

    async def _clean_cache_files(self, mountpoint: str) -> float:
        """清理缓存文件"""
        recovered_space = 0.0
        cache_dirs = [
            os.path.join(mountpoint, "Library", "Caches"),
            os.path.join(mountpoint, "var", "cache"),
            os.path.expanduser("~/Library/Caches"),
        ]

        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                try:
                    for root, dirs, files in os.walk(cache_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                file_size = os.path.getsize(file_path) / (1024**3)
                                # 只删除超过30天的缓存文件
                                if (
                                    time.time() - os.path.getctime(file_path)
                                    > 30 * 24 * 3600
                                ):
                                    os.remove(file_path)
                                    recovered_space += file_size
                            except Exception:
                                continue
                except Exception as e:
                    logger.warning(f"清理缓存失败 {cache_dir}: {e}")

        return recovered_space

    async def _clean_old_logs(self, mountpoint: str) -> float:
        """清理旧日志文件"""
        recovered_space = 0.0
        log_dirs = [
            "/var/log",
            os.path.join(mountpoint, "var", "log"),
            os.path.expanduser("~/Library/Logs"),
        ]

        for log_dir in log_dirs:
            if os.path.exists(log_dir):
                try:
                    for root, dirs, files in os.walk(log_dir):
                        for file in files:
                            if file.endswith(".log"):
                                file_path = os.path.join(root, file)
                                try:
                                    file_size = os.path.getsize(file_path) / (1024**3)
                                    # 删除超过7天的日志文件
                                    if (
                                        time.time() - os.path.getctime(file_path)
                                        > 7 * 24 * 3600
                                    ):
                                        os.remove(file_path)
                                        recovered_space += file_size
                                except Exception:
                                    continue
                except Exception as e:
                    logger.warning(f"清理日志失败 {log_dir}: {e}")

        return recovered_space

    async def _handle_low_space(self, event_data: Dict):
        """处理低存储空间事件"""
        device_name = event_data.get("device")
        if device_name in self.storage_devices:
            device = self.storage_devices[device_name]
            recovered_space = await self._optimize_storage(device)
            logger.info(f"响应低存储空间事件，回收空间: {recovered_space:.2f} GB")

    async def _handle_optimize_request(self, event_data: Dict):
        """处理优化请求事件"""
        device_name = event_data.get("device", "all")
        if device_name == "all":
            for device in self.storage_devices.values():
                await self._optimize_storage(device)
        elif device_name in self.storage_devices:
            await self._optimize_storage(self.storage_devices[device_name])

    def _get_devices_summary(self) -> Dict:
        """获取设备摘要信息"""
        summary = {}
        for name, device in self.storage_devices.items():
            summary[name] = {
                "total_gb": device.total_gb,
                "used_gb": device.used_gb,
                "free_gb": device.free_gb,
                "usage_percent": device.usage_percent,
                "storage_type": device.storage_type.value,
                "health_status": device.health_status,
            }
        return summary

    async def get_storage_analysis(self) -> Dict:
        """获取存储分析报告"""
        return {
            "devices": self._get_devices_summary(),
            "performance_metrics": self.performance_metrics,
            "optimization_history": self.optimization_history[-10:],  # 最近10次
            "recommendations": await self._generate_recommendations(),
            "timestamp": time.time(),
        }

    async def _generate_recommendations(self) -> List[str]:
        """生成存储优化建议"""
        recommendations = []

        for device_name, device in self.storage_devices.items():
            if device.usage_percent > 0.9:
                recommendations.append(
                    f"设备 {device_name} 存储空间严重不足，建议立即清理"
                )
            elif device.usage_percent > 0.8:
                recommendations.append(f"设备 {device_name} 存储空间紧张，建议进行优化")

            if device.storage_type == StorageType.HDD and device.usage_percent > 0.75:
                recommendations.append(
                    f"机械硬盘 {device_name} 使用率较高，可能影响性能"
                )

        # 检查外接硬盘
        external_drives = [
            d
            for d in self.storage_devices.values()
            if d.storage_type == StorageType.EXTERNAL
        ]
        if len(external_drives) < len(self.config["external_drives"]):
            missing = set(self.config["external_drives"]) - set(
                self.storage_devices.keys()
            )
            recommendations.append(f"外接硬盘未连接: {', '.join(missing)}")

        return recommendations

    async def relocate_data(
        self, source_device: str, target_device: str, data_patterns: List[str]
    ) -> Dict:
        """重定位数据到其他存储设备"""
        if (
            source_device not in self.storage_devices
            or target_device not in self.storage_devices
        ):
            return {"success": False, "error": "设备不存在"}

        source = self.storage_devices[source_device]
        target = self.storage_devices[target_device]

        if target.free_gb < source.used_gb * 0.1:  # 目标设备至少需要10%的源数据空间
            return {"success": False, "error": "目标设备空间不足"}

        # 实现数据迁移逻辑
        # 这里需要根据具体的数据模式实现迁移

        return {
            "success": True,
            "message": "数据重定位计划已创建",
            "estimated_time": "需要具体实现",
            "space_to_move_gb": source.used_gb * 0.1,  # 示例：移动10%的数据
        }
