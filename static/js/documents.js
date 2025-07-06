/**
 * 文档学习平台 JavaScript
 * 实现PDF查看、标注、笔记记录等功能
 */

class DocumentLearningPlatform {
    constructor() {
        this.currentDocument = null;
        this.currentPage = 1;
        this.totalPages = 0;
        this.zoomLevel = 1.0;
        this.pdfDoc = null;
        this.annotations = [];
        this.notes = { pages: {}, bookmarks: [], progress: 0 };
        this.selectedTool = null;
        this.selectedColor = '#ffeb3b';
        this.isSelecting = false;
        this.selectionStart = null;
        this.studyStartTime = null;
        this.studyDuration = 0;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadDocuments();
        this.setupPDFJS();
        this.setupKeyboardShortcuts();
    }
    
    setupPDFJS() {
        // 设置PDF.js worker
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    }
    
    setupEventListeners() {
        // 文档上传
        document.getElementById('uploadBtn').addEventListener('click', () => this.uploadDocument());
        
        // 页面导航
        document.getElementById('prevPage').addEventListener('click', () => this.previousPage());
        document.getElementById('nextPage').addEventListener('click', () => this.nextPage());
        
        // 缩放控制
        document.getElementById('zoomIn').addEventListener('click', () => this.zoomIn());
        document.getElementById('zoomOut').addEventListener('click', () => this.zoomOut());
        document.getElementById('fitWidth').addEventListener('click', () => this.fitWidth());
        document.getElementById('fitPage').addEventListener('click', () => this.fitPage());
        
        // 全屏和演示模式
        document.getElementById('fullscreen').addEventListener('click', () => this.toggleFullscreen());
        document.getElementById('presentationMode').addEventListener('click', () => this.enterPresentationMode());
        
        // 学习工具
        document.getElementById('highlightTool').addEventListener('click', () => this.selectTool('highlight'));
        document.getElementById('noteTool').addEventListener('click', () => this.selectTool('note'));
        document.getElementById('bookmarkTool').addEventListener('click', () => this.selectTool('bookmark'));
        
        // 颜色选择
        document.querySelectorAll('.color-option').forEach(option => {
            option.addEventListener('click', (e) => this.selectColor(e.target.dataset.color));
        });
        
        // 清除标注
        document.getElementById('clearAnnotations').addEventListener('click', () => this.clearAnnotations());
        
        // 笔记功能
        document.getElementById('savePageNote').addEventListener('click', () => this.savePageNote());
        document.getElementById('addBookmark').addEventListener('click', () => this.addBookmark());
        document.getElementById('saveNote').addEventListener('click', () => this.saveNoteFromModal());
        
        // 导出功能
        document.getElementById('exportNotes').addEventListener('click', () => this.exportNotes());
        document.getElementById('clearNotes').addEventListener('click', () => this.clearNotes());
        
        // 查看器内容事件
        const viewerContent = document.getElementById('viewerContent');
        viewerContent.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        viewerContent.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        viewerContent.addEventListener('mouseup', (e) => this.handleMouseUp(e));
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            
            switch(e.key) {
                case 'ArrowLeft':
                case 'ArrowUp':
                    e.preventDefault();
                    this.previousPage();
                    break;
                case 'ArrowRight':
                case 'ArrowDown':
                case ' ':
                    e.preventDefault();
                    this.nextPage();
                    break;
                case 'Escape':
                    e.preventDefault();
                    this.exitFullscreen();
                    break;
                case 'f':
                case 'F':
                    if (e.ctrlKey || e.metaKey) return;
                    e.preventDefault();
                    this.toggleFullscreen();
                    break;
                case '+':
                case '=':
                    e.preventDefault();
                    this.zoomIn();
                    break;
                case '-':
                    e.preventDefault();
                    this.zoomOut();
                    break;
            }
        });
    }
    
    async loadDocuments() {
        try {
            const response = await fetch('/api/documents');
            const data = await response.json();
            
            if (data.success) {
                this.renderDocumentList(data.documents);
            }
        } catch (error) {
            console.error('加载文档列表失败:', error);
            this.showMessage('加载文档列表失败', 'error');
        }
    }
    
    renderDocumentList(documents) {
        const listContainer = document.getElementById('documentList');
        
        if (documents.length === 0) {
            listContainer.innerHTML = `
                <div class="text-center text-muted p-3">
                    <i class="fas fa-folder-open fa-2x mb-2"></i>
                    <div>暂无文档</div>
                </div>
            `;
            return;
        }
        
        listContainer.innerHTML = documents.map(doc => `
            <div class="document-list-item" data-doc-id="${doc.id}">
                <div class="d-flex align-items-center" onclick="documentPlatform.loadDocument('${doc.id}')" style="flex: 1; cursor: pointer;">
                    <i class="fas fa-file-${this.getFileIcon(doc.type)} fa-2x me-3 text-primary"></i>
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${doc.name}</h6>
                        <small class="text-muted">
                            ${this.formatFileSize(doc.size)} • ${this.formatDate(doc.created)}
                        </small>
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-danger ms-2" onclick="event.stopPropagation(); documentPlatform.deleteDocument('${doc.id}', '${doc.name}')" title="删除文档">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `).join('');
    }
    
    getFileIcon(type) {
        const icons = {
            '.pdf': 'pdf',
            '.ppt': 'powerpoint',
            '.pptx': 'powerpoint',
            '.doc': 'word',
            '.docx': 'word'
        };
        return icons[type] || 'alt';
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('zh-CN');
    }
    
    async uploadDocument() {
        const fileInput = document.getElementById('documentFile');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showMessage('请选择要上传的文档', 'warning');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            this.showLoading(true);
            const response = await fetch('/api/documents', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showMessage('文档上传成功', 'success');
                fileInput.value = '';
                await this.loadDocuments();
            } else {
                this.showMessage(data.error || '上传失败', 'error');
            }
        } catch (error) {
            console.error('上传失败:', error);
            this.showMessage('上传失败', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async deleteDocument(docId, docName) {
        // 确认删除
        if (!confirm(`确定要删除文档 "${docName}" 吗？\n\n此操作将永久删除文档及其所有相关数据（笔记、书签、标注等），且无法恢复。`)) {
            return;
        }
        
        try {
            this.showLoading(true);
            const response = await fetch(`/api/documents/${encodeURIComponent(docId)}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showMessage('文档删除成功', 'success');
                
                // 如果删除的是当前正在查看的文档，清空查看器
                if (this.currentDocument === docId) {
                    this.currentDocument = null;
                    this.resetViewer();
                }
                
                // 重新加载文档列表
                await this.loadDocuments();
            } else {
                this.showMessage(data.error || '删除失败', 'error');
            }
        } catch (error) {
            console.error('删除文档失败:', error);
            this.showMessage('删除文档失败', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    resetViewer() {
        // 重置查看器状态
        const viewerContent = document.getElementById('viewerContent');
        viewerContent.innerHTML = `
            <div class="d-flex align-items-center justify-content-center h-100 text-muted">
                <div class="text-center">
                    <i class="fas fa-file-alt fa-4x mb-3"></i>
                    <h5>选择文档开始学习</h5>
                    <p>上传或选择一个文档来开始您的学习之旅</p>
                </div>
            </div>
        `;
        
        // 隐藏学习工具和页面导航
        document.getElementById('learningTools').style.display = 'none';
        document.getElementById('pageNavigation').style.display = 'none';
        
        // 清空笔记输入框
        const noteInput = document.getElementById('currentPageNote');
        if (noteInput) {
            noteInput.value = '';
        }
        
        // 重置数据
        this.notes = { pages: {}, bookmarks: [], progress: 0 };
        this.annotations = [];
        this.currentPage = 1;
        this.totalPages = 0;
        this.pdfDoc = null;
        
        // 更新界面显示
        this.updatePageNotesList();
        this.updateBookmarksList();
        this.updateAnnotationsList();
        
        // 清除选中状态
        document.querySelectorAll('.document-list-item').forEach(item => {
            item.classList.remove('active');
        });
    }
    
    async loadDocument(docId) {
        try {
            this.showLoading(true);
            
            // 如果有当前文档且要切换到不同文档，先自动保存当前页面笔记
            if (this.currentDocument && this.currentDocument !== docId) {
                this.autoSaveCurrentPageNote();
            }
            
            // 立即清空查看器内容，防止显示上一个文档的内容
            const viewerContent = document.getElementById('viewerContent');
            viewerContent.innerHTML = '<div class="text-center p-5"><i class="fas fa-spinner fa-spin fa-2x text-muted"></i><p class="text-muted mt-3">正在加载文档...</p></div>';
            
            // 立即清空当前页面笔记输入框，防止数据污染
            const noteInput = document.getElementById('currentPageNote');
            if (noteInput) {
                noteInput.value = '';
            }
            
            // 重置笔记和标注数据，防止显示上一个文档的内容
            this.notes = { pages: {}, bookmarks: [], progress: 0 };
            this.annotations = [];
            
            // 立即更新界面显示，清空上一个文档的笔记列表
            this.updatePageNotesList();
            this.updateBookmarksList();
            this.updateAnnotationsList();
            
            // 重置页面信息显示
            document.getElementById('currentPageInfo').textContent = '- / -';
            document.getElementById('zoomLevel').textContent = '-%';
            
            // 清空缩略图
            const thumbnailContainer = document.getElementById('pageThumbnails');
            thumbnailContainer.innerHTML = '';
            
            // 设置新的当前文档ID（在加载数据之前）
            this.currentDocument = docId;
            
            // 标记当前选中的文档
            document.querySelectorAll('.document-list-item').forEach(item => {
                item.classList.remove('active');
            });
            document.querySelector(`[data-doc-id="${docId}"]`).classList.add('active');
            
            // 获取文档信息以确定文件类型
            const documentsResponse = await fetch('/api/documents');
            const documentsData = await documentsResponse.json();
            
            if (!documentsData.success) {
                this.showMessage('获取文档信息失败', 'error');
                return;
            }
            
            const currentDoc = documentsData.documents.find(doc => doc.id === docId);
            if (!currentDoc) {
                this.showMessage('文档不存在', 'error');
                return;
            }
            
            // 检查文件类型
            const fileType = currentDoc.type.toLowerCase();
            
            if (fileType === '.pdf') {
                // 加载PDF文档
                const response = await fetch(`/api/documents/${docId}/view`);
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    
                    // 加载PDF
                    await this.loadPDF(url);
                    
                    // 加载笔记和标注
                    await this.loadNotes(docId);
                    await this.loadAnnotations(docId);
                    
                    // 显示学习工具
                    document.getElementById('learningTools').style.display = 'block';
                    document.getElementById('pageNavigation').style.display = 'block';
                    document.getElementById('progressContainer').style.display = 'block';
                    
                    // 开始计时
                    this.startStudyTimer();
                    
                } else {
                    this.showMessage('加载文档失败', 'error');
                }
            } else {
                // 处理非PDF文件
                this.handleNonPDFDocument(currentDoc);
            }
            
        } catch (error) {
            console.error('加载文档失败:', error);
            this.showMessage('加载文档失败', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async handleNonPDFDocument(doc) {
        // 清空查看器内容
        const viewerContent = document.getElementById('viewerContent');
        
        // 获取文件类型的友好名称
        const fileTypeNames = {
            '.ppt': 'PowerPoint 演示文稿',
            '.pptx': 'PowerPoint 演示文稿',
            '.doc': 'Word 文档',
            '.docx': 'Word 文档',
            '.txt': '文本文档'
        };
        
        const fileTypeName = fileTypeNames[doc.type] || '文档';
        
        // 如果是文本文件，尝试加载并显示内容
        if (doc.type === '.txt') {
            try {
                const response = await fetch(`/api/documents/${doc.id}/view`);
                if (response.ok) {
                    const textContent = await response.text();
                    
                    viewerContent.innerHTML = `
                        <div class="text-viewer">
                            <div class="text-content p-4">
                                <div class="mb-3">
                                    <h5><i class="fas fa-file-text"></i> ${doc.name}</h5>
                                    <small class="text-muted">文件大小: ${this.formatFileSize(doc.size)}</small>
                                </div>
                                <div class="text-content-body" style="white-space: pre-wrap; font-family: monospace; background: #f8f9fa; padding: 20px; border-radius: 5px; max-height: 600px; overflow-y: auto;">
                                    ${this.escapeHtml(textContent)}
                                </div>
                                <div class="mt-3">
                                    <a href="/api/documents/${doc.id}/view" 
                                       class="btn btn-outline-primary btn-sm" 
                                       download="${doc.name}">
                                        <i class="fas fa-download"></i> 下载文件
                                    </a>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    throw new Error('Failed to load text content');
                }
            } catch (error) {
                console.error('加载文本内容失败:', error);
                this.showNonTextDocument(doc, fileTypeName);
            }
        } else {
            this.showNonTextDocument(doc, fileTypeName);
        }
        
        // 设置默认页面信息（用于笔记功能）
        this.totalPages = 1;
        this.currentPage = 1;
        this.pdfDoc = null;
        
        // 更新页面信息显示
        document.getElementById('currentPageInfo').textContent = '1 / 1';
        document.getElementById('zoomLevel').textContent = '100%';
        
        // 清空缩略图
        const thumbnailContainer = document.getElementById('pageThumbnails');
        thumbnailContainer.innerHTML = `
            <div class="page-thumbnail active">1</div>
        `;
        
        // 加载笔记（仍然支持笔记功能）
        this.loadNotes(doc.id);
        
        // 显示学习工具（但隐藏不适用的功能）
        document.getElementById('learningTools').style.display = 'block';
        document.getElementById('pageNavigation').style.display = 'none'; // 隐藏页面导航
        document.getElementById('progressContainer').style.display = 'block';
        
        // 加载当前页面笔记
        this.loadCurrentPageNote();
        
        // 开始计时
        this.startStudyTimer();
    }
    
    showNonTextDocument(doc, fileTypeName) {
        const viewerContent = document.getElementById('viewerContent');
        
        viewerContent.innerHTML = `
            <div class="non-pdf-viewer">
                <div class="text-center p-5">
                    <i class="fas fa-file-${this.getFileIcon(doc.type)} fa-5x text-muted mb-4"></i>
                    <h4 class="text-muted mb-3">${fileTypeName}预览</h4>
                    <p class="text-muted mb-4">
                        当前系统暂不支持在线预览${fileTypeName}，但您仍可以使用学习笔记功能。
                    </p>
                    <div class="mb-4">
                        <strong>文件名：</strong> ${doc.name}<br>
                        <strong>文件大小：</strong> ${this.formatFileSize(doc.size)}
                    </div>
                    <a href="/api/documents/${doc.id}/view" 
                       class="btn btn-primary" 
                       download="${doc.name}">
                        <i class="fas fa-download"></i> 下载文件
                    </a>
                </div>
            </div>
        `;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    async loadPDF(url) {
        try {
            const loadingTask = pdfjsLib.getDocument(url);
            this.pdfDoc = await loadingTask.promise;
            this.totalPages = this.pdfDoc.numPages;
            this.currentPage = 1;
            
            await this.renderPage(this.currentPage);
            this.generatePageThumbnails();
            this.updatePageInfo();
            
        } catch (error) {
            console.error('PDF加载失败:', error);
            this.showMessage('PDF加载失败', 'error');
        }
    }
    
    async renderPage(pageNum) {
        try {
            const page = await this.pdfDoc.getPage(pageNum);
            const viewport = page.getViewport({ scale: this.zoomLevel });
            
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            canvas.className = 'pdf-canvas';
            canvas.id = `page-${pageNum}`;
            
            const renderContext = {
                canvasContext: context,
                viewport: viewport
            };
            
            await page.render(renderContext).promise;
            
            // 清空并添加新页面
            const viewerContent = document.getElementById('viewerContent');
            viewerContent.innerHTML = '';
            viewerContent.appendChild(canvas);
            
            // 渲染标注
            this.renderAnnotations(pageNum);
            
            this.currentPage = pageNum;
            this.updatePageInfo();
            this.updateProgress();
            
        } catch (error) {
            console.error('页面渲染失败:', error);
        }
    }
    
    generatePageThumbnails() {
        const container = document.getElementById('pageThumbnails');
        container.innerHTML = '';
        
        for (let i = 1; i <= this.totalPages; i++) {
            const thumbnail = document.createElement('div');
            thumbnail.className = 'page-thumbnail';
            thumbnail.textContent = i;
            thumbnail.onclick = () => this.goToPage(i);
            
            if (i === this.currentPage) {
                thumbnail.classList.add('active');
            }
            
            container.appendChild(thumbnail);
        }
    }
    
    updatePageInfo() {
        document.getElementById('currentPageInfo').textContent = `${this.currentPage} / ${this.totalPages}`;
        document.getElementById('zoomLevel').textContent = `${Math.round(this.zoomLevel * 100)}%`;
        
        // 更新缩略图
        document.querySelectorAll('.page-thumbnail').forEach((thumb, index) => {
            thumb.classList.toggle('active', index + 1 === this.currentPage);
        });
        
        // 加载当前页面笔记
        this.loadCurrentPageNote();
    }
    
    previousPage() {
        if (this.currentPage > 1) {
            this.autoSaveCurrentPageNote();
            this.renderPage(this.currentPage - 1);
        }
    }
    
    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.autoSaveCurrentPageNote();
            this.renderPage(this.currentPage + 1);
        }
    }
    
    goToPage(pageNum) {
        if (pageNum >= 1 && pageNum <= this.totalPages) {
            this.autoSaveCurrentPageNote();
            this.renderPage(pageNum);
        }
    }
    
    zoomIn() {
        this.zoomLevel = Math.min(this.zoomLevel * 1.2, 3.0);
        this.renderPage(this.currentPage);
    }
    
    zoomOut() {
        this.zoomLevel = Math.max(this.zoomLevel / 1.2, 0.5);
        this.renderPage(this.currentPage);
    }
    
    fitWidth() {
        const viewerContent = document.getElementById('viewerContent');
        const containerWidth = viewerContent.clientWidth - 40; // 减去padding
        
        if (this.pdfDoc) {
            this.pdfDoc.getPage(this.currentPage).then(page => {
                const viewport = page.getViewport({ scale: 1.0 });
                this.zoomLevel = containerWidth / viewport.width;
                this.renderPage(this.currentPage);
            });
        }
    }
    
    fitPage() {
        const viewerContent = document.getElementById('viewerContent');
        const containerWidth = viewerContent.clientWidth - 40;
        const containerHeight = viewerContent.clientHeight - 40;
        
        if (this.pdfDoc) {
            this.pdfDoc.getPage(this.currentPage).then(page => {
                const viewport = page.getViewport({ scale: 1.0 });
                const scaleX = containerWidth / viewport.width;
                const scaleY = containerHeight / viewport.height;
                this.zoomLevel = Math.min(scaleX, scaleY);
                this.renderPage(this.currentPage);
            });
        }
    }
    
    toggleFullscreen() {
        const viewer = document.getElementById('documentViewer');
        
        if (!document.fullscreenElement) {
            viewer.requestFullscreen().then(() => {
                viewer.classList.add('fullscreen');
                document.getElementById('fullscreen').innerHTML = '<i class="fas fa-compress"></i>';
            });
        } else {
            this.exitFullscreen();
        }
    }
    
    exitFullscreen() {
        if (document.fullscreenElement) {
            document.exitFullscreen().then(() => {
                this.exitFullscreenMode();
            });
        } else {
            // 如果不在浏览器全屏状态，直接退出自定义全屏模式
            this.exitFullscreenMode();
        }
    }
    
    exitFullscreenMode() {
        const viewer = document.getElementById('documentViewer');
        viewer.classList.remove('fullscreen');
        viewer.classList.remove('presentation-mode');
        document.getElementById('fullscreen').innerHTML = '<i class="fas fa-expand"></i>';
        
        // 恢复工具栏显示
        const toolbar = document.querySelector('.viewer-toolbar');
        if (toolbar) {
            toolbar.style.display = 'flex';
        }
        
        // 停止自动播放
        this.stopAutoPlay();
    }
    
    enterPresentationMode() {
        // 进入全屏模式
        const viewer = document.getElementById('documentViewer');
        if (!document.fullscreenElement) {
            viewer.requestFullscreen().then(() => {
                viewer.classList.add('fullscreen');
                viewer.classList.add('presentation-mode');
                document.getElementById('fullscreen').innerHTML = '<i class="fas fa-compress"></i>';
                
                // 隐藏工具栏（通过CSS类控制）
                // 自动播放
                this.startAutoPlay();
            });
        } else {
            viewer.classList.add('presentation-mode');
            this.startAutoPlay();
        }
    }
    
    startAutoPlay() {
        // 可以添加自动翻页功能
        this.autoPlayInterval = setInterval(() => {
            if (this.currentPage < this.totalPages) {
                this.nextPage();
            } else {
                this.stopAutoPlay();
            }
        }, 5000); // 5秒自动翻页
    }
    
    stopAutoPlay() {
        if (this.autoPlayInterval) {
            clearInterval(this.autoPlayInterval);
            this.autoPlayInterval = null;
        }
    }
    
    selectTool(tool) {
        // 清除之前的选择
        document.querySelectorAll('.toolbar-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // 选择新工具
        this.selectedTool = tool;
        document.getElementById(tool + 'Tool').classList.add('active');
        
        // 改变鼠标样式
        const viewerContent = document.getElementById('viewerContent');
        viewerContent.style.cursor = tool === 'highlight' ? 'crosshair' : 'pointer';
    }
    
    selectColor(color) {
        document.querySelectorAll('.color-option').forEach(option => {
            option.classList.remove('selected');
        });
        
        document.querySelector(`[data-color="${color}"]`).classList.add('selected');
        this.selectedColor = color;
    }
    
    handleMouseDown(e) {
        if (this.selectedTool === 'highlight') {
            this.isSelecting = true;
            this.selectionStart = { x: e.offsetX, y: e.offsetY };
        }
    }
    
    handleMouseMove(e) {
        if (this.isSelecting && this.selectedTool === 'highlight') {
            // 显示选择框
            this.showSelectionBox(this.selectionStart, { x: e.offsetX, y: e.offsetY });
        }
    }
    
    handleMouseUp(e) {
        if (this.isSelecting && this.selectedTool === 'highlight') {
            this.isSelecting = false;
            const end = { x: e.offsetX, y: e.offsetY };
            
            // 创建高亮标注
            this.createHighlight(this.selectionStart, end);
            this.hideSelectionBox();
        } else if (this.selectedTool === 'note') {
            // 显示笔记弹窗
            this.showNoteModal(e.offsetX, e.offsetY);
        } else if (this.selectedTool === 'bookmark') {
            this.addBookmark();
        }
    }
    
    showSelectionBox(start, end) {
        let selectionBox = document.getElementById('selectionBox');
        if (!selectionBox) {
            selectionBox = document.createElement('div');
            selectionBox.id = 'selectionBox';
            selectionBox.style.position = 'absolute';
            selectionBox.style.border = '2px dashed #007bff';
            selectionBox.style.background = 'rgba(0, 123, 255, 0.1)';
            selectionBox.style.pointerEvents = 'none';
            selectionBox.style.zIndex = '999';
            document.getElementById('viewerContent').appendChild(selectionBox);
        }
        
        const left = Math.min(start.x, end.x);
        const top = Math.min(start.y, end.y);
        const width = Math.abs(end.x - start.x);
        const height = Math.abs(end.y - start.y);
        
        selectionBox.style.left = left + 'px';
        selectionBox.style.top = top + 'px';
        selectionBox.style.width = width + 'px';
        selectionBox.style.height = height + 'px';
        selectionBox.style.display = 'block';
    }
    
    hideSelectionBox() {
        const selectionBox = document.getElementById('selectionBox');
        if (selectionBox) {
            selectionBox.style.display = 'none';
        }
    }
    
    createHighlight(start, end) {
        const annotation = {
            type: 'highlight',
            page: this.currentPage,
            color: this.selectedColor,
            coordinates: {
                x: Math.min(start.x, end.x),
                y: Math.min(start.y, end.y),
                width: Math.abs(end.x - start.x),
                height: Math.abs(end.y - start.y)
            },
            created: new Date().toISOString()
        };
        
        this.annotations.push(annotation);
        this.saveAnnotations();
        this.renderAnnotations(this.currentPage);
        this.updateAnnotationsList();
    }
    
    renderAnnotations(pageNum) {
        // 清除现有标注
        document.querySelectorAll('.highlight').forEach(el => el.remove());
        
        // 渲染当前页面的标注
        const pageAnnotations = this.annotations.filter(ann => ann.page === pageNum);
        const viewerContent = document.getElementById('viewerContent');
        
        pageAnnotations.forEach(annotation => {
            if (annotation.type === 'highlight') {
                const highlight = document.createElement('div');
                highlight.className = 'highlight';
                highlight.style.position = 'absolute';
                highlight.style.left = annotation.coordinates.x + 'px';
                highlight.style.top = annotation.coordinates.y + 'px';
                highlight.style.width = annotation.coordinates.width + 'px';
                highlight.style.height = annotation.coordinates.height + 'px';
                highlight.style.backgroundColor = annotation.color;
                highlight.style.opacity = '0.3';
                highlight.style.pointerEvents = 'auto';
                highlight.style.cursor = 'pointer';
                
                highlight.onclick = () => this.selectAnnotation(annotation);
                
                viewerContent.appendChild(highlight);
            }
        });
    }
    
    selectAnnotation(annotation) {
        // 高亮选中的标注
        document.querySelectorAll('.highlight').forEach(el => {
            el.classList.remove('selected');
        });
        
        event.target.classList.add('selected');
        
        // 可以添加编辑或删除功能
        this.showAnnotationMenu(annotation, event.target);
    }
    
    showAnnotationMenu(annotation, element) {
        // 创建右键菜单
        const menu = document.createElement('div');
        menu.className = 'annotation-menu';
        menu.style.position = 'absolute';
        menu.style.background = 'white';
        menu.style.border = '1px solid #ddd';
        menu.style.borderRadius = '4px';
        menu.style.padding = '5px';
        menu.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
        menu.style.zIndex = '1001';
        
        menu.innerHTML = `
            <button class="btn btn-sm btn-outline-danger" onclick="documentPlatform.deleteAnnotation('${annotation.id}')">
                <i class="fas fa-trash"></i> 删除
            </button>
        `;
        
        const rect = element.getBoundingClientRect();
        menu.style.left = rect.right + 'px';
        menu.style.top = rect.top + 'px';
        
        document.body.appendChild(menu);
        
        // 点击其他地方关闭菜单
        setTimeout(() => {
            document.addEventListener('click', function closeMenu() {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            });
        }, 100);
    }
    
    deleteAnnotation(annotationId) {
        this.annotations = this.annotations.filter(ann => ann.id !== annotationId);
        this.saveAnnotations();
        this.renderAnnotations(this.currentPage);
        this.updateAnnotationsList();
    }
    
    clearAnnotations() {
        if (confirm('确定要清除所有标注吗？')) {
            this.annotations = [];
            this.saveAnnotations();
            this.renderAnnotations(this.currentPage);
            this.updateAnnotationsList();
        }
    }
    
    showNoteModal(x, y) {
        const modal = new bootstrap.Modal(document.getElementById('noteModal'));
        modal.show();
        
        // 保存点击位置，用于创建笔记
        this.notePosition = { x, y, page: this.currentPage };
    }
    
    saveNoteFromModal() {
        const content = document.getElementById('noteContent').value;
        const tags = document.getElementById('noteTags').value;
        
        if (!content.trim()) {
            this.showMessage('请输入笔记内容', 'warning');
            return;
        }
        
        const note = {
            id: Date.now().toString(),
            content: content,
            tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag),
            page: this.notePosition.page,
            position: { x: this.notePosition.x, y: this.notePosition.y },
            created: new Date().toISOString()
        };
        
        if (!this.notes.pages[this.currentPage]) {
            this.notes.pages[this.currentPage] = [];
        }
        
        this.notes.pages[this.currentPage].push(note);
        this.saveNotes();
        this.updatePageNotesList();
        
        // 清空表单并关闭模态框
        document.getElementById('noteContent').value = '';
        document.getElementById('noteTags').value = '';
        bootstrap.Modal.getInstance(document.getElementById('noteModal')).hide();
        
        this.showMessage('笔记保存成功', 'success');
    }
    
    savePageNote() {
        const content = document.getElementById('currentPageNote').value;
        
        if (!content.trim()) {
            this.showMessage('请输入笔记内容', 'warning');
            return;
        }
        
        // 使用统一的对象结构
        this.notes.pages[this.currentPage] = {
            content: content,
            created: this.notes.pages[this.currentPage] ? this.notes.pages[this.currentPage].created : new Date().toISOString(),
            updated: new Date().toISOString()
        };
        
        this.saveNotes();
        this.updatePageNotesList();
        
        this.showMessage('笔记保存成功', 'success');
    }
    
    loadCurrentPageNote() {
        const pageNote = this.notes.pages[this.currentPage];
        
        if (pageNote && pageNote.content) {
            document.getElementById('currentPageNote').value = pageNote.content;
        } else {
            document.getElementById('currentPageNote').value = '';
        }
    }
    
    // 自动保存当前页面笔记（在页面切换前调用）
    autoSaveCurrentPageNote() {
        // 确保有当前文档才保存
        if (!this.currentDocument) {
            return;
        }
        
        const content = document.getElementById('currentPageNote').value;
        
        if (content.trim()) {
            const existingNote = this.notes.pages[this.currentPage];
            
            this.notes.pages[this.currentPage] = {
                content: content,
                created: existingNote ? existingNote.created : new Date().toISOString(),
                updated: new Date().toISOString()
            };
            
            this.saveNotes();
        } else {
            // 如果内容为空，将页面笔记内容设为空字符串以便后端删除
            if (this.notes.pages[this.currentPage]) {
                this.notes.pages[this.currentPage] = {
                    content: '',
                    created: this.notes.pages[this.currentPage].created || new Date().toISOString(),
                    updated: new Date().toISOString()
                };
                this.saveNotes();
                // 保存后再删除本地记录以更新界面
                setTimeout(() => {
                    delete this.notes.pages[this.currentPage];
                    this.updatePageNotesList();
                }, 100);
            }
        }
    }
    
    deletePageNote(pageNum) {
        if (confirm('确定要删除这个页面笔记吗？')) {
            delete this.notes.pages[pageNum];
            
            // 如果删除的是当前页面的笔记，清空输入框
            if (pageNum == this.currentPage) {
                const noteTextarea = document.getElementById('currentPageNote');
                if (noteTextarea) {
                    noteTextarea.value = '';
                }
            }
            
            this.saveNotes();
            this.updatePageNotesList();
            this.showMessage('笔记删除成功', 'success');
        }
    }
    
    updatePageNotesList() {
        const container = document.getElementById('pageNotesList');
        const allNotes = [];
        
        Object.keys(this.notes.pages).forEach(page => {
            const note = this.notes.pages[page];
            if (note && note.content) {
                allNotes.push({ 
                    ...note, 
                    page: parseInt(page)
                });
            }
        });
        
        if (allNotes.length === 0) {
            container.innerHTML = `
                <div class="text-muted text-center">
                    <i class="fas fa-sticky-note fa-2x mb-2"></i>
                    <div>暂无笔记</div>
                </div>
            `;
            return;
        }
        
        allNotes.sort((a, b) => new Date(b.created) - new Date(a.created));
        
        container.innerHTML = allNotes.map(note => `
            <div class="note-item" onclick="documentPlatform.goToPage(${note.page})">
                <div class="note-content mb-2">${note.content}</div>
                <div class="note-metadata d-flex justify-content-between align-items-center">
                    <span class="badge bg-secondary">第 ${note.page} 页</span>
                    <div class="note-timestamps">
                        <small class="text-muted d-block">创建: ${this.formatDate(note.created)}</small>
                        ${note.updated && note.updated !== note.created ? 
                            `<small class="text-muted d-block">修改: ${this.formatDate(note.updated)}</small>` : ''}
                    </div>
                    <button class="btn btn-sm btn-outline-danger ms-2" onclick="event.stopPropagation(); documentPlatform.deletePageNote(${note.page})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    addBookmark() {
        const bookmark = {
            id: Date.now().toString(),
            page: this.currentPage,
            title: `第 ${this.currentPage} 页`,
            created: new Date().toISOString()
        };
        
        this.notes.bookmarks.push(bookmark);
        this.saveNotes();
        this.updateBookmarksList();
        this.showMessage('书签添加成功', 'success');
    }
    
    updateBookmarksList() {
        const container = document.getElementById('bookmarksList');
        
        if (this.notes.bookmarks.length === 0) {
            container.innerHTML = `
                <div class="text-muted text-center">
                    <i class="fas fa-bookmark fa-2x mb-2"></i>
                    <div>暂无书签</div>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.notes.bookmarks.map(bookmark => `
            <div class="note-item" onclick="documentPlatform.goToPage(${bookmark.page})">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <i class="fas fa-bookmark text-primary me-2"></i>
                        ${bookmark.title}
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="event.stopPropagation(); documentPlatform.removeBookmark('${bookmark.id}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <small class="text-muted">${this.formatDate(bookmark.created)}</small>
            </div>
        `).join('');
    }
    
    removeBookmark(bookmarkId) {
        this.notes.bookmarks = this.notes.bookmarks.filter(b => b.id !== bookmarkId);
        this.saveNotes();
        this.updateBookmarksList();
    }
    
    updateAnnotationsList() {
        const container = document.getElementById('annotationsList');
        
        if (this.annotations.length === 0) {
            container.innerHTML = `
                <div class="text-muted text-center">
                    <i class="fas fa-highlighter fa-2x mb-2"></i>
                    <div>暂无标注</div>
                </div>
            `;
            return;
        }
        
        const sortedAnnotations = [...this.annotations].sort((a, b) => b.page - a.page);
        
        container.innerHTML = sortedAnnotations.map(annotation => `
            <div class="note-item" onclick="documentPlatform.goToPage(${annotation.page})">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <i class="fas fa-highlighter me-2" style="color: ${annotation.color}"></i>
                        第 ${annotation.page} 页
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="event.stopPropagation(); documentPlatform.deleteAnnotation('${annotation.id}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <small class="text-muted">${this.formatDate(annotation.created)}</small>
            </div>
        `).join('');
    }
    
    async loadNotes(docId) {
        try {
            const response = await fetch(`/api/documents/${docId}/notes`);
            const data = await response.json();
            
            if (data.success && data.notes) {
                this.notes = data.notes;
            } else {
                // 如果加载失败或无数据，重置为空的笔记结构
                this.notes = { pages: {}, bookmarks: [], progress: 0 };
            }
        } catch (error) {
            console.error('加载笔记失败:', error);
            // 如果请求失败，重置为空的笔记结构
            this.notes = { pages: {}, bookmarks: [], progress: 0 };
        }
        
        // 无论成功还是失败，都要更新界面显示
        this.updatePageNotesList();
        this.updateBookmarksList();
        this.updateProgress();
        // 加载当前页面的笔记内容到输入框
        this.loadCurrentPageNote();
    }
    
    async saveNotes() {
        if (!this.currentDocument) return;
        
        try {
            await fetch(`/api/documents/${this.currentDocument}/notes`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.notes)
            });
        } catch (error) {
            console.error('保存笔记失败:', error);
        }
    }
    
    async loadAnnotations(docId) {
        try {
            const response = await fetch(`/api/documents/${docId}/annotations`);
            const data = await response.json();
            
            if (data.success && data.annotations) {
                this.annotations = data.annotations;
            } else {
                // 如果加载失败或无数据，重置为空的标注数组
                this.annotations = [];
            }
        } catch (error) {
            console.error('加载标注失败:', error);
            // 如果请求失败，重置为空的标注数组
            this.annotations = [];
        }
        
        // 无论成功还是失败，都要更新界面显示
        this.updateAnnotationsList();
    }
    
    async saveAnnotations() {
        if (!this.currentDocument) return;
        
        try {
            // 为每个标注添加ID（如果没有的话）
            this.annotations.forEach(annotation => {
                if (!annotation.id) {
                    annotation.id = Date.now().toString() + Math.random().toString(36).substr(2, 9);
                }
            });
            
            await fetch(`/api/documents/${this.currentDocument}/annotations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.annotations[this.annotations.length - 1]) // 只发送最新的标注
            });
        } catch (error) {
            console.error('保存标注失败:', error);
        }
    }
    
    updateProgress() {
        if (!this.totalPages) return;
        
        // 计算学习进度（基于访问的页面数）
        const visitedPages = new Set();
        Object.keys(this.notes.pages).forEach(page => {
            visitedPages.add(parseInt(page));
        });
        
        visitedPages.add(this.currentPage);
        
        const progress = (visitedPages.size / this.totalPages) * 100;
        this.notes.progress = progress;
        
        // 更新进度条
        document.getElementById('learningProgress').style.width = progress + '%';
        document.getElementById('progressText').textContent = Math.round(progress) + '%';
        document.getElementById('globalProgress').style.width = progress + '%';
        document.getElementById('progressPercentage').textContent = Math.round(progress) + '%';
        
        this.saveNotes();
    }
    
    startStudyTimer() {
        this.studyStartTime = Date.now();
        
        this.studyTimer = setInterval(() => {
            this.studyDuration = Math.floor((Date.now() - this.studyStartTime) / 1000 / 60); // 分钟
            document.getElementById('studyTime').textContent = this.studyDuration + '分钟';
        }, 60000); // 每分钟更新一次
    }
    
    exportNotes() {
        // 生成Markdown格式的学习笔记
        let markdownContent = `# ${this.currentDocument || '学习笔记'}\n\n`;
        
        // 添加页面笔记
        if (this.notes.pages && Object.keys(this.notes.pages).length > 0) {
            markdownContent += `## 📝 页面笔记\n\n`;
            
            // 按页码排序
            const sortedPages = Object.keys(this.notes.pages)
                .map(page => parseInt(page))
                .sort((a, b) => a - b);
            
            sortedPages.forEach(pageNum => {
                const note = this.notes.pages[pageNum];
                if (note && note.content && note.content.trim()) {
                    markdownContent += `### 第 ${pageNum} 页\n\n`;
                    markdownContent += `${note.content.trim()}\n\n`;
                    if (note.updated) {
                        const updateDate = new Date(note.updated).toLocaleDateString('zh-CN');
                        markdownContent += `*更新时间: ${updateDate}*\n\n`;
                    }
                    markdownContent += `---\n\n`;
                }
            });
        }
        
        // 添加书签
        if (this.notes.bookmarks && this.notes.bookmarks.length > 0) {
            markdownContent += `## 🔖 重要书签\n\n`;
            
            // 按页码排序书签
            const sortedBookmarks = [...this.notes.bookmarks]
                .sort((a, b) => a.page - b.page);
            
            sortedBookmarks.forEach(bookmark => {
                markdownContent += `- **第 ${bookmark.page} 页**: ${bookmark.title || '重要标记'}\n`;
                if (bookmark.note && bookmark.note.trim()) {
                    markdownContent += `  > ${bookmark.note.trim()}\n`;
                }
            });
            markdownContent += `\n`;
        }
        
        // 添加学习进度信息
        if (this.notes.progress > 0) {
            markdownContent += `## 📊 学习进度\n\n`;
            markdownContent += `学习完成度: ${Math.round(this.notes.progress)}%\n\n`;
        }
        
        // 如果没有任何内容，添加提示
        if (!this.notes.pages || Object.keys(this.notes.pages).length === 0) {
            if (!this.notes.bookmarks || this.notes.bookmarks.length === 0) {
                markdownContent += `## 📝 暂无学习笔记\n\n`;
                markdownContent += `开始学习并记录您的想法和重点内容吧！\n\n`;
            }
        }
        
        // 添加导出时间
        const exportTime = new Date().toLocaleString('zh-CN');
        markdownContent += `\n---\n\n*导出时间: ${exportTime}*\n`;
        
        // 创建并下载Markdown文件
        const blob = new Blob([markdownContent], { type: 'text/markdown;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `学习笔记_${this.currentDocument || 'notes'}_${new Date().toISOString().split('T')[0]}.md`;
        a.click();
        
        URL.revokeObjectURL(url);
        this.showMessage('学习笔记已导出为Markdown格式', 'success');
    }
    
    clearNotes() {
        if (confirm('确定要清空所有笔记吗？')) {
            this.notes = { pages: {}, bookmarks: [], progress: 0 };
            this.saveNotes();
            this.updatePageNotesList();
            this.updateBookmarksList();
            this.updateProgress();
            this.showMessage('笔记已清空', 'success');
        }
    }
    
    showLoading(show) {
        document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
    }
    
    showMessage(message, type = 'info') {
        // 创建消息提示
        const alert = document.createElement('div');
        alert.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        alert.style.position = 'fixed';
        alert.style.top = '20px';
        alert.style.right = '20px';
        alert.style.zIndex = '9999';
        alert.style.minWidth = '300px';
        
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        // 3秒后自动消失
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 3000);
    }
}

// 初始化文档学习平台
let documentPlatform;
document.addEventListener('DOMContentLoaded', () => {
    documentPlatform = new DocumentLearningPlatform();
});