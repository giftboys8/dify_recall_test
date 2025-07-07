"""PDF翻译功能的Web API接口

提供PDF翻译的HTTP服务接口。
"""

import os
import json
import tempfile
import asyncio
import threading
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from queue import Queue

from flask import Blueprint, request, jsonify, send_file, current_app, Response, stream_template
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from ..translation.processor import BatchProcessor, ProcessingConfig
from ..translation.translator import TranslationEngine
from ..translation.formatter import DocumentFormatter
from ..utils.logger import get_logger

# 创建蓝图
translation_bp = Blueprint('translation', __name__, url_prefix='/api/translation')
logger = get_logger(__name__)

# 文件存储字典（用于下载）
file_storage = {}

# 进度跟踪字典
progress_storage = {}

# 配置常量
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename: str) -> bool:
    """检查文件类型是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file(file: FileStorage) -> tuple[bool, str]:
    """验证上传的文件"""
    if not file or file.filename == '':
        return False, '未选择文件'
    
    if not allowed_file(file.filename):
        return False, '不支持的文件类型，仅支持PDF文件'
    
    # 检查文件大小（通过读取内容长度）
    file.seek(0, 2)  # 移动到文件末尾
    file_size = file.tell()
    file.seek(0)  # 重置到文件开头
    
    if file_size > MAX_FILE_SIZE:
        return False, f'文件大小超过限制 ({MAX_FILE_SIZE // (1024*1024)}MB)'
    
    return True, ''

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
                    'target': ['zh-CN', 'en', 'zh-TW', 'ja', 'ko', 'fr', 'de', 'es', 'ru', 'ar']
                }
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


@translation_bp.route('/translate/stream', methods=['POST'])
def translate_pdf_stream():
    """流式翻译PDF文件，提供实时进度更新"""
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
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
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
        
        # 初始化进度跟踪
        progress_storage[task_id] = {
            'status': 'starting',
            'progress': 0,
            'current_step': '准备开始翻译...',
            'total_texts': 0,
            'completed_texts': 0,
            'error': None,
            'result': None
        }
        
        # 创建临时目录用于处理
        temp_dir = tempfile.mkdtemp()
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        input_path = os.path.join(temp_dir, filename)
        file.save(input_path)
        
        # 设置输出目录
        config_params['output_directory'] = temp_dir
        config_params['keep_temp_files'] = True
        
        # 在后台线程中执行翻译
        def translate_in_background():
            try:
                # 创建处理器配置
                config = ProcessingConfig(**config_params)
                
                # 创建带进度回调的批处理器
                processor = BatchProcessorWithProgress(config, task_id)
                
                # 执行翻译
                logger.info(f"开始流式翻译PDF: {filename}")
                result = processor.process_pdf(input_path)
                
                if result.success:
                    # 创建持久化下载目录
                    download_dir = os.path.join(tempfile.gettempdir(), 'translation_downloads')
                    os.makedirs(download_dir, exist_ok=True)
                    
                    output_files = []
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
                            output_files.append(file_info)
                    
                    # 更新进度为完成
                    progress_storage[task_id].update({
                        'status': 'completed',
                        'progress': 100,
                        'current_step': '翻译完成',
                        'result': {
                            'input_file': filename,
                            'processing_time': result.processing_time,
                            'original_text_count': result.original_text_count,
                            'translated_text_count': result.translated_text_count,
                            'provider': result.provider,
                            'timestamp': result.timestamp,
                            'output_files': output_files
                        }
                    })
                    
                    logger.info(f"PDF流式翻译成功: {filename}")
                
                else:
                    # 更新进度为失败
                    progress_storage[task_id].update({
                        'status': 'failed',
                        'current_step': '翻译失败',
                        'error': result.error
                    })
                    logger.error(f"PDF流式翻译失败: {result.error}")
            
            except Exception as e:
                # 更新进度为错误
                progress_storage[task_id].update({
                    'status': 'error',
                    'current_step': '发生错误',
                    'error': str(e)
                })
                logger.error(f"流式翻译异常: {e}")
            
            finally:
                # 清理临时处理目录
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"清理临时目录失败: {e}")
        
        # 启动后台翻译线程
        thread = threading.Thread(target=translate_in_background)
        thread.daemon = True
        thread.start()
        
        # 返回任务ID
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '翻译任务已启动，请使用task_id查询进度'
        })
    
    except Exception as e:
        logger.error(f"流式翻译API异常: {e}")
        return jsonify({
            'success': False,
            'error': f"服务器内部错误: {str(e)}"
        }), 500


@translation_bp.route('/progress/<task_id>', methods=['GET'])
def get_translation_progress(task_id):
    """获取翻译进度"""
    try:
        if task_id not in progress_storage:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404
        
        progress_data = progress_storage[task_id]
        
        return jsonify({
            'success': True,
            'data': progress_data
        })
    
    except Exception as e:
        logger.error(f"获取翻译进度失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@translation_bp.route('/progress/stream/<task_id>')
def stream_translation_progress(task_id):
    """流式获取翻译进度 (Server-Sent Events)"""
    def generate():
        try:
            while True:
                if task_id not in progress_storage:
                    yield f"data: {json.dumps({'error': '任务不存在'})}\n\n"
                    break
                
                progress_data = progress_storage[task_id]
                yield f"data: {json.dumps(progress_data)}\n\n"
                
                # 如果任务完成或失败，结束流
                if progress_data['status'] in ['completed', 'failed', 'error']:
                    break
                
                # 等待1秒后再次检查
                import time
                time.sleep(1)
        
        except Exception as e:
            logger.error(f"流式进度异常: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/plain')


class BatchProcessorWithProgress(BatchProcessor):
    """带进度回调的批处理器"""
    
    def __init__(self, config: ProcessingConfig, task_id: str):
        super().__init__(config)
        self.task_id = task_id
    
    def _update_progress(self, progress: int, step: str, completed: int = 0, total: int = 0):
        """更新进度"""
        if self.task_id in progress_storage:
            progress_storage[self.task_id].update({
                'progress': progress,
                'current_step': step,
                'completed_texts': completed,
                'total_texts': total
            })
    
    def process_pdf(self, pdf_path: str, output_name: Optional[str] = None):
        """处理单个PDF文件，带进度更新"""
        import time
        start_time = time.time()
        temp_files = []
        output_files = []
        
        try:
            self._update_progress(5, "开始处理PDF文档...")
            self.logger.info(f"开始处理PDF: {pdf_path}")
            
            # 验证输入文件
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
            
            # 准备输出目录和文件名
            output_dir = self.config.output_directory or os.path.dirname(pdf_path)
            if output_name is None:
                output_name = Path(pdf_path).stem + "_translated"
            
            os.makedirs(output_dir, exist_ok=True)
            
            # 步骤1: 解析PDF
            self._update_progress(10, "正在解析PDF文档...")
            self.logger.info("步骤1: 解析PDF文档")
            parse_result = self.pdf_parser.parse_pdf(pdf_path)
            
            if not parse_result['success']:
                raise RuntimeError(f"PDF解析失败: {parse_result.get('error')}")
            
            # 添加临时文件到清理列表
            if 'temp_docx_path' in parse_result:
                temp_files.append(parse_result['temp_docx_path'])
            
            # 从文档数据中提取文本（使用智能分块）
            self._update_progress(20, "正在提取文本内容...")
            document_data = parse_result['document_data']
            extracted_texts = self.pdf_parser.get_text_for_translation(
                document_data, 
                use_smart_chunking=self.config.use_smart_chunking,
                max_chars=self.config.max_chunk_chars,
                min_chars=self.config.min_chunk_chars
            )
            
            if not extracted_texts:
                raise RuntimeError("PDF中未提取到任何文本")
            
            total_texts = len(extracted_texts)
            self._update_progress(30, f"提取了 {total_texts} 个文本块，开始翻译...", 0, total_texts)
            
            if self.config.use_smart_chunking:
                self.logger.info(f"智能分块后提取了 {total_texts} 个文本块")
            else:
                self.logger.info(f"提取了 {total_texts} 个文本段落")
            
            # 步骤2: 翻译文本（带进度回调）
            self.logger.info("步骤2: 翻译文本内容")
            translation_result = self._translate_texts_with_progress(extracted_texts)
            
            if not translation_result['success']:
                raise RuntimeError(f"翻译失败: {translation_result.get('error')}")
            
            translated_texts = translation_result['translated_texts']
            self.logger.info(f"翻译了 {len(translated_texts)} 个文本段落")
            
            # 步骤3: 生成输出文档
            self._update_progress(90, "正在生成输出文档...")
            self.logger.info("步骤3: 生成输出文档")
            output_files = self._generate_output_documents(
                extracted_texts, 
                translated_texts, 
                output_dir, 
                output_name
            )
            
            # 步骤4: 生成处理报告
            self._update_progress(95, "正在生成处理报告...")
            self._generate_processing_report(
                translation_result, 
                extracted_texts, 
                translated_texts,
                output_dir, 
                output_name
            )
            
            processing_time = time.time() - start_time
            
            from ..translation.processor import ProcessingResult
            result = ProcessingResult(
                success=True,
                input_file=pdf_path,
                output_files=output_files,
                processing_time=processing_time,
                original_text_count=len(extracted_texts),
                translated_text_count=len(translated_texts),
                provider=self.config.translation_provider
            )
            
            self._update_progress(100, "翻译完成！")
            self.logger.info(f"PDF处理完成，耗时: {processing_time:.2f}秒")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"PDF处理失败: {error_msg}")
            
            from ..translation.processor import ProcessingResult
            return ProcessingResult(
                success=False,
                input_file=pdf_path,
                output_files=output_files,
                processing_time=processing_time,
                original_text_count=0,
                translated_text_count=0,
                provider=self.config.translation_provider,
                error=error_msg
            )
        
        finally:
            # 清理临时文件
            if not self.config.keep_temp_files:
                self._cleanup_temp_files(temp_files)
    
    def _translate_texts_with_progress(self, texts: List[str]) -> Dict[str, Any]:
        """翻译文本并更新进度"""
        try:
            translated_texts = []
            total_texts = len(texts)
            
            # 使用批处理翻译
            batch_size = self.config.batch_size
            
            for i in range(0, total_texts, batch_size):
                batch = texts[i:i + batch_size]
                
                # 更新进度
                progress = 30 + int((i / total_texts) * 60)  # 30-90% 用于翻译
                self._update_progress(
                    progress, 
                    f"正在翻译第 {i+1}-{min(i+len(batch), total_texts)} 个文本块...",
                    i,
                    total_texts
                )
                
                # 翻译当前批次
                batch_results = self.translation_engine.translator.translate_batch(batch)
                translated_texts.extend(batch_results)
                
                # 记录进度
                completed = min(i + len(batch), total_texts)
                self.logger.info(f"翻译进度: {completed}/{total_texts}")
            
            return {
                'success': True,
                'translated_texts': translated_texts
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


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
            
            # 处理结果
            response_data = {
                'success': True,
                'data': {
                    'total_files': len(results),
                    'successful_files': sum(1 for r in results if r.success),
                    'failed_files': sum(1 for r in results if not r.success),
                    'results': []
                }
            }
            
            # 创建持久化下载目录
            download_dir = os.path.join(tempfile.gettempdir(), 'translation_downloads')
            os.makedirs(download_dir, exist_ok=True)
            
            for result in results:
                result_data = {
                    'input_file': os.path.basename(result.input_file),
                    'success': result.success,
                    'processing_time': result.processing_time,
                    'provider': result.provider,
                    'output_files': []
                }
                
                if result.success:
                    result_data.update({
                        'original_text_count': result.original_text_count,
                        'translated_text_count': result.translated_text_count,
                        'timestamp': result.timestamp
                    })
                    
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
                            result_data['output_files'].append(file_info)
                else:
                    result_data['error'] = result.error
                
                response_data['data']['results'].append(result_data)
            
            logger.info(f"批量翻译完成: {response_data['data']['successful_files']}/{response_data['data']['total_files']} 成功")
            return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"批量翻译API异常: {e}")
        return jsonify({
            'success': False,
            'error': f"服务器内部错误: {str(e)}"
        }), 500


def cleanup_old_files():
    """清理过期的下载文件"""
    try:
        download_dir = os.path.join(tempfile.gettempdir(), 'translation_downloads')
        if not os.path.exists(download_dir):
            return
        
        import time
        current_time = time.time()
        
        for filename in os.listdir(download_dir):
            file_path = os.path.join(download_dir, filename)
            if os.path.isfile(file_path):
                # 删除超过1小时的文件
                if current_time - os.path.getmtime(file_path) > 3600:
                    try:
                        os.remove(file_path)
                        # 从存储字典中移除
                        if filename in file_storage:
                            del file_storage[filename]
                        logger.info(f"清理过期文件: {filename}")
                    except Exception as e:
                        logger.warning(f"清理文件失败 {filename}: {e}")
    
    except Exception as e:
        logger.warning(f"清理过期文件异常: {e}")


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
        
        # 检查文件是否存在于存储字典中
        if secure_name not in file_storage:
            return jsonify({
                'success': False,
                'error': '文件不存在或已过期'
            }), 404
        
        file_path = file_storage[secure_name]
        
        # 检查文件是否实际存在
        if not os.path.exists(file_path):
            # 从存储字典中移除不存在的文件
            del file_storage[secure_name]
            return jsonify({
                'success': False,
                'error': '文件不存在'
            }), 404
        
        # 发送文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=secure_name
        )
    
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
        config_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'translation_config.json')
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info("翻译配置已保存")
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
                'min_chunk_chars': 100,
                'batch_size': 10,
                'delay': 1.0
            }
            return jsonify({
                'success': True,
                'data': default_config
            })
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return jsonify({
            'success': True,
            'data': config
        })
    
    except Exception as e:
        logger.error(f"加载翻译配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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