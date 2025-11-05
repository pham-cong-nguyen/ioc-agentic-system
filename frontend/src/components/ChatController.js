/**
 * Chat Controller - Handle chat interface logic
 */

import { StepTracker } from './StepTracker.js';
import { StreamingStepTracker } from './StreamingStepTracker.js';

export class ChatController {
    constructor(api, state, ui) {
        this.api = api;
        this.state = state;
        this.ui = ui;
        
        this.currentConversationId = null;
        this.messages = [];
        this.llmModelName = 'Loading...';
        this.stepTracker = new StepTracker();
        this.streamingStepTracker = new StreamingStepTracker();
        this.useStreaming = true; // Toggle streaming mode
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.loadExampleQueries();
        await this.loadLLMConfig();
    }

    async loadLLMConfig() {
        try {
            const response = await fetch('http://localhost:8862/config/llm');
            const config = await response.json();
            this.llmModelName = config.display_name || 'AI Model';
            
            // Update UI
            const modelElement = document.querySelector('.chat-model');
            if (modelElement) {
                modelElement.textContent = `Powered by ${this.llmModelName}`;
            }
            
            console.log('🤖 LLM Config loaded:', config);
        } catch (error) {
            console.error('❌ Failed to load LLM config:', error);
            this.llmModelName = 'AI Model';
        }
    }

    setupEventListeners() {
        console.log('🎯 ChatController: Setting up event listeners...');
        
        // Send button
        const sendBtn = document.getElementById('sendBtn');
        console.log('Send button element:', sendBtn);
        
        if (sendBtn) {
            console.log('✅ Attaching click listener to send button');
            sendBtn.addEventListener('click', () => {
                console.log('🖱️ Send button clicked!');
                this.sendMessage();
            });
            
            // Test if listener works
            sendBtn.onclick = () => {
                console.log('🖱️ Send button onclick triggered!');
            };
        } else {
            console.error('❌ Send button not found!');
        }

        // Chat input
        const chatInput = document.getElementById('chatInput');
        console.log('Chat input element:', chatInput);
        
        if (chatInput) {
            console.log('✅ Attaching keydown listener to chat input');
            chatInput.addEventListener('keydown', (e) => {
                console.log('⌨️ Key pressed:', e.key);
                if (e.key === 'Enter' && !e.shiftKey) {
                    console.log('✅ Enter key detected, sending message');
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            // Auto-resize textarea
            chatInput.addEventListener('input', (e) => {
                e.target.style.height = 'auto';
                e.target.style.height = e.target.scrollHeight + 'px';
            });
        } else {
            console.error('❌ Chat input not found!');
        }

        // New chat button
        const newChatBtn = document.getElementById('newChat');
        if (newChatBtn) {
            console.log('✅ Attaching listener to new chat button');
            newChatBtn.addEventListener('click', () => {
                console.log('🖱️ New chat button clicked!');
                this.startNewChat();
            });
        }

        // Clear chat button
        const clearChatBtn = document.getElementById('clearChat');
        if (clearChatBtn) {
            console.log('✅ Attaching listener to clear chat button');
            clearChatBtn.addEventListener('click', () => {
                console.log('🖱️ Clear chat button clicked!');
                this.clearChat();
            });
        }

        // Example queries
        console.log('✅ Attaching listeners to example queries');
        document.addEventListener('click', (e) => {
            if (e.target.closest('.example-query')) {
                console.log('🖱️ Example query clicked!');
                const query = e.target.closest('.example-query').dataset.query;
                console.log('Query text:', query);
                document.getElementById('chatInput').value = query;
                this.sendMessage();
            }
        });
        
        console.log('✅ ChatController event listeners setup complete');
    }

    async loadHistory() {
        try {
            const history = await this.api.getQueryHistory();
            this.renderChatList(history.queries || []);
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    async loadExampleQueries() {
        try {
            const examples = await this.api.getExampleQueries();
            // Store for later use
            this.state.setState({ exampleQueries: examples });
        } catch (error) {
            console.error('Failed to load examples:', error);
        }
    }

    renderChatList(conversations) {
        const chatList = document.getElementById('chatList');
        if (!chatList) return;

        if (conversations.length === 0) {
            chatList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-comments"></i>
                    <p>No conversations yet</p>
                </div>
            `;
            return;
        }

        chatList.innerHTML = conversations.map((conv, index) => `
            <div class="chat-item ${index === 0 ? 'active' : ''}" data-id="${conv.query_id}">
                <div class="chat-item-title">${this.truncate(conv.query, 30)}</div>
                <div class="chat-item-preview">${this.ui.formatDate(conv.timestamp)}</div>
            </div>
        `).join('');

        // Add click handlers
        chatList.querySelectorAll('.chat-item').forEach(item => {
            item.addEventListener('click', () => {
                this.loadConversation(item.dataset.id);
            });
        });
    }

    async sendMessage() {
        const input = document.getElementById('chatInput');
        const query = input.value.trim();

        if (!query) return;

        // Clear input
        input.value = '';
        input.style.height = 'auto';

        // Hide welcome message
        const welcomeMsg = document.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.style.display = 'none';
        }

        // Add user message to UI
        this.addMessage('user', query);

        // Create assistant message container with streaming placeholder
        const assistantMessageId = this.addStreamingMessage();

        try {
            // Detect language
            const language = this.detectLanguage(query);

            if (this.useStreaming) {
                // Use streaming mode
                await this.sendStreamingMessage(query, language, assistantMessageId);
            } else {
                // Use non-streaming mode (fallback)
                await this.sendNonStreamingMessage(query, language, assistantMessageId);
            }

            // Store conversation ID
            if (!this.currentConversationId) {
                this.currentConversationId = `conv_${Date.now()}`;
            }

        } catch (error) {
            this.removeMessage(assistantMessageId);
            this.addMessage('assistant', 'Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại.', {
                error: error.message
            });
            this.ui.showToast('Failed to process query', 'error');
        }
    }

    async sendStreamingMessage(query, language, messageId) {
        const messageEl = document.querySelector(`[data-id="${messageId}"]`);
        if (!messageEl) return;

        const contentEl = messageEl.querySelector('.message-content');
        
        // Create streaming container
        const streamContainer = document.createElement('div');
        streamContainer.className = 'streaming-container';
        contentEl.innerHTML = ''; // Clear loading
        contentEl.appendChild(streamContainer);

        // Start streaming
        this.startAutoScroll();
        await this.streamingStepTracker.startStreaming(
            streamContainer,
            query,
            'default_user',
            this.currentConversationId
        );
        this.stopAutoScroll();
    }

    async sendNonStreamingMessage(query, language, messageId) {
        // Existing non-streaming implementation
        const response = await this.api.processQueryV2(
            query,
            language,
            this.currentConversationId
        );

        // Remove loading message
        this.removeMessage(messageId);

        // Add assistant response with steps
        this.addMessage('assistant', response.response, {
            steps: response.steps || [],
            apiCalls: response.api_calls || [],
            totalSteps: response.total_steps,
            totalApiCalls: response.total_api_calls,
            processingTime: response.processing_time_ms,
            qualityScore: response.quality_score
        });
    }

    /**
     * Start auto-scroll interval for streaming messages
     */
    startAutoScroll() {
        if (this.autoScrollInterval) {
            return; // Already scrolling
        }
        
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;
        
        // Scroll every 100ms during streaming
        this.autoScrollInterval = setInterval(() => {
            const isNearBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < 200;
            
            if (isNearBottom) {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }, 100);
        
        console.log('🔄 Auto-scroll started');
    }

    /**
     * Stop auto-scroll interval
     */
    stopAutoScroll() {
        if (this.autoScrollInterval) {
            clearInterval(this.autoScrollInterval);
            this.autoScrollInterval = null;
            console.log('⏹️ Auto-scroll stopped');
        }
        
        // Final scroll to ensure we're at bottom
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            setTimeout(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }, 100);
        }
    }

    addStreamingMessage() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return null;

        const messageId = `msg-${Date.now()}-${Math.random()}`;
        const message = {
            id: messageId,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            metadata: { streaming: true }
        };

        this.messages.push(message);

        const messageEl = document.createElement('div');
        messageEl.className = 'message assistant fade-in';
        messageEl.dataset.id = messageId;
        messageEl.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;

        messagesContainer.appendChild(messageEl);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        return messageId;
    }

    addMessage(role, content, metadata = {}) {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        const messageId = `msg-${Date.now()}-${Math.random()}`;
        const message = {
            id: messageId,
            role,
            content,
            timestamp: new Date(),
            metadata
        };

        this.messages.push(message);

        const messageEl = this.createMessageElement(message);
        messagesContainer.appendChild(messageEl);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        return messageId;
    }

    createMessageElement(message) {
        const div = document.createElement('div');
        div.className = `message ${message.role} fade-in`;
        div.dataset.id = message.id;

        const avatarIcon = message.role === 'user' 
            ? '<i class="fas fa-user"></i>' 
            : '<i class="fas fa-robot"></i>';

        let metadataHTML = '';
        
        // Add step tracker for assistant messages with steps
        if (message.role === 'assistant' && message.metadata.steps && message.metadata.steps.length > 0) {
            const stepTrackerContainer = document.createElement('div');
            stepTrackerContainer.className = 'step-tracker-wrapper';
            this.stepTracker.createStepTrackerUI(
                stepTrackerContainer, 
                message.metadata.steps,
                message.metadata.apiCalls || []
            );
            // We'll append this later
        }
        
        if (message.metadata.insights && message.metadata.insights.length > 0) {
            metadataHTML += `
                <div class="message-insights">
                    <div class="insights-header">
                        <i class="fas fa-lightbulb"></i>
                        <span>Insights</span>
                    </div>
                    <ul>
                        ${message.metadata.insights.map(insight => `<li>${insight}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (message.metadata.processingTime) {
            metadataHTML += `
                <div class="message-stats">
                    <i class="fas fa-clock"></i>
                    <span>${(message.metadata.processingTime / 1000).toFixed(2)}s</span>
                    ${message.metadata.qualityScore ? `
                        <span class="quality-badge" title="Quality Score">
                            <i class="fas fa-star"></i> ${(message.metadata.qualityScore * 100).toFixed(0)}%
                        </span>
                    ` : ''}
                </div>
            `;
        }

        div.innerHTML = `
            <div class="message-avatar">${avatarIcon}</div>
            <div class="message-content">
                <div class="message-bubble">
                    ${this.formatMessageContent(message.content)}
                </div>
                ${metadataHTML}
                <div class="message-meta">
                    <span>${this.ui.formatTime(message.timestamp)}</span>
                    <div class="message-actions">
                        <button class="message-action-btn" data-action="copy">
                            <i class="fas fa-copy"></i> Copy
                        </button>
                        ${message.role === 'assistant' ? `
                            <button class="message-action-btn" data-action="feedback">
                                <i class="fas fa-thumbs-up"></i> Feedback
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;

        // Insert step tracker before message-meta if exists
        if (message.role === 'assistant' && message.metadata.steps && message.metadata.steps.length > 0) {
            const messageContent = div.querySelector('.message-content');
            const messageMeta = div.querySelector('.message-meta');
            const stepTrackerContainer = document.createElement('div');
            stepTrackerContainer.className = 'step-tracker-wrapper';
            this.stepTracker.createStepTrackerUI(
                stepTrackerContainer, 
                message.metadata.steps,
                message.metadata.apiCalls || []
            );
            messageContent.insertBefore(stepTrackerContainer, messageMeta);
        }

        // Add action handlers
        div.querySelectorAll('.message-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                if (action === 'copy') {
                    this.ui.copyToClipboard(message.content);
                } else if (action === 'feedback') {
                    this.showFeedbackDialog(message.id);
                }
            });
        });

        return div;
    }

    addLoadingMessage() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return null;

        const loadingId = `loading-${Date.now()}`;
        const div = document.createElement('div');
        div.className = 'message assistant fade-in';
        div.dataset.id = loadingId;

        div.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;

        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        return loadingId;
    }

    removeMessage(messageId) {
        const message = document.querySelector(`[data-id="${messageId}"]`);
        if (message) {
            message.remove();
        }
    }

    formatMessageContent(content) {
        // Simple markdown-like formatting
        let formatted = this.ui.escapeHtml(content);
        
        // Bold
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italic
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Line breaks
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }

    detectLanguage(text) {
        // Simple Vietnamese detection
        const vietnameseChars = /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i;
        return vietnameseChars.test(text) ? 'vi' : 'en';
    }

    truncate(text, length) {
        if (text.length <= length) return text;
        return text.substring(0, length) + '...';
    }

    startNewChat() {
        this.currentConversationId = null;
        this.messages = [];
        
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
            
            // Show welcome message
            const welcomeMsg = document.querySelector('.welcome-message');
            if (welcomeMsg) {
                welcomeMsg.style.display = 'block';
            } else {
                this.renderWelcomeMessage();
            }
        }
        
        document.getElementById('chatTitle').textContent = 'New Conversation';
    }

    async clearChat() {
        const confirmed = await this.ui.showConfirm(
            'Clear Chat',
            'Are you sure you want to clear this conversation?'
        );

        if (confirmed === 'confirm') {
            this.startNewChat();
            this.ui.showToast('Chat cleared', 'success');
        }
    }

    renderWelcomeMessage() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">
                    <i class="fas fa-robot"></i>
                </div>
                <h2>Welcome to IOC Agentic System</h2>
                <p>Ask me anything about your operations in Vietnamese or English</p>
                <div class="example-queries">
                    <div class="example-query" data-query="Mức tiêu thụ điện hôm nay là bao nhiêu?">
                        <i class="fas fa-bolt"></i>
                        <span>Mức tiêu thụ điện hôm nay?</span>
                    </div>
                    <div class="example-query" data-query="So sánh lưu lượng giao thông tuần này với tuần trước">
                        <i class="fas fa-traffic-light"></i>
                        <span>So sánh lưu lượng giao thông</span>
                    </div>
                    <div class="example-query" data-query="Chất lượng không khí ở Hà Nội như thế nào?">
                        <i class="fas fa-wind"></i>
                        <span>Chất lượng không khí</span>
                    </div>
                </div>
            </div>
        `;
    }

    async showFeedbackDialog(messageId) {
        const content = `
            <div class="feedback-form">
                <p>How would you rate this response?</p>
                <div class="rating-stars">
                    ${[1, 2, 3, 4, 5].map(i => `
                        <button class="star-btn" data-rating="${i}">
                            <i class="fas fa-star"></i>
                        </button>
                    `).join('')}
                </div>
                <textarea id="feedbackText" placeholder="Additional feedback (optional)" rows="3"></textarea>
            </div>
        `;

        const result = await this.ui.showModal('Feedback', content, [
            { label: 'Cancel', action: 'cancel', type: 'secondary' },
            { label: 'Submit', action: 'submit', type: 'primary' }
        ]);

        if (result === 'submit') {
            // Get rating and feedback
            const rating = document.querySelector('.star-btn.active')?.dataset.rating || 5;
            const feedback = document.getElementById('feedbackText')?.value || null;
            
            try {
                await this.api.submitFeedback(messageId, parseInt(rating), feedback);
                this.ui.showToast('Thank you for your feedback!', 'success');
            } catch (error) {
                this.ui.showToast('Failed to submit feedback', 'error');
            }
        }
    }

    async loadConversation(conversationId) {
        try {
            const conversation = await this.api.getQueryResult(conversationId);
            // Implement conversation loading
            this.ui.showToast('Conversation loaded', 'info');
        } catch (error) {
            this.ui.showToast('Failed to load conversation', 'error');
        }
    }

    searchHistory(query) {
        // Implement history search
        console.log('Searching history:', query);
    }
}
