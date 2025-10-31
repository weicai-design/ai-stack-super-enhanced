#!/bin/bash
FILE="./🚀 Core System & Entry Points/bootstrap.sh"

# 备份
cp "$FILE" "${FILE}.backup.$(date +%s)"

# 替换完整的参数解析部分
python3 - << 'PYTHON'
import re

with open("./🚀 Core System & Entry Points/bootstrap.sh", "r") as f:
    content = f.read()

# 替换整个参数解析部分
new_content = re.sub(
    r'# 解析命令行参数.*?esac\n    done',
    '''# 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --phase)
                PHASE="$2"
                shift 2
                ;;
            --help)
                echo "用法: $0 [--phase rag-core|all]"
                echo ""
                echo "选项:"
                echo "  --phase rag-core    启动 RAG 核心系统"
                echo "  --phase all         启动所有系统组件"
                echo "  --help             显示此帮助信息"
                echo ""
                echo "示例:"
                echo "  $0 --phase rag-core    # 启动 RAG 核心系统"
                exit 0
                ;;
            *)
                warn "忽略未知参数: $1"
                shift
                ;;
        esac
    done''',
    content,
    flags=re.DOTALL
)

with open("./🚀 Core System & Entry Points/bootstrap.sh", "w") as f:
    f.write(new_content)

print("修复完成")
PYTHON

echo "修复后的参数解析："
sed -n '360,385p' "$FILE"
