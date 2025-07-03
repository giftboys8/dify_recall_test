#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试NLLB翻译器修复
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量解决OpenMP冲突
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.translation.translator import TranslationEngine, TranslationConfig

def test_nllb_dependencies():
    """测试NLLB依赖包"""
    print("测试1: 检查NLLB依赖包...")
    
    try:
        import transformers
        import torch
        import sentencepiece
        import sacremoses
        
        print(f"✓ transformers版本: {transformers.__version__}")
        print(f"✓ torch版本: {torch.__version__}")
        print(f"✓ sentencepiece版本: {sentencepiece.__version__}")
        print(f"✓ sacremoses已安装")
        
        return True
        
    except ImportError as e:
        print(f"✗ 依赖包导入失败: {e}")
        return False

def test_nllb_translator_creation():
    """测试NLLB翻译器创建"""
    print("\n测试2: 创建NLLB翻译器...")
    
    try:
        config = TranslationConfig(
            provider='nllb',
            source_language='en',
            target_language='zh-CN',
            model='facebook/nllb-200-distilled-600M'
        )
        
        engine = TranslationEngine(config)
        translator = engine._get_translator()
        
        print(f"✓ 翻译器创建成功: {type(translator).__name__}")
        print(f"✓ 翻译器可用性: {translator.is_available()}")
        
        return True
        
    except Exception as e:
        print(f"✗ 翻译器创建失败: {e}")
        return False

def test_simple_translation():
    """测试简单翻译"""
    print("\n测试3: 测试简单翻译...")
    
    try:
        config = TranslationConfig(
            provider='nllb',
            source_language='en',
            target_language='zh-CN',
            model='facebook/nllb-200-distilled-600M'
        )
        
        engine = TranslationEngine(config)
        
        # 测试简单文本翻译
        test_texts = ["Hello world!", "This is a test."]
        result = engine.translate_texts(test_texts)
        
        if result['success']:
            print(f"✓ 翻译成功")
            for i, (original, translated) in enumerate(zip(test_texts, result['translated_texts'])):
                print(f"  原文{i+1}: {original}")
                print(f"  译文{i+1}: {translated}")
            return True
        else:
            print(f"✗ 翻译失败: {result.get('error')}")
            return False
        
    except Exception as e:
        print(f"✗ 翻译测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("NLLB翻译器修复测试")
    print("=" * 50)
    
    tests = [
        test_nllb_dependencies,
        test_nllb_translator_creation,
        test_simple_translation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            # 如果前面的测试失败，跳过后续测试
            break
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！NLLB翻译器修复成功。")
        return True
    else:
        print("✗ 部分测试失败，需要进一步检查。")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)