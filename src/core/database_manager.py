#!/usr/bin/env python3
"""
数据库管理模块
为每个文档创建独立的SQLite数据库来存储笔记和标注
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging


class DocumentDatabaseManager:
    """文档数据库管理器"""
    
    def __init__(self, db_base_dir: str = "data/databases"):
        self.db_base_dir = Path(db_base_dir)
        self.db_base_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
    def get_db_path(self, doc_id: str) -> Path:
        """获取文档数据库路径"""
        return self.db_base_dir / f"{doc_id}.db"
    
    def init_document_db(self, doc_id: str) -> None:
        """初始化文档数据库"""
        db_path = self.get_db_path(doc_id)
        
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            
            # 创建页面笔记表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS page_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    page_number INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(page_number)
                )
            """)
            
            # 创建书签表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    page_number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建标注表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS annotations (
                    id TEXT PRIMARY KEY,
                    page_number INTEGER NOT NULL,
                    x REAL NOT NULL,
                    y REAL NOT NULL,
                    width REAL NOT NULL,
                    height REAL NOT NULL,
                    color TEXT NOT NULL DEFAULT '#ffff00',
                    text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建学习进度表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_progress (
                    id INTEGER PRIMARY KEY,
                    progress_percentage REAL DEFAULT 0,
                    total_pages INTEGER DEFAULT 0,
                    visited_pages TEXT DEFAULT '[]',
                    study_time_minutes INTEGER DEFAULT 0,
                    last_page INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 初始化学习进度记录
            cursor.execute("""
                INSERT OR IGNORE INTO learning_progress (id, progress_percentage) 
                VALUES (1, 0)
            """)
            
            conn.commit()
            self.logger.info(f"Initialized database for document: {doc_id}")
    
    def save_page_note(self, doc_id: str, page_number: int, content: str) -> bool:
        """保存页面笔记"""
        try:
            db_path = self.get_db_path(doc_id)
            
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO page_notes (page_number, content, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (page_number, content))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save page note: {e}")
            return False
    
    def delete_page_note(self, doc_id: str, page_number: int) -> bool:
        """删除页面笔记"""
        try:
            db_path = self.get_db_path(doc_id)
            
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM page_notes WHERE page_number = ?
                """, (page_number,))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to delete page note: {e}")
            return False
    
    def get_page_note(self, doc_id: str, page_number: int) -> Optional[str]:
        """获取页面笔记"""
        try:
            db_path = self.get_db_path(doc_id)
            
            if not db_path.exists():
                self.init_document_db(doc_id)
                return None
            
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT content FROM page_notes WHERE page_number = ?
                """, (page_number,))
                
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            self.logger.error(f"Failed to get page note: {e}")
            return None
    
    def get_all_page_notes(self, doc_id: str) -> Dict[int, Dict[str, Any]]:
        """获取所有页面笔记"""
        try:
            db_path = self.get_db_path(doc_id)
            
            if not db_path.exists():
                self.init_document_db(doc_id)
                return {}
            
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT page_number, content, created_at, updated_at 
                    FROM page_notes ORDER BY page_number
                """)
                
                notes = {}
                for row in cursor.fetchall():
                    page_num, content, created_at, updated_at = row
                    notes[page_num] = {
                        'content': content,
                        'created': created_at,
                        'updated': updated_at
                    }
                
                return notes
                
        except Exception as e:
            self.logger.error(f"Failed to get all page notes: {e}")
            return {}
    
    def add_bookmark(self, doc_id: str, page_number: int, title: str, description: str = "") -> bool:
        """添加书签"""
        try:
            db_path = self.get_db_path(doc_id)
            
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO bookmarks (page_number, title, description)
                    VALUES (?, ?, ?)
                """, (page_number, title, description))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add bookmark: {e}")
            return False
    
    def get_bookmarks(self, doc_id: str) -> List[Dict[str, Any]]:
        """获取所有书签"""
        try:
            db_path = self.get_db_path(doc_id)
            
            if not db_path.exists():
                self.init_document_db(doc_id)
                return []
            
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, page_number, title, description, created_at 
                    FROM bookmarks ORDER BY page_number
                """)
                
                bookmarks = []
                for row in cursor.fetchall():
                    bookmark_id, page_num, title, desc, created_at = row
                    bookmarks.append({
                        'id': bookmark_id,
                        'page': page_num,
                        'title': title,
                        'description': desc,
                        'created': created_at
                    })
                
                return bookmarks
                
        except Exception as e:
            self.logger.error(f"Failed to get bookmarks: {e}")
            return []
    
    def remove_bookmark(self, doc_id: str, bookmark_id: int) -> bool:
        """删除书签"""
        try:
            db_path = self.get_db_path(doc_id)
            
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to remove bookmark: {e}")
            return False
    
    def save_annotation(self, doc_id: str, annotation: Dict[str, Any]) -> bool:
        """保存标注"""
        try:
            db_path = self.get_db_path(doc_id)
            
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO annotations 
                    (id, page_number, x, y, width, height, color, text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    annotation['id'],
                    annotation['page'],
                    annotation['x'],
                    annotation['y'],
                    annotation['width'],
                    annotation['height'],
                    annotation.get('color', '#ffff00'),
                    annotation.get('text', '')
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save annotation: {e}")
            return False
    
    def get_annotations(self, doc_id: str) -> List[Dict[str, Any]]:
        """获取所有标注"""
        try:
            db_path = self.get_db_path(doc_id)
            
            if not db_path.exists():
                self.init_document_db(doc_id)
                return []
            
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, page_number, x, y, width, height, color, text, created_at 
                    FROM annotations ORDER BY page_number, created_at
                """)
                
                annotations = []
                for row in cursor.fetchall():
                    ann_id, page_num, x, y, width, height, color, text, created_at = row
                    annotations.append({
                        'id': ann_id,
                        'page': page_num,
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height,
                        'color': color,
                        'text': text,
                        'created': created_at
                    })
                
                return annotations
                
        except Exception as e:
            self.logger.error(f"Failed to get annotations: {e}")
            return []
    
    def update_progress(self, doc_id: str, progress_percentage: float, 
                       total_pages: int, visited_pages: List[int], 
                       study_time_minutes: int = 0, last_page: int = 1) -> bool:
        """更新学习进度"""
        try:
            db_path = self.get_db_path(doc_id)
            
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE learning_progress SET 
                    progress_percentage = ?,
                    total_pages = ?,
                    visited_pages = ?,
                    study_time_minutes = ?,
                    last_page = ?,
                    updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, (
                    progress_percentage,
                    total_pages,
                    json.dumps(visited_pages),
                    study_time_minutes,
                    last_page
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update progress: {e}")
            return False
    
    def get_progress(self, doc_id: str) -> Dict[str, Any]:
        """获取学习进度"""
        try:
            db_path = self.get_db_path(doc_id)
            
            if not db_path.exists():
                self.init_document_db(doc_id)
                return {
                    'progress': 0,
                    'total_pages': 0,
                    'visited_pages': [],
                    'study_time_minutes': 0,
                    'last_page': 1
                }
            
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT progress_percentage, total_pages, visited_pages, 
                           study_time_minutes, last_page, updated_at
                    FROM learning_progress WHERE id = 1
                """)
                
                result = cursor.fetchone()
                if result:
                    progress, total_pages, visited_pages_json, study_time, last_page, updated_at = result
                    visited_pages = json.loads(visited_pages_json) if visited_pages_json else []
                    
                    return {
                        'progress': progress,
                        'total_pages': total_pages,
                        'visited_pages': visited_pages,
                        'study_time_minutes': study_time,
                        'last_page': last_page,
                        'updated_at': updated_at
                    }
                else:
                    return {
                        'progress': 0,
                        'total_pages': 0,
                        'visited_pages': [],
                        'study_time_minutes': 0,
                        'last_page': 1
                    }
                
        except Exception as e:
            self.logger.error(f"Failed to get progress: {e}")
            return {
                'progress': 0,
                'total_pages': 0,
                'visited_pages': [],
                'study_time_minutes': 0,
                'last_page': 1
            }
    
    def migrate_from_json(self, doc_id: str, notes_file: Path, annotations_file: Path) -> bool:
        """从JSON文件迁移数据到SQLite数据库"""
        try:
            self.init_document_db(doc_id)
            
            # 迁移笔记数据
            if notes_file.exists():
                with open(notes_file, 'r', encoding='utf-8') as f:
                    notes_data = json.load(f)
                
                # 迁移页面笔记
                pages = notes_data.get('pages', {})
                for page_str, note_data in pages.items():
                    page_num = int(page_str)
                    content = note_data.get('content', '') if isinstance(note_data, dict) else str(note_data)
                    if content:
                        self.save_page_note(doc_id, page_num, content)
                
                # 迁移书签
                bookmarks = notes_data.get('bookmarks', [])
                for bookmark in bookmarks:
                    self.add_bookmark(
                        doc_id,
                        bookmark.get('page', 1),
                        bookmark.get('title', ''),
                        bookmark.get('description', '')
                    )
                
                # 迁移进度
                progress = notes_data.get('progress', 0)
                self.update_progress(doc_id, progress, 0, [], 0, 1)
            
            # 迁移标注数据
            if annotations_file.exists():
                with open(annotations_file, 'r', encoding='utf-8') as f:
                    annotations_data = json.load(f)
                
                for annotation in annotations_data:
                    self.save_annotation(doc_id, annotation)
            
            self.logger.info(f"Successfully migrated data for document: {doc_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to migrate data for document {doc_id}: {e}")
            return False
    
    def get_document_notes(self, doc_id: str) -> Dict[str, Any]:
        """获取文档笔记（兼容原JSON格式）"""
        try:
            # 确保数据库已初始化
            if not self.get_db_path(doc_id).exists():
                self.init_document_db(doc_id)
            
            page_notes = self.get_all_page_notes(doc_id)
            bookmarks = self.get_bookmarks(doc_id)
            progress_data = self.get_progress(doc_id)
            
            # 转换为兼容格式
            pages = {}
            for page_num, note_data in page_notes.items():
                pages[str(page_num)] = {
                    'content': note_data['content'],
                    'created': note_data['created'],
                    'updated': note_data['updated']
                }
            
            return {
                'pages': pages,
                'bookmarks': bookmarks,
                'progress': progress_data['progress']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get document notes: {e}")
            return {'pages': {}, 'bookmarks': [], 'progress': 0}
    
    def save_document_notes(self, doc_id: str, notes_data: Dict[str, Any]) -> bool:
        """保存文档笔记（兼容原JSON格式）"""
        try:
            # 确保数据库已初始化
            if not self.get_db_path(doc_id).exists():
                self.init_document_db(doc_id)
            
            # 保存页面笔记
            pages = notes_data.get('pages', {})
            for page_str, note_data in pages.items():
                page_num = int(page_str)
                if isinstance(note_data, dict):
                    content = note_data.get('content', '')
                else:
                    content = str(note_data)
                
                if content:
                    self.save_page_note(doc_id, page_num, content)
                else:
                    # 如果内容为空，删除该页面的笔记
                    self.delete_page_note(doc_id, page_num)
            
            # 保存书签（先清空再重新添加）
            self._clear_bookmarks(doc_id)
            bookmarks = notes_data.get('bookmarks', [])
            for bookmark in bookmarks:
                self.add_bookmark(
                    doc_id,
                    bookmark.get('page', 1),
                    bookmark.get('title', ''),
                    bookmark.get('description', '')
                )
            
            # 保存进度
            progress = notes_data.get('progress', 0)
            self.update_progress(doc_id, progress, 0, [], 0, 1)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save document notes: {e}")
            return False
    
    def get_document_annotations(self, doc_id: str) -> List[Dict[str, Any]]:
        """获取文档标注"""
        # 确保数据库已初始化
        if not self.get_db_path(doc_id).exists():
            self.init_document_db(doc_id)
        
        return self.get_annotations(doc_id)
    
    def add_document_annotation(self, doc_id: str, annotation: Dict[str, Any]) -> str:
        """添加文档标注"""
        try:
            # 确保数据库已初始化
            if not self.get_db_path(doc_id).exists():
                self.init_document_db(doc_id)
            
            # 生成唯一ID
            annotation_id = str(int(time.time() * 1000))
            annotation['id'] = annotation_id
            annotation['created'] = datetime.now().isoformat()
            
            if self.save_annotation(doc_id, annotation):
                return annotation_id
            else:
                raise Exception("Failed to save annotation")
                
        except Exception as e:
            self.logger.error(f"Failed to add document annotation: {e}")
            raise
    
    def _clear_bookmarks(self, doc_id: str) -> bool:
        """清空所有书签"""
        try:
            db_path = self.get_db_path(doc_id)
            
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM bookmarks")
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to clear bookmarks: {e}")
            return False
    
    def export_to_json(self, doc_id: str) -> Dict[str, Any]:
        """导出数据为JSON格式"""
        try:
            # 获取所有数据
            page_notes = self.get_all_page_notes(doc_id)
            bookmarks = self.get_bookmarks(doc_id)
            annotations = self.get_annotations(doc_id)
            progress_data = self.get_progress(doc_id)
            
            # 转换为兼容格式
            pages = {}
            for page_num, note_data in page_notes.items():
                pages[str(page_num)] = {
                    'content': note_data['content'],
                    'created': note_data['created'],
                    'updated': note_data['updated']
                }
            
            export_data = {
                'document_id': doc_id,
                'notes': {
                    'pages': pages,
                    'bookmarks': bookmarks,
                    'progress': progress_data['progress']
                },
                'annotations': annotations,
                'progress': progress_data,
                'exported_at': datetime.now().isoformat()
            }
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"Failed to export data for document {doc_id}: {e}")
            return {}