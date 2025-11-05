#!/usr/bin/env bash
# AI Stack Super Enhanced - 冒烟测试脚本
set -euo pipefail
cd "$(dirname "$0")/.."

API_URL="http://127.0.0.1:8011"
API_KEY="${RAG_API_KEY:-}"

# 检查服务是否运行
if ! curl -s -f "$API_URL/readyz" >/dev/null 2>&1; then
    echo "❌ 错误: API服务未运行，请先运行 'make dev' 或 'bash scripts/dev.sh'"
    exit 1
fi

echo "✅ API服务正在运行"
echo ""

# 准备测试文件
TEST_FILE="/tmp/ai-stack-test-$(date +%s).txt"
echo "Hello KG: test@example.com https://example.com Example email domain." > "$TEST_FILE"

# 定义curl函数，支持API Key
curl_api() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    if [ -n "$API_KEY" ]; then
        curl -s -X "$method" "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -H "X-API-Key: $API_KEY" \
            -d "$data"
    else
        curl -s -X "$method" "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data"
    fi
}

# 测试1: 健康检查
echo "📋 测试1: 健康检查"
curl -s "$API_URL/readyz" | { command -v jq >/dev/null && jq . || cat; }
echo ""

# 测试2: 文档摄取
echo "📋 测试2: 文档摄取"
curl_api "POST" "/rag/ingest" "{\"path\":\"$TEST_FILE\",\"save_index\":true}" | { command -v jq >/dev/null && jq . || cat; }
echo ""

# 等待索引完成
sleep 1

# 测试3: 语义搜索
echo "📋 测试3: 语义搜索"
curl -s "$API_URL/rag/search?query=example%20email&top_k=3" | { command -v jq >/dev/null && jq '.items[0]' || cat; }
echo ""

# 测试4: 索引信息
echo "📋 测试4: 索引信息"
curl -s "$API_URL/index/info" | { command -v jq >/dev/null && jq . || cat; }
echo ""

# 测试5: 知识图谱快照
echo "📋 测试5: 知识图谱快照"
curl -s "$API_URL/kg/snapshot" | { command -v jq >/dev/null && jq '.sample' || cat; }
echo ""

# 清理测试文件
rm -f "$TEST_FILE"
echo "✅ 冒烟测试完成"
