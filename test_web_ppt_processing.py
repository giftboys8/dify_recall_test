#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试web界面的PPT处理流程
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append('/opt/work/kb')
from src.translation.ppt_parser import PPTParser

def test_web_ppt_processing():
    """测试web界面的PPT处理流程"""
    print("=== 测试Web界面PPT处理流程 ===")
    
    # 查找刚创建的测试PPT文件
    docs_dir = Path('/opt/work/kb/uploads/documents')
    ppt_files = list(docs_dir.glob('*测试.pptx'))
    
    if not ppt_files:
        print("✗ 未找到测试PPT文件")
        return
    
    test_ppt = ppt_files[0]
    print(f"找到测试PPT文件: {test_ppt}")
    
    try:
        # 模拟web界面的处理逻辑
        ppt_parser = PPTParser()
        print(f"PPT解析器初始化: {'成功' if ppt_parser.is_available() else '失败'}")
        
        if ppt_parser.is_available():
            # 模拟web界面的PDF转换流程
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_filename = f"{timestamp}_{test_ppt.stem.replace('_测试', '')}.pdf"
            pdf_file_path = docs_dir / pdf_filename
            
            print(f"开始转换: {test_ppt} -> {pdf_file_path}")
            
            # 执行转换
            converted_path = ppt_parser.convert_ppt_to_pdf(str(test_ppt), str(pdf_file_path))
            
            if converted_path and converted_path.endswith('.pdf'):
                print(f"✓ 转换成功: {converted_path}")
                
                # 检查文件大小
                file_size = os.path.getsize(converted_path)
                print(f"PDF文件大小: {file_size} 字节")
                
                # 模拟web界面的文件替换逻辑
                print(f"删除原始PPT文件: {test_ppt}")
                test_ppt.unlink()  # 删除原始PPT文件
                
                print(f"✓ 最终文件: {pdf_file_path}")
                print(f"文件类型: .pdf")
                
                # 验证PDF内容
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(converted_path)
                    total_text = ""
                    for page in reader.pages:
                        total_text += page.extract_text()
                    
                    print(f"PDF页数: {len(reader.pages)}")
                    print(f"提取的文本长度: {len(total_text)} 字符")
                    
                    # 检查中文字符
                    chinese_chars = sum(1 for char in total_text if '\u4e00' <= char <= '\u9fff')
                    print(f"中文字符数量: {chinese_chars}")
                    
                    if chinese_chars > 0:
                        print("✓ 中文字符处理正常")
                        
                        # 显示部分内容
                        content_preview = total_text[:500].replace('\n', ' ').strip()
                        print(f"\n内容预览:\n{content_preview}...")
                    else:
                        print("⚠ 未检测到中文字符")
                        
                except ImportError:
                    print("PyPDF2未安装，无法验证PDF内容")
                except Exception as e:
                    print(f"PDF内容验证失败: {e}")
                    
            else:
                print(f"✗ 转换失败: {converted_path}")
        else:
            # 模拟fallback到文本转换
            print("PPT解析器不可用，使用文本转换")
            txt_filename = f"{timestamp}_{test_ppt.stem.replace('_测试', '')}.txt"
            txt_file_path = docs_dir / txt_filename
            
            converted_path = ppt_parser.convert_ppt_to_pdf(str(test_ppt), str(txt_file_path))
            
            if converted_path and converted_path.endswith('.txt'):
                print(f"✓ 文本转换成功: {converted_path}")
                
                # 读取文本内容
                with open(converted_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"文本内容长度: {len(content)} 字符")
                print(f"\n内容预览:\n{content[:300]}...")
                
                # 删除原始PPT文件
                test_ppt.unlink()
                print(f"删除原始PPT文件: {test_ppt}")
            else:
                print(f"✗ 文本转换失败: {converted_path}")
                
    except Exception as e:
        print(f"✗ 处理过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_web_ppt_processing()