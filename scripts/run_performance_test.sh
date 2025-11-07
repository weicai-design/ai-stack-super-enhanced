#!/bin/bash

# 性能和压力测试脚本

echo "🚀 开始性能和压力测试..."
echo "================================"

PROJECT_ROOT="/Users/ywc/ai-stack-super-enhanced"
cd "$PROJECT_ROOT"

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ==================== 1. 单元性能测试 ====================
echo ""
echo -e "${BLUE}1️⃣  运行单元性能测试${NC}"
echo "--------------------------------"

pytest -v -m "performance and not slow" \
    --durations=10 \
    --tb=short

# ==================== 2. API压力测试 (使用Apache Bench) ====================
echo ""
echo -e "${BLUE}2️⃣  API压力测试${NC}"
echo "--------------------------------"

# 检查ab命令
if command -v ab &> /dev/null; then
    echo "测试RAG健康检查端点..."
    ab -n 1000 -c 10 http://localhost:8011/health
    
    echo ""
    echo "测试ERP财务概览端点..."
    ab -n 500 -c 10 http://localhost:8013/api/finance/summary
else
    echo -e "${YELLOW}⚠️  Apache Bench (ab) 未安装，跳过压力测试${NC}"
    echo "安装方法: brew install httpd (macOS)"
fi

# ==================== 3. 负载测试 (使用locust) ====================
echo ""
echo -e "${BLUE}3️⃣  负载测试${NC}"
echo "--------------------------------"

if command -v locust &> /dev/null; then
    echo "启动Locust Web界面..."
    echo "访问: http://localhost:8089"
    
    # 如果有locustfile则运行
    if [ -f "tests/performance/locustfile.py" ]; then
        locust -f tests/performance/locustfile.py --host=http://localhost:8011
    else
        echo -e "${YELLOW}⚠️  locustfile.py 不存在${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Locust 未安装，跳过负载测试${NC}"
    echo "安装方法: pip install locust"
fi

# ==================== 4. 内存泄漏测试 ====================
echo ""
echo -e "${BLUE}4️⃣  内存泄漏检测${NC}"
echo "--------------------------------"

if command -v memory_profiler &> /dev/null; then
    echo "运行内存分析..."
    python -m memory_profiler tests/performance/test_memory_leak.py
else
    echo -e "${YELLOW}⚠️  memory_profiler 未安装${NC}"
    echo "安装方法: pip install memory_profiler"
fi

# ==================== 5. 生成性能报告 ====================
echo ""
echo -e "${BLUE}5️⃣  生成性能报告${NC}"
echo "--------------------------------"

# 运行完整性能测试并生成报告
pytest -v -m "performance" \
    --html=reports/performance_report.html \
    --self-contained-html

echo ""
echo -e "${GREEN}✅ 性能测试完成！${NC}"
echo ""
echo "报告位置："
echo "  - HTML报告: reports/performance_report.html"
echo "  - 覆盖率报告: htmlcov/index.html"

