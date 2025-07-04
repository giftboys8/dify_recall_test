#!/usr/bin/env python3
"""
统一数据库管理模块
使用单一SQLite数据库存储所有文档的笔记和标注
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging


class UnifiedDatabaseManager:
    """统一数据库管理器"""
    
    def __init__(self, db_path: str = "data/unified_documents.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.init_database()
        
    def init_database(self) -> None:
        """初始化统一数据库"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # 创建文档表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建页面笔记表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS page_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    UNIQUE(document_id, page_number)
                )
            """)
            
            # 创建书签表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)
            
            # 创建标注表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS annotations (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    x REAL NOT NULL,
                    y REAL NOT NULL,
                    width REAL NOT NULL,
                    height REAL NOT NULL,
                    color TEXT NOT NULL DEFAULT '#ffff00',
                    text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)
            
            # 创建学习进度表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    progress_percentage REAL DEFAULT 0,
                    total_pages INTEGER DEFAULT 0,
                    visited_pages TEXT DEFAULT '[]',
                    study_time_minutes INTEGER DEFAULT 0,
                    last_page INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    UNIQUE(document_id)
                )
            """)
            
            conn.commit()
            self.logger.info("Initialized unified database")
    
    def register_document(self, doc_id: str, title: str, file_path: str = None) -> bool:
        """注册文档"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO documents (id, title, file_path, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (doc_id, title, file_path))
                
                # 初始化学习进度记录
                cursor.execute("""
                    INSERT OR IGNORE INTO learning_progress (document_id, progress_percentage) 
                    VALUES (?, 0)
                """, (doc_id,))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to register document: {e}")
            return False
    
    def get_document_annotations(self, doc_id: str) -> List[Dict[str, Any]]:
        """获取文档标注（兼容API调用）"""
        return self.get_annotations(doc_id)
    
    def add_document_annotation(self, doc_id: str, annotation: Dict[str, Any]) -> str:
        """添加文档标注（兼容API调用）"""
        # 生成唯一ID如果没有提供
        if 'id' not in annotation:
            import uuid
            annotation['id'] = str(uuid.uuid4())
        
        success = self.save_annotation(doc_id, annotation)
        if success:
            return annotation['id']
        else:
            raise Exception("Failed to save annotation")
    
    def save_page_note(self, doc_id: str, page_number: int, content: str) -> bool:
        """保存页面笔记"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO page_notes (document_id, page_number, content, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (doc_id, page_number, content))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save page note: {e}")
            return False
    
    def delete_page_note(self, doc_id: str, page_number: int) -> bool:
        """删除页面笔记"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM page_notes WHERE document_id = ? AND page_number = ?
                """, (doc_id, page_number))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to delete page note: {e}")
            return False
    
    def get_page_note(self, doc_id: str, page_number: int) -> Optional[str]:
        """获取页面笔记"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT content FROM page_notes WHERE document_id = ? AND page_number = ?
                """, (doc_id, page_number))
                
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            self.logger.error(f"Failed to get page note: {e}")
            return None
    
    def get_all_page_notes(self, doc_id: str) -> Dict[int, Dict[str, Any]]:
        """获取所有页面笔记"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT page_number, content, created_at, updated_at 
                    FROM page_notes WHERE document_id = ? ORDER BY page_number
                """, (doc_id,))
                
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
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO bookmarks (document_id, page_number, title, description)
                    VALUES (?, ?, ?, ?)
                """, (doc_id, page_number, title, description))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add bookmark: {e}")
            return False
    
    def get_bookmarks(self, doc_id: str) -> List[Dict[str, Any]]:
        """获取所有书签"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, page_number, title, description, created_at 
                    FROM bookmarks WHERE document_id = ? ORDER BY page_number
                """, (doc_id,))
                
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
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM bookmarks WHERE id = ? AND document_id = ?
                """, (bookmark_id, doc_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to remove bookmark: {e}")
            return False
    
    def save_annotation(self, doc_id: str, annotation: Dict[str, Any]) -> bool:
        """保存标注"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO annotations 
                    (id, document_id, page_number, x, y, width, height, color, text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    annotation['id'],
                    doc_id,
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
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, page_number, x, y, width, height, color, text, created_at 
                    FROM annotations WHERE document_id = ? ORDER BY page_number, created_at
                """, (doc_id,))
                
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
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE learning_progress SET 
                    progress_percentage = ?,
                    total_pages = ?,
                    visited_pages = ?,
                    study_time_minutes = ?,
                    last_page = ?,
                    updated_at = CURRENT_TIMESTAMP
                    WHERE document_id = ?
                """, (
                    progress_percentage,
                    total_pages,
                    json.dumps(visited_pages),
                    study_time_minutes,
                    last_page,
                    doc_id
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update progress: {e}")
            return False
    
    def get_progress(self, doc_id: str) -> Dict[str, Any]:
        """获取学习进度"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT progress_percentage, total_pages, visited_pages, 
                           study_time_minutes, last_page, updated_at
                    FROM learning_progress WHERE document_id = ?
                """, (doc_id,))
                
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
    
    def get_document_notes(self, doc_id: str) -> Dict[str, Any]:
        """获取文档笔记（兼容原JSON格式）"""
        try:
            # 确保文档已注册
            self.register_document(doc_id, doc_id)
            
            page_notes = self.get_all_page_notes(doc_id)
            bookmarks = self.get_bookmarks(doc_id)
            progress_data = self.get_progress(doc_id)
            
            return {
                'pages': page_notes,
                'bookmarks': bookmarks,
                'progress': progress_data['progress']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get document notes: {e}")
            return {'pages': {}, 'bookmarks': [], 'progress': 0}
    
    def save_document_notes(self, doc_id: str, notes_data: Dict[str, Any]) -> bool:
        """保存文档笔记（兼容原JSON格式）"""
        try:
            # 确保文档已注册
            self.register_document(doc_id, doc_id)
            
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
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save document notes: {e}")
            return False
    
    def _clear_bookmarks(self, doc_id: str) -> None:
        """清空文档的所有书签"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM bookmarks WHERE document_id = ?", (doc_id,))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to clear bookmarks: {e}")
    
    def migrate_from_old_databases(self, old_db_dir: str) -> bool:
        """从旧的独立数据库迁移数据"""
        try:
            old_db_path = Path(old_db_dir)
            if not old_db_path.exists():
                self.logger.info("No old databases to migrate")
                return True
            
            migrated_count = 0
            for db_file in old_db_path.glob("*.db"):
                doc_id = db_file.stem
                self.logger.info(f"Migrating database for document: {doc_id}")
                
                # 注册文档
                self.register_document(doc_id, doc_id)
                
                # 迁移数据
                with sqlite3.connect(str(db_file)) as old_conn:
                    old_cursor = old_conn.cursor()
                    
                    # 迁移页面笔记
                    try:
                        old_cursor.execute("SELECT page_number, content FROM page_notes")
                        for page_num, content in old_cursor.fetchall():
                            self.save_page_note(doc_id, page_num, content)
                    except sqlite3.OperationalError:
                        pass  # 表不存在
                    
                    # 迁移书签
                    try:
                        old_cursor.execute("SELECT page_number, title, description FROM bookmarks")
                        for page_num, title, desc in old_cursor.fetchall():
                            self.add_bookmark(doc_id, page_num, title, desc or "")
                    except sqlite3.OperationalError:
                        pass  # 表不存在
                    
                    # 迁移标注
                    try:
                        old_cursor.execute("SELECT id, page_number, x, y, width, height, color, text FROM annotations")
                        for ann_id, page_num, x, y, width, height, color, text in old_cursor.fetchall():
                            annotation = {
                                'id': ann_id,
                                'page': page_num,
                                'x': x,
                                'y': y,
                                'width': width,
                                'height': height,
                                'color': color,
                                'text': text or ''
                            }
                            self.save_annotation(doc_id, annotation)
                    except sqlite3.OperationalError:
                        pass  # 表不存在
                
                migrated_count += 1
            
            self.logger.info(f"Successfully migrated {migrated_count} databases")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to migrate databases: {e}")
            return False