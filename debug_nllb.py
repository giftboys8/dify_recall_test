#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试NLLB翻译错误的脚本
"""

import sys
import os
import json
import traceback
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_nllb_import():
    """测试transformers库导入"""
    print("=== 测试transformers库导入 ===")
    try:
        from transformers import pipeline
        print("✓ transformers库导入成功")
        return True
    except ImportError as e:
        print(f"✗ transformers库导入失败: {e}")
        return False

def test_nllb_model_loading():
    """测试NLLB模型加载"""
    print("\n=== 测试NLLB模型加载 ===")
    try:
        from transformers import pipeline
        print("正在加载NLLB模型...")
        translator = pipeline(
            'translation',
            model='facebook/nllb-200-distilled-600M',
            device=-1  # 使用CPU
        )
        print("✓ NLLB模型加载成功")
        return translator
    except Exception as e:
        print(f"✗ NLLB模型加载失败: {e}")
        traceback.print_exc()
        return None

def test_nllb_translation(translator):
    """测试NLLB翻译功能"""
    print("\n=== 测试NLLB翻译功能 ===")
    if not translator:
        print("✗ 翻译器未初始化")
        return
    
    try:
        test_text = "Hello, how are you?"
        print(f"原文: {test_text}")
        
        result = translator(
            test_text,
            src_lang='eng_Latn',
            tgt_lang='zho_Hans'
        )
        
        translated_text = result[0]['translation_text']
        print(f"译文: {translated_text}")
        print("✓ NLLB翻译测试成功")
        return translated_text
    except Exception as e:
        print(f"✗ NLLB翻译测试失败: {e}")
        traceback.print_exc()
        return None

def test_translation_config():
    """测试翻译配置"""
    print("\n=== 测试翻译配置 ===")
    try:
        from translation.translator import TranslationConfig, TranslationEngine
        
        config = TranslationConfig(
            provider='nllb',
            source_language='en',
            target_language='zh-CN'
        )
        print(f"✓ 翻译配置创建成功: {config}")
        
        engine = TranslationEngine(config)
        print("✓ 翻译引擎创建成功")
        
        test_text = "Hello, world!"
        result = engine.translate_single(test_text)
        print(f"翻译结果: {result}")
        print("✓ 翻译引擎测试成功")
        
    except Exception as e:
        print(f"✗ 翻译配置测试失败: {e}")
        traceback.print_exc()

def test_api_request():
    """测试API请求"""
    print("\n=== 测试API请求 ===")
    try:
        import requests
        
        # 测试数据
        test_data = {
            'text': 'Hello, world!',
            'provider': 'nllb',
            'source_language': 'en',
            'target_language': 'zh-CN'
        }
        
        # 发送请求到本地服务器
        response = requests.post(
            'http://localhost:8080/api/translation/test',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
        if response.headers.get('content-type', '').startswith('text/html'):
            print("⚠️  警告: 服务器返回HTML而不是JSON")
            print("这可能是导致'Unexpected token <'错误的原因")
        
        try:
            json_response = response.json()
            print(f"✓ JSON解析成功: {json_response}")
        except json.JSONDecodeError as e:
            print(f"✗ JSON解析失败: {e}")
            
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"✗ API请求测试失败: {e}")
        traceback.print_exc()

def main():
    """主函数"""
    print("NLLB翻译错误诊断工具")
    print("=" * 50)
    
    # 1. 测试transformers库导入
    if not test_nllb_import():
        print("\n建议: pip install transformers torch")
        return
    
    # 2. 测试NLLB模型加载
    translator = test_nllb_model_loading()
    
    # 3. 测试NLLB翻译功能
    if translator:
        test_nllb_translation(translator)
    
    # 4. 测试翻译配置
    test_translation_config()
    
    # 5. 测试API请求
    test_api_request()
    
    print("\n=== 诊断完成 ===")
    print("如果仍有问题，请检查:")
    print("1. transformers库版本是否兼容")
    print("2. 网络连接是否正常（下载模型需要）")
    print("3. 磁盘空间是否足够（模型文件较大）")
    print("4. 服务器是否正确启动")

if __name__ == '__main__':
    main()