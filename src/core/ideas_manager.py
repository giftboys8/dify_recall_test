#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ideas Collection Manager

This module provides database management for the ideas collection feature.

Author: Assistant
Version: 1.0
Date: 2025-01-02
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class Idea:
    """Idea data model."""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    category: str = ""
    tags: str = ""  # JSON string of tag list
    priority: str = "medium"  # high, medium, low
    status: str = "pending"  # pending, in_progress, completed, on_hold
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    target_date: Optional[str] = None
    related_links: str = ""  # JSON string of link list
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Parse JSON fields
        try:
            data['tags'] = json.loads(self.tags) if self.tags else []
        except json.JSONDecodeError:
            data['tags'] = []
        
        try:
            data['related_links'] = json.loads(self.related_links) if self.related_links else []
        except json.JSONDecodeError:
            data['related_links'] = []
        
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Idea':
        """Create from dictionary."""
        # Convert lists to JSON strings
        if 'tags' in data and isinstance(data['tags'], list):
            data['tags'] = json.dumps(data['tags'])
        if 'related_links' in data and isinstance(data['related_links'], list):
            data['related_links'] = json.dumps(data['related_links'])
        
        return cls(**data)


class IdeasManager:
    """Ideas database manager."""
    
    def __init__(self, db_path: str = "data/ideas.db"):
        """Initialize ideas manager."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ideas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    tags TEXT,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    updated_at TEXT,
                    target_date TEXT,
                    related_links TEXT,
                    notes TEXT
                )
            """)
            conn.commit()
    
    def add_idea(self, idea: Idea) -> int:
        """Add a new idea."""
        now = datetime.now().isoformat()
        idea.created_at = now
        idea.updated_at = now
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO ideas (
                    title, description, category, tags, priority, status,
                    created_at, updated_at, target_date, related_links, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                idea.title, idea.description, idea.category, idea.tags,
                idea.priority, idea.status, idea.created_at, idea.updated_at,
                idea.target_date, idea.related_links, idea.notes
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_idea(self, idea_id: int) -> Optional[Idea]:
        """Get idea by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
            row = cursor.fetchone()
            if row:
                return Idea(**dict(row))
        return None
    
    def get_all_ideas(self, filters: Optional[Dict[str, Any]] = None) -> List[Idea]:
        """Get all ideas with optional filters."""
        query = "SELECT * FROM ideas"
        params = []
        
        if filters:
            conditions = []
            if 'status' in filters:
                conditions.append("status = ?")
                params.append(filters['status'])
            if 'priority' in filters:
                conditions.append("priority = ?")
                params.append(filters['priority'])
            if 'category' in filters:
                conditions.append("category = ?")
                params.append(filters['category'])
            if 'search' in filters:
                conditions.append("(title LIKE ? OR description LIKE ?)")
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term])
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [Idea(**dict(row)) for row in rows]
    
    def update_idea(self, idea_id: int, updates: Dict[str, Any]) -> bool:
        """Update an idea."""
        updates['updated_at'] = datetime.now().isoformat()
        
        # Convert lists to JSON strings if needed
        if 'tags' in updates and isinstance(updates['tags'], list):
            updates['tags'] = json.dumps(updates['tags'])
        if 'related_links' in updates and isinstance(updates['related_links'], list):
            updates['related_links'] = json.dumps(updates['related_links'])
        
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        query = f"UPDATE ideas SET {set_clause} WHERE id = ?"
        params = list(updates.values()) + [idea_id]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_idea(self, idea_id: int) -> bool:
        """Delete an idea."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ideas statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Total count
            total = conn.execute("SELECT COUNT(*) FROM ideas").fetchone()[0]
            
            # Status counts
            status_counts = {}
            cursor = conn.execute("SELECT status, COUNT(*) FROM ideas GROUP BY status")
            for status, count in cursor.fetchall():
                status_counts[status] = count
            
            # Priority counts
            priority_counts = {}
            cursor = conn.execute("SELECT priority, COUNT(*) FROM ideas GROUP BY priority")
            for priority, count in cursor.fetchall():
                priority_counts[priority] = count
            
            # Category counts
            category_counts = {}
            cursor = conn.execute("SELECT category, COUNT(*) FROM ideas WHERE category != '' GROUP BY category")
            for category, count in cursor.fetchall():
                category_counts[category] = count
            
            return {
                'total': total,
                'status_counts': status_counts,
                'priority_counts': priority_counts,
                'category_counts': category_counts,
                'completion_rate': (status_counts.get('completed', 0) / total * 100) if total > 0 else 0
            }
    
    def export_ideas(self, format_type: str = 'json') -> str:
        """Export all ideas to JSON or CSV format."""
        ideas = self.get_all_ideas()
        
        if format_type == 'json':
            return json.dumps([idea.to_dict() for idea in ideas], indent=2, ensure_ascii=False)
        elif format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            if ideas:
                fieldnames = ['id', 'title', 'description', 'category', 'tags', 'priority', 
                             'status', 'created_at', 'updated_at', 'target_date', 'related_links', 'notes']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for idea in ideas:
                    row = idea.to_dict()
                    # Convert lists back to strings for CSV
                    row['tags'] = ', '.join(row['tags']) if row['tags'] else ''
                    row['related_links'] = ', '.join(row['related_links']) if row['related_links'] else ''
                    writer.writerow(row)
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def import_ideas(self, data: str, format_type: str = 'json') -> int:
        """Import ideas from JSON or CSV format."""
        imported_count = 0
        
        if format_type == 'json':
            ideas_data = json.loads(data)
            for idea_data in ideas_data:
                # Remove id to avoid conflicts
                idea_data.pop('id', None)
                idea = Idea.from_dict(idea_data)
                self.add_idea(idea)
                imported_count += 1
        
        elif format_type == 'csv':
            import csv
            import io
            
            reader = csv.DictReader(io.StringIO(data))
            for row in reader:
                # Convert string tags back to list
                if row.get('tags'):
                    row['tags'] = [tag.strip() for tag in row['tags'].split(',') if tag.strip()]
                if row.get('related_links'):
                    row['related_links'] = [link.strip() for link in row['related_links'].split(',') if link.strip()]
                
                # Remove id to avoid conflicts
                row.pop('id', None)
                idea = Idea.from_dict(row)
                self.add_idea(idea)
                imported_count += 1
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        return imported_count