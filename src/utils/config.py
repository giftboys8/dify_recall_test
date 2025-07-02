#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration management utilities for Dify KB Recall Testing Tool.

This module provides functions to load, validate, and manage configuration files.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .logger import get_logger


class ConfigManager:
    """
    Manage configuration loading and validation.
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.logger = get_logger(self.__class__.__name__)
    
    def load_config(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Args:
            config_file: Path to configuration file (if None, uses default)
        
        Returns:
            Configuration dictionary
        """
        if config_file is None:
            # Try to find default config
            for filename in ['default.json', 'config.json']:
                config_path = self.config_dir / filename
                if config_path.exists():
                    config_file = str(config_path)
                    break
            
            if config_file is None:
                raise FileNotFoundError("No configuration file found")
        
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.logger.info(f"Loaded configuration from {config_path}")
            return self._validate_config(config)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading configuration: {e}")
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize configuration.
        
        Args:
            config: Raw configuration dictionary
        
        Returns:
            Validated configuration dictionary
        """
        # Required fields
        required_fields = ['api_base_url', 'api_key', 'dataset_id']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required configuration field: {field}")
        
        # Set defaults
        defaults = {
            'test_settings': {
                'top_k': 10,
                'delay_between_requests': 1.0,
                'score_threshold_enabled': False,
                'score_threshold': 0.0,
                'reranking_enabled': True,
                'search_method': 'semantic_search',
                'reranking_model': {
                    'provider': 'cohere',
                    'model': 'rerank-multilingual-v3.0'
                },
                'hybrid_search_weights': {
                    'semantic_weight': 0.8,
                    'keyword_weight': 0.2
                },
                'embedding_model': {
                    'provider': 'openai',
                    'model': 'embedding-3'
                }
            },
            'output_settings': {
                'output_dir': 'data/output',
                'output_prefix': 'recall_test',
                'save_csv': True,
                'save_detailed_json': True,
                'include_document_content': True
            },
            'logging': {
                'level': 'INFO',
                'file': None,
                'console_output': True
            }
        }
        
        # Merge defaults with provided config
        for section, section_defaults in defaults.items():
            if section not in config:
                config[section] = {}
            
            for key, default_value in section_defaults.items():
                if key not in config[section]:
                    config[section][key] = default_value
        
        # Validate URLs
        if not config['api_base_url'].startswith(('http://', 'https://')):
            raise ValueError("api_base_url must start with http:// or https://")
        
        # Validate numeric values
        test_settings = config['test_settings']
        if test_settings['top_k'] <= 0:
            raise ValueError("top_k must be positive")
        if test_settings['delay_between_requests'] < 0:
            raise ValueError("delay_between_requests must be non-negative")
        if test_settings['score_threshold'] < 0 or test_settings['score_threshold'] > 1:
            raise ValueError("score_threshold must be between 0 and 1")
        
        # Validate search method
        valid_search_methods = ['semantic_search', 'keyword_search', 'hybrid_search']
        if test_settings['search_method'] not in valid_search_methods:
            raise ValueError(f"search_method must be one of: {valid_search_methods}")
        
        # Validate hybrid search weights
        if test_settings['search_method'] == 'hybrid_search':
            weights = test_settings['hybrid_search_weights']
            if abs(weights['semantic_weight'] + weights['keyword_weight'] - 1.0) > 0.01:
                raise ValueError("Hybrid search weights must sum to 1.0")
        
        self.logger.info("Configuration validation passed")
        return config
    
    def save_config(self, config: Dict[str, Any], config_file: str) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary
            config_file: Path to save configuration
        """
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            raise RuntimeError(f"Error saving configuration: {e}")
    
    def create_template_config(self, output_file: str = None) -> str:
        """
        Create a template configuration file.
        
        Args:
            output_file: Path to save template (if None, uses default)
        
        Returns:
            Path to created template file
        """
        if output_file is None:
            output_file = self.config_dir / "template.json"
        
        template = {
            "api_base_url": "http://your-dify-instance.com",
            "api_key": "your-api-key",
            "dataset_id": "your-dataset-id",
            "test_settings": {
                "top_k": 10,
                "delay_between_requests": 1.0,
                "score_threshold_enabled": False,
                "score_threshold": 0.0,
                "reranking_enabled": True,
                "search_method": "semantic_search",
                "reranking_model": {
                    "provider": "cohere",
                    "model": "rerank-multilingual-v3.0"
                },
                "hybrid_search_weights": {
                    "semantic_weight": 0.8,
                    "keyword_weight": 0.2
                },
                "embedding_model": {
                    "provider": "openai",
                    "model": "embedding-3"
                }
            },
            "output_settings": {
                "output_dir": "data/output",
                "output_prefix": "recall_test",
                "save_csv": True,
                "save_detailed_json": True,
                "include_document_content": True
            },
            "logging": {
                "level": "INFO",
                "file": None,
                "console_output": True
            }
        }
        
        self.save_config(template, output_file)
        return str(output_file)
    
    def get_config_value(self, config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            config: Configuration dictionary
            key_path: Dot-separated key path (e.g., 'test_settings.top_k')
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_config_value(self, config: Dict[str, Any], key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            config: Configuration dictionary
            key_path: Dot-separated key path (e.g., 'test_settings.top_k')
            value: Value to set
        """
        keys = key_path.split('.')
        current = config
        
        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value


def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to load configuration.
    
    Args:
        config_file: Path to configuration file
    
    Returns:
        Configuration dictionary
    """
    manager = ConfigManager()
    return manager.load_config(config_file)


def create_default_config(output_dir: str = "config") -> str:
    """
    Create default configuration files.
    
    Args:
        output_dir: Directory to create configuration files
    
    Returns:
        Path to created template file
    """
    manager = ConfigManager(output_dir)
    return manager.create_template_config()