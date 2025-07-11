#!/usr/bin/env python3
"""
网站管理器
用于管理网站收藏、标签、搜索等功能
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


@dataclass
class WebsiteAccount:
    """网站账号数据模型"""
    username: str = ""
    email: str = ""
    notes: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    id: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.id is None:
            import uuid
            self.id = str(uuid.uuid4())


@dataclass
class Website:
    """网站数据模型"""
    id: Optional[int] = None
    url: str = ""
    title: str = ""
    description: str = ""
    tags: List[str] = None
    favicon_url: str = ""
    accounts: List[WebsiteAccount] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    visit_count: int = 0
    last_visited: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.accounts is None:
            self.accounts = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()


class WebsitesManager:
    """网站管理器"""
    
    def __init__(self, db_path: str = "data/websites.db"):
        """初始化网站管理器"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            # 创建网站表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS websites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    tags TEXT,  -- JSON格式存储标签列表
                    favicon_url TEXT,
                    accounts TEXT,  -- JSON格式存储账号列表
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    visit_count INTEGER DEFAULT 0,
                    last_visited TEXT
                )
            """)
            
            # 检查是否需要添加accounts字段（向后兼容）
            cursor = conn.execute("PRAGMA table_info(websites)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'accounts' not in columns:
                conn.execute("ALTER TABLE websites ADD COLUMN accounts TEXT DEFAULT '[]'")
            
            conn.commit()
    
    def add_website(self, website: Website) -> int:
        """添加网站"""
        try:
            # 自动获取网站信息
            if not website.title or not website.description:
                self._fetch_website_info(website)
            
            website.updated_at = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO websites (url, title, description, tags, favicon_url, accounts,
                                        created_at, updated_at, visit_count, last_visited)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    website.url,
                    website.title,
                    website.description,
                    json.dumps(website.tags, ensure_ascii=False),
                    website.favicon_url,
                    json.dumps([asdict(acc) if isinstance(acc, WebsiteAccount) else acc for acc in website.accounts], ensure_ascii=False),
                    website.created_at,
                    website.updated_at,
                    website.visit_count,
                    website.last_visited
                ))
                website.id = cursor.lastrowid
                conn.commit()
                
            self.logger.info(f"添加网站成功: {website.title} ({website.url})")
            return website.id
            
        except sqlite3.IntegrityError:
            raise ValueError(f"网站URL已存在: {website.url}")
        except Exception as e:
            self.logger.error(f"添加网站失败: {e}")
            raise
    
    def update_website(self, website_id: int, **kwargs) -> bool:
        """更新网站信息"""
        try:
            # 构建更新字段
            update_fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in ['title', 'description', 'url', 'favicon_url', 'last_visited']:
                    update_fields.append(f"{field} = ?")
                    values.append(value)
                elif field == 'tags' and isinstance(value, list):
                    update_fields.append("tags = ?")
                    values.append(json.dumps(value, ensure_ascii=False))
                elif field == 'accounts' and isinstance(value, list):
                    update_fields.append("accounts = ?")
                    # 处理WebsiteAccount对象或字典
                    accounts_data = []
                    for acc in value:
                        if isinstance(acc, WebsiteAccount):
                            accounts_data.append(asdict(acc))
                        elif isinstance(acc, dict):
                            accounts_data.append(acc)
                    values.append(json.dumps(accounts_data, ensure_ascii=False))
                elif field == 'visit_count' and isinstance(value, int):
                    update_fields.append("visit_count = ?")
                    values.append(value)
            
            if not update_fields:
                return False
            
            # 添加更新时间
            update_fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(website_id)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    f"UPDATE websites SET {', '.join(update_fields)} WHERE id = ?",
                    values
                )
                success = cursor.rowcount > 0
                conn.commit()
                
            if success:
                self.logger.info(f"更新网站成功: ID {website_id}")
            return success
            
        except Exception as e:
            self.logger.error(f"更新网站失败: {e}")
            raise
    
    def delete_website(self, website_id: int) -> bool:
        """删除网站"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM websites WHERE id = ?", (website_id,))
                success = cursor.rowcount > 0
                conn.commit()
                
            if success:
                self.logger.info(f"删除网站成功: ID {website_id}")
            return success
            
        except Exception as e:
            self.logger.error(f"删除网站失败: {e}")
            raise
    
    def get_website(self, website_id: int) -> Optional[Website]:
        """获取单个网站"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM websites WHERE id = ?", (website_id,))
                row = cursor.fetchone()
                
            if row:
                return self._row_to_website(row)
            return None
            
        except Exception as e:
            self.logger.error(f"获取网站失败: {e}")
            raise
    
    def get_all_websites(self, limit: int = None, offset: int = 0) -> List[Website]:
        """获取所有网站"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = "SELECT * FROM websites ORDER BY updated_at DESC"
                params = []
                
                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
            return [self._row_to_website(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"获取网站列表失败: {e}")
            raise
    
    def search_websites(self, query: str, tags: List[str] = None, limit: int = None, offset: int = 0) -> List[Website]:
        """搜索网站（基础文本搜索）"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                sql_query = """
                    SELECT * FROM websites 
                    WHERE (title LIKE ? OR description LIKE ? OR url LIKE ?)
                """
                params = [f"%{query}%", f"%{query}%", f"%{query}%"]
                
                # 标签过滤
                if tags:
                    tag_conditions = []
                    for tag in tags:
                        tag_conditions.append("tags LIKE ?")
                        params.append(f"%{tag}%")
                    sql_query += " AND (" + " OR ".join(tag_conditions) + ")"
                
                sql_query += " ORDER BY visit_count DESC, updated_at DESC"
                
                # 添加分页
                if limit:
                    sql_query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                
                cursor = conn.execute(sql_query, params)
                rows = cursor.fetchall()
                
            return [self._row_to_website(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"搜索网站失败: {e}")
            raise
    
    def get_websites_by_tags(self, tags: List[str], limit: int = None, offset: int = 0) -> List[Website]:
        """根据标签获取网站"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                tag_conditions = []
                params = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                
                query = f"""
                    SELECT * FROM websites 
                    WHERE {' OR '.join(tag_conditions)}
                    ORDER BY visit_count DESC, updated_at DESC
                """
                
                # 添加分页
                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
            return [self._row_to_website(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"根据标签获取网站失败: {e}")
            raise
    
    def get_websites_count(self, search_query: str = None, tags: List[str] = None) -> int:
        """获取网站总数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if search_query:
                    # 搜索模式下的总数
                    sql_query = """
                        SELECT COUNT(*) FROM websites 
                        WHERE (title LIKE ? OR description LIKE ? OR url LIKE ?)
                    """
                    params = [f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"]
                    
                    # 标签过滤
                    if tags:
                        tag_conditions = []
                        for tag in tags:
                            tag_conditions.append("tags LIKE ?")
                            params.append(f"%{tag}%")
                        sql_query += " AND (" + " OR ".join(tag_conditions) + ")"
                    
                    cursor = conn.execute(sql_query, params)
                elif tags:
                    # 标签筛选模式下的总数
                    tag_conditions = []
                    params = []
                    for tag in tags:
                        tag_conditions.append("tags LIKE ?")
                        params.append(f"%{tag}%")
                    
                    query = f"""
                        SELECT COUNT(*) FROM websites 
                        WHERE {' OR '.join(tag_conditions)}
                    """
                    cursor = conn.execute(query, params)
                else:
                    # 获取所有网站总数
                    cursor = conn.execute("SELECT COUNT(*) FROM websites")
                
                return cursor.fetchone()[0]
                
        except Exception as e:
            self.logger.error(f"获取网站总数失败: {e}")
            raise
    
    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT DISTINCT tags FROM websites WHERE tags IS NOT NULL")
                rows = cursor.fetchall()
                
            all_tags = set()
            for row in rows:
                if row[0]:
                    try:
                        tags = json.loads(row[0])
                        all_tags.update(tags)
                    except json.JSONDecodeError:
                        continue
                        
            return sorted(list(all_tags))
            
        except Exception as e:
            self.logger.error(f"获取标签列表失败: {e}")
            raise
    
    def record_visit(self, website_id: int) -> bool:
        """记录访问"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE websites 
                    SET visit_count = visit_count + 1, 
                        last_visited = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), website_id))
                success = cursor.rowcount > 0
                conn.commit()
                
            return success
            
        except Exception as e:
            self.logger.error(f"记录访问失败: {e}")
            raise
    
    def _row_to_website(self, row: sqlite3.Row) -> Website:
        """将数据库行转换为Website对象"""
        tags = []
        if row['tags']:
            try:
                tags = json.loads(row['tags'])
            except json.JSONDecodeError:
                tags = []
        
        accounts = []
        # 处理accounts字段（向后兼容）
        try:
            accounts_data = row['accounts'] or '[]'
        except (KeyError, IndexError):
            accounts_data = '[]'
        
        if accounts_data:
            try:
                accounts_list = json.loads(accounts_data)
                accounts = [WebsiteAccount(**acc_data) for acc_data in accounts_list]
            except (json.JSONDecodeError, TypeError):
                accounts = []
        
        return Website(
            id=row['id'],
            url=row['url'],
            title=row['title'],
            description=row['description'] or "",
            tags=tags,
            favicon_url=row['favicon_url'] or "",
            accounts=accounts,
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            visit_count=row['visit_count'],
            last_visited=row['last_visited']
        )
    
    def _fetch_website_info(self, website: Website):
        """自动获取网站信息"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(website.url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 获取标题
            if not website.title:
                title_tag = soup.find('title')
                if title_tag:
                    website.title = title_tag.get_text().strip()
                else:
                    website.title = urlparse(website.url).netloc
            
            # 获取描述
            if not website.description:
                # 尝试获取meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    website.description = meta_desc['content'].strip()
                else:
                    # 尝试获取og:description
                    og_desc = soup.find('meta', attrs={'property': 'og:description'})
                    if og_desc and og_desc.get('content'):
                        website.description = og_desc['content'].strip()
                    else:
                        website.description = f"来自 {urlparse(website.url).netloc} 的网站"
            
            # 获取favicon
            if not website.favicon_url:
                # 尝试获取favicon链接
                favicon_link = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
                if favicon_link and favicon_link.get('href'):
                    favicon_url = favicon_link['href']
                    if favicon_url.startswith('//'):
                        favicon_url = f"https:{favicon_url}"
                    elif favicon_url.startswith('/'):
                        parsed_url = urlparse(website.url)
                        favicon_url = f"{parsed_url.scheme}://{parsed_url.netloc}{favicon_url}"
                    elif not favicon_url.startswith('http'):
                        parsed_url = urlparse(website.url)
                        favicon_url = f"{parsed_url.scheme}://{parsed_url.netloc}/{favicon_url}"
                    website.favicon_url = favicon_url
                else:
                    # 使用默认favicon路径
                    parsed_url = urlparse(website.url)
                    website.favicon_url = f"{parsed_url.scheme}://{parsed_url.netloc}/favicon.ico"
                    
        except Exception as e:
            self.logger.warning(f"获取网站信息失败 {website.url}: {e}")
            # 设置默认值
            if not website.title:
                website.title = urlparse(website.url).netloc
            if not website.description:
                website.description = f"来自 {urlparse(website.url).netloc} 的网站"
    
    def export_websites(self) -> List[Dict[str, Any]]:
        """导出网站数据"""
        websites = self.get_all_websites()
        return [asdict(website) for website in websites]
    
    def import_websites(self, websites_data: List[Dict[str, Any]]) -> int:
        """导入网站数据"""
        imported_count = 0
        for data in websites_data:
            try:
                # 移除id字段，让数据库自动生成
                data.pop('id', None)
                website = Website(**data)
                self.add_website(website)
                imported_count += 1
            except Exception as e:
                self.logger.warning(f"导入网站失败 {data.get('url', 'unknown')}: {e}")
                continue
        
        return imported_count
    
    def add_website_account(self, website_id: int, account: WebsiteAccount) -> str:
        """为网站添加账号"""
        try:
            website = self.get_website(website_id)
            if not website:
                raise ValueError(f"网站不存在: ID {website_id}")
            
            # 添加到账号列表
            website.accounts.append(account)
            
            # 更新数据库
            success = self.update_website(website_id, accounts=website.accounts)
            if success:
                return account.id
            else:
                raise Exception("更新数据库失败")
            
        except Exception as e:
            self.logger.error(f"添加网站账号失败: {e}")
            raise
    
    def update_website_account(self, website_id: int, account_id: str, **kwargs) -> bool:
        """更新网站账号"""
        try:
            website = self.get_website(website_id)
            if not website:
                raise ValueError(f"网站不存在: ID {website_id}")
            
            # 查找账号
            account = None
            for acc in website.accounts:
                if acc.id == account_id:
                    account = acc
                    break
            
            if not account:
                raise ValueError(f"账号不存在: ID {account_id}")
            
            # 更新账号信息
            if 'username' in kwargs:
                account.username = kwargs['username']
            if 'email' in kwargs:
                account.email = kwargs['email']
            if 'notes' in kwargs:
                account.notes = kwargs['notes']
            
            # 更新时间戳
            from datetime import datetime
            account.updated_at = datetime.now().isoformat()
            
            # 更新数据库
            return self.update_website(website_id, accounts=website.accounts)
            
        except Exception as e:
            self.logger.error(f"更新网站账号失败: {e}")
            raise
    
    def delete_website_account(self, website_id: int, account_id: str) -> bool:
        """删除网站账号"""
        try:
            website = self.get_website(website_id)
            if not website:
                raise ValueError(f"网站不存在: ID {website_id}")
            
            # 查找并删除账号
            original_count = len(website.accounts)
            website.accounts = [acc for acc in website.accounts if acc.id != account_id]
            
            if len(website.accounts) == original_count:
                raise ValueError(f"账号不存在: ID {account_id}")
            
            # 更新数据库
            return self.update_website(website_id, accounts=website.accounts)
            
        except Exception as e:
            self.logger.error(f"删除网站账号失败: {e}")
            raise
    
    def get_website_accounts(self, website_id: int) -> List[WebsiteAccount]:
        """获取网站的所有账号"""
        try:
            website = self.get_website(website_id)
            if not website:
                raise ValueError(f"网站不存在: ID {website_id}")
            
            return website.accounts
            
        except Exception as e:
            self.logger.error(f"获取网站账号失败: {e}")
            raise