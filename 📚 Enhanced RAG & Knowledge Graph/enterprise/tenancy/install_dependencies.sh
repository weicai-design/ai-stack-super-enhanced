#!/bin/bash
# 多租户认证系统依赖安装脚本
# Multi-tenant Authentication System Dependency Installation Script

set -e  # 遇到错误立即退出

echo "=================================="
echo "  多租户认证系统依赖安装"
echo "  Dependency Installation"
echo "=================================="
echo ""

# 检查 Python 版本
echo "📋 检查 Python 版本..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python 版本: $PYTHON_VERSION"
echo ""

# 核心依赖包
echo "📦 安装核心依赖包..."
python3 -m pip install --user --break-system-packages pydantic==2.12.4
python3 -m pip install --user --break-system-packages fastapi==0.121.1
python3 -m pip install --user --break-system-packages "python-jose[cryptography]==3.3.0"
python3 -m pip install --user --break-system-packages "passlib[bcrypt]==1.7.4"
python3 -m pip install --user --break-system-packages python-dotenv==1.0.1

echo ""
echo "✅ 核心依赖包安装完成"
echo ""

# 可选依赖包
echo "📦 安装可选依赖包（如果未安装）..."
python3 -m pip install --user --break-system-packages cryptography>=43.0.0 || echo "⚠️  cryptography 安装失败（可选）"
python3 -m pip install --user --break-system-packages PyJWT>=2.8.0 || echo "⚠️  PyJWT 安装失败（可选，已有 python-jose）"

echo ""
echo "✅ 所有依赖包安装完成"
echo ""
echo "=================================="
echo "  安装完成"
echo "=================================="
echo ""
echo "下一步："
echo "1. 运行完整性检查: python3 '📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/check_system_integrity.py'"
echo "2. 运行集成测试: python3 '📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/test_integration.py'"
echo ""

