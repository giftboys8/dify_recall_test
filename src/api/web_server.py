#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify Knowledge Base Recall Testing Tool - Web Interface

This module provides a Flask-based web interface for the Dify KB recall testing tool.

Author: Assistant
Version: 3.0
Date: 2025-01-02
"""

import json
import os
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import asdict

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

# Import the testing modules and utilities
try:
    from ..core.tester import EnhancedDifyRecallTester, TestCase, RecallResult, load_test_cases_from_csv
    from ..core.basic_tester import DifyRecallTester
    from ..utils import setup_logger, get_logger, ConfigManager, load_config
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.tester import EnhancedDifyRecallTester, TestCase, RecallResult, load_test_cases_from_csv
    from core.basic_tester import DifyRecallTester
    from utils import setup_logger, get_logger, ConfigManager, load_config


class WebInterface:
    """Web interface for Dify KB recall testing tool."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize web interface."""
        setup_logger()
        self.logger = get_logger(self.__class__.__name__)
        
        # Load configuration
        self.config_manager = ConfigManager()
        if config_path:
            self.config = load_config(config_path)
        else:
            # Try to load from default config.json file
            try:
                self.config = load_config('config.json')
                # Convert config format to web interface format
                if 'api_base_url' in self.config:
                    # Convert from tester format to web format
                    web_config = {
                        'api': {
                            'base_url': self.config.get('api_base_url', ''),
                            'api_key': self.config.get('api_key', ''),
                            'dataset_id': self.config.get('dataset_id', '')
                        },
                        'testing': self.config.get('test_settings', {
                            'top_k': 10,
                            'delay_between_requests': 1.0,
                            'score_threshold_enabled': False,
                            'score_threshold': 0.0,
                            'reranking_enabled': True
                        }),
                        'output': self.config.get('output_settings', {
                            'output_dir': 'data/output',
                            'save_csv': True,
                            'save_detailed_json': True
                        })
                    }
                    self.config = web_config
                self.logger.info("Loaded configuration from config.json")
            except Exception as e:
                self.logger.warning(f"Could not load config.json: {e}, using default config")
                # Create a minimal default config for web interface
                self.config = {
                    'api': {
                        'base_url': '',
                        'api_key': '',
                        'dataset_id': ''
                    },
                    'testing': {
                        'top_k': 10,
                        'delay_between_requests': 1.0,
                        'score_threshold_enabled': False,
                        'score_threshold': 0.0,
                        'reranking_enabled': True
                    },
                    'output': {
                        'output_dir': 'data/output',
                        'save_csv': True,
                        'save_detailed_json': True
                    }
                }
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Setup routes
        self._setup_routes()
        
        # Test results storage
        self.test_results = []
        self.test_cases = []
        
        self.logger.info("Web interface initialized")
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main page."""
            return render_template('index.html')
        
        @self.app.route('/api/config', methods=['GET', 'POST'])
        def config_api():
            """Configuration API."""
            if request.method == 'GET':
                # Return current config (without sensitive data)
                safe_config = {
                    'api': {
                        'base_url': self.config.get('api', {}).get('base_url', ''),
                        'dataset_id': self.config.get('api', {}).get('dataset_id', '')
                    },
                    'testing': self.config.get('testing', {}),
                    'output': self.config.get('output', {})
                }
                return jsonify(safe_config)
            
            elif request.method == 'POST':
                # Update config
                try:
                    new_config = request.json
                    self.config.update(new_config)
                    return jsonify({'success': True, 'message': 'Configuration updated'})
                except Exception as e:
                    return jsonify({'success': False, 'error': str(e)}), 400
        
        @self.app.route('/api/test-cases', methods=['GET', 'POST'])
        def test_cases_api():
            """Test cases API."""
            if request.method == 'GET':
                return jsonify([
                    {
                        'id': tc.id,
                        'query': tc.query,
                        'expected_answer': tc.expected_answer,
                        'category': tc.category
                    } for tc in self.test_cases
                ])
            
            elif request.method == 'POST':
                try:
                    data = request.json
                    if 'file_content' in data:
                        # Load from CSV content
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                            f.write(data['file_content'])
                            temp_path = f.name
                        
                        self.test_cases = load_test_cases_from_csv(temp_path)
                        os.unlink(temp_path)
                        
                        return jsonify({
                            'success': True,
                            'message': f'Loaded {len(self.test_cases)} test cases',
                            'count': len(self.test_cases)
                        })
                    
                    elif 'test_case' in data:
                        # Add single test case
                        tc_data = data['test_case']
                        test_case = TestCase(
                            id=tc_data['id'],
                            query=tc_data['query'],
                            expected_answer=tc_data.get('expected_answer', ''),
                            category=tc_data.get('category', '')
                        )
                        self.test_cases.append(test_case)
                        
                        return jsonify({
                            'success': True,
                            'message': 'Test case added',
                            'count': len(self.test_cases)
                        })
                    
                    else:
                        return jsonify({'success': False, 'error': 'Invalid request data'}), 400
                
                except Exception as e:
                    return jsonify({'success': False, 'error': str(e)}), 400
        
        @self.app.route('/api/test-cases/clear', methods=['POST'])
        def clear_test_cases():
            """Clear all test cases."""
            self.test_cases = []
            return jsonify({'success': True, 'message': 'Test cases cleared'})
        
        @self.app.route('/api/run-test', methods=['POST'])
        def run_test():
            """Run tests API."""
            try:
                if not self.test_cases:
                    return jsonify({'success': False, 'error': 'No test cases available'}), 400
                
                # Validate config
                api_config = self.config.get('api', {})
                if not all(key in api_config for key in ['base_url', 'api_key', 'dataset_id']):
                    return jsonify({'success': False, 'error': 'Incomplete API configuration'}), 400
                
                # Initialize tester with properly formatted config
                # Convert web config format to tester config format
                tester_config = {
                    'api_base_url': api_config['base_url'],
                    'api_key': api_config['api_key'],
                    'dataset_id': api_config['dataset_id'],
                    'test_settings': self.config.get('testing', {}),
                    'output_settings': self.config.get('output', {})
                }
                tester = EnhancedDifyRecallTester(tester_config)
                
                # Run tests
                self.test_results = tester.batch_test(self.test_cases)
                
                # Calculate summary
                successful_tests = [r for r in self.test_results if r.status == 'success']
                summary = {
                    'total': len(self.test_results),
                    'successful': len(successful_tests),
                    'failed': len(self.test_results) - len(successful_tests),
                    'success_rate': len(successful_tests) / len(self.test_results) * 100 if self.test_results else 0
                }
                
                return jsonify({
                    'success': True,
                    'message': 'Tests completed',
                    'summary': summary
                })
            
            except Exception as e:
                self.logger.error(f"Test execution failed: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/results', methods=['GET'])
        def get_results():
            """Get test results."""
            if not self.test_results:
                return jsonify({'results': [], 'summary': {}})
            
            # Convert results to JSON-serializable format
            results_data = []
            for result in self.test_results:
                result_dict = {
                    'test_id': result.test_id,
                    'query': result.query,
                    'category': result.category,
                    'status': result.status,
                    'documents_count': len(result.documents),
                    'response_time': result.response_time,
                    'timestamp': result.timestamp,
                    'error_message': result.error_message
                }
                
                # Add score information if available
                if hasattr(result, 'scores') and result.scores:
                    result_dict.update({
                        'max_score': max(result.scores),
                        'min_score': min(result.scores),
                        'avg_score': sum(result.scores) / len(result.scores)
                    })
                
                results_data.append(result_dict)
            
            # Calculate summary
            successful_results = [r for r in self.test_results if r.status == 'success']
            summary = {
                'total': len(self.test_results),
                'successful': len(successful_results),
                'failed': len(self.test_results) - len(successful_results),
                'success_rate': len(successful_results) / len(self.test_results) * 100 if self.test_results else 0
            }
            
            if successful_results:
                avg_response_time = sum(r.response_time for r in successful_results) / len(successful_results)
                summary['avg_response_time'] = avg_response_time
            
            return jsonify({
                'results': results_data,
                'summary': summary
            })
        
        @self.app.route('/api/results/clear', methods=['POST'])
        def clear_results():
            """Clear test results."""
            self.test_results = []
            return jsonify({'success': True, 'message': 'Results cleared'})
        
        @self.app.route('/api/export/<format_type>')
        def export_results(format_type):
            """Export results in specified format."""
            if not self.test_results:
                return jsonify({'success': False, 'error': 'No results to export'}), 400
            
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # Convert RecallResult objects to dictionaries for serialization
                results_data = []
                for result in self.test_results:
                    if hasattr(result, '__dict__'):
                        # Convert RecallResult object to dictionary
                        result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
                        results_data.append(result_dict)
                    else:
                        # Already a dictionary
                        results_data.append(result)
                
                if format_type == 'csv':
                    # Create temporary CSV file
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                        # Use results manager to save CSV
                        from ..utils import ResultsManager
                        results_manager = ResultsManager()
                        csv_path = results_manager.save_csv(results_data, self.test_cases, f.name)
                        
                        return send_file(
                            csv_path,
                            as_attachment=True,
                            download_name=f'recall_test_results_{timestamp}.csv',
                            mimetype='text/csv'
                        )
                
                elif format_type == 'json':
                    # Create temporary JSON file
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        from ..utils import ResultsManager
                        results_manager = ResultsManager()
                        json_path = results_manager.save_json(results_data, self.test_cases, f.name)
                        
                        return send_file(
                            json_path,
                            as_attachment=True,
                            download_name=f'recall_test_results_{timestamp}.json',
                            mimetype='application/json'
                        )
                
                else:
                    return jsonify({'success': False, 'error': 'Unsupported format'}), 400
            
            except Exception as e:
                self.logger.error(f"Export failed: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
    
    def run(self, host='127.0.0.1', port=8080, debug=False):
        """Run the web server."""
        self.logger.info(f"Starting web server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def create_app(config_path: Optional[str] = None) -> Flask:
    """Create Flask app instance."""
    web_interface = WebInterface(config_path)
    return web_interface.app


if __name__ == '__main__':
    # For direct execution
    web_interface = WebInterface()
    web_interface.run(debug=True)