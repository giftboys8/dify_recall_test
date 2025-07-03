#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试仅使用DeepSeek翻译器的流程
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量解决OpenMP冲突
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.translation.translator import TranslationEngine, TranslationConfig

def test_deepseek_dependencies():
    """测试DeepSeek依赖包"""
    print("测试1: 检查DeepSeek依赖包...")
    
    try:
        import openai
        print(f"✓ openai版本: {openai.__version__}")
        return True
        
    except ImportError as e:
        print(f"✗ openai库导入失败: {e}")
        return False

def test_deepseek_translator_creation():
    """测试DeepSeek翻译器创建"""
    print("\n测试2: 创建DeepSeek翻译器...")
    
    try:
        # 注意：这里需要实际的API密钥才能完全测试
        config = TranslationConfig(
            provider='deepseek',
            source_language='en',
            target_language='zh-CN',
            model='deepseek-chat',
            api_key='test-key'  # 测试用的假密钥
        )
        
        engine = TranslationEngine(config)
        translator = engine._get_translator()
        
        print(f"✓ 翻译器创建成功: {type(translator).__name__}")
        print(f"✓ 翻译器类型: DeepSeek")
        
        return True
        
    except Exception as e:
        print(f"✗ 翻译器创建失败: {e}")
        return False

def test_supported_providers():
    """测试支持的翻译提供商"""
    print("\n测试3: 检查支持的翻译提供商...")
    
    try:
        providers = TranslationEngine.get_supported_providers()
        print(f"✓ 支持的提供商: {providers}")
        
        if 'deepseek' in providers:
            print("✓ DeepSeek提供商可用")
        else:
            print("✗ DeepSeek提供商不可用")
            return False
            
        # 检查是否包含NLLB（应该包含，即使依赖未安装）
        if 'nllb' in providers:
            print("✓ NLLB提供商在列表中（依赖可能未安装）")
        
        return True
        
    except Exception as e:
        print(f"✗ 获取支持的提供商失败: {e}")
        return False

def test_translation_engine_basic():
    """测试翻译引擎基本功能"""
    print("\n测试4: 测试翻译引擎基本功能...")
    
    try:
        config = TranslationConfig(
            provider='deepseek',
            source_language='en',
            target_language='zh-CN',
            model='deepseek-chat',
            api_key='test-key'
        )
        
        engine = TranslationEngine(config)
        
        # 测试配置访问
        print(f"✓ 引擎配置: {engine.config.provider}")
        print(f"✓ 源语言: {engine.config.source_language}")
        print(f"✓ 目标语言: {engine.config.target_language}")
        
        return True
        
    except Exception as e:
        print(f"✗ 翻译引擎基本功能测试失败: {e}")
        return False

def test_config_creation():
    """测试配置创建"""
    print("\n测试5: 测试配置创建...")
    
    try:
        # 测试DeepSeek配置
        config = TranslationEngine.create_config(
            'deepseek',
            source_language='en',
            target_language='zh-CN',
            api_key='test-key'
        )
        
        print(f"✓ DeepSeek配置创建成功")
        print(f"  - 提供商: {config.provider}")
        print(f"  - 源语言: {config.source_language}")
        print(f"  - 目标语言: {config.target_language}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置创建失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("DeepSeek翻译器流程测试（无NLLB依赖）")
    print("=" * 60)
    
    tests = [
        test_deepseek_dependencies,
        test_deepseek_translator_creation,
        test_supported_providers,
        test_translation_engine_basic,
        test_config_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！DeepSeek翻译器流程可以正常运行。")
        print("\n建议:")
        print("1. 配置有效的DeepSeek API密钥")
        print("2. 可以开始使用DeepSeek进行翻译")
        print("3. 如需NLLB功能，后续可安装: pip install transformers torch sentencepiece sacremoses")
        return True
    else:
        print("✗ 部分测试失败，需要进一步检查。")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)