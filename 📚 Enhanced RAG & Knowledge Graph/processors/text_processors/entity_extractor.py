"""
实体提取器
支持NER实体识别、实体链接、实体消歧等功能
"""
import re
from typing import List, Dict, Set, Optional


class EntityExtractor:
    """实体提取器"""
    
    def __init__(self):
        """初始化实体提取器"""
        # 预定义的实体模式
        self.patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "url": r'https?://[^\s<>"{}|\\^`\[\]]+',
            "phone": r'1[3-9]\d{9}',
            "date": r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?',
            "money": r'[¥$€£]\s?\d+(?:,\d{3})*(?:\.\d{2})?',
            "percentage": r'\d+(?:\.\d+)?%'
        }
    
    def extract(
        self,
        text: str,
        entity_types: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        提取实体
        
        Args:
            text: 输入文本
            entity_types: 要提取的实体类型列表（None表示全部）
            
        Returns:
            提取的实体字典
        """
        entities = {}
        
        # 基于规则的实体提取
        for entity_type, pattern in self.patterns.items():
            if entity_types and entity_type not in entity_types:
                continue
            
            matches = re.finditer(pattern, text)
            entity_list = []
            
            for match in matches:
                entity_list.append({
                    "text": match.group(),
                    "type": entity_type,
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.95
                })
            
            if entity_list:
                entities[entity_type] = entity_list
        
        # 命名实体识别（需要NLP模型）
        ner_entities = self._extract_ner_entities(text)
        entities.update(ner_entities)
        
        return {
            "success": True,
            "text": text,
            "entities": entities,
            "entity_count": sum(len(v) for v in entities.values()),
            "entity_types": list(entities.keys())
        }
    
    def _extract_ner_entities(self, text: str) -> Dict[str, List[Dict]]:
        """
        命名实体识别
        
        使用NLP模型识别人名、地名、机构名等
        
        实际实现需要使用：
        - spaCy
        - transformers (BERT-NER)
        - 或百度、讯飞等NER API
        """
        # 模拟NER结果
        # 简单的规则识别（实际应使用模型）
        
        entities = {}
        
        # 识别中文人名（简单规则）
        person_pattern = r'[王李张刘陈杨黄赵周吴徐孙马朱胡郭何高林罗郑梁宋谢唐韩曹许邓萧冯曾程蔡彭潘袁于董余苏叶吕魏蒋田杜丁沈姜范江傅钟卢汪戴崔任陆廖姚方金邱夏谭韦贾邹石熊孟秦阎薛侯雷白龙段郝孔邵史毛常万顾赖武康贺严尹钱施牛洪龚]\w{1,3}'
        persons = re.findall(person_pattern, text)
        if persons:
            entities["person"] = [
                {"text": p, "type": "person", "confidence": 0.75}
                for p in set(persons)
            ]
        
        # 识别机构名（简单规则）
        org_keywords = ['公司', '集团', '企业', '股份', '有限', '科技', '银行', '大学', '学院', '医院', '政府', '部门']
        org_pattern = r'[\u4e00-\u9fa5]{2,10}(?:' + '|'.join(org_keywords) + ')'
        orgs = re.findall(org_pattern, text)
        if orgs:
            entities["organization"] = [
                {"text": o, "type": "organization", "confidence": 0.80}
                for o in set(orgs)
            ]
        
        # 识别地名（简单规则）
        location_keywords = ['省', '市', '县', '区', '镇', '村', '路', '街', '道']
        loc_pattern = r'[\u4e00-\u9fa5]{2,6}(?:' + '|'.join(location_keywords) + ')'
        locations = re.findall(loc_pattern, text)
        if locations:
            entities["location"] = [
                {"text": l, "type": "location", "confidence": 0.78}
                for l in set(locations)
            ]
        
        return entities
    
    def extract_with_context(
        self,
        text: str,
        entity_types: Optional[List[str]] = None,
        context_window: int = 50
    ) -> List[Dict]:
        """
        提取实体并包含上下文
        
        Args:
            text: 输入文本
            entity_types: 实体类型
            context_window: 上下文窗口大小（字符）
            
        Returns:
            实体及其上下文
        """
        result = self.extract(text, entity_types)
        entities_with_context = []
        
        for entity_type, entity_list in result["entities"].items():
            for entity in entity_list:
                start = max(0, entity["start"] - context_window)
                end = min(len(text), entity["end"] + context_window)
                
                entities_with_context.append({
                    **entity,
                    "context": text[start:end],
                    "context_start": start,
                    "context_end": end
                })
        
        return entities_with_context
    
    def link_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        实体链接
        
        将提取的实体链接到知识库
        
        Args:
            entities: 实体列表
            
        Returns:
            链接后的实体
        """
        # 实际应查询知识图谱或外部知识库
        linked = []
        
        for entity in entities:
            linked_entity = entity.copy()
            
            # 模拟链接到知识库ID
            linked_entity["kb_id"] = f"KB_{entity['type'].upper()}_{hash(entity['text']) % 10000}"
            linked_entity["linked"] = True
            
            linked.append(linked_entity)
        
        return linked
    
    def disambiguate(self, entity_text: str, context: str) -> Dict:
        """
        实体消歧
        
        在多个可能的实体中选择正确的一个
        
        Args:
            entity_text: 实体文本
            context: 上下文
            
        Returns:
            消歧结果
        """
        # 实际应使用上下文和知识库进行消歧
        return {
            "entity": entity_text,
            "context": context,
            "candidates": [
                {"text": entity_text, "type": "person", "score": 0.85},
                {"text": entity_text, "type": "location", "score": 0.15}
            ],
            "selected": {
                "text": entity_text,
                "type": "person",
                "reason": "基于上下文分析"
            }
        }
    
    def get_entity_statistics(self, entities: Dict) -> Dict:
        """获取实体统计信息"""
        stats = {
            "total_entities": sum(len(v) for v in entities.values()),
            "entity_types": len(entities),
            "by_type": {}
        }
        
        for entity_type, entity_list in entities.items():
            stats["by_type"][entity_type] = {
                "count": len(entity_list),
                "unique": len(set(e["text"] for e in entity_list))
            }
        
        return stats


# 使用示例
if __name__ == "__main__":
    extractor = EntityExtractor()
    
    test_text = """
华为技术有限公司于2025年11月9日在深圳市发布了新产品。
联系方式：contact@huawei.com，电话：13800138000。
产品售价为¥5,999，预计销售额达到50亿元。
详情请访问 https://www.huawei.com/cn/
    """
    
    print("✅ 实体提取器已加载\n")
    
    # 提取实体
    result = extractor.extract(test_text)
    
    print(f"📊 提取结果:")
    print(f"  总实体数: {result['entity_count']}")
    print(f"  实体类型: {', '.join(result['entity_types'])}")
    print()
    
    for entity_type, entities in result["entities"].items():
        print(f"  {entity_type}:")
        for e in entities:
            print(f"    - {e['text']}")
    
    print("\n💡 实际部署建议:")
    print("  • 安装 spaCy + 中文模型: python -m spacy download zh_core_web_sm")
    print("  • 或使用 transformers 加载BERT-NER模型")
    print("  • 或对接百度、讯飞等NER API")


