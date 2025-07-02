"""批处理模块

统一管理PDF翻译的完整流程，包括解析、翻译、格式化和输出。
"""

import os
import time
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict

from .pdf_parser import PDFParser
from .translator import TranslationEngine, TranslationConfig
from .formatter import DocumentFormatter
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessingConfig:
    """处理配置"""
    # 翻译配置
    translation_provider: str = 'nllb'
    source_language: str = 'auto'
    target_language: str = 'zh-CN'
    translation_model: Optional[str] = None
    api_key: Optional[str] = None
    
    # 输出配置
    output_format: str = 'docx'  # 'docx', 'pdf', 'both'
    layout: str = 'side_by_side'  # 'side_by_side', 'paragraph_by_paragraph'
    replace_original: bool = False
    
    # 处理配置
    batch_size: int = 10
    delay_between_requests: float = 1.0
    max_retries: int = 3
    
    # 文件配置
    keep_temp_files: bool = False
    output_directory: Optional[str] = None


@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    input_file: str
    output_files: List[str]
    processing_time: float
    original_text_count: int
    translated_text_count: int
    provider: str
    error: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class BatchProcessor:
    """批处理器"""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.logger = get_logger(__name__)
        
        # 初始化组件
        self.pdf_parser = PDFParser()
        self.formatter = DocumentFormatter()
        
        # 创建翻译引擎
        translation_config = TranslationConfig(
            provider=config.translation_provider,
            source_language=config.source_language,
            target_language=config.target_language,
            model=config.translation_model,
            api_key=config.api_key,
            batch_size=config.batch_size,
            delay_between_requests=config.delay_between_requests,
            max_retries=config.max_retries
        )
        
        self.translation_engine = TranslationEngine(translation_config)
    
    def process_pdf(self, pdf_path: str, output_name: Optional[str] = None) -> ProcessingResult:
        """处理单个PDF文件
        
        Args:
            pdf_path: PDF文件路径
            output_name: 输出文件名（不含扩展名）
            
        Returns:
            处理结果
        """
        start_time = time.time()
        temp_files = []
        output_files = []
        
        try:
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
            self.logger.info("步骤1: 解析PDF文档")
            parse_result = self.pdf_parser.parse_pdf(pdf_path)
            
            if not parse_result['success']:
                raise RuntimeError(f"PDF解析失败: {parse_result.get('error')}")
            
            temp_files.extend(parse_result.get('temp_files', []))
            extracted_texts = parse_result['texts']
            
            if not extracted_texts:
                raise RuntimeError("PDF中未提取到任何文本")
            
            self.logger.info(f"提取了 {len(extracted_texts)} 个文本段落")
            
            # 步骤2: 翻译文本
            self.logger.info("步骤2: 翻译文本内容")
            translation_result = self.translation_engine.translate_texts(extracted_texts)
            
            if not translation_result['success']:
                raise RuntimeError(f"翻译失败: {translation_result.get('error')}")
            
            translated_texts = translation_result['translated_texts']
            self.logger.info(f"翻译了 {len(translated_texts)} 个文本段落")
            
            # 步骤3: 生成输出文档
            self.logger.info("步骤3: 生成输出文档")
            output_files = self._generate_output_documents(
                extracted_texts, 
                translated_texts, 
                output_dir, 
                output_name
            )
            
            # 步骤4: 生成处理报告
            self._generate_processing_report(
                translation_result, 
                extracted_texts, 
                translated_texts,
                output_dir, 
                output_name
            )
            
            processing_time = time.time() - start_time
            
            result = ProcessingResult(
                success=True,
                input_file=pdf_path,
                output_files=output_files,
                processing_time=processing_time,
                original_text_count=len(extracted_texts),
                translated_text_count=len(translated_texts),
                provider=self.config.translation_provider
            )
            
            self.logger.info(f"PDF处理完成，耗时: {processing_time:.2f}秒")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"PDF处理失败: {error_msg}")
            
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
    
    def process_multiple_pdfs(self, pdf_paths: List[str]) -> List[ProcessingResult]:
        """批量处理多个PDF文件
        
        Args:
            pdf_paths: PDF文件路径列表
            
        Returns:
            处理结果列表
        """
        results = []
        
        self.logger.info(f"开始批量处理 {len(pdf_paths)} 个PDF文件")
        
        for i, pdf_path in enumerate(pdf_paths, 1):
            self.logger.info(f"处理进度: {i}/{len(pdf_paths)} - {os.path.basename(pdf_path)}")
            
            result = self.process_pdf(pdf_path)
            results.append(result)
            
            # 处理间隔
            if i < len(pdf_paths) and self.config.delay_between_requests > 0:
                time.sleep(self.config.delay_between_requests)
        
        # 生成批量处理报告
        self._generate_batch_report(results)
        
        self.logger.info("批量处理完成")
        return results
    
    def _generate_output_documents(self, 
                                 original_texts: List[str], 
                                 translated_texts: List[str],
                                 output_dir: str, 
                                 output_name: str) -> List[str]:
        """生成输出文档"""
        output_files = []
        
        # 生成DOCX文档
        if self.config.output_format in ['docx', 'both']:
            docx_path = os.path.join(output_dir, f"{output_name}.docx")
            
            success = self.formatter.create_bilingual_document(
                original_texts=original_texts,
                translated_texts=translated_texts,
                output_path=docx_path,
                title=f"双语对照文档 - {output_name}",
                layout=self.config.layout
            )
            
            if success:
                output_files.append(docx_path)
                self.logger.info(f"DOCX文档已生成: {docx_path}")
        
        # 生成PDF文档
        if self.config.output_format in ['pdf', 'both']:
            if self.formatter.is_docx2pdf_available():
                # 先生成DOCX，再转换为PDF
                temp_docx = os.path.join(output_dir, f"{output_name}_temp.docx")
                pdf_path = os.path.join(output_dir, f"{output_name}.pdf")
                
                docx_success = self.formatter.create_bilingual_document(
                    original_texts=original_texts,
                    translated_texts=translated_texts,
                    output_path=temp_docx,
                    title=f"双语对照文档 - {output_name}",
                    layout=self.config.layout
                )
                
                if docx_success:
                    pdf_success = self.formatter.convert_docx_to_pdf(temp_docx, pdf_path)
                    if pdf_success:
                        output_files.append(pdf_path)
                        self.logger.info(f"PDF文档已生成: {pdf_path}")
                    
                    # 清理临时DOCX文件
                    if not self.config.keep_temp_files:
                        try:
                            os.remove(temp_docx)
                        except:
                            pass
            else:
                self.logger.warning("docx2pdf不可用，跳过PDF生成")
        
        return output_files
    
    def _generate_processing_report(self, 
                                  translation_result: Dict[str, Any],
                                  original_texts: List[str],
                                  translated_texts: List[str],
                                  output_dir: str, 
                                  output_name: str):
        """生成处理报告"""
        try:
            report_path = os.path.join(output_dir, f"{output_name}_report.docx")
            
            # 增强翻译结果数据
            enhanced_result = translation_result.copy()
            enhanced_result.update({
                'original_texts': original_texts,
                'translated_texts': translated_texts,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'config': asdict(self.config)
            })
            
            self.formatter.create_translation_report(enhanced_result, report_path)
            self.logger.info(f"处理报告已生成: {report_path}")
            
        except Exception as e:
            self.logger.error(f"生成处理报告失败: {e}")
    
    def _generate_batch_report(self, results: List[ProcessingResult]):
        """生成批量处理报告"""
        try:
            if not self.config.output_directory:
                return
            
            report_path = os.path.join(
                self.config.output_directory, 
                f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("PDF批量翻译处理报告\n")
                f.write("=" * 50 + "\n\n")
                
                # 统计信息
                total_files = len(results)
                successful_files = sum(1 for r in results if r.success)
                failed_files = total_files - successful_files
                total_time = sum(r.processing_time for r in results)
                
                f.write(f"处理统计:\n")
                f.write(f"  总文件数: {total_files}\n")
                f.write(f"  成功文件数: {successful_files}\n")
                f.write(f"  失败文件数: {failed_files}\n")
                f.write(f"  总处理时间: {total_time:.2f}秒\n")
                f.write(f"  平均处理时间: {total_time/total_files:.2f}秒/文件\n\n")
                
                # 详细结果
                f.write("详细结果:\n")
                f.write("-" * 30 + "\n")
                
                for i, result in enumerate(results, 1):
                    f.write(f"{i}. {os.path.basename(result.input_file)}\n")
                    f.write(f"   状态: {'成功' if result.success else '失败'}\n")
                    f.write(f"   处理时间: {result.processing_time:.2f}秒\n")
                    
                    if result.success:
                        f.write(f"   原文段落数: {result.original_text_count}\n")
                        f.write(f"   译文段落数: {result.translated_text_count}\n")
                        f.write(f"   输出文件: {', '.join(os.path.basename(f) for f in result.output_files)}\n")
                    else:
                        f.write(f"   错误信息: {result.error}\n")
                    
                    f.write("\n")
            
            self.logger.info(f"批量处理报告已生成: {report_path}")
            
        except Exception as e:
            self.logger.error(f"生成批量处理报告失败: {e}")
    
    def _cleanup_temp_files(self, temp_files: List[str]):
        """清理临时文件"""
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    self.logger.debug(f"已清理临时文件: {temp_file}")
            except Exception as e:
                self.logger.warning(f"清理临时文件失败 {temp_file}: {e}")
    
    @staticmethod
    def create_config(**kwargs) -> ProcessingConfig:
        """创建处理配置
        
        Args:
            **kwargs: 配置参数
            
        Returns:
            处理配置对象
        """
        return ProcessingConfig(**kwargs)
    
    def get_status(self) -> Dict[str, Any]:
        """获取处理器状态"""
        return {
            'translation_providers': TranslationEngine.get_supported_providers(),
            'output_formats': DocumentFormatter.get_supported_formats(),
            'config': asdict(self.config),
            'components': {
                'pdf_parser': self.pdf_parser is not None,
                'translation_engine': self.translation_engine is not None,
                'document_formatter': self.formatter is not None
            }
        }