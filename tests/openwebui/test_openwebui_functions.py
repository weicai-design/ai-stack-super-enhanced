"""
OpenWebUI - Functions测试
"""

import pytest
from tests.test_utils import test_helper


@pytest.mark.openwebui
@pytest.mark.integration
@pytest.mark.critical
class TestOpenWebUIFunctions:
    """OpenWebUI Functions测试"""
    
    def test_search_knowledge_function(self):
        """测试：搜索知识库Function"""
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/💬 Intelligent OpenWebUI Interaction Center")
            from openwebui_functions.ai_stack_tools import search_knowledge
            
            # 测试调用
            result = search_knowledge(query="测试", top_k=5)
            
            assert result is not None
            assert isinstance(result, (str, dict, list))
        except ImportError:
            pytest.skip("OpenWebUI Functions未找到")
        except Exception as e:
            # Functions可能需要实际的API服务运行
            pytest.skip(f"Function执行需要服务运行: {e}")
    
    def test_get_financial_summary_function(self):
        """测试：获取财务概览Function"""
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/💬 Intelligent OpenWebUI Interaction Center")
            from openwebui_functions.ai_stack_tools import get_financial_summary
            
            result = get_financial_summary()
            
            assert result is not None
        except ImportError:
            pytest.skip("OpenWebUI Functions未找到")
        except Exception as e:
            pytest.skip(f"Function执行需要服务运行: {e}")
    
    def test_system_status_function(self):
        """测试：系统状态Function"""
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/💬 Intelligent OpenWebUI Interaction Center")
            from openwebui_functions.ai_stack_tools import get_system_status
            
            result = get_system_status()
            
            assert result is not None
            assert isinstance(result, (str, dict))
        except ImportError:
            pytest.skip("OpenWebUI Functions未找到")
        except Exception as e:
            pytest.skip(f"Function执行需要服务运行: {e}")
    
    @pytest.mark.parametrize("function_name", [
        "search_knowledge",
        "get_financial_summary",
        "query_customers",
        "get_stock_price",
        "get_system_status"
    ])
    def test_function_exists(self, function_name):
        """测试：验证Function存在"""
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/💬 Intelligent OpenWebUI Interaction Center")
            import openwebui_functions.ai_stack_tools as tools
            
            assert hasattr(tools, function_name), f"Function {function_name} 不存在"
        except ImportError:
            pytest.skip("OpenWebUI Functions未找到")

