# 代码质量与可维护性指南

## 🎯 概述

本指南基于对知识库项目的深入分析，提供提升代码质量和可维护性的具体建议。涵盖错误处理、代码结构、性能优化、测试覆盖率和文档完善等多个方面。

## 🔧 已解决的问题

### PPT形状类型错误处理

**问题描述**：PPT转换时遇到未知形状类型导致"Shape instance of unrecognized shape type"错误

**解决方案**：在 `src/translation/ppt_parser.py` 中添加了异常处理机制

```python
# 修复前的代码
for shape in slide.shapes:
    if hasattr(shape, "text") and shape.text.strip():
        # 处理逻辑

# 修复后的代码
for shape in slide.shapes:
    try:
        if hasattr(shape, "text") and shape.text.strip():
            # 处理逻辑
    except Exception as e:
        self.logger.warning(f"跳过无法处理的形状: {e}")
        continue
```

**改进效果**：
- 对所有形状遍历操作添加 try-catch 块
- 记录警告日志但不中断处理流程
- 确保转换过程的鲁棒性

## 🚀 代码质量改进建议

### 1. 错误处理与日志记录

#### 当前状态评估
- ✅ 基本的异常处理已实现
- ✅ 日志记录系统已建立
- ⚠️ 部分模块缺乏统一的错误处理策略

#### 改进建议

**A. 统一异常处理策略**

创建自定义异常类层次结构：

```python
# src/utils/exceptions.py
class KnowledgeBaseError(Exception):
    """知识库项目基础异常类"""
    pass

class DocumentProcessingError(KnowledgeBaseError):
    """文档处理相关异常"""
    pass

class TranslationError(KnowledgeBaseError):
    """翻译相关异常"""
    pass

class DatabaseError(KnowledgeBaseError):
    """数据库操作异常"""
    pass

class ConfigurationError(KnowledgeBaseError):
    """配置相关异常"""
    pass
```

**B. 增强日志记录**

实现结构化日志记录：

```python
# src/utils/logger.py
import structlog
import logging
from typing import Dict, Any

def setup_structured_logging():
    """设置结构化日志记录"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

class ContextLogger:
    """带上下文的日志记录器"""
    
    def __init__(self, name: str):
        self.logger = structlog.get_logger(name)
    
    def log_operation(self, operation: str, **context: Any):
        """记录操作日志"""
        self.logger.info("Operation started", operation=operation, **context)
    
    def log_performance(self, operation: str, duration: float, **metrics: Any):
        """记录性能指标"""
        self.logger.info(
            "Performance metrics",
            operation=operation,
            duration_seconds=duration,
            **metrics
        )
```

### 2. 代码结构优化

#### 当前状态评估
- ✅ 模块化设计良好
- ✅ 职责分离清晰
- ⚠️ 部分类过于庞大，可进一步拆分

#### 改进建议

**A. 单一职责原则应用**

重构PPTParser类：

```python
# src/translation/ppt/reader.py
class PPTReader:
    """负责读取PPT文件"""
    
    def read_file(self, file_path: str) -> Presentation:
        """读取PPT文件"""
        pass

# src/translation/ppt/text_extractor.py
class PPTTextExtractor:
    """负责文本提取"""
    
    def extract_text(self, presentation: Presentation) -> List[str]:
        """提取文本内容"""
        pass

# src/translation/ppt/converter.py
class PPTToPDFConverter:
    """负责PDF转换"""
    
    def convert_to_pdf(self, ppt_path: str, pdf_path: str) -> bool:
        """转换为PDF"""
        pass

# src/translation/ppt/shape_handler.py
class PPTShapeHandler:
    """负责形状处理"""
    
    def process_shapes(self, slide: Slide) -> List[Dict]:
        """处理幻灯片形状"""
        pass
```

**B. 工厂模式应用**

实现文档解析器工厂：

```python
# src/translation/factory.py
from abc import ABC, abstractmethod
from typing import Dict, Type

class DocumentParser(ABC):
    """文档解析器抽象基类"""
    
    @abstractmethod
    def parse(self, file_path: str) -> Dict:
        """解析文档"""
        pass

class DocumentParserFactory:
    """文档解析器工厂"""
    
    _parsers: Dict[str, Type[DocumentParser]] = {
        '.pdf': PDFParser,
        '.ppt': PPTParser,
        '.pptx': PPTParser,
        '.txt': TextParser,
        '.docx': WordParser
    }
    
    @classmethod
    def create_parser(cls, file_extension: str) -> DocumentParser:
        """创建对应的解析器"""
        parser_class = cls._parsers.get(file_extension.lower())
        if not parser_class:
            raise ValueError(f"不支持的文件类型: {file_extension}")
        return parser_class()
    
    @classmethod
    def register_parser(cls, extension: str, parser_class: Type[DocumentParser]):
        """注册新的解析器"""
        cls._parsers[extension] = parser_class
```

### 3. 性能优化

#### 当前状态评估
- ✅ 基本的文件处理功能正常
- ⚠️ 大文件处理可能存在内存压力
- ⚠️ 缺乏缓存机制

#### 改进建议

**A. 内存优化**

实现流式处理：

```python
# src/utils/stream_processor.py
from typing import Iterator, Generator
import mmap

class StreamProcessor:
    """流式文档处理器"""
    
    @staticmethod
    def process_large_file(file_path: str, chunk_size: int = 8192) -> Generator[bytes, None, None]:
        """使用生成器逐块处理大文件"""
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    @staticmethod
    def memory_mapped_read(file_path: str) -> Iterator[str]:
        """使用内存映射读取大文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                for line in iter(mm.readline, b""):
                    yield line.decode('utf-8')
```

**B. 缓存策略**

实现多层缓存系统：

```python
# src/utils/cache.py
from functools import lru_cache, wraps
from cachetools import TTLCache, LRUCache
import hashlib
import pickle
from typing import Any, Callable

class DocumentCache:
    """文档缓存管理器"""
    
    def __init__(self):
        self.memory_cache = TTLCache(maxsize=100, ttl=3600)  # 1小时TTL
        self.lru_cache = LRUCache(maxsize=50)
    
    def get_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def cache_result(self, key: str, value: Any, ttl: int = 3600):
        """缓存结果"""
        self.memory_cache[key] = value
    
    def get_cached_result(self, key: str) -> Any:
        """获取缓存结果"""
        return self.memory_cache.get(key)

def cached_document_operation(ttl: int = 3600):
    """文档操作缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        cache = TTLCache(maxsize=128, ttl=ttl)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 创建缓存键
            cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # 检查缓存
            if cache_key in cache:
                return cache[cache_key]
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache[cache_key] = result
            return result
        
        return wrapper
    return decorator
```

**C. 异步处理**

实现异步文档处理：

```python
# src/utils/async_processor.py
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Callable, Any

class AsyncDocumentProcessor:
    """异步文档处理器"""
    
    def __init__(self, max_workers: int = 4):
        self.thread_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=max_workers)
    
    async def process_document_async(self, file_path: str, processor_func: Callable) -> Any:
        """异步处理单个文档"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.thread_executor, processor_func, file_path
        )
    
    async def process_documents_batch(self, file_paths: List[str], processor_func: Callable) -> List[Any]:
        """批量异步处理文档"""
        tasks = [
            self.process_document_async(file_path, processor_func)
            for file_path in file_paths
        ]
        return await asyncio.gather(*tasks)
    
    async def process_with_progress(self, file_paths: List[str], processor_func: Callable, 
                                  progress_callback: Callable = None) -> List[Any]:
        """带进度回调的批量处理"""
        results = []
        total = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            result = await self.process_document_async(file_path, processor_func)
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, total, file_path)
        
        return results
    
    def __del__(self):
        """清理资源"""
        self.thread_executor.shutdown(wait=True)
        self.process_executor.shutdown(wait=True)
```

### 4. 测试覆盖率提升

#### 当前状态评估
- ✅ 基本的功能测试存在
- ⚠️ 缺乏系统性的单元测试
- ⚠️ 缺乏集成测试

#### 改进建议

**A. 单元测试框架**

```python
# tests/unit/test_ppt_parser.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.translation.ppt_parser import PPTParser
from src.utils.exceptions import DocumentProcessingError

class TestPPTParser:
    """PPT解析器单元测试"""
    
    def setup_method(self):
        """测试前置设置"""
        self.parser = PPTParser()
        self.sample_ppt_path = "tests/fixtures/sample.pptx"
    
    def test_convert_ppt_to_pdf_success(self):
        """测试成功转换PPT到PDF"""
        with patch('src.translation.ppt_parser.Presentation') as mock_presentation:
            mock_pres = MagicMock()
            mock_presentation.return_value = mock_pres
            
            result = self.parser.convert_ppt_to_pdf(self.sample_ppt_path, "output.pdf")
            
            assert result is True
            mock_pres.save.assert_called_once()
    
    def test_convert_ppt_to_pdf_invalid_file(self):
        """测试无效文件处理"""
        with pytest.raises(DocumentProcessingError):
            self.parser.convert_ppt_to_pdf("nonexistent.ppt", "output.pdf")
    
    @patch('src.translation.ppt_parser.Presentation')
    def test_handle_unknown_shape_type(self, mock_presentation):
        """测试未知形状类型处理"""
        # 模拟包含未知形状的幻灯片
        mock_slide = MagicMock()
        mock_shape = MagicMock()
        mock_shape.text = "测试文本"
        
        # 模拟形状访问时抛出异常
        mock_shape.__getattribute__.side_effect = Exception("Unknown shape type")
        mock_slide.shapes = [mock_shape]
        
        mock_pres = MagicMock()
        mock_pres.slides = [mock_slide]
        mock_presentation.return_value = mock_pres
        
        # 应该能够处理异常而不崩溃
        result = self.parser.extract_text(self.sample_ppt_path)
        assert isinstance(result, list)
    
    def test_extract_text_empty_presentation(self):
        """测试空演示文稿处理"""
        with patch('src.translation.ppt_parser.Presentation') as mock_presentation:
            mock_pres = MagicMock()
            mock_pres.slides = []
            mock_presentation.return_value = mock_pres
            
            result = self.parser.extract_text(self.sample_ppt_path)
            assert result == []
    
    @pytest.mark.parametrize("file_extension", [".ppt", ".pptx"])
    def test_supported_file_extensions(self, file_extension):
        """测试支持的文件扩展名"""
        assert self.parser.supports_extension(file_extension)
    
    def test_unsupported_file_extension(self):
        """测试不支持的文件扩展名"""
        assert not self.parser.supports_extension(".txt")
```

**B. 集成测试**

```python
# tests/integration/test_document_workflow.py
import pytest
import tempfile
import os
from pathlib import Path

class TestDocumentWorkflow:
    """文档处理工作流集成测试"""
    
    def setup_method(self):
        """测试前置设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files_dir = Path("tests/fixtures")
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_full_document_processing_pipeline(self):
        """测试完整的文档处理流程"""
        # 准备测试文件
        input_file = self.test_files_dir / "sample.pptx"
        output_file = Path(self.temp_dir) / "translated.pdf"
        
        # 执行完整流程
        from src.translation.processor import DocumentProcessor
        processor = DocumentProcessor()
        
        result = processor.process_document(
            input_path=str(input_file),
            output_path=str(output_file),
            source_lang="zh",
            target_lang="en"
        )
        
        # 验证结果
        assert result.success is True
        assert output_file.exists()
        assert output_file.stat().st_size > 0
    
    def test_batch_processing(self):
        """测试批量处理"""
        input_files = [
            self.test_files_dir / "sample1.pptx",
            self.test_files_dir / "sample2.pdf"
        ]
        
        from src.translation.processor import BatchProcessor
        processor = BatchProcessor()
        
        results = processor.process_batch(
            input_files=[str(f) for f in input_files],
            output_dir=self.temp_dir,
            source_lang="zh",
            target_lang="en"
        )
        
        assert len(results) == len(input_files)
        assert all(r.success for r in results)
    
    def test_error_recovery(self):
        """测试错误恢复机制"""
        # 使用损坏的文件测试错误恢复
        corrupted_file = Path(self.temp_dir) / "corrupted.pptx"
        corrupted_file.write_bytes(b"invalid content")
        
        from src.translation.processor import DocumentProcessor
        processor = DocumentProcessor()
        
        result = processor.process_document(
            input_path=str(corrupted_file),
            output_path=str(Path(self.temp_dir) / "output.pdf"),
            source_lang="zh",
            target_lang="en"
        )
        
        # 应该优雅地处理错误
        assert result.success is False
        assert result.error_message is not None
```

**C. 性能测试**

```python
# tests/performance/test_performance.py
import pytest
import time
from pathlib import Path

class TestPerformance:
    """性能测试"""
    
    @pytest.mark.performance
    def test_large_file_processing_time(self):
        """测试大文件处理时间"""
        large_file = Path("tests/fixtures/large_presentation.pptx")
        
        from src.translation.ppt_parser import PPTParser
        parser = PPTParser()
        
        start_time = time.time()
        result = parser.extract_text(str(large_file))
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # 大文件处理应该在合理时间内完成（例如30秒）
        assert processing_time < 30.0
        assert len(result) > 0
    
    @pytest.mark.performance
    def test_memory_usage(self):
        """测试内存使用情况"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 处理多个文件
        from src.translation.processor import BatchProcessor
        processor = BatchProcessor()
        
        files = [f"tests/fixtures/sample{i}.pptx" for i in range(10)]
        processor.process_batch(files, "/tmp/output", "zh", "en")
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 内存增长应该在合理范围内（例如100MB）
        assert memory_increase < 100 * 1024 * 1024
```

## 📋 实施计划

### 阶段1：基础改进（1-2周）
1. 实施统一异常处理策略
2. 增强日志记录系统
3. 添加基础单元测试

### 阶段2：结构优化（2-3周）
1. 重构大型类，应用单一职责原则
2. 实施工厂模式
3. 添加集成测试

### 阶段3：性能优化（2-3周）
1. 实施缓存策略
2. 添加异步处理支持
3. 优化内存使用

### 阶段4：测试完善（1-2周）
1. 提高测试覆盖率到80%以上
2. 添加性能测试
3. 完善文档

## 📊 质量指标

### 代码质量指标
- **测试覆盖率**：目标 > 80%
- **代码复杂度**：单个函数圈复杂度 < 10
- **代码重复率**：< 5%
- **文档覆盖率**：公共API 100%

### 性能指标
- **响应时间**：API响应 < 2秒
- **内存使用**：处理大文件内存增长 < 100MB
- **并发处理**：支持至少10个并发请求

### 可维护性指标
- **模块耦合度**：低耦合
- **代码可读性**：遵循PEP 8
- **错误处理**：100%覆盖关键路径

---

*本指南将根据项目发展持续更新和完善*