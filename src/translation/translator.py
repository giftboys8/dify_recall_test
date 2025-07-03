"""翻译引擎模块

支持多种翻译API和本地NLLB模型的翻译功能。
"""

import asyncio
import gc
import json
import os
import time
import torch
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
        self.model_loaded = False
        self.nllb_config = self._load_nllb_config()
        # 延迟加载模型，避免初始化时内存压力
    
    def _load_nllb_config(self) -> Dict[str, Any]:
        """加载NLLB配置文件"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'nllb_config.json')
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    return config_data.get('nllb_translator', {})
            else:
                self.logger.warning(f"NLLB配置文件不存在: {config_path}，使用默认配置")
        except Exception as e:
            self.logger.warning(f"加载NLLB配置文件失败: {e}，使用默认配置")
        
        # 返回默认配置
        return {
            "model_name": "facebook/nllb-200-distilled-600M",
            "device": "cpu",
            "memory_optimization": {
                "use_half_precision": True,
                "low_cpu_mem_usage": True,
                "use_cache": False
            },
            "offline_mode": {
                "prefer_local_files": True,
                "fallback_to_online": True
            }
        }
    
    def _initialize_model(self):
        """初始化NLLB模型（延迟加载）"""
        if self.model_loaded:
            return
            
        if pipeline is None:
            raise ImportError("transformers库未安装，请运行: pip install transformers torch")
        
        try:
            import gc
            import torch
            
            # 清理内存
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # 从配置文件获取模型设置
            model_name = self.config.model or self.nllb_config.get('model_name', 'facebook/nllb-200-distilled-600M')
            memory_config = self.nllb_config.get('memory_optimization', {})
            offline_config = self.nllb_config.get('offline_mode', {})
            
            self.logger.info(f"正在加载NLLB模型: {model_name}")
            self.logger.info(f"内存优化设置: {memory_config}")
            self.logger.info(f"离线模式设置: {offline_config}")
            
            # 使用配置文件设置，支持离线模式
            device = -1 if self.nllb_config.get('device', 'cpu') == 'cpu' else 0
            
            # 构建模型参数
            model_kwargs = {}
            if memory_config.get('low_cpu_mem_usage', True):
                model_kwargs['low_cpu_mem_usage'] = True
            if memory_config.get('use_half_precision', True):
                model_kwargs['torch_dtype'] = torch.float16
            if not memory_config.get('use_cache', False):
                model_kwargs['use_cache'] = False
            
            # 尝试加载模型
            if offline_config.get('prefer_local_files', True):
                try:
                    # 首先尝试使用本地缓存的模型
                    self.translator = pipeline(
                        'translation',
                        model=model_name,
                        device=device,
                        local_files_only=True,  # 只使用本地文件
                        model_kwargs=model_kwargs
                    )
                    self.logger.info(f"成功从本地缓存加载NLLB模型: {model_name}")
                except Exception as e:
                    self.logger.warning(f"本地缓存加载失败: {e}")
                    if offline_config.get('fallback_to_online', True):
                        self._try_online_loading(model_name, device, model_kwargs, memory_config)
                    else:
                        raise e
            else:
                # 直接尝试在线加载
                self._try_online_loading(model_name, device, model_kwargs, memory_config)
            
            self.model_loaded = True
            self.logger.info("NLLB模型加载完成")
            
        except Exception as e:
            self.logger.error(f"NLLB模型加载失败: {e}")
            # 不抛出异常，而是标记为不可用
            self.translator = None
            self.model_loaded = False
    
    def _try_online_loading(self, model_name: str, device: int, model_kwargs: Dict, memory_config: Dict):
        """尝试在线加载模型"""
        try:
            # 回退到在线下载
            self.translator = pipeline(
                'translation',
                model=model_name,
                device=device,
                model_kwargs=model_kwargs
            )
            self.logger.info(f"成功在线下载NLLB模型: {model_name}")
        except Exception as e2:
            self.logger.warning(f"在线下载也失败，尝试标准加载: {e2}")
            # 最后回退到标准加载
            try:
                self.translator = pipeline(
                    'translation',
                    model=model_name,
                    device=device
                )
                self.logger.info(f"使用标准方式加载NLLB模型: {model_name}")
            except Exception as e3:
                self.logger.error(f"所有加载方式都失败: {e3}")
                # 尝试回退模型
                fallback_models = self.nllb_config.get('fallback_models', [])
                if fallback_models:
                    self._try_fallback_models(fallback_models, device)
                else:
                    raise e3
    
    def _try_fallback_models(self, fallback_models: List[str], device: int):
        """尝试回退模型"""
        for fallback_model in fallback_models:
            try:
                self.logger.info(f"尝试回退模型: {fallback_model}")
                self.translator = pipeline(
                    'translation',
                    model=fallback_model,
                    device=device
                )
                self.logger.info(f"成功加载回退模型: {fallback_model}")
                return
            except Exception as e:
                self.logger.warning(f"回退模型 {fallback_model} 加载失败: {e}")
                continue
        
        # 所有模型都失败
        raise Exception("所有模型（包括回退模型）都加载失败")
    
    def translate_text(self, text: str) -> str:
        """翻译单个文本"""
        if not text.strip():
            return text
        
        # 确保模型已加载
        if not self.model_loaded:
            self._initialize_model()
        
        # 如果模型仍未加载成功，返回原文
        if not self.translator:
            self.logger.warning("NLLB模型未加载，返回原文")
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
        
        # 动态计算批处理大小
        dynamic_batch_size = self._calculate_dynamic_batch_size(texts)
        self.logger.info(f"使用动态批处理大小: {dynamic_batch_size}")
        
        for i in range(0, len(texts), dynamic_batch_size):
            batch = texts[i:i + dynamic_batch_size]
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
    
    def _calculate_dynamic_batch_size(self, texts: List[str], max_tokens_per_batch: int = 15000) -> int:
        """动态计算批处理大小
        
        Args:
            texts: 文本列表
            max_tokens_per_batch: 每批次最大token数
            
        Returns:
            动态批处理大小
        """
        if not texts:
            return self.config.batch_size
        
        # 计算平均文本长度
        total_chars = sum(len(text) for text in texts)
        avg_chars = total_chars / len(texts)
        
        # 估算token数（中文约1.3倍字符数，英文约0.25倍字符数）
        # 使用保守估计1.5倍字符数
        estimated_tokens_per_text = avg_chars * 1.5
        
        if estimated_tokens_per_text <= 0:
            return self.config.batch_size
        
        # 计算动态批处理大小
        dynamic_size = max(1, min(self.config.batch_size, int(max_tokens_per_batch / estimated_tokens_per_text)))
        
        # 根据翻译提供商调整
        if self.config.provider in ['deepseek', 'openai']:
            # API服务可以处理更大批次
            dynamic_size = min(dynamic_size, 20)
        elif self.config.provider == 'nllb':
            # 本地模型限制更严格
            dynamic_size = min(dynamic_size, 5)
        
        self.logger.debug(f"文本统计: 总数={len(texts)}, 平均长度={avg_chars:.1f}字符, 估算token={estimated_tokens_per_text:.1f}")
        
        return dynamic_size
    
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
        if not self.model_loaded:
            try:
                self._initialize_model()
            except Exception as e:
                self.logger.error(f"模型初始化检查失败: {e}")
                return False
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


class DeepSeekTranslator(BaseTranslator):
    """DeepSeek翻译器（使用OpenAI兼容API）"""
    
    def __init__(self, config: TranslationConfig):
        super().__init__(config)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化DeepSeek客户端"""
        if openai is None:
            raise ImportError("openai库未安装，请运行: pip install openai")
        
        if not self.config.api_key:
            raise ValueError("DeepSeek API密钥未配置")
        
        # 创建OpenAI客户端，指向DeepSeek API
        try:
            # 尝试使用新版本的openai库
            self.client = openai.OpenAI(
                api_key=self.config.api_key,
                base_url="https://api.deepseek.com"
            )
        except AttributeError:
            # 兼容旧版本的openai库
            openai.api_key = self.config.api_key
            openai.api_base = "https://api.deepseek.com/v1"
            self.client = openai
        
        self.logger.info("DeepSeek客户端初始化完成")
    
    def translate_text(self, text: str) -> str:
        """翻译单个文本"""
        if not text.strip():
            return text
        
        try:
            model = self.config.model or "deepseek-chat"
            
            target_lang_name = self._get_language_name(self.config.target_language)
            source_lang_name = self._get_language_name(self.config.source_language)
            
            prompt = f"请将以下{source_lang_name}文本翻译成{target_lang_name}，保持原文的格式和含义：\n\n{text}"
            
            # 兼容不同版本的openai库
            if hasattr(self.client, 'chat'):
                # 新版本openai库
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的翻译助手，能够准确翻译各种语言。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                translated_text = response.choices[0].message.content.strip()
            else:
                # 旧版本openai库
                response = self.client.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的翻译助手，能够准确翻译各种语言。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                translated_text = response.choices[0].message.content.strip()
            
            return translated_text
            
        except Exception as e:
            self.logger.error(f"DeepSeek翻译失败: {e}")
            return text
    
    def translate_batch(self, texts: List[str]) -> List[str]:
        """批量翻译文本"""
        translated_texts = []
        
        # 动态计算批处理大小
        dynamic_batch_size = self._calculate_dynamic_batch_size(texts)
        self.logger.info(f"使用动态批处理大小: {dynamic_batch_size}")
        
        for i in range(0, len(texts), dynamic_batch_size):
            batch = texts[i:i + dynamic_batch_size]
            batch_results = []
            
            for j, text in enumerate(batch):
                self.logger.info(f"翻译进度: {i+j+1}/{len(texts)}")
                translated_text = self.translate_text(text)
                batch_results.append(translated_text)
                
                # 添加延迟以避免API限制
                if j < len(batch) - 1:
                    time.sleep(self.config.delay_between_requests)
            
            translated_texts.extend(batch_results)
            
            # 批次间额外延迟
            if i + dynamic_batch_size < len(texts):
                time.sleep(self.config.delay_between_requests * 0.5)
        
        return translated_texts
    
    def _calculate_dynamic_batch_size(self, texts: List[str], max_tokens_per_batch: int = 12000) -> int:
        """动态计算批处理大小（DeepSeek优化版本）
        
        Args:
            texts: 文本列表
            max_tokens_per_batch: 每批次最大token数
            
        Returns:
            动态批处理大小
        """
        if not texts:
            return self.config.batch_size
        
        # 计算平均文本长度
        total_chars = sum(len(text) for text in texts)
        avg_chars = total_chars / len(texts)
        
        # DeepSeek API的token估算（更保守）
        estimated_tokens_per_text = avg_chars * 1.8  # 包含prompt开销
        
        if estimated_tokens_per_text <= 0:
            return self.config.batch_size
        
        # 计算动态批处理大小
        dynamic_size = max(1, min(self.config.batch_size, int(max_tokens_per_batch / estimated_tokens_per_text)))
        
        # DeepSeek API限制调整
        dynamic_size = min(dynamic_size, 15)  # DeepSeek API建议的最大并发
        
        self.logger.debug(f"DeepSeek文本统计: 总数={len(texts)}, 平均长度={avg_chars:.1f}字符, 估算token={estimated_tokens_per_text:.1f}")
        
        return dynamic_size
    
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
            'es': '西班牙文',
            'auto': '自动检测'
        }
        return lang_names.get(lang_code, '英文')
    
    def is_available(self) -> bool:
        """检查DeepSeek翻译器是否可用"""
        return bool(self.config.api_key and self.client)


class DeepSeekReasonerTranslator(BaseTranslator):
    """DeepSeek Reasoner翻译器 - 专门用于复杂推理翻译任务"""
    
    def __init__(self, config: TranslationConfig):
        super().__init__(config)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化DeepSeek Reasoner客户端"""
        if openai is None:
            raise ImportError("openai库未安装，请运行: pip install openai")
        
        if not self.config.api_key:
            raise ValueError("DeepSeek API密钥未配置")
        
        # 创建OpenAI客户端，指向DeepSeek API
        try:
            # 尝试使用新版本的openai库
            self.client = openai.OpenAI(
                api_key=self.config.api_key,
                base_url="https://api.deepseek.com"
            )
        except AttributeError:
            # 兼容旧版本的openai库
            openai.api_key = self.config.api_key
            openai.api_base = "https://api.deepseek.com/v1"
            self.client = openai
        
        self.logger.info("DeepSeek Reasoner客户端初始化完成")
    
    def translate_text(self, text: str) -> str:
        """翻译单个文本 - 使用深度推理方法"""
        if not text.strip():
            return text
        
        try:
            model = self.config.model or "deepseek-reasoner"
            
            # 构建更详细的翻译提示，利用推理能力
            target_lang_name = self._get_language_name(self.config.target_language)
            source_lang_name = self._get_language_name(self.config.source_language)
            
            prompt = f"""作为一个专业的翻译专家，请仔细分析以下文本并进行高质量翻译：

原文语言：{source_lang_name}
目标语言：{target_lang_name}

请按照以下步骤进行翻译：
1. 首先理解原文的核心含义、语境和语调
2. 识别专业术语、习语或文化特定表达
3. 考虑目标语言的表达习惯和文化背景
4. 确保翻译的准确性、流畅性和自然性
5. 保持原文的格式和结构

原文：
{text}

请提供最终的翻译结果："""
            
            # 兼容不同版本的openai库
            if hasattr(self.client, 'chat'):
                # 新版本openai库
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "你是一个具有深度推理能力的专业翻译专家，能够理解复杂语境并提供高质量的翻译。你会仔细分析文本的含义、语境和文化背景，然后提供准确、流畅、自然的翻译。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=6000  # 增加token限制以支持推理过程
                )
                return response.choices[0].message.content.strip()
            else:
                # 旧版本openai库
                response = self.client.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "你是一个具有深度推理能力的专业翻译专家，能够理解复杂语境并提供高质量的翻译。你会仔细分析文本的含义、语境和文化背景，然后提供准确、流畅、自然的翻译。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=6000
                )
                return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"DeepSeek Reasoner翻译失败: {e}")
            return text  # 翻译失败时返回原文
    
    def translate_batch(self, texts: List[str]) -> List[str]:
        """批量翻译文本 - 使用推理模型，增加延迟以确保质量"""
        results = []
        
        # 动态计算批处理大小（推理模型更保守）
        dynamic_batch_size = self._calculate_dynamic_batch_size(texts)
        self.logger.info(f"推理翻译使用动态批处理大小: {dynamic_batch_size}")
        
        for i in range(0, len(texts), dynamic_batch_size):
            batch = texts[i:i + dynamic_batch_size]
            batch_results = []
            
            for j, text in enumerate(batch):
                translated = self.translate_text(text)
                batch_results.append(translated)
                
                # 推理模型需要更多时间，增加延迟
                delay = max(self.config.delay_between_requests, 2.0)  # 最少2秒延迟
                time.sleep(delay)
                
                if (i + j + 1) % 3 == 0:  # 更频繁的进度报告
                    self.logger.info(f"已完成推理翻译: {i + j + 1}/{len(texts)}")
            
            results.extend(batch_results)
            
            # 批次间额外延迟（推理模型需要更多休息时间）
            if i + dynamic_batch_size < len(texts):
                time.sleep(self.config.delay_between_requests * 1.5)
        
        return results
    
    def _calculate_dynamic_batch_size(self, texts: List[str], max_tokens_per_batch: int = 8000) -> int:
        """动态计算批处理大小（推理模型优化版本）
        
        Args:
            texts: 文本列表
            max_tokens_per_batch: 每批次最大token数（推理模型更保守）
            
        Returns:
            动态批处理大小
        """
        if not texts:
            return min(self.config.batch_size, 3)  # 推理模型默认更小批次
        
        # 计算平均文本长度
        total_chars = sum(len(text) for text in texts)
        avg_chars = total_chars / len(texts)
        
        # 推理模型的token估算（包含大量推理过程开销）
        estimated_tokens_per_text = avg_chars * 2.5  # 推理过程需要更多token
        
        if estimated_tokens_per_text <= 0:
            return min(self.config.batch_size, 3)
        
        # 计算动态批处理大小
        dynamic_size = max(1, min(self.config.batch_size, int(max_tokens_per_batch / estimated_tokens_per_text)))
        
        # 推理模型限制更严格
        dynamic_size = min(dynamic_size, 5)  # 推理模型最大批次为5
        
        self.logger.debug(f"推理模型文本统计: 总数={len(texts)}, 平均长度={avg_chars:.1f}字符, 估算token={estimated_tokens_per_text:.1f}")
        
        return dynamic_size
    
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
            'es': '西班牙文',
            'auto': '自动检测'
        }
        return lang_names.get(lang_code, '英文')
    
    def is_available(self) -> bool:
        """检查DeepSeek Reasoner翻译器是否可用"""
        return bool(self.config.api_key and self.client)




class TranslationEngine:
    """翻译引擎主类"""
    
    def __init__(self, config: TranslationConfig):
        self.config = config
        self.translator = None
        self.logger = get_logger(__name__)
    
    def _get_translator(self) -> BaseTranslator:
        """获取翻译器实例（延迟初始化）"""
        if self.translator is None:
            self.translator = self._create_translator()
        return self.translator
    
    def _create_translator(self) -> BaseTranslator:
        """创建翻译器实例"""
        if self.config.provider == 'nllb':
            return NLLBTranslator(self.config)
        elif self.config.provider == 'openai':
            return OpenAITranslator(self.config)
        elif self.config.provider == 'deepseek':
            return DeepSeekTranslator(self.config)
        elif self.config.provider == 'deepseek-reasoner':
            return DeepSeekReasonerTranslator(self.config)
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
            translator = self._get_translator()
            if not translator.is_available():
                raise RuntimeError(f"翻译器 {self.config.provider} 不可用")
            
            self.logger.info(f"开始翻译 {len(texts)} 个文本片段")
            start_time = time.time()
            
            # 执行批量翻译
            translated_texts = translator.translate_batch(texts)
            
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
        translator = self._get_translator()
        if not translator.is_available():
            self.logger.error(f"翻译器 {self.config.provider} 不可用")
            return text
        
        return translator.translate_text(text)
    
    @staticmethod
    def get_supported_providers() -> List[str]:
        """获取支持的翻译提供商列表"""
        providers = ['nllb']
        
        if openai is not None:
            providers.extend(['openai', 'deepseek', 'deepseek-reasoner'])
        
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