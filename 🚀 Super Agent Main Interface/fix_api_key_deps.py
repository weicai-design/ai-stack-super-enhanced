#!/usr/bin/env python3
"""
批量修复super_agent_api.py文件中的API密钥依赖函数
将所有 _get_require_api_key() 替换为 require_api_token
"""

import re

def fix_api_key_dependencies():
    file_path = "/Users/ywc/ai-stack-super-enhanced/🚀 Super Agent Main Interface/api/super_agent_api.py"
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换所有 _get_require_api_key() 为 require_api_token
    old_pattern = r'_get_require_api_key\(\)'
    new_content = re.sub(old_pattern, 'require_api_token', content)
    
    # 检查是否有变化
    if content == new_content:
        print("没有找到需要修复的 _get_require_api_key() 调用")
        return
    
    # 写入修改后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # 统计修复数量
    old_count = len(re.findall(old_pattern, content))
    new_count = len(re.findall(old_pattern, new_content))
    
    print(f"成功修复 {old_count - new_count} 个 _get_require_api_key() 调用")
    print("所有API密钥依赖函数已更新为 require_api_token")

if __name__ == "__main__":
    fix_api_key_dependencies()