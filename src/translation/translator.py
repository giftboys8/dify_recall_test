"""翻译引擎模块

支持多种翻译API和本地NLLB模型的翻译功能。
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass

try:
    from transformers import pipeline
except ImportError:
    pipeline = None

try:
    import openai
except ImportError:
    openai = None

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TranslationConfig:
    """翻译配置"""
    provider: str  # 'nllb', 'openai', 'google', 'baidu'
    source_language: str = 'auto'
    target_language: str = 'zh-CN'
    model: Optional[str] = None
    api_key: Optional[str] = None
    batch_size: int = 10
    delay_between_requests: float = 1.0
    temperature: float = 0.1
    max_retries: int = 3


class BaseTranslator(ABC):
    """翻译器基类"""
    
    def __init__(self, config: TranslationConfig):
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def translate_text(self, text: str) -> str:
        """翻译单个文本"""
        pass
    
    @abstractmethod
    def translate_batch(self, texts: List[str]) -> List[str]:
        """批量翻译文本"""
        pass
    
    def is_available(self) -> bool:
        """检查翻译器是否可用"""
        return True


class NLLBTranslator(BaseTranslator):
    """NLLB本地翻译器"""
    
    def __init__(self, config: TranslationConfig):
        super().__init__(config)
        self.translator = None
        self._initialize_model()
    
    def _initialize_model(self):
        """初始化NLLB模型"""
        if pipeline is None:
            raise ImportError("transformers库未安装，请运行: pip install transformers torch")
        
        try:
            model_name = self.config.model or 'facebook/nllb-200-distilled-600M'
            self.logger.info(f"正在加载NLLB模型: {model_name}")
            
            self.translator = pipeline(
                'translation',
                model=model_name,
                device=-1  # 使用CPU，如需GPU可设为0
            )
            
            self.logger.info("NLLB模型加载完成")
            
        except Exception as e:
            self.logger.error(f"NLLB模型加载失败: {e}")
            raise
    
    def translate_text(self, text: str) -> str:
        """翻译单个文本"""
        if not text.strip():
            return text
        
        try:
            # NLLB语言代码映射
            src_lang = self._get_nllb_lang_code(self.config.source_language)
            tgt_lang = self._get_nllb_lang_code(self.config.target_language)
            
            result = self.translator(
                text,
                src_lang=src_lang,
                tgt_lang=tgt_lang
            )
            
            return result[0]['translation_text']
            
        except Exception as e:
            self.logger.error(f"NLLB翻译失败: {e}")
            return text  # 翻译失败时返回原文
    
    def translate_batch(self, texts: List[str]) -> List[str]:
        """批量翻译文本"""
        results = []
        
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]
            batch_results = []
            
            for text in batch:
                translated = self.translate_text(text)
                batch_results.append(translated)
                
                # 添加延迟避免过载
                if self.config.delay_between_requests > 0:
                    time.sleep(self.config.delay_between_requests)
            
            results.extend(batch_results)
            self.logger.info(f"已完成批次翻译: {i + len(batch)}/{len(texts)}")
        
        return results
    
    def _get_nllb_lang_code(self, lang: str) -> str:
        """获取NLLB语言代码"""
        lang_mapping = {
            'zh-CN': 'zho_Hans',
            'zh': 'zho_Hans',
            'en': 'eng_Latn',
            'en-US': 'eng_Latn',
            'ja': 'jpn_Jpan',
            'ko': 'kor_Hang',
            'fr': 'fra_Latn',
            'de': 'deu_Latn',
            'es': 'spa_Latn',
            'auto': 'zho_Hans'  # 默认假设中文
        }
        
        return lang_mapping.get(lang, 'eng_Latn')
    
    def is_available(self) -> bool:
        """检查NLLB翻译器是否可用"""
        return self.translator is not None


class OpenAITranslator(BaseTranslator):
    """OpenAI翻译器"""
    
    def __init__(self, config: TranslationConfig):
        super().__init__(config)
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化OpenAI客户端"""
        if openai is None:
            raise ImportError("openai库未安装，请运行: pip install openai")
        
        if not self.config.api_key:
            raise ValueError("OpenAI API密钥未配置")
        
        openai.api_key = self.config.api_key
        self.logger.info("OpenAI客户端初始化完成")
    
    def translate_text(self, text: str) -> str:
        """翻译单个文本"""
        if not text.strip():
            return text
        
        try:
            model = self.config.model or "gpt-3.5-turbo"
            
            # 构建翻译提示
            target_lang_name = self._get_language_name(self.config.target_language)
            prompt = f"请将以下文本翻译成{target_lang_name}，保持原文的语气和格式：\n\n{text}"
            
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个专业的翻译助手，能够准确翻译各种文档内容。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=4000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"OpenAI翻译失败: {e}")
            return text
    
    def translate_batch(self, texts: List[str]) -> List[str]:
        """批量翻译文本"""
        results = []
        
        for i, text in enumerate(texts):
            translated = self.translate_text(text)
            results.append(translated)
            
            # 添加延迟避免API限流
            if self.config.delay_between_requests > 0:
                time.sleep(self.config.delay_between_requests)
            
            if (i + 1) % 10 == 0:
                self.logger.info(f"已完成翻译: {i + 1}/{len(texts)}")
        
        return results
    
    def _get_language_name(self, lang_code: str) -> str:
        """获取语言名称"""
        lang_names = {
            'zh-CN': '中文',
            'zh': '中文',
            'en': '英文',
            'en-US': '英文',
            'ja': '日文',
            'ko': '韩文',
            'fr': '法文',
            'de': '德文',
            'es': '西班牙文'
        }
        return lang_names.get(lang_code, '英文')
    
    def is_available(self) -> bool:
        """检查OpenAI翻译器是否可用"""
        return bool(self.config.api_key)


class TranslationEngine:
    """翻译引擎主类"""
    
    def __init__(self, config: TranslationConfig):
        self.config = config
        self.translator = self._create_translator()
        self.logger = get_logger(__name__)
    
    def _create_translator(self) -> BaseTranslator:
        """创建翻译器实例"""
        if self.config.provider == 'nllb':
            return NLLBTranslator(self.config)
        elif self.config.provider == 'openai':
            return OpenAITranslator(self.config)
        else:
            raise ValueError(f"不支持的翻译提供商: {self.config.provider}")
    
    def translate_texts(self, texts: List[str]) -> Dict[str, Any]:
        """翻译文本列表
        
        Args:
            texts: 待翻译的文本列表
            
        Returns:
            翻译结果字典
        """
        try:
            if not self.translator.is_available():
                raise RuntimeError(f"翻译器 {self.config.provider} 不可用")
            
            self.logger.info(f"开始翻译 {len(texts)} 个文本片段")
            start_time = time.time()
            
            # 执行批量翻译
            translated_texts = self.translator.translate_batch(texts)
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.logger.info(f"翻译完成，耗时: {duration:.2f}秒")
            
            return {
                'success': True,
                'translated_texts': translated_texts,
                'original_count': len(texts),
                'translated_count': len(translated_texts),
                'duration': duration,
                'provider': self.config.provider
            }
            
        except Exception as e:
            self.logger.error(f"翻译失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': self.config.provider
            }
    
    def translate_single(self, text: str) -> str:
        """翻译单个文本
        
        Args:
            text: 待翻译的文本
            
        Returns:
            翻译后的文本
        """
        if not self.translator.is_available():
            self.logger.error(f"翻译器 {self.config.provider} 不可用")
            return text
        
        return self.translator.translate_text(text)
    
    @staticmethod
    def get_supported_providers() -> List[str]:
        """获取支持的翻译提供商列表"""
        providers = ['nllb']
        
        if openai is not None:
            providers.append('openai')
        
        return providers
    
    @staticmethod
    def create_config(provider: str, **kwargs) -> TranslationConfig:
        """创建翻译配置
        
        Args:
            provider: 翻译提供商
            **kwargs: 其他配置参数
            
        Returns:
            翻译配置对象
        """
        return TranslationConfig(provider=provider, **kwargs)