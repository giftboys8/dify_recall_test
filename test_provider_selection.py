#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试翻译提供商选择问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.translation.processor import ProcessingConfig, BatchProcessor
from src.translation.translator import TranslationEngine

def test_default_provider():
    """测试默认提供商"""
    print("测试1: 检查默认翻译提供商...")
    
    # 创建默认配置
    config = ProcessingConfig()
    print(f"默认提供商: {config.translation_provider}")
    
    # 创建批处理器
    processor = BatchProcessor(config)
    print(f"批处理器使用的提供商: {processor.config.translation_provider}")
    
    return config.translation_provider

def test_deepseek_provider():
    """测试DeepSeek提供商配置"""
    print("\n测试2: 配置DeepSeek提供商...")
    
    # 创建DeepSeek配置
    config = ProcessingConfig(
        translation_provider='deepseek',
        translation_model='deepseek-chat',
        api_key='test-key'  # 测试用密钥
    )
    print(f"DeepSeek配置提供商: {config.translation_provider}")
    print(f"DeepSeek配置模型: {config.translation_model}")
    
    # 创建批处理器
    processor = BatchProcessor(config)
    print(f"批处理器使用的提供商: {processor.config.translation_provider}")
    
    return config.translation_provider

def test_translation_engine_creation():
    """测试翻译引擎创建"""
    print("\n测试3: 测试翻译引擎创建...")
    
    # 测试NLLB引擎
    try:
        from src.translation.translator import TranslationConfig
        nllb_config = TranslationConfig(provider='nllb')
        nllb_engine = TranslationEngine(nllb_config)
        print(f"✓ NLLB引擎创建成功，提供商: {nllb_engine.config.provider}")
    except Exception as e:
        print(f"✗ NLLB引擎创建失败: {e}")
    
    # 测试DeepSeek引擎
    try:
        deepseek_config = TranslationConfig(
            provider='deepseek',
            model='deepseek-chat',
            api_key='test-key'
        )
        deepseek_engine = TranslationEngine(deepseek_config)
        print(f"✓ DeepSeek引擎创建成功，提供商: {deepseek_engine.config.provider}")
    except Exception as e:
        print(f"✗ DeepSeek引擎创建失败: {e}")

def main():
    print("翻译提供商选择问题诊断")
    print("=" * 50)
    
    # 运行测试
    default_provider = test_default_provider()
    deepseek_provider = test_deepseek_provider()
    test_translation_engine_creation()
    
    print("\n" + "=" * 50)
    print("诊断结果:")
    print(f"1. 默认提供商是: {default_provider}")
    print(f"2. 这解释了为什么系统尝试加载NLLB模型")
    print("3. 用户需要在Web界面中明确选择'DeepSeek Chat'选项")
    print("4. 或者修改代码中的默认提供商设置")
    
    print("\n解决方案:")
    print("方案1: 在Web界面的'Translation Provider'下拉菜单中选择'DeepSeek Chat'")
    print("方案2: 修改ProcessingConfig的默认值为'deepseek'")
    print("方案3: 在API调用时明确传递provider='deepseek'参数")

if __name__ == '__main__':
    main()