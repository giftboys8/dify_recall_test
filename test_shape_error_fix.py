#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的PPT解析器对未知形状类型的处理
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, '/opt/work/kb')

from src.translation.ppt_parser import PPTParser
from src.utils.logger import get_logger

def test_shape_error_fix():
    """测试形状错误修复"""
    logger = get_logger(__name__)
    print("=== 测试PPT形状错误修复 ===")
    
    # 查找上传目录中的PPT文件
    uploads_dir = Path('/opt/work/kb/uploads/documents')
    ppt_files = list(uploads_dir.glob('*.pptx')) + list(uploads_dir.glob('*.ppt'))
    
    if not ppt_files:
        print("✗ 未找到PPT文件进行测试")
        return
    
    # 选择最新的PPT文件
    ppt_file = max(ppt_files, key=lambda x: x.stat().st_mtime)
    print(f"测试文件: {ppt_file}")
    
    # 创建PPT解析器
    parser = PPTParser()
    
    if not parser.is_available():
        print("✗ PPT解析器不可用")
        return
    
    try:
        print("\n--- 开始转换测试 ---")
        
        # 生成输出文件路径
        output_path = str(uploads_dir / f"test_fixed_{ppt_file.stem}.pdf")
        
        # 执行转换
        result_path = parser.convert_ppt_to_pdf(str(ppt_file), output_path)
        
        print(f"✓ 转换成功: {result_path}")
        
        # 检查输出文件
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"✓ 输出文件存在，大小: {file_size} 字节")
            
            if file_size > 1000:  # 大于1KB
                print("✓ 文件大小正常")
            else:
                print("⚠ 文件可能过小")
        else:
            print("✗ 输出文件不存在")
            
        # 测试提取幻灯片信息
        print("\n--- 测试幻灯片信息提取 ---")
        slide_info = parser.extract_slide_info(str(ppt_file))
        
        if 'error' in slide_info:
            print(f"⚠ 信息提取出现问题: {slide_info['error']}")
        else:
            print(f"✓ 幻灯片数量: {slide_info.get('slide_count', 0)}")
            print(f"✓ 成功提取信息")
            
            # 显示每张幻灯片的文本内容数量
            for slide in slide_info.get('slides', []):
                text_count = len(slide.get('text_content', []))
                shape_count = slide.get('shape_count', 0)
                print(f"  幻灯片 {slide['index']}: {text_count} 个文本块, {shape_count} 个形状")
        
        print("\n✓ 所有测试完成，未出现形状类型错误")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理临时文件
        parser.cleanup()
        print("\n--- 清理完成 ---")

if __name__ == "__main__":
    test_shape_error_fix()