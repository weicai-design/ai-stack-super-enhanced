"""
API密钥配置向导
帮助用户快速配置所有外部API密钥
"""
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


class APIKeyConfigurator:
    """API密钥配置向导"""
    
    def __init__(self, env_file_path: str = None):
        """
        初始化配置向导
        
        Args:
            env_file_path: .env文件路径
        """
        if env_file_path is None:
            # 默认在项目根目录
            self.env_file_path = Path(__file__).parent.parent / ".env"
        else:
            self.env_file_path = Path(env_file_path)
        
        self.api_configs = self._init_api_configs()
    
    def _init_api_configs(self) -> Dict[str, Dict[str, Any]]:
        """初始化API配置信息"""
        return {
            "同花顺": {
                "env_keys": ["THS_API_KEY", "THS_SECRET_KEY"],
                "description": "同花顺股票交易API",
                "registration_url": "https://open.10jqka.com.cn/",
                "documentation_url": "https://open.10jqka.com.cn/doc/",
                "features": ["实时行情", "历史数据", "股票交易"],
                "required": False,
                "priority": "high",
                "example": {
                    "THS_API_KEY": "your_ths_api_key_here",
                    "THS_SECRET_KEY": "your_ths_secret_key_here"
                }
            },
            "小红书": {
                "env_keys": ["XHS_API_KEY", "XHS_APP_ID", "XHS_APP_SECRET"],
                "description": "小红书内容发布API",
                "registration_url": "https://open.xiaohongshu.com/",
                "documentation_url": "https://open.xiaohongshu.com/docs",
                "features": ["内容发布", "数据统计", "粉丝管理"],
                "required": False,
                "priority": "medium",
                "example": {
                    "XHS_API_KEY": "your_xhs_api_key_here",
                    "XHS_APP_ID": "your_app_id_here",
                    "XHS_APP_SECRET": "your_app_secret_here"
                }
            },
            "抖音": {
                "env_keys": ["DOUYIN_API_KEY", "DOUYIN_APP_ID", "DOUYIN_APP_SECRET"],
                "description": "抖音开放平台API",
                "registration_url": "https://open.douyin.com/",
                "documentation_url": "https://open.douyin.com/platform/doc",
                "features": ["视频发布", "数据分析", "互动管理"],
                "required": False,
                "priority": "medium",
                "example": {
                    "DOUYIN_API_KEY": "your_douyin_api_key_here",
                    "DOUYIN_APP_ID": "your_app_id_here",
                    "DOUYIN_APP_SECRET": "your_app_secret_here"
                }
            },
            "知乎": {
                "env_keys": ["ZHIHU_API_KEY", "ZHIHU_APP_ID"],
                "description": "知乎开放平台API",
                "registration_url": "https://open.zhihu.com/",
                "documentation_url": "https://open.zhihu.com/api",
                "features": ["文章发布", "数据统计"],
                "required": False,
                "priority": "low",
                "example": {
                    "ZHIHU_API_KEY": "your_zhihu_api_key_here",
                    "ZHIHU_APP_ID": "your_app_id_here"
                }
            },
            "今日头条": {
                "env_keys": ["TOUTIAO_API_KEY", "TOUTIAO_APP_ID", "TOUTIAO_APP_SECRET"],
                "description": "今日头条开放平台API",
                "registration_url": "https://open.toutiao.com/",
                "documentation_url": "https://open.toutiao.com/docs",
                "features": ["文章发布", "视频发布", "数据分析"],
                "required": False,
                "priority": "low",
                "example": {
                    "TOUTIAO_API_KEY": "your_toutiao_api_key_here",
                    "TOUTIAO_APP_ID": "your_app_id_here",
                    "TOUTIAO_APP_SECRET": "your_app_secret_here"
                }
            }
        }
    
    def generate_configuration_guide(self) -> str:
        """
        生成配置指南
        
        Returns:
            配置指南文本
        """
        guide = """
╔════════════════════════════════════════════════════════════════╗
║                     API密钥配置向导                              ║
║                  AI-Stack API Key Configurator                 ║
╚════════════════════════════════════════════════════════════════╝

本向导将帮助您快速配置AI-Stack系统所需的外部API密钥。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 需要配置的API服务
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        for i, (service_name, config) in enumerate(self.api_configs.items(), 1):
            priority_label = {
                "high": "高优先级 🔴",
                "medium": "中优先级 🟡",
                "low": "低优先级 🟢"
            }.get(config["priority"], "")
            
            guide += f"""
{i}. {service_name} API  [{priority_label}]
   
   📝 描述: {config['description']}
   
   🔑 需要的密钥:
"""
            for key in config["env_keys"]:
                guide += f"      • {key}\n"
            
            guide += f"""   
   ✨ 功能:
"""
            for feature in config["features"]:
                guide += f"      • {feature}\n"
            
            guide += f"""   
   📚 注册地址: {config['registration_url']}
   📖 文档地址: {config['documentation_url']}

"""
        
        guide += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 配置步骤
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

步骤1: 申请API密钥
      访问上述各服务的注册地址，申请开发者账号并获取API密钥

步骤2: 配置密钥
      方式A（推荐）：使用交互式配置
      $ python api_key_configurator.py --interactive
      
      方式B：手动编辑.env文件
      $ nano .env
      
      方式C：使用本向导的set_api_key()方法

步骤3: 验证配置
      $ python api_key_configurator.py --validate

步骤4: 重启相关服务
      $ ./scripts/restart_services.sh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  重要提示
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. API密钥是敏感信息，请妥善保管
2. 不要将.env文件提交到代码仓库
3. 定期更换API密钥以确保安全
4. 某些API可能需要付费或有调用限制
5. 如不需要某个功能，可以跳过对应API的配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 常见问题
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q: 必须配置所有API吗？
A: 不是。只配置您需要使用的功能对应的API即可。

Q: 如何知道密钥是否配置正确？
A: 运行验证命令或查看服务日志。

Q: 配置后需要重启吗？
A: 是的，需要重启相关服务才能生效。

Q: 如何保护API密钥安全？
A: .env文件已在.gitignore中，不会被提交到代码仓库。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

需要帮助？请查看文档或联系技术支持。
"""
        
        return guide
    
    def set_api_key(
        self,
        service_name: str,
        key_value_pairs: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        设置API密钥
        
        Args:
            service_name: 服务名称
            key_value_pairs: 密钥键值对
        
        Returns:
            设置结果
        """
        if service_name not in self.api_configs:
            return {
                "success": False,
                "message": f"未知的服务: {service_name}"
            }
        
        # 读取现有.env文件
        env_content = {}
        if self.env_file_path.exists():
            with open(self.env_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_content[key.strip()] = value.strip()
        
        # 更新密钥
        for key, value in key_value_pairs.items():
            env_content[key] = value
        
        # 写回.env文件
        with open(self.env_file_path, 'w', encoding='utf-8') as f:
            f.write("# AI-Stack API配置文件\n")
            f.write("# 此文件包含敏感信息，请勿提交到代码仓库\n\n")
            
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")
        
        return {
            "success": True,
            "message": f"{service_name} API密钥已配置",
            "keys_set": list(key_value_pairs.keys())
        }
    
    def validate_configuration(
        self,
        service_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        验证API配置
        
        Args:
            service_name: 服务名称（可选，为空则验证所有）
        
        Returns:
            验证结果
        """
        # 读取.env文件
        env_vars = {}
        if self.env_file_path.exists():
            with open(self.env_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        
        # 验证
        results = {}
        services_to_check = (
            [service_name] if service_name else self.api_configs.keys()
        )
        
        for service in services_to_check:
            if service not in self.api_configs:
                continue
            
            config = self.api_configs[service]
            required_keys = config["env_keys"]
            
            missing_keys = []
            configured_keys = []
            
            for key in required_keys:
                if key in env_vars and env_vars[key] and env_vars[key] != f"your_{key.lower()}_here":
                    configured_keys.append(key)
                else:
                    missing_keys.append(key)
            
            is_configured = len(missing_keys) == 0
            
            results[service] = {
                "configured": is_configured,
                "configured_keys": configured_keys,
                "missing_keys": missing_keys,
                "status": "✅ 已配置" if is_configured else "⚠️ 未配置" if not configured_keys else "🔶 部分配置"
            }
        
        all_configured = all(r["configured"] for r in results.values())
        
        return {
            "success": True,
            "all_configured": all_configured,
            "results": results,
            "summary": self._generate_validation_summary(results)
        }
    
    def _generate_validation_summary(
        self,
        results: Dict[str, Dict[str, Any]]
    ) -> str:
        """生成验证摘要"""
        summary = "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        summary += "           API配置验证结果\n"
        summary += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for service, result in results.items():
            summary += f"{service}: {result['status']}\n"
            if result['configured_keys']:
                summary += f"  ✓ 已配置: {', '.join(result['configured_keys'])}\n"
            if result['missing_keys']:
                summary += f"  ✗ 缺失: {', '.join(result['missing_keys'])}\n"
            summary += "\n"
        
        return summary
    
    def generate_env_template(self) -> str:
        """
        生成.env模板文件
        
        Returns:
            模板内容
        """
        template = """# AI-Stack API配置文件
# 此文件包含敏感信息，请勿提交到代码仓库
# 复制此文件为.env并填入真实的API密钥

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 核心服务配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Ollama配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:14b

# 数据库配置
DATABASE_URL=sqlite:///./ai_stack.db

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 股票交易API（高优先级）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 同花顺API
THS_API_KEY=your_ths_api_key_here
THS_SECRET_KEY=your_ths_secret_key_here

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 内容发布API（中优先级）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 小红书API
XHS_API_KEY=your_xhs_api_key_here
XHS_APP_ID=your_app_id_here
XHS_APP_SECRET=your_app_secret_here

# 抖音API
DOUYIN_API_KEY=your_douyin_api_key_here
DOUYIN_APP_ID=your_app_id_here
DOUYIN_APP_SECRET=your_app_secret_here

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 内容平台API（低优先级）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 知乎API
ZHIHU_API_KEY=your_zhihu_api_key_here
ZHIHU_APP_ID=your_app_id_here

# 今日头条API
TOUTIAO_API_KEY=your_toutiao_api_key_here
TOUTIAO_APP_ID=your_app_id_here
TOUTIAO_APP_SECRET=your_app_secret_here

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 其他配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 日志级别
LOG_LEVEL=INFO

# 系统运行端口
CHAT_SERVER_PORT=8020
RAG_SERVER_PORT=8011
ERP_SERVER_PORT=8013
"""
        return template
    
    def create_env_file(self, force: bool = False) -> Dict[str, Any]:
        """
        创建.env文件
        
        Args:
            force: 是否强制覆盖
        
        Returns:
            创建结果
        """
        if self.env_file_path.exists() and not force:
            return {
                "success": False,
                "message": ".env文件已存在，使用force=True强制覆盖"
            }
        
        template = self.generate_env_template()
        
        with open(self.env_file_path, 'w', encoding='utf-8') as f:
            f.write(template)
        
        return {
            "success": True,
            "message": f".env文件已创建: {self.env_file_path}",
            "next_steps": [
                "编辑.env文件，填入真实的API密钥",
                "运行验证: python api_key_configurator.py --validate",
                "重启服务使配置生效"
            ]
        }


# 命令行接口
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-Stack API密钥配置向导")
    parser.add_argument("--guide", action="store_true", help="显示配置指南")
    parser.add_argument("--validate", action="store_true", help="验证API配置")
    parser.add_argument("--create-env", action="store_true", help="创建.env模板文件")
    parser.add_argument("--force", action="store_true", help="强制覆盖现有文件")
    
    args = parser.parse_args()
    
    configurator = APIKeyConfigurator()
    
    if args.guide:
        print(configurator.generate_configuration_guide())
    
    elif args.validate:
        result = configurator.validate_configuration()
        print(result["summary"])
    
    elif args.create_env:
        result = configurator.create_env_file(force=args.force)
        print(f"{'✅' if result['success'] else '❌'} {result['message']}")
        if result.get("next_steps"):
            print("\n下一步:")
            for step in result["next_steps"]:
                print(f"  {step}")
    
    else:
        # 默认显示配置指南
        print(configurator.generate_configuration_guide())



























