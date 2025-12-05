"""
多租户认证系统完整性检查脚本
Multi-tenant Authentication System Integrity Check Script

用于检查系统的完整性和依赖项：
1. Python 版本检查
2. 依赖包检查和安装提示
3. 环境变量配置检查
4. 数据库连接检查
5. 模块导入检查
6. 文件系统权限检查

运行方式：
    python "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/check_system_integrity.py"
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import importlib.util

# 添加项目根目录到路径
rag_root = Path(__file__).parent.parent.parent  # "📚 Enhanced RAG & Knowledge Graph"
project_root = rag_root.parent  # 项目根目录
sys.path.insert(0, str(rag_root))
sys.path.insert(0, str(project_root))

# 切换到正确的目录
os.chdir(rag_root)


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {Colors.BOLD}{title}{Colors.END}")
    print("=" * 70)


def print_check(name: str, status: bool, message: str = "", warning: bool = False):
    """打印检查结果"""
    if status:
        icon = f"{Colors.GREEN}✅{Colors.END}"
        status_text = f"{Colors.GREEN}通过{Colors.END}"
    elif warning:
        icon = f"{Colors.YELLOW}⚠️{Colors.END}"
        status_text = f"{Colors.YELLOW}警告{Colors.END}"
    else:
        icon = f"{Colors.RED}❌{Colors.END}"
        status_text = f"{Colors.RED}失败{Colors.END}"
    
    print(f"{icon} {name}: {status_text}", end="")
    if message:
        print(f" - {message}")
    else:
        print()


def check_python_version() -> bool:
    """检查 Python 版本"""
    print_header("检查 1: Python 版本")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    # Python 3.11+ 推荐
    if version.major == 3 and version.minor >= 11:
        print_check("Python 版本", True, f"Python {version_str} (推荐 3.11+)")
        return True
    elif version.major == 3 and version.minor >= 8:
        print_check("Python 版本", True, f"Python {version_str} (最低要求 3.8+)", warning=True)
        return True
    else:
        print_check("Python 版本", False, f"Python {version_str} (需要 3.8+)")
        return False


def check_dependencies() -> Tuple[bool, List[str]]:
    """检查依赖包"""
    print_header("检查 2: Python 依赖包")
    
    # 必需的依赖包
    required_packages = {
        "pydantic": "Pydantic (数据验证)",
        "fastapi": "FastAPI (Web 框架)",
        "jwt": "PyJWT (JWT 处理)",
        "passlib": "Passlib (密码哈希)",
        "bcrypt": "Bcrypt (密码加密)",
        "sqlite3": "SQLite3 (数据库，Python 内置)",
        "dotenv": "python-dotenv (环境变量加载)",
    }
    
    # 可选的依赖包
    optional_packages = {
        "python-jose": "python-jose (JWT 替代方案)",
        "cryptography": "Cryptography (加密库)",
    }
    
    missing_packages = []
    all_passed = True
    
    # 检查必需包
    for package, description in required_packages.items():
        if package == "sqlite3":
            # SQLite3 是内置的
            try:
                import sqlite3
                version = sqlite3.sqlite_version
                print_check(f"{description}", True, f"版本 {version}")
            except ImportError:
                print_check(f"{description}", False, "未找到")
                missing_packages.append("sqlite3")
                all_passed = False
        elif package == "jwt":
            # 检查 PyJWT
            try:
                import jwt
                print_check(f"{description}", True)
            except ImportError:
                # 尝试 python-jose
                try:
                    from jose import jwt as jose_jwt
                    print_check(f"{description}", True, "使用 python-jose")
                except ImportError:
                    print_check(f"{description}", False, "需要安装 PyJWT 或 python-jose[cryptography]")
                    missing_packages.append("PyJWT")
                    all_passed = False
        elif package == "dotenv":
            try:
                import dotenv
                print_check(f"{description}", True)
            except ImportError:
                print_check(f"{description}", False, "需要安装 python-dotenv")
                missing_packages.append("python-dotenv")
                all_passed = False
        else:
            try:
                __import__(package)
                print_check(f"{description}", True)
            except ImportError:
                print_check(f"{description}", False, f"需要安装 {package}")
                missing_packages.append(package)
                all_passed = False
    
    # 检查可选包
    print(f"\n{Colors.BLUE}可选依赖包:{Colors.END}")
    for package, description in optional_packages.items():
        try:
            __import__(package.replace("-", "_"))
            print_check(f"{description}", True, "已安装")
        except ImportError:
            print_check(f"{description}", False, "未安装（可选）", warning=True)
    
    return all_passed, missing_packages


def check_environment_variables() -> bool:
    """检查环境变量配置"""
    print_header("检查 3: 环境变量配置")
    
    # 检查 .env 文件是否存在
    env_file = project_root / ".env"
    if env_file.exists():
        print_check(".env 文件", True, f"路径: {env_file}")
        
        # 加载环境变量
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except Exception as e:
            print_check("加载 .env 文件", False, str(e))
            return False
    else:
        env_example = project_root / "env.example"
        if env_example.exists():
            print_check(".env 文件", False, f"未找到，请复制 env.example 到 .env")
            print(f"  {Colors.YELLOW}提示: cp env.example .env{Colors.END}")
        else:
            print_check(".env 文件", False, "未找到 .env 或 env.example")
        return False
    
    # 检查必需的环境变量
    required_vars = {
        "JWT_SECRET_KEY": "JWT 签名密钥",
    }
    
    optional_vars = {
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "访问令牌过期时间（分钟）",
        "JWT_REFRESH_TOKEN_EXPIRE_DAYS": "刷新令牌过期时间（天）",
        "API_KEY_USE_DATABASE": "是否使用数据库存储 API Key",
        "TOKEN_REVOCATION_ENABLED": "是否启用 Token 撤销",
        "AUDIT_LOGGING_ENABLED": "是否启用审计日志",
    }
    
    all_passed = True
    
    # 检查必需变量
    print(f"\n{Colors.BLUE}必需配置:{Colors.END}")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and value not in ["your-super-secret-jwt-key", "your-secret-key-here"]:
            # 隐藏敏感值
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            print_check(f"{description} ({var})", True, f"已设置: {masked_value}")
        else:
            print_check(f"{description} ({var})", False, "未设置或使用默认值")
            all_passed = False
    
    # 检查可选变量
    print(f"\n{Colors.BLUE}可选配置:{Colors.END}")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print_check(f"{description} ({var})", True, f"已设置: {value}")
        else:
            print_check(f"{description} ({var})", False, "未设置（将使用默认值）", warning=True)
    
    return all_passed


def check_database() -> bool:
    """检查数据库连接"""
    print_header("检查 4: 数据库连接")
    
    try:
        from enterprise.tenancy.database import get_database
        db = get_database()
        print_check("数据库模块导入", True)
        
        # 尝试连接
        conn = db._get_connection()
        if conn:
            print_check("数据库连接", True, "SQLite 连接成功")
            
            # 检查表是否存在
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name IN ('api_keys', 'token_blacklist', 'audit_logs')
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ["api_keys", "token_blacklist", "audit_logs"]
            for table in expected_tables:
                if table in tables:
                    print_check(f"数据表 '{table}'", True)
                else:
                    print_check(f"数据表 '{table}'", False, "表不存在，可能需要初始化")
            
            return len(tables) == len(expected_tables)
        else:
            print_check("数据库连接", False, "无法建立连接")
            return False
            
    except ImportError as e:
        print_check("数据库模块导入", False, str(e))
        return False
    except Exception as e:
        print_check("数据库连接", False, str(e))
        return False


def check_module_imports() -> bool:
    """检查模块导入"""
    print_header("检查 5: 模块导入")
    
    modules_to_check = [
        ("enterprise.tenancy.auth", "认证模块"),
        ("enterprise.tenancy.models", "租户模型"),
        ("enterprise.tenancy.manager", "租户管理器"),
        ("enterprise.tenancy.middleware", "中间件"),
        ("enterprise.tenancy.database", "数据库模块"),
        ("enterprise.tenancy.audit_logging", "日志模块"),
        ("enterprise.tenancy.api", "API 端点"),
    ]
    
    all_passed = True
    
    for module_name, description in modules_to_check:
        try:
            module = __import__(module_name, fromlist=[""])
            print_check(f"{description} ({module_name})", True)
        except ImportError as e:
            print_check(f"{description} ({module_name})", False, str(e))
            all_passed = False
        except Exception as e:
            print_check(f"{description} ({module_name})", False, str(e))
            all_passed = False
    
    return all_passed


def check_file_permissions() -> bool:
    """检查文件系统权限"""
    print_header("检查 6: 文件系统权限")
    
    # 检查关键目录和文件
    paths_to_check = [
        (project_root / "logs", "日志目录", True),
        (project_root / "data", "数据目录", True),
        (rag_root / "enterprise" / "tenancy", "租户模块目录", False),
    ]
    
    all_passed = True
    
    for path, description, is_dir in paths_to_check:
        if is_dir:
            # 检查目录是否存在，不存在则尝试创建
            if path.exists():
                if os.access(path, os.W_OK):
                    print_check(f"{description} ({path})", True, "可写")
                else:
                    print_check(f"{description} ({path})", False, "无写入权限")
                    all_passed = False
            else:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    print_check(f"{description} ({path})", True, "已创建")
                except Exception as e:
                    print_check(f"{description} ({path})", False, f"无法创建: {e}")
                    all_passed = False
        else:
            # 检查文件是否存在
            if path.exists():
                print_check(f"{description} ({path})", True)
            else:
                print_check(f"{description} ({path})", False, "不存在")
                all_passed = False
    
    return all_passed


def generate_install_command(missing_packages: List[str]) -> str:
    """生成安装命令"""
    if not missing_packages:
        return ""
    
    # 包名映射（安装名 -> 包名）
    package_map = {
        "PyJWT": "PyJWT",
        "jwt": "PyJWT",
        "dotenv": "python-dotenv",
        "sqlite3": "",  # 内置，不需要安装
    }
    
    # 过滤和映射包名
    install_packages = []
    for pkg in missing_packages:
        if pkg in package_map:
            mapped = package_map[pkg]
            if mapped and mapped not in install_packages:
                install_packages.append(mapped)
        elif pkg not in install_packages:
            install_packages.append(pkg)
    
    if not install_packages:
        return ""
    
    # 生成命令
    base_packages = ["pydantic", "fastapi", "python-jose[cryptography]", "passlib[bcrypt]", "python-dotenv"]
    
    return f"pip install {' '.join(base_packages)}"


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print(f"  {Colors.BOLD}多租户认证系统完整性检查{Colors.END}")
    print(f"  Multi-tenant Authentication System Integrity Check")
    print("=" * 70)
    print(f"\n项目根目录: {project_root}")
    print(f"工作目录: {rag_root}")
    
    results = []
    
    # 运行所有检查
    results.append(("Python 版本", check_python_version()))
    deps_passed, missing_packages = check_dependencies()
    results.append(("依赖包", deps_passed))
    results.append(("环境变量", check_environment_variables()))
    results.append(("数据库连接", check_database()))
    results.append(("模块导入", check_module_imports()))
    results.append(("文件权限", check_file_permissions()))
    
    # 输出汇总
    print_header("检查结果汇总")
    
    for check_name, passed in results:
        status = f"{Colors.GREEN}✅ 通过{Colors.END}" if passed else f"{Colors.RED}❌ 失败{Colors.END}"
        print(f"  {check_name:20s} {status}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    failed = total - passed
    
    print(f"\n  总计: {passed}/{total} 通过, {failed} 失败")
    
    # 如果有缺失的依赖包，显示安装命令
    if missing_packages:
        print(f"\n{Colors.YELLOW}缺失的依赖包:{Colors.END}")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        
        install_cmd = generate_install_command(missing_packages)
        if install_cmd:
            print(f"\n{Colors.BLUE}安装命令:{Colors.END}")
            print(f"  {install_cmd}")
    
    # 最终结果
    if passed == total:
        print(f"\n{Colors.GREEN}{'🎉' * 35}{Colors.END}")
        print(f"  {Colors.BOLD}{Colors.GREEN}所有检查通过！系统完整性良好。{Colors.END}")
        print(f"{Colors.GREEN}{'🎉' * 35}{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{'⚠️' * 35}{Colors.END}")
        print(f"  {Colors.BOLD}{Colors.YELLOW}有 {failed} 项检查失败，请根据上述信息修复问题。{Colors.END}")
        print(f"{Colors.YELLOW}{'⚠️' * 35}{Colors.END}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

