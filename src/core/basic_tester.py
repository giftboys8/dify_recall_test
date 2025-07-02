#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify Knowledge Base Recall Testing Tool - Basic Version

This script provides basic testing capabilities for Dify knowledge base recall performance.
It's a simplified version focused on core functionality.

Features:
- Batch testing with CSV input
- Configurable parameters (top_k, score thresholds, etc.)
- Detailed logging and result analysis
- CSV output with comprehensive metrics

Author: Assistant
Version: 3.0
Date: 2025-01-02
"""

import csv
import json
import os
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests

# Import utilities from utils module
from ..utils import (
    setup_logger, get_logger, LoggerMixin,
    ConfigManager, load_config
)

import logging
from dataclasses import dataclass
import argparse

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
class TestCase:
    """测试用例数据结构"""
    id: str
    query: str
    expected_docs: List[str] = None
    category: str = ""
    description: str = ""
    expected_answer: str = ""

@dataclass
class RecallResult:
    """召回结果数据结构"""
    test_id: str
    query: str
    documents: List[Dict[str, Any]]
    scores: List[float]
    response_time: float
    timestamp: str
    success: bool
    error_message: str = ""
    
    @property
    def status(self) -> str:
        """返回测试状态"""
        return 'success' if self.success else 'error'

class DifyRecallTester(LoggerMixin):
    """Dify知识库召回测试器"""
    
    def __init__(self, config: Optional[Dict] = None, config_file: Optional[str] = None):
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
                config_manager = ConfigManager()
                config = config_manager.load_config()
            else:
                config = load_config(config_file)
        
        self.config = config
        self.api_base_url = config['api_base_url'].rstrip('/')
        self.api_key = config['api_key']
        self.dataset_id = config['dataset_id']
        
        # Extract test settings
        test_settings = config.get('test_settings', {})
        self.top_k = test_settings.get('top_k', 10)
        
        # 设置请求头
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_single_query(self, query: str, top_k: int = 10) -> RecallResult:
        """
        测试单个查询的召回效果
        
        Args:
            query: 查询文本
            top_k: 返回的文档数量
            
        Returns:
            RecallResult: 召回结果
        """
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            # 构建API请求
            url = f"{self.api_base_url}/v1/datasets/{self.dataset_id}/hit-testing"
            payload = {
                "query": query,
                "retrieval_model": {
                    "search_method": "semantic_search",
                    "reranking_enable": True,
                    "reranking_model": {
                        "reranking_provider_name": "cohere",
                        "reranking_model_name": "rerank-multilingual-v3.0"
                    },
                    "top_k": top_k,
                    "score_threshold_enabled": False
                }
            }
            
            logger.info(f"发送查询请求: {query}")
            response = self.session.post(url, json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                documents = data.get('query', {}).get('records', [])
                scores = [doc.get('score', 0.0) for doc in documents]
                
                self.logger.info(f"查询成功，返回 {len(documents)} 个文档")
                
                return RecallResult(
                    test_id="",
                    query=query,
                    documents=documents,
                    scores=scores,
                    response_time=response_time,
                    timestamp=timestamp,
                    success=True
                )
            else:
                error_msg = f"API请求失败: {response.status_code} - {response.text}"
                logger.error(error_msg)
                
                return RecallResult(
                    test_id="",
                    query=query,
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
                test_id="",
                query=query,
                documents=[],
                scores=[],
                response_time=time.time() - start_time,
                timestamp=timestamp,
                success=False,
                error_message=error_msg
            )
    
    def batch_test(self, test_cases: List[TestCase], 
                   top_k: int = 10, 
                   delay: float = 1.0) -> List[RecallResult]:
        """
        批量测试召回效果
        
        Args:
            test_cases: 测试用例列表
            top_k: 每个查询返回的文档数量
            delay: 请求间隔时间（秒）
            
        Returns:
            List[RecallResult]: 测试结果列表
        """
        results = []
        total_cases = len(test_cases)
        
        self.logger.info(f"开始批量测试，共 {total_cases} 个测试用例")
        
        for i, test_case in enumerate(test_cases, 1):
            self.logger.info(f"执行测试 {i}/{total_cases}: {test_case.id}")
            
            result = self.test_single_query(test_case.query, top_k)
            result.test_id = test_case.id
            results.append(result)
            
            # 添加延迟避免请求过于频繁
            if i < total_cases and delay > 0:
                time.sleep(delay)
        
        self.logger.info(f"批量测试完成，成功 {sum(1 for r in results if r.success)} 个")
        return results
    
    def save_results_to_csv(self, results: List[RecallResult], filename: str):
        """
        将测试结果保存到CSV文件
        
        Args:
            results: 测试结果列表
            filename: 输出文件名
        """
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'test_id', 'query', 'success', 'response_time', 'timestamp',
                'doc_count', 'max_score', 'min_score', 'avg_score', 
                'scores', 'error_message'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                scores = result.scores if result.success else []
                row = {
                    'test_id': result.test_id,
                    'query': result.query,
                    'success': result.success,
                    'response_time': round(result.response_time, 3),
                    'timestamp': result.timestamp,
                    'doc_count': len(result.documents),
                    'max_score': max(scores) if scores else 0,
                    'min_score': min(scores) if scores else 0,
                    'avg_score': sum(scores) / len(scores) if scores else 0,
                    'scores': json.dumps(scores),
                    'error_message': result.error_message
                }
                writer.writerow(row)
        
        self.logger.info(f"结果已保存到: {filename}")
    
    def save_detailed_results_to_json(self, results: List[RecallResult], filename: str):
        """
        将详细测试结果保存到JSON文件
        
        Args:
            results: 测试结果列表
            filename: 输出文件名
        """
        output_data = []
        
        for result in results:
            result_dict = {
                'test_id': result.test_id,
                'query': result.query,
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
                        'content': doc.get('segment', {}).get('content', ''),
                        'document_name': doc.get('document', {}).get('name', ''),
                        'document_id': doc.get('document', {}).get('id', ''),
                        'segment_id': doc.get('segment', {}).get('id', '')
                    }
                    result_dict['documents'].append(doc_info)
            
            output_data.append(result_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"详细JSON结果已保存到: {filename}")

def load_test_cases_from_csv(filename: str) -> List[TestCase]:
    """
    从CSV文件加载测试用例
    
    CSV格式: id,query,category,description
    
    Args:
        filename: CSV文件路径
        
    Returns:
        List[TestCase]: 测试用例列表
    """
    test_cases = []
    
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            test_case = TestCase(
                id=row.get('id', ''),
                query=row.get('query', ''),
                category=row.get('category', ''),
                description=row.get('description', ''),
                expected_answer=row.get('expected_answer', '')
            )
            test_cases.append(test_case)
    
    logger.info(f"从 {filename} 加载了 {len(test_cases)} 个测试用例")
    return test_cases

def create_sample_test_cases() -> List[TestCase]:
    """
    创建示例测试用例
    
    Returns:
        List[TestCase]: 示例测试用例列表
    """
    return [
        TestCase("001", "什么是人工智能？", "基础概念", "AI基础概念查询"),
        TestCase("002", "机器学习的主要算法有哪些？", "技术细节", "ML算法查询"),
        TestCase("003", "深度学习和传统机器学习的区别", "对比分析", "技术对比查询"),
        TestCase("004", "如何选择合适的模型？", "实践指导", "模型选择指导"),
        TestCase("005", "数据预处理的步骤", "流程说明", "数据处理流程")
    ]

def main():
    parser = argparse.ArgumentParser(description='Dify知识库召回测试工具 - 基础版')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--test-file', required=True, help='测试用例CSV文件路径')
    parser.add_argument('--output-dir', default='./results', help='输出目录')
    parser.add_argument('--top-k', type=int, help='返回文档数量（覆盖配置文件）')
    parser.add_argument('--delay', type=float, default=1.0, help='请求间延迟（秒）')
    
    args = parser.parse_args()
    
    try:
        # 创建输出目录
        Path(args.output_dir).mkdir(exist_ok=True)
        
        # 初始化测试器
        tester = DifyRecallTester(config_file=args.config)
        
        # 覆盖top_k设置（如果指定）
        if args.top_k:
            tester.top_k = args.top_k
        
        # 加载测试用例
        test_cases = load_test_cases_from_csv(args.test_file)
        
        # 执行批量测试
        results = tester.batch_test(test_cases, top_k=tester.top_k, delay=args.delay)
        
        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"{args.output_dir}/recall_test_results_{timestamp}.csv"
        json_filename = f"{args.output_dir}/recall_test_detailed_{timestamp}.json"
        
        tester.save_results_to_csv(results, csv_filename)
        tester.save_detailed_results_to_json(results, json_filename)
        
        # 输出统计信息
        successful_tests = [r for r in results if r.success]
        failed_tests = [r for r in results if not r.success]
        
        print(f"\n=== 测试结果统计 ===")
        print(f"总测试数: {len(results)}")
        print(f"成功测试数: {len(successful_tests)}")
        print(f"失败测试数: {len(failed_tests)}")
        print(f"成功率: {len(successful_tests)/len(results)*100:.1f}%")
        
        if successful_tests:
            all_scores = []
            for result in successful_tests:
                all_scores.extend(result.scores)
            
            if all_scores:
                print(f"\n=== 分数统计 ===")
                print(f"最高分数: {max(all_scores):.4f}")
                print(f"最低分数: {min(all_scores):.4f}")
                print(f"平均分数: {statistics.mean(all_scores):.4f}")
                print(f"中位数分数: {statistics.median(all_scores):.4f}")
        
        print(f"\n结果已保存到:")
        print(f"CSV: {csv_filename}")
        print(f"JSON: {json_filename}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    main()