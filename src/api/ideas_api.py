#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ideas Collection API

This module provides Flask API endpoints for the ideas collection feature.

Author: Assistant
Version: 1.0
Date: 2025-01-02
"""

import json
import tempfile
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from typing import Dict, Any

try:
    from ..core.ideas_manager import IdeasManager, Idea
    from ..utils import get_logger
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.ideas_manager import IdeasManager, Idea
    from utils import get_logger


# Create blueprint
ideas_bp = Blueprint('ideas', __name__, url_prefix='/api/ideas')
logger = get_logger(__name__)

# Initialize ideas manager
ideas_manager = IdeasManager()


@ideas_bp.route('/', methods=['GET'])
def get_ideas():
    """Get all ideas with optional filters."""
    try:
        # Parse query parameters
        filters = {}
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('priority'):
            filters['priority'] = request.args.get('priority')
        if request.args.get('category'):
            filters['category'] = request.args.get('category')
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        ideas = ideas_manager.get_all_ideas(filters)
        return jsonify({
            'success': True,
            'ideas': [idea.to_dict() for idea in ideas],
            'count': len(ideas)
        })
    
    except Exception as e:
        logger.error(f"Error getting ideas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ideas_bp.route('/', methods=['POST'])
def create_idea():
    """Create a new idea."""
    try:
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({'success': False, 'error': 'Title is required'}), 400
        
        idea = Idea.from_dict(data)
        idea_id = ideas_manager.add_idea(idea)
        
        return jsonify({
            'success': True,
            'message': 'Idea created successfully',
            'idea_id': idea_id
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating idea: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ideas_bp.route('/<int:idea_id>', methods=['GET'])
def get_idea(idea_id):
    """Get a specific idea by ID."""
    try:
        idea = ideas_manager.get_idea(idea_id)
        if not idea:
            return jsonify({'success': False, 'error': 'Idea not found'}), 404
        
        return jsonify({
            'success': True,
            'idea': idea.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error getting idea {idea_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ideas_bp.route('/<int:idea_id>', methods=['PUT'])
def update_idea(idea_id):
    """Update an existing idea."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Remove id from updates to prevent conflicts
        data.pop('id', None)
        
        success = ideas_manager.update_idea(idea_id, data)
        if not success:
            return jsonify({'success': False, 'error': 'Idea not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Idea updated successfully'
        })
    
    except Exception as e:
        logger.error(f"Error updating idea {idea_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ideas_bp.route('/<int:idea_id>', methods=['DELETE'])
def delete_idea(idea_id):
    """Delete an idea."""
    try:
        success = ideas_manager.delete_idea(idea_id)
        if not success:
            return jsonify({'success': False, 'error': 'Idea not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Idea deleted successfully'
        })
    
    except Exception as e:
        logger.error(f"Error deleting idea {idea_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ideas_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get ideas statistics."""
    try:
        stats = ideas_manager.get_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ideas_bp.route('/export/<format_type>', methods=['GET'])
def export_ideas(format_type):
    """Export ideas in specified format."""
    try:
        if format_type not in ['json', 'csv']:
            return jsonify({'success': False, 'error': 'Unsupported format'}), 400
        
        data = ideas_manager.export_ideas(format_type)
        
        # Create temporary file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_type}', delete=False, encoding='utf-8') as f:
            f.write(data)
            temp_path = f.name
        
        mimetype = 'application/json' if format_type == 'json' else 'text/csv'
        filename = f'ideas_export_{timestamp}.{format_type}'
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
    
    except Exception as e:
        logger.error(f"Error exporting ideas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ideas_bp.route('/import', methods=['POST'])
def import_ideas():
    """Import ideas from uploaded file."""
    try:
        data = request.get_json()
        if not data or 'content' not in data or 'format' not in data:
            return jsonify({'success': False, 'error': 'Content and format are required'}), 400
        
        format_type = data['format']
        content = data['content']
        
        if format_type not in ['json', 'csv']:
            return jsonify({'success': False, 'error': 'Unsupported format'}), 400
        
        imported_count = ideas_manager.import_ideas(content, format_type)
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {imported_count} ideas',
            'imported_count': imported_count
        })
    
    except Exception as e:
        logger.error(f"Error importing ideas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ideas_bp.route('/batch', methods=['POST'])
def batch_operations():
    """Perform batch operations on ideas."""
    try:
        data = request.get_json()
        if not data or 'operation' not in data or 'idea_ids' not in data:
            return jsonify({'success': False, 'error': 'Operation and idea_ids are required'}), 400
        
        operation = data['operation']
        idea_ids = data['idea_ids']
        
        if not isinstance(idea_ids, list) or not idea_ids:
            return jsonify({'success': False, 'error': 'idea_ids must be a non-empty list'}), 400
        
        success_count = 0
        
        if operation == 'delete':
            for idea_id in idea_ids:
                if ideas_manager.delete_idea(idea_id):
                    success_count += 1
        
        elif operation == 'update_status':
            new_status = data.get('status')
            if not new_status:
                return jsonify({'success': False, 'error': 'Status is required for update_status operation'}), 400
            
            for idea_id in idea_ids:
                if ideas_manager.update_idea(idea_id, {'status': new_status}):
                    success_count += 1
        
        elif operation == 'update_priority':
            new_priority = data.get('priority')
            if not new_priority:
                return jsonify({'success': False, 'error': 'Priority is required for update_priority operation'}), 400
            
            for idea_id in idea_ids:
                if ideas_manager.update_idea(idea_id, {'priority': new_priority}):
                    success_count += 1
        
        else:
            return jsonify({'success': False, 'error': 'Unsupported operation'}), 400
        
        return jsonify({
            'success': True,
            'message': f'Batch operation completed. {success_count}/{len(idea_ids)} items processed successfully',
            'success_count': success_count,
            'total_count': len(idea_ids)
        })
    
    except Exception as e:
        logger.error(f"Error in batch operation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ideas_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all unique categories."""
    try:
        ideas = ideas_manager.get_all_ideas()
        categories = set()
        
        for idea in ideas:
            if idea.category:
                categories.add(idea.category)
        
        return jsonify({
            'success': True,
            'categories': sorted(list(categories))
        })
    
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ideas_bp.route('/tags', methods=['GET'])
def get_tags():
    """Get all unique tags."""
    try:
        ideas = ideas_manager.get_all_ideas()
        tags = set()
        
        for idea in ideas:
            idea_dict = idea.to_dict()
            if idea_dict.get('tags'):
                tags.update(idea_dict['tags'])
        
        return jsonify({
            'success': True,
            'tags': sorted(list(tags))
        })
    
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500