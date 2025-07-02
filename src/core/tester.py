#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify Knowledge Base Recall Testing Tool - Enhanced Version 3.0

This module provides comprehensive testing capabilities for Dify knowledge base recall performance,
including batch testing, detailed analysis, and visualization of results.
"""

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import utilities from utils module
from ..utils import (
    setup_logger, get_logger, LoggerMixin,
    VisualizationGenerator, generate_visualization,
    save_results, ResultsManager,
    ConfigManager, load_config
)

# 导入必要的模块
import logging
# import matplotlib.pyplot as plt
import statistics
from dataclasses import dataclass

# 设置中文字体支持
# plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
# plt.rcParams['axes.unicode_minus'] = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dify_recall_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestConfig:
    """测试配置"""
    api_base_url: str
    api_key: str
    dataset_id: str
    top_k: int = 10
    delay_between_requests: float = 1.0
    score_threshold_enabled: bool = False
    score_threshold: float = 0.0
    reranking_enabled: bool = True
    reranking_provider: str = ""
    reranking_model: str = ""
    output_prefix: str = "recall_test"
    save_csv: bool = True
    save_detailed_json: bool = True
    include_document_content: bool = True
    # 新增配置参数
    search_method: str = "semantic_search"
    hybrid_search_weights: Dict[str, float] = None
    embedding_model: Dict[str, str] = None
    
    def __post_init__(self):
        """初始化后处理默认值"""
        if self.hybrid_search_weights is None:
            self.hybrid_search_weights = {"semantic_weight": 0.8, "keyword_weight": 0.2}
        if self.embedding_model is None:
            self.embedding_model = {"provider": "openai", "model": "embedding-3"}

@dataclass
class TestCase:
    """测试用例数据结构"""
    id: str
    query: str
    expected_docs: List[str] = None
    category: str = ""
    description: str = ""
    expected_answer: str = ""
    expected_score_threshold: float = 0.0

@dataclass
class RecallResult:
    """召回结果数据结构"""
    test_id: str
    query: str
    category: str
    documents: List[Dict[str, Any]]
    scores: List[float]
    response_time: float
    timestamp: str
    success: bool
    error_message: str = ""
    api_response_raw: Dict = None
    
    @property
    def status(self) -> str:
        """返回测试状态"""
        return 'success' if self.success else 'error'

class DifyClient(LoggerMixin):
    """
    Client for interacting with Dify API.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Dify client.
        
        Args:
            config: Configuration dictionary containing API settings
        """
        super().__init__()
        self.api_base_url = config['api_base_url'].rstrip('/')
        self.api_key = config['api_key']
        self.dataset_id = config['dataset_id']
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

class EnhancedDifyRecallTester(LoggerMixin):
    """增强版Dify知识库召回测试器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, config_file: Optional[str] = None):
        """
        初始化测试器
        
        Args:
            config: 配置字典
            config_file: 配置文件路径
        """
        super().__init__()
        
        # Load configuration
        if config is None:
            if config_file is None:
                # Try to find default config
                config_manager = ConfigManager()
                config = config_manager.load_config()
            else:
                config = load_config(config_file)
        
        self.config = config
        
        # Extract API settings
        self.api_base_url = config['api_base_url'].rstrip('/')
        self.api_key = config['api_key']
        self.dataset_id = config['dataset_id']
        
        # Extract test settings
        test_settings = config.get('test_settings', {})
        self.top_k = test_settings.get('top_k', 10)
        self.delay_between_requests = test_settings.get('delay_between_requests', 1.0)
        self.score_threshold_enabled = test_settings.get('score_threshold_enabled', False)
        self.score_threshold = test_settings.get('score_threshold', 0.0)
        self.reranking_enabled = test_settings.get('reranking_enabled', True)
        self.search_method = test_settings.get('search_method', 'semantic_search')
        self.reranking_model = test_settings.get('reranking_model', {
            "provider": "",
            "model": ""
        })
        self.hybrid_search_weights = test_settings.get('hybrid_search_weights', {
            "semantic_weight": 0.8,
            "keyword_weight": 0.2
        })
        self.embedding_model = test_settings.get('embedding_model', {
            "provider": "openai",
            "model": "embedding-3"
        })
        
        # Extract output settings
        output_settings = config.get('output_settings', {})
        self.output_dir = output_settings.get('output_dir', 'data/output')
        self.output_prefix = output_settings.get('output_prefix', 'recall_test')
        self.save_csv = output_settings.get('save_csv', True)
        self.save_detailed_json = output_settings.get('save_detailed_json', True)
        self.include_document_content = output_settings.get('include_document_content', True)
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        self.results_history = []
        
        # Initialize utility classes
        self.results_manager = ResultsManager(output_dir=self.output_dir)
        self.viz_generator = VisualizationGenerator()
        
        # Initialize Dify client
        self.client = DifyClient(config)
    
    def test_single_query(self, test_case: TestCase) -> RecallResult:
        """
        测试单个查询的召回效果
        
        Args:
            test_case: 测试用例
            
        Returns:
            RecallResult: 召回结果
        """
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            # 构建API请求
            url = f"{self.api_base_url.rstrip('/')}/v1/datasets/{self.dataset_id}/hit-testing"
            
            retrieval_model = {
                "search_method": self.search_method,
                "reranking_enable": self.reranking_enabled,
                "top_k": self.top_k,
                "score_threshold_enabled": self.score_threshold_enabled
            }
            
            # 添加混合检索权重配置
            if self.search_method == "hybrid_search" and self.hybrid_search_weights:
                retrieval_model["weights"] = self.hybrid_search_weights
            
            if self.reranking_enabled:
                retrieval_model["reranking_model"] = {
                    "reranking_provider_name": self.reranking_model.get("provider", "cohere"),
                    "reranking_model_name": self.reranking_model.get("model", "rerank-multilingual-v3.0")
                }
            
            if self.score_threshold_enabled:
                retrieval_model["score_threshold"] = self.score_threshold
            
            payload = {
                "query": test_case.query,
                "retrieval_model": retrieval_model
            }
            
            logger.info(f"发送查询请求: {test_case.id} - {test_case.query}")
            response = self.session.post(url, json=payload, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                documents = data.get('records', [])
                scores = [doc.get('score', 0.0) for doc in documents]
                
                logger.info(f"查询成功，返回 {len(documents)} 个文档，最高分数: {max(scores) if scores else 0:.3f}")
                
                return RecallResult(
                    test_id=test_case.id,
                    query=test_case.query,
                    category=test_case.category,
                    documents=documents,
                    scores=scores,
                    response_time=response_time,
                    timestamp=timestamp,
                    success=True,
                    api_response_raw=data if self.include_document_content else None
                )
            else:
                error_msg = f"API请求失败: {response.status_code} - {response.text}"
                logger.error(error_msg)
                
                return RecallResult(
                    test_id=test_case.id,
                    query=test_case.query,
                    category=test_case.category,
                    documents=[],
                    scores=[],
                    response_time=response_time,
                    timestamp=timestamp,
                    success=False,
                    error_message=error_msg
                )
                
        except Exception as e:
            error_msg = f"请求异常: {str(e)}"
            logger.error(error_msg)
            
            return RecallResult(
                test_id=test_case.id,
                query=test_case.query,
                category=test_case.category,
                documents=[],
                scores=[],
                response_time=time.time() - start_time,
                timestamp=timestamp,
                success=False,
                error_message=error_msg
            )
    
    def batch_test(self, test_cases: List[TestCase]) -> List[RecallResult]:
        """
        批量测试召回效果
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            List[RecallResult]: 测试结果列表
        """
        results = []
        total_cases = len(test_cases)
        
        logger.info(f"开始批量测试，共 {total_cases} 个测试用例")
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"执行测试 {i}/{total_cases}: {test_case.id}")
            
            result = self.test_single_query(test_case)
            results.append(result)
            
            # 添加延迟避免请求过于频繁
            if i < total_cases and self.delay_between_requests > 0:
                time.sleep(self.delay_between_requests)
        
        self.results_history.extend(results)
        logger.info(f"批量测试完成，成功 {sum(1 for r in results if r.success)} 个")
        return results
    
    def analyze_results(self, results: List[RecallResult]) -> Dict[str, Any]:
        """
        分析测试结果
        
        Args:
            results: 测试结果列表
            
        Returns:
            Dict: 分析统计结果
        """
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            return {"error": "没有成功的测试结果"}
        
        # 收集所有分数
        all_scores = []
        category_scores = {}
        
        for result in successful_results:
            all_scores.extend(result.scores)
            
            if result.category not in category_scores:
                category_scores[result.category] = []
            category_scores[result.category].extend(result.scores)
        
        # 计算统计指标
        analysis = {
            "总体统计": {
                "总测试数": len(results),
                "成功测试数": len(successful_results),
                "失败测试数": len(results) - len(successful_results),
                "成功率": len(successful_results) / len(results) * 100,
                "平均响应时间": statistics.mean([r.response_time for r in successful_results]),
                "总召回文档数": sum(len(r.documents) for r in successful_results)
            },
            "分数统计": {
                "总分数数量": len(all_scores),
                "最高分数": max(all_scores) if all_scores else 0,
                "最低分数": min(all_scores) if all_scores else 0,
                "平均分数": statistics.mean(all_scores) if all_scores else 0,
                "中位数分数": statistics.median(all_scores) if all_scores else 0,
                "标准差": statistics.stdev(all_scores) if len(all_scores) > 1 else 0
            },
            "分类统计": {}
        }
        
        # 按分类统计
        for category, scores in category_scores.items():
            if scores:
                analysis["分类统计"][category] = {
                    "测试数量": len([r for r in successful_results if r.category == category]),
                    "平均分数": statistics.mean(scores),
                    "最高分数": max(scores),
                    "最低分数": min(scores),
                    "文档数量": len(scores)
                }
        
        return analysis
    
    def save_results_to_csv(self, results: List[RecallResult], filename: str):
        """
        将测试结果保存到CSV文件
        """
        # 准备CSV数据
        csv_data = []
        for result in results:
            scores = result.scores if result.success else []
            row = {
                'test_id': result.test_id,
                'query': result.query,
                'category': result.category,
                'success': result.success,
                'response_time': round(result.response_time, 3),
                'timestamp': result.timestamp,
                'doc_count': len(result.documents),
                'max_score': max(scores) if scores else 0,
                'min_score': min(scores) if scores else 0,
                'avg_score': statistics.mean(scores) if scores else 0,
                'median_score': statistics.median(scores) if scores else 0,
                'scores_json': json.dumps(scores),
                'error_message': result.error_message
            }
            csv_data.append(row)
        
        # 使用结果管理器保存
        self.results_manager.save_csv(csv_data, filename)
        logger.info(f"CSV结果已保存到: {filename}")
    
    def save_detailed_results_to_json(self, results: List[RecallResult], filename: str):
        """
        将详细测试结果保存到JSON文件
        """
        output_data = []
        
        for result in results:
            result_dict = {
                'test_id': result.test_id,
                'query': result.query,
                'category': result.category,
                'success': result.success,
                'response_time': result.response_time,
                'timestamp': result.timestamp,
                'error_message': result.error_message,
                'documents': []
            }
            
            if result.success:
                for i, doc in enumerate(result.documents):
                    doc_info = {
                        'rank': i + 1,
                        'score': result.scores[i] if i < len(result.scores) else 0,
                        'content': doc.get('segment', {}).get('content', '') if self.include_document_content else '',
                        'document_name': doc.get('document', {}).get('name', ''),
                        'document_id': doc.get('document', {}).get('id', ''),
                        'segment_id': doc.get('segment', {}).get('id', ''),
                        'segment_position': doc.get('segment', {}).get('position', 0)
                    }
                    result_dict['documents'].append(doc_info)
            
            output_data.append(result_dict)
        
        # 使用结果管理器保存
        self.results_manager.save_json(output_data, filename)
        logger.info(f"详细JSON结果已保存到: {filename}")
    
    def generate_visualizations(self, output_dir: str = None) -> Dict[str, str]:
        """
        生成可视化图表
        
        Args:
            output_dir: 输出目录
            
        Returns:
            Dict[str, str]: 生成的图表文件路径
        """
        if not self.results_history:
            logger.warning("没有测试结果，无法生成可视化图表")
            return {}
        
        if output_dir is None:
            output_dir = self.output_dir
        
        try:
            # 使用可视化生成器
            visualizations = generate_visualization(self.results_history, output_dir)
            
            logger.info(f"生成了 {len(visualizations)} 个可视化图表")
            return visualizations
            
        except Exception as e:
            logger.error(f"生成可视化时出错: {e}")
            return {}

def load_config_from_file(config_file: str) -> TestConfig:
    """
    从JSON文件加载配置
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        TestConfig: 测试配置对象
    """
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    # 合并嵌套配置
    flat_config = {
        'api_base_url': config_data['api_base_url'],
        'api_key': config_data['api_key'],
        'dataset_id': config_data['dataset_id']
    }
    
    # 添加测试设置
    if 'test_settings' in config_data:
        test_settings = config_data['test_settings']
        
        # 处理基础设置
        for key in ['top_k', 'delay_between_requests', 'score_threshold_enabled', 
                   'score_threshold', 'reranking_enabled', 'search_method']:
            if key in test_settings:
                flat_config[key] = test_settings[key]
        
        # 处理嵌套的reranking_model配置
        if 'reranking_model' in test_settings:
            rerank_model = test_settings['reranking_model']
            flat_config['reranking_provider'] = rerank_model.get('provider', 'openai')
            flat_config['reranking_model'] = rerank_model.get('model', 'rerank-model')
        
        # 处理嵌套的hybrid_search_weights配置
        if 'hybrid_search_weights' in test_settings:
            flat_config['hybrid_search_weights'] = test_settings['hybrid_search_weights']
        
        # 处理嵌套的embedding_model配置
        if 'embedding_model' in test_settings:
            flat_config['embedding_model'] = test_settings['embedding_model']
    
    # 添加输出设置
    if 'output_settings' in config_data:
        flat_config.update(config_data['output_settings'])
    
    return TestConfig(**flat_config)

def load_test_cases_from_csv(file_path: str) -> List[TestCase]:
    """
    从CSV文件加载测试用例
    
    Args:
        file_path: CSV文件路径
        
    Returns:
        测试用例列表
    """
    test_cases = []
    logger = get_logger('load_test_cases')
    
    try:
        import csv
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for i, row in enumerate(reader, 1):
                test_case = TestCase(
                    id=row.get('id', str(i)),
                    query=row['query'],
                    expected_answer=row.get('expected_answer', ''),
                    category=row.get('category', 'default')
                )
                test_cases.append(test_case)
        
        logger.info(f"成功加载 {len(test_cases)} 个测试用例")
        return test_cases
        
    except Exception as e:
        logger.error(f"加载测试用例失败: {str(e)}")
        raise

def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Dify知识库召回测试工具')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--test-cases', type=str, default='tests/test_cases/sample.csv', help='测试用例文件路径')
    parser.add_argument('--output-dir', type=str, help='输出目录（覆盖配置文件设置）')
    parser.add_argument('--visualize', action='store_true', help='生成可视化图表')
    
    args = parser.parse_args()
    
    try:
        # 创建测试器（自动加载配置）
        tester = EnhancedDifyRecallTester(config_file=args.config)
        
        # 覆盖输出目录（如果指定）
        if args.output_dir:
            tester.output_dir = args.output_dir
            tester.results_manager = ResultsManager(output_dir=args.output_dir)
        
        # 加载测试用例
        test_cases = load_test_cases_from_csv(args.test_cases)
        
        # 运行测试
        print(f"开始测试 {len(test_cases)} 个用例...")
        results = tester.batch_test(test_cases)
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存CSV
        if tester.save_csv:
            csv_file = tester.save_results_csv(results)
            print(f"CSV结果已保存到: {csv_file}")
        
        # 保存详细JSON
        if tester.save_detailed_json:
            json_file = tester.save_results_json(results)
            print(f"JSON结果已保存到: {json_file}")
        
        # 生成可视化（如果需要）
        if args.visualize:
            tester.generate_visualizations()
        
        # 打印总结
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        print(f"\n测试完成!")
        print(f"总测试数: {total_tests}")
        print(f"成功测试数: {successful_tests}")
        print(f"成功率: {successful_tests/total_tests*100:.1f}%")
        print(f"结果已保存到: {tester.output_dir}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    main()