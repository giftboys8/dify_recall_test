#!/usr/bin/env python3
"""
调试翻译API响应格式
检查翻译完成后的实际响应数据
"""

import os
import sys
import requests
import json
from pathlib import Path

# 添加项目路径
sys.path.append('/opt/work/kb')

def create_test_pdf():
    """创建一个简单的测试PDF文件"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        test_pdf_path = '/tmp/test_translation.pdf'
        c = canvas.Canvas(test_pdf_path, pagesize=letter)
        c.drawString(100, 750, "Hello World")
        c.drawString(100, 730, "This is a test document for translation.")
        c.drawString(100, 710, "Testing PDF translation functionality.")
        c.save()
        
        return test_pdf_path
    except ImportError:
        print("reportlab not available, trying to install it...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'reportlab'])
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            test_pdf_path = '/tmp/test_translation.pdf'
            c = canvas.Canvas(test_pdf_path, pagesize=letter)
            c.drawString(100, 750, "Hello World")
            c.drawString(100, 730, "This is a test document for translation.")
            c.drawString(100, 710, "Testing PDF translation functionality.")
            c.save()
            
            return test_pdf_path
        except Exception as e:
            print(f"Failed to install reportlab: {e}")
            print("Please manually create a PDF file for testing")
            return None

def test_translation_api():
    """测试翻译API并检查响应格式"""
    print("=== 调试翻译API响应 ===")
    
    # 1. 检查服务器状态
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
        return False
    
    # 2. 创建测试文件
    print("\n2. 创建测试文件...")
    test_file_path = create_test_pdf()
    if test_file_path and os.path.exists(test_file_path):
        print(f"✓ 测试文件创建成功: {test_file_path}")
    else:
        print("✗ 测试文件创建失败，跳过API测试")
        print("请手动上传PDF文件到网页进行测试")
        return False
    
    # 3. 测试翻译API
    print("\n3. 测试翻译API...")
    try:
        # 准备请求数据
        files = {'file': open(test_file_path, 'rb')}
        data = {
            'provider': 'nllb',  # 使用本地NLLB避免API密钥问题
            'source_language': 'en',
            'target_language': 'zh-CN',
            'output_format': 'docx',
            'layout': 'side_by_side'
        }
        
        print(f"发送请求到: http://localhost:8080/api/translation/translate")
        print(f"请求参数: {data}")
        
        response = requests.post(
            'http://localhost:8080/api/translation/translate',
            files=files,
            data=data,
            timeout=60
        )
        
        files['file'].close()
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ 翻译API响应成功")
            print("\n=== 完整响应数据 ===")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 检查响应结构
            print("\n=== 响应结构分析 ===")
            if 'success' in result:
                print(f"success: {result['success']}")
            
            if 'data' in result:
                data = result['data']
                print("data字段存在:")
                for key, value in data.items():
                    if key == 'output_files' and isinstance(value, list):
                        print(f"  {key}: [{len(value)} files]")
                        for i, file_info in enumerate(value):
                            print(f"    文件 {i+1}: {file_info}")
                    else:
                        print(f"  {key}: {value}")
            
            # 检查下载链接
            if 'data' in result and 'output_files' in result['data']:
                output_files = result['data']['output_files']
                if output_files:
                    print("\n=== 测试下载链接 ===")
                    for file_info in output_files:
                        if 'download_url' in file_info:
                            download_url = f"http://localhost:8080{file_info['download_url']}"
                            print(f"测试下载: {download_url}")
                            
                            try:
                                dl_response = requests.head(download_url, timeout=10)
                                print(f"  状态码: {dl_response.status_code}")
                                if dl_response.status_code == 200:
                                    print(f"  ✓ 下载链接有效")
                                else:
                                    print(f"  ✗ 下载链接无效")
                            except Exception as e:
                                print(f"  ✗ 下载测试失败: {e}")
                
            return True
            
        else:
            print(f"\n✗ 翻译API响应失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"错误文本: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n✗ 翻译API测试失败: {e}")
        return False
    
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            print(f"\n清理测试文件: {test_file_path}")

def check_frontend_javascript():
    """检查前端JavaScript代码"""
    print("\n=== 检查前端JavaScript ===")
    
    js_file = '/opt/work/kb/src/api/static/js/app.js'
    if os.path.exists(js_file):
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查关键函数
        if 'displayTranslationResults' in content:
            print("✓ displayTranslationResults 函数存在")
        else:
            print("✗ displayTranslationResults 函数缺失")
            
        if 'downloadLinks' in content:
            print("✓ downloadLinks 处理代码存在")
        else:
            print("✗ downloadLinks 处理代码缺失")
            
        if 'output_files' in content:
            print("✓ output_files 处理代码存在")
        else:
            print("✗ output_files 处理代码缺失")
    else:
        print(f"✗ JavaScript文件不存在: {js_file}")

if __name__ == '__main__':
    print("翻译API响应调试工具")
    print("=" * 50)
    
    success = test_translation_api()
    check_frontend_javascript()
    
    if success:
        print("\n✓ 调试完成，请检查上述输出")
    else:
        print("\n✗ 调试过程中发现问题")
    
    print("\n=== 前端调试建议 ===")
    print("1. 打开浏览器开发者工具 (F12)")
    print("2. 切换到 Console 标签页")
    print("3. 进行PDF翻译操作")
    print("4. 查看是否有JavaScript错误")
    print("5. 在 Network 标签页查看API请求和响应")
    print("6. 检查 Elements 标签页中 #translationResults 元素是否正确显示")