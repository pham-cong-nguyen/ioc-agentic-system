/**
 * Conversation Service - Manage conversation history and persistence
 */

export class ConversationService {
    constructor(api, state) {
        this.api = api;
        this.state = state;
        this.currentConversation = null;
        this.storageKey = 'ioc_conversations';
    }

    /**
     * Initialize conversation service
     */
    async init() {
        await this.loadConversations();
    }

    /**
     * Load all conversations from local storage and backend
     */
    async loadConversations() {
        try {
            // Load from local storage first for instant display
            const localConversations = this.getLocalConversations();
            
            if (localConversations.length > 0) {
                this.state.setState('conversations', localConversations);
            }

            // Then sync with backend if available
            try {
                const response = await this.api.get('/conversations');
                if (response.conversations) {
                    this.state.setState('conversations', response.conversations);
                    this.saveToLocalStorage(response.conversations);
                }
            } catch (error) {
                console.warn('Failed to load conversations from backend:', error);
                // Continue with local storage data
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
        }
    }

    /**
     * Create a new conversation
     */
    async createConversation(title = 'New Conversation') {
        const conversation = {
            id: this.generateId(),
            title,
            messages: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };

        try {
            // Try to save to backend
            const response = await this.api.post('/conversations', conversation);
            if (response.conversation) {
                conversation.id = response.conversation.id;
            }
        } catch (error) {
            console.warn('Failed to save conversation to backend:', error);
        }

        // Add to state
        const conversations = this.state.getState('conversations') || [];
        conversations.unshift(conversation);
        this.state.setState('conversations', conversations);
        
        // Save to local storage
        this.saveToLocalStorage(conversations);
        
        this.currentConversation = conversation;
        return conversation;
    }

    /**
     * Get conversation by ID
     */
    getConversation(id) {
        const conversations = this.state.getState('conversations') || [];
        return conversations.find(conv => conv.id === id);
    }

    /**
     * Update conversation
     */
    async updateConversation(id, updates) {
        const conversations = this.state.getState('conversations') || [];
        const index = conversations.findIndex(conv => conv.id === id);
        
        if (index !== -1) {
            conversations[index] = {
                ...conversations[index],
                ...updates,
                updatedAt: new Date().toISOString()
            };
            
            this.state.setState('conversations', conversations);
            this.saveToLocalStorage(conversations);
            
            // Try to sync with backend
            try {
                await this.api.put(`/conversations/${id}`, updates);
            } catch (error) {
                console.warn('Failed to update conversation on backend:', error);
            }
            
            return conversations[index];
        }
        
        return null;
    }

    /**
     * Delete conversation
     */
    async deleteConversation(id) {
        const conversations = this.state.getState('conversations') || [];
        const filtered = conversations.filter(conv => conv.id !== id);
        
        this.state.setState('conversations', filtered);
        this.saveToLocalStorage(filtered);
        
        // Try to delete from backend
        try {
            await this.api.delete(`/conversations/${id}`);
        } catch (error) {
            console.warn('Failed to delete conversation from backend:', error);
        }
        
        if (this.currentConversation?.id === id) {
            this.currentConversation = null;
        }
    }

    /**
     * Add message to current conversation
     */
    async addMessage(message) {
        if (!this.currentConversation) {
            this.currentConversation = await this.createConversation();
        }

        const messageWithId = {
            ...message,
            id: this.generateId(),
            timestamp: new Date().toISOString()
        };

        this.currentConversation.messages.push(messageWithId);
        
        // Update conversation title based on first message
        if (this.currentConversation.messages.length === 1 && message.role === 'user') {
            const title = message.content.substring(0, 50) + (message.content.length > 50 ? '...' : '');
            this.currentConversation.title = title;
        }

        await this.updateConversation(this.currentConversation.id, {
            messages: this.currentConversation.messages,
            title: this.currentConversation.title
        });

        return messageWithId;
    }

    /**
     * Get current conversation messages
     */
    getCurrentMessages() {
        return this.currentConversation?.messages || [];
    }

    /**
     * Set current conversation
     */
    setCurrentConversation(id) {
        const conversation = this.getConversation(id);
        if (conversation) {
            this.currentConversation = conversation;
            this.state.setState('currentConversationId', id);
            return true;
        }
        return false;
    }

    /**
     * Search conversations
     */
    searchConversations(query) {
        const conversations = this.state.getState('conversations') || [];
        const lowerQuery = query.toLowerCase();
        
        return conversations.filter(conv => {
            // Search in title
            if (conv.title.toLowerCase().includes(lowerQuery)) {
                return true;
            }
            
            // Search in messages
            return conv.messages.some(msg => 
                msg.content.toLowerCase().includes(lowerQuery)
            );
        });
    }

    /**
     * Get conversation statistics
     */
    getStats() {
        const conversations = this.state.getState('conversations') || [];
        
        const totalMessages = conversations.reduce((sum, conv) => 
            sum + conv.messages.length, 0
        );
        
        const totalTokens = conversations.reduce((sum, conv) => 
            sum + (conv.tokens || 0), 0
        );

        return {
            totalConversations: conversations.length,
            totalMessages,
            totalTokens,
            avgMessagesPerConversation: conversations.length > 0 
                ? (totalMessages / conversations.length).toFixed(1)
                : 0
        };
    }

    /**
     * Export conversation to JSON
     */
    exportConversation(id) {
        const conversation = this.getConversation(id);
        if (conversation) {
            const dataStr = JSON.stringify(conversation, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `conversation_${id}_${Date.now()}.json`;
            link.click();
            
            URL.revokeObjectURL(url);
        }
    }

    /**
     * Import conversation from JSON
     */
    async importConversation(file) {
        try {
            const text = await file.text();
            const conversation = JSON.parse(text);
            
            // Validate conversation structure
            if (!conversation.id || !Array.isArray(conversation.messages)) {
                throw new Error('Invalid conversation format');
            }
            
            // Generate new ID to avoid conflicts
            conversation.id = this.generateId();
            conversation.importedAt = new Date().toISOString();
            
            const conversations = this.state.getState('conversations') || [];
            conversations.unshift(conversation);
            this.state.setState('conversations', conversations);
            this.saveToLocalStorage(conversations);
            
            return conversation;
        } catch (error) {
            console.error('Error importing conversation:', error);
            throw error;
        }
    }

    /**
     * Clear all conversations
     */
    async clearAllConversations() {
        this.state.setState('conversations', []);
        this.currentConversation = null;
        localStorage.removeItem(this.storageKey);
        
        // Try to clear from backend
        try {
            await this.api.delete('/conversations/all');
        } catch (error) {
            console.warn('Failed to clear conversations from backend:', error);
        }
    }

    /**
     * Save conversations to local storage
     */
    saveToLocalStorage(conversations) {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(conversations));
        } catch (error) {
            console.error('Error saving to local storage:', error);
        }
    }

    /**
     * Get conversations from local storage
     */
    getLocalConversations() {
        try {
            const data = localStorage.getItem(this.storageKey);
            return data ? JSON.parse(data) : [];
        } catch (error) {
            console.error('Error reading from local storage:', error);
            return [];
        }
    }

    /**
     * Generate unique ID
     */
    generateId() {
        return `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Get or create current conversation
     */
    async ensureCurrentConversation() {
        if (!this.currentConversation) {
            this.currentConversation = await this.createConversation();
        }
        return this.currentConversation;
    }
}
