#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Results handling utilities for Dify KB Recall Testing Tool.

This module provides functions to save, load, and manage test results.
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from .logger import get_logger


class ResultsManager:
    """
    Manage test results storage and retrieval.
    """
    
    def __init__(self, output_dir: str = "data/output"):
        """
        Initialize results manager.
        
        Args:
            output_dir: Directory to store results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(self.__class__.__name__)
    
    def save_results_csv(
        self, 
        results: List[Dict[str, Any]], 
        filename: Optional[str] = None
    ) -> str:
        """
        Save test results to CSV file.
        
        Args:
            results: List of test result dictionaries
            filename: Output filename (auto-generated if None)
        
        Returns:
            Path to saved CSV file
        """
        if not results:
            raise ValueError("No results to save")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recall_test_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        # Get all possible fieldnames from all results
        fieldnames = set()
        for result in results:
            fieldnames.update(result.keys())
        fieldnames = sorted(list(fieldnames))
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            
            self.logger.info(f"Results saved to CSV: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving CSV results: {e}")
            raise
    
    def save_results_json(
        self, 
        results: List[Dict[str, Any]], 
        filename: Optional[str] = None,
        indent: int = 2
    ) -> str:
        """
        Save test results to JSON file.
        
        Args:
            results: List of test result dictionaries
            filename: Output filename (auto-generated if None)
            indent: JSON indentation level
        
        Returns:
            Path to saved JSON file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recall_test_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(results, jsonfile, indent=indent, ensure_ascii=False)
            
            self.logger.info(f"Results saved to JSON: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving JSON results: {e}")
            raise
    
    def save_summary_report(
        self, 
        results: List[Dict[str, Any]], 
        filename: Optional[str] = None
    ) -> str:
        """
        Save summary report to text file.
        
        Args:
            results: List of test result dictionaries
            filename: Output filename (auto-generated if None)
        
        Returns:
            Path to saved report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_report_{timestamp}.txt"
        
        filepath = self.output_dir / filename
        
        try:
            # Calculate statistics
            total_tests = len(results)
            successful_tests = len([r for r in results if r.get('status') == 'success'])
            failed_tests = total_tests - successful_tests
            success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
            
            # Get score statistics for successful tests
            successful_results = [r for r in results if r.get('status') == 'success']
            
            score_stats = {}
            if successful_results:
                for score_type in ['max_score', 'avg_score', 'min_score']:
                    scores = [r.get(score_type, 0) for r in successful_results if r.get(score_type) is not None]
                    if scores:
                        score_stats[score_type] = {
                            'mean': sum(scores) / len(scores),
                            'min': min(scores),
                            'max': max(scores),
                            'count': len(scores)
                        }
            
            # Document count statistics
            doc_counts = [r.get('documents_count', 0) for r in successful_results]
            total_documents = sum(doc_counts)
            avg_documents = (total_documents / len(doc_counts)) if doc_counts else 0
            
            # Generate report
            with open(filepath, 'w', encoding='utf-8') as report_file:
                report_file.write("=" * 60 + "\n")
                report_file.write("DIFY KNOWLEDGE BASE RECALL TEST SUMMARY REPORT\n")
                report_file.write("=" * 60 + "\n\n")
                
                # Test overview
                report_file.write("TEST OVERVIEW\n")
                report_file.write("-" * 20 + "\n")
                report_file.write(f"Total Tests: {total_tests}\n")
                report_file.write(f"Successful Tests: {successful_tests}\n")
                report_file.write(f"Failed Tests: {failed_tests}\n")
                report_file.write(f"Success Rate: {success_rate:.2f}%\n\n")
                
                # Document statistics
                report_file.write("DOCUMENT RECALL STATISTICS\n")
                report_file.write("-" * 30 + "\n")
                report_file.write(f"Total Documents Recalled: {total_documents}\n")
                report_file.write(f"Average Documents per Query: {avg_documents:.2f}\n\n")
                
                # Score statistics
                if score_stats:
                    report_file.write("SCORE STATISTICS\n")
                    report_file.write("-" * 20 + "\n")
                    for score_type, stats in score_stats.items():
                        report_file.write(f"{score_type.replace('_', ' ').title()}:\n")
                        report_file.write(f"  Mean: {stats['mean']:.4f}\n")
                        report_file.write(f"  Min: {stats['min']:.4f}\n")
                        report_file.write(f"  Max: {stats['max']:.4f}\n")
                        report_file.write(f"  Count: {stats['count']}\n\n")
                
                # Failed tests details
                if failed_tests > 0:
                    report_file.write("FAILED TESTS\n")
                    report_file.write("-" * 15 + "\n")
                    for i, result in enumerate(results):
                        if result.get('status') != 'success':
                            report_file.write(f"Test {i+1}: {result.get('query', 'N/A')}\n")
                            report_file.write(f"  Error: {result.get('error', 'Unknown error')}\n\n")
                
                # Timestamp
                report_file.write("=" * 60 + "\n")
                report_file.write(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                report_file.write("=" * 60 + "\n")
            
            self.logger.info(f"Summary report saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving summary report: {e}")
            raise
    
    def load_results_csv(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Load test results from CSV file.
        
        Args:
            filepath: Path to CSV file
        
        Returns:
            List of test result dictionaries
        """
        try:
            df = pd.read_csv(filepath)
            results = df.to_dict('records')
            self.logger.info(f"Loaded {len(results)} results from {filepath}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error loading CSV results: {e}")
            raise
    
    def load_results_json(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Load test results from JSON file.
        
        Args:
            filepath: Path to JSON file
        
        Returns:
            List of test result dictionaries
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as jsonfile:
                results = json.load(jsonfile)
            
            self.logger.info(f"Loaded {len(results)} results from {filepath}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error loading JSON results: {e}")
            raise
    
    def get_latest_results(self, file_type: str = "csv") -> Optional[str]:
        """
        Get path to the latest results file.
        
        Args:
            file_type: File type to search for (csv, json)
        
        Returns:
            Path to latest results file or None if not found
        """
        pattern = f"recall_test_*.{file_type}"
        files = list(self.output_dir.glob(pattern))
        
        if not files:
            return None
        
        # Sort by modification time, newest first
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        return str(latest_file)
    
    def list_results_files(self) -> Dict[str, List[str]]:
        """
        List all available results files.
        
        Returns:
            Dictionary mapping file type to list of file paths
        """
        file_types = {
            'csv': list(self.output_dir.glob("recall_test_*.csv")),
            'json': list(self.output_dir.glob("recall_test_*.json")),
            'reports': list(self.output_dir.glob("summary_report_*.txt"))
        }
        
        # Convert to strings and sort by modification time
        for file_type, files in file_types.items():
            file_types[file_type] = sorted(
                [str(f) for f in files],
                key=lambda f: Path(f).stat().st_mtime,
                reverse=True
            )
        
        return file_types
    
    def cleanup_old_results(self, keep_count: int = 10) -> int:
        """
        Clean up old result files, keeping only the most recent ones.
        
        Args:
            keep_count: Number of recent files to keep for each type
        
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        
        for pattern in ["recall_test_*.csv", "recall_test_*.json", "summary_report_*.txt"]:
            files = list(self.output_dir.glob(pattern))
            
            if len(files) > keep_count:
                # Sort by modification time, oldest first
                files_to_delete = sorted(files, key=lambda f: f.stat().st_mtime)[:-keep_count]
                
                for file_path in files_to_delete:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        self.logger.info(f"Deleted old result file: {file_path}")
                    except Exception as e:
                        self.logger.error(f"Error deleting file {file_path}: {e}")
        
        self.logger.info(f"Cleanup completed. Deleted {deleted_count} old result files.")
        return deleted_count


def save_results(
    results: List[Dict[str, Any]], 
    output_dir: str = "data/output",
    formats: List[str] = None
) -> Dict[str, str]:
    """
    Convenience function to save results in multiple formats.
    
    Args:
        results: List of test result dictionaries
        output_dir: Directory to save results
        formats: List of formats to save (csv, json, report)
    
    Returns:
        Dictionary mapping format to file path
    """
    if formats is None:
        formats = ['csv', 'json', 'report']
    
    manager = ResultsManager(output_dir)
    saved_files = {}
    
    if 'csv' in formats:
        saved_files['csv'] = manager.save_results_csv(results)
    
    if 'json' in formats:
        saved_files['json'] = manager.save_results_json(results)
    
    if 'report' in formats:
        saved_files['report'] = manager.save_summary_report(results)
    
    return saved_files