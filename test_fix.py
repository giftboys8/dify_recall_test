#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
sys.path.append('/opt/work/kb')

from src.translation.translator import TranslationEngine, TranslationConfig

def test_deepseek_translator():
    """测试DeepSeek翻译器是否可以正确创建而不触发transformers错误"""
    try:
        print("测试1: 创建DeepSeek翻译配置...")
        config = TranslationConfig(
            provider='deepseek',
            source_language='en',
            target_language='zh-CN',
            api_key='test-key'
        )
        print("✓ 配置创建成功")
        
        print("\n测试2: 创建翻译引擎（延迟初始化）...")
        engine = TranslationEngine(config)
        print("✓ 翻译引擎创建成功")
        
        print("\n测试3: 获取翻译器实例...")
        translator = engine._get_translator()
        print(f"✓ 翻译器创建成功: {type(translator).__name__}")
        
        print("\n测试4: 检查翻译器可用性...")
        is_available = translator.is_available()
        print(f"✓ 翻译器可用性: {is_available}")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_deepseek_reasoner_translator():
    """测试DeepSeek Reasoner翻译器"""
    try:
        print("\n测试5: 创建DeepSeek Reasoner翻译配置...")
        config = TranslationConfig(
            provider='deepseek-reasoner',
            source_language='en',
            target_language='zh-CN',
            api_key='test-key'
        )
        print("✓ 配置创建成功")
        
        print("\n测试6: 创建翻译引擎（延迟初始化）...")
        engine = TranslationEngine(config)
        print("✓ 翻译引擎创建成功")
        
        print("\n测试7: 获取翻译器实例...")
        translator = engine._get_translator()
        print(f"✓ 翻译器创建成功: {type(translator).__name__}")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

if __name__ == '__main__':
    print("开始测试DeepSeek翻译器修复...")
    print("=" * 50)
    
    success1 = test_deepseek_translator()
    success2 = test_deepseek_reasoner_translator()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✓ 所有测试通过！修复成功。")
    else:
        print("✗ 部分测试失败。")