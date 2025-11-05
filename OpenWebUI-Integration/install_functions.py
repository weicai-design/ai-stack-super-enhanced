#!/usr/bin/env python3
"""
OpenWebUI Functions 自动安装脚本
通过API批量安装Functions到OpenWebUI
"""

import requests
import json
import os
from pathlib import Path
import time

# OpenWebUI配置
OPENWEBUI_URL = "http://localhost:3000"
FUNCTIONS_DIR = Path(__file__).parent / "openwebui-functions"

# 颜色输出
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✅ {msg}{NC}")

def print_error(msg):
    print(f"{RED}❌ {msg}{NC}")

def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{NC}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{NC}")


def check_openwebui():
    """检查OpenWebUI是否运行"""
    try:
        response = requests.get(f"{OPENWEBUI_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("OpenWebUI运行正常")
            return True
        else:
            print_error(f"OpenWebUI响应异常: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"无法连接OpenWebUI: {e}")
        print_info("请确保OpenWebUI正在运行: http://localhost:3000")
        return False


def get_api_key():
    """获取API密钥"""
    print("\n" + "="*60)
    print("📋 OpenWebUI API密钥获取方法：")
    print("="*60)
    print("\n1. 访问 http://localhost:3000")
    print("2. 登录账号")
    print("3. 点击左下角头像 → Settings")
    print("4. 左侧菜单 → Account")
    print("5. 找到 'API Keys' 部分")
    print("6. 点击 'Create new API key'")
    print("7. 复制生成的API密钥")
    print("\n" + "="*60)
    
    api_key = input("\n请粘贴API密钥 (或按Enter跳过，使用手动安装方法): ").strip()
    
    return api_key if api_key else None


def install_function_via_api(api_key, function_file):
    """通过API安装Function"""
    try:
        # 读取Function代码
        with open(function_file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 提取Function元数据
        import re
        title_match = re.search(r'title:\s*(.+)', code)
        title = title_match.group(1).strip() if title_match else function_file.stem
        
        # 准备请求
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "id": function_file.stem,
            "name": title,
            "content": code,
            "meta": {
                "manifest": {}
            }
        }
        
        # 发送请求
        response = requests.post(
            f"{OPENWEBUI_URL}/api/v1/functions/create",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            print_success(f"已安装: {title}")
            return True
        else:
            print_error(f"安装失败 ({title}): {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print_error(f"安装错误: {e}")
        return False


def manual_install_guide():
    """显示手动安装指南"""
    print("\n" + "="*60)
    print("📖 手动安装Functions指南")
    print("="*60)
    
    functions = list(FUNCTIONS_DIR.glob("*.py"))
    
    print(f"\n共需安装 {len(functions)} 个Functions：\n")
    
    for i, func_file in enumerate(functions, 1):
        print(f"{i}. {func_file.name}")
    
    print("\n" + "-"*60)
    print("手动安装步骤（每个Function重复）：")
    print("-"*60)
    
    print("\n1️⃣  打开Functions管理页")
    print("   http://localhost:3000/admin/functions")
    
    print("\n2️⃣  点击 '+' 添加Function")
    
    print("\n3️⃣  复制Function代码")
    print("   执行命令（会复制到剪贴板）：")
    
    for func_file in functions:
        print(f"\n   cat {func_file} | pbcopy")
        print(f"   # 然后在OpenWebUI中粘贴 (Command+V)")
        print(f"   # 保存并配置 {func_file.name}")
    
    print("\n4️⃣  配置API端点（重要！）")
    print("   对于每个Function，点击⚙️配置：")
    print("\n   RAG Integration:")
    print("     rag_api_endpoint: http://host.docker.internal:8011")
    print("\n   ERP Query:")
    print("     erp_api_endpoint: http://host.docker.internal:8013")
    print("\n   Stock Analysis:")
    print("     stock_api_endpoint: http://host.docker.internal:8014")
    print("\n   Content Creation:")
    print("     content_api_endpoint: http://host.docker.internal:8016")
    
    print("\n5️⃣  启用所有Functions")
    print("   确保每个Function的开关是绿色（已启用）")
    
    print("\n6️⃣  测试")
    print("   在聊天框输入: /aistack status")
    
    print("\n" + "="*60)


def copy_to_clipboard(function_file):
    """复制Function代码到剪贴板"""
    try:
        os.system(f"cat {function_file} | pbcopy")
        print_success(f"已复制到剪贴板: {function_file.name}")
        print_info("现在可以在OpenWebUI中粘贴 (Command+V)")
        return True
    except Exception as e:
        print_error(f"复制失败: {e}")
        return False


def interactive_install():
    """交互式安装"""
    print("\n" + "="*60)
    print("🚀 OpenWebUI Functions 交互式安装")
    print("="*60)
    
    functions = sorted(FUNCTIONS_DIR.glob("*.py"))
    
    print(f"\n找到 {len(functions)} 个Functions：\n")
    
    for i, func_file in enumerate(functions, 1):
        # 读取Function标题
        with open(func_file, 'r') as f:
            content = f.read()
            import re
            title_match = re.search(r'title:\s*(.+)', content)
            title = title_match.group(1).strip() if title_match else func_file.name
        
        print(f"{i}. {title} ({func_file.name})")
    
    print("\n" + "-"*60)
    print("交互式安装步骤：")
    print("-"*60)
    
    print("\n我会逐个帮你复制Function代码到剪贴板。")
    print("你需要在OpenWebUI中粘贴并保存。\n")
    
    input("按Enter开始... ")
    
    for i, func_file in enumerate(functions, 1):
        with open(func_file, 'r') as f:
            content = f.read()
            import re
            title_match = re.search(r'title:\s*(.+)', content)
            title = title_match.group(1).strip() if title_match else func_file.name
        
        print("\n" + "="*60)
        print(f"Function {i}/{len(functions)}: {title}")
        print("="*60)
        
        # 复制到剪贴板
        os.system(f"cat {func_file} | pbcopy")
        
        print_success(f"✅ 已复制: {func_file.name}")
        print("\n📋 现在在OpenWebUI中：")
        print("   1. 点击 '+' 添加Function")
        print("   2. 粘贴代码 (Command+V)")
        print("   3. 点击 Save")
        
        # 显示配置提示
        if "rag" in func_file.name:
            print("\n⚙️  配置：")
            print("   rag_api_endpoint: http://host.docker.internal:8011")
        elif "erp" in func_file.name:
            print("\n⚙️  配置：")
            print("   erp_api_endpoint: http://host.docker.internal:8013")
        elif "stock" in func_file.name:
            print("\n⚙️  配置：")
            print("   stock_api_endpoint: http://host.docker.internal:8014")
        elif "content" in func_file.name:
            print("\n⚙️  配置：")
            print("   content_api_endpoint: http://host.docker.internal:8016")
        
        if i < len(functions):
            input(f"\n完成后按Enter继续下一个 ({i+1}/{len(functions)})... ")
        else:
            print(f"\n🎉 所有Functions已准备完毕！")


def main():
    print("\n" + "="*60)
    print("🌐 OpenWebUI Functions 自动安装工具")
    print("="*60)
    
    # 检查OpenWebUI
    if not check_openwebui():
        return
    
    # 检查Functions文件
    functions = list(FUNCTIONS_DIR.glob("*.py"))
    if not functions:
        print_error(f"未找到Functions文件: {FUNCTIONS_DIR}")
        return
    
    print_info(f"找到 {len(functions)} 个Functions")
    
    # 选择安装方法
    print("\n" + "="*60)
    print("选择安装方法：")
    print("="*60)
    print("\n1. 交互式安装（逐个复制到剪贴板）⭐ 推荐")
    print("2. 通过API安装（需要API密钥）")
    print("3. 显示手动安装指南")
    print("4. 退出")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == "1":
        interactive_install()
    elif choice == "2":
        api_key = get_api_key()
        if api_key:
            print("\n开始通过API安装Functions...")
            success_count = 0
            for func_file in functions:
                if install_function_via_api(api_key, func_file):
                    success_count += 1
                time.sleep(1)
            print(f"\n✅ 成功安装 {success_count}/{len(functions)} 个Functions")
        else:
            print_warning("未提供API密钥，切换到手动安装模式")
            manual_install_guide()
    elif choice == "3":
        manual_install_guide()
    else:
        print("退出")


if __name__ == "__main__":
    main()



