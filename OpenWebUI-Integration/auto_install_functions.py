#!/usr/bin/env python3
"""
OpenWebUI Functions 自动安装脚本
通过直接操作OpenWebUI数据库安装Functions
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
import hashlib
import re

# 配置
OPENWEBUI_DB = "/Users/ywc/ai-stack-super-enhanced/OpenWebUI-Integration/open-webui/backend/data/webui.db"
FUNCTIONS_DIR = Path("/Users/ywc/ai-stack-super-enhanced/OpenWebUI-Integration/openwebui-functions")

# 尝试从Docker容器复制数据库
DOCKER_DB = "open-webui:/app/backend/data/webui.db"

def copy_db_from_docker():
    """从Docker容器复制数据库"""
    print("📦 从Docker容器复制数据库...")
    os.system(f"docker cp {DOCKER_DB} {OPENWEBUI_DB}")
    print("✅ 数据库已复制")

def copy_db_to_docker():
    """复制数据库回Docker容器"""
    print("📦 复制数据库回Docker容器...")
    os.system(f"docker cp {OPENWEBUI_DB} {DOCKER_DB}")
    print("✅ 数据库已更新")
    print("🔄 重启OpenWebUI容器...")
    os.system("docker restart open-webui")
    print("✅ OpenWebUI已重启")

def extract_function_metadata(code):
    """提取Function元数据"""
    metadata = {
        "title": "Untitled Function",
        "author": "AI Stack Team",
        "version": "1.0.0",
        "description": ""
    }
    
    # 提取docstring中的元数据
    title_match = re.search(r'title:\s*(.+)', code)
    if title_match:
        metadata["title"] = title_match.group(1).strip()
    
    author_match = re.search(r'author:\s*(.+)', code)
    if author_match:
        metadata["author"] = author_match.group(1).strip()
    
    version_match = re.search(r'version:\s*(.+)', code)
    if version_match:
        metadata["version"] = version_match.group(1).strip()
    
    desc_match = re.search(r'description:\s*(.+)', code)
    if desc_match:
        metadata["description"] = desc_match.group(1).strip()
    
    return metadata

def install_function_to_db(db_path, function_file):
    """安装Function到数据库"""
    try:
        # 读取Function代码
        with open(function_file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 提取元数据
        metadata = extract_function_metadata(code)
        
        # 生成ID
        function_id = function_file.stem
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='function'")
        if not cursor.fetchone():
            print(f"❌ 未找到function表")
            conn.close()
            return False
        
        # 检查是否已存在
        cursor.execute("SELECT id FROM function WHERE id=?", (function_id,))
        exists = cursor.fetchone()
        
        # 准备数据
        now = int(datetime.now().timestamp())
        
        meta_json = json.dumps({
            "title": metadata["title"],
            "author": metadata["author"],
            "version": metadata["version"],
            "description": metadata["description"]
        })
        
        if exists:
            # 更新
            cursor.execute("""
                UPDATE function 
                SET content=?, meta=?, updated_at=?
                WHERE id=?
            """, (code, meta_json, now, function_id))
            print(f"🔄 更新: {metadata['title']}")
        else:
            # 插入
            cursor.execute("""
                INSERT INTO function (id, user_id, name, type, content, meta, is_active, is_global, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                function_id,
                "",  # user_id (空表示全局)
                metadata["title"],
                "function",
                code,
                meta_json,
                1,  # is_active
                1,  # is_global
                now,
                now
            ))
            print(f"✅ 安装: {metadata['title']}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🚀 OpenWebUI Functions 自动安装工具")
    print("="*60)
    print()
    
    # 检查Functions文件
    functions = sorted(FUNCTIONS_DIR.glob("*.py"))
    if not functions:
        print(f"❌ 未找到Functions文件: {FUNCTIONS_DIR}")
        return
    
    print(f"📦 找到 {len(functions)} 个Functions")
    print()
    
    # 复制数据库
    print("Step 1: 从Docker获取数据库")
    print("-" * 60)
    copy_db_from_docker()
    print()
    
    # 检查数据库
    if not os.path.exists(OPENWEBUI_DB):
        print(f"❌ 数据库文件不存在: {OPENWEBUI_DB}")
        return
    
    # 安装Functions
    print("Step 2: 安装Functions到数据库")
    print("-" * 60)
    
    success_count = 0
    for func_file in functions:
        if install_function_to_db(OPENWEBUI_DB, func_file):
            success_count += 1
    
    print()
    print(f"✅ 成功安装 {success_count}/{len(functions)} 个Functions")
    print()
    
    # 复制回Docker
    print("Step 3: 更新OpenWebUI")
    print("-" * 60)
    copy_db_to_docker()
    print()
    
    print("="*60)
    print("🎉 Functions自动安装完成！")
    print("="*60)
    print()
    print("⏰ 等待OpenWebUI重启完成 (约10秒)...")
    print()
    print("然后访问: http://localhost:3000/workspace/functions")
    print("查看已安装的Functions")
    print()

if __name__ == "__main__":
    main()



