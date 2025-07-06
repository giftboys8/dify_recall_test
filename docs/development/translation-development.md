# 翻译功能开发指南

## 🎯 概述

本文档详细介绍了项目中翻译功能的技术实现、架构设计和开发指南。翻译功能支持多种文档格式，包括PDF、PPT、Word等，并集成了多个翻译引擎。

## 🏗️ 架构设计

### 核心组件

```
翻译系统架构
├── 文档解析层 (Document Parsers)
│   ├── PDFParser - PDF文档解析
│   ├── PPTParser - PowerPoint解析
│   └── WordParser - Word文档解析
├── 翻译引擎层 (Translation Engines)
│   ├── OpenAITranslator - GPT翻译
│   ├── DeepSeekTranslator - DeepSeek翻译
│   └── NLLBTranslator - NLLB本地翻译
├── 格式处理层 (Format Processors)
│   ├── LayoutPreserver - 布局保持
│   └── StyleManager - 样式管理
└── 输出生成层 (Output Generators)
    ├── PDFGenerator - PDF生成
    └── DocumentGenerator - 文档生成
```

### 数据流程

```
输入文档 → 格式检测 → 文档解析 → 文本提取 → 翻译处理 → 格式重建 → 输出文档
```

## 📄 支持的文档格式

### PDF文档处理

**技术栈**：
- `pdf2docx` - PDF到DOCX转换
- `PyPDF2` - PDF文本提取
- `reportlab` - PDF生成

**处理流程**：

```python
# PDF翻译处理流程
from pdf2docx import Converter
from src.translation.pdf_parser import PDFParser
from src.translation.translator import TranslationEngine

def translate_pdf_with_layout(input_pdf: str, output_pdf: str, 
                             source_lang: str, target_lang: str):
    """
    保持布局的PDF翻译
    
    Args:
        input_pdf: 输入PDF文件路径
        output_pdf: 输出PDF文件路径
        source_lang: 源语言代码
        target_lang: 目标语言代码
    """
    
    # Step 1: PDF转换为结构化DOCX
    temp_docx = "temp_converted.docx"
    cv = Converter(input_pdf)
    cv.convert(temp_docx, keep_layout=True)
    cv.close()
    
    # Step 2: 提取文本内容
    parser = PDFParser()
    text_blocks = parser.extract_text_blocks(temp_docx)
    
    # Step 3: 批量翻译
    translator = TranslationEngine.create("openai")
    translated_blocks = translator.translate_batch(
        text_blocks, source_lang, target_lang
    )
    
    # Step 4: 重建文档结构
    parser.rebuild_document(temp_docx, translated_blocks)
    
    # Step 5: 转换回PDF
    parser.convert_to_pdf(temp_docx, output_pdf)
    
    # 清理临时文件
    os.remove(temp_docx)
```

### PowerPoint处理

**技术栈**：
- `python-pptx` - PPT文档操作
- `Pillow` - 图像处理

**核心实现**：

```python
# src/translation/ppt_parser.py
from pptx import Presentation
from typing import List, Dict, Any
import logging

class PPTParser:
    """PowerPoint文档解析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_text_with_metadata(self, ppt_path: str) -> List[Dict[str, Any]]:
        """
        提取文本及其元数据
        
        Returns:
            包含文本、位置、样式信息的字典列表
        """
        presentation = Presentation(ppt_path)
        text_blocks = []
        
        for slide_idx, slide in enumerate(presentation.slides):
            slide_texts = self._extract_slide_text(slide, slide_idx)
            text_blocks.extend(slide_texts)
        
        return text_blocks
    
    def _extract_slide_text(self, slide, slide_idx: int) -> List[Dict[str, Any]]:
        """提取单个幻灯片的文本"""
        texts = []
        
        for shape_idx, shape in enumerate(slide.shapes):
            try:
                if hasattr(shape, "text") and shape.text.strip():
                    text_info = {
                        'text': shape.text,
                        'slide_index': slide_idx,
                        'shape_index': shape_idx,
                        'position': {
                            'left': shape.left,
                            'top': shape.top,
                            'width': shape.width,
                            'height': shape.height
                        },
                        'shape_type': str(shape.shape_type)
                    }
                    
                    # 提取字体样式信息
                    if hasattr(shape, 'text_frame'):
                        text_info['font_info'] = self._extract_font_info(shape.text_frame)
                    
                    texts.append(text_info)
                    
            except Exception as e:
                self.logger.warning(f"跳过幻灯片{slide_idx}形状{shape_idx}: {e}")
                continue
        
        return texts
    
    def _extract_font_info(self, text_frame) -> Dict[str, Any]:
        """提取字体信息"""
        font_info = {
            'font_name': None,
            'font_size': None,
            'bold': False,
            'italic': False,
            'color': None
        }
        
        try:
            for paragraph in text_frame.paragraphs:
                for run in paragraph.runs:
                    if run.font.name:
                        font_info['font_name'] = run.font.name
                    if run.font.size:
                        font_info['font_size'] = run.font.size.pt
                    font_info['bold'] = run.font.bold or False
                    font_info['italic'] = run.font.italic or False
                    break  # 使用第一个run的样式
                break  # 使用第一个段落的样式
        except Exception as e:
            self.logger.warning(f"提取字体信息失败: {e}")
        
        return font_info
    
    def rebuild_presentation(self, original_path: str, translated_blocks: List[Dict[str, Any]], 
                           output_path: str):
        """重建翻译后的演示文稿"""
        presentation = Presentation(original_path)
        
        # 按幻灯片和形状索引组织翻译文本
        translations_map = {}
        for block in translated_blocks:
            slide_idx = block['slide_index']
            shape_idx = block['shape_index']
            if slide_idx not in translations_map:
                translations_map[slide_idx] = {}
            translations_map[slide_idx][shape_idx] = block['translated_text']
        
        # 应用翻译
        for slide_idx, slide in enumerate(presentation.slides):
            if slide_idx in translations_map:
                self._apply_translations_to_slide(slide, translations_map[slide_idx])
        
        presentation.save(output_path)
    
    def _apply_translations_to_slide(self, slide, translations: Dict[int, str]):
        """将翻译应用到幻灯片"""
        for shape_idx, shape in enumerate(slide.shapes):
            if shape_idx in translations and hasattr(shape, "text"):
                try:
                    shape.text = translations[shape_idx]
                except Exception as e:
                    self.logger.warning(f"应用翻译失败: {e}")
```

## 🔧 翻译引擎集成

### OpenAI翻译引擎

```python
# src/translation/engines/openai_translator.py
import openai
from typing import List, Dict, Any
from src.utils.config import get_config

class OpenAITranslator:
    """OpenAI翻译引擎"""
    
    def __init__(self):
        config = get_config()
        self.client = openai.OpenAI(
            api_key=config['openai']['api_key'],
            base_url=config['openai'].get('base_url')
        )
        self.model = config['openai'].get('model', 'gpt-3.5-turbo')
    
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """翻译单个文本"""
        prompt = f"""
        请将以下{source_lang}文本翻译成{target_lang}，保持原文的格式和语气：
        
        {text}
        
        翻译结果：
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的翻译助手，擅长准确翻译各种文档内容。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    
    def translate_batch(self, texts: List[str], source_lang: str, 
                       target_lang: str, batch_size: int = 10) -> List[str]:
        """批量翻译"""
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = []
            
            for text in batch:
                if text.strip():  # 跳过空文本
                    translated = self.translate_text(text, source_lang, target_lang)
                    batch_results.append(translated)
                else:
                    batch_results.append(text)
            
            results.extend(batch_results)
            
            # 添加延迟避免API限制
            time.sleep(1)
        
        return results
```

### NLLB本地翻译引擎

```python
# src/translation/engines/nllb_translator.py
from transformers import pipeline
import torch
from typing import List, Dict

class NLLBTranslator:
    """NLLB本地翻译引擎"""
    
    # 语言代码映射
    LANGUAGE_CODES = {
        'zh': 'zho_Hans',
        'en': 'eng_Latn',
        'ja': 'jpn_Jpan',
        'ko': 'kor_Hang',
        'fr': 'fra_Latn',
        'de': 'deu_Latn',
        'es': 'spa_Latn',
        'ru': 'rus_Cyrl'
    }
    
    def __init__(self, model_name: str = 'facebook/nllb-200-distilled-600M'):
        self.model_name = model_name
        self.device = 0 if torch.cuda.is_available() else -1
        self.translator = None
        self._load_model()
    
    def _load_model(self):
        """加载翻译模型"""
        try:
            self.translator = pipeline(
                'translation',
                model=self.model_name,
                device=self.device,
                model_kwargs={
                    'low_cpu_mem_usage': True,
                    'torch_dtype': torch.float16 if torch.cuda.is_available() else torch.float32
                }
            )
        except Exception as e:
            raise RuntimeError(f"NLLB模型加载失败: {e}")
    
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """翻译单个文本"""
        if not text.strip():
            return text
        
        src_code = self.LANGUAGE_CODES.get(source_lang)
        tgt_code = self.LANGUAGE_CODES.get(target_lang)
        
        if not src_code or not tgt_code:
            raise ValueError(f"不支持的语言: {source_lang} -> {target_lang}")
        
        try:
            result = self.translator(
                text,
                src_lang=src_code,
                tgt_lang=tgt_code,
                max_length=512
            )
            return result[0]['translation_text']
        except Exception as e:
            raise RuntimeError(f"翻译失败: {e}")
    
    def translate_batch(self, texts: List[str], source_lang: str, 
                       target_lang: str, batch_size: int = 8) -> List[str]:
        """批量翻译"""
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = []
            
            for text in batch:
                translated = self.translate_text(text, source_lang, target_lang)
                batch_results.append(translated)
            
            results.extend(batch_results)
        
        return results
```

## ⚙️ 配置管理

### 翻译配置结构

```json
{
  "translation": {
    "default_engine": "openai",
    "engines": {
      "openai": {
        "api_key": "your_api_key",
        "model": "gpt-3.5-turbo",
        "base_url": "https://api.openai.com/v1",
        "temperature": 0.3,
        "max_tokens": 2000,
        "batch_size": 10,
        "delay_between_requests": 1.0
      },
      "deepseek": {
        "api_key": "your_deepseek_key",
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1",
        "temperature": 0.1
      },
      "nllb": {
        "model_name": "facebook/nllb-200-distilled-600M",
        "device": "auto",
        "batch_size": 8,
        "max_length": 512,
        "use_cache": true
      }
    },
    "output": {
      "format": "pdf",
      "preserve_layout": true,
      "preserve_fonts": true,
      "output_directory": "./translated_documents"
    },
    "processing": {
      "chunk_size": 1000,
      "overlap_size": 100,
      "smart_chunking": true,
      "parallel_processing": true,
      "max_workers": 4
    }
  }
}
```

### 配置加载器

```python
# src/utils/translation_config.py
import json
from pathlib import Path
from typing import Dict, Any

class TranslationConfig:
    """翻译配置管理器"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "config/translation_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            return self._get_default_config()
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"配置文件加载失败: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "translation": {
                "default_engine": "nllb",
                "engines": {
                    "nllb": {
                        "model_name": "facebook/nllb-200-distilled-600M",
                        "device": "auto",
                        "batch_size": 8
                    }
                },
                "output": {
                    "format": "pdf",
                    "preserve_layout": True
                }
            }
        }
    
    def get_engine_config(self, engine_name: str) -> Dict[str, Any]:
        """获取特定引擎的配置"""
        engines = self.config.get("translation", {}).get("engines", {})
        return engines.get(engine_name, {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """获取输出配置"""
        return self.config.get("translation", {}).get("output", {})
    
    def save_config(self, config: Dict[str, Any]):
        """保存配置"""
        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        self.config = config
```

## 🚀 使用示例

### 基础翻译示例

```python
# 基础PDF翻译
from src.translation.processor import DocumentProcessor

processor = DocumentProcessor()
result = processor.translate_document(
    input_path="document.pdf",
    output_path="translated_document.pdf",
    source_lang="zh",
    target_lang="en",
    engine="openai"
)

if result.success:
    print(f"翻译完成: {result.output_path}")
else:
    print(f"翻译失败: {result.error_message}")
```

### 批量翻译示例

```python
# 批量文档翻译
from src.translation.batch_processor import BatchTranslationProcessor

processor = BatchTranslationProcessor()
files = ["doc1.pdf", "doc2.pptx", "doc3.docx"]

results = processor.process_batch(
    input_files=files,
    output_directory="./translated",
    source_lang="zh",
    target_lang="en",
    engine="nllb",
    parallel=True
)

for result in results:
    if result.success:
        print(f"✅ {result.input_file} -> {result.output_file}")
    else:
        print(f"❌ {result.input_file}: {result.error_message}")
```

### 自定义翻译流程

```python
# 自定义翻译流程
from src.translation.engines import TranslationEngineFactory
from src.translation.parsers import DocumentParserFactory

# 创建解析器和翻译引擎
parser = DocumentParserFactory.create_parser(".pdf")
translator = TranslationEngineFactory.create_engine("openai")

# 提取文本
text_blocks = parser.extract_text_with_metadata("input.pdf")

# 翻译文本
translated_blocks = []
for block in text_blocks:
    translated_text = translator.translate_text(
        block['text'], "zh", "en"
    )
    block['translated_text'] = translated_text
    translated_blocks.append(block)

# 重建文档
parser.rebuild_document("input.pdf", translated_blocks, "output.pdf")
```

## 🔍 调试和故障排除

### 常见问题

1. **PPT形状类型错误**
   ```python
   # 解决方案：添加异常处理
   try:
       shape_text = shape.text
   except Exception as e:
       logger.warning(f"跳过未知形状类型: {e}")
       continue
   ```

2. **内存不足**
   ```python
   # 解决方案：分块处理
   def process_large_document(file_path, chunk_size=1000):
       for chunk in split_document(file_path, chunk_size):
           process_chunk(chunk)
   ```

3. **API限制**
   ```python
   # 解决方案：添加重试和延迟
   import time
   from tenacity import retry, stop_after_attempt, wait_exponential
   
   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
   def translate_with_retry(text, source_lang, target_lang):
       return translator.translate_text(text, source_lang, target_lang)
   ```

### 日志配置

```python
# 翻译功能专用日志配置
import logging

def setup_translation_logging():
    """设置翻译功能日志"""
    logger = logging.getLogger('translation')
    logger.setLevel(logging.INFO)
    
    handler = logging.FileHandler('logs/translation.log')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
```

## 📈 性能优化

### 缓存策略

```python
# 翻译结果缓存
from functools import lru_cache
import hashlib

class TranslationCache:
    def __init__(self):
        self.cache = {}
    
    def get_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """生成缓存键"""
        content = f"{text}|{source_lang}|{target_lang}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_translation(self, text: str, source_lang: str, target_lang: str) -> str:
        """获取缓存的翻译"""
        key = self.get_cache_key(text, source_lang, target_lang)
        return self.cache.get(key)
    
    def cache_translation(self, text: str, source_lang: str, 
                         target_lang: str, translation: str):
        """缓存翻译结果"""
        key = self.get_cache_key(text, source_lang, target_lang)
        self.cache[key] = translation
```

### 并行处理

```python
# 并行翻译处理
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable

class ParallelTranslationProcessor:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    def process_parallel(self, texts: List[str], 
                        translation_func: Callable) -> List[str]:
        """并行处理翻译"""
        results = [None] * len(texts)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任务
            future_to_index = {
                executor.submit(translation_func, text): i 
                for i, text in enumerate(texts)
            }
            
            # 收集结果
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    results[index] = f"翻译失败: {e}"
        
        return results
```

## 📚 扩展开发

### 添加新的翻译引擎

```python
# 新翻译引擎示例
from abc import ABC, abstractmethod

class BaseTranslationEngine(ABC):
    """翻译引擎基类"""
    
    @abstractmethod
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """翻译单个文本"""
        pass
    
    @abstractmethod
    def translate_batch(self, texts: List[str], source_lang: str, 
                       target_lang: str) -> List[str]:
        """批量翻译"""
        pass

class CustomTranslationEngine(BaseTranslationEngine):
    """自定义翻译引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # 初始化自定义引擎
    
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        # 实现自定义翻译逻辑
        pass
    
    def translate_batch(self, texts: List[str], source_lang: str, 
                       target_lang: str) -> List[str]:
        # 实现批量翻译逻辑
        pass

# 注册新引擎
TranslationEngineFactory.register_engine("custom", CustomTranslationEngine)
```

### 添加新的文档格式支持

```python
# 新文档格式解析器
class ExcelParser(BaseDocumentParser):
    """Excel文档解析器"""
    
    def extract_text_with_metadata(self, file_path: str) -> List[Dict[str, Any]]:
        """提取Excel文本和元数据"""
        import openpyxl
        
        workbook = openpyxl.load_workbook(file_path)
        text_blocks = []
        
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            for row in sheet.iter_rows(values_only=True):
                for col_idx, cell_value in enumerate(row):
                    if cell_value and isinstance(cell_value, str):
                        text_blocks.append({
                            'text': cell_value,
                            'sheet': sheet_name,
                            'row': row[0].row,
                            'column': col_idx + 1
                        })
        
        return text_blocks
    
    def rebuild_document(self, original_path: str, translated_blocks: List[Dict[str, Any]], 
                        output_path: str):
        """重建Excel文档"""
        # 实现Excel重建逻辑
        pass

# 注册新解析器
DocumentParserFactory.register_parser(".xlsx", ExcelParser)
```

---

*本文档将随着功能发展持续更新*