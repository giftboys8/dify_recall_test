// 前端调试工具 - 添加到页面中用于调试翻译结果显示问题

// 在控制台中调用这些函数来调试
window.debugTranslation = {
    // 模拟一个成功的翻译响应来测试显示功能
    testDisplayResults: function() {
        console.log('Testing displayTranslationResults with mock data...');
        
        const mockResult = {
            success: true,
            data: {
                processing_time: 5.2,
                original_text_count: 150,
                translated_text_count: 180,
                provider: 'nllb',
                input_file: 'test.pdf',
                timestamp: new Date().toISOString(),
                output_files: [
                    {
                        filename: 'test_translated.docx',
                        download_url: '/api/download/test_translated.docx',
                        size: 25600
                    }
                ]
            }
        };
        
        // 调用实际的显示函数
        if (window.pdfTranslator && window.pdfTranslator.displayTranslationResults) {
            window.pdfTranslator.displayTranslationResults(mockResult);
            console.log('Mock result displayed');
        } else {
            console.error('pdfTranslator.displayTranslationResults not found');
        }
    },
    
    // 检查DOM元素状态
    checkElements: function() {
        console.log('Checking DOM elements...');
        
        const elements = {
            translationResults: document.getElementById('translationResults'),
            translationInfo: document.getElementById('translationInfo'),
            downloadLinks: document.getElementById('downloadLinks')
        };
        
        Object.keys(elements).forEach(key => {
            const element = elements[key];
            if (element) {
                console.log(`${key}:`, {
                    exists: true,
                    display: window.getComputedStyle(element).display,
                    visibility: window.getComputedStyle(element).visibility,
                    innerHTML: element.innerHTML.substring(0, 100) + '...'
                });
            } else {
                console.log(`${key}: NOT FOUND`);
            }
        });
    },
    
    // 强制显示翻译结果区域
    forceShow: function() {
        console.log('Force showing translation results...');
        
        const resultsDiv = document.getElementById('translationResults');
        if (resultsDiv) {
            resultsDiv.style.display = 'block';
            resultsDiv.style.visibility = 'visible';
            console.log('Translation results forced to show');
        } else {
            console.error('translationResults element not found');
        }
    },
    
    // 监听翻译API调用
    interceptFetch: function() {
        console.log('Setting up fetch interception...');
        
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            const url = args[0];
            if (url.includes('/api/translation/translate')) {
                console.log('Translation API call detected:', args);
                
                return originalFetch.apply(this, args).then(response => {
                    console.log('Translation API response:', response);
                    
                    // 克隆响应以便我们可以读取它
                    const clonedResponse = response.clone();
                    clonedResponse.json().then(data => {
                        console.log('Translation API response data:', data);
                    }).catch(err => {
                        console.error('Failed to parse response JSON:', err);
                    });
                    
                    return response;
                });
            }
            return originalFetch.apply(this, args);
        };
        
        console.log('Fetch interception set up. Now perform a translation to see the API response.');
    },
    
    // 重置fetch拦截
    resetFetch: function() {
        // 这个函数需要在页面刷新后重新设置
        console.log('Please refresh the page to reset fetch interception');
    }
};

// 自动运行一些检查
console.log('Debug tools loaded. Available functions:');
console.log('- debugTranslation.testDisplayResults() - Test with mock data');
console.log('- debugTranslation.checkElements() - Check DOM elements');
console.log('- debugTranslation.forceShow() - Force show results area');
console.log('- debugTranslation.interceptFetch() - Monitor API calls');

// 自动检查元素状态
debugTranslation.checkElements();