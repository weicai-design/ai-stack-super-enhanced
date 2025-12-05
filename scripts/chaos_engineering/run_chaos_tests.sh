#!/bin/bash
# -*- coding: utf-8 -*-
# P3-403: 故障演练脚本

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT_DIR="${PROJECT_ROOT}/scripts/chaos_engineering"

# 默认值
SCENARIO="${1:-all}"  # all/sidecar_down/database_degraded/api_timeout
DURATION="${2:-60}"  # 故障持续时间（秒）

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}故障演练脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "场景: ${SCENARIO}"
echo "持续时间: ${DURATION}秒"
echo ""

# 检查依赖
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}警告: 未找到 docker，部分功能可能不可用${NC}"
fi

# 运行故障演练
run_chaos_test() {
    local scenario=$1
    echo -e "${BLUE}执行故障演练: ${scenario}${NC}"
    
    python3 << EOF
import asyncio
import sys
sys.path.insert(0, "${PROJECT_ROOT}")

from scripts.chaos_engineering.chaos_test_runner import ChaosTestRunner, ChaosScenario

async def main():
    runner = ChaosTestRunner()
    
    if "${scenario}" == "all" or "${scenario}" == "sidecar_down":
        print("\\n🔴 测试场景1: Sidecar宕机")
        result = await runner.test_sidecar_down(
            sidecar_name="rag-sidecar",
            duration=int("${DURATION}")
        )
        print(f"结果: {'成功' if result.success else '失败'}")
        if result.recovery_time:
            print(f"恢复时间: {result.recovery_time:.2f}秒")
    
    if "${scenario}" == "all" or "${scenario}" == "database_degraded":
        print("\\n🔴 测试场景2: 数据库降级")
        result = await runner.test_database_degraded(
            database_name="postgres",
            degradation_type="slow_queries",
            duration=int("${DURATION}")
        )
        print(f"结果: {'成功' if result.success else '失败'}")
        if result.recovery_time:
            print(f"恢复时间: {result.recovery_time:.2f}秒")
    
    if "${scenario}" == "all" or "${scenario}" == "api_timeout":
        print("\\n🔴 测试场景3: API超时")
        result = await runner.test_api_timeout(
            endpoint="/gateway/rag/search",
            timeout_duration=30,
            test_duration=int("${DURATION}")
        )
        print(f"结果: {'成功' if result.success else '失败'}")
        if result.recovery_time:
            print(f"恢复时间: {result.recovery_time:.2f}秒")
    
    # 生成报告
    report = runner.generate_chaos_report()
    print("\\n📊 故障演练报告:")
    print(f"总测试数: {report['total_tests']}")
    print(f"成功: {report['summary']['successful_tests']}")
    print(f"失败: {report['summary']['failed_tests']}")
    print(f"平均恢复时间: {report['summary']['avg_recovery_time']:.2f}秒")

asyncio.run(main())
EOF
}

# 主函数
main() {
    echo -e "${YELLOW}警告: 故障演练将影响系统运行，请确保在测试环境执行${NC}"
    read -p "确认继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 0
    fi
    
    run_chaos_test "${SCENARIO}"
    
    echo -e "${GREEN}故障演练完成${NC}"
}

# 运行主函数
main

