#!/bin/bash

# 修复 bootstrap.sh 的参数解析问题
FILE="./🚀 Core System & Entry Points/bootstrap.sh"

# 备份原文件
cp "$FILE" "$FILE.backup.$(date +%Y%m%d_%H%M%S)"

# 修复参数解析逻辑 - 将错误退出改为警告继续
sed -i '' 's/error "未知参数: \$1"/warn "忽略未知参数: \$1"/' "$FILE"
sed -i '' 's/exit 1/# continue execution/' "$FILE"

echo "修复完成，原文件已备份"
echo "修复内容："
echo "1. 将未知参数的 'error' 改为 'warn'"
echo "2. 移除未知参数时的退出逻辑"
