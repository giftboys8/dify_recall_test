/**
 * 网站管理页面JavaScript
 * 提供网站的增删改查、搜索、标签管理等功能
 */

class WebsitesManager {
    constructor() {
        this.websites = [];
        this.allTags = [];
        this.currentEditId = null;
        this.pagination = {
            page: 1,
            pageSize: 20,
            total: 0,
            totalPages: 0
        };
        this.currentQuery = {
            search: '',
            tags: []
        };
        this.init();
    }

    /**
     * 初始化
     */
    init() {
        // 确保分页控制区域初始状态正确
        const paginationControls = document.getElementById('paginationControls');
        if (paginationControls) {
            paginationControls.style.display = 'none';
        }
        
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

        // 页面大小选择器变化事件
        document.getElementById('pageSizeSelect').addEventListener('change', (e) => {
            this.pagination.pageSize = parseInt(e.target.value);
            this.pagination.page = 1; // 重置到第一页
            this.loadWebsites();
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
        const dropdown = container.querySelector('.existing-tags-dropdown');
        
        // 输入事件处理
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const tag = input.value.trim();
                if (tag && !this.hasTag(container, tag)) {
                    this.addTag(container, tag);
                    input.value = '';
                    this.hideTagsDropdown(container);
                    this.updateQuickTags(containerId);
                }
            }
        });
        
        // 输入框获得焦点时显示下拉列表
        input.addEventListener('focus', () => {
            this.showTagsDropdown(container);
        });
        
        // 输入框失去焦点时延迟隐藏下拉列表（允许点击下拉项）
        input.addEventListener('blur', () => {
            setTimeout(() => {
                this.hideTagsDropdown(container);
            }, 200);
        });
        
        // 输入内容变化时过滤标签
        input.addEventListener('input', () => {
            this.filterExistingTags(container, input.value.trim());
        });
        
        // 初始化快速标签
        this.updateQuickTags(containerId);
    }
    
    /**
     * 显示已有标签下拉列表
     */
    showTagsDropdown(container) {
        const dropdown = container.querySelector('.existing-tags-dropdown');
        const input = container.querySelector('.tag-input');
        
        this.renderExistingTags(container);
        dropdown.style.display = 'block';
        this.filterExistingTags(container, input.value.trim());
    }
    
    /**
     * 隐藏已有标签下拉列表
     */
    hideTagsDropdown(container) {
        const dropdown = container.querySelector('.existing-tags-dropdown');
        dropdown.style.display = 'none';
    }
    
    /**
     * 渲染已有标签列表
     */
    renderExistingTags(container) {
        const tagsList = container.querySelector('.existing-tags-list');
        const currentTags = this.getTags(container);
        
        tagsList.innerHTML = '';
        
        if (this.allTags.length === 0) {
            tagsList.innerHTML = '<div class="text-muted text-center py-2">暂无已有标签</div>';
            return;
        }
        
        this.allTags.forEach(tag => {
            const isDisabled = currentTags.includes(tag);
            const tagButton = document.createElement('button');
            tagButton.className = `existing-tag-item ${isDisabled ? 'disabled' : ''}`;
            tagButton.textContent = tag;
            tagButton.disabled = isDisabled;
            
            if (!isDisabled) {
                tagButton.addEventListener('click', () => {
                    this.addTag(container, tag);
                    this.hideTagsDropdown(container);
                    this.updateQuickTags(container.id);
                    container.querySelector('.tag-input').focus();
                });
            }
            
            tagsList.appendChild(tagButton);
        });
    }
    
    /**
     * 过滤已有标签
     */
    filterExistingTags(container, searchText) {
        const tagsList = container.querySelector('.existing-tags-list');
        const tagItems = tagsList.querySelectorAll('.existing-tag-item');
        
        tagItems.forEach(item => {
            const tagText = item.textContent.toLowerCase();
            const matches = tagText.includes(searchText.toLowerCase());
            item.style.display = matches ? 'block' : 'none';
        });
    }
    
    /**
     * 更新快速标签按钮
     */
    updateQuickTags(containerId) {
        const container = document.getElementById(containerId);
        const quickTagsId = containerId === 'websiteTagsInput' ? 'quickTagsAdd' : 'quickTagsEdit';
        const quickTagsContainer = document.getElementById(quickTagsId);
        const currentTags = this.getTags(container);
        
        if (!quickTagsContainer) return;
        
        quickTagsContainer.innerHTML = '';
        
        // 获取最常用的标签（按使用频率排序）
        const tagFrequency = {};
        this.websites.forEach(website => {
            if (website.tags && Array.isArray(website.tags)) {
                website.tags.forEach(tag => {
                    tagFrequency[tag] = (tagFrequency[tag] || 0) + 1;
                });
            }
        });
        
        const sortedTags = Object.entries(tagFrequency)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 8) // 显示前8个最常用标签
            .map(([tag]) => tag);
        
        if (sortedTags.length === 0) {
            quickTagsContainer.innerHTML = '<small class="text-muted">暂无常用标签</small>';
            return;
        }
        
        sortedTags.forEach(tag => {
            const isDisabled = currentTags.includes(tag);
            const tagButton = document.createElement('button');
            tagButton.className = `quick-tag ${isDisabled ? 'disabled' : ''}`;
            tagButton.textContent = tag;
            tagButton.disabled = isDisabled;
            tagButton.type = 'button';
            
            if (!isDisabled) {
                tagButton.addEventListener('click', () => {
                    this.addTag(container, tag);
                    this.updateQuickTags(containerId);
                    container.querySelector('.tag-input').focus();
                });
            }
            
            quickTagsContainer.appendChild(tagButton);
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
            <span class="tag-remove" onclick="this.parentElement.remove(); websitesManager.updateQuickTags('${container.id}'); websitesManager.renderExistingTags(document.getElementById('${container.id}'));">
                <i class="bi bi-x"></i>
            </span>
        `;
        
        const input = container.querySelector('.tag-input');
        container.insertBefore(tagItem, input);
        
        // 更新快速标签和下拉列表状态
        this.updateQuickTags(container.id);
        if (container.querySelector('.existing-tags-dropdown').style.display === 'block') {
            this.renderExistingTags(container);
        }
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
    async loadWebsites(page = 1, resetPagination = true) {
        try {
            this.showLoading();
            
            // 构建请求URL
            const params = new URLSearchParams();
            params.append('limit', this.pagination.pageSize);
            params.append('offset', (page - 1) * this.pagination.pageSize);
            
            if (this.currentQuery.search) {
                params.append('q', this.currentQuery.search);
            }
            
            this.currentQuery.tags.forEach(tag => {
                params.append('tags', tag);
            });
            
            const response = await fetch(`/api/websites?${params.toString()}`);
            const result = await response.json();
            
            if (result.success) {
                this.websites = result.data;
                
                if (resetPagination && result.pagination) {
                    this.pagination = {
                        page: result.pagination.page,
                        pageSize: result.pagination.page_size,
                        total: result.pagination.total,
                        totalPages: result.pagination.total_pages
                    };
                }
                
                // 批量更新DOM，避免闪跳
                requestAnimationFrame(() => {
                    this.renderWebsites(this.websites);
                    this.renderPagination();
                    this.updateStats();
                });
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
        
        tbody.innerHTML = websites.map(website => {
            // 字符截断函数
            const truncateText = (text, maxLength) => {
                if (!text) return '';
                return text.length > maxLength ? text.substring(0, maxLength) : text;
            };
            
            const title = website.title || '未知标题';
            const url = website.url || '';
            const description = website.description || '暂无描述';
            
            const truncatedTitle = truncateText(title, 8);
            const truncatedUrl = truncateText(url, 30);
            const truncatedDescription = truncateText(description, 10);
            
            return `
            <tr>
                <td>
                    <img src="${website.favicon_url || '/static/images/default-favicon.png'}" 
                         class="website-favicon" 
                         onerror="this.src='/static/images/default-favicon.png'" 
                         alt="favicon">
                </td>
                <td>
                    <div class="website-title expandable-content content-collapsed" 
                         data-full-text="${this.escapeHtml(title)}" 
                         data-truncated="${this.escapeHtml(truncatedTitle)}">
                        <span class="content-text">${this.escapeHtml(truncatedTitle)}</span>${title.length > 8 ? '<span class="expand-toggle" onclick="websitesManager.toggleContent(this)">...</span>' : ''}
                    </div>
                </td>
                <td>
                    <div class="website-url expandable-content content-collapsed" 
                         data-full-text="${this.escapeHtml(url)}" 
                         data-truncated="${this.escapeHtml(truncatedUrl)}">
                        <span class="content-text">
                            <a href="${url}" target="_blank" 
                               onclick="websitesManager.recordVisit(${website.id})">
                                ${this.escapeHtml(truncatedUrl)}
                            </a>
                        </span>${url.length > 30 ? '<span class="expand-toggle" onclick="websitesManager.toggleContent(this)">...</span>' : ''}
                    </div>
                </td>
                <td>
                    <div class="website-description expandable-content content-collapsed" 
                         data-full-text="${this.escapeHtml(description)}" 
                         data-truncated="${this.escapeHtml(truncatedDescription)}">
                        <span class="content-text">${this.escapeHtml(truncatedDescription)}</span>${description.length > 10 ? '<span class="expand-toggle" onclick="websitesManager.toggleContent(this)">...</span>' : ''}
                    </div>
                </td>
                <td>
                    ${website.tags.map(tag => 
                        `<span class="badge bg-secondary tag-badge">${this.escapeHtml(tag)}</span>`
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
                            <button class="btn btn-outline-info" 
                                    onclick="websitesManager.manageAccounts(${website.id})" 
                                    title="账号管理" 
                                    aria-label="管理账号">
                                <i class="bi bi-person-gear"></i>
                            </button>
                            <button class="btn btn-outline-primary" 
                                    onclick="websitesManager.editWebsite(${website.id})" 
                                    title="编辑" 
                                    aria-label="编辑网站">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-success" 
                                    onclick="websitesManager.visitWebsite('${this.escapeHtml(website.url)}', ${website.id})" 
                                    title="访问" 
                                    aria-label="访问网站">
                                <i class="bi bi-box-arrow-up-right"></i>
                            </button>
                            <button class="btn btn-outline-danger" 
                                    onclick="websitesManager.deleteWebsite(${website.id})" 
                                    title="删除" 
                                    aria-label="删除网站">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </td>
            </tr>
            `;
        }).join('');
    }
    
    /**
     * 切换内容展开/收起状态
     */
    toggleContent(toggleElement) {
        const container = toggleElement.closest('.expandable-content');
        const contentText = container.querySelector('.content-text');
        const fullText = container.getAttribute('data-full-text');
        const truncatedText = container.getAttribute('data-truncated');
        
        if (container.classList.contains('content-collapsed')) {
            // 展开内容
            container.classList.remove('content-collapsed');
            container.classList.add('content-expanded');
            
            // 更新内容和切换按钮
            if (container.classList.contains('website-url')) {
                // URL特殊处理，保持链接功能
                const link = contentText.querySelector('a');
                if (link) {
                    link.textContent = fullText;
                }
            } else {
                contentText.textContent = fullText;
            }
            toggleElement.textContent = '收起';
        } else {
            // 收起内容
            container.classList.remove('content-expanded');
            container.classList.add('content-collapsed');
            
            // 恢复截断内容和切换按钮
            if (container.classList.contains('website-url')) {
                // URL特殊处理，保持链接功能
                const link = contentText.querySelector('a');
                if (link) {
                    link.textContent = truncatedText;
                }
            } else {
                contentText.textContent = truncatedText;
            }
            toggleElement.textContent = '...';
        }
    }

    /**
     * 渲染分页控件
     */
    renderPagination() {
        const paginationContainer = document.getElementById('paginationContainer');
        const paginationControls = document.getElementById('paginationControls');
        const paginationInfo = document.getElementById('paginationInfo');
        const pageSizeSelect = document.getElementById('pageSizeSelect');
        
        if (!paginationContainer) return;
        
        const { page, totalPages, total, pageSize } = this.pagination;
        
        // 更新页面大小选择器的值
        if (pageSizeSelect) {
            pageSizeSelect.value = pageSize.toString();
        }
        
        // 显示/隐藏分页控制区域
        if (paginationControls) {
            const shouldShow = total > 0;
            const currentDisplay = paginationControls.style.display;
            const isCurrentlyVisible = currentDisplay === 'flex' || (currentDisplay === '' && total > 0);
            
            if (shouldShow && !isCurrentlyVisible) {
                paginationControls.style.display = 'flex';
            } else if (!shouldShow && isCurrentlyVisible) {
                paginationControls.style.display = 'none';
            }
        }
        
        // 更新分页信息
        if (paginationInfo && total > 0) {
            const startItem = (page - 1) * pageSize + 1;
            const endItem = Math.min(page * pageSize, total);
            paginationInfo.innerHTML = `显示第 ${startItem} - ${endItem} 条，共 ${total} 条记录`;
        }
        
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }
        
        let paginationHtml = '<nav aria-label="网站列表分页">';
        paginationHtml += '<ul class="pagination justify-content-center mb-0">';
        
        // 上一页按钮
         paginationHtml += `
             <li class="page-item ${page <= 1 ? 'disabled' : ''}">
                 <a class="page-link" href="#" onclick="websitesManager.goToPage(${page - 1}); return false;">
                     <i class="bi bi-chevron-left"></i> 上一页
                 </a>
             </li>
         `;
        
        // 页码按钮
        const startPage = Math.max(1, page - 2);
        const endPage = Math.min(totalPages, page + 2);
        
        if (startPage > 1) {
            paginationHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="websitesManager.goToPage(1); return false;">1</a>
                </li>
            `;
            if (startPage > 2) {
                paginationHtml += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            paginationHtml += `
                <li class="page-item ${i === page ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="websitesManager.goToPage(${i}); return false;">${i}</a>
                </li>
            `;
        }
        
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                paginationHtml += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
            paginationHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="websitesManager.goToPage(${totalPages}); return false;">${totalPages}</a>
                </li>
            `;
        }
        
        // 下一页按钮
         paginationHtml += `
             <li class="page-item ${page >= totalPages ? 'disabled' : ''}">
                 <a class="page-link" href="#" onclick="websitesManager.goToPage(${page + 1}); return false;">
                     下一页 <i class="bi bi-chevron-right"></i>
                 </a>
             </li>
         `;
        
        paginationHtml += '</ul>';
        paginationHtml += '</nav>';
        
        paginationContainer.innerHTML = paginationHtml;
    }

    /**
     * 跳转到指定页面
     */
    async goToPage(page) {
        if (page < 1 || page > this.pagination.totalPages || page === this.pagination.page) {
            return;
        }
        
        this.pagination.page = page;
        await this.loadWebsites(page, false);
    }

    /**
     * 更新统计信息
     */
    updateStats() {
        // 添加空值检查，防止DOM元素不存在时出错
        const totalWebsitesEl = document.getElementById('totalWebsites');
        const totalTagsEl = document.getElementById('totalTags');
        const totalVisitsEl = document.getElementById('totalVisits');
        const recentlyAddedEl = document.getElementById('recentlyAdded');
        
        if (totalWebsitesEl) {
            // 使用分页信息中的总数，如果没有则使用当前页面的数据
            const totalWebsites = this.pagination.total || this.websites.length;
            totalWebsitesEl.textContent = totalWebsites;
        }
        
        if (totalTagsEl) {
            totalTagsEl.textContent = this.allTags.length;
        }
        
        if (totalVisitsEl) {
            // 计算总访问次数
            const totalVisits = this.websites.reduce((sum, website) => {
                return sum + (website.visit_count || 0);
            }, 0);
            totalVisitsEl.textContent = totalVisits;
        }
        
        if (recentlyAddedEl) {
            // 计算最近添加（7天内）
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            const recentAdded = this.websites.filter(website => {
                return new Date(website.created_at) > weekAgo;
            }).length;
            recentlyAddedEl.textContent = recentAdded;
        }
    }

    /**
     * 执行搜索
     */
    async performSearch() {
        const query = document.getElementById('searchInput').value.trim();
        const selectedTags = Array.from(document.getElementById('tagFilter').selectedOptions)
                                 .map(option => option.value);
        
        // 更新当前查询条件
        this.currentQuery.search = query;
        this.currentQuery.tags = selectedTags;
        
        // 重置到第一页并加载数据
        await this.loadWebsites(1, true);
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
        const accounts = this.getAccountsFromForm('add');
        
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
                    favicon_url: favicon,
                    accounts: accounts
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
        
        // 加载账号数据
        this.loadAccountsToForm(website.accounts || [], 'edit');
        
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
        const accounts = this.getAccountsFromForm('edit');
        
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
                    favicon_url: favicon,
                    accounts: accounts
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
        this.clearAccountsFromForm('add');
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

    /**
     * HTML转义
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 表单中的账号管理
     */
    addAccountToForm(formType) {
        const usernameId = formType === 'add' ? 'addAccountUsername' : 'editAccountUsername';
        const descriptionId = formType === 'add' ? 'addAccountDescription' : 'editAccountDescription';
        const listId = formType === 'add' ? 'addWebsiteAccountsList' : 'editWebsiteAccountsList';
        
        const usernameElement = document.getElementById(usernameId);
        const descriptionElement = document.getElementById(descriptionId);
        const accountsList = document.getElementById(listId);
        
        if (!usernameElement || !descriptionElement || !accountsList) {
            console.warn('Required form elements not found');
            return;
        }
        
        const username = usernameElement.value.trim();
        const description = descriptionElement.value.trim();
        
        if (!username) {
            this.showError('请输入用户名');
            return;
        }
        
        const accountIndex = accountsList.children.length;
        
        const accountItem = document.createElement('div');
        accountItem.className = 'account-item d-flex justify-content-between align-items-center mb-2 p-2 border rounded';
        accountItem.innerHTML = `
            <div>
                <strong>${this.escapeHtml(username)}</strong>
                ${description ? `<small class="text-muted d-block">${this.escapeHtml(description)}</small>` : ''}
            </div>
            <button type="button" class="btn btn-outline-danger btn-sm" onclick="websitesManager.removeAccountFromForm(this, '${formType}')">
                <i class="bi bi-trash"></i>
            </button>
        `;
        accountItem.dataset.username = username;
        accountItem.dataset.notes = description;
        
        accountsList.appendChild(accountItem);
        
        // 清空输入框
        usernameElement.value = '';
        descriptionElement.value = '';
    }
    
    removeAccountFromForm(button, formType) {
        button.closest('.account-item').remove();
    }
    
    getAccountsFromForm(formType) {
        const listId = formType === 'add' ? 'addWebsiteAccountsList' : 'editWebsiteAccountsList';
        const accountsList = document.getElementById(listId);
        const accounts = [];
        
        if (!accountsList) {
            console.warn(`Element with id '${listId}' not found`);
            return accounts;
        }
        
        Array.from(accountsList.children).forEach(item => {
            accounts.push({
                username: item.dataset.username,
                notes: item.dataset.notes || ''
            });
        });
        
        return accounts;
    }
    
    clearAccountsFromForm(formType) {
        const listId = formType === 'add' ? 'addWebsiteAccountsList' : 'editWebsiteAccountsList';
        const element = document.getElementById(listId);
        if (element) {
            element.innerHTML = '';
        }
    }
    
    loadAccountsToForm(accounts, formType) {
        this.clearAccountsFromForm(formType);
        const listId = formType === 'add' ? 'addWebsiteAccountsList' : 'editWebsiteAccountsList';
        const accountsList = document.getElementById(listId);
        
        if (!accountsList) {
            console.warn(`Element with id '${listId}' not found`);
            return;
        }
        
        accounts.forEach(account => {
            const accountItem = document.createElement('div');
            accountItem.className = 'account-item d-flex justify-content-between align-items-center mb-2 p-2 border rounded';
            accountItem.innerHTML = `
                <div>
                    <strong>${this.escapeHtml(account.username)}</strong>
                    ${account.notes ? `<small class="text-muted d-block">${this.escapeHtml(account.notes)}</small>` : ''}
                </div>
                <button type="button" class="btn btn-outline-danger btn-sm" onclick="websitesManager.removeAccountFromForm(this, '${formType}')">
                    <i class="bi bi-trash"></i>
                </button>
            `;
            accountItem.dataset.username = account.username;
            accountItem.dataset.notes = account.notes || '';
            
            accountsList.appendChild(accountItem);
        });
    }
    /**
     * 管理网站账号
     */
    async manageAccounts(websiteId) {
        const website = this.websites.find(w => w.id === websiteId);
        if (!website) {
            this.showError('网站不存在');
            return;
        }
        
        this.currentWebsiteId = websiteId;
        
        // 设置模态框标题
        document.getElementById('accountsModalLabel').textContent = `管理账号 - ${website.title || website.url}`;
        
        // 加载账号列表
        await this.loadWebsiteAccounts(websiteId);
        
        // 显示模态框
        new bootstrap.Modal(document.getElementById('accountsModal')).show();
    }

    /**
     * 加载网站账号列表
     */
    async loadWebsiteAccounts(websiteId) {
        try {
            const response = await fetch(`/api/websites/${websiteId}/accounts`);
            const result = await response.json();
            
            if (result.success) {
                this.renderAccountsList(result.data);
            } else {
                this.showError('加载账号列表失败: ' + result.error);
            }
        } catch (error) {
            console.error('加载账号列表失败:', error);
            this.showError('加载账号列表失败: ' + error.message);
        }
    }

    /**
     * 渲染账号列表
     */
    renderAccountsList(accounts) {
        const tbody = document.getElementById('accountsTableBody');
        const emptyState = document.getElementById('accountsEmptyState');
        
        if (accounts.length === 0) {
            tbody.innerHTML = '';
            emptyState.style.display = 'block';
            return;
        }
        
        emptyState.style.display = 'none';
        
        tbody.innerHTML = accounts.map(account => `
            <tr>
                <td>
                    <div class="account-username" title="${account.username}">
                        ${account.username}
                    </div>
                </td>
                <td>
                    <div class="account-description" title="${account.notes || ''}">
                        ${account.notes || '暂无描述'}
                    </div>
                </td>
                <td>
                    <div class="account-created">
                        ${new Date(account.created_at).toLocaleDateString()}
                    </div>
                </td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-primary" 
                                onclick="websitesManager.editAccount('${account.id}')" 
                                title="编辑" 
                                aria-label="编辑账号">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger" 
                                onclick="websitesManager.deleteAccount('${account.id}')" 
                                title="删除" 
                                aria-label="删除账号">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    /**
     * 添加账号
     */
    async addAccount() {
        const username = document.getElementById('accountUsername').value.trim();
        const description = document.getElementById('accountDescription').value.trim();
        
        if (!username) {
            this.showError('请输入用户名');
            return;
        }
        
        try {
            const response = await fetch(`/api/websites/${this.currentWebsiteId}/accounts`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    notes: description
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('账号添加成功');
                this.clearAccountForm();
                await this.loadWebsiteAccounts(this.currentWebsiteId);
            } else {
                this.showError('添加失败: ' + result.error);
            }
        } catch (error) {
            console.error('添加账号失败:', error);
            this.showError('添加失败: ' + error.message);
        }
    }

    /**
     * 编辑账号
     */
    async editAccount(accountId) {
        try {
            const response = await fetch(`/api/websites/${this.currentWebsiteId}/accounts`);
            const result = await response.json();
            
            if (result.success) {
                const account = result.data.find(acc => acc.id === accountId);
                if (!account) {
                    this.showError('账号不存在');
                    return;
                }
                
                this.currentEditAccountId = accountId;
                
                // 填充表单
                document.getElementById('editAccountUsername').value = account.username;
                document.getElementById('editAccountDescription').value = account.notes || '';
                
                // 显示编辑模态框
                new bootstrap.Modal(document.getElementById('editAccountModal')).show();
            } else {
                this.showError('获取账号信息失败: ' + result.error);
            }
        } catch (error) {
            console.error('获取账号信息失败:', error);
            this.showError('获取账号信息失败: ' + error.message);
        }
    }

    /**
     * 更新账号
     */
    async updateAccount() {
        const username = document.getElementById('editAccountUsername').value.trim();
        const description = document.getElementById('editAccountDescription').value.trim();
        
        if (!username) {
            this.showError('请输入用户名');
            return;
        }
        
        try {
            const response = await fetch(`/api/websites/${this.currentWebsiteId}/accounts/${this.currentEditAccountId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    notes: description
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('账号更新成功');
                bootstrap.Modal.getInstance(document.getElementById('editAccountModal')).hide();
                await this.loadWebsiteAccounts(this.currentWebsiteId);
            } else {
                this.showError('更新失败: ' + result.error);
            }
        } catch (error) {
            console.error('更新账号失败:', error);
            this.showError('更新失败: ' + error.message);
        }
    }

    /**
     * 删除账号
     */
    async deleteAccount(accountId) {
        if (!confirm('确定要删除这个账号吗？')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/websites/${this.currentWebsiteId}/accounts/${accountId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('账号删除成功');
                await this.loadWebsiteAccounts(this.currentWebsiteId);
            } else {
                this.showError('删除失败: ' + result.error);
            }
        } catch (error) {
            console.error('删除账号失败:', error);
            this.showError('删除失败: ' + error.message);
        }
    }

    /**
     * 清空账号表单
     */
    clearAccountForm() {
        document.getElementById('accountUsername').value = '';
        document.getElementById('accountDescription').value = '';
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