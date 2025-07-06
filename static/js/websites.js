/**
 * 网站管理页面JavaScript
 * 提供网站的增删改查、搜索、标签管理等功能
 */

class WebsitesManager {
    constructor() {
        this.websites = [];
        this.allTags = [];
        this.currentEditId = null;
        this.init();
    }

    /**
     * 初始化
     */
    init() {
        this.loadWebsites();
        this.loadTags();
        this.setupEventListeners();
        this.setupTagsInput();
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 搜索输入框回车事件
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });

        // 标签筛选变化事件
        document.getElementById('tagFilter').addEventListener('change', () => {
            this.performSearch();
        });

        // 添加网站表单提交
        document.getElementById('addWebsiteForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addWebsite();
        });

        // 编辑网站表单提交
        document.getElementById('editWebsiteForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.updateWebsite();
        });
    }

    /**
     * 设置标签输入功能
     */
    setupTagsInput() {
        this.setupTagsInputForElement('websiteTagsInput');
        this.setupTagsInputForElement('editWebsiteTagsInput');
    }

    /**
     * 为指定元素设置标签输入功能
     */
    setupTagsInputForElement(containerId) {
        const container = document.getElementById(containerId);
        const input = container.querySelector('.tag-input');
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const tag = input.value.trim();
                if (tag && !this.hasTag(container, tag)) {
                    this.addTag(container, tag);
                    input.value = '';
                }
            }
        });
    }

    /**
     * 检查是否已有指定标签
     */
    hasTag(container, tag) {
        const existingTags = container.querySelectorAll('.tag-item');
        for (let tagItem of existingTags) {
            if (tagItem.textContent.trim().replace('×', '').trim() === tag) {
                return true;
            }
        }
        return false;
    }

    /**
     * 添加标签
     */
    addTag(container, tag) {
        const tagItem = document.createElement('span');
        tagItem.className = 'tag-item';
        tagItem.innerHTML = `
            ${tag}
            <span class="tag-remove" onclick="this.parentElement.remove()">
                <i class="bi bi-x"></i>
            </span>
        `;
        
        const input = container.querySelector('.tag-input');
        container.insertBefore(tagItem, input);
    }

    /**
     * 获取容器中的所有标签
     */
    getTags(container) {
        const tags = [];
        const tagItems = container.querySelectorAll('.tag-item');
        tagItems.forEach(item => {
            const tag = item.textContent.trim().replace('×', '').trim();
            if (tag) {
                tags.push(tag);
            }
        });
        return tags;
    }

    /**
     * 设置容器中的标签
     */
    setTags(container, tags) {
        // 清除现有标签
        const existingTags = container.querySelectorAll('.tag-item');
        existingTags.forEach(tag => tag.remove());
        
        // 添加新标签
        tags.forEach(tag => {
            this.addTag(container, tag);
        });
    }

    /**
     * 加载网站列表
     */
    async loadWebsites() {
        try {
            this.showLoading();
            const response = await fetch('/api/websites');
            const result = await response.json();
            
            if (result.success) {
                this.websites = result.data;
                this.renderWebsites(this.websites);
                this.updateStats();
            } else {
                this.showError('加载网站列表失败: ' + result.error);
            }
        } catch (error) {
            console.error('加载网站列表失败:', error);
            this.showError('加载网站列表失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    /**
     * 加载标签列表
     */
    async loadTags() {
        try {
            const response = await fetch('/api/websites/tags');
            const result = await response.json();
            
            if (result.success) {
                this.allTags = result.data;
                this.renderTagFilter();
            }
        } catch (error) {
            console.error('加载标签列表失败:', error);
        }
    }

    /**
     * 渲染标签筛选器
     */
    renderTagFilter() {
        const tagFilter = document.getElementById('tagFilter');
        tagFilter.innerHTML = '';
        
        this.allTags.forEach(tag => {
            const option = document.createElement('option');
            option.value = tag;
            option.textContent = tag;
            tagFilter.appendChild(option);
        });
    }

    /**
     * 渲染网站列表
     */
    renderWebsites(websites) {
        const tbody = document.getElementById('websitesTableBody');
        const emptyState = document.getElementById('emptyState');
        
        if (websites.length === 0) {
            tbody.innerHTML = '';
            emptyState.style.display = 'block';
            return;
        }
        
        emptyState.style.display = 'none';
        
        tbody.innerHTML = websites.map(website => `
            <tr>
                <td>
                    <img src="${website.favicon_url || '/static/images/default-favicon.png'}" 
                         class="website-favicon" 
                         onerror="this.src='/static/images/default-favicon.png'" 
                         alt="favicon">
                </td>
                <td>
                    <div class="website-title" title="${website.title || ''}">
                        ${website.title || '未知标题'}
                    </div>
                </td>
                <td>
                    <div class="website-url" title="${website.url}">
                        <a href="${website.url}" target="_blank" 
                           onclick="websitesManager.recordVisit(${website.id})">
                            ${website.url}
                        </a>
                    </div>
                </td>
                <td>
                    <div class="website-description" title="${website.description || ''}">
                        ${website.description || '暂无描述'}
                    </div>
                </td>
                <td>
                    ${website.tags.map(tag => 
                        `<span class="badge bg-secondary tag-badge">${tag}</span>`
                    ).join('')}
                </td>
                <td>
                    <div class="visit-count">
                        <i class="bi bi-eye"></i> ${website.visit_count || 0}
                    </div>
                </td>
                <td>
                    <div class="last-visited">
                        ${website.last_visited ? 
                            new Date(website.last_visited).toLocaleDateString() : 
                            '从未访问'
                        }
                    </div>
                </td>
                <td>
                    <div class="action-buttons">
                        <div class="btn-group btn-group-sm" role="group">
                            <button class="btn btn-outline-primary" 
                                    onclick="websitesManager.editWebsite(${website.id})" 
                                    title="编辑">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-success" 
                                    onclick="websitesManager.visitWebsite('${website.url}', ${website.id})" 
                                    title="访问">
                                <i class="bi bi-box-arrow-up-right"></i>
                            </button>
                            <button class="btn btn-outline-danger" 
                                    onclick="websitesManager.deleteWebsite(${website.id})" 
                                    title="删除">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    /**
     * 更新统计信息
     */
    updateStats() {
        document.getElementById('totalWebsites').textContent = this.websites.length;
        document.getElementById('totalTags').textContent = this.allTags.length;
        
        // 计算今日访问量（简化版本）
        const today = new Date().toDateString();
        const todayVisits = this.websites.filter(website => {
            if (!website.last_visited) return false;
            return new Date(website.last_visited).toDateString() === today;
        }).length;
        document.getElementById('todayVisits').textContent = todayVisits;
        
        // 计算最近添加（7天内）
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        const recentAdded = this.websites.filter(website => {
            return new Date(website.created_at) > weekAgo;
        }).length;
        document.getElementById('recentAdded').textContent = recentAdded;
    }

    /**
     * 执行搜索
     */
    async performSearch() {
        const query = document.getElementById('searchInput').value.trim();
        const selectedTags = Array.from(document.getElementById('tagFilter').selectedOptions)
                                 .map(option => option.value);
        
        if (!query && selectedTags.length === 0) {
            this.renderWebsites(this.websites);
            return;
        }
        
        try {
            this.showLoading();
            
            let url = '/api/websites?';
            const params = new URLSearchParams();
            
            if (query) {
                params.append('q', query);
            }
            
            selectedTags.forEach(tag => {
                params.append('tags', tag);
            });
            
            url += params.toString();
            
            const response = await fetch(url);
            const result = await response.json();
            
            if (result.success) {
                this.renderWebsites(result.data);
            } else {
                this.showError('搜索失败: ' + result.error);
            }
        } catch (error) {
            console.error('搜索失败:', error);
            this.showError('搜索失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    /**
     * 清除搜索
     */
    clearSearch() {
        document.getElementById('searchInput').value = '';
        document.getElementById('tagFilter').selectedIndex = -1;
        this.renderWebsites(this.websites);
    }

    /**
     * 添加网站
     */
    async addWebsite() {
        const url = document.getElementById('websiteUrl').value.trim();
        const title = document.getElementById('websiteTitle').value.trim();
        const description = document.getElementById('websiteDescription').value.trim();
        const favicon = document.getElementById('websiteFavicon').value.trim();
        const tagsContainer = document.getElementById('websiteTagsInput');
        const tags = this.getTags(tagsContainer);
        
        if (!url) {
            this.showError('请输入网站URL');
            return;
        }
        
        try {
            const response = await fetch('/api/websites', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: url,
                    title: title,
                    description: description,
                    tags: tags,
                    favicon_url: favicon
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('网站添加成功');
                this.clearAddForm();
                bootstrap.Modal.getInstance(document.getElementById('addWebsiteModal')).hide();
                await this.loadWebsites();
                await this.loadTags();
            } else {
                this.showError('添加失败: ' + result.error);
            }
        } catch (error) {
            console.error('添加网站失败:', error);
            this.showError('添加失败: ' + error.message);
        }
    }

    /**
     * 编辑网站
     */
    editWebsite(id) {
        const website = this.websites.find(w => w.id === id);
        if (!website) {
            this.showError('网站不存在');
            return;
        }
        
        this.currentEditId = id;
        
        // 填充表单
        document.getElementById('editWebsiteId').value = id;
        document.getElementById('editWebsiteUrl').value = website.url;
        document.getElementById('editWebsiteTitle').value = website.title || '';
        document.getElementById('editWebsiteDescription').value = website.description || '';
        document.getElementById('editWebsiteFavicon').value = website.favicon_url || '';
        
        // 设置标签
        const tagsContainer = document.getElementById('editWebsiteTagsInput');
        this.setTags(tagsContainer, website.tags || []);
        
        // 显示模态框
        new bootstrap.Modal(document.getElementById('editWebsiteModal')).show();
    }

    /**
     * 更新网站
     */
    async updateWebsite() {
        const id = this.currentEditId;
        const url = document.getElementById('editWebsiteUrl').value.trim();
        const title = document.getElementById('editWebsiteTitle').value.trim();
        const description = document.getElementById('editWebsiteDescription').value.trim();
        const favicon = document.getElementById('editWebsiteFavicon').value.trim();
        const tagsContainer = document.getElementById('editWebsiteTagsInput');
        const tags = this.getTags(tagsContainer);
        
        if (!url) {
            this.showError('请输入网站URL');
            return;
        }
        
        try {
            const response = await fetch(`/api/websites/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: url,
                    title: title,
                    description: description,
                    tags: tags,
                    favicon_url: favicon
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('网站更新成功');
                bootstrap.Modal.getInstance(document.getElementById('editWebsiteModal')).hide();
                await this.loadWebsites();
                await this.loadTags();
            } else {
                this.showError('更新失败: ' + result.error);
            }
        } catch (error) {
            console.error('更新网站失败:', error);
            this.showError('更新失败: ' + error.message);
        }
    }

    /**
     * 删除网站
     */
    async deleteWebsite(id) {
        if (!confirm('确定要删除这个网站吗？')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/websites/${id}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('网站删除成功');
                await this.loadWebsites();
                await this.loadTags();
            } else {
                this.showError('删除失败: ' + result.error);
            }
        } catch (error) {
            console.error('删除网站失败:', error);
            this.showError('删除失败: ' + error.message);
        }
    }

    /**
     * 访问网站并记录访问
     */
    async visitWebsite(url, id) {
        // 记录访问
        try {
            await fetch(`/api/websites/${id}/visit`, {
                method: 'POST'
            });
        } catch (error) {
            console.error('记录访问失败:', error);
        }
        
        // 打开网站
        window.open(url, '_blank');
        
        // 刷新数据
        setTimeout(() => {
            this.loadWebsites();
        }, 1000);
    }

    /**
     * 记录访问（用于链接点击）
     */
    async recordVisit(id) {
        try {
            await fetch(`/api/websites/${id}/visit`, {
                method: 'POST'
            });
            
            // 延迟刷新数据
            setTimeout(() => {
                this.loadWebsites();
            }, 1000);
        } catch (error) {
            console.error('记录访问失败:', error);
        }
    }

    /**
     * 导出网站数据
     */
    async exportWebsites() {
        try {
            const response = await fetch('/api/websites/export');
            const result = await response.json();
            
            if (result.success) {
                const dataStr = JSON.stringify(result.data, null, 2);
                const dataBlob = new Blob([dataStr], {type: 'application/json'});
                
                const link = document.createElement('a');
                link.href = URL.createObjectURL(dataBlob);
                link.download = `websites_export_${new Date().toISOString().split('T')[0]}.json`;
                link.click();
                
                this.showSuccess('数据导出成功');
            } else {
                this.showError('导出失败: ' + result.error);
            }
        } catch (error) {
            console.error('导出失败:', error);
            this.showError('导出失败: ' + error.message);
        }
    }

    /**
     * 导入网站数据
     */
    async importWebsites() {
        const fileInput = document.getElementById('importFile');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showError('请选择文件');
            return;
        }
        
        try {
            const text = await file.text();
            const data = JSON.parse(text);
            
            const response = await fetch('/api/websites/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    websites: data
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess(`导入成功：${result.imported_count} 个网站`);
                bootstrap.Modal.getInstance(document.getElementById('importModal')).hide();
                await this.loadWebsites();
                await this.loadTags();
            } else {
                this.showError('导入失败: ' + result.error);
            }
        } catch (error) {
            console.error('导入失败:', error);
            this.showError('导入失败: ' + error.message);
        }
    }

    /**
     * 清空所有网站数据
     */
    async clearAllWebsites() {
        if (!confirm('确定要清空所有网站数据吗？此操作不可恢复！')) {
            return;
        }
        
        if (!confirm('请再次确认：这将删除所有网站数据！')) {
            return;
        }
        
        try {
            // 批量删除所有网站
            const deletePromises = this.websites.map(website => 
                fetch(`/api/websites/${website.id}`, { method: 'DELETE' })
            );
            
            await Promise.all(deletePromises);
            
            this.showSuccess('所有网站数据已清空');
            await this.loadWebsites();
            await this.loadTags();
        } catch (error) {
            console.error('清空数据失败:', error);
            this.showError('清空数据失败: ' + error.message);
        }
    }

    /**
     * 清空添加表单
     */
    clearAddForm() {
        document.getElementById('addWebsiteForm').reset();
        const tagsContainer = document.getElementById('websiteTagsInput');
        this.setTags(tagsContainer, []);
    }

    /**
     * 显示加载状态
     */
    showLoading() {
        document.getElementById('loadingState').style.display = 'block';
        document.getElementById('emptyState').style.display = 'none';
    }

    /**
     * 隐藏加载状态
     */
    hideLoading() {
        document.getElementById('loadingState').style.display = 'none';
    }

    /**
     * 显示成功消息
     */
    showSuccess(message) {
        this.showToast(message, 'success');
    }

    /**
     * 显示错误消息
     */
    showError(message) {
        this.showToast(message, 'error');
    }

    /**
     * 显示提示消息
     */
    showToast(message, type = 'info') {
        // 创建toast容器（如果不存在）
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }
        
        // 创建toast
        const toastId = 'toast_' + Date.now();
        const bgClass = type === 'success' ? 'bg-success' : 
                       type === 'error' ? 'bg-danger' : 'bg-info';
        
        const toastHtml = `
            <div id="${toastId}" class="toast ${bgClass} text-white" role="alert">
                <div class="toast-header ${bgClass} text-white border-0">
                    <i class="bi bi-${type === 'success' ? 'check-circle' : 
                                     type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
                    <strong class="me-auto">${type === 'success' ? '成功' : 
                                                type === 'error' ? '错误' : '提示'}</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        // 显示toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: type === 'error' ? 5000 : 3000
        });
        
        toast.show();
        
        // 自动清理
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
}

// 全局函数（供HTML调用）
let websitesManager;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    websitesManager = new WebsitesManager();
});

// 导出全局函数
window.performSearch = () => websitesManager.performSearch();
window.clearSearch = () => websitesManager.clearSearch();
window.addWebsite = () => websitesManager.addWebsite();
window.updateWebsite = () => websitesManager.updateWebsite();
window.exportWebsites = () => websitesManager.exportWebsites();
window.importWebsites = () => websitesManager.importWebsites();
window.clearAllWebsites = () => websitesManager.clearAllWebsites();