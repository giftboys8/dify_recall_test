#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify知识库召回测试工具 - 增强版
支持配置文件、批量测试、结果分析和可视化
"""

import requests
import json
import csv
import time
import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse
import os
from pathlib import Path
import statistics

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

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

class EnhancedDifyRecallTester:
    """增强版Dify知识库召回测试器"""
    
    def __init__(self, config: TestConfig):
        """
        初始化测试器
        
        Args:
            config: 测试配置
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json'
        })
        self.results_history = []
    
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
            url = f"{self.config.api_base_url.rstrip('/')}/v1/datasets/{self.config.dataset_id}/hit-testing"
            
            retrieval_model = {
                "search_method": self.config.search_method,
                "reranking_enable": self.config.reranking_enabled,
                "top_k": self.config.top_k,
                "score_threshold_enabled": self.config.score_threshold_enabled
            }
            
            # 添加混合检索权重配置
            if self.config.search_method == "hybrid_search" and self.config.hybrid_search_weights:
                retrieval_model["weights"] = self.config.hybrid_search_weights
            
            if self.config.reranking_enabled:
                retrieval_model["reranking_model"] = {
                    "reranking_provider_name": self.config.reranking_provider,
                    "reranking_model_name": self.config.reranking_model
                }
            
            if self.config.score_threshold_enabled:
                retrieval_model["score_threshold"] = self.config.score_threshold
            
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
                    api_response_raw=data if self.config.include_document_content else None
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
            if i < total_cases and self.config.delay_between_requests > 0:
                time.sleep(self.config.delay_between_requests)
        
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
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'test_id', 'query', 'category', 'success', 'response_time', 'timestamp',
                'doc_count', 'max_score', 'min_score', 'avg_score', 'median_score',
                'scores_json', 'error_message'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
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
                writer.writerow(row)
        
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
                        'content': doc.get('segment', {}).get('content', '') if self.config.include_document_content else '',
                        'document_name': doc.get('document', {}).get('name', ''),
                        'document_id': doc.get('document', {}).get('id', ''),
                        'segment_id': doc.get('segment', {}).get('id', ''),
                        'segment_position': doc.get('segment', {}).get('position', 0)
                    }
                    result_dict['documents'].append(doc_info)
            
            output_data.append(result_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"详细JSON结果已保存到: {filename}")
    
    def generate_visualization(self, results: List[RecallResult], output_dir: str):
        """
        生成可视化图表
        
        Args:
            results: 测试结果列表
            output_dir: 输出目录
        """
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            logger.warning("没有成功的测试结果，无法生成可视化图表")
            return
        
        # 创建输出目录
        Path(output_dir).mkdir(exist_ok=True)
        
        # 1. 分数分布直方图
        plt.figure(figsize=(12, 8))
        all_scores = [score for result in successful_results for score in result.scores]
        
        plt.subplot(2, 2, 1)
        plt.hist(all_scores, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        plt.title('召回分数分布')
        plt.xlabel('分数')
        plt.ylabel('频次')
        plt.grid(True, alpha=0.3)
        
        # 2. 按分类的平均分数
        plt.subplot(2, 2, 2)
        category_avg_scores = {}
        for result in successful_results:
            if result.category and result.scores:
                if result.category not in category_avg_scores:
                    category_avg_scores[result.category] = []
                category_avg_scores[result.category].extend(result.scores)
        
        categories = list(category_avg_scores.keys())
        avg_scores = [statistics.mean(scores) for scores in category_avg_scores.values()]
        
        if categories:
            plt.bar(categories, avg_scores, color='lightcoral')
            plt.title('各分类平均召回分数')
            plt.xlabel('分类')
            plt.ylabel('平均分数')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
        
        # 3. 响应时间分布
        plt.subplot(2, 2, 3)
        response_times = [r.response_time for r in successful_results]
        plt.hist(response_times, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
        plt.title('响应时间分布')
        plt.xlabel('响应时间 (秒)')
        plt.ylabel('频次')
        plt.grid(True, alpha=0.3)
        
        # 4. 召回文档数量分布
        plt.subplot(2, 2, 4)
        doc_counts = [len(r.documents) for r in successful_results]
        plt.hist(doc_counts, bins=range(0, max(doc_counts)+2), alpha=0.7, color='gold', edgecolor='black')
        plt.title('召回文档数量分布')
        plt.xlabel('文档数量')
        plt.ylabel('频次')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/recall_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"可视化图表已保存到: {output_dir}/recall_analysis.png")

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

def load_test_cases_from_csv(filename: str) -> List[TestCase]:
    """
    从CSV文件加载测试用例
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
                expected_score_threshold=float(row.get('expected_score_threshold', 0.0))
            )
            test_cases.append(test_case)
    
    logger.info(f"从 {filename} 加载了 {len(test_cases)} 个测试用例")
    return test_cases

def main():
    parser = argparse.ArgumentParser(description='Dify知识库召回测试工具 - 增强版')
    parser.add_argument('--config', help='配置文件路径 (JSON格式)')
    parser.add_argument('--api-url', help='Dify API基础URL')
    parser.add_argument('--api-key', help='API密钥')
    parser.add_argument('--dataset-id', help='知识库ID')
    parser.add_argument('--test-file', required=True, help='测试用例CSV文件路径')
    parser.add_argument('--output-dir', default='./results', help='输出目录')
    parser.add_argument('--generate-viz', action='store_true', help='生成可视化图表')
    
    args = parser.parse_args()
    
    # 加载配置
    if args.config and os.path.exists(args.config):
        config = load_config_from_file(args.config)
    else:
        # 使用命令行参数创建配置
        if not all([args.api_url, args.api_key, args.dataset_id]):
            logger.error("请提供配置文件或完整的API参数")
            return
        
        config = TestConfig(
            api_base_url=args.api_url,
            api_key=args.api_key,
            dataset_id=args.dataset_id
        )
    
    # 创建输出目录
    Path(args.output_dir).mkdir(exist_ok=True)
    
    # 初始化测试器
    tester = EnhancedDifyRecallTester(config)
    
    # 加载测试用例
    if not os.path.exists(args.test_file):
        logger.error(f"测试文件不存在: {args.test_file}")
        return
    
    test_cases = load_test_cases_from_csv(args.test_file)
    
    # 执行批量测试
    results = tester.batch_test(test_cases)
    
    # 分析结果
    analysis = tester.analyze_results(results)
    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if config.save_csv:
        csv_filename = f"{args.output_dir}/{config.output_prefix}_{timestamp}.csv"
        tester.save_results_to_csv(results, csv_filename)
    
    if config.save_detailed_json:
        json_filename = f"{args.output_dir}/{config.output_prefix}_{timestamp}_detailed.json"
        tester.save_detailed_results_to_json(results, json_filename)
    
    # 保存分析结果
    analysis_filename = f"{args.output_dir}/{config.output_prefix}_{timestamp}_analysis.json"
    with open(analysis_filename, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    # 生成可视化图表
    if args.generate_viz:
        tester.generate_visualization(results, args.output_dir)
    
    # 输出统计信息
    logger.info("\n=== 测试结果分析 ===")
    for key, value in analysis.items():
        logger.info(f"{key}: {json.dumps(value, ensure_ascii=False, indent=2)}")

if __name__ == '__main__':
    main()