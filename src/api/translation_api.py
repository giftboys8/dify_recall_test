"""PDF翻译功能的Web API接口

提供PDF翻译的HTTP服务接口。
"""

import os
import json
import tempfile
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from ..translation.processor import BatchProcessor, ProcessingConfig
from ..translation.translator import TranslationEngine
from ..translation.formatter import DocumentFormatter
from ..utils.logger import get_logger

logger = get_logger(__name__)

# 创建蓝图
translation_bp = Blueprint('translation', __name__, url_prefix='/api/translation')

# 支持的文件类型
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def allowed_file(filename: str) -> bool:
    """检查文件类型是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file(file: FileStorage) -> tuple[bool, str]:
    """验证上传的文件"""
    if not file:
        return False, "未选择文件"
    
    if file.filename == '':
        return False, "文件名为空"
    
    if not allowed_file(file.filename):
        return False, f"不支持的文件类型，仅支持: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # 检查文件大小（如果可能）
    if hasattr(file, 'content_length') and file.content_length:
        if file.content_length > MAX_FILE_SIZE:
            return False, f"文件大小超过限制 ({MAX_FILE_SIZE // (1024*1024)}MB)"
    
    return True, ""


@translation_bp.route('/providers', methods=['GET'])
def get_translation_providers():
    """获取支持的翻译提供商"""
    try:
        providers = TranslationEngine.get_supported_providers()
        output_formats = DocumentFormatter.get_supported_formats()
        
        return jsonify({
            'success': True,
            'data': {
                'translation_providers': providers,
                'output_formats': output_formats,
                'supported_languages': {
                    'source': ['auto', 'en', 'zh-CN', 'ja', 'ko', 'fr', 'de', 'es'],
                    'target': ['zh-CN', 'en', 'ja', 'ko', 'fr', 'de', 'es']
                },
                'layout_options': ['side_by_side', 'paragraph_by_paragraph']
            }
        })
    
    except Exception as e:
        logger.error(f"获取翻译提供商失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@translation_bp.route('/translate', methods=['POST'])
def translate_pdf():
    """翻译PDF文件"""
    try:
        # 检查文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '未找到上传文件'
            }), 400
        
        file = request.files['file']
        is_valid, error_msg = validate_file(file)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # 获取翻译参数
        form_data = request.form.to_dict()
        
        # 解析配置参数
        config_params = {
            'translation_provider': form_data.get('provider', 'nllb'),
            'source_language': form_data.get('source_language', 'auto'),
            'target_language': form_data.get('target_language', 'zh-CN'),
            'translation_model': form_data.get('model'),
            'api_key': form_data.get('api_key'),
            'output_format': form_data.get('output_format', 'docx'),
            'layout': form_data.get('layout', 'side_by_side'),
            'replace_original': form_data.get('replace_original', 'false').lower() == 'true',
            'batch_size': int(form_data.get('batch_size', 10)),
            'delay_between_requests': float(form_data.get('delay', 1.0)),
            'use_smart_chunking': form_data.get('use_smart_chunking', 'true').lower() == 'true',
            'max_chunk_chars': int(form_data.get('max_chunk_chars', 1500)),
            'min_chunk_chars': int(form_data.get('min_chunk_chars', 50))
        }
        
        # 创建临时目录用于处理
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 保存上传的文件
            filename = secure_filename(file.filename)
            input_path = os.path.join(temp_dir, filename)
            file.save(input_path)
            
            # 设置输出目录
            config_params['output_directory'] = temp_dir
            config_params['keep_temp_files'] = True
            
            # 创建处理器配置
            config = ProcessingConfig(**config_params)
            
            # 创建批处理器
            processor = BatchProcessor(config)
            
            # 执行翻译
            logger.info(f"开始翻译PDF: {filename}")
            result = processor.process_pdf(input_path)
            
            if result.success:
                # 准备返回数据
                response_data = {
                    'success': True,
                    'data': {
                        'input_file': filename,
                        'processing_time': result.processing_time,
                        'original_text_count': result.original_text_count,
                        'translated_text_count': result.translated_text_count,
                        'provider': result.provider,
                        'timestamp': result.timestamp,
                        'output_files': []
                    }
                }
                
                # 创建持久化下载目录
                download_dir = os.path.join(tempfile.gettempdir(), 'translation_downloads')
                os.makedirs(download_dir, exist_ok=True)
                
                # 处理输出文件
                for output_file in result.output_files:
                    if os.path.exists(output_file):
                        # 复制文件到持久化目录
                        import shutil
                        output_filename = os.path.basename(output_file)
                        persistent_path = os.path.join(download_dir, output_filename)
                        shutil.copy2(output_file, persistent_path)
                        
                        # 存储文件路径到全局字典
                        file_storage[output_filename] = persistent_path
                        
                        file_info = {
                            'filename': output_filename,
                            'size': os.path.getsize(persistent_path),
                            'download_url': f"/api/translation/download/{output_filename}"
                        }
                        response_data['data']['output_files'].append(file_info)
                
                logger.info(f"PDF翻译成功: {filename}")
                return jsonify(response_data)
            
            else:
                logger.error(f"PDF翻译失败: {result.error}")
                return jsonify({
                    'success': False,
                    'error': result.error,
                    'processing_time': result.processing_time
                }), 500
        
        finally:
            # 清理临时处理目录
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"清理临时目录失败: {e}")
    
    except Exception as e:
        logger.error(f"翻译API异常: {e}")
        return jsonify({
            'success': False,
            'error': f"服务器内部错误: {str(e)}"
        }), 500


@translation_bp.route('/translate/batch', methods=['POST'])
def translate_multiple_pdfs():
    """批量翻译多个PDF文件"""
    try:
        # 检查文件
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': '未找到上传文件'
            }), 400
        
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({
                'success': False,
                'error': '未选择任何文件'
            }), 400
        
        # 验证所有文件
        for file in files:
            is_valid, error_msg = validate_file(file)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': f"文件 {file.filename}: {error_msg}"
                }), 400
        
        # 获取翻译参数
        form_data = request.form.to_dict()
        
        # 解析配置参数
        config_params = {
            'translation_provider': form_data.get('provider', 'nllb'),
            'source_language': form_data.get('source_language', 'auto'),
            'target_language': form_data.get('target_language', 'zh-CN'),
            'translation_model': form_data.get('model'),
            'api_key': form_data.get('api_key'),
            'output_format': form_data.get('output_format', 'docx'),
            'layout': form_data.get('layout', 'side_by_side'),
            'replace_original': form_data.get('replace_original', 'false').lower() == 'true',
            'batch_size': int(form_data.get('batch_size', 10)),
            'delay_between_requests': float(form_data.get('delay', 1.0)),
            'use_smart_chunking': form_data.get('use_smart_chunking', 'true').lower() == 'true',
            'max_chunk_chars': int(form_data.get('max_chunk_chars', 1500)),
            'min_chunk_chars': int(form_data.get('min_chunk_chars', 50))
        }
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 保存所有上传的文件
            input_paths = []
            for file in files:
                filename = secure_filename(file.filename)
                input_path = os.path.join(temp_dir, filename)
                file.save(input_path)
                input_paths.append(input_path)
            
            # 设置输出目录
            config_params['output_directory'] = temp_dir
            config_params['keep_temp_files'] = True
            
            # 创建处理器配置
            config = ProcessingConfig(**config_params)
            
            # 创建批处理器
            processor = BatchProcessor(config)
            
            # 执行批量翻译
            logger.info(f"开始批量翻译 {len(input_paths)} 个PDF文件")
            results = processor.process_multiple_pdfs(input_paths)
            
            # 统计结果
            successful_count = sum(1 for r in results if r.success)
            failed_count = len(results) - successful_count
            total_time = sum(r.processing_time for r in results)
            
            # 准备返回数据
            response_data = {
                'success': True,
                'data': {
                    'total_files': len(results),
                    'successful_files': successful_count,
                    'failed_files': failed_count,
                    'total_processing_time': total_time,
                    'average_processing_time': total_time / len(results) if results else 0,
                    'results': []
                }
            }
            
            # 添加每个文件的结果
            for result in results:
                file_result = {
                    'filename': os.path.basename(result.input_file),
                    'success': result.success,
                    'processing_time': result.processing_time,
                    'timestamp': result.timestamp
                }
                
                if result.success:
                    # 创建持久化下载目录
                    download_dir = os.path.join(tempfile.gettempdir(), 'translation_downloads')
                    os.makedirs(download_dir, exist_ok=True)
                    
                    output_files_info = []
                    # 处理输出文件
                    for output_file in result.output_files:
                        if os.path.exists(output_file):
                            # 复制文件到持久化目录
                            import shutil
                            output_filename = os.path.basename(output_file)
                            persistent_path = os.path.join(download_dir, output_filename)
                            shutil.copy2(output_file, persistent_path)
                            
                            # 存储文件路径到全局字典
                            file_storage[output_filename] = persistent_path
                            
                            file_info = {
                                'filename': output_filename,
                                'size': os.path.getsize(persistent_path),
                                'download_url': f"/api/translation/download/{output_filename}"
                            }
                            output_files_info.append(file_info)
                    
                    file_result.update({
                        'original_text_count': result.original_text_count,
                        'translated_text_count': result.translated_text_count,
                        'provider': result.provider,
                        'output_files': output_files_info
                    })
                else:
                    file_result['error'] = result.error
                
                response_data['data']['results'].append(file_result)
            
            logger.info(f"批量翻译完成: {successful_count}/{len(results)} 成功")
            return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"批量翻译API异常: {e}")
        return jsonify({
            'success': False,
            'error': f"服务器内部错误: {str(e)}"
        }), 500


# 全局文件存储字典，用于跟踪生成的文件
# 在生产环境中，应该使用Redis或数据库来存储这些信息
file_storage = {}

def cleanup_old_files():
    """清理超过1小时的下载文件"""
    try:
        download_dir = os.path.join(tempfile.gettempdir(), 'translation_downloads')
        if not os.path.exists(download_dir):
            return
        
        import time
        current_time = time.time()
        files_to_remove = []
        
        for filename, file_path in file_storage.items():
            try:
                if os.path.exists(file_path):
                    # 检查文件创建时间，超过1小时的文件将被删除
                    file_age = current_time - os.path.getctime(file_path)
                    if file_age > 3600:  # 1小时 = 3600秒
                        os.remove(file_path)
                        files_to_remove.append(filename)
                        logger.info(f"清理过期文件: {filename}")
                else:
                    files_to_remove.append(filename)
            except Exception as e:
                logger.warning(f"清理文件 {filename} 时出错: {e}")
                files_to_remove.append(filename)
        
        # 从字典中移除已清理的文件
        for filename in files_to_remove:
            file_storage.pop(filename, None)
            
    except Exception as e:
        logger.error(f"文件清理过程出错: {e}")

@translation_bp.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """下载翻译后的文件"""
    try:
        # 定期清理过期文件
        cleanup_old_files()
        
        # 安全文件名检查
        secure_name = secure_filename(filename)
        if not secure_name:
            return jsonify({
                'success': False,
                'error': '无效的文件名'
            }), 400
        
        # 首先检查文件存储字典
        if secure_name in file_storage:
            file_path = file_storage[secure_name]
            if os.path.exists(file_path):
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=secure_name,
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
        
        # 如果字典中没有，搜索临时目录
        import glob
        temp_pattern = os.path.join(tempfile.gettempdir(), '**', secure_name)
        matching_files = glob.glob(temp_pattern, recursive=True)
        
        if matching_files:
            # 使用最新的文件
            file_path = max(matching_files, key=os.path.getctime)
            if os.path.exists(file_path):
                # 更新文件存储字典
                file_storage[secure_name] = file_path
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=secure_name,
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
        
        return jsonify({
            'success': False,
            'error': '文件不存在或已过期'
        }), 404
        
    except Exception as e:
        logger.error(f"文件下载失败: {e}")
        return jsonify({
            'success': False,
            'error': f"下载失败: {str(e)}"
        }), 500


@translation_bp.route('/status', methods=['GET'])
def get_translation_status():
    """获取翻译服务状态"""
    try:
        # 创建一个临时处理器来检查状态
        config = ProcessingConfig()
        processor = BatchProcessor(config)
        status = processor.get_status()
        
        return jsonify({
            'success': True,
            'data': status
        })
    
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@translation_bp.route('/test', methods=['POST'])
def test_translation():
    """测试翻译功能"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': '缺少测试文本'
            }), 400
        
        test_text = data['text']
        provider = data.get('provider', 'nllb')
        source_lang = data.get('source_language', 'auto')
        target_lang = data.get('target_language', 'zh-CN')
        model = data.get('model')
        api_key = data.get('api_key')
        
        # 创建翻译配置
        from ..translation.translator import TranslationConfig
        config = TranslationConfig(
            provider=provider,
            source_language=source_lang,
            target_language=target_lang,
            model=model,
            api_key=api_key
        )
        
        # 创建翻译引擎
        engine = TranslationEngine(config)
        
        # 执行测试翻译
        start_time = datetime.now()
        translated_text = engine.translate_single(test_text)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        return jsonify({
            'success': True,
            'data': {
                'original_text': test_text,
                'translated_text': translated_text,
                'provider': provider,
                'source_language': source_lang,
                'target_language': target_lang,
                'duration': duration,
                'timestamp': end_time.isoformat()
            }
        })
    
    except Exception as e:
        logger.error(f"测试翻译失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@translation_bp.route('/config', methods=['POST'])
def save_translation_config():
    """保存翻译配置"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '缺少配置数据'
            }), 400
        
        # 验证必要的配置字段
        required_fields = ['provider', 'source_language', 'target_language']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必要字段: {field}'
                }), 400
        
        # 保存配置到文件
        config_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'config')
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, 'translation_config.json')
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"翻译配置已保存: {data.get('provider')}")
        
        return jsonify({
            'success': True,
            'message': '配置保存成功'
        })
    
    except Exception as e:
        logger.error(f"保存翻译配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@translation_bp.route('/config', methods=['GET'])
def load_translation_config():
    """加载翻译配置"""
    try:
        config_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'translation_config.json')
        
        if not os.path.exists(config_file):
            # 返回默认配置
            default_config = {
                'provider': 'nllb',
                'source_language': 'auto',
                'target_language': 'zh-CN',
                'output_format': 'docx',
                'layout_option': 'preserve',
                'use_smart_chunking': True,
                'max_chunk_chars': 2000,
                'min_chunk_chars': 500,
                'batch_size': 5,
                'translation_delay': 1000
            }
            return jsonify({
                'success': True,
                'data': default_config
            })
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return jsonify({
            'success': True,
            'data': config_data
        })
    
    except Exception as e:
        logger.error(f"加载翻译配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500





# 错误处理
@translation_bp.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': f'文件大小超过限制 ({MAX_FILE_SIZE // (1024*1024)}MB)'
    }), 413


@translation_bp.errorhandler(400)
def bad_request(e):
    return jsonify({
        'success': False,
        'error': '请求格式错误'
    }), 400


@translation_bp.errorhandler(500)
def internal_error(e):
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500