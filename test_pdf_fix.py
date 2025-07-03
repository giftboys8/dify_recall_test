#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试PDF处理修复
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量解决OpenMP冲突
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.translation.processor import BatchProcessor, ProcessingConfig
from src.translation.pdf_parser import PDFParser

def test_pdf_parser():
    """测试PDF解析器的数据结构"""
    print("测试1: 测试PDF解析器数据结构...")
    
    try:
        # 创建一个简单的测试文档
        test_content = """Hello World!

This is a test document for PDF translation.

It contains multiple paragraphs to test the translation functionality.

The system should be able to extract and translate this text properly."""
        
        # 创建临时文本文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_txt = f.name
        
        print(f"✓ 创建测试文件: {temp_txt}")
        
        # 模拟文档数据结构
        mock_doc_data = {
            'paragraphs': [
                {'index': 0, 'text': 'Hello World!', 'style': None},
                {'index': 1, 'text': 'This is a test document for PDF translation.', 'style': None},
                {'index': 2, 'text': 'It contains multiple paragraphs to test the translation functionality.', 'style': None},
                {'index': 3, 'text': 'The system should be able to extract and translate this text properly.', 'style': None}
            ],
            'tables': [],
            'total_paragraphs': 4,
            'total_tables': 0
        }
        
        # 测试get_text_for_translation方法
        parser = PDFParser()
        texts = parser.get_text_for_translation(mock_doc_data)
        
        print(f"✓ 提取文本数量: {len(texts)}")
        for i, text in enumerate(texts):
            print(f"  文本{i+1}: {text[:50]}...")
        
        # 清理临时文件
        os.unlink(temp_txt)
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_processing_config():
    """测试处理配置"""
    print("\n测试2: 测试处理配置...")
    
    try:
        config = ProcessingConfig(
            translation_provider='deepseek',
            source_language='en',
            target_language='zh-CN',
            output_format='docx',
            layout='side_by_side'
        )
        
        print(f"✓ 配置创建成功")
        print(f"  翻译提供商: {config.translation_provider}")
        print(f"  源语言: {config.source_language}")
        print(f"  目标语言: {config.target_language}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置创建失败: {e}")
        return False

def test_batch_processor_init():
    """测试批处理器初始化"""
    print("\n测试3: 测试批处理器初始化...")
    
    try:
        config = ProcessingConfig(
            translation_provider='deepseek',
            source_language='en',
            target_language='zh-CN'
        )
        
        processor = BatchProcessor(config)
        
        print(f"✓ 批处理器创建成功")
        print(f"  PDF解析器: {type(processor.pdf_parser).__name__}")
        print(f"  翻译引擎: {type(processor.translation_engine).__name__}")
        print(f"  文档格式化器: {type(processor.formatter).__name__}")
        
        return True
        
    except Exception as e:
        print(f"✗ 批处理器创建失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("PDF处理修复测试")
    print("=" * 50)
    
    tests = [
        test_pdf_parser,
        test_processing_config,
        test_batch_processor_init
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！PDF处理修复成功。")
        return True
    else:
        print("✗ 部分测试失败，需要进一步检查。")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)