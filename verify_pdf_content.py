#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证生成的PDF文件内容
"""

import os
from pathlib import Path
from PyPDF2 import PdfReader

def verify_pdf_content():
    """验证PDF文件内容"""
    print("=== 验证PDF文件内容 ===")
    
    # 查找最新生成的PDF文件
    docs_dir = Path('/opt/work/kb/uploads/documents')
    pdf_files = list(docs_dir.glob('*盛远生产可视化项目导入规划.pdf'))
    
    if not pdf_files:
        print("✗ 未找到目标PDF文件")
        return
    
    # 选择最新的文件
    pdf_file = max(pdf_files, key=lambda x: x.stat().st_mtime)
    print(f"验证文件: {pdf_file}")
    
    try:
        # 读取PDF内容
        reader = PdfReader(str(pdf_file))
        print(f"PDF页数: {len(reader.pages)}")
        
        total_text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            total_text += page_text
            print(f"\n--- 第{i+1}页内容 ---")
            print(page_text[:300] + "..." if len(page_text) > 300 else page_text)
        
        print(f"\n=== 总体统计 ===")
        print(f"总文本长度: {len(total_text)} 字符")
        
        # 检查中文字符
        chinese_chars = sum(1 for char in total_text if '\u4e00' <= char <= '\u9fff')
        print(f"中文字符数量: {chinese_chars}")
        
        # 检查关键词
        keywords = ['盛远', '生产', '可视化', '项目', '导入', '规划', '技术', '架构', '实施', '计划']
        found_keywords = []
        for keyword in keywords:
            if keyword in total_text:
                found_keywords.append(keyword)
        
        print(f"找到关键词: {found_keywords}")
        print(f"关键词覆盖率: {len(found_keywords)}/{len(keywords)} ({len(found_keywords)/len(keywords)*100:.1f}%)")
        
        if chinese_chars > 0:
            print("\n✓ 中文字符处理正常")
        else:
            print("\n⚠ 未检测到中文字符")
            
        if len(found_keywords) >= len(keywords) * 0.7:  # 70%以上关键词匹配
            print("✓ 内容完整性良好")
        else:
            print("⚠ 内容可能不完整")
            
        # 检查文件大小
        file_size = pdf_file.stat().st_size
        print(f"\n文件大小: {file_size} 字节")
        
        if file_size > 10000:  # 大于10KB
            print("✓ 文件大小正常")
        else:
            print("⚠ 文件可能过小")
            
    except Exception as e:
        print(f"✗ PDF验证失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_pdf_content()