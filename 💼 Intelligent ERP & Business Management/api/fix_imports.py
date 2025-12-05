#!/usr/bin/env python3
"""
批量修复API文件中的导入路径
将所有相对导入改为绝对导入，并确保Python路径正确设置
"""

import os
import re

def fix_imports_in_file(file_path):
    """修复单个文件中的导入路径"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换所有相对导入为绝对导入
    content = re.sub(r'from \.\.core\.', 'from core.', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已修复: {file_path}")

def main():
    api_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 修复所有API文件
    for filename in os.listdir(api_dir):
        if filename.endswith('_api.py') and filename != 'main.py':
            file_path = os.path.join(api_dir, filename)
            fix_imports_in_file(file_path)
    
    print("🎉 所有API文件导入路径修复完成！")

if __name__ == "__main__":
    main()