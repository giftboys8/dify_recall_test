#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from flask import Flask, request, jsonify
import sys
sys.path.append('/opt/work/kb')

from src.translation.translator import TranslationEngine, TranslationConfig

app = Flask(__name__)

@app.route('/test_translation', methods=['POST'])
def test_translation():
    try:
        # 创建DeepSeek配置
        config = TranslationConfig(
            provider='deepseek',
            source_language='en',
            target_language='zh-CN',
            api_key='test-key'
        )
        
        # 创建翻译引擎（延迟初始化）
        engine = TranslationEngine(config)
        
        # 测试翻译器是否可以正确创建
        translator = engine._get_translator()
        
        return jsonify({
            'success': True,
            'message': f'翻译器创建成功: {type(translator).__name__}',
            'provider': config.provider
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print('Starting test server on http://127.0.0.1:5000')
    app.run(host='127.0.0.1', port=5000, debug=True)