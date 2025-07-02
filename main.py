#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify KB Recall Testing Tool - Main Entry Point

This is the main entry point for the Dify Knowledge Base recall testing tool.
It provides a unified interface for running enhanced tests, quick setup, and web interface.

Usage:
    python main.py enhanced --config config/default.json --test-cases tests/test_cases/sample.csv
    python main.py basic --config config/default.json --test-file tests/test_cases/sample.csv
    python main.py quick-start
    python main.py web --port 8080
    python main.py config --create

Author: Assistant
Version: 3.0
Date: 2025-01-02
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent
src_path = current_dir / 'src'
sys.path.insert(0, str(src_path))

from src.core.tester import EnhancedDifyRecallTester, load_test_cases_from_csv
from src.core.basic_tester import DifyRecallTester
from src.api.web_server import WebInterface
from src.utils import setup_logger, get_logger, ConfigManager, create_default_config

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Dify KB Recall Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s enhanced --config config/default.json --test-cases tests/test_cases/sample.csv
  %(prog)s basic --config config/default.json --test-file tests/test_cases/sample.csv
  %(prog)s quick-start
  %(prog)s web --port 8080
  %(prog)s config --create
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Enhanced test command
    enhanced_parser = subparsers.add_parser('enhanced', help='Run enhanced recall testing')
    enhanced_parser.add_argument('--config', type=str, help='Configuration file path')
    enhanced_parser.add_argument('--test-cases', type=str, default='tests/test_cases/sample.csv', help='Test cases file path')
    enhanced_parser.add_argument('--output-dir', type=str, help='Output directory (overrides config)')
    enhanced_parser.add_argument('--visualize', action='store_true', help='Generate visualization charts')
    
    # Basic test command
    basic_parser = subparsers.add_parser('basic', help='Run basic recall testing')
    basic_parser.add_argument('--config', type=str, help='Configuration file path')
    basic_parser.add_argument('--test-file', type=str, required=True, help='Test cases CSV file path')
    basic_parser.add_argument('--output-dir', type=str, default='./results', help='Output directory')
    basic_parser.add_argument('--top-k', type=int, help='Number of documents to return (overrides config)')
    basic_parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests (seconds)')
    
    # Configuration management command
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_parser.add_argument('--create', action='store_true', help='Create default configuration template')
    config_parser.add_argument('--output-dir', type=str, default='config', help='Output directory for config files')
    
    # Quick start command
    quick_parser = subparsers.add_parser('quick-start', help='Quick setup and test')
    quick_parser.add_argument('--config-template', action='store_true', help='Create configuration template')
    
    # Web interface command
    web_parser = subparsers.add_parser('web', help='Start web interface')
    web_parser.add_argument('--port', type=int, default=8080, help='Port to run web server')
    web_parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind web server')
    web_parser.add_argument('--config', type=str, help='Configuration file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'enhanced':
            return run_enhanced_test(args)
        elif args.command == 'basic':
            return run_basic_test(args)
        elif args.command == 'config':
            return run_config_management(args)
        elif args.command == 'quick-start':
            return run_quick_start(args)
        elif args.command == 'web':
            return run_web_interface(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

def run_enhanced_test(args):
    """Run enhanced testing workflow."""
    setup_logger()
    logger = get_logger(__name__)
    
    try:
        # Initialize tester with config
        if args.config:
            tester = EnhancedDifyRecallTester(config_path=args.config)
        else:
            # Try to find default config
            default_configs = ['config/default.json', 'config.json', 'default.json']
            config_path = None
            for path in default_configs:
                if os.path.exists(path):
                    config_path = path
                    break
            
            if config_path:
                tester = EnhancedDifyRecallTester(config_path=config_path)
            else:
                logger.error("No configuration file found. Please specify --config or create config/default.json")
                return 1
        
        # Override output directory if specified
        if args.output_dir:
            tester.output_dir = args.output_dir
            os.makedirs(args.output_dir, exist_ok=True)
        
        # Load test cases
        logger.info(f"Loading test cases from: {args.test_cases}")
        test_cases = load_test_cases_from_csv(args.test_cases)
        
        if not test_cases:
            logger.error("No test cases loaded")
            return 1
        
        logger.info(f"Loaded {len(test_cases)} test cases")
        
        # Run batch testing
        logger.info("Starting batch testing...")
        results = tester.batch_test(test_cases)
        
        # Save results
        logger.info("Saving results...")
        csv_file = tester.save_results_csv(results, test_cases)
        json_file = tester.save_results_json(results, test_cases)
        
        logger.info(f"Results saved to: {csv_file}, {json_file}")
        
        # Generate visualizations if requested
        if args.visualize:
            logger.info("Generating visualizations...")
            tester.generate_visualizations(results, test_cases)
        
        # Print summary
        total_tests = len(results)
        logger.info(f"Testing completed: {total_tests} queries processed")
        
        return 0
        
    except Exception as e:
        logger.error(f"Enhanced testing failed: {e}")
        return 1


def run_basic_test(args):
    """Run basic testing workflow."""
    setup_logger()
    logger = get_logger(__name__)
    
    try:
        # Initialize basic tester
        if args.config:
            tester = DifyRecallTester(config_path=args.config)
        else:
            # Try to find default config
            default_configs = ['config/default.json', 'config.json', 'default.json']
            config_path = None
            for path in default_configs:
                if os.path.exists(path):
                    config_path = path
                    break
            
            if config_path:
                tester = DifyRecallTester(config_path=config_path)
            else:
                logger.error("No configuration file found. Please specify --config or create config/default.json")
                return 1
        
        # Override top_k if specified
        if args.top_k:
            tester.top_k = args.top_k
        
        # Create output directory
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Load and run tests
        logger.info(f"Loading test cases from: {args.test_file}")
        results = tester.batch_test(args.test_file, delay=args.delay)
        
        # Save results
        csv_file = os.path.join(args.output_dir, f"recall_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        json_file = os.path.join(args.output_dir, f"detailed_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        tester.save_results_to_csv(results, csv_file)
        tester.save_detailed_results_to_json(results, json_file)
        
        logger.info(f"Results saved to: {csv_file}, {json_file}")
        
        # Print summary statistics
        if results:
            total_tests = len(results)
            avg_score = sum(r['relevance_score'] for r in results) / total_tests
            logger.info(f"Testing completed: {total_tests} queries, average relevance: {avg_score:.2f}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Basic testing failed: {e}")
        return 1


def run_config_management(args):
    """Run configuration management."""
    if args.create:
        try:
            os.makedirs(args.output_dir, exist_ok=True)
            config_path = os.path.join(args.output_dir, 'default.json')
            
            success = create_default_config(config_path)
            if success:
                print(f"✓ Default configuration created at: {config_path}")
                print("\nPlease update the configuration with your Dify API details:")
                print("  - api_base_url: Your Dify API base URL")
                print("  - api_key: Your Dify API key")
                print("  - dataset_id: Your dataset ID")
                return 0
            else:
                print(f"✗ Failed to create configuration at: {config_path}")
                return 1
        except Exception as e:
            print(f"Error creating configuration: {e}")
            return 1
    else:
        print("No configuration action specified. Use --create to create default config.")
        return 1


def run_quick_start(args):
    """Run quick start workflow."""
    print("Quick Start - Setting up Dify KB Recall Testing Tool")
    print("1. Creating default configuration...")
    
    # Create default config
    os.makedirs('config', exist_ok=True)
    config_path = "config/default.json"
    
    if args.config_template or not os.path.exists(config_path):
        success = create_default_config(config_path)
        if success:
            print(f"   ✓ Configuration created at: {config_path}")
        else:
            print(f"   ✗ Failed to create configuration")
            return 1
    else:
        print(f"   ✓ Configuration already exists at: {config_path}")
    
    print("\n2. Please update the configuration file with your Dify API details:")
    print(f"   - Edit {config_path}")
    print("   - Set your api_base_url, api_key, and dataset_id")
    
    print("\n3. Prepare your test cases:")
    print("   - Create a CSV file with columns: id,query,expected_answer,category")
    print("   - Example: tests/test_cases/sample.csv")
    
    print("\n4. Run testing:")
    print(f"   python main.py enhanced --config {config_path} --test-cases your_test_cases.csv")
    print(f"   python main.py basic --config {config_path} --test-file your_test_cases.csv")
    
    print("\nQuick start setup completed!")
    return 0


def run_web_interface(args):
    """Run web interface."""
    try:
        # Initialize web interface
        if args.config:
            web_interface = WebInterface(config_path=args.config)
        else:
            web_interface = WebInterface()
        
        print(f"Starting web server on {args.host}:{args.port}")
        web_interface.run(host=args.host, port=args.port)
        return 0
        
    except Exception as e:
        print(f"Failed to start web interface: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())