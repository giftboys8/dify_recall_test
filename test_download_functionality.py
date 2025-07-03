#!/usr/bin/env python3
"""
测试下载功能的脚本
验证翻译后的文档下载是否正常工作
"""

import os
import sys
import requests
import tempfile
import time
from pathlib import Path

# 添加项目路径
sys.path.append('/opt/work/kb')

def test_download_functionality():
    """测试下载功能"""
    print("=== 测试下载功能 ===")
    
    # 1. 检查Web服务器状态
    print("\n1. 检查Web服务器状态...")
    try:
        response = requests.get('http://localhost:8080', timeout=5)
        if response.status_code == 200:
            print("✓ Web服务器运行正常")
        else:
            print(f"✗ Web服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ 无法连接到Web服务器: {e}")
        print("请确保Web服务器正在运行 (python -m src.api.web_server)")
        return False
    
    # 2. 检查临时目录中的文件
    print("\n2. 检查临时目录中的翻译文件...")
    temp_dir = tempfile.gettempdir()
    print(f"临时目录: {temp_dir}")
    
    # 查找最近的翻译文件
    import glob
    pattern = os.path.join(temp_dir, '**/*translated*.docx')
    files = glob.glob(pattern, recursive=True)
    
    if files:
        # 按修改时间排序，获取最新的文件
        latest_file = max(files, key=os.path.getctime)
        print(f"✓ 找到翻译文件: {latest_file}")
        print(f"  文件大小: {os.path.getsize(latest_file)} bytes")
        print(f"  修改时间: {time.ctime(os.path.getctime(latest_file))}")
        
        # 3. 测试下载端点
        print("\n3. 测试下载端点...")
        filename = os.path.basename(latest_file)
        download_url = f'http://localhost:8080/api/translation/download/{filename}'
        
        try:
            response = requests.get(download_url, timeout=10)
            if response.status_code == 200:
                print(f"✓ 下载端点响应正常")
                print(f"  Content-Type: {response.headers.get('Content-Type')}")
                print(f"  Content-Length: {response.headers.get('Content-Length')}")
                
                # 验证文件内容
                if len(response.content) > 0:
                    print(f"✓ 文件内容正常 ({len(response.content)} bytes)")
                else:
                    print("✗ 文件内容为空")
                    
            else:
                print(f"✗ 下载端点响应异常: {response.status_code}")
                print(f"  响应内容: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ 下载请求失败: {e}")
            
    else:
        print("✗ 未找到翻译文件")
        print("请先进行一次PDF翻译以生成测试文件")
        return False
    
    # 4. 检查前端界面
    print("\n4. 检查前端界面...")
    try:
        response = requests.get('http://localhost:8080', timeout=5)
        if 'Translation Results' in response.text:
            print("✓ 前端界面包含翻译结果区域")
        else:
            print("✗ 前端界面缺少翻译结果区域")
            
        if 'downloadLinks' in response.text:
            print("✓ 前端界面包含下载链接区域")
        else:
            print("✗ 前端界面缺少下载链接区域")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ 无法获取前端界面: {e}")
    
    print("\n=== 测试完成 ===")
    return True

def show_usage_instructions():
    """显示使用说明"""
    print("\n=== 使用说明 ===")
    print("1. 启动Web服务器:")
    print("   cd /opt/work/kb")
    print("   python -m src.api.web_server")
    print("")
    print("2. 打开浏览器访问: http://localhost:8080")
    print("")
    print("3. 在PDF Translation标签页中:")
    print("   - 选择翻译提供商 (如 DeepSeek Chat)")
    print("   - 配置源语言和目标语言")
    print("   - 如果使用API提供商，输入API密钥")
    print("   - 上传PDF文件")
    print("   - 点击 'Translate PDF' 按钮")
    print("")
    print("4. 翻译完成后:")
    print("   - 在 'Translation Results' 区域查看翻译信息")
    print("   - 点击下载链接下载翻译后的文档")
    print("   - 在 'Translation History' 中查看历史记录")
    print("")
    print("5. 问题解决:")
    print("   - 如果看不到下载链接，检查浏览器控制台是否有错误")
    print("   - 如果下载失败，检查临时文件是否存在")
    print("   - 确保Web服务器有足够的权限访问临时目录")

if __name__ == '__main__':
    print("PDF翻译下载功能测试")
    print("=" * 50)
    
    success = test_download_functionality()
    
    if success:
        print("\n✓ 下载功能测试通过")
    else:
        print("\n✗ 下载功能测试失败")
    
    show_usage_instructions()