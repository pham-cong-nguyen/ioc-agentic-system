/**
 * StreamingStepTracker - Real-time step display with SSE
 * Shows reasoning steps as they happen (like OpenAI)
 * With character-level streaming and markdown rendering
 */

import { MarkdownRenderer, CharacterStreamRenderer } from '../utils/markdown.js';

export class StreamingStepTracker {
    constructor() {
        this.container = null;
        this.steps = [];
        this.apiCalls = [];
        this.eventSource = null;
        this.markdownRenderer = new MarkdownRenderer();
        this.currentStreamRenderer = null; // For streaming final answer
        this.streamingConfig = null; // Cache streaming config
    }

    /**
     * Fetch streaming configuration from backend
     */
    async fetchStreamingConfig() {
        if (this.streamingConfig) {
            return this.streamingConfig; // Use cached config
        }

        try {
            const baseURL = window.location.hostname === 'localhost' 
                ? 'http://localhost:8862/api/v1'
                : '/api/v1';
            
            const response = await fetch(`${baseURL}/agent/v2/streaming-config`);
            if (response.ok) {
                const data = await response.json();
                this.streamingConfig = data.data;
                console.log('✓ Loaded streaming config:', this.streamingConfig);
                return this.streamingConfig;
            }
        } catch (error) {
            console.warn('Failed to fetch streaming config, using defaults:', error);
        }

        // Default fallback
        this.streamingConfig = {
            charsPerFrame: 3,
            minDelay: 15,
            maxDelay: 35,
            internalCharsPerFrame: 5,
            internalMinDelay: 5,
            internalMaxDelay: 15
        };
        return this.streamingConfig;
    }

    /**
     * Start streaming query and display steps in real-time
     */
    async startStreaming(container, query, userId = 'default_user', conversationId = null) {
        this.container = container;
        this.steps = [];
        this.apiCalls = [];
        
        // Clear container
        container.innerHTML = '';
        
        // Create UI structure with collapsible internal steps
        const wrapper = document.createElement('div');
        wrapper.className = 'streaming-step-tracker';
        wrapper.innerHTML = `
            <div class="stream-header">
                <div class="stream-status">
                    <div class="status-indicator streaming"></div>
                    <span>Processing query...</span>
                </div>
            </div>
            
            <!-- Collapsible Internal Steps -->
            <div class="internal-steps-container">
                <button class="toggle-steps" id="toggleSteps">
                    <i class="fas fa-chevron-down"></i>
                    <span class="toggle-text">View reasoning steps</span>
                    <span class="steps-count">(0 steps)</span>
                </button>
                <div class="steps-content" id="stepsContent">
                    <div class="stream-steps" id="streamSteps"></div>
                </div>
            </div>
            
            <!-- Always Visible Final Answer -->
            <div class="final-answer-container" id="finalAnswerContainer" style="display:none;"></div>
            
            <!-- Metrics Footer -->
            <div class="stream-footer" id="streamFooter" style="display:none;">
                <div class="stream-metrics">
                    <span class="metric" id="totalSteps">Steps: 0</span>
                    <span class="metric" id="totalApiCalls">API Calls: 0</span>
                    <span class="metric" id="processingTime">Time: 0s</span>
                    <span class="metric" id="qualityScore">Quality: 0%</span>
                </div>
            </div>
        `;
        container.appendChild(wrapper);
        
        // Get references to key elements
        const stepsContainer = wrapper.querySelector('#streamSteps');
        const finalAnswerContainer = wrapper.querySelector('#finalAnswerContainer');
        const footer = wrapper.querySelector('#streamFooter');
        const toggleBtn = wrapper.querySelector('#toggleSteps');
        const stepsContent = wrapper.querySelector('#stepsContent');
        const stepsCountEl = wrapper.querySelector('.steps-count');
        
        // Setup toggle button
        let isExpanded = true; // Start expanded so user can see streaming
        
        toggleBtn.addEventListener('click', () => {
            isExpanded = !isExpanded;
            stepsContent.style.display = isExpanded ? 'block' : 'none';
            const icon = toggleBtn.querySelector('i');
            icon.className = isExpanded ? 'fas fa-chevron-down' : 'fas fa-chevron-right';
        });
        
        // Setup SSE
        const baseURL = window.location.hostname === 'localhost' 
            ? 'http://localhost:8862/api/v1'
            : '/api/v1';
        
        const url = `${baseURL}/agent/v2/query/stream`;
        
        // Use fetch with streaming response
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    user_id: userId,
                    conversation_id: conversationId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                
                // Process complete SSE messages
                const lines = buffer.split('\n\n');
                buffer = lines.pop(); // Keep incomplete message in buffer
                
                for (const line of lines) {
                    if (line.trim()) {
                        this.handleSSEMessage(line, stepsContainer, finalAnswerContainer, footer, stepsCountEl);
                    }
                }
            }
            
        } catch (error) {
            console.error('Streaming error:', error);
            this.showError(stepsContainer, error.message);
        }
    }
    
    /**
     * Handle incoming SSE message
     */
    handleSSEMessage(message, stepsContainer, finalAnswerContainer, footer, stepsCountEl) {
        const lines = message.split('\n');
        let eventType = 'message';
        let data = null;
        
        for (const line of lines) {
            if (line.startsWith('event:')) {
                eventType = line.substring(6).trim();
            } else if (line.startsWith('data:')) {
                try {
                    data = JSON.parse(line.substring(5).trim());
                } catch (e) {
                    console.error('Failed to parse SSE data:', e);
                }
            }
        }
        
        if (!data) return;
        
        // Handle different event types
        switch (eventType) {
            case 'start':
                console.log('Stream started:', data.query);
                break;
                
            case 'thought':
                this.addThoughtStep(stepsContainer, data);
                this.updateStepsCount(stepsCountEl);
                break;
                
            case 'action':
                this.addActionStep(stepsContainer, data);
                this.updateStepsCount(stepsCountEl);
                break;
                
            case 'observation':
                this.addObservationStep(stepsContainer, data);
                this.updateStepsCount(stepsCountEl);
                break;
                
            case 'final_answer':
                this.addFinalAnswer(finalAnswerContainer, data);
                break;
                
            case 'complete':
                this.showCompletion(footer, data);
                break;
                
            case 'error':
                this.showError(stepsContainer, data.error);
                break;
        }
        
        // Auto scroll ONLY the internal steps container
        if (eventType !== 'final_answer' && stepsContainer.parentElement) {
            stepsContainer.scrollTop = stepsContainer.scrollHeight;
        }
    }
    
    /**
     * Update steps count in toggle button
     */
    updateStepsCount(stepsCountEl) {
        if (stepsCountEl) {
            const count = this.steps.length;
            stepsCountEl.textContent = `(${count} step${count !== 1 ? 's' : ''})`;
        }
    }
    
    /**
     * Add thought step to display with character streaming
     */
    async addThoughtStep(container, data) {
        const stepEl = document.createElement('div');
        stepEl.className = 'stream-step thought fade-in';
        
        stepEl.innerHTML = `
            <div class="step-icon">💭</div>
            <div class="step-content">
                <div class="step-header">
                    <span class="step-type">Thought</span>
                    <span class="step-number">#${data.step_number}</span>
                </div>
                <div class="step-body markdown-content" id="thought-${data.step_number}"></div>
            </div>
        `;
        container.appendChild(stepEl);
        
        // Get streaming config from backend
        const config = await this.fetchStreamingConfig();
        
        // Stream the content character by character (faster than final answer)
        const contentBody = stepEl.querySelector(`#thought-${data.step_number}`);
        const streamRenderer = new CharacterStreamRenderer(
            contentBody,
            this.markdownRenderer,
            {
                charsPerFrame: config.internalCharsPerFrame,
                minDelay: config.internalMinDelay,
                maxDelay: config.internalMaxDelay
            }
        );
        
        await streamRenderer.streamText(data.content, true);
        
        this.steps.push(data);
    }
    
    /**
     * Add action step to display
     */
    addActionStep(container, data) {
        const stepEl = document.createElement('div');
        stepEl.className = 'stream-step action fade-in';
        stepEl.innerHTML = `
            <div class="step-icon">⚡</div>
            <div class="step-content">
                <div class="step-header">
                    <span class="step-type">Action</span>
                    <span class="step-number">#${data.step_number}</span>
                </div>
                <div class="step-body">
                    <strong>Execute:</strong> ${this.escapeHtml(data.function_name)}
                    <details style="margin-top: 8px;">
                        <summary style="cursor: pointer; color: #94a3b8;">Parameters</summary>
                        <pre style="margin-top: 8px; padding: 8px; background: #1e293b; border-radius: 4px; font-size: 0.75rem;">${JSON.stringify(data.parameters, null, 2)}</pre>
                    </details>
                </div>
            </div>
        `;
        container.appendChild(stepEl);
        this.steps.push(data);
        
        // Track API call
        this.apiCalls.push({
            function_name: data.function_name,
            parameters: data.parameters,
            status: 'executing'
        });
    }
    
    /**
     * Add observation step to display with character streaming
     */
    async addObservationStep(container, data) {
        const stepEl = document.createElement('div');
        stepEl.className = `stream-step observation ${data.success ? 'success' : 'failed'} fade-in`;
        
        const statusIcon = data.success ? '✅' : '❌';
        const statusText = data.success ? 'Success' : 'Failed';
        
        stepEl.innerHTML = `
            <div class="step-icon">👁️</div>
            <div class="step-content">
                <div class="step-header">
                    <span class="step-type">Observation ${statusIcon}</span>
                    <span class="step-number">#${data.step_number}</span>
                    ${data.execution_time_ms ? `<span class="step-time">${data.execution_time_ms}ms</span>` : ''}
                </div>
                <div class="step-body markdown-content" id="obs-${data.step_number}"></div>
            </div>
        `;
        container.appendChild(stepEl);
        
        // Get streaming config from backend
        const config = await this.fetchStreamingConfig();
        
        // Stream the observation result character by character (faster than final answer)
        const obsBody = stepEl.querySelector(`#obs-${data.step_number}`);
        const streamRenderer = new CharacterStreamRenderer(
            obsBody,
            this.markdownRenderer,
            {
                charsPerFrame: config.internalCharsPerFrame,
                minDelay: config.internalMinDelay,
                maxDelay: config.internalMaxDelay
            }
        );
        
        const resultText = `**${statusText}:** ${data.result || data.content || ''}`;
        await streamRenderer.streamText(resultText, true);
        
        this.steps.push(data);
        
        // Update last API call status
        if (this.apiCalls.length > 0) {
            this.apiCalls[this.apiCalls.length - 1].status = data.success ? 'success' : 'failed';
            this.apiCalls[this.apiCalls.length - 1].execution_time_ms = data.execution_time_ms;
        }
    }
    
    /**
     * Add final answer to separate container with character streaming
     */
    async addFinalAnswer(container, data) {
        // Show the final answer container
        container.style.display = 'block';
        
        const answerEl = document.createElement('div');
        answerEl.className = 'final-answer-content fade-in';
        answerEl.innerHTML = `
            <div class="answer-header">
                <div class="answer-title">
                    <span>Final Answer</span>
                    <span class="quality-badge">
                        <i class="fas fa-star"></i> ${(data.quality_score * 100).toFixed(0)}%
                    </span>
                </div>
            </div>
            <div class="answer-body markdown-content" id="answerBody"></div>
        `;
        container.appendChild(answerEl);
        
        // Get streaming config from backend
        const config = await this.fetchStreamingConfig();
        
        // Stream the answer character by character
        const answerBody = answerEl.querySelector('#answerBody');
        this.currentStreamRenderer = new CharacterStreamRenderer(
            answerBody,
            this.markdownRenderer,
            {
                charsPerFrame: config.charsPerFrame,
                minDelay: config.minDelay,
                maxDelay: config.maxDelay
            }
        );
        
        // Start streaming
        await this.currentStreamRenderer.streamText(data.response, true);
    }
    
    /**
     * Show completion metrics
     */
    showCompletion(footer, data) {
        // Update status
        const statusIndicator = this.container.querySelector('.status-indicator');
        const statusText = this.container.querySelector('.stream-status span');
        
        if (statusIndicator) {
            statusIndicator.className = `status-indicator ${data.success ? 'completed' : 'failed'}`;
        }
        if (statusText) {
            statusText.textContent = data.success ? 'Completed' : 'Incomplete';
        }
        
        // Show footer with metrics
        footer.style.display = 'block';
        footer.querySelector('#totalSteps').textContent = `Steps: ${data.total_steps}`;
        footer.querySelector('#totalApiCalls').textContent = `API Calls: ${data.total_api_calls}`;
        footer.querySelector('#processingTime').textContent = `Time: ${(data.processing_time_ms / 1000).toFixed(2)}s`;
        footer.querySelector('#qualityScore').textContent = `Quality: ${(data.quality_score * 100).toFixed(0)}%`;
    }
    
    /**
     * Show error message
     */
    showError(container, message) {
        const errorEl = document.createElement('div');
        errorEl.className = 'stream-error fade-in';
        errorEl.innerHTML = `
            <div class="error-icon">❌</div>
            <div class="error-message">
                <strong>Error:</strong> ${this.escapeHtml(message)}
            </div>
        `;
        container.appendChild(errorEl);
        
        // Update status
        const statusIndicator = this.container.querySelector('.status-indicator');
        const statusText = this.container.querySelector('.stream-status span');
        
        if (statusIndicator) {
            statusIndicator.className = 'status-indicator failed';
        }
        if (statusText) {
            statusText.textContent = 'Failed';
        }
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Stop streaming
     */
    stopStreaming() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}
