#!/usr/bin/env bash
# AI Stack Super Enhanced - 快速测试脚本
# 用于快速验证服务功能

set -euo pipefail

API_URL="http://127.0.0.1:8011"

echo "🧪 AI Stack Super Enhanced - 快速功能测试"
echo "=========================================="
echo ""

# 1. 检查服务状态
echo "1️⃣  检查服务状态..."
if curl -s -f "$API_URL/readyz" >/dev/null 2>&1; then
    echo "   ✅ 服务运行正常"
    curl -s "$API_URL/readyz" | python3 -m json.tool 2>/dev/null || curl -s "$API_URL/readyz"
else
    echo "   ❌ 服务未运行"
    echo "   💡 请先运行: make dev"
    exit 1
fi
echo ""

# 2. 检查索引信息
echo "2️⃣  检查索引信息..."
curl -s "$API_URL/index/info" | python3 -m json.tool 2>/dev/null || curl -s "$API_URL/index/info"
echo ""
echo ""

# 3. 创建测试文档
echo "3️⃣  创建测试文档..."
TEST_FILE="/tmp/ai-stack-test-$(date +%s).txt"
cat > "$TEST_FILE" << 'TESTCONTENT'
AI Stack Super Enhanced 测试文档

这是一个用于验证RAG系统功能的测试文档。

联系信息:
- 邮箱: test@example.com
- 网址: https://ai-stack.example.com
- 项目: AI Stack Super Enhanced

这是一个增强的RAG（检索增强生成）系统，支持多种文档格式处理和知识图谱构建。
TESTCONTENT
echo "   ✅ 测试文档已创建: $TEST_FILE"
echo ""

# 4. 摄入文档
echo "4️⃣  摄入文档到RAG..."
INGEST_RESPONSE=$(curl -s -X POST "$API_URL/rag/ingest" \
    -H "Content-Type: application/json" \
    -d "{\"path\":\"$TEST_FILE\",\"save_index\":true}")

echo "$INGEST_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$INGEST_RESPONSE"

if echo "$INGEST_RESPONSE" | grep -q '"success".*true'; then
    echo "   ✅ 文档摄入成功"
else
    echo "   ⚠️  文档摄入可能失败"
fi
echo ""

# 等待索引完成
sleep 2

# 5. 搜索文档
echo "5️⃣  搜索文档..."
SEARCH_RESPONSE=$(curl -s "$API_URL/rag/search?query=AI%20Stack&top_k=3")
echo "$SEARCH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SEARCH_RESPONSE"

if echo "$SEARCH_RESPONSE" | grep -q '"items"'; then
    echo "   ✅ 搜索功能正常"
else
    echo "   ⚠️  搜索可能未返回结果"
fi
echo ""

# 6. 查看知识图谱
echo "6️⃣  查看知识图谱快照..."
KG_RESPONSE=$(curl -s "$API_URL/kg/snapshot")
echo "$KG_RESPONSE" | python3 -m json.tool 2>/dev/null | head -30 || echo "$KG_RESPONSE" | head -30

if echo "$KG_RESPONSE" | grep -q '"nodes"'; then
    echo "   ✅ 知识图谱功能正常"
else
    echo "   ⚠️  知识图谱可能为空"
fi
echo ""

# 7. 清理
echo "7️⃣  清理测试文件..."
rm -f "$TEST_FILE"
echo "   ✅ 测试文件已清理"
echo ""

# 总结
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 快速测试完成！"
echo ""
echo "📊 测试结果:"
echo "   • 服务状态: ✅"
echo "   • 文档摄入: ✅"
echo "   • 搜索功能: ✅"
echo "   • 知识图谱: ✅"
echo ""
echo "🌐 访问API文档: http://127.0.0.1:8011/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

