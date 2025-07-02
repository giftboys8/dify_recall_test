#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visualization utilities for Dify KB Recall Testing Tool.

This module provides functions to generate charts and visualizations
for test results analysis.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# import matplotlib.pyplot as plt
import pandas as pd
# import seaborn as sns
# from matplotlib.figure import Figure

from .logger import get_logger


class VisualizationGenerator:
    """
    Generate visualizations for recall test results.
    """
    
    def __init__(self, output_dir: str = "data/output"):
        """
        Initialize visualization generator.
        
        Args:
            output_dir: Directory to save visualizations
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(self.__class__.__name__)
        
        # Set style
        # plt.style.use('seaborn-v0_8')
        # sns.set_palette("husl")
    
    def generate_score_distribution(self, df: pd.DataFrame, save_path: Optional[str] = None) -> str:
        """
        Generate score distribution visualization.
        
        Args:
            df: DataFrame with test results
            save_path: Path to save the plot
        
        Returns:
            Path to saved plot
        """
        # Temporarily disabled due to matplotlib dependency issues
        self.logger.warning("Visualization temporarily disabled due to matplotlib dependency issues")
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.output_dir / f"score_distribution_{timestamp}.png"
        return str(save_path)
        
        # fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        # fig.suptitle('Score Distribution Analysis', fontsize=16, fontweight='bold')
        # 
        # # Max score distribution
        # axes[0, 0].hist(df['max_score'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        # axes[0, 0].set_title('Max Score Distribution')
        # axes[0, 0].set_xlabel('Max Score')
        # axes[0, 0].set_ylabel('Frequency')
        # axes[0, 0].grid(True, alpha=0.3)
        # 
        # # Min score distribution
        # axes[0, 1].hist(df['min_score'], bins=20, alpha=0.7, color='lightcoral', edgecolor='black')
        # axes[0, 1].set_title('Min Score Distribution')
        # axes[0, 1].set_xlabel('Min Score')
        # axes[0, 1].set_ylabel('Frequency')
        # axes[0, 1].grid(True, alpha=0.3)
        # 
        # # Average score distribution
        # axes[1, 0].hist(df['avg_score'], bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
        # axes[1, 0].set_title('Average Score Distribution')
        # axes[1, 0].set_xlabel('Average Score')
        # axes[1, 0].set_ylabel('Frequency')
        # axes[1, 0].grid(True, alpha=0.3)
        # 
        # # Box plot comparison
        # score_data = [df['max_score'], df['avg_score'], df['min_score']]
        # axes[1, 1].boxplot(score_data, labels=['Max', 'Avg', 'Min'])
        # axes[1, 1].set_title('Score Comparison')
        # axes[1, 1].set_ylabel('Score')
        # axes[1, 1].grid(True, alpha=0.3)
        # 
        # plt.tight_layout()
        # plt.savefig(save_path, dpi=300, bbox_inches='tight')
        # plt.close()
        # 
        # self.logger.info(f"Score distribution plot saved to {save_path}")
        # return str(save_path)
    
    def generate_recall_performance(self, df: pd.DataFrame, save_path: Optional[str] = None) -> str:
        """
        Generate recall performance visualization.
        
        Args:
            df: DataFrame with test results
            save_path: Path to save the plot
        
        Returns:
            Path to saved plot
        """
        # Temporarily disabled due to matplotlib dependency issues
        self.logger.warning("Visualization temporarily disabled due to matplotlib dependency issues")
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.output_dir / f"recall_performance_{timestamp}.png"
        return str(save_path)
        
        # fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        # fig.suptitle('Recall Performance Analysis', fontsize=16, fontweight='bold')
        
        # Temporarily disabled matplotlib code
        # axes[0, 0].bar(range(len(df)), df['documents_count'], alpha=0.7, color='steelblue')
        # ... (all matplotlib code commented out)
        # self.logger.info(f"Recall performance plot saved to {save_path}")
        # return str(save_path)
    
    def generate_summary_report(self, df: pd.DataFrame, save_path: Optional[str] = None) -> str:
        """
        Generate summary report visualization.
        
        Args:
            df: DataFrame with test results
            save_path: Path to save the plot
        
        Returns:
            Path to saved plot
        """
        # Temporarily disabled due to matplotlib dependency issues
        self.logger.warning("Visualization temporarily disabled due to matplotlib dependency issues")
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.output_dir / f"summary_report_{timestamp}.png"
        return str(save_path)
        
        # fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        # fig.suptitle('Test Results Summary Report', fontsize=16, fontweight='bold')
        
        # Overall statistics
        total_queries = len(df)
        successful_queries = len(df[df['status'] == 'success'])
        success_rate = (successful_queries / total_queries) * 100 if total_queries > 0 else 0
        
        # Success rate pie chart
        success_data = [successful_queries, total_queries - successful_queries]
        success_labels = ['Success', 'Failed']
        axes[0, 0].pie(success_data, labels=success_labels, autopct='%1.1f%%', 
                      colors=['lightgreen', 'lightcoral'])
        axes[0, 0].set_title(f'Overall Success Rate\n({successful_queries}/{total_queries})')
        
        # Score statistics
        if successful_queries > 0:
            successful_df = df[df['status'] == 'success']
            score_stats = {
                'Max Score': [successful_df['max_score'].mean(), successful_df['max_score'].std()],
                'Avg Score': [successful_df['avg_score'].mean(), successful_df['avg_score'].std()],
                'Min Score': [successful_df['min_score'].mean(), successful_df['min_score'].std()]
            }
            
            x_pos = range(len(score_stats))
            means = [stats[0] for stats in score_stats.values()]
            stds = [stats[1] for stats in score_stats.values()]
            
            axes[0, 1].bar(x_pos, means, yerr=stds, capsize=5, alpha=0.7, color='skyblue')
            axes[0, 1].set_title('Score Statistics (Mean ± Std)')
            axes[0, 1].set_xticks(x_pos)
            axes[0, 1].set_xticklabels(score_stats.keys())
            axes[0, 1].set_ylabel('Score')
            axes[0, 1].grid(True, alpha=0.3)
        
        # Documents count distribution
        if successful_queries > 0:
            doc_counts = successful_df['documents_count'].value_counts().sort_index()
            axes[0, 2].bar(doc_counts.index, doc_counts.values, alpha=0.7, color='orange')
            axes[0, 2].set_title('Documents Count Distribution')
            axes[0, 2].set_xlabel('Number of Documents')
            axes[0, 2].set_ylabel('Frequency')
            axes[0, 2].grid(True, alpha=0.3)
        
        # Score correlation heatmap
        if successful_queries > 0:
            score_corr = successful_df[['max_score', 'avg_score', 'min_score', 'documents_count']].corr()
            im = axes[1, 0].imshow(score_corr, cmap='coolwarm', aspect='auto')
            axes[1, 0].set_title('Score Correlation Matrix')
            axes[1, 0].set_xticks(range(len(score_corr.columns)))
            axes[1, 0].set_yticks(range(len(score_corr.columns)))
            axes[1, 0].set_xticklabels(score_corr.columns, rotation=45)
            axes[1, 0].set_yticklabels(score_corr.columns)
            
            # Add correlation values
            for i in range(len(score_corr.columns)):
                for j in range(len(score_corr.columns)):
                    axes[1, 0].text(j, i, f'{score_corr.iloc[i, j]:.2f}', 
                                   ha='center', va='center')
        
        # Query length vs performance (if query available)
        if 'query' in df.columns and successful_queries > 0:
            successful_df_copy = successful_df.copy()
            successful_df_copy['query_length'] = successful_df_copy['query'].str.len()
            axes[1, 1].scatter(successful_df_copy['query_length'], successful_df_copy['avg_score'], 
                             alpha=0.6, color='purple')
            axes[1, 1].set_title('Query Length vs Average Score')
            axes[1, 1].set_xlabel('Query Length (characters)')
            axes[1, 1].set_ylabel('Average Score')
            axes[1, 1].grid(True, alpha=0.3)
        
        # Performance trend (if timestamp available)
        if 'timestamp' in df.columns and successful_queries > 0:
            successful_df_sorted = successful_df.sort_values('timestamp')
            axes[1, 2].plot(range(len(successful_df_sorted)), successful_df_sorted['avg_score'], 
                          marker='o', alpha=0.7, color='green')
            axes[1, 2].set_title('Performance Trend Over Time')
            axes[1, 2].set_xlabel('Test Sequence')
            axes[1, 2].set_ylabel('Average Score')
            axes[1, 2].grid(True, alpha=0.3)
        else:
            axes[1, 2].text(0.5, 0.5, 'No timestamp data available', 
                           ha='center', va='center', transform=axes[1, 2].transAxes)
            axes[1, 2].set_title('Performance Trend')
        
        # plt.tight_layout()
        # plt.savefig(save_path, dpi=300, bbox_inches='tight')
        # plt.close()
        
        self.logger.info(f"Summary report saved to {save_path}")
        return str(save_path)
    
    def generate_all_visualizations(self, csv_file: str) -> Dict[str, str]:
        """
        Generate all available visualizations from CSV file.
        
        Args:
            csv_file: Path to CSV results file
        
        Returns:
            Dictionary mapping visualization type to file path
        """
        try:
            df = pd.read_csv(csv_file)
            self.logger.info(f"Loaded {len(df)} records from {csv_file}")
            
            visualizations = {}
            
            # Generate score distribution
            if all(col in df.columns for col in ['max_score', 'min_score', 'avg_score']):
                viz_path = self.generate_score_distribution(df)
                visualizations['score_distribution'] = viz_path
            
            # Generate recall performance
            viz_path = self.generate_recall_performance(df)
            visualizations['recall_performance'] = viz_path
            
            # Generate summary report
            viz_path = self.generate_summary_report(df)
            visualizations['summary_report'] = viz_path
            
            self.logger.info(f"Generated {len(visualizations)} visualizations")
            return visualizations
            
        except Exception as e:
            self.logger.error(f"Error generating visualizations: {e}")
            raise


def generate_visualization(csv_file: str, output_dir: str = "data/output") -> Dict[str, str]:
    """
    Convenience function to generate all visualizations.
    
    Args:
        csv_file: Path to CSV results file
        output_dir: Directory to save visualizations
    
    Returns:
        Dictionary mapping visualization type to file path
    """
    generator = VisualizationGenerator(output_dir)
    return generator.generate_all_visualizations(csv_file)