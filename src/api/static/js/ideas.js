/**
 * Ideas Collection JavaScript Module
 * 
 * Handles all frontend interactions for the ideas collection feature.
 * 
 * Author: Assistant
 * Version: 1.0
 * Date: 2025-01-02
 */

class IdeasManager {
    constructor() {
        this.ideas = [];
        this.filteredIdeas = [];
        this.currentView = 'table'; // table, cards, kanban
        this.currentFilters = {};
        this.selectedIdeas = new Set();
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadIdeas();
        this.loadStatistics();
        this.loadCategories();
        this.loadTags();
    }
    
    bindEvents() {
        // Add idea button
        document.getElementById('addIdeaBtn')?.addEventListener('click', () => {
            this.showAddIdeaModal();
        });
        
        // Save idea button
        document.getElementById('saveIdeaBtn')?.addEventListener('click', () => {
            this.saveIdea();
        });
        
        // View toggle buttons
        document.querySelectorAll('.view-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchView(e.target.dataset.view);
            });
        });
        
        // Filter controls
        document.getElementById('statusFilter')?.addEventListener('change', () => {
            this.applyFilters();
        });
        
        document.getElementById('priorityFilter')?.addEventListener('change', () => {
            this.applyFilters();
        });
        
        document.getElementById('categoryFilter')?.addEventListener('change', () => {
            this.applyFilters();
        });
        
        document.getElementById('searchInput')?.addEventListener('input', () => {
            this.applyFilters();
        });
        
        // Batch operations
        document.getElementById('batchDeleteBtn')?.addEventListener('click', () => {
            this.batchDelete();
        });
        
        document.getElementById('batchStatusBtn')?.addEventListener('click', () => {
            this.showBatchStatusModal();
        });
        
        // Export/Import
        document.getElementById('exportJsonBtn')?.addEventListener('click', () => {
            this.exportIdeas('json');
        });
        
        document.getElementById('exportCsvBtn')?.addEventListener('click', () => {
            this.exportIdeas('csv');
        });
        
        document.getElementById('importBtn')?.addEventListener('click', () => {
            this.showImportModal();
        });
        
        document.getElementById('importFileBtn')?.addEventListener('click', () => {
            this.importIdeas();
        });
        
        // Select all checkbox
        document.getElementById('selectAllIdeas')?.addEventListener('change', (e) => {
            this.toggleSelectAll(e.target.checked);
        });
    }
    
    async loadIdeas(filters = {}) {
        try {
            const params = new URLSearchParams(filters);
            const response = await fetch(`/api/ideas/?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.ideas = data.ideas;
                this.filteredIdeas = [...this.ideas];
                this.renderIdeas();
                this.updateIdeaCount();
            } else {
                this.showError('Failed to load ideas: ' + data.error);
            }
        } catch (error) {
            this.showError('Error loading ideas: ' + error.message);
        }
    }
    
    async loadStatistics() {
        try {
            const response = await fetch('/api/ideas/statistics');
            const data = await response.json();
            
            if (data.success) {
                this.renderStatistics(data.statistics);
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }
    
    async loadCategories() {
        try {
            const response = await fetch('/api/ideas/categories');
            const data = await response.json();
            
            if (data.success) {
                this.populateCategoryFilter(data.categories);
            }
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }
    
    async loadTags() {
        try {
            const response = await fetch('/api/ideas/tags');
            const data = await response.json();
            
            if (data.success) {
                this.populateTagsInput(data.tags);
            }
        } catch (error) {
            console.error('Error loading tags:', error);
        }
    }
    
    renderStatistics(stats) {
        document.getElementById('totalIdeas').textContent = stats.total || 0;
        document.getElementById('pendingIdeas').textContent = stats.status_counts?.pending || 0;
        document.getElementById('inProgressIdeas').textContent = stats.status_counts?.in_progress || 0;
        document.getElementById('completedIdeas').textContent = stats.status_counts?.completed || 0;
        document.getElementById('completionRate').textContent = `${Math.round(stats.completion_rate || 0)}%`;
    }
    
    renderIdeas() {
        if (this.currentView === 'table') {
            this.renderTableView();
        } else if (this.currentView === 'cards') {
            this.renderCardsView();
        } else if (this.currentView === 'kanban') {
            this.renderKanbanView();
        }
    }
    
    renderTableView() {
        const tbody = document.querySelector('#ideasTable tbody');
        if (!tbody) return;
        
        if (this.filteredIdeas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No ideas found</td></tr>';
            return;
        }
        
        tbody.innerHTML = this.filteredIdeas.map(idea => `
            <tr>
                <td>
                    <input type="checkbox" class="form-check-input idea-checkbox" 
                           value="${idea.id}" ${this.selectedIdeas.has(idea.id) ? 'checked' : ''}>
                </td>
                <td>
                    <span class="fw-bold">${this.escapeHtml(idea.title)}</span>
                    ${idea.description ? `<br><small class="text-muted">${this.escapeHtml(idea.description.substring(0, 100))}${idea.description.length > 100 ? '...' : ''}</small>` : ''}
                </td>
                <td><span class="badge bg-secondary">${this.escapeHtml(idea.category || 'Uncategorized')}</span></td>
                <td>
                    ${idea.tags.map(tag => `<span class="badge bg-info me-1">${this.escapeHtml(tag)}</span>`).join('')}
                </td>
                <td><span class="badge bg-${this.getPriorityColor(idea.priority)}">${this.escapeHtml(idea.priority)}</span></td>
                <td><span class="badge bg-${this.getStatusColor(idea.status)}">${this.escapeHtml(idea.status.replace('_', ' '))}</span></td>
                <td><small>${this.formatDate(idea.created_at)}</small></td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="ideasManager.editIdea(${idea.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="ideasManager.deleteIdea(${idea.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
        
        // Bind checkbox events
        tbody.querySelectorAll('.idea-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const ideaId = parseInt(e.target.value);
                if (e.target.checked) {
                    this.selectedIdeas.add(ideaId);
                } else {
                    this.selectedIdeas.delete(ideaId);
                }
                this.updateBatchControls();
            });
        });
    }
    
    renderCardsView() {
        const container = document.getElementById('ideasCardsContainer');
        if (!container) return;
        
        if (this.filteredIdeas.length === 0) {
            container.innerHTML = '<div class="col-12 text-center text-muted">No ideas found</div>';
            return;
        }
        
        container.innerHTML = this.filteredIdeas.map(idea => `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card h-100 idea-card" data-id="${idea.id}">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">${this.escapeHtml(idea.title)}</h6>
                        <div class="form-check">
                            <input type="checkbox" class="form-check-input idea-checkbox" 
                                   value="${idea.id}" ${this.selectedIdeas.has(idea.id) ? 'checked' : ''}>
                        </div>
                    </div>
                    <div class="card-body">
                        <p class="card-text">${this.escapeHtml(idea.description || 'No description')}</p>
                        <div class="mb-2">
                            <span class="badge bg-secondary me-1">${this.escapeHtml(idea.category || 'Uncategorized')}</span>
                            <span class="badge bg-${this.getPriorityColor(idea.priority)} me-1">${this.escapeHtml(idea.priority)}</span>
                            <span class="badge bg-${this.getStatusColor(idea.status)}">${this.escapeHtml(idea.status.replace('_', ' '))}</span>
                        </div>
                        <div class="mb-2">
                            ${idea.tags.map(tag => `<span class="badge bg-info me-1">${this.escapeHtml(tag)}</span>`).join('')}
                        </div>
                        <small class="text-muted">Created: ${this.formatDate(idea.created_at)}</small>
                    </div>
                    <div class="card-footer">
                        <div class="btn-group w-100">
                            <button class="btn btn-outline-primary btn-sm" onclick="ideasManager.editIdea(${idea.id})">
                                <i class="fas fa-edit"></i> Edit
                            </button>
                            <button class="btn btn-outline-danger btn-sm" onclick="ideasManager.deleteIdea(${idea.id})">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Bind checkbox events
        container.querySelectorAll('.idea-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const ideaId = parseInt(e.target.value);
                if (e.target.checked) {
                    this.selectedIdeas.add(ideaId);
                } else {
                    this.selectedIdeas.delete(ideaId);
                }
                this.updateBatchControls();
            });
        });
    }
    
    renderKanbanView() {
        const container = document.getElementById('kanbanContainer');
        if (!container) return;
        
        const statuses = ['pending', 'in_progress', 'completed', 'on_hold'];
        const statusLabels = {
            'pending': 'Pending',
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'on_hold': 'On Hold'
        };
        
        container.innerHTML = statuses.map(status => {
            const statusIdeas = this.filteredIdeas.filter(idea => idea.status === status);
            return `
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-header bg-${this.getStatusColor(status)} text-white">
                            <h6 class="mb-0">${statusLabels[status]} (${statusIdeas.length})</h6>
                        </div>
                        <div class="card-body kanban-column" data-status="${status}">
                            ${statusIdeas.map(idea => `
                                <div class="card mb-2 kanban-item" data-id="${idea.id}" draggable="true">
                                    <div class="card-body p-2">
                                        <div class="d-flex justify-content-between align-items-start">
                                            <h6 class="card-title mb-1">${this.escapeHtml(idea.title)}</h6>
                                            <input type="checkbox" class="form-check-input idea-checkbox" 
                                                   value="${idea.id}" ${this.selectedIdeas.has(idea.id) ? 'checked' : ''}>
                                        </div>
                                        <p class="card-text small">${this.escapeHtml(idea.description?.substring(0, 80) || '')}${idea.description?.length > 80 ? '...' : ''}</p>
                                        <div class="d-flex justify-content-between align-items-center">
                                            <span class="badge bg-${this.getPriorityColor(idea.priority)}">${this.escapeHtml(idea.priority)}</span>
                                            <div class="btn-group btn-group-sm">
                                                <button class="btn btn-outline-primary btn-sm" onclick="ideasManager.editIdea(${idea.id})" title="Edit">
                                                    <i class="fas fa-edit"></i>
                                                </button>
                                                <button class="btn btn-outline-danger btn-sm" onclick="ideasManager.deleteIdea(${idea.id})" title="Delete">
                                                    <i class="fas fa-trash"></i>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        // Enable drag and drop
        this.enableDragAndDrop();
        
        // Bind checkbox events
        container.querySelectorAll('.idea-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const ideaId = parseInt(e.target.value);
                if (e.target.checked) {
                    this.selectedIdeas.add(ideaId);
                } else {
                    this.selectedIdeas.delete(ideaId);
                }
                this.updateBatchControls();
            });
        });
    }
    
    enableDragAndDrop() {
        const kanbanItems = document.querySelectorAll('.kanban-item');
        const kanbanColumns = document.querySelectorAll('.kanban-column');
        
        kanbanItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', e.target.dataset.id);
                e.target.classList.add('dragging');
            });
            
            item.addEventListener('dragend', (e) => {
                e.target.classList.remove('dragging');
            });
        });
        
        kanbanColumns.forEach(column => {
            column.addEventListener('dragover', (e) => {
                e.preventDefault();
                column.classList.add('drag-over');
            });
            
            column.addEventListener('dragleave', (e) => {
                column.classList.remove('drag-over');
            });
            
            column.addEventListener('drop', (e) => {
                e.preventDefault();
                column.classList.remove('drag-over');
                
                const ideaId = parseInt(e.dataTransfer.getData('text/plain'));
                const newStatus = column.dataset.status;
                
                this.updateIdeaStatus(ideaId, newStatus);
            });
        });
    }
    
    async updateIdeaStatus(ideaId, newStatus) {
        try {
            const response = await fetch(`/api/ideas/${ideaId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: newStatus })
            });
            
            const data = await response.json();
            if (data.success) {
                this.loadIdeas();
                this.loadStatistics();
                this.showSuccess('Idea status updated successfully');
            } else {
                this.showError('Failed to update idea status: ' + data.error);
            }
        } catch (error) {
            this.showError('Error updating idea status: ' + error.message);
        }
    }
    
    switchView(view) {
        this.currentView = view;
        
        // Update active button
        document.querySelectorAll('.view-toggle').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-view="${view}"]`)?.classList.add('active');
        
        // Show/hide view containers
        document.getElementById('tableView')?.style.setProperty('display', view === 'table' ? 'block' : 'none');
        document.getElementById('cardsView')?.style.setProperty('display', view === 'cards' ? 'block' : 'none');
        document.getElementById('kanbanView')?.style.setProperty('display', view === 'kanban' ? 'block' : 'none');
        
        this.renderIdeas();
    }
    
    applyFilters() {
        const status = document.getElementById('statusFilter')?.value;
        const priority = document.getElementById('priorityFilter')?.value;
        const category = document.getElementById('categoryFilter')?.value;
        const search = document.getElementById('searchInput')?.value?.toLowerCase();
        
        this.filteredIdeas = this.ideas.filter(idea => {
            if (status && idea.status !== status) return false;
            if (priority && idea.priority !== priority) return false;
            if (category && idea.category !== category) return false;
            if (search && !idea.title.toLowerCase().includes(search) && 
                !idea.description.toLowerCase().includes(search)) return false;
            
            return true;
        });
        
        this.renderIdeas();
        this.updateIdeaCount();
    }
    
    showAddIdeaModal() {
        this.clearIdeaForm();
        document.getElementById('ideaModalTitle').textContent = 'Add New Idea';
        document.getElementById('ideaForm').dataset.mode = 'add';
        new bootstrap.Modal(document.getElementById('ideaModal')).show();
    }
    
    async editIdea(ideaId) {
        try {
            const response = await fetch(`/api/ideas/${ideaId}`);
            const data = await response.json();
            
            if (data.success) {
                this.populateIdeaForm(data.idea);
                document.getElementById('ideaModalTitle').textContent = 'Edit Idea';
                document.getElementById('ideaForm').dataset.mode = 'edit';
                document.getElementById('ideaForm').dataset.ideaId = ideaId;
                new bootstrap.Modal(document.getElementById('ideaModal')).show();
            } else {
                this.showError('Failed to load idea: ' + data.error);
            }
        } catch (error) {
            this.showError('Error loading idea: ' + error.message);
        }
    }
    
    async saveIdea() {
        const form = document.getElementById('ideaForm');
        const formData = new FormData(form);
        
        const ideaData = {
            title: formData.get('title'),
            description: formData.get('description'),
            category: formData.get('category'),
            tags: formData.get('tags') ? formData.get('tags').split(',').map(tag => tag.trim()).filter(tag => tag) : [],
            priority: formData.get('priority'),
            status: formData.get('status'),
            target_date: formData.get('target_date') || null,
            related_links: formData.get('related_links') ? formData.get('related_links').split('\n').map(link => link.trim()).filter(link => link) : [],
            notes: formData.get('notes')
        };
        
        if (!ideaData.title) {
            this.showError('Title is required');
            return;
        }
        
        try {
            const mode = form.dataset.mode;
            const url = mode === 'edit' ? `/api/ideas/${form.dataset.ideaId}` : '/api/ideas/';
            const method = mode === 'edit' ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(ideaData)
            });
            
            const data = await response.json();
            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('ideaModal')).hide();
                this.loadIdeas();
                this.loadStatistics();
                this.loadCategories();
                this.loadTags();
                this.showSuccess(mode === 'edit' ? 'Idea updated successfully' : 'Idea created successfully');
            } else {
                this.showError('Failed to save idea: ' + data.error);
            }
        } catch (error) {
            this.showError('Error saving idea: ' + error.message);
        }
    }
    
    async deleteIdea(ideaId) {
        if (!confirm('Are you sure you want to delete this idea?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/ideas/${ideaId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            if (data.success) {
                this.loadIdeas();
                this.loadStatistics();
                this.showSuccess('Idea deleted successfully');
            } else {
                this.showError('Failed to delete idea: ' + data.error);
            }
        } catch (error) {
            this.showError('Error deleting idea: ' + error.message);
        }
    }
    
    async batchDelete() {
        if (this.selectedIdeas.size === 0) {
            this.showError('Please select ideas to delete');
            return;
        }
        
        if (!confirm(`Are you sure you want to delete ${this.selectedIdeas.size} selected ideas?`)) {
            return;
        }
        
        try {
            const response = await fetch('/api/ideas/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    operation: 'delete',
                    idea_ids: Array.from(this.selectedIdeas)
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.selectedIdeas.clear();
                this.loadIdeas();
                this.loadStatistics();
                this.updateBatchControls();
                this.showSuccess(data.message);
            } else {
                this.showError('Failed to delete ideas: ' + data.error);
            }
        } catch (error) {
            this.showError('Error deleting ideas: ' + error.message);
        }
    }
    
    async exportIdeas(format) {
        try {
            const response = await fetch(`/api/ideas/export/${format}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `ideas_export_${new Date().toISOString().split('T')[0]}.${format}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                this.showSuccess('Ideas exported successfully');
            } else {
                this.showError('Failed to export ideas');
            }
        } catch (error) {
            this.showError('Error exporting ideas: ' + error.message);
        }
    }
    
    async importIdeas() {
        const fileInput = document.getElementById('importFile');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showError('Please select a file to import');
            return;
        }
        
        const format = file.name.endsWith('.json') ? 'json' : 'csv';
        
        try {
            const content = await file.text();
            const response = await fetch('/api/ideas/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: content,
                    format: format
                })
            });
            
            const data = await response.json();
            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('importModal')).hide();
                this.loadIdeas();
                this.loadStatistics();
                this.loadCategories();
                this.loadTags();
                this.showSuccess(data.message);
            } else {
                this.showError('Failed to import ideas: ' + data.error);
            }
        } catch (error) {
            this.showError('Error importing ideas: ' + error.message);
        }
    }
    
    clearIdeaForm() {
        document.getElementById('ideaForm').reset();
        delete document.getElementById('ideaForm').dataset.ideaId;
    }
    
    populateIdeaForm(idea) {
        document.getElementById('ideaTitle').value = idea.title || '';
        document.getElementById('ideaDescription').value = idea.description || '';
        document.getElementById('ideaCategory').value = idea.category || '';
        document.getElementById('ideaTags').value = idea.tags ? idea.tags.join(', ') : '';
        document.getElementById('ideaPriority').value = idea.priority || 'medium';
        document.getElementById('ideaStatus').value = idea.status || 'pending';
        document.getElementById('ideaTargetDate').value = idea.target_date || '';
        document.getElementById('ideaRelatedLinks').value = idea.related_links ? idea.related_links.join('\n') : '';
        document.getElementById('ideaNotes').value = idea.notes || '';
    }
    
    populateCategoryFilter(categories) {
        const select = document.getElementById('categoryFilter');
        if (!select) return;
        
        select.innerHTML = '<option value="">All Categories</option>' +
            categories.map(cat => `<option value="${this.escapeHtml(cat)}">${this.escapeHtml(cat)}</option>`).join('');
    }
    
    populateTagsInput(tags) {
        // Could implement tag autocomplete here
        console.log('Available tags:', tags);
    }
    
    toggleSelectAll(checked) {
        this.selectedIdeas.clear();
        if (checked) {
            this.filteredIdeas.forEach(idea => this.selectedIdeas.add(idea.id));
        }
        
        document.querySelectorAll('.idea-checkbox').forEach(checkbox => {
            checkbox.checked = checked;
        });
        
        this.updateBatchControls();
    }
    
    updateBatchControls() {
        const selectedCount = this.selectedIdeas.size;
        const batchControls = document.getElementById('batchControls');
        const selectedCountSpan = document.getElementById('selectedCount');
        
        if (batchControls) {
            batchControls.style.display = selectedCount > 0 ? 'block' : 'none';
        }
        
        if (selectedCountSpan) {
            selectedCountSpan.textContent = selectedCount;
        }
    }
    
    updateIdeaCount() {
        const countElement = document.getElementById('ideasCount');
        if (countElement) {
            countElement.textContent = this.filteredIdeas.length;
        }
    }
    
    getPriorityColor(priority) {
        const colors = {
            'high': 'danger',
            'medium': 'warning',
            'low': 'success'
        };
        return colors[priority] || 'secondary';
    }
    
    getStatusColor(status) {
        const colors = {
            'pending': 'secondary',
            'in_progress': 'primary',
            'completed': 'success',
            'on_hold': 'warning'
        };
        return colors[status] || 'secondary';
    }
    
    formatDate(dateString) {
        if (!dateString) return '';
        return new Date(dateString).toLocaleDateString();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showSuccess(message) {
        this.showToast(message, 'success');
    }
    
    showError(message) {
        this.showToast(message, 'danger');
    }
    
    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        // Add to toast container
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast element after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}

// Initialize ideas manager when DOM is loaded
let ideasManager;
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('ideas-panel')) {
        ideasManager = new IdeasManager();
    }
});