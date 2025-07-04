// Dify KB Recall Testing Tool - Web Interface JavaScript

class DifyTestApp {
    constructor() {
        this.testCases = [];
        this.testResults = [];
        this.config = {};
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadConfig();
        this.loadTestCases();
        this.loadResults();
    }

    bindEvents() {
        // Configuration form
        document.getElementById('configForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveConfig();
        });

        // Test case management
        document.getElementById('loadCsvBtn').addEventListener('click', () => this.loadCsvFile());
        document.getElementById('clearCasesBtn').addEventListener('click', () => this.clearTestCases());
        document.getElementById('addCaseBtn').addEventListener('click', () => this.showAddCaseModal());
        document.getElementById('saveCaseBtn').addEventListener('click', () => this.saveTestCase());

        // Test execution
        document.getElementById('runTestBtn').addEventListener('click', () => this.runTests());
        document.getElementById('clearResultsBtn').addEventListener('click', () => this.clearResults());

        // Export functions
        document.getElementById('exportCsvBtn').addEventListener('click', () => this.exportResults('csv'));
        document.getElementById('exportJsonBtn').addEventListener('click', () => this.exportResults('json'));
        
        // Advanced settings event listeners
        document.getElementById('scoreThresholdEnabled').addEventListener('change', () => {
            this.updateAdvancedSettingsUI();
        });
        
        document.getElementById('rerankingEnabled').addEventListener('change', () => {
            this.updateAdvancedSettingsUI();
        });
        
        document.getElementById('rerankingProvider').addEventListener('change', (e) => {
            const provider = e.target.value;
            const modelInput = document.getElementById('rerankingModel');
            if (provider === 'jina') {
                modelInput.value = 'jina-reranker-v2-base-multilingual';
            } else {
                modelInput.value = '';
            }
        });
        
        // PDF Translation events
        this.bindTranslationEvents();
        
        // Tab switching events
        this.bindTabEvents();
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
        document.getElementById('apiBaseUrl').value = api.base_url || '';
        document.getElementById('datasetId').value = api.dataset_id || '';
        
        const testing = this.config.testing || {};
        document.getElementById('topK').value = testing.top_k || 10;
        
        // Advanced settings
        const testSettings = this.config.test_settings || {};
        
        // Search method
        document.getElementById('searchMethod').value = testSettings.search_method || 'semantic_search';
        
        // Reranking settings
        document.getElementById('rerankingEnabled').checked = testSettings.reranking_enabled !== false;
        const rerankingModel = testSettings.reranking_model || {};
        document.getElementById('rerankingProvider').value = rerankingModel.provider || '';
        document.getElementById('rerankingModel').value = rerankingModel.model || (rerankingModel.provider === 'jina' ? 'jina-reranker-v2-base-multilingual' : '');
        
        // Embedding settings
        const embeddingModel = testSettings.embedding_model || {};
        document.getElementById('embeddingProvider').value = embeddingModel.provider || 'zhipuai';
        document.getElementById('embeddingModel').value = embeddingModel.model || 'embedding-3';
        
        // Score threshold
        document.getElementById('scoreThresholdEnabled').checked = testSettings.score_threshold_enabled || false;
        document.getElementById('scoreThreshold').value = testSettings.score_threshold || 0.55;
        
        // Delay
        document.getElementById('delayBetweenRequests').value = testSettings.delay_between_requests || 1.0;
        
        // Update UI based on settings
        this.updateAdvancedSettingsUI();
    }
    
    updateAdvancedSettingsUI() {
        // Show/hide score threshold settings
        const scoreThresholdEnabled = document.getElementById('scoreThresholdEnabled').checked;
        const scoreThresholdSettings = document.getElementById('scoreThresholdSettings');
        scoreThresholdSettings.style.display = scoreThresholdEnabled ? 'block' : 'none';
        
        // Show/hide reranking settings
        const rerankingEnabled = document.getElementById('rerankingEnabled').checked;
        const rerankingSettings = document.getElementById('rerankingSettings');
        rerankingSettings.style.display = rerankingEnabled ? 'block' : 'none';
    }

    async saveConfig() {
        const config = {
            api: {
                base_url: document.getElementById('apiBaseUrl').value,
                api_key: document.getElementById('apiKey').value,
                dataset_id: document.getElementById('datasetId').value
            },
            testing: {
                top_k: parseInt(document.getElementById('topK').value),
                delay_between_requests: parseFloat(document.getElementById('delayBetweenRequests').value),
                score_threshold_enabled: document.getElementById('scoreThresholdEnabled').checked,
                score_threshold: parseFloat(document.getElementById('scoreThreshold').value),
                reranking_enabled: document.getElementById('rerankingEnabled').checked
            },
            test_settings: {
                search_method: document.getElementById('searchMethod').value,
                reranking_enabled: document.getElementById('rerankingEnabled').checked,
                reranking_model: {
                    provider: document.getElementById('rerankingProvider').value,
                    model: document.getElementById('rerankingModel').value
                },
                embedding_model: {
                    provider: document.getElementById('embeddingProvider').value,
                    model: document.getElementById('embeddingModel').value
                },
                score_threshold_enabled: document.getElementById('scoreThresholdEnabled').checked,
                score_threshold: parseFloat(document.getElementById('scoreThreshold').value),
                delay_between_requests: parseFloat(document.getElementById('delayBetweenRequests').value)
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

    async loadCsvFile() {
        const fileInput = document.getElementById('csvFile');
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
        document.getElementById('testCaseCount').textContent = this.testCases.length;
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
        const modal = new bootstrap.Modal(document.getElementById('addCaseModal'));
        modal.show();
    }

    async saveTestCase() {
        const testCase = {
            id: document.getElementById('newCaseId').value,
            query: document.getElementById('newCaseQuery').value,
            expected_answer: document.getElementById('newCaseAnswer').value,
            category: document.getElementById('newCaseCategory').value
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
                document.getElementById('addCaseForm').reset();
                const modal = bootstrap.Modal.getInstance(document.getElementById('addCaseModal'));
                modal.hide();
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
        
        runBtn.disabled = true;
        loading.style.display = 'block';

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
            runBtn.disabled = false;
            loading.style.display = 'none';
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
        
        document.getElementById('totalTests').textContent = summary.total || 0;
        document.getElementById('successfulTests').textContent = summary.successful || 0;
        document.getElementById('failedTests').textContent = summary.failed || 0;
        document.getElementById('successRate').textContent = `${(summary.success_rate || 0).toFixed(1)}%`;
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
        // Translation provider change
        const translationProvider = document.getElementById('translationProvider');
        if (translationProvider) {
            translationProvider.addEventListener('change', (e) => {
                this.updateTranslationProviderUI(e.target.value);
            });
        }
        
        // Test translation
        const testTranslationBtn = document.getElementById('testTranslationBtn');
        if (testTranslationBtn) {
            testTranslationBtn.addEventListener('click', () => this.testTranslation());
        }
        
        // PDF translation
        const translatePdfBtn = document.getElementById('translatePdfBtn');
        if (translatePdfBtn) {
            translatePdfBtn.addEventListener('click', () => this.translatePdf());
        }
        
        // Initialize translation provider UI
        this.updateTranslationProviderUI('nllb');
        
        // Smart chunking settings toggle
        const useSmartChunking = document.getElementById('useSmartChunking');
        if (useSmartChunking) {
            useSmartChunking.addEventListener('change', (e) => {
                const chunkingSettings = document.getElementById('chunkingSettings');
                if (chunkingSettings) {
                    chunkingSettings.style.display = e.target.checked ? 'block' : 'none';
                }
            });
        }
    }
    
    updateTranslationProviderUI(provider) {
        const apiKeyGroup = document.getElementById('apiKeyGroup');
        if (apiKeyGroup) {
            // 显示API密钥输入框的提供商：openai, deepseek, deepseek-reasoner
            const needsApiKey = ['openai', 'deepseek', 'deepseek-reasoner'].includes(provider);
            apiKeyGroup.style.display = needsApiKey ? 'block' : 'none';
            
            // 更新API密钥标签
            const apiKeyLabel = apiKeyGroup.querySelector('label');
            if (apiKeyLabel) {
                if (provider === 'openai') {
                    apiKeyLabel.textContent = 'OpenAI API Key';
                } else if (provider === 'deepseek' || provider === 'deepseek-reasoner') {
                    apiKeyLabel.textContent = 'DeepSeek API Key';
                }
            }
        }
    }
    
    async testTranslation() {
        const testText = document.getElementById('testText').value.trim();
        if (!testText) {
            this.showAlert('Please enter text to test translation.', 'warning');
            return;
        }
        
        const config = this.getTranslationConfig();
        if (!config) return;
        
        const testBtn = document.getElementById('testTranslationBtn');
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
                document.getElementById('testTranslationResult').textContent = result.translated_text;
                document.getElementById('testResult').style.display = 'block';
                this.showAlert('Translation test completed!', 'success');
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
    
    async translatePdf() {
        const fileInput = document.getElementById('pdfFile');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showAlert('Please select a PDF file first.', 'warning');
            return;
        }
        
        if (file.size > 50 * 1024 * 1024) {
            this.showAlert('File size exceeds 50MB limit.', 'danger');
            return;
        }
        
        const config = this.getTranslationConfig();
        if (!config) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        // 将配置参数作为单独的表单字段添加
        formData.append('provider', config.provider);
        formData.append('source_language', config.source_language);
        formData.append('target_language', config.target_language);
        formData.append('output_format', config.output_format);
        formData.append('layout', config.layout);
        
        if (config.api_key) {
            formData.append('api_key', config.api_key);
        }
        
        const translateBtn = document.getElementById('translatePdfBtn');
        const loadingDiv = document.querySelector('.loading-translation');
        const progressBar = document.querySelector('.progress-bar');
        
        translateBtn.disabled = true;
        loadingDiv.style.display = 'block';
        
        try {
            const response = await fetch('/api/translation/translate', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                this.displayTranslationResults(result);
                this.addToTranslationHistory(file.name, config, result);
                this.showAlert('PDF translation completed!', 'success');
            } else {
                const error = await response.json();
                this.showAlert(`Translation failed: ${error.error}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Translation failed: ${error.message}`, 'danger');
        } finally {
            translateBtn.disabled = false;
            loadingDiv.style.display = 'none';
            progressBar.style.width = '0%';
        }
    }
    
    getTranslationConfig() {
        const provider = document.getElementById('translationProvider').value;
        const sourceLanguage = document.getElementById('sourceLanguage').value;
        const targetLanguage = document.getElementById('targetLanguage').value;
        const outputFormat = document.getElementById('outputFormat').value;
        const layoutOption = document.getElementById('layoutOption').value;
        
        // Smart chunking settings
        const useSmartChunking = document.getElementById('useSmartChunking').checked;
        const maxChunkChars = parseInt(document.getElementById('maxChunkChars').value) || 1500;
        const minChunkChars = parseInt(document.getElementById('minChunkChars').value) || 50;
        
        // Batch processing settings
        const batchSize = parseInt(document.getElementById('batchSize').value) || 10;
        const delay = parseFloat(document.getElementById('translationDelay').value) || 1.0;
        
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
            const apiKey = document.getElementById('translationApiKey').value.trim();
            if (!apiKey) {
                const providerName = provider === 'openai' ? 'OpenAI' : 'DeepSeek';
                this.showAlert(`Please enter ${providerName} API key.`, 'warning');
                return null;
            }
            config.api_key = apiKey;
        }
        
        return config;
    }
    
    displayTranslationResults(result) {
        const resultsDiv = document.getElementById('translationResults');
        const infoDiv = document.getElementById('translationInfo');
        const linksDiv = document.getElementById('downloadLinks');
        
        // Handle the new API response format
        const data = result.data || result;
        
        infoDiv.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <strong>Processing Time:</strong> ${data.processing_time}s<br>
                    <strong>Original Text Count:</strong> ${data.original_text_count || 'N/A'}<br>
                    <strong>Translated Text Count:</strong> ${data.translated_text_count || 'N/A'}
                </div>
                <div class="col-md-6">
                    <strong>Provider:</strong> ${data.provider}<br>
                    <strong>Input File:</strong> ${data.input_file}<br>
                    <strong>Timestamp:</strong> ${new Date(data.timestamp).toLocaleString()}
                </div>
            </div>
        `;
        
        let downloadHtml = '';
        if (data.output_files && data.output_files.length > 0) {
            data.output_files.forEach(file => {
                downloadHtml += `
                    <a href="${file.download_url}" class="btn btn-outline-primary me-2 mb-2" download>
                        <i class="fas fa-download"></i> Download ${file.filename}
                    </a>
                    <small class="text-muted d-block mb-2">Size: ${(file.size / 1024).toFixed(1)} KB</small>
                `;
            });
        } else {
            downloadHtml = '<p class="text-muted">No output files available for download.</p>';
        }
        
        linksDiv.innerHTML = downloadHtml;
        resultsDiv.style.display = 'block';
    }
    
    addToTranslationHistory(fileName, config, result) {
        const historyTable = document.getElementById('translationHistoryTable').getElementsByTagName('tbody')[0];
        
        // Remove "No translation history" row if it exists
        const noHistoryRow = historyTable.querySelector('td[colspan="7"]');
        if (noHistoryRow) {
            noHistoryRow.parentElement.remove();
        }
        
        const row = historyTable.insertRow(0);
        const data = result.data || result;
        const timestamp = new Date().toLocaleString();
        const languages = `${config.source_language} → ${config.target_language}`;
        const status = result.success ? 'Success' : 'Failed';
        const statusClass = result.success ? 'text-success' : 'text-danger';
        
        row.innerHTML = `
            <td>${fileName}</td>
            <td>${config.provider}</td>
            <td>${languages}</td>
            <td><span class="${statusClass}">${status}</span></td>
            <td>${data.processing_time}s</td>
            <td>${timestamp}</td>
            <td>
                ${data.output_files ? data.output_files.map(file => 
                    `<a href="${file.download_url}" class="btn btn-sm btn-outline-primary me-1" download>
                        <i class="fas fa-download"></i> ${file.filename}
                    </a>`
                ).join('') : ''}
            </td>
        `;
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
        const translationResults = document.getElementById('translationResults');
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
        const pdfFile = document.getElementById('pdfFile');
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

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DifyTestApp();
});