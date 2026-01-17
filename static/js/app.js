// Research Agent Frontend JavaScript

// Check agent status on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAgentStatus();
    loadAvailableModels();
});

function updateTokenValue(value) {
    document.getElementById('token-value').textContent = value;
}

async function checkAgentStatus() {
    const statusEl = document.getElementById('status');
    const modelInfoEl = document.getElementById('model-info');
    
    try {
        // Check health
        const healthResponse = await fetch('/health');
        const healthData = await healthResponse.json();
        
        // Check agent info
        const infoResponse = await fetch('/agent/info');
        const infoData = await infoResponse.json();
        
        if (infoData.status === 'ready') {
            statusEl.textContent = '✓ Ready';
            statusEl.className = 'status healthy';
            modelInfoEl.textContent = `Default Model: ${infoData.model}`;
        } else {
            statusEl.textContent = '⚠ Not Configured';
            statusEl.className = 'status error';
            modelInfoEl.textContent = 'Please set GOOGLE_API_KEY';
        }
    } catch (error) {
        statusEl.textContent = '✗ Error';
        statusEl.className = 'status error';
        modelInfoEl.textContent = 'Failed to connect';
        console.error('Status check failed:', error);
    }
}

async function loadAvailableModels() {
    const modelSelect = document.getElementById('model-select');
    
    try {
        const response = await fetch('/models');
        const data = await response.json();
        
        if (data.models && data.models.length > 0) {
            // Clear loading option
            modelSelect.innerHTML = '';
            
            // Add models to dropdown (already sorted by price from backend)
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                // Include price indicator in the display
                const priceIndicator = model.price_indicator || '💰';
                option.textContent = `${priceIndicator} ${model.display_name} (${model.name})`;
                modelSelect.appendChild(option);
            });
            
            // Set default to gemini-2.0-flash-exp if available
            const defaultModel = data.models.find(m => m.name === 'gemini-2.0-flash-exp');
            if (defaultModel) {
                modelSelect.value = 'gemini-2.0-flash-exp';
            }
        } else {
            modelSelect.innerHTML = '<option value="">No models available</option>';
        }
    } catch (error) {
        console.error('Failed to load models:', error);
        modelSelect.innerHTML = '<option value="gemini-2.0-flash-exp">💰 gemini-2.0-flash-exp (default)</option>';
    }
}

async function performResearch() {
    const queryInput = document.getElementById('query-input');
    const modelSelect = document.getElementById('model-select');
    const tokenLimit = document.getElementById('token-limit');
    const resultsSection = document.getElementById('results-section');
    const resultsContent = document.getElementById('results-content');
    const loading = document.getElementById('loading');
    const researchBtn = document.getElementById('research-btn');
    
    const query = queryInput.value.trim();
    const selectedModel = modelSelect.value;
    const maxTokens = parseInt(tokenLimit.value);
    
    if (!query) {
        alert('Please enter a research question');
        return;
    }
    
    if (!selectedModel) {
        alert('Please select a model');
        return;
    }
    
    // Show loading state
    loading.style.display = 'block';
    resultsSection.style.display = 'none';
    researchBtn.disabled = true;
    
    try {
        const response = await fetch('/research', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                query: query,
                model: selectedModel,
                max_tokens: maxTokens
            })
        });
        
        if (!response.ok) {
            if (response.status === 429) {
                // Rate limit error
                const errorData = await response.json();
                throw new Error(`⏱️ Rate Limit: ${errorData.detail || 'Too many requests. Please wait a moment.'}`);
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Clear previous results
        resultsContent.innerHTML = '';
        
        // Display model info
        const modelInfo = document.createElement('div');
        modelInfo.style.cssText = 'color: #6c757d; font-size: 0.9em; margin-bottom: 10px; font-style: italic;';
        modelInfo.innerHTML = `Response from: <strong>${data.model}</strong> | Max tokens: <strong>${maxTokens}</strong>`;
        resultsContent.appendChild(modelInfo);
        
        // Display token usage in a separate styled div (always show, even if 0)
        if (data.token_usage) {
            const tokenUsageDiv = document.createElement('div');
            tokenUsageDiv.style.cssText = `
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 15px;
                border-radius: 8px;
                margin-bottom: 15px;
                font-size: 0.9em;
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
            `;
            
            const promptTokens = data.token_usage.prompt_tokens || 0;
            const completionTokens = data.token_usage.completion_tokens || 0;
            const totalTokens = data.token_usage.total_tokens || 0;
            
            const isEstimated = totalTokens > 0 && (promptTokens + completionTokens > 0);
            const estimatedLabel = isEstimated ? '' : ' <span style="font-size:0.8em;">(estimated)</span>';
            
            tokenUsageDiv.innerHTML = `
                <strong>📊 Token Usage:</strong>${estimatedLabel}<br>
                Input: ${promptTokens} tokens | 
                Output: ${completionTokens} tokens | 
                <strong>Total: ${totalTokens} tokens</strong>
            `;
            resultsContent.appendChild(tokenUsageDiv);
        } else {
            // Fallback if no token_usage in response
            const tokenUsageDiv = document.createElement('div');
            tokenUsageDiv.style.cssText = `
                background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%);
                color: #000;
                padding: 12px 15px;
                border-radius: 8px;
                margin-bottom: 15px;
                font-size: 0.9em;
            `;
            tokenUsageDiv.innerHTML = `
                <strong>⚠️ Token Usage:</strong> Not available in response
            `;
            resultsContent.appendChild(tokenUsageDiv);
        }
        
        // Display the actual result
        const resultText = document.createElement('div');
        resultText.textContent = data.result;
        resultText.style.cssText = 'line-height: 1.6;';
        resultsContent.appendChild(resultText);
        
        resultsSection.style.display = 'block';
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
    } catch (error) {
        console.error('Research failed:', error);
        resultsContent.textContent = `Error: ${error.message}\n\nPlease make sure GOOGLE_API_KEY is configured.`;
        resultsSection.style.display = 'block';
    } finally {
        loading.style.display = 'none';
        researchBtn.disabled = false;
    }
}

// Allow Enter key to submit (Ctrl/Cmd + Enter in textarea)
document.getElementById('query-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        performResearch();
    }
});
