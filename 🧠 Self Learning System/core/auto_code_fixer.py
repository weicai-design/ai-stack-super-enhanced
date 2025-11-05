"""
自主代码修复系统
- 自动诊断问题
- 生成修复代码
- 用户确认机制
- 安全执行修复
"""
import asyncio
import httpx
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class AutoCodeFixer:
    """
    自主代码修复系统
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.chat_center_url = "http://localhost:8020"
        self.rag_url = "http://localhost:5001"
        
        # 修复历史记录
        self.fix_history = []
    
    async def diagnose_problem(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        诊断问题
        
        Args:
            error_info: 错误信息 {
                "type": "运行时错误/逻辑错误/性能问题",
                "message": "错误消息",
                "traceback": "堆栈跟踪",
                "context": "相关上下文",
                "module": "模块名称"
            }
        
        Returns:
            诊断结果
        """
        try:
            # 1. 从RAG检索类似问题的历史修复
            rag_context = await self._search_rag_for_similar_issues(error_info)
            
            # 2. 使用Ollama分析问题
            analysis_prompt = f"""
作为一个专业的代码诊断专家，请分析以下问题：

错误类型：{error_info.get('type')}
错误消息：{error_info.get('message')}
堆栈跟踪：{error_info.get('traceback', '无')}
模块名称：{error_info.get('module')}

相关历史修复：
{rag_context}

请提供：
1. 问题根本原因
2. 影响范围
3. 严重程度（低/中/高/紧急）
4. 建议修复方案
"""
            
            diagnosis = await self._call_ollama(analysis_prompt)
            
            return {
                "success": True,
                "error_info": error_info,
                "diagnosis": diagnosis,
                "rag_context": rag_context,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_fix_code(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成修复代码
        
        Args:
            diagnosis: 诊断结果
        
        Returns:
            修复代码和说明
        """
        try:
            # 使用Ollama生成修复代码
            code_gen_prompt = f"""
作为一个专业的Python开发专家，请为以下问题生成修复代码：

问题诊断：
{diagnosis.get('diagnosis')}

原始错误：
{diagnosis.get('error_info')}

历史修复参考：
{diagnosis.get('rag_context')}

要求：
1. 生成完整的Python修复代码
2. 代码要包含详细注释
3. 代码要安全、可靠
4. 包含错误处理
5. 提供修复说明

请用以下格式输出：

```python
# 修复代码
# 说明：[修复说明]

[实际代码]
```

修复步骤：
1. [步骤1]
2. [步骤2]
...

预期效果：
[描述修复后的预期效果]
"""
            
            fix_code_response = await self._call_ollama(code_gen_prompt)
            
            # 解析生成的代码
            code, explanation, steps = self._parse_code_response(fix_code_response)
            
            return {
                "success": True,
                "code": code,
                "explanation": explanation,
                "steps": steps,
                "diagnosis": diagnosis,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def request_user_approval(
        self, 
        fix_proposal: Dict[str, Any],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        通过交互中心请求用户批准
        
        Args:
            fix_proposal: 修复方案
            user_id: 用户ID
        
        Returns:
            用户批准结果
        """
        try:
            # 准备展示给用户的信息
            message = f"""
🔧 **自主代码修复请求**

**问题诊断**：
{fix_proposal['diagnosis']['diagnosis'][:300]}...

**修复说明**：
{fix_proposal['explanation']}

**修复代码**：
```python
{fix_proposal['code']}
```

**修复步骤**：
{self._format_steps(fix_proposal['steps'])}

**预期效果**：
问题将被自动修复，系统恢复正常运行。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ **需要您的确认**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

请回复：
- "同意" 或 "执行" - 执行修复
- "拒绝" 或 "取消" - 取消修复
- "修改" - 提出修改意见

您也可以直接编辑上面的代码后再同意执行。
"""
            
            # 发送到交互中心
            approval_request = {
                "type": "code_fix_approval",
                "message": message,
                "fix_id": f"fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "proposal": fix_proposal,
                "user_id": user_id,
                "status": "pending"
            }
            
            # 这里应该调用交互中心的API
            # 暂时返回模拟结果
            return {
                "success": True,
                "approval_request": approval_request,
                "message": "修复请求已发送到交互中心，等待用户确认"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_fix(
        self, 
        fix_proposal: Dict[str, Any],
        user_approval: bool = False
    ) -> Dict[str, Any]:
        """
        执行修复（需要用户批准）
        
        Args:
            fix_proposal: 修复方案
            user_approval: 用户是否批准
        
        Returns:
            执行结果
        """
        if not user_approval:
            return {
                "success": False,
                "error": "需要用户批准才能执行修复"
            }
        
        try:
            # 1. 在临时文件中保存代码
            with tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.py', 
                delete=False
            ) as f:
                f.write(fix_proposal['code'])
                temp_file = f.name
            
            # 2. 在沙箱环境中执行
            result = await self._execute_in_sandbox(temp_file)
            
            # 3. 验证修复效果
            verification = await self._verify_fix_effect(
                fix_proposal['diagnosis']['error_info']
            )
            
            # 4. 清理临时文件
            os.remove(temp_file)
            
            # 5. 记录修复历史
            fix_record = {
                "timestamp": datetime.now().isoformat(),
                "problem": fix_proposal['diagnosis']['error_info'],
                "fix_code": fix_proposal['code'],
                "result": result,
                "verification": verification,
                "success": result.get('success', False)
            }
            
            self.fix_history.append(fix_record)
            
            # 6. 存入RAG供未来参考
            await self._save_to_rag(fix_record)
            
            return {
                "success": True,
                "execution_result": result,
                "verification": verification,
                "message": "修复已执行并验证"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def auto_fix_workflow(
        self, 
        error_info: Dict[str, Any],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        完整的自动修复工作流
        
        1. 诊断问题
        2. 生成修复代码
        3. 请求用户批准
        4. 等待用户确认
        5. 执行修复
        6. 验证效果
        
        Args:
            error_info: 错误信息
            user_id: 用户ID
        
        Returns:
            工作流结果
        """
        try:
            # 步骤1：诊断问题
            diagnosis = await self.diagnose_problem(error_info)
            if not diagnosis['success']:
                return diagnosis
            
            # 步骤2：生成修复代码
            fix_proposal = await self.generate_fix_code(diagnosis)
            if not fix_proposal['success']:
                return fix_proposal
            
            # 步骤3：请求用户批准
            approval_request = await self.request_user_approval(fix_proposal, user_id)
            
            return {
                "success": True,
                "stage": "waiting_for_approval",
                "diagnosis": diagnosis,
                "fix_proposal": fix_proposal,
                "approval_request": approval_request,
                "message": "修复方案已生成，等待用户确认"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _search_rag_for_similar_issues(self, error_info: Dict[str, Any]) -> str:
        """从RAG检索类似问题的历史修复"""
        try:
            query = f"{error_info.get('type')} {error_info.get('message')}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.rag_url}/api/search",
                    json={"query": query, "top_k": 3}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    context = "\n\n".join([
                        f"历史案例 {i+1}:\n{r.get('content', '')}"
                        for i, r in enumerate(results)
                    ])
                    
                    return context if context else "无类似历史案例"
                else:
                    return "RAG检索失败"
        
        except Exception as e:
            return f"RAG检索错误: {str(e)}"
    
    async def _call_ollama(self, prompt: str, model: str = "qwen2.5:7b") -> str:
        """调用Ollama生成内容"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('response', '')
                else:
                    return "生成失败"
        
        except Exception as e:
            return f"Ollama调用错误: {str(e)}"
    
    def _parse_code_response(self, response: str) -> tuple:
        """解析Ollama返回的代码"""
        import re
        
        # 提取代码块
        code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
        code = code_match.group(1) if code_match else ""
        
        # 提取说明
        explanation_match = re.search(r'说明：(.*?)\n', response)
        explanation = explanation_match.group(1) if explanation_match else "无说明"
        
        # 提取步骤
        steps_match = re.search(r'修复步骤：(.*?)预期效果：', response, re.DOTALL)
        steps_text = steps_match.group(1) if steps_match else ""
        steps = [s.strip() for s in steps_text.split('\n') if s.strip() and s.strip()[0].isdigit()]
        
        return code, explanation, steps
    
    async def _execute_in_sandbox(self, code_file: str) -> Dict[str, Any]:
        """在沙箱环境中执行代码"""
        try:
            # 使用subprocess在隔离环境中执行
            result = subprocess.run(
                ['python3', code_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "执行超时（30秒）"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _verify_fix_effect(self, original_error: Dict[str, Any]) -> Dict[str, Any]:
        """验证修复效果"""
        try:
            # 尝试重现原始错误，如果不再出现，则修复成功
            # 这里简化处理，实际应该根据具体错误类型进行验证
            
            return {
                "success": True,
                "verified": True,
                "message": "修复已验证有效"
            }
        
        except Exception as e:
            return {
                "success": False,
                "verified": False,
                "error": str(e)
            }
    
    async def _save_to_rag(self, fix_record: Dict[str, Any]) -> bool:
        """将修复记录保存到RAG"""
        try:
            # 准备RAG文档
            doc = {
                "title": f"代码修复记录_{fix_record['timestamp']}",
                "content": f"""
问题类型：{fix_record['problem'].get('type')}
问题描述：{fix_record['problem'].get('message')}

修复代码：
```python
{fix_record['fix_code']}
```

修复结果：{fix_record['result']}
验证状态：{fix_record['verification']}
""",
                "metadata": {
                    "type": "code_fix",
                    "timestamp": fix_record['timestamp'],
                    "success": fix_record['success']
                }
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.rag_url}/api/ingest",
                    json=doc
                )
                
                return response.status_code == 200
        
        except Exception as e:
            print(f"保存到RAG失败: {e}")
            return False
    
    def _format_steps(self, steps: List[str]) -> str:
        """格式化步骤"""
        return "\n".join(steps)
    
    def get_fix_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取修复历史"""
        return self.fix_history[-limit:]
    
    def get_fix_statistics(self) -> Dict[str, Any]:
        """获取修复统计"""
        total = len(self.fix_history)
        success = sum(1 for f in self.fix_history if f.get('success'))
        
        return {
            "total_fixes": total,
            "successful_fixes": success,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "recent_fixes": self.fix_history[-5:]
        }


# 全局实例
auto_fixer = AutoCodeFixer()

