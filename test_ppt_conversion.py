#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.translation.ppt_parser import PPTParser
import tempfile
import os

def test_ppt_conversion():
    parser = PPTParser()
    print('PPT Parser available:', parser.is_available())
    print('Can convert to PDF:', parser.can_convert_to_pdf())
    
    # 检查是否有测试文件
    test_files = [
        '/opt/work/kb/uploads/documents/20250704_090637_（已压缩）DoDAF V2 - Volume 2.pptx',
        '/opt/work/kb/uploads/documents/20250704_091028_DODAF V2 - Volume 3.pptx'
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f'Found test file: {test_file}')
            try:
                result = parser.convert_ppt_to_pdf(test_file)
                print(f'Conversion result: {result}')
                print(f'Output file exists: {os.path.exists(result)}')
                if os.path.exists(result):
                    print(f'Output file size: {os.path.getsize(result)} bytes')
                break
            except Exception as e:
                print(f'Conversion failed: {e}')
        else:
            print(f'Test file not found: {test_file}')
    
    print('Test completed.')

if __name__ == '__main__':
    test_ppt_conversion()