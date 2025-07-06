#!/usr/bin/env python3
"""
网站管理API
提供网站收藏、搜索、管理等功能的RESTful接口
"""

import json
import logging
from flask import Blueprint, request, jsonify
from typing import List, Dict, Any
from urllib.parse import urlparse

from ..core.websites_manager import WebsitesManager, Website, WebsiteAccount
from ..utils.logger import get_logger


class WebsitesAPI:
    """网站管理API类"""
    
    def __init__(self):
        """初始化API"""
        self.logger = get_logger(self.__class__.__name__)
        self.websites_manager = WebsitesManager()
        self.blueprint = Blueprint('websites_api', __name__)
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.blueprint.route('/api/websites', methods=['GET'])
        def get_websites():
            """获取网站列表"""
            try:
                # 获取查询参数
                limit = request.args.get('limit', type=int)
                offset = request.args.get('offset', 0, type=int)
                search_query = request.args.get('q', '').strip()
                tags = request.args.getlist('tags')
                
                if search_query:
                    # 执行搜索
                    websites = self.websites_manager.search_websites(search_query, tags)
                elif tags:
                    # 按标签筛选
                    websites = self.websites_manager.get_websites_by_tags(tags)
                else:
                    # 获取所有网站
                    websites = self.websites_manager.get_all_websites(limit, offset)
                
                # 转换为字典格式
                websites_data = []
                for website in websites:
                    website_dict = {
                        'id': website.id,
                        'url': website.url,
                        'title': website.title,
                        'description': website.description,
                        'tags': website.tags,
                        'favicon_url': website.favicon_url,
                        'created_at': website.created_at,
                        'updated_at': website.updated_at,
                        'visit_count': website.visit_count,
                        'last_visited': website.last_visited,
                        'accounts': [{
                            'id': acc.id,
                            'username': acc.username,
                            'description': acc.notes,
                            'created_at': acc.created_at,
                            'updated_at': acc.updated_at
                        } for acc in (website.accounts or [])]
                    }
                    websites_data.append(website_dict)
                
                return jsonify({
                    'success': True,
                    'data': websites_data,
                    'total': len(websites_data)
                })
                
            except Exception as e:
                self.logger.error(f"获取网站列表失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.blueprint.route('/api/websites', methods=['POST'])
        def add_website():
            """添加网站"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': '请提供网站数据'
                    }), 400
                
                # 验证必需字段
                url = data.get('url', '').strip()
                if not url:
                    return jsonify({
                        'success': False,
                        'error': 'URL是必需的'
                    }), 400
                
                # 验证URL格式
                try:
                    parsed_url = urlparse(url)
                    if not parsed_url.scheme or not parsed_url.netloc:
                        return jsonify({
                            'success': False,
                            'error': 'URL格式无效'
                        }), 400
                except Exception:
                    return jsonify({
                        'success': False,
                        'error': 'URL格式无效'
                    }), 400
                
                # 创建网站对象
                website = Website(
                    url=url,
                    title=data.get('title', '').strip(),
                    description=data.get('description', '').strip(),
                    tags=data.get('tags', []),
                    favicon_url=data.get('favicon_url', '').strip(),
                    accounts=data.get('accounts', [])
                )
                
                # 添加网站
                website_id = self.websites_manager.add_website(website)
                
                # 获取完整的网站信息
                created_website = self.websites_manager.get_website(website_id)
                
                return jsonify({
                    'success': True,
                    'data': {
                        'id': created_website.id,
                        'url': created_website.url,
                        'title': created_website.title,
                        'description': created_website.description,
                        'tags': created_website.tags,
                        'favicon_url': created_website.favicon_url,
                        'created_at': created_website.created_at,
                        'updated_at': created_website.updated_at,
                        'visit_count': created_website.visit_count,
                        'last_visited': created_website.last_visited,
                        'accounts': [{
                            'id': acc.id,
                            'username': acc.username,
                            'description': acc.notes,
                            'created_at': acc.created_at,
                            'updated_at': acc.updated_at
                        } for acc in (created_website.accounts or [])]
                    },
                    'message': '网站添加成功'
                }), 201
                
            except ValueError as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 400
            except Exception as e:
                self.logger.error(f"添加网站失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.blueprint.route('/api/websites/<int:website_id>', methods=['PUT'])
        def update_website(website_id):
            """更新网站"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': '请提供更新数据'
                    }), 400
                
                # 检查网站是否存在
                existing_website = self.websites_manager.get_website(website_id)
                if not existing_website:
                    return jsonify({
                        'success': False,
                        'error': '网站不存在'
                    }), 404
                
                # 准备更新数据
                update_data = {}
                for field in ['title', 'description', 'url', 'favicon_url']:
                    if field in data:
                        update_data[field] = data[field].strip() if isinstance(data[field], str) else data[field]
                
                if 'tags' in data and isinstance(data['tags'], list):
                    update_data['tags'] = data['tags']
                
                if 'accounts' in data and isinstance(data['accounts'], list):
                    update_data['accounts'] = data['accounts']
                
                # 执行更新
                success = self.websites_manager.update_website(website_id, **update_data)
                
                if success:
                    # 获取更新后的网站信息
                    updated_website = self.websites_manager.get_website(website_id)
                    return jsonify({
                        'success': True,
                        'data': {
                            'id': updated_website.id,
                            'url': updated_website.url,
                            'title': updated_website.title,
                            'description': updated_website.description,
                            'tags': updated_website.tags,
                            'favicon_url': updated_website.favicon_url,
                            'created_at': updated_website.created_at,
                            'updated_at': updated_website.updated_at,
                            'visit_count': updated_website.visit_count,
                            'last_visited': updated_website.last_visited,
                            'accounts': [{
                                'id': acc.id,
                                'username': acc.username,
                                'description': acc.notes,
                                'created_at': acc.created_at,
                                'updated_at': acc.updated_at
                            } for acc in (updated_website.accounts or [])]
                        },
                        'message': '网站更新成功'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': '更新失败'
                    }), 500
                
            except Exception as e:
                self.logger.error(f"更新网站失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.blueprint.route('/api/websites/<int:website_id>', methods=['DELETE'])
        def delete_website(website_id):
            """删除网站"""
            try:
                # 检查网站是否存在
                existing_website = self.websites_manager.get_website(website_id)
                if not existing_website:
                    return jsonify({
                        'success': False,
                        'error': '网站不存在'
                    }), 404
                
                # 执行删除
                success = self.websites_manager.delete_website(website_id)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': '网站删除成功'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': '删除失败'
                    }), 500
                
            except Exception as e:
                self.logger.error(f"删除网站失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.blueprint.route('/api/websites/<int:website_id>', methods=['GET'])
        def get_website(website_id):
            """获取单个网站"""
            try:
                website = self.websites_manager.get_website(website_id)
                
                if website:
                    return jsonify({
                        'success': True,
                        'data': {
                            'id': website.id,
                            'url': website.url,
                            'title': website.title,
                            'description': website.description,
                            'tags': website.tags,
                            'favicon_url': website.favicon_url,
                            'created_at': website.created_at,
                            'updated_at': website.updated_at,
                            'visit_count': website.visit_count,
                            'last_visited': website.last_visited,
                            'accounts': [{
                                'id': acc.id,
                                'username': acc.username,
                                'description': acc.notes,
                                'created_at': acc.created_at,
                                'updated_at': acc.updated_at
                            } for acc in (website.accounts or [])]
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': '网站不存在'
                    }), 404
                
            except Exception as e:
                self.logger.error(f"获取网站失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.blueprint.route('/api/websites/search', methods=['POST'])
        def search_websites():
            """语义搜索网站"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': '请提供搜索数据'
                    }), 400
                
                query = data.get('query', '').strip()
                if not query:
                    return jsonify({
                        'success': False,
                        'error': '搜索查询不能为空'
                    }), 400
                
                tags = data.get('tags', [])
                
                # 执行搜索（目前使用基础文本搜索，后续可扩展为语义搜索）
                websites = self.websites_manager.search_websites(query, tags)
                
                # 转换为字典格式
                websites_data = []
                for website in websites:
                    website_dict = {
                        'id': website.id,
                        'url': website.url,
                        'title': website.title,
                        'description': website.description,
                        'tags': website.tags,
                        'favicon_url': website.favicon_url,
                        'created_at': website.created_at,
                        'updated_at': website.updated_at,
                        'visit_count': website.visit_count,
                        'last_visited': website.last_visited,
                        'accounts': [{
                            'id': acc.id,
                            'username': acc.username,
                            'description': acc.notes,
                            'created_at': acc.created_at,
                            'updated_at': acc.updated_at
                        } for acc in (website.accounts or [])]
                    }
                    websites_data.append(website_dict)
                
                return jsonify({
                    'success': True,
                    'data': websites_data,
                    'total': len(websites_data),
                    'query': query
                })
                
            except Exception as e:
                self.logger.error(f"搜索网站失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.blueprint.route('/api/websites/<int:website_id>/visit', methods=['POST'])
        def record_visit(website_id):
            """记录网站访问"""
            try:
                # 检查网站是否存在
                existing_website = self.websites_manager.get_website(website_id)
                if not existing_website:
                    return jsonify({
                        'success': False,
                        'error': '网站不存在'
                    }), 404
                
                # 记录访问
                success = self.websites_manager.record_visit(website_id)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': '访问记录成功'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': '记录访问失败'
                    }), 500
                
            except Exception as e:
                self.logger.error(f"记录访问失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.blueprint.route('/api/websites/tags', methods=['GET'])
        def get_tags():
            """获取所有标签"""
            try:
                tags = self.websites_manager.get_all_tags()
                return jsonify({
                    'success': True,
                    'data': tags
                })
                
            except Exception as e:
                self.logger.error(f"获取标签失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.blueprint.route('/api/websites/export', methods=['GET'])
        def export_websites():
            """导出网站数据"""
            try:
                websites_data = self.websites_manager.export_websites()
                return jsonify({
                    'success': True,
                    'data': websites_data,
                    'total': len(websites_data)
                })
                
            except Exception as e:
                self.logger.error(f"导出网站数据失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.blueprint.route('/api/websites/import', methods=['POST'])
        def import_websites():
            """导入网站数据"""
            try:
                data = request.get_json()
                if not data or 'websites' not in data:
                    return jsonify({
                        'success': False,
                        'error': '请提供网站数据'
                    }), 400
                
                websites_data = data['websites']
                if not isinstance(websites_data, list):
                    return jsonify({
                        'success': False,
                        'error': '网站数据格式错误'
                    }), 400
                
                imported_count = self.websites_manager.import_websites(websites_data)
                
                return jsonify({
                    'success': True,
                    'message': f'成功导入 {imported_count} 个网站',
                    'imported_count': imported_count,
                    'total_provided': len(websites_data)
                })
                
            except Exception as e:
                self.logger.error(f"导入网站数据失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.blueprint.route('/api/websites/<int:website_id>/accounts', methods=['GET'])
        def get_website_accounts(website_id):
            """获取网站账号列表"""
            try:
                # 检查网站是否存在
                existing_website = self.websites_manager.get_website(website_id)
                if not existing_website:
                    return jsonify({
                        'success': False,
                        'error': '网站不存在'
                    }), 404
                
                accounts = self.websites_manager.get_website_accounts(website_id)
                
                accounts_data = [{
                    'id': acc.id,
                    'username': acc.username,
                    'description': acc.notes,
                    'created_at': acc.created_at,
                    'updated_at': acc.updated_at
                } for acc in accounts]
                
                return jsonify({
                    'success': True,
                    'data': accounts_data,
                    'total': len(accounts_data)
                })
                
            except Exception as e:
                self.logger.error(f"获取网站账号失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.blueprint.route('/api/websites/<int:website_id>/accounts', methods=['POST'])
        def add_website_account(website_id):
            """添加网站账号"""
            try:
                # 检查网站是否存在
                existing_website = self.websites_manager.get_website(website_id)
                if not existing_website:
                    return jsonify({
                        'success': False,
                        'error': '网站不存在'
                    }), 404
                
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': '请提供账号数据'
                    }), 400
                
                username = data.get('username', '').strip()
                if not username:
                    return jsonify({
                        'success': False,
                        'error': '用户名是必需的'
                    }), 400
                
                # 创建账号对象
                account = WebsiteAccount(
                    username=username,
                    notes=data.get('notes', '').strip()
                )
                
                # 添加账号
                account_id = self.websites_manager.add_website_account(website_id, account)
                
                # 获取完整的账号信息
                accounts = self.websites_manager.get_website_accounts(website_id)
                created_account = next((acc for acc in accounts if acc.id == account_id), None)
                
                if created_account:
                    return jsonify({
                        'success': True,
                        'data': {
                            'id': created_account.id,
                            'username': created_account.username,
                            'description': created_account.notes,
                            'created_at': created_account.created_at,
                            'updated_at': created_account.updated_at
                        },
                        'message': '账号添加成功'
                    }), 201
                else:
                    return jsonify({
                        'success': False,
                        'error': '添加账号失败'
                    }), 500
                
            except ValueError as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 400
            except Exception as e:
                self.logger.error(f"添加网站账号失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.blueprint.route('/api/websites/<int:website_id>/accounts/<account_id>', methods=['PUT'])
        def update_website_account(website_id, account_id):
            """更新网站账号"""
            try:
                # 检查网站是否存在
                existing_website = self.websites_manager.get_website(website_id)
                if not existing_website:
                    return jsonify({
                        'success': False,
                        'error': '网站不存在'
                    }), 404
                
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': '请提供更新数据'
                    }), 400
                
                # 准备更新数据
                update_data = {}
                if 'username' in data:
                    username = data['username'].strip()
                    if not username:
                        return jsonify({
                            'success': False,
                            'error': '用户名不能为空'
                        }), 400
                    update_data['username'] = username
                
                if 'notes' in data:
                    update_data['notes'] = data['notes'].strip()
                
                # 执行更新
                success = self.websites_manager.update_website_account(website_id, account_id, **update_data)
                
                if success:
                    # 获取更新后的账号信息
                    accounts = self.websites_manager.get_website_accounts(website_id)
                    updated_account = next((acc for acc in accounts if acc.id == account_id), None)
                    
                    if updated_account:
                        return jsonify({
                            'success': True,
                            'data': {
                                'id': updated_account.id,
                                'username': updated_account.username,
                                'description': updated_account.notes,
                                'created_at': updated_account.created_at,
                                'updated_at': updated_account.updated_at
                            },
                            'message': '账号更新成功'
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': '账号不存在'
                        }), 404
                else:
                    return jsonify({
                        'success': False,
                        'error': '更新失败'
                    }), 500
                
            except Exception as e:
                self.logger.error(f"更新网站账号失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.blueprint.route('/api/websites/<int:website_id>/accounts/<account_id>', methods=['DELETE'])
        def delete_website_account(website_id, account_id):
            """删除网站账号"""
            try:
                # 检查网站是否存在
                existing_website = self.websites_manager.get_website(website_id)
                if not existing_website:
                    return jsonify({
                        'success': False,
                        'error': '网站不存在'
                    }), 404
                
                # 执行删除
                success = self.websites_manager.delete_website_account(website_id, account_id)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': '账号删除成功'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': '删除失败或账号不存在'
                    }), 404
                
            except Exception as e:
                self.logger.error(f"删除网站账号失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    def get_blueprint(self):
        """获取Blueprint对象"""
        return self.blueprint