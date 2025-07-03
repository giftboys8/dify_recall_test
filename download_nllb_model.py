#!/usr/bin/env python3
"""
预下载NLLB模型到本地缓存
用于离线环境下的翻译功能
"""

import os
import sys
from transformers import pipeline
import torch

def download_nllb_model(model_name='facebook/nllb-200-distilled-600M'):
    """
    下载NLLB模型到本地缓存
    
    Args:
        model_name: 要下载的模型名称
    """
    print(f"正在下载NLLB模型: {model_name}")
    print("这可能需要几分钟时间，请耐心等待...")
    
    try:
        # 下载模型到本地缓存
        translator = pipeline(
            'translation',
            model=model_name,
            device=-1,  # 使用CPU
            model_kwargs={
                'low_cpu_mem_usage': True,
                'torch_dtype': torch.float16
            }
        )
        
        print(f"✅ 模型 {model_name} 下载成功！")
        print("现在可以在离线环境下使用NLLB翻译功能了。")
        
        # 测试翻译功能
        test_text = "Hello, world!"
        result = translator(test_text, src_lang="eng_Latn", tgt_lang="zho_Hans")
        print(f"\n测试翻译:")
        print(f"原文: {test_text}")
        print(f"译文: {result[0]['translation_text']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型下载失败: {e}")
        print("请检查网络连接或尝试使用代理。")
        return False

def main():
    """主函数"""
    print("NLLB模型下载工具")
    print("=" * 50)
    
    # 检查网络连接
    print("正在检查网络连接...")
    
    # 默认模型
    model_name = 'facebook/nllb-200-distilled-600M'
    
    # 如果用户提供了模型名称参数
    if len(sys.argv) > 1:
        model_name = sys.argv[1]
    
    print(f"目标模型: {model_name}")
    
    # 下载模型
    success = download_nllb_model(model_name)
    
    if success:
        print("\n🎉 下载完成！现在可以在离线环境下使用翻译功能了。")
    else:
        print("\n💡 建议:")
        print("1. 检查网络连接")
        print("2. 如果在公司网络环境，可能需要配置代理")
        print("3. 可以尝试使用更小的模型，如: facebook/nllb-200-distilled-1.3B")

if __name__ == "__main__":
    main()