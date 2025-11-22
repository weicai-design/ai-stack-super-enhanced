#!/bin/bash
# -*- coding: utf-8 -*-
# P3-403: 性能测试脚本

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT_DIR="${PROJECT_ROOT}/scripts/performance"
REPORT_DIR="${PROJECT_ROOT}/reports/performance"

# 默认值
TEST_TYPE="${1:-all}"  # all/load/stress/stability/benchmark
BASE_URL="${2:-http://localhost:9000}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}性能测试脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "测试类型: ${TEST_TYPE}"
echo "基础URL: ${BASE_URL}"
echo ""

# 检查依赖
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3${NC}"
    exit 1
fi

# 创建报告目录
mkdir -p "${REPORT_DIR}"

# 运行性能测试
run_performance_test() {
    local test_type=$1
    echo -e "${BLUE}执行性能测试: ${test_type}${NC}"
    
    python3 << EOF
import asyncio
import sys
import json
sys.path.insert(0, "${PROJECT_ROOT}")

from tests.performance.test_performance_suite import PerformanceTestSuite

async def main():
    suite = PerformanceTestSuite(base_url="${BASE_URL}")
    
    try:
        if "${test_type}" == "all" or "${test_type}" == "load":
            print("\\n📊 负载测试")
            result = await suite.load_test(
                endpoint="/health",
                concurrent_users=10,
                requests_per_user=10,
            )
            print(f"QPS: {result.qps:.2f}")
            print(f"成功率: {result.success_rate:.2f}%")
            print(f"平均响应时间: {result.avg_response_time:.2f}ms")
        
        if "${test_type}" == "all" or "${test_type}" == "stress":
            print("\\n📊 压力测试")
            results = await suite.stress_test(
                endpoint="/health",
                initial_users=10,
                max_users=50,
                step=10,
            )
            print(f"完成 {len(results)} 个压力级别测试")
        
        if "${test_type}" == "all" or "${test_type}" == "stability":
            print("\\n📊 稳定性测试")
            result = await suite.stability_test(
                endpoint="/health",
                duration_seconds=60,
                requests_per_second=10,
            )
            print(f"QPS: {result.qps:.2f}")
            print(f"成功率: {result.success_rate:.2f}%")
        
        if "${test_type}" == "all" or "${test_type}" == "benchmark":
            print("\\n📊 基准测试")
            results = await suite.benchmark_test(
                endpoints=["/health", "/gateway/health"],
                iterations=100,
            )
            for endpoint, metrics in results.items():
                print(f"{endpoint}: {metrics.avg_response_time:.2f}ms")
        
        # 生成报告
        report = suite.generate_report()
        report_file = "${REPORT_DIR}/performance_report_\$(date +%Y%m%d_%H%M%S).json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\\n✅ 性能测试完成，报告已保存: {report_file}")
        
    finally:
        await suite.close()

asyncio.run(main())
EOF
}

# 主函数
main() {
    run_performance_test "${TEST_TYPE}"
    
    echo -e "${GREEN}性能测试完成${NC}"
}

# 运行主函数
main

