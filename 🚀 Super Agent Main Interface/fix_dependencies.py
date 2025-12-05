#!/usr/bin/env python3
"""
批量修复super_agent_api.py文件中的dependencies参数
将dependencies=[xxx_dep]改为dependencies=[Depends(xxx_dep)]
"""

import re

def fix_dependencies_in_file(file_path):
    """修复文件中的dependencies参数"""
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定义要修复的依赖项模式
    dependency_patterns = [
        (r'dependencies=\[finance_read_dep\]', 'dependencies=[Depends(finance_read_dep)]'),
        (r'dependencies=\[finance_write_dep\]', 'dependencies=[Depends(finance_write_dep)]'),
        (r'dependencies=\[security_read_dep\]', 'dependencies=[Depends(security_read_dep)]'),
        (r'dependencies=\[security_write_dep\]', 'dependencies=[Depends(security_write_dep)]'),
        (r'dependencies=\[rag_read_dep\]', 'dependencies=[Depends(rag_read_dep)]'),
        (r'dependencies=\[rag_write_dep\]', 'dependencies=[Depends(rag_write_dep)]'),
        (r'dependencies=\[erp_read_dep\]', 'dependencies=[Depends(erp_read_dep)]'),
        (r'dependencies=\[erp_write_dep\]', 'dependencies=[Depends(erp_write_dep)]'),
        (r'dependencies=\[content_read_dep\]', 'dependencies=[Depends(content_read_dep)]'),
        (r'dependencies=\[content_write_dep\]', 'dependencies=[Depends(content_write_dep)]'),
        (r'dependencies=\[trend_read_dep\]', 'dependencies=[Depends(trend_read_dep)]'),
        (r'dependencies=\[trend_write_dep\]', 'dependencies=[Depends(trend_write_dep)]'),
    ]
    
    # 应用所有替换
    fixed_content = content
    for pattern, replacement in dependency_patterns:
        fixed_content = re.sub(pattern, replacement, fixed_content)
    
    # 如果内容有变化，则写入文件
    if fixed_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"已修复 {file_path} 中的dependencies参数")
        return True
    else:
        print(f"{file_path} 中未找到需要修复的dependencies参数")
        return False

if __name__ == "__main__":
    file_path = "/Users/ywc/ai-stack-super-enhanced/🚀 Super Agent Main Interface/api/super_agent_api.py"
    fix_dependencies_in_file(file_path)