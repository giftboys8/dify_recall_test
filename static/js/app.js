// Dify KB Recall Testing Tool - Web Interface JavaScript

class DifyTestApp {
    constructor() {
        this.testCases = [];
        this.testResults = [];
        this.config = {};
        
        // Element ID constants for better maintainability
        this.ELEMENT_IDS = {
            PDF_FILE_INPUT: 'pdfFileInput',
            START_TRANSLATION_BTN: 'startTranslationBtn',
            TRANSLATION_PROGRESS: 'translationProgress',
            PROGRESS_BAR: 'progressBar',
            PROGRESS_TEXT: 'progressText',
            PROGRESS_DETAILS: 'progressDetails',
            TRANSLATION_RESULT: 'translationResult',
            TRANSLATION_RESULTS: 'translationResults',
            TRANSLATION_INFO: 'translationInfo',
            DOWNLOAD_LINKS: 'downloadLinks',
            HISTORY_TABLE: 'historyTable',
            FILE_INFO: 'fileInfo',
            FILE_NAME: 'fileName',
            FILE_SIZE: 'fileSize',
            UPLOAD_TIME: 'uploadTime',
            UPLOAD_AREA: 'uploadArea',
            RESULT_CARD: 'resultCard'
        };
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadConfig();
        this.loadTestCases();
        this.loadResults();
        this.loadTranslationConfig();
    }

    bindEvents() {
        // Configuration form (only for recall testing page)
        const configForm = document.getElementById('configForm');
        if (configForm) {
            configForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveConfig();
            });
        }

        // Test case management (only for recall testing page)
        const loadCsvBtn = document.getElementById('loadCsvBtn');
        if (loadCsvBtn) {
            loadCsvBtn.addEventListener('click', () => this.loadCsvFile());
        }
        
        const clearCasesBtn = document.getElementById('clearCasesBtn');
        if (clearCasesBtn) {
            clearCasesBtn.addEventListener('click', () => this.clearTestCases());
        }
        
        const addCaseBtn = document.getElementById('addCaseBtn');
        if (addCaseBtn) {
            addCaseBtn.addEventListener('click', () => this.showAddCaseModal());
        }
        
        const saveCaseBtn = document.getElementById('saveCaseBtn');
        if (saveCaseBtn) {
            saveCaseBtn.addEventListener('click', () => this.saveTestCase());
        }

        // Test execution (only for recall testing page)
        const runTestBtn = document.getElementById('runTestBtn');
        if (runTestBtn) {
            runTestBtn.addEventListener('click', () => this.runTests());
        }
        
        const clearResultsBtn = document.getElementById('clearResultsBtn');
        if (clearResultsBtn) {
            clearResultsBtn.addEventListener('click', () => this.clearResults());
        }

        // Export functions (only for recall testing page)
        const exportCsvBtn = document.getElementById('exportCsvBtn');
        if (exportCsvBtn) {
            exportCsvBtn.addEventListener('click', () => this.exportResults('csv'));
        }
        
        const exportJsonBtn = document.getElementById('exportJsonBtn');
        if (exportJsonBtn) {
            exportJsonBtn.addEventListener('click', () => this.exportResults('json'));
        }
        
        // Advanced settings event listeners (only for recall testing page)
        const scoreThresholdEnabled = document.getElementById('scoreThresholdEnabled');
        if (scoreThresholdEnabled) {
            scoreThresholdEnabled.addEventListener('change', () => {
                this.updateAdvancedSettingsUI();
            });
        }
        
        const rerankingEnabled = document.getElementById('rerankingEnabled');
        if (rerankingEnabled) {
            rerankingEnabled.addEventListener('change', () => {
                this.updateAdvancedSettingsUI();
            });
        }
        
        const rerankingProvider = document.getElementById('rerankingProvider');
        if (rerankingProvider) {
            rerankingProvider.addEventListener('change', (e) => {
                const provider = e.target.value;
                const modelInput = document.getElementById('rerankingModel');
                if (modelInput) {
                    if (provider === 'jina') {
                        modelInput.value = 'jina-reranker-v2-base-multilingual';
                    } else {
                        modelInput.value = '';
                    }
                }
            });
        }
        
        // PDF Translation events
        this.bindTranslationEvents();
        
        // Translation settings form (only for translation page)
        const translationSettingsForm = document.getElementById('translationSettingsForm');
        if (translationSettingsForm) {
            translationSettingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveTranslationConfig();
            });
        }
        
        // Tab switching events
        this.bindTabEvents();
        
        // Translation provider change event (only for translation page)
        const translationProvider = document.getElementById('translationProvider');
        if (translationProvider) {
            translationProvider.addEventListener('change', () => {
                this.updateTranslationProviderUI();
            });
        }
        
        // Smart chunking toggle event (only for translation page)
        const useSmartChunking = document.getElementById('useSmartChunking');
        if (useSmartChunking) {
            useSmartChunking.addEventListener('change', () => {
                this.updateChunkingSettingsUI();
            });
        }
    }

    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            if (response.ok) {
                this.config = await response.json();
                this.populateConfigForm();
            }
        } catch (error) {
            console.error('Error loading config:', error);
        }
    }

    populateConfigForm() {
        const api = this.config.api || {};
        
        const apiBaseUrl = document.getElementById('apiBaseUrl');
        if (apiBaseUrl) apiBaseUrl.value = api.base_url || '';
        
        const datasetId = document.getElementById('datasetId');
        if (datasetId) datasetId.value = api.dataset_id || '';
        
        const testing = this.config.testing || {};
        const topK = document.getElementById('topK');
        if (topK) topK.value = testing.top_k || 10;
        
        // Advanced settings
        const testSettings = this.config.test_settings || {};
        
        // Search method
        const searchMethod = document.getElementById('searchMethod');
        if (searchMethod) searchMethod.value = testSettings.search_method || 'semantic_search';
        
        // Reranking settings
        const rerankingEnabled = document.getElementById('rerankingEnabled');
        if (rerankingEnabled) rerankingEnabled.checked = testSettings.reranking_enabled !== false;
        
        const rerankingModel = testSettings.reranking_model || {};
        const rerankingProvider = document.getElementById('rerankingProvider');
        if (rerankingProvider) rerankingProvider.value = rerankingModel.provider || '';
        
        const rerankingModelEl = document.getElementById('rerankingModel');
        if (rerankingModelEl) rerankingModelEl.value = rerankingModel.model || (rerankingModel.provider === 'jina' ? 'jina-reranker-v2-base-multilingual' : '');
        
        // Embedding settings
        const embeddingModel = testSettings.embedding_model || {};
        const embeddingProvider = document.getElementById('embeddingProvider');
        if (embeddingProvider) embeddingProvider.value = embeddingModel.provider || 'zhipuai';
        
        const embeddingModelEl = document.getElementById('embeddingModel');
        if (embeddingModelEl) embeddingModelEl.value = embeddingModel.model || 'embedding-3';
        
        // Score threshold
        const scoreThresholdEnabled = document.getElementById('scoreThresholdEnabled');
        if (scoreThresholdEnabled) scoreThresholdEnabled.checked = testSettings.score_threshold_enabled || false;
        
        const scoreThreshold = document.getElementById('scoreThreshold');
        if (scoreThreshold) scoreThreshold.value = testSettings.score_threshold || 0.55;
        
        // Delay
        const delayBetweenRequests = document.getElementById('delayBetweenRequests');
        if (delayBetweenRequests) delayBetweenRequests.value = testSettings.delay_between_requests || 1.0;
        
        // Update UI based on settings
        this.updateAdvancedSettingsUI();
    }
    
    updateAdvancedSettingsUI() {
        // Show/hide score threshold settings
        const scoreThresholdEnabledEl = document.getElementById('scoreThresholdEnabled');
        const scoreThresholdSettings = document.getElementById('scoreThresholdSettings');
        
        if (scoreThresholdEnabledEl && scoreThresholdSettings) {
            const scoreThresholdEnabled = scoreThresholdEnabledEl.checked;
            scoreThresholdSettings.style.display = scoreThresholdEnabled ? 'block' : 'none';
        }
        
        // Show/hide reranking settings
        const rerankingEnabledEl = document.getElementById('rerankingEnabled');
        const rerankingSettings = document.getElementById('rerankingSettings');
        
        if (rerankingEnabledEl && rerankingSettings) {
            const rerankingEnabled = rerankingEnabledEl.checked;
            rerankingSettings.style.display = rerankingEnabled ? 'block' : 'none';
        }
    }

    async saveConfig() {
        // Get all DOM elements with null checks
        const apiBaseUrl = document.getElementById('apiBaseUrl');
        const apiKey = document.getElementById('apiKey');
        const datasetId = document.getElementById('datasetId');
        const topK = document.getElementById('topK');
        const delayBetweenRequests = document.getElementById('delayBetweenRequests');
        const scoreThresholdEnabled = document.getElementById('scoreThresholdEnabled');
        const scoreThreshold = document.getElementById('scoreThreshold');
        const rerankingEnabled = document.getElementById('rerankingEnabled');
        const searchMethod = document.getElementById('searchMethod');
        const rerankingProvider = document.getElementById('rerankingProvider');
        const rerankingModel = document.getElementById('rerankingModel');
        const embeddingProvider = document.getElementById('embeddingProvider');
        const embeddingModelEl = document.getElementById('embeddingModel');
        
        const config = {
            api: {
                base_url: apiBaseUrl ? apiBaseUrl.value : '',
                api_key: apiKey ? apiKey.value : '',
                dataset_id: datasetId ? datasetId.value : ''
            },
            testing: {
                top_k: topK ? parseInt(topK.value) : 10,
                delay_between_requests: delayBetweenRequests ? parseFloat(delayBetweenRequests.value) : 1.0,
                score_threshold_enabled: scoreThresholdEnabled ? scoreThresholdEnabled.checked : false,
                score_threshold: scoreThreshold ? parseFloat(scoreThreshold.value) : 0.55,
                reranking_enabled: rerankingEnabled ? rerankingEnabled.checked : false
            },
            test_settings: {
                search_method: searchMethod ? searchMethod.value : 'semantic_search',
                reranking_enabled: rerankingEnabled ? rerankingEnabled.checked : false,
                reranking_model: {
                    provider: rerankingProvider ? rerankingProvider.value : '',
                    model: rerankingModel ? rerankingModel.value : ''
                },
                embedding_model: {
                    provider: embeddingProvider ? embeddingProvider.value : 'zhipuai',
                    model: embeddingModelEl ? embeddingModelEl.value : 'embedding-3'
                },
                score_threshold_enabled: scoreThresholdEnabled ? scoreThresholdEnabled.checked : false,
                score_threshold: scoreThreshold ? parseFloat(scoreThreshold.value) : 0.55,
                delay_between_requests: delayBetweenRequests ? parseFloat(delayBetweenRequests.value) : 1.0
            }
        };

        try {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                this.showAlert('Configuration saved successfully!', 'success');
                this.config = config;
            } else {
                const error = await response.json();
                this.showAlert(`Error saving configuration: ${error.error}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Error saving configuration: ${error.message}`, 'danger');
        }
    }

    async saveTranslationConfig() {
        const config = this.getTranslationConfig();
        if (!config) {
            return;
        }

        try {
            const response = await fetch('/api/translation/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                this.showAlert('Translation configuration saved successfully!', 'success');
                // Store config locally for future use
                localStorage.setItem('translationConfig', JSON.stringify(config));
            } else {
                const error = await response.json();
                this.showAlert(`Error saving translation configuration: ${error.error}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Error saving translation configuration: ${error.message}`, 'danger');
        }
    }

    async loadTranslationConfig() {
        try {
            // First try to load from backend
            const response = await fetch('/api/translation/config');
            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data) {
                    this.populateTranslationConfigForm(result.data);
                    // Also save to localStorage as backup
                    localStorage.setItem('translationConfig', JSON.stringify(result.data));
                    return;
                }
            }
            
            // If backend fails, try localStorage
            const savedConfig = localStorage.getItem('translationConfig');
            if (savedConfig) {
                const config = JSON.parse(savedConfig);
                this.populateTranslationConfigForm(config);
            }
        } catch (error) {
            console.error('Error loading translation config:', error);
            // Try localStorage as fallback
            try {
                const savedConfig = localStorage.getItem('translationConfig');
                if (savedConfig) {
                    const config = JSON.parse(savedConfig);
                    this.populateTranslationConfigForm(config);
                }
            } catch (localError) {
                console.error('Error loading from localStorage:', localError);
            }
        }
    }

    populateTranslationConfigForm(config) {
        // Populate translation provider
        const providerElement = document.getElementById('translationProvider');
        if (providerElement && config.provider) {
            providerElement.value = config.provider;
        }

        // Populate API key
        const apiKeyElement = document.getElementById('translationApiKey');
        if (apiKeyElement && config.api_key) {
            apiKeyElement.value = config.api_key;
        }

        // Populate languages
        const sourceLanguageElement = document.getElementById('sourceLanguage');
        if (sourceLanguageElement && config.source_language) {
            sourceLanguageElement.value = config.source_language;
        }

        const targetLanguageElement = document.getElementById('targetLanguage');
        if (targetLanguageElement && config.target_language) {
            targetLanguageElement.value = config.target_language;
        }

        // Populate output format
        const outputFormatElement = document.getElementById('outputFormat');
        if (outputFormatElement && config.output_format) {
            outputFormatElement.value = config.output_format;
        }

        // Populate layout option
        const layoutOptionElement = document.getElementById('layoutOption');
        if (layoutOptionElement && config.layout) {
            layoutOptionElement.value = config.layout;
        }

        // Populate smart chunking settings
        const useSmartChunkingElement = document.getElementById('useSmartChunking');
        if (useSmartChunkingElement && config.use_smart_chunking !== undefined) {
            useSmartChunkingElement.checked = config.use_smart_chunking;
        }

        const maxChunkCharsElement = document.getElementById('maxChunkChars');
        if (maxChunkCharsElement && config.max_chunk_chars) {
            maxChunkCharsElement.value = config.max_chunk_chars;
        }

        const minChunkCharsElement = document.getElementById('minChunkChars');
        if (minChunkCharsElement && config.min_chunk_chars) {
            minChunkCharsElement.value = config.min_chunk_chars;
        }

        // Populate batch processing settings
        const batchSizeElement = document.getElementById('batchSize');
        if (batchSizeElement && config.batch_size) {
            batchSizeElement.value = config.batch_size;
        }

        const delayElement = document.getElementById('translationDelay');
        if (delayElement && config.delay) {
            delayElement.value = config.delay;
        }

        // Update UI states
        this.updateTranslationProviderUI();
        this.updateChunkingSettingsUI();
    }

    async loadCsvFile() {
        const fileInput = document.getElementById('csvFile');
        
        if (!fileInput) {
            this.showAlert('File input not found on this page.', 'warning');
            return;
        }
        
        const file = fileInput.files[0];
        
        if (!file) {
            this.showAlert('Please select a CSV file first.', 'warning');
            return;
        }

        try {
            const fileContent = await this.readFileAsText(file);
            
            const response = await fetch('/api/test-cases', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ file_content: fileContent })
            });

            if (response.ok) {
                const result = await response.json();
                this.showAlert(result.message, 'success');
                this.loadTestCases();
            } else {
                const error = await response.json();
                this.showAlert(`Error loading test cases: ${error.error}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Error loading CSV file: ${error.message}`, 'danger');
        }
    }

    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e);
            reader.readAsText(file);
        });
    }

    async loadTestCases() {
        try {
            const response = await fetch('/api/test-cases');
            if (response.ok) {
                this.testCases = await response.json();
                this.updateTestCasesTable();
                this.updateTestCaseCount();
            }
        } catch (error) {
            console.error('Error loading test cases:', error);
        }
    }

    updateTestCasesTable() {
        const tbody = document.querySelector('#testCasesTable tbody');
        
        if (!tbody) {
            // Only show warning if we're on a page that should have this table
            if (window.location.pathname.includes('recall') || window.location.pathname === '/') {
                console.warn('Test cases table not found on this page');
            }
            return;
        }
        
        if (this.testCases.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No test cases loaded</td></tr>';
            return;
        }

        tbody.innerHTML = this.testCases.map(tc => `
            <tr>
                <td>${this.escapeHtml(tc.id)}</td>
                <td title="${this.escapeHtml(tc.query)}">${this.truncateText(tc.query, 50)}</td>
                <td title="${this.escapeHtml(tc.expected_answer || '')}">${this.truncateText(tc.expected_answer || '', 30)}</td>
                <td>${this.escapeHtml(tc.category || '')}</td>
            </tr>
        `).join('');
    }

    updateTestCaseCount() {
        const testCaseCount = document.getElementById('testCaseCount');
        if (testCaseCount) {
            testCaseCount.textContent = this.testCases.length;
        }
    }

    async clearTestCases() {
        if (!confirm('Are you sure you want to clear all test cases?')) {
            return;
        }

        try {
            const response = await fetch('/api/test-cases/clear', {
                method: 'POST'
            });

            if (response.ok) {
                this.testCases = [];
                this.updateTestCasesTable();
                this.updateTestCaseCount();
                this.showAlert('Test cases cleared successfully!', 'success');
            }
        } catch (error) {
            this.showAlert(`Error clearing test cases: ${error.message}`, 'danger');
        }
    }

    showAddCaseModal() {
        const addCaseModal = document.getElementById('addCaseModal');
        if (addCaseModal) {
            const modal = new bootstrap.Modal(addCaseModal);
            modal.show();
        }
    }

    async saveTestCase() {
        const newCaseId = document.getElementById('newCaseId');
        const newCaseQuery = document.getElementById('newCaseQuery');
        const newCaseAnswer = document.getElementById('newCaseAnswer');
        const newCaseCategory = document.getElementById('newCaseCategory');
        
        const testCase = {
            id: newCaseId ? newCaseId.value : '',
            query: newCaseQuery ? newCaseQuery.value : '',
            expected_answer: newCaseAnswer ? newCaseAnswer.value : '',
            category: newCaseCategory ? newCaseCategory.value : ''
        };

        if (!testCase.id || !testCase.query) {
            this.showAlert('Please fill in required fields (ID and Query).', 'warning');
            return;
        }

        try {
            const response = await fetch('/api/test-cases', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ test_case: testCase })
            });

            if (response.ok) {
                const result = await response.json();
                this.showAlert(result.message, 'success');
                this.loadTestCases();
                
                // Clear form and close modal
                const addCaseForm = document.getElementById('addCaseForm');
                if (addCaseForm) addCaseForm.reset();
                
                const addCaseModal = document.getElementById('addCaseModal');
                if (addCaseModal) {
                    const modal = bootstrap.Modal.getInstance(addCaseModal);
                    if (modal) modal.hide();
                }
            } else {
                const error = await response.json();
                this.showAlert(`Error saving test case: ${error.error}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Error saving test case: ${error.message}`, 'danger');
        }
    }

    async runTests() {
        if (this.testCases.length === 0) {
            this.showAlert('Please load test cases first.', 'warning');
            return;
        }

        if (!this.config.api || !this.config.api.api_key || !this.config.api.dataset_id) {
            this.showAlert('Please configure API settings first.', 'warning');
            return;
        }

        // Show loading state
        const runBtn = document.getElementById('runTestBtn');
        const loading = document.querySelector('.loading');
        
        if (runBtn) runBtn.disabled = true;
        if (loading) loading.style.display = 'block';

        try {
            const response = await fetch('/api/run-test', {
                method: 'POST'
            });

            if (response.ok) {
                const result = await response.json();
                this.showAlert(result.message, 'success');
                this.loadResults();
            } else {
                const error = await response.json();
                this.showAlert(`Error running tests: ${error.error}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Error running tests: ${error.message}`, 'danger');
        } finally {
            if (runBtn) runBtn.disabled = false;
            if (loading) loading.style.display = 'none';
        }
    }

    async loadResults() {
        try {
            const response = await fetch('/api/results');
            if (response.ok) {
                const data = await response.json();
                this.testResults = data.results;
                this.updateResultsTable();
                this.updateSummaryCards(data.summary);
            }
        } catch (error) {
            console.error('Error loading results:', error);
        }
    }

    updateResultsTable() {
        const tbody = document.querySelector('#resultsTable tbody');
        
        if (!tbody) {
            // Only show warning if we're on a page that should have this table
            if (window.location.pathname.includes('recall') || window.location.pathname === '/') {
                console.warn('Results table not found on this page');
            }
            return;
        }
        
        if (this.testResults.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No results available</td></tr>';
            return;
        }

        tbody.innerHTML = this.testResults.map(result => `
            <tr>
                <td>${this.escapeHtml(result.test_id)}</td>
                <td title="${this.escapeHtml(result.query)}">${this.truncateText(result.query, 40)}</td>
                <td><span class="${result.status === 'success' ? 'status-success' : 'status-error'}">
                    <i class="fas fa-${result.status === 'success' ? 'check-circle' : 'times-circle'}"></i>
                    ${result.status}
                </span></td>
                <td>${result.documents_count}</td>
                <td>${result.max_score ? result.max_score.toFixed(3) : 'N/A'}</td>
                <td>${result.avg_score ? result.avg_score.toFixed(3) : 'N/A'}</td>
                <td>${result.response_time.toFixed(2)}s</td>
            </tr>
        `).join('');
    }

    updateSummaryCards(summary) {
        if (!summary) return;
        
        const totalTests = document.getElementById('totalTests');
        const successfulTests = document.getElementById('successfulTests');
        const failedTests = document.getElementById('failedTests');
        const successRate = document.getElementById('successRate');
        
        if (!totalTests || !successfulTests || !failedTests || !successRate) {
            // Only show warning if we're on a page that should have these elements
            if (window.location.pathname.includes('recall') || window.location.pathname === '/') {
                console.warn('Summary card elements not found on this page');
            }
            return;
        }
        
        totalTests.textContent = summary.total || 0;
        successfulTests.textContent = summary.successful || 0;
        failedTests.textContent = summary.failed || 0;
        successRate.textContent = `${(summary.success_rate || 0).toFixed(1)}%`;
    }

    async clearResults() {
        if (!confirm('Are you sure you want to clear all results?')) {
            return;
        }

        try {
            const response = await fetch('/api/results/clear', {
                method: 'POST'
            });

            if (response.ok) {
                this.testResults = [];
                this.updateResultsTable();
                this.updateSummaryCards({});
                this.showAlert('Results cleared successfully!', 'success');
            }
        } catch (error) {
            this.showAlert(`Error clearing results: ${error.message}`, 'danger');
        }
    }

    async exportResults(format) {
        if (this.testResults.length === 0) {
            this.showAlert('No results to export.', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/export/${format}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `recall_test_results_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showAlert(`Results exported as ${format.toUpperCase()}!`, 'success');
            } else {
                const error = await response.json();
                this.showAlert(`Export failed: ${error.error}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Export failed: ${error.message}`, 'danger');
        }
    }

    showAlert(message, type) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    truncateText(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    // PDF Translation Methods
    bindTranslationEvents() {
        // Test translation
        const testTranslationBtn = document.getElementById('testTranslationBtn');
        if (testTranslationBtn) {
            testTranslationBtn.addEventListener('click', () => this.testTranslation());
        }
        
        // PDF translation
        const translatePdfBtn = document.getElementById('startTranslationBtn');
        if (translatePdfBtn) {
            translatePdfBtn.addEventListener('click', () => this.translatePdf());
        }
        
        // File upload events
        const selectFileBtn = document.getElementById('selectFileBtn');
        const pdfFileInput = document.getElementById('pdfFileInput');
        const uploadArea = document.getElementById('uploadArea');
        
        if (selectFileBtn && pdfFileInput) {
            selectFileBtn.addEventListener('click', () => {
                pdfFileInput.click();
            });
            
            pdfFileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileSelection(e.target.files[0]);
                }
            });
        }
        
        if (uploadArea) {
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('drag-over');
            });
            
            uploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('drag-over');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('drag-over');
                const files = e.dataTransfer.files;
                if (files.length > 0 && files[0].type === 'application/pdf') {
                    this.handleFileSelection(files[0]);
                }
            });
        }
        
        // Start translation button event is already bound above as translatePdfBtn
        
        // Cancel upload button
        const cancelUploadBtn = document.getElementById('cancelUploadBtn');
        if (cancelUploadBtn) {
            cancelUploadBtn.addEventListener('click', () => this.cancelUpload());
        }
        
        // Clear history button
        const clearHistoryBtn = document.getElementById('clearHistoryBtn');
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', () => this.clearTranslationHistory());
        }
        
        // Initialize UI states
        this.updateTranslationProviderUI();
        this.updateChunkingSettingsUI();
    }
    

    
    async testTranslation() {
        const testTextElement = document.getElementById('testText');
        if (!testTextElement) {
            this.showAlert('Test text input not found.', 'danger');
            return;
        }
        
        const testText = testTextElement.value.trim();
        if (!testText) {
            this.showAlert('Please enter text to test translation.', 'warning');
            return;
        }
        
        const config = this.getTranslationConfig();
        if (!config) return;
        
        const testBtn = document.getElementById('testTranslationBtn');
        if (!testBtn) {
            this.showAlert('Test button not found.', 'danger');
            return;
        }
        
        const originalText = testBtn.innerHTML;
        testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
        testBtn.disabled = true;
        
        try {
            const response = await fetch('/api/translation/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: testText,
                    ...config
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                const translatedText = result.data ? result.data.translated_text : result.translated_text;
                
                const testTranslationResult = document.getElementById('testTranslationResult');
                const testResult = document.getElementById('testResult');
                
                if (testTranslationResult && testResult) {
                    testTranslationResult.textContent = translatedText;
                    testResult.style.display = 'block';
                    this.showAlert('Translation test completed!', 'success');
                } else {
                    console.warn('Test result display elements not found');
                    this.showAlert('Translation completed, but unable to display result.', 'warning');
                }
            } else {
                const error = await response.json();
                this.showAlert(`Translation test failed: ${error.error}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Translation test failed: ${error.message}`, 'danger');
        } finally {
            testBtn.innerHTML = originalText;
            testBtn.disabled = false;
        }
    }
    
    // PDF翻译相关方法
    async translatePdf() {
        const fileInput = document.getElementById(this.ELEMENT_IDS.PDF_FILE_INPUT);
        
        if (!fileInput) {
            this.showAlert('文件输入元素未找到，请刷新页面重试', 'error');
            console.error('PDF file input element not found');
            return;
        }
        
        const file = fileInput.files && fileInput.files[0];
        
        if (!file) {
            this.showAlert('请先选择PDF文件', 'warning');
            return;
        }
        
        // 验证文件类型
        if (file.type !== 'application/pdf') {
            this.showAlert('请选择有效的PDF文件', 'error');
            return;
        }
        
        // 验证文件大小 (50MB limit)
        const maxSize = 50 * 1024 * 1024; // 50MB in bytes
        if (file.size > maxSize) {
            this.showAlert('文件大小不能超过50MB', 'error');
            return;
        }
        
        // 获取翻译配置
        const config = this.getTranslationConfig();
        if (!config) {
            this.showAlert('翻译配置无效，请检查设置', 'error');
            return;
        }
        
        // 创建FormData
        const formData = new FormData();
        formData.append('file', file);
        
        // 添加配置参数
        Object.keys(config).forEach(key => {
            formData.append(key, config[key]);
        });
        
        try {
            // 显示进度区域
            this.showTranslationProgress();
            
            // 禁用翻译按钮防止重复提交
            const translateBtn = document.getElementById(this.ELEMENT_IDS.START_TRANSLATION_BTN);
            if (translateBtn) {
                translateBtn.disabled = true;
                translateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 翻译中...';
            }
            
            // 使用流式翻译API
            const response = await fetch('/api/translation/translate/stream', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                // 开始监听进度
                this.monitorTranslationProgress(result.task_id);
            } else {
                this.handleTranslationError(result.error || '未知错误');
            }
            
        } catch (error) {
            console.error('Translation error:', error);
            this.handleTranslationError(error.message || '网络连接错误');
        }
    }
    
    // 显示翻译进度
    showTranslationProgress() {
        const progressContainer = document.getElementById(this.ELEMENT_IDS.TRANSLATION_PROGRESS);
        const progressBar = document.getElementById(this.ELEMENT_IDS.PROGRESS_BAR);
        const progressText = document.getElementById(this.ELEMENT_IDS.PROGRESS_TEXT);
        const progressDetails = document.getElementById(this.ELEMENT_IDS.PROGRESS_DETAILS);
        
        if (progressContainer) progressContainer.style.display = 'block';
        if (progressBar) progressBar.style.width = '0%';
        if (progressText) progressText.textContent = '准备开始翻译...';
        if (progressDetails) progressDetails.textContent = '';
        
        // 隐藏结果区域
        const resultElement = document.getElementById(this.ELEMENT_IDS.TRANSLATION_RESULT);
        if (resultElement) resultElement.style.display = 'none';
    }
    
    // 隐藏翻译进度
    hideTranslationProgress() {
        const progressContainer = document.getElementById(this.ELEMENT_IDS.TRANSLATION_PROGRESS);
        if (progressContainer) progressContainer.style.display = 'none';
        
        // 重新启用翻译按钮
        const translateBtn = document.getElementById(this.ELEMENT_IDS.START_TRANSLATION_BTN);
        if (translateBtn) {
            translateBtn.disabled = false;
            translateBtn.innerHTML = '<i class="fas fa-language"></i> 开始翻译';
        }
    }
    
    // 监听翻译进度
    monitorTranslationProgress(taskId) {
        // 使用轮询方式获取进度（也可以使用Server-Sent Events）
        const pollProgress = async () => {
            try {
                const response = await fetch(`/api/translation/progress/${taskId}`);
                const result = await response.json();
                
                if (result.success) {
                    const data = result.data;
                    this.updateProgressDisplay(data);
                    
                    // 如果任务完成或失败，停止轮询
                    if (data.status === 'completed') {
                        this.handleTranslationComplete(data.result);
                        return;
                    } else if (data.status === 'failed' || data.status === 'error') {
                        this.handleTranslationError(data.error);
                        return;
                    }
                    
                    // 继续轮询
                    setTimeout(pollProgress, 1000);
                } else {
                    this.handleTranslationError(result.error);
                }
            } catch (error) {
                this.handleTranslationError(error.message);
            }
        };
        
        // 开始轮询
        pollProgress();
    }
    
    // 更新进度显示
    updateProgressDisplay(data) {
        const progressBar = document.getElementById(this.ELEMENT_IDS.PROGRESS_BAR);
        const progressText = document.getElementById(this.ELEMENT_IDS.PROGRESS_TEXT);
        const progressDetails = document.getElementById(this.ELEMENT_IDS.PROGRESS_DETAILS);
        
        // 更新进度条
        if (progressBar && typeof data.progress === 'number') {
            progressBar.style.width = `${Math.min(100, Math.max(0, data.progress))}%`;
            progressBar.setAttribute('aria-valuenow', data.progress);
        }
        
        // 更新进度文本
        if (progressText && data.current_step) {
            progressText.textContent = data.current_step;
        }
        
        // 更新详细信息
        if (progressDetails) {
            if (data.total_texts > 0) {
                progressDetails.textContent = `进度: ${data.completed_texts || 0}/${data.total_texts} 个文本块`;
            } else {
                progressDetails.textContent = data.details || '';
            }
        }
    }
    
    // 处理翻译完成
    handleTranslationComplete(result) {
        this.hideTranslationProgress();
        this.displayTranslationResults(result);
        
        // 获取文件名和配置信息
        const data = result.data || result;
        const fileName = data.input_file || this.selectedFile?.name || '未知文件';
        const config = this.getTranslationConfig() || {};
        
        this.addToTranslationHistory(fileName, config, result);
        this.showAlert('翻译完成！', 'success');
    }
    
    // 处理翻译错误
    handleTranslationError(error) {
        console.error('Translation error:', error);
        this.hideTranslationProgress();
        
        // 获取错误信息
        let errorMessage = '未知错误';
        if (typeof error === 'string') {
            errorMessage = error;
        } else if (error && error.message) {
            errorMessage = error.message;
        } else if (error && error.error) {
            errorMessage = error.error;
        }
        
        // 显示错误信息
        const resultDiv = document.getElementById(this.ELEMENT_IDS.TRANSLATION_RESULT);
        if (resultDiv) {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <h5><i class="fas fa-exclamation-triangle"></i> 翻译失败</h5>
                    <p><strong>错误信息:</strong> ${this.escapeHtml(errorMessage)}</p>
                    <small class="text-muted">请检查文件格式、网络连接或翻译配置后重试。</small>
                </div>
            `;
            resultDiv.style.display = 'block';
        }
        
        // 显示简短的错误提示
        this.showAlert(`翻译失败: ${errorMessage}`, 'error');
    }
    
    // HTML转义函数
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getTranslationConfig() {
        const providerElement = document.getElementById('translationProvider');
        const sourceLanguageElement = document.getElementById('sourceLanguage');
        const targetLanguageElement = document.getElementById('targetLanguage');
        const outputFormatElement = document.getElementById('outputFormat');
        const layoutOptionElement = document.getElementById('layoutOption');
        
        // Check if required elements exist
        if (!providerElement || !sourceLanguageElement || !targetLanguageElement || !outputFormatElement || !layoutOptionElement) {
            this.showAlert('Translation configuration elements not found.', 'danger');
            return null;
        }
        
        const provider = providerElement.value;
        const sourceLanguage = sourceLanguageElement.value;
        const targetLanguage = targetLanguageElement.value;
        const outputFormat = outputFormatElement.value;
        const layoutOption = layoutOptionElement.value;
        
        // Smart chunking settings
        const useSmartChunkingElement = document.getElementById('useSmartChunking');
        const maxChunkCharsElement = document.getElementById('maxChunkChars');
        const minChunkCharsElement = document.getElementById('minChunkChars');
        
        const useSmartChunking = useSmartChunkingElement ? useSmartChunkingElement.checked : true;
        const maxChunkChars = maxChunkCharsElement ? parseInt(maxChunkCharsElement.value) || 1500 : 1500;
        const minChunkChars = minChunkCharsElement ? parseInt(minChunkCharsElement.value) || 50 : 50;
        
        // Batch processing settings
        const batchSizeElement = document.getElementById('batchSize');
        const delayElement = document.getElementById('translationDelay');
        
        const batchSize = batchSizeElement ? parseInt(batchSizeElement.value) || 10 : 10;
        const delay = delayElement ? parseFloat(delayElement.value) || 1.0 : 1.0;
        
        if (sourceLanguage === targetLanguage) {
            this.showAlert('Source and target languages cannot be the same.', 'warning');
            return null;
        }
        
        const config = {
            provider,
            source_language: sourceLanguage,
            target_language: targetLanguage,
            output_format: outputFormat,
            layout: layoutOption,
            use_smart_chunking: useSmartChunking,
            max_chunk_chars: maxChunkChars,
            min_chunk_chars: minChunkChars,
            batch_size: batchSize,
            delay: delay
        };
        
        if (['openai', 'deepseek', 'deepseek-reasoner'].includes(provider)) {
            const apiKeyElement = document.getElementById('translationApiKey');
            if (!apiKeyElement) {
                this.showAlert('API key input field not found.', 'danger');
                return null;
            }
            
            const apiKey = apiKeyElement.value.trim();
            if (!apiKey) {
                const providerName = provider === 'openai' ? 'OpenAI' : 'DeepSeek';
                this.showAlert(`Please enter ${providerName} API key.`, 'warning');
                return null;
            }
            config.api_key = apiKey;
        }
        
        return config;
    }
    
    handleFileSelection(file) {
        // Validate file type
        if (file.type !== 'application/pdf') {
            this.showAlert('请选择PDF文件', 'warning');
            return;
        }
        
        // Validate file size (50MB limit)
        if (file.size > 50 * 1024 * 1024) {
            this.showAlert('文件大小超过50MB限制', 'danger');
            return;
        }
        
        // Store the selected file
        this.selectedFile = file;
        
        // Update UI to show file info
        const fileInfo = document.getElementById(this.ELEMENT_IDS.FILE_INFO);
        const fileName = document.getElementById(this.ELEMENT_IDS.FILE_NAME);
        const fileSize = document.getElementById(this.ELEMENT_IDS.FILE_SIZE);
        const uploadTime = document.getElementById(this.ELEMENT_IDS.UPLOAD_TIME);
        
        if (fileInfo && fileName && fileSize && uploadTime) {
            fileName.textContent = file.name;
            fileSize.textContent = this.formatFileSize(file.size);
            uploadTime.textContent = new Date().toLocaleString();
            fileInfo.style.display = 'block';
        }
        
        // Hide upload area and show file info
        const uploadArea = document.getElementById(this.ELEMENT_IDS.UPLOAD_AREA);
        if (uploadArea) {
            uploadArea.style.display = 'none';
        }
        
        this.showAlert('文件选择成功，点击"开始翻译"按钮进行翻译', 'success');
    }
    
    cancelUpload() {
        // Clear selected file
        this.selectedFile = null;
        
        // Reset file input
        const pdfFileInput = document.getElementById(this.ELEMENT_IDS.PDF_FILE_INPUT);
        if (pdfFileInput) {
            pdfFileInput.value = '';
        }
        
        // Hide file info and show upload area
        const fileInfo = document.getElementById(this.ELEMENT_IDS.FILE_INFO);
        const uploadArea = document.getElementById(this.ELEMENT_IDS.UPLOAD_AREA);
        
        if (fileInfo) {
            fileInfo.style.display = 'none';
        }
        
        if (uploadArea) {
            uploadArea.style.display = 'block';
        }
        
        this.showAlert('已取消文件上传', 'info');
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    updateTranslationProviderUI() {
        const providerElement = document.getElementById('translationProvider');
        const apiKeyInput = document.getElementById('translationApiKey');
        
        if (!providerElement || !apiKeyInput) {
            return; // Elements don't exist on this page
        }
        
        const provider = providerElement.value;
        const apiKeyHelp = apiKeyInput.nextElementSibling;
        
        if (provider === 'nllb') {
            apiKeyInput.disabled = true;
            apiKeyInput.value = '';
            if (apiKeyHelp) {
                apiKeyHelp.textContent = 'NLLB本地模型无需API Key';
            }
        } else {
            apiKeyInput.disabled = false;
            const providerName = {
                'openai': 'OpenAI',
                'deepseek': 'DeepSeek',
                'deepseek-reasoner': 'DeepSeek Reasoner'
            }[provider] || provider;
            if (apiKeyHelp) {
                apiKeyHelp.textContent = `请输入${providerName} API Key`;
            }
        }
    }
    
    updateChunkingSettingsUI() {
        const useSmartChunking = document.getElementById('useSmartChunking');
        const chunkingSettings = document.getElementById('chunkingSettings');
        
        if (!useSmartChunking || !chunkingSettings) {
            return; // Elements don't exist on this page
        }
        
        chunkingSettings.style.display = useSmartChunking.checked ? 'block' : 'none';
    }
    
    displayTranslationResults(result) {
        const resultCard = document.getElementById(this.ELEMENT_IDS.RESULT_CARD);
        const translationResult = document.getElementById(this.ELEMENT_IDS.TRANSLATION_RESULT);
        
        // Check if required elements exist
        if (!resultCard || !translationResult) {
            console.warn('Translation results display elements not found');
            this.showAlert('无法显示翻译结果：页面元素缺失', 'warning');
            return;
        }
        
        // Handle the new API response format
        const data = result.data || result;
        
        let resultHtml = `
            <div class="mb-3">
                <h6><i class="fas fa-info-circle"></i> 翻译信息</h6>
                <div class="row">
                    <div class="col-md-6">
                        <strong>处理时间:</strong> ${data.processing_time}s<br>
                        <strong>原文字符数:</strong> ${data.original_text_count || 'N/A'}<br>
                        <strong>译文字符数:</strong> ${data.translated_text_count || 'N/A'}
                    </div>
                    <div class="col-md-6">
                        <strong>翻译提供商:</strong> ${data.provider}<br>
                        <strong>输入文件:</strong> ${data.input_file}<br>
                        <strong>完成时间:</strong> ${new Date(data.timestamp).toLocaleString()}
                    </div>
                </div>
            </div>
        `;
        
        if (data.output_files && data.output_files.length > 0) {
            resultHtml += `
                <div class="mb-3">
                    <h6><i class="fas fa-download"></i> 下载文件</h6>
                    <div class="d-flex flex-wrap gap-2">
            `;
            data.output_files.forEach(file => {
                resultHtml += `
                    <a href="${file.download_url}" class="btn btn-outline-primary" download>
                        <i class="fas fa-download"></i> ${file.filename}
                    </a>
                `;
            });
            resultHtml += `
                    </div>
                </div>
            `;
        } else {
            resultHtml += '<div class="alert alert-warning">没有可下载的文件</div>';
        }
        
        translationResult.innerHTML = resultHtml;
        resultCard.style.display = 'block';
    }
    
    addToTranslationHistory(fileName, config, result) {
        const historyTableElement = document.getElementById(this.ELEMENT_IDS.HISTORY_TABLE);
        if (!historyTableElement) {
            console.warn('Translation history table not found');
            return;
        }
        
        const historyTable = historyTableElement.getElementsByTagName('tbody')[0];
        if (!historyTable) {
            console.warn('Translation history table body not found');
            return;
        }
        
        // Remove "No translation history" row if it exists
        const noHistoryRow = historyTable.querySelector('td[colspan="3"]');
        if (noHistoryRow) {
            noHistoryRow.parentElement.remove();
        }

        const row = historyTable.insertRow(0);
        const data = result.data || result;
        const timestamp = new Date().toLocaleString();
        const status = result.success ? '成功' : '失败';
        const statusClass = result.success ? 'text-success' : 'text-danger';

        // Create a clickable filename that shows download options
        const downloadLinks = data.output_files ? data.output_files.map(file => 
            `<a href="${file.download_url}" class="text-decoration-none" download title="下载 ${file.filename}">
                <i class="fas fa-download"></i>
            </a>`
        ).join(' ') : '';

        row.innerHTML = `
            <td>
                <span title="${fileName}">${fileName}</span>
                ${downloadLinks ? ` ${downloadLinks}` : ''}
            </td>
            <td><span class="${statusClass}">${status}</span></td>
            <td>${timestamp}</td>
        `;
    }
    
    clearTranslationHistory() {
        if (!confirm('确定要清空所有翻译历史吗？')) {
            return;
        }
        
        const historyTableElement = document.getElementById(this.ELEMENT_IDS.HISTORY_TABLE);
        if (!historyTableElement) {
            console.warn('Translation history table not found');
            return;
        }
        
        const historyTable = historyTableElement.getElementsByTagName('tbody')[0];
        if (!historyTable) {
            console.warn('Translation history table body not found');
            return;
        }
        
        // Clear all rows and add the "no history" message
        historyTable.innerHTML = '<tr><td colspan="3" class="text-center text-muted">暂无翻译历史</td></tr>';
        
        this.showAlert('翻译历史已清空', 'success');
    }
    
    // Tab switching event handling
    bindTabEvents() {
        const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
        tabButtons.forEach(button => {
            button.addEventListener('shown.bs.tab', (e) => {
                const targetPanel = e.target.getAttribute('data-bs-target');
                
                // When switching to PDF Translation tab, hide recall testing results
                if (targetPanel === '#translation-panel') {
                    this.hideRecallTestingResults();
                }
                // When switching to Recall Testing tab, hide translation results
                else if (targetPanel === '#recall-panel') {
                    this.hideTranslationResults();
                }
            });
        });
    }
    
    hideRecallTestingResults() {
        // Force hide the entire recall panel when switching to translation
        const recallPanel = document.getElementById('recall-panel');
        if (recallPanel) {
            recallPanel.style.display = 'none';
        }
        
        // Show translation panel
        const translationPanel = document.getElementById('translation-panel');
        if (translationPanel) {
            translationPanel.style.display = 'block';
        }
        
        // Reset test statistics to initial state
        const totalTests = document.getElementById('totalTests');
        const successfulTests = document.getElementById('successfulTests');
        const failedTests = document.getElementById('failedTests');
        const successRate = document.getElementById('successRate');
        
        if (totalTests) totalTests.textContent = '0';
        if (successfulTests) successfulTests.textContent = '0';
        if (failedTests) failedTests.textContent = '0';
        if (successRate) successRate.textContent = '0%';
        
        // Clear test cases table
        const testCasesTable = document.querySelector('#recall-panel #testCasesTable tbody');
        if (testCasesTable) {
            testCasesTable.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No test cases loaded</td></tr>';
        }
        
        // Clear test results table
        const testResultsTable = document.querySelector('#recall-panel #testResultsTable tbody');
        if (testResultsTable) {
            testResultsTable.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No results available</td></tr>';
        }
        
        // Hide loading indicator
        const loadingElement = document.querySelector('#recall-panel .loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
    
    hideTranslationResults() {
        // Force hide the entire translation panel when switching to recall testing
        const translationPanel = document.getElementById('translation-panel');
        if (translationPanel) {
            translationPanel.style.display = 'none';
        }
        
        // Show recall panel
        const recallPanel = document.getElementById('recall-panel');
        if (recallPanel) {
            recallPanel.style.display = 'block';
        }
        
        // Hide translation results panel
        const translationResults = document.getElementById(this.ELEMENT_IDS.TRANSLATION_RESULTS);
        if (translationResults) {
            translationResults.style.display = 'none';
        }
        
        // Clear translation info
        const translationInfo = document.getElementById('translationInfo');
        if (translationInfo) {
            translationInfo.innerHTML = '';
        }
        
        // Clear download links
        const downloadLinks = document.getElementById('downloadLinks');
        if (downloadLinks) {
            downloadLinks.innerHTML = '';
        }
        
        // Hide translation loading indicator
        const loadingTranslation = document.querySelector('#translation-panel .loading-translation');
        if (loadingTranslation) {
            loadingTranslation.style.display = 'none';
        }
        
        // Reset progress bar
        const progressBar = document.querySelector('#translation-panel .progress-bar');
        if (progressBar) {
            progressBar.style.width = '0%';
        }
        
        // Clear file input
        const pdfFile = document.getElementById('pdfFileInput');
        if (pdfFile) {
            pdfFile.value = '';
        }
        
        // Clear translation history table
        const translationHistoryTable = document.querySelector('#translation-panel .table tbody');
        if (translationHistoryTable) {
            translationHistoryTable.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No translation history</td></tr>';
        }
    }
}

// App initialization is handled in the HTML template to avoid duplicate instances