#!/bin/bash
# ============================================
# SQLite 检查命令
# ============================================
# 说明：这个命令用来检查 SQLite 是否可用
# 使用方法：在终端中运行：bash sqlite_check_command.sh
# 或者：python3 -c "import sqlite3; print('✅ SQLite 已可用'); print(f'SQLite 版本: {sqlite3.sqlite_version}')"

echo "正在检查 SQLite..."
python3 -c "import sqlite3; print('✅ SQLite 已可用'); print(f'SQLite 版本: {sqlite3.sqlite_version}')"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 检查完成！SQLite 可以正常使用。"
else
    echo ""
    echo "❌ 检查失败，请检查 Python 是否正确安装。"
fi
