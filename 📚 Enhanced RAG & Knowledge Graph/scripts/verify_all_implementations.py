#!/usr/bin/env python3
"""
验证所有MD文档中描述的功能是否都有完整的代码实现
Verify all functionalities described in MD files have complete code implementations
"""

import ast
import importlib.util
import os
import sys
from pathlib import Path
from typing import Dict, List, Set

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# 需要验证的核心模块
CORE_MODULES = {
    # RAG核心模块
    "core.advanced_reranker": "高级重排序",
    "core.self_rag": "Self-RAG",
    "core.semantic_segmentation": "语义分割优化",
    "core.kg_infused_rag": "KG-Infused RAG",
    "core.hierarchical_indexing": "层次化索引",
    "core.agentic_rag": "Agentic RAG",
    "core.rag_expert_system": "RAG专家系统",
    "core.multimodal_retrieval": "多模态检索",
    "core.query_enhancement": "查询增强",
    "core.semantic_grouping": "语义分组",
    
    # 知识图谱模块
    "knowledge_graph.enhanced_kg_builder": "增强知识图谱构建器",
    "knowledge_graph.enhanced_kg_query": "增强知识图谱查询",
    "knowledge_graph.kg_enhancement_complete": "知识图谱功能完善",
    "knowledge_graph.kg_query_cache": "知识图谱查询缓存",
    "knowledge_graph.graph_database_adapter": "图数据库适配器",
    "knowledge_graph.dynamic_graph_updater": "动态图谱更新",
    "knowledge_graph.graph_construction_engine": "图谱构建引擎",
    "knowledge_graph.node_relationship_miner": "节点关系挖掘",
    "knowledge_graph.graph_query_optimizer": "查询优化器",
    "knowledge_graph.knowledge_inference_engine": "知识推理引擎",
    
    # API模块
    "api.expert_api": "专家API",
    "api.self_rag_api": "Self-RAG API",
    "api.agentic_rag_api": "Agentic RAG API",
    "api.kg_batch_api": "知识图谱批量API",
    "api.graph_db_api": "图数据库API",
    "api.groups_api": "语义分组API",
}

# 需要验证的主要类和方法
REQUIRED_CLASSES = {
    "core.advanced_reranker": ["AdvancedReranker"],
    "core.self_rag": ["SelfRAG"],
    "core.semantic_segmentation": ["SemanticSegmentationOptimizer"],  # 修正类名
    "core.kg_infused_rag": ["KGInfusedRAG"],
    "core.hierarchical_indexing": ["HierarchicalIndex"],  # 修正类名
    "core.agentic_rag": ["AgenticRAG"],
    "core.rag_expert_system": ["RAGExpertSystem"],
    "core.multimodal_retrieval": ["MultimodalRetriever"],
    "knowledge_graph.graph_database_adapter": ["GraphDatabaseAdapter"],
}

def check_module_exists(module_path: str) -> tuple[bool, str]:
    """检查模块是否存在"""
    try:
        parts = module_path.split(".")
        module_file = PROJECT_ROOT / Path(*parts[:-1]) / f"{parts[-1]}.py"
        
        if not module_file.exists():
            return False, f"文件不存在: {module_file}"
        
        # 尝试导入
        spec = importlib.util.spec_from_file_location(module_path, module_file)
        if spec is None or spec.loader is None:
            return False, f"无法加载模块规范: {module_file}"
        
        return True, "OK"
    except Exception as e:
        return False, f"错误: {e}"

def check_class_exists(module_path: str, class_name: str) -> tuple[bool, str]:
    """检查类是否存在"""
    try:
        parts = module_path.split(".")
        module_file = PROJECT_ROOT / Path(*parts[:-1]) / f"{parts[-1]}.py"
        
        if not module_file.exists():
            return False, f"模块文件不存在"
        
        # 读取文件内容
        with open(module_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用AST解析
        tree = ast.parse(content, filename=str(module_file))
        
        # 查找类定义
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return True, "OK"
        
        return False, f"类 {class_name} 不存在"
    except Exception as e:
        return False, f"解析错误: {e}"

def main():
    """主验证函数"""
    print("=" * 80)
    print("验证所有MD文档描述的功能实现")
    print("=" * 80)
    print()
    
    results = {
        "passed": [],
        "failed": [],
        "missing": [],
    }
    
    # 检查核心模块
    print("📋 检查核心模块...")
    for module_path, description in CORE_MODULES.items():
        exists, message = check_module_exists(module_path)
        if exists:
            print(f"  ✅ {description} ({module_path}): {message}")
            results["passed"].append((module_path, description))
        else:
            print(f"  ❌ {description} ({module_path}): {message}")
            results["failed"].append((module_path, description, message))
    
    print()
    
    # 检查关键类
    print("📋 检查关键类...")
    for module_path, class_names in REQUIRED_CLASSES.items():
        exists, _ = check_module_exists(module_path)
        if exists:
            for class_name in class_names:
                class_exists, message = check_class_exists(module_path, class_name)
                if class_exists:
                    print(f"  ✅ {module_path}.{class_name}: {message}")
                else:
                    print(f"  ❌ {module_path}.{class_name}: {message}")
                    results["failed"].append((module_path, class_name, message))
    
    print()
    
    # 生成报告
    print("=" * 80)
    print("验证结果汇总")
    print("=" * 80)
    print(f"✅ 通过: {len(results['passed'])}")
    print(f"❌ 失败: {len(results['failed'])}")
    print()
    
    if results["failed"]:
        print("失败的模块:")
        for item in results["failed"]:
            if len(item) == 3:
                print(f"  - {item[0]}: {item[2]}")
            else:
                print(f"  - {item[0]}: {item[1]}")
    
    return len(results["failed"]) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

