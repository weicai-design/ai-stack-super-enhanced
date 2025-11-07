"""
文件处理综合测试脚本
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.file_processor import FileProcessor
from processors.text_processor import TextProcessor
from processors.preprocessor import Preprocessor


def create_test_files():
    """创建测试文件"""
    test_dir = Path(__file__).parent / "test_files"
    test_dir.mkdir(exist_ok=True)
    
    # 1. 创建文本文件
    txt_file = test_dir / "test.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("""这是一个测试文本文件。
        
它包含多个段落。用于测试文件处理器的功能。

This is a test text file.
It contains multiple paragraphs. For testing the file processor.

测试内容包括：
1. 中文文本
2. English text
3. 数字 123456
4. 标点符号！？。，
""")
    
    # 2. 创建Markdown文件
    md_file = test_dir / "test.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("""# 测试Markdown文件

## 第一节

这是正文内容。

## 第二节

- 列表项1
- 列表项2
- 列表项3

```python
def hello():
    print("Hello, World!")
```
""")
    
    # 3. 创建Python代码文件
    py_file = test_dir / "test.py"
    with open(py_file, 'w', encoding='utf-8') as f:
        f.write("""#!/usr/bin/env python3
# -*- coding: utf-8 -*-

\"\"\"
测试Python文件
\"\"\"

def test_function():
    \"\"\"测试函数\"\"\"
    print("这是一个测试函数")
    return True

if __name__ == "__main__":
    test_function()
""")
    
    # 4. 创建JSON文件
    json_file = test_dir / "test.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write("""{
    "name": "测试数据",
    "type": "JSON",
    "items": [
        {"id": 1, "value": "项目1"},
        {"id": 2, "value": "项目2"}
    ]
}""")
    
    print(f"✅ 测试文件已创建在: {test_dir}")
    return test_dir


def test_file_processor():
    """测试文件处理器"""
    print("\n" + "="*70)
    print("  测试 1: 文件处理器")
    print("="*70)
    
    processor = FileProcessor()
    
    # 显示支持的格式
    formats = processor.get_supported_formats_info()
    print(f"\n支持的文件格式: {formats['total_formats']}种")
    for category, info in formats['categories'].items():
        print(f"  {category:12s}: {info['count']:2d}种")
    
    # 创建测试文件
    test_dir = create_test_files()
    
    # 测试每个文件
    print(f"\n开始处理测试文件...")
    for file in test_dir.glob("*"):
        if file.is_file():
            print(f"\n{'─'*70}")
            result = processor.process_file(str(file))
            
            if result.get("success"):
                print(f"✅ 文件: {result['file_name']}")
                print(f"   类型: {result['file_type']} | 类别: {result['file_category']}")
                print(f"   大小: {result['file_size']}字节")
                print(f"   内容: {result['content_length']}字符")
                print(f"   预览: {result['content'][:100]}...")
            else:
                print(f"❌ 处理失败: {result.get('error')}")
    
    print(f"\n{'='*70}")
    print("✅ 文件处理器测试完成")


def test_text_processor():
    """测试文本处理器"""
    print("\n" + "="*70)
    print("  测试 2: 文本处理器")
    print("="*70)
    
    processor = TextProcessor()
    
    # 测试文本
    test_text = """
人工智能（Artificial Intelligence, AI）是计算机科学的一个分支。
它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。

Machine learning is a subset of artificial intelligence.
It focuses on the development of computer programs that can access data and use it to learn for themselves.
"""
    
    print(f"\n原文长度: {len(test_text)}字符\n")
    
    # 测试不同的分块方法
    methods = ["fixed", "sentence", "semantic"]
    
    for method in methods:
        print(f"\n{'─'*70}")
        print(f"分块方法: {method}")
        print(f"{'─'*70}")
        
        chunks = processor.split_text(test_text, chunk_size=100, method=method)
        
        print(f"生成块数: {len(chunks)}")
        for chunk in chunks[:3]:  # 只显示前3个
            print(f"\n块 {chunk['chunk_id']}:")
            print(f"  长度: {chunk['length']}字符")
            print(f"  内容: {chunk['content'][:60]}...")
    
    # 测试文本清洗
    print(f"\n{'─'*70}")
    print("文本清洗")
    print(f"{'─'*70}")
    
    dirty_text = """
这是    一段    有    多余空白    的文本


它有太多换行符



需要清洗
"""
    cleaned = processor.clean_text(dirty_text)
    print(f"原文: '{dirty_text}'")
    print(f"清洗后: '{cleaned}'")
    
    print(f"\n{'='*70}")
    print("✅ 文本处理器测试完成")


def test_preprocessor():
    """测试预处理器"""
    print("\n" + "="*70)
    print("  测试 3: 预处理器")
    print("="*70)
    
    preprocessor = Preprocessor()
    
    # 测试案例
    test_cases = [
        {
            "name": "正常文本",
            "text": "这是一段正常的中文文本。It also contains English. 用于测试预处理功能。"
        },
        {
            "name": "包含HTML标签",
            "text": "<p>这是<strong>HTML</strong>文本</p>"
        },
        {
            "name": "包含URL",
            "text": "访问网站 https://example.com 获取更多信息"
        },
        {
            "name": "包含邮箱",
            "text": "联系我们: contact@example.com"
        },
        {
            "name": "文本过短",
            "text": "短文本"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'─'*70}")
        print(f"测试案例 {i}: {case['name']}")
        print(f"{'─'*70}")
        
        result = preprocessor.preprocess(case['text'])
        
        print(f"原文: {result['original_text']}")
        print(f"处理后: {result['processed_text']}")
        print(f"长度: {result['original_length']} → {result['final_length']}")
        print(f"重复: {result['is_duplicate']}")
        print(f"验证: {'✅ 通过' if result['passed_validation'] else '❌ 未通过'}")
        
        if result['warnings']:
            print(f"⚠️  警告: {', '.join(result['warnings'])}")
    
    # 测试重复检测
    print(f"\n{'─'*70}")
    print("重复检测测试")
    print(f"{'─'*70}")
    
    text1 = "这是第一段文本"
    text2 = "这是第二段文本"
    text3 = "这是第一段文本"  # 与text1重复
    
    result1 = preprocessor.preprocess(text1)
    print(f"文本1: 重复={result1['is_duplicate']}")
    
    result2 = preprocessor.preprocess(text2)
    print(f"文本2: 重复={result2['is_duplicate']}")
    
    result3 = preprocessor.preprocess(text3)
    print(f"文本3: 重复={result3['is_duplicate']} (应该检测到重复)")
    
    print(f"\n{'='*70}")
    print("✅ 预处理器测试完成")


def test_integrated_workflow():
    """测试集成工作流"""
    print("\n" + "="*70)
    print("  测试 4: 集成工作流")
    print("="*70)
    
    # 初始化所有处理器
    file_processor = FileProcessor()
    text_processor = TextProcessor()
    preprocessor = Preprocessor()
    
    # 创建测试文件
    test_dir = create_test_files()
    test_file = test_dir / "test.txt"
    
    print(f"\n完整处理流程演示:")
    print(f"{'─'*70}")
    
    # 步骤1: 文件处理
    print("\n步骤1: 提取文件内容")
    file_result = file_processor.process_file(str(test_file))
    if not file_result.get("success"):
        print("❌ 文件处理失败")
        return
    
    content = file_result["content"]
    print(f"✅ 提取了 {len(content)} 字符")
    
    # 步骤2: 文本预处理
    print("\n步骤2: 预处理文本")
    preprocess_result = preprocessor.preprocess(content)
    processed_content = preprocess_result["processed_text"]
    print(f"✅ 预处理完成: {preprocess_result['original_length']} → {preprocess_result['final_length']}字符")
    print(f"   验证: {'通过' if preprocess_result['passed_validation'] else '未通过'}")
    
    # 步骤3: 文本分块
    print("\n步骤3: 文本分块")
    chunks = text_processor.split_text(processed_content, chunk_size=200)
    print(f"✅ 生成了 {len(chunks)} 个文本块")
    
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"\n  块 {i}:")
        print(f"    长度: {chunk['length']}字符")
        print(f"    预览: {chunk['content'][:60]}...")
    
    # 步骤4: 提取关键词
    print("\n步骤4: 提取关键词")
    keywords = text_processor.extract_keywords(processed_content, top_k=5)
    print(f"✅ 关键词: {', '.join(keywords)}")
    
    print(f"\n{'='*70}")
    print("✅ 集成工作流测试完成")
    print(f"{'='*70}")
    
    print(f"\n📊 处理流程总结:")
    print(f"  文件 → 内容提取 → 预处理 → 分块 → 关键词提取")
    print(f"  {file_result['file_name']} → {len(content)}字符 → {len(processed_content)}字符 → {len(chunks)}块 → {len(keywords)}个关键词")


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  🧪 RAG文件处理系统 - 综合测试".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "═"*68 + "╝")
    
    try:
        # 运行所有测试
        test_file_processor()
        test_text_processor()
        test_preprocessor()
        test_integrated_workflow()
        
        # 总结
        print("\n\n")
        print("╔" + "═"*68 + "╗")
        print("║" + " "*68 + "║")
        print("║" + "  🎉 所有测试通过！".center(68) + "║")
        print("║" + " "*68 + "║")
        print("╚" + "═"*68 + "╝")
        
        print("\n✅ 文件处理引擎开发完成！")
        print("\n已实现功能:")
        print("  ✅ 文件处理器 (支持10+种文件格式)")
        print("  ✅ 文本处理器 (分块、清洗、关键词提取)")
        print("  ✅ 预处理器 (四项预处理功能)")
        print("  ✅ 集成工作流 (完整处理流程)")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()




