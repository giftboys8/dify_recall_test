#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify知识库召回测试工具
用于批量测试Dify知识库的召回效果并获取score值
"""

import requests
import json
import csv
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import argparse
import os

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

class DifyKnowledgeBaseRecallTester:
    """Dify知识库召回测试器"""
    
    def __init__(self, api_base_url: str, api_key: str, dataset_id: str):
        """
        初始化测试器
        
        Args:
            api_base_url: Dify API基础URL
            api_key: API密钥
            dataset_id: 知识库ID
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.dataset_id = dataset_id
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
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
                
                logger.info(f"查询成功，返回 {len(documents)} 个文档")
                
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
        
        logger.info(f"开始批量测试，共 {total_cases} 个测试用例")
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"执行测试 {i}/{total_cases}: {test_case.id}")
            
            result = self.test_single_query(test_case.query, top_k)
            result.test_id = test_case.id
            results.append(result)
            
            # 添加延迟避免请求过于频繁
            if i < total_cases and delay > 0:
                time.sleep(delay)
        
        logger.info(f"批量测试完成，成功 {sum(1 for r in results if r.success)} 个")
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
        
        logger.info(f"结果已保存到: {filename}")
    
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
        
        logger.info(f"详细结果已保存到: {filename}")

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
                description=row.get('description', '')
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
    parser = argparse.ArgumentParser(description='Dify知识库召回测试工具')
    parser.add_argument('--api-url', required=True, help='Dify API基础URL')
    parser.add_argument('--api-key', required=True, help='API密钥')
    parser.add_argument('--dataset-id', required=True, help='知识库ID')
    parser.add_argument('--test-file', help='测试用例CSV文件路径')
    parser.add_argument('--top-k', type=int, default=10, help='返回文档数量')
    parser.add_argument('--delay', type=float, default=1.0, help='请求间隔时间（秒）')
    parser.add_argument('--output-prefix', default='recall_test', help='输出文件前缀')
    
    args = parser.parse_args()
    
    # 初始化测试器
    tester = DifyKnowledgeBaseRecallTester(
        api_base_url=args.api_url,
        api_key=args.api_key,
        dataset_id=args.dataset_id
    )
    
    # 加载测试用例
    if args.test_file and os.path.exists(args.test_file):
        test_cases = load_test_cases_from_csv(args.test_file)
    else:
        logger.warning("未指定测试文件或文件不存在，使用示例测试用例")
        test_cases = create_sample_test_cases()
    
    # 执行批量测试
    results = tester.batch_test(test_cases, args.top_k, args.delay)
    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f"{args.output_prefix}_{timestamp}.csv"
    json_filename = f"{args.output_prefix}_{timestamp}_detailed.json"
    
    tester.save_results_to_csv(results, csv_filename)
    tester.save_detailed_results_to_json(results, json_filename)
    
    # 输出统计信息
    successful_tests = [r for r in results if r.success]
    if successful_tests:
        all_scores = [score for result in successful_tests for score in result.scores]
        logger.info(f"测试统计:")
        logger.info(f"  总测试数: {len(results)}")
        logger.info(f"  成功数: {len(successful_tests)}")
        logger.info(f"  失败数: {len(results) - len(successful_tests)}")
        logger.info(f"  平均响应时间: {sum(r.response_time for r in successful_tests) / len(successful_tests):.3f}秒")
        if all_scores:
            logger.info(f"  分数统计: 最高={max(all_scores):.3f}, 最低={min(all_scores):.3f}, 平均={sum(all_scores)/len(all_scores):.3f}")

if __name__ == '__main__':
    main()