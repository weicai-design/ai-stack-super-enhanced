#!/bin/bash
# -*- coding: utf-8 -*-
# P1-201: 多环境部署自动化脚本

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="${PROJECT_ROOT}/scripts"
CONFIG_DIR="${PROJECT_ROOT}/config"

# 默认值
ENV_PROFILE="${1:-dev}"
DRY_RUN="${2:-false}"
SELECTED_STEPS="${3:-}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AI-STACK 多环境部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "环境配置: ${ENV_PROFILE}"
echo "干运行模式: ${DRY_RUN}"
echo "选定步骤: ${SELECTED_STEPS:-全部}"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3${NC}"
    exit 1
fi

# 检查配置文件
if [ ! -f "${CONFIG_DIR}/environments/${ENV_PROFILE}.yaml" ]; then
    echo -e "${RED}错误: 未找到环境配置: ${ENV_PROFILE}${NC}"
    echo "可用配置:"
    ls -1 "${CONFIG_DIR}/environments/"*.yaml | xargs -n1 basename | sed 's/.yaml$//'
    exit 1
fi

# 激活虚拟环境（如果存在）
if [ -d "${PROJECT_ROOT}/venv" ]; then
    source "${PROJECT_ROOT}/venv/bin/activate"
fi

# 运行部署
echo -e "${YELLOW}开始部署...${NC}"
cd "${PROJECT_ROOT}"

if [ "${DRY_RUN}" = "true" ]; then
    python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, str(Path('🚀 Super Agent Main Interface').absolute()))
from core.config_automation import get_deployment_manager

manager = get_deployment_manager()
import asyncio
result = asyncio.run(manager.run_pipeline('${ENV_PROFILE}', dry_run=True))
print(f\"部署完成: {result['completed']}\")
"
else
    python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, str(Path('🚀 Super Agent Main Interface').absolute()))
from core.config_automation import get_deployment_manager

manager = get_deployment_manager()
import asyncio
selected = '${SELECTED_STEPS}'.split(',') if '${SELECTED_STEPS}' else None
result = asyncio.run(manager.run_pipeline('${ENV_PROFILE}', dry_run=False, selected_steps=selected))
print(f\"部署完成: {result['completed']}\")
for step in result['steps']:
    status = '✅' if step['status'] == 'success' else '❌' if step['status'] == 'failed' else '⏭️'
    print(f\"{status} {step['name']}: {step['status']}\")
"
fi

echo ""
echo -e "${GREEN}部署脚本执行完成${NC}"

